#!/usr/bin/env python3
"""
Test Telegram Notifications

This script tests the Telegram notification functionality to help diagnose issues.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from config.trading_mode import TradingMode
from core.bot_management.event_bus import EventBus
from core.bot_management.notification.notification_handler import NotificationHandler
from core.bot_management.notification.notification_content import NotificationType


async def test_telegram_notifications():
    """Test Telegram notification functionality."""
    
    print("🧪 Testing Telegram Notifications")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variable
    telegram_url = os.getenv("APPRISE_NOTIFICATION_URLS", "")
    print(f"📋 Environment Variable Check:")
    print(f"   APPRISE_NOTIFICATION_URLS: {'✅ Set' if telegram_url else '❌ Not set'}")
    
    if telegram_url:
        print(f"   URL Length: {len(telegram_url)} characters")
        print(f"   URL Preview: {telegram_url[:20]}...")
        
        # Basic format validation
        if telegram_url.startswith("tgram://"):
            print(f"   Format: ✅ Starts with 'tgram://'")
            
            try:
                parts = telegram_url.replace("tgram://", "").split("/")
                if len(parts) == 2:
                    bot_token, chat_id = parts
                    print(f"   Bot Token: {'✅ Present' if ':' in bot_token else '❌ Invalid format'}")
                    print(f"   Chat ID: {'✅ Valid' if chat_id.isdigit() or chat_id.startswith('-') else '❌ Invalid format'}")
                else:
                    print(f"   Format: ❌ Should have format 'tgram://bot_token/chat_id'")
            except Exception as e:
                print(f"   Format: ❌ Error parsing URL: {e}")
        else:
            print(f"   Format: ❌ Should start with 'tgram://'")
    
    print()
    
    # Test with different trading modes
    test_modes = [
        (TradingMode.BACKTEST, "Backtest (should be disabled)"),
        (TradingMode.PAPER_TRADING, "Paper Trading (should be enabled)"),
        (TradingMode.LIVE, "Live Trading (should be enabled)")
    ]
    
    for trading_mode, description in test_modes:
        print(f"🔧 Testing {description}")
        print("-" * 30)
        
        # Create event bus and notification handler
        event_bus = EventBus()
        
        try:
            # Parse URLs like the main.py does
            urls = []
            if telegram_url.strip():
                urls = [url.strip() for url in telegram_url.split(",") if url.strip()]
            
            handler = NotificationHandler(
                event_bus=event_bus,
                urls=urls,
                trading_mode=trading_mode
            )
            
            print(f"   Handler Enabled: {'✅ Yes' if handler.enabled else '❌ No'}")
            print(f"   Apprise Instance: {'✅ Created' if handler.apprise_instance else '❌ None'}")
            
            if handler.enabled:
                print(f"   🧪 Testing notification sending...")
                
                # Test simple notification
                success = await handler.async_send_notification(
                    f"🤖 Test from {trading_mode.value} mode\n\n"
                    f"This is a test notification from {trading_mode.value} mode. "
                    f"If you see this, notifications are working! 🎉"
                )
                
                print(f"   Simple Notification: {'✅ Success' if success else '❌ Failed'}")
                
                # Test typed notification
                success2 = await handler.async_send_notification(
                    NotificationType.ORDER_PLACED,
                    order_details=f"Test order from {trading_mode.value} mode"
                )
                
                print(f"   Typed Notification: {'✅ Success' if success2 else '❌ Failed'}")
                
                # Test the built-in test method
                try:
                    success3 = await handler.test_notification()
                    print(f"   Test Method: {'✅ Success' if success3 else '❌ Failed'}")
                except Exception as e:
                    print(f"   Test Method: ❌ Error: {e}")
                    success3 = False
                
                if success or success2 or success3:
                    print(f"   🎉 At least one notification succeeded!")
                else:
                    print(f"   ⚠️ All notifications failed")
            else:
                print(f"   ⏭️ Skipping notification tests (handler disabled)")
            
        except Exception as e:
            print(f"   ❌ Error during testing: {e}")
        
        finally:
            await event_bus.shutdown()
        
        print()
    
    # Provide recommendations
    print("💡 Recommendations:")
    print("-" * 20)
    
    if not telegram_url:
        print("   1. ❌ Set APPRISE_NOTIFICATION_URLS in your .env file")
        print("      Example: APPRISE_NOTIFICATION_URLS=tgram://bot_token/chat_id")
    else:
        print("   1. ✅ Telegram URL is configured")
    
    print("   2. 🔄 Change trading mode to 'paper_trading' or 'live' to enable notifications")
    print("      Current config.json has 'backtest' mode which disables notifications")
    
    print("   3. 🤖 Verify your Telegram bot:")
    print("      - Bot token is valid and active")
    print("      - Chat ID is correct (your user ID or group ID)")
    print("      - Bot has permission to send messages to the chat")
    
    print("   4. 🌐 Test network connectivity to Telegram API")
    
    print("\n🔗 Useful Links:")
    print("   - Create Telegram Bot: https://t.me/BotFather")
    print("   - Get Chat ID: https://t.me/userinfobot")
    print("   - Apprise Documentation: https://github.com/caronc/apprise")


if __name__ == "__main__":
    asyncio.run(test_telegram_notifications())
