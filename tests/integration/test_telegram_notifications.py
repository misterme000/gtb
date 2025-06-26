import pytest
import os
import tempfile
import json
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path

from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from core.bot_management.event_bus import EventBus
from core.bot_management.notification.notification_handler import NotificationHandler
from core.bot_management.notification.notification_content import NotificationType


class TestTelegramNotifications:
    """Tests for Telegram notification functionality."""
    
    def test_telegram_url_format_validation(self):
        """Test that Telegram URL format is correct."""
        # Get the current Telegram URL from environment
        telegram_url = os.getenv("APPRISE_NOTIFICATION_URLS", "")
        
        print(f"Current Telegram URL: {telegram_url}")
        
        # Check if URL is properly formatted
        if telegram_url:
            assert telegram_url.startswith("tgram://"), f"Telegram URL should start with 'tgram://', got: {telegram_url}"
            
            # Parse the URL format: tgram://bot_token/chat_id
            parts = telegram_url.replace("tgram://", "").split("/")
            assert len(parts) == 2, f"Telegram URL should have format 'tgram://bot_token/chat_id', got: {telegram_url}"
            
            bot_token, chat_id = parts
            assert ":" in bot_token, f"Bot token should contain ':', got: {bot_token}"
            assert chat_id.isdigit() or chat_id.startswith("-"), f"Chat ID should be numeric or start with '-', got: {chat_id}"
            
            print(f"✅ Telegram URL format is valid")
            print(f"   Bot Token: {bot_token[:10]}...")
            print(f"   Chat ID: {chat_id}")
        else:
            print("⚠️ No Telegram URL configured in APPRISE_NOTIFICATION_URLS")
    
    def test_notification_handler_initialization_with_telegram(self):
        """Test that NotificationHandler initializes correctly with Telegram URL."""
        telegram_url = os.getenv("APPRISE_NOTIFICATION_URLS", "")
        
        if not telegram_url:
            pytest.skip("No Telegram URL configured")
        
        event_bus = MagicMock()
        
        # Test with LIVE mode (should enable notifications)
        handler = NotificationHandler(
            event_bus=event_bus,
            urls=[telegram_url],
            trading_mode=TradingMode.LIVE
        )
        
        assert handler.enabled is True
        assert handler.apprise_instance is not None
        
        # Test with BACKTEST mode (should disable notifications)
        handler_backtest = NotificationHandler(
            event_bus=event_bus,
            urls=[telegram_url],
            trading_mode=TradingMode.BACKTEST
        )
        
        assert handler_backtest.enabled is False
        assert handler_backtest.apprise_instance is None
        
        print("✅ NotificationHandler initialization works correctly")
    
    @patch('apprise.Apprise')
    def test_telegram_notification_sending(self, mock_apprise):
        """Test sending notifications through Telegram."""
        telegram_url = os.getenv("APPRISE_NOTIFICATION_URLS", "")
        
        if not telegram_url:
            pytest.skip("No Telegram URL configured")
        
        # Mock the Apprise instance
        mock_apprise_instance = MagicMock()
        mock_apprise.return_value = mock_apprise_instance
        
        event_bus = MagicMock()
        
        handler = NotificationHandler(
            event_bus=event_bus,
            urls=[telegram_url],
            trading_mode=TradingMode.LIVE
        )
        
        # Test sending a simple notification
        handler.send_notification("Test notification message")
        
        # Verify that notify was called
        mock_apprise_instance.notify.assert_called_once_with(
            title="Notification",
            body="Test notification message"
        )
        
        # Test sending a typed notification
        mock_apprise_instance.reset_mock()
        handler.send_notification(
            NotificationType.ORDER_FILLED,
            order_details="BUY 0.1 BTC at $50000"
        )
        
        mock_apprise_instance.notify.assert_called_once_with(
            title="Order Filled",
            body="Order has been filled successfully:\nBUY 0.1 BTC at $50000"
        )
        
        print("✅ Telegram notification sending works correctly")
    
    def test_why_notifications_not_working_in_backtest(self):
        """Identify why notifications don't work in backtest mode."""
        telegram_url = os.getenv("APPRISE_NOTIFICATION_URLS", "")
        
        if not telegram_url:
            print("❌ Issue 1: No Telegram URL configured in APPRISE_NOTIFICATION_URLS")
            return
        
        # Check current config trading mode
        config_path = "config/config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                trading_mode = config.get("exchange", {}).get("trading_mode", "unknown")
                
                print(f"Current trading mode: {trading_mode}")
                
                if trading_mode == "backtest":
                    print("❌ Issue 2: Notifications are DISABLED in backtest mode by design")
                    print("   This is intentional to prevent spam during backtesting")
                    print("   Notifications only work in 'live' or 'paper_trading' modes")
                else:
                    print(f"✅ Trading mode '{trading_mode}' should support notifications")
        
        # Test notification handler behavior
        event_bus = MagicMock()
        
        # Test with backtest mode
        handler_backtest = NotificationHandler(
            event_bus=event_bus,
            urls=[telegram_url],
            trading_mode=TradingMode.BACKTEST
        )
        
        print(f"Backtest mode - enabled: {handler_backtest.enabled}")
        print(f"Backtest mode - apprise_instance: {handler_backtest.apprise_instance}")
        
        # Test with live mode
        handler_live = NotificationHandler(
            event_bus=event_bus,
            urls=[telegram_url],
            trading_mode=TradingMode.LIVE
        )
        
        print(f"Live mode - enabled: {handler_live.enabled}")
        print(f"Live mode - apprise_instance: {handler_live.apprise_instance is not None}")
    
    def test_telegram_url_parsing_issues(self):
        """Test for common Telegram URL parsing issues."""
        telegram_url = os.getenv("APPRISE_NOTIFICATION_URLS", "")
        
        if not telegram_url:
            print("❌ No Telegram URL to test")
            return
        
        # Check for common issues
        issues = []
        
        # Issue 1: Empty or whitespace URLs
        if not telegram_url.strip():
            issues.append("URL is empty or contains only whitespace")
        
        # Issue 2: Multiple URLs not properly separated
        urls = telegram_url.split(",")
        for i, url in enumerate(urls):
            url = url.strip()
            if url and not url.startswith(("tgram://", "telegram://", "discord://", "slack://")):
                issues.append(f"URL {i+1} doesn't start with a valid protocol: {url}")
        
        # Issue 3: Invalid bot token format
        if telegram_url.startswith("tgram://"):
            try:
                token_part = telegram_url.replace("tgram://", "").split("/")[0]
                if ":" not in token_part:
                    issues.append("Bot token doesn't contain ':' separator")
                else:
                    bot_id, bot_secret = token_part.split(":", 1)
                    if not bot_id.isdigit():
                        issues.append(f"Bot ID should be numeric, got: {bot_id}")
                    if len(bot_secret) < 10:
                        issues.append(f"Bot secret seems too short: {len(bot_secret)} characters")
            except Exception as e:
                issues.append(f"Error parsing Telegram URL: {e}")
        
        if issues:
            print("❌ Telegram URL issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Telegram URL appears to be correctly formatted")
    
    @pytest.mark.asyncio
    async def test_async_notification_sending(self):
        """Test async notification sending."""
        telegram_url = os.getenv("APPRISE_NOTIFICATION_URLS", "")
        
        if not telegram_url:
            pytest.skip("No Telegram URL configured")
        
        event_bus = EventBus()
        
        with patch('apprise.Apprise') as mock_apprise:
            mock_apprise_instance = MagicMock()
            mock_apprise.return_value = mock_apprise_instance
            
            handler = NotificationHandler(
                event_bus=event_bus,
                urls=[telegram_url],
                trading_mode=TradingMode.LIVE
            )
            
            # Test async notification
            await handler.async_send_notification(
                NotificationType.ORDER_PLACED,
                order_details="Test order details"
            )
            
            # Give it a moment to process
            await asyncio.sleep(0.1)
            
            # Verify notification was sent
            assert mock_apprise_instance.notify.called
            
        await event_bus.shutdown()
        print("✅ Async notification sending works correctly")
    
    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        from dotenv import load_dotenv
        
        # Reload environment variables
        load_dotenv()
        
        telegram_url = os.getenv("APPRISE_NOTIFICATION_URLS", "")
        api_key = os.getenv("EXCHANGE_API_KEY", "")
        secret_key = os.getenv("EXCHANGE_SECRET_KEY", "")
        
        print(f"Environment variables loaded:")
        print(f"  APPRISE_NOTIFICATION_URLS: {'✅ Set' if telegram_url else '❌ Not set'}")
        print(f"  EXCHANGE_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
        print(f"  EXCHANGE_SECRET_KEY: {'✅ Set' if secret_key else '❌ Not set'}")
        
        if telegram_url:
            print(f"  Telegram URL length: {len(telegram_url)} characters")
        
        # Test the main.py initialization function
        from main import initialize_notification_handler
        
        # Create a mock config manager
        config_manager = MagicMock()
        config_manager.get_trading_mode.return_value = TradingMode.LIVE
        
        event_bus = MagicMock()
        
        handler = initialize_notification_handler(config_manager, event_bus)
        
        print(f"  NotificationHandler enabled: {handler.enabled}")
        print(f"  NotificationHandler has apprise: {handler.apprise_instance is not None}")
