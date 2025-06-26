#!/usr/bin/env python3
"""
Example: Running Backtests with Live Downloaded Data

This script demonstrates how to run backtests using real historical data
downloaded directly from exchanges (instead of pre-existing CSV files).

The system can download data from multiple exchanges including:
- Coinbase
- Kraken  
- Bitfinex
- Bitstamp
- Huobi
- OKEx
- Bybit
- And more...

Note: Some exchanges like Binance may have geographic restrictions.
"""

import asyncio
import json
import tempfile
import os
from pathlib import Path

# Add the project root to the path so we can import modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from core.bot_management.grid_trading_bot import GridTradingBot
from core.bot_management.event_bus import EventBus
from core.bot_management.notification.notification_handler import NotificationHandler


def create_live_data_config(
    exchange_name: str = "coinbase",
    start_date: str = "2024-12-01T00:00:00Z",
    end_date: str = "2024-12-03T23:59:59Z",
    timeframe: str = "1h",
    initial_balance: float = 10000,
    grid_top: float = 105000,
    grid_bottom: float = 95000,
    num_grids: int = 10
):
    """
    Create a configuration for backtesting with live downloaded data.
    
    Key point: NO 'historical_data_file' is specified, which forces the system
    to download real data from the exchange.
    """
    return {
        "exchange": {
            "name": exchange_name,
            "trading_fee": 0.005,  # 0.5% fee (typical for most exchanges)
            "trading_mode": "backtest"
        },
        "pair": {
            "base_currency": "BTC",
            "quote_currency": "USDT"
        },
        "trading_settings": {
            "timeframe": timeframe,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "initial_balance": initial_balance
            # NOTE: No "historical_data_file" - this triggers live data download
        },
        "grid_strategy": {
            "type": "simple_grid",
            "spacing": "arithmetic",
            "num_grids": num_grids,
            "range": {
                "top": grid_top,
                "bottom": grid_bottom
            }
        },
        "risk_management": {
            "take_profit": {
                "enabled": False,
                "threshold": 0
            },
            "stop_loss": {
                "enabled": False,
                "threshold": 0
            }
        },
        "logging": {
            "log_level": "INFO",
            "log_to_file": False
        }
    }


async def run_backtest_with_live_data(config):
    """Run a backtest using the provided configuration."""
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        print(f"🚀 Starting backtest with live data from {config['exchange']['name']}")
        print(f"📅 Date range: {config['trading_settings']['period']['start_date']} to {config['trading_settings']['period']['end_date']}")
        print(f"⏰ Timeframe: {config['trading_settings']['timeframe']}")
        print(f"💰 Initial balance: ${config['trading_settings']['initial_balance']:,}")
        print(f"🔢 Grid range: ${config['grid_strategy']['range']['bottom']:,} - ${config['grid_strategy']['range']['top']:,}")
        print()
        
        # Initialize components
        config_manager = ConfigManager(config_path, ConfigValidator())
        event_bus = EventBus()
        notification_handler = NotificationHandler(event_bus, [], TradingMode.BACKTEST)
        
        # Create and run bot
        bot = GridTradingBot(
            config_path=config_path,
            config_manager=config_manager,
            notification_handler=notification_handler,
            event_bus=event_bus,
            save_performance_results_path=None,
            no_plot=True
        )
        
        # Run the backtest
        await bot.run()
        
        # Get results
        strategy = bot.strategy
        performance_report, formatted_orders = strategy.generate_performance_report()
        
        print("\n" + "="*60)
        print("📊 BACKTEST RESULTS")
        print("="*60)
        print(f"📈 Data points processed: {len(strategy.data)}")
        print(f"🔄 Total trades: {performance_report.get('Number of Buy Trades', 0) + performance_report.get('Number of Sell Trades', 0)}")
        print(f"💹 ROI: {performance_report.get('ROI', 'N/A')}")
        print(f"📉 Max Drawdown: {performance_report.get('Max Drawdown', 'N/A')}")
        print(f"💰 Final Balance: {performance_report.get('Final Balance (Fiat)', 'N/A')}")
        print(f"₿ Final Crypto: {performance_report.get('Final Crypto Balance', 'N/A')}")
        
        # Clean up
        await event_bus.shutdown()
        
    finally:
        os.unlink(config_path)


async def main():
    """Run multiple backtest examples with different configurations."""
    
    print("🎯 Grid Trading Bot - Live Data Backtest Examples")
    print("="*60)
    print()
    
    # Example 1: Recent 2-day hourly data from Coinbase
    print("📋 Example 1: Recent 2-day hourly data from Coinbase")
    config1 = create_live_data_config(
        exchange_name="coinbase",
        start_date="2024-12-20T00:00:00Z",
        end_date="2024-12-22T00:00:00Z",
        timeframe="1h",
        initial_balance=10000,
        grid_top=105000,
        grid_bottom=95000,
        num_grids=8
    )
    
    await run_backtest_with_live_data(config1)
    
    print("\n" + "-"*60 + "\n")
    
    # Example 2: Longer period with 6-hour timeframe
    print("📋 Example 2: 5-day period with 6-hour timeframe")
    config2 = create_live_data_config(
        exchange_name="coinbase",
        start_date="2024-12-15T00:00:00Z",
        end_date="2024-12-20T00:00:00Z",
        timeframe="6h",
        initial_balance=25000,
        grid_top=110000,
        grid_bottom=90000,
        num_grids=12
    )
    
    await run_backtest_with_live_data(config2)
    
    print("\n" + "="*60)
    print("✅ All backtest examples completed!")
    print()
    print("💡 Key Points:")
    print("   • Data is downloaded in real-time from the exchange")
    print("   • No CSV files needed - just specify date ranges")
    print("   • Supports multiple exchanges and timeframes")
    print("   • Perfect for testing strategies on any historical period")
    print()
    print("🔧 To customize:")
    print("   • Change exchange_name (coinbase, kraken, bitfinex, etc.)")
    print("   • Adjust date ranges for different periods")
    print("   • Modify timeframes (1h, 6h, 12h, 1d, etc.)")
    print("   • Update grid parameters for different strategies")


if __name__ == "__main__":
    asyncio.run(main())
