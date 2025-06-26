import pytest
import asyncio
import tempfile
import json
import pandas as pd
from pathlib import Path
from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from core.services.backtest_exchange_service import BacktestExchangeService
from core.bot_management.grid_trading_bot import GridTradingBot
from core.bot_management.event_bus import EventBus
from core.bot_management.notification.notification_handler import NotificationHandler


class TestLiveDataDownload:
    """Tests for downloading real historical data from exchanges."""
    
    def test_backtest_exchange_service_downloads_real_data(self):
        """Test that BacktestExchangeService can download real data from Binance."""
        # Create config WITHOUT historical_data_file to force live data download
        config = {
            "exchange": {
                "name": "coinbase",
                "trading_fee": 0.005,
                "trading_mode": "backtest"
            },
            "pair": {
                "base_currency": "BTC",
                "quote_currency": "USDT"
            },
            "trading_settings": {
                "timeframe": "1h",
                "period": {
                    "start_date": "2024-12-01T00:00:00Z",
                    "end_date": "2024-12-02T23:59:59Z"
                },
                "initial_balance": 10000
                # NOTE: No "historical_data_file" specified - this forces live data download
            },
            "grid_strategy": {
                "type": "simple_grid",
                "spacing": "arithmetic",
                "num_grids": 5,
                "range": {
                    "top": 105000,
                    "bottom": 95000
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=2)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path, ConfigValidator())
            
            # Verify that no historical_data_file is configured
            assert config_manager.get_historical_data_file() is None
            
            # Create exchange service
            exchange_service = BacktestExchangeService(config_manager)
            
            # This should download real data from Coinbase
            print("Downloading real historical data from Coinbase...")
            ohlcv_data = exchange_service.fetch_ohlcv(
                pair="BTC/USDT",
                timeframe="1h",
                start_date="2024-12-01T00:00:00Z",
                end_date="2024-12-02T23:59:59Z"
            )
            
            # Verify data was downloaded
            assert isinstance(ohlcv_data, pd.DataFrame)
            assert len(ohlcv_data) > 0
            assert all(col in ohlcv_data.columns for col in ['open', 'high', 'low', 'close', 'volume'])
            
            # Verify data quality
            assert all(ohlcv_data['high'] >= ohlcv_data['low'])
            assert all(ohlcv_data['volume'] > 0)
            
            # Verify price ranges are realistic for BTC in December 2024
            assert ohlcv_data['close'].min() > 50000  # BTC should be above $50k
            assert ohlcv_data['close'].max() < 150000  # BTC should be below $150k
            
            print(f"✅ Successfully downloaded {len(ohlcv_data)} rows of real BTC/USDT data")
            print(f"📊 Date range: {ohlcv_data.index.min()} to {ohlcv_data.index.max()}")
            print(f"💰 Price range: ${ohlcv_data['low'].min():.2f} - ${ohlcv_data['high'].max():.2f}")
            print(f"📈 Volume range: {ohlcv_data['volume'].min():.2f} - {ohlcv_data['volume'].max():.2f}")
            
        finally:
            import os
            os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_full_backtest_with_downloaded_data(self):
        """Test complete backtest execution with downloaded real data."""
        # Create config WITHOUT historical_data_file
        config = {
            "exchange": {
                "name": "coinbase",
                "trading_fee": 0.005,
                "trading_mode": "backtest"
            },
            "pair": {
                "base_currency": "BTC",
                "quote_currency": "USDT"
            },
            "trading_settings": {
                "timeframe": "1h",
                "period": {
                    "start_date": "2024-12-01T00:00:00Z",
                    "end_date": "2024-12-02T23:59:59Z"
                },
                "initial_balance": 10000
                # No historical_data_file - will download from exchange
            },
            "grid_strategy": {
                "type": "simple_grid",
                "spacing": "arithmetic",
                "num_grids": 10,
                "range": {
                    "top": 105000,
                    "bottom": 95000
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=2)
            config_path = f.name
        
        try:
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
            
            # Verify bot is in backtest mode
            assert bot.trading_mode == TradingMode.BACKTEST
            
            print("🚀 Running backtest with downloaded real data...")
            
            # Run the backtest
            await bot.run()
            
            # Verify that the strategy has processed data
            strategy = bot.strategy
            assert strategy.data is not None
            assert len(strategy.data) > 0
            assert 'close' in strategy.data.columns
            
            # Generate and verify performance report
            performance_report, formatted_orders = strategy.generate_performance_report()
            
            # Verify performance report structure
            assert isinstance(performance_report, dict)
            assert isinstance(formatted_orders, list)
            
            print(f"✅ Backtest completed successfully with downloaded data!")
            print(f"📊 Processed {len(strategy.data)} data points")
            print(f"📈 Performance metrics available: {list(performance_report.keys())}")
            
            # Clean up
            await event_bus.shutdown()
            
        finally:
            import os
            os.unlink(config_path)
    
    def test_different_date_ranges_and_timeframes(self):
        """Test downloading data for different date ranges and timeframes."""
        test_cases = [
            {
                "name": "Recent 1-day hourly data",
                "timeframe": "1h",
                "start_date": "2024-12-20T00:00:00Z",
                "end_date": "2024-12-21T00:00:00Z",
                "expected_min_rows": 20  # At least 20 hours of data
            },
            {
                "name": "Recent 3-day 6-hour data",
                "timeframe": "6h",
                "start_date": "2024-12-18T00:00:00Z",
                "end_date": "2024-12-21T00:00:00Z",
                "expected_min_rows": 10  # At least 10 6-hour candles
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            
            config = {
                "exchange": {
                    "name": "coinbase",
                    "trading_fee": 0.005,
                    "trading_mode": "backtest"
                },
                "pair": {
                    "base_currency": "BTC",
                    "quote_currency": "USDT"
                },
                "trading_settings": {
                    "timeframe": test_case["timeframe"],
                    "period": {
                        "start_date": test_case["start_date"],
                        "end_date": test_case["end_date"]
                    },
                    "initial_balance": 10000
                },
                "grid_strategy": {
                    "type": "simple_grid",
                    "spacing": "arithmetic",
                    "num_grids": 5,
                    "range": {
                        "top": 105000,
                        "bottom": 95000
                    }
                },
                "risk_management": {
                    "take_profit": {"enabled": False, "threshold": 0},
                    "stop_loss": {"enabled": False, "threshold": 0}
                },
                "logging": {
                    "log_level": "INFO",
                    "log_to_file": False
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(config, f, indent=2)
                config_path = f.name
            
            try:
                config_manager = ConfigManager(config_path, ConfigValidator())
                exchange_service = BacktestExchangeService(config_manager)
                
                # Download data
                ohlcv_data = exchange_service.fetch_ohlcv(
                    pair="BTC/USDT",
                    timeframe=test_case["timeframe"],
                    start_date=test_case["start_date"],
                    end_date=test_case["end_date"]
                )
                
                # Verify data
                assert isinstance(ohlcv_data, pd.DataFrame)
                assert len(ohlcv_data) >= test_case["expected_min_rows"]
                assert all(col in ohlcv_data.columns for col in ['open', 'high', 'low', 'close', 'volume'])
                
                print(f"✅ Downloaded {len(ohlcv_data)} rows for {test_case['timeframe']} timeframe")
                
            finally:
                import os
                os.unlink(config_path)
