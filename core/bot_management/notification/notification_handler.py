from typing import List, Optional, Union
import apprise, logging, asyncio
from concurrent.futures import ThreadPoolExecutor
from .notification_content import NotificationType
from config.trading_mode import TradingMode
from core.bot_management.event_bus import EventBus, Events
from core.order_handling.order import Order

class NotificationHandler:
    """
    Handles sending notifications through various channels using the Apprise library.
    Supports multiple notification services like Telegram, Discord, Slack, etc.
    """
    _executor = ThreadPoolExecutor(max_workers=3)

    def __init__(
        self,
        event_bus: EventBus,
        urls: Optional[List[str]],
        trading_mode: TradingMode
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_bus = event_bus

        # Validate URLs and filter out empty ones
        valid_urls = self._validate_urls(urls) if urls else []

        # Check if notifications should be enabled
        self.enabled = bool(valid_urls) and trading_mode in {TradingMode.LIVE, TradingMode.PAPER_TRADING}
        self.lock = asyncio.Lock()
        self.apprise_instance = apprise.Apprise() if self.enabled else None

        # Log notification status
        if not valid_urls:
            self.logger.info("No valid notification URLs provided - notifications disabled")
        elif trading_mode not in {TradingMode.LIVE, TradingMode.PAPER_TRADING}:
            self.logger.info(f"Notifications disabled in {trading_mode.value} mode")
        else:
            self.logger.info(f"Notifications enabled with {len(valid_urls)} URL(s)")

        if self.enabled and valid_urls:
            self.event_bus.subscribe(Events.ORDER_FILLED, self._send_notification_on_order_filled)

            for url in valid_urls:
                try:
                    self.apprise_instance.add(url)
                    self.logger.debug(f"Added notification URL: {self._mask_url(url)}")
                except Exception as e:
                    self.logger.error(f"Failed to add notification URL {self._mask_url(url)}: {e}")

    def _validate_urls(self, urls: List[str]) -> List[str]:
        """Validate and filter notification URLs."""
        if not urls:
            return []

        valid_urls = []
        for url in urls:
            url = url.strip()
            if not url:
                continue

            # Basic URL validation
            if not any(url.startswith(protocol) for protocol in ['tgram://', 'telegram://', 'discord://', 'slack://', 'mailto://', 'webhook://']):
                self.logger.warning(f"Unsupported notification URL protocol: {self._mask_url(url)}")
                continue

            # Telegram-specific validation
            if url.startswith('tgram://'):
                if not self._validate_telegram_url(url):
                    continue

            valid_urls.append(url)

        return valid_urls

    def _validate_telegram_url(self, url: str) -> bool:
        """Validate Telegram URL format."""
        try:
            # Format: tgram://bot_token/chat_id
            parts = url.replace('tgram://', '').split('/')
            if len(parts) != 2:
                self.logger.error(f"Invalid Telegram URL format. Expected: tgram://bot_token/chat_id")
                return False

            bot_token, chat_id = parts

            # Validate bot token format (should contain ':')
            if ':' not in bot_token:
                self.logger.error(f"Invalid Telegram bot token format. Should contain ':'")
                return False

            bot_id, bot_secret = bot_token.split(':', 1)

            # Validate bot ID (should be numeric)
            if not bot_id.isdigit():
                self.logger.error(f"Invalid Telegram bot ID. Should be numeric")
                return False

            # Validate bot secret (should be reasonable length)
            if len(bot_secret) < 10:
                self.logger.error(f"Invalid Telegram bot secret. Seems too short")
                return False

            # Validate chat ID (should be numeric or start with -)
            if not (chat_id.isdigit() or (chat_id.startswith('-') and chat_id[1:].isdigit())):
                self.logger.error(f"Invalid Telegram chat ID format. Should be numeric or start with '-'")
                return False

            self.logger.debug(f"Telegram URL validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Error validating Telegram URL: {e}")
            return False

    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of URL for logging."""
        if url.startswith('tgram://'):
            # Mask bot token but show chat ID
            parts = url.replace('tgram://', '').split('/')
            if len(parts) == 2:
                bot_token, chat_id = parts
                if ':' in bot_token:
                    bot_id, bot_secret = bot_token.split(':', 1)
                    masked_token = f"{bot_id}:{'*' * min(len(bot_secret), 10)}"
                    return f"tgram://{masked_token}/{chat_id}"

        # For other URLs, just mask after the protocol
        if '://' in url:
            protocol, rest = url.split('://', 1)
            return f"{protocol}://{'*' * min(len(rest), 20)}"

        return url

    def send_notification(
        self,
        content: Union[NotificationType, str],
        **kwargs
    ) -> bool:
        """Send a notification. Returns True if successful, False otherwise."""
        if not self.enabled:
            self.logger.debug("Notifications are disabled - skipping notification")
            return False

        if not self.apprise_instance:
            self.logger.error("Apprise instance not initialized")
            return False

        try:
            if isinstance(content, NotificationType):
                title = content.value.title
                message_template = content.value.message
                required_placeholders = {key.strip("{}") for key in message_template.split() if "{" in key and "}" in key}
                missing_placeholders = required_placeholders - kwargs.keys()

                if missing_placeholders:
                    self.logger.warning(f"Missing placeholders for notification: {missing_placeholders}. " "Defaulting to 'N/A' for missing values.")

                message = message_template.format(**{key: kwargs.get(key, 'N/A') for key in required_placeholders})
            else:
                title = "Grid Trading Bot Notification"
                message = str(content)

            self.logger.debug(f"Sending notification: {title}")
            success = self.apprise_instance.notify(title=title, body=message)

            if success:
                self.logger.debug("Notification sent successfully")
            else:
                self.logger.warning("Notification sending failed (Apprise returned False)")

            return success

        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return False

    async def async_send_notification(
        self,
        content: Union[NotificationType, str],
        **kwargs
    ) -> bool:
        """Send a notification asynchronously. Returns True if successful, False otherwise."""
        if not self.enabled:
            return False

        async with self.lock:
            loop = asyncio.get_running_loop()
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(self._executor, lambda: self.send_notification(content, **kwargs)),
                    timeout=10  # Increased timeout for better reliability
                )
                return result
            except asyncio.TimeoutError:
                self.logger.error("Notification sending timed out after 10 seconds")
                return False
            except Exception as e:
                self.logger.error(f"Failed to send notification: {str(e)}")
                return False
    
    async def _send_notification_on_order_filled(self, order: Order) -> None:
        """Handle order filled event by sending notification."""
        success = await self.async_send_notification(NotificationType.ORDER_FILLED, order_details=str(order))
        if not success:
            self.logger.warning(f"Failed to send order filled notification for order: {order.id}")

    async def test_notification(self) -> bool:
        """Send a test notification to verify connectivity. Returns True if successful."""
        if not self.enabled:
            self.logger.info("Cannot test notifications - they are disabled")
            return False

        self.logger.info("Sending test notification...")
        success = await self.async_send_notification(
            "🤖 Grid Trading Bot Test\n\n"
            "This is a test notification to verify that Telegram notifications are working correctly. "
            "If you receive this message, your notification setup is working! 🎉"
        )

        if success:
            self.logger.info("✅ Test notification sent successfully")
        else:
            self.logger.error("❌ Test notification failed")

        return success