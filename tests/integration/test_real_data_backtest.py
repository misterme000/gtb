import pytest
import asyncio
import os
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


class TestRealDataBacktest:
    """Tests for backtesting with actual historical data files."""
    
    def test_load_existing_historical_data(self):
        """Test loading data from existing historical data files."""
        # Check if the actual data files exist
        data_file_2024 = "data/BTC_USDT/2024/1h.csv"
        data_file_2023 = "data/BTC_USDT/2023/1h.csv"
        
        if not os.path.exists(data_file_2024):
            pytest.skip(f"Historical data file {data_file_2024} not found")
        
        # Read and verify the data structure
        df = pd.read_csv(data_file_2024)
        
        # Verify required columns exist
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        assert all(col in df.columns for col in required_columns)
        
        # Verify data types and content
        assert len(df) > 0
        assert df['timestamp'].dtype in ['int64', 'float64']
        
        # Verify OHLC relationships
        assert all(df['high'] >= df['low'])
        assert all(df['high'] >= df['open'])
        assert all(df['high'] >= df['close'])
        assert all(df['low'] <= df['open'])
        assert all(df['low'] <= df['close'])
        
        # Verify volume is positive
        assert all(df['volume'] > 0)
        
        print(f"Successfully validated {len(df)} rows of historical data")
        print(f"Date range: {pd.to_datetime(df['timestamp'].min(), unit='ms')} to {pd.to_datetime(df['timestamp'].max(), unit='ms')}")
        print(f"Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    
    def test_backtest_exchange_service_with_real_data(self):
        """Test BacktestExchangeService with actual historical data."""
        data_file = "data/BTC_USDT/2024/1h.csv"
        
        if not os.path.exists(data_file):
            pytest.skip(f"Historical data file {data_file} not found")
        
        # Create a temporary config that points to the real data file
        config = {
            "exchange": {
                "name": "binance",
                "trading_fee": 0.001,
                "trading_mode": "backtest"
            },
            "pair": {
                "base_currency": "BTC",
                "quote_currency": "USDT"
            },
            "trading_settings": {
                "timeframe": "1h",
                "period": {
                    "start_date": "2024-06-10T00:00:00Z",
                    "end_date": "2024-06-12T23:59:59Z"
                },
                "initial_balance": 10000,
                "historical_data_file": data_file
            },
            "grid_strategy": {
                "type": "simple_grid",
                "spacing": "arithmetic",
                "num_grids": 5,
                "range": {
                    "top": 74000,
                    "bottom": 67000
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
            exchange_service = BacktestExchangeService(config_manager)
            
            # Fetch OHLCV data for the specified period
            ohlcv_data = exchange_service.fetch_ohlcv(
                pair="BTC/USDT",
                timeframe="1h",
                start_date="2024-06-10T00:00:00Z",
                end_date="2024-06-12T23:59:59Z"
            )
            
            # Verify data was loaded
            assert isinstance(ohlcv_data, pd.DataFrame)
            assert len(ohlcv_data) > 0
            assert all(col in ohlcv_data.columns for col in ['open', 'high', 'low', 'close', 'volume'])
            
            # Verify data quality
            assert all(ohlcv_data['high'] >= ohlcv_data['low'])
            assert all(ohlcv_data['volume'] > 0)
            
            print(f"Successfully loaded {len(ohlcv_data)} rows of OHLCV data")
            print(f"Price range: ${ohlcv_data['low'].min():.2f} - ${ohlcv_data['high'].max():.2f}")
            
        finally:
            os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_full_backtest_with_real_data(self):
        """Test complete backtest execution with real historical data."""
        data_file = "data/BTC_USDT/2024/1h.csv"
        
        if not os.path.exists(data_file):
            pytest.skip(f"Historical data file {data_file} not found")
        
        # Create config for backtest
        config = {
            "exchange": {
                "name": "binance",
                "trading_fee": 0.001,
                "trading_mode": "backtest"
            },
            "pair": {
                "base_currency": "BTC",
                "quote_currency": "USDT"
            },
            "trading_settings": {
                "timeframe": "1h",
                "period": {
                    "start_date": "2024-06-10T00:00:00Z",
                    "end_date": "2024-06-12T23:59:59Z"
                },
                "initial_balance": 10000,
                "historical_data_file": data_file
            },
            "grid_strategy": {
                "type": "simple_grid",
                "spacing": "arithmetic",
                "num_grids": 10,
                "range": {
                    "top": 74000,
                    "bottom": 67000
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
            
            print(f"Backtest completed successfully!")
            print(f"Processed {len(strategy.data)} data points")
            print(f"Performance metrics: {list(performance_report.keys())}")
            
            # Clean up
            await event_bus.shutdown()
            
        finally:
            os.unlink(config_path)
