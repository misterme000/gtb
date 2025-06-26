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
from core.bot_management.grid_trading_bot import GridTradingBot
from core.bot_management.event_bus import EventBus
from core.bot_management.notification.notification_handler import NotificationHandler


class TestBacktestIntegration:
    """Integration tests for backtesting with real historical data."""
    
    @pytest.fixture
    def sample_historical_data(self):
        """Create sample historical data that mimics real BTC/USDT data."""
        # Use timestamps that correspond to the date range in the config (2024-06-10)
        base_timestamp = 1718064000000  # 2024-06-10 00:00:00 UTC
        return pd.DataFrame({
            'timestamp': [
                base_timestamp + i * 3600000 for i in range(10)  # Hourly intervals
            ],
            'open': [67000.0, 67086.4, 67223.2, 67329.1, 67452.0, 67484.3, 67676.5, 67794.7, 67864.1, 67963.6],
            'high': [67154.5, 67265.4, 67420.3, 67464.7, 67597.5, 67689.7, 67878.5, 67897.6, 68045.3, 68102.4],
            'low': [66896.8, 67000.4, 67156.4, 67222.1, 67357.5, 67409.7, 67623.6, 67732.2, 67839.1, 67885.4],
            'close': [67086.4, 67223.2, 67329.1, 67452.0, 67484.3, 67676.5, 67794.7, 67864.1, 67963.6, 67972.1],
            'volume': [2745, 3293, 2112, 3826, 3082, 2808, 3967, 3800, 1723, 2484]
        })
    
    @pytest.fixture
    def temp_config_and_data(self, sample_historical_data):
        """Create temporary config file and historical data file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create data directory structure
            data_dir = temp_path / "data" / "BTC_USDT" / "2024"
            data_dir.mkdir(parents=True)
            
            # Save historical data to CSV
            data_file = data_dir / "1h.csv"
            sample_historical_data.to_csv(data_file, index=False)
            
            # Create config file
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
                        "end_date": "2024-06-10T09:00:00Z"
                    },
                    "initial_balance": 10000,
                    "historical_data_file": str(data_file)
                },
                "grid_strategy": {
                    "type": "simple_grid",
                    "spacing": "arithmetic",
                    "num_grids": 5,
                    "range": {
                        "top": 68000,
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
            
            config_file = temp_path / "test_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            yield str(config_file), str(data_file)
    
    @pytest.mark.asyncio
    async def test_full_backtest_with_real_data_structure(self, temp_config_and_data):
        """Test complete backtest execution with realistic data structure."""
        config_path, data_file = temp_config_and_data
        
        # Verify data file exists and has correct structure
        assert os.path.exists(data_file)
        df = pd.read_csv(data_file)
        assert len(df) == 10
        assert all(col in df.columns for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
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
        
        # Verify that account values were tracked during backtest
        if 'account_value' in strategy.data.columns:
            account_values = strategy.data['account_value'].dropna()
            assert len(account_values) > 0
            # Account values should be reasonable (not negative, not extremely large)
            assert all(val > 0 for val in account_values)
            assert all(val < 1000000 for val in account_values)  # Sanity check
        
        # Generate and verify performance report
        performance_report, formatted_orders = strategy.generate_performance_report()
        
        # Verify performance report structure
        assert isinstance(performance_report, dict)
        assert isinstance(formatted_orders, list)
        
        # Performance report should contain key metrics
        expected_keys = ['initial_balance', 'final_balance', 'total_return_pct', 'total_trades']
        for key in expected_keys:
            if key in performance_report:
                assert isinstance(performance_report[key], (int, float))
        
        # Clean up
        await event_bus.shutdown()
    
    @pytest.mark.asyncio
    async def test_backtest_data_loading_from_file(self, temp_config_and_data):
        """Test that backtest correctly loads data from historical data file."""
        config_path, data_file = temp_config_and_data
        
        config_manager = ConfigManager(config_path, ConfigValidator())
        
        # Verify config points to correct data file
        assert config_manager.get_historical_data_file() == data_file
        
        # Test exchange service data loading
        from core.services.backtest_exchange_service import BacktestExchangeService
        
        exchange_service = BacktestExchangeService(config_manager)
        
        # Fetch OHLCV data
        ohlcv_data = exchange_service.fetch_ohlcv(
            pair="BTC/USDT",
            timeframe="1h",
            start_date="2024-06-10T00:00:00Z",
            end_date="2024-06-10T09:00:00Z"
        )
        
        # Verify data structure and content
        assert isinstance(ohlcv_data, pd.DataFrame)
        assert len(ohlcv_data) == 10
        assert all(col in ohlcv_data.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        
        # Verify data values are realistic
        assert ohlcv_data['close'].min() > 60000  # BTC price should be reasonable
        assert ohlcv_data['close'].max() < 80000
        assert all(ohlcv_data['volume'] > 0)  # Volume should be positive
        
        # Verify OHLC relationships (high >= open, close; low <= open, close)
        assert all(ohlcv_data['high'] >= ohlcv_data['open'])
        assert all(ohlcv_data['high'] >= ohlcv_data['close'])
        assert all(ohlcv_data['low'] <= ohlcv_data['open'])
        assert all(ohlcv_data['low'] <= ohlcv_data['close'])
    
    def test_historical_data_file_validation(self, temp_config_and_data):
        """Test validation of historical data file format and content."""
        config_path, data_file = temp_config_and_data
        
        # Test with valid file
        df = pd.read_csv(data_file)
        
        # Verify required columns exist
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        assert all(col in df.columns for col in required_columns)
        
        # Verify data types
        assert df['timestamp'].dtype in ['int64', 'float64']  # Unix timestamp
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert pd.api.types.is_numeric_dtype(df[col])
        
        # Verify no missing values in critical columns
        for col in required_columns:
            assert not df[col].isnull().any()
        
        # Verify timestamps are in ascending order
        assert df['timestamp'].is_monotonic_increasing
        
        # Verify OHLC data integrity
        assert all(df['high'] >= df['low'])
        assert all(df['high'] >= df['open'])
        assert all(df['high'] >= df['close'])
        assert all(df['low'] <= df['open'])
        assert all(df['low'] <= df['close'])
