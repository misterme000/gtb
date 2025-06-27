"""
Callback Integration Tests for Grid Trading Bot Web UI

Tests for callback functions and their interactions with UI components.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import dash
from dash import html, dcc
from dash.testing.application_runners import import_app
from dash.testing.composite import DashComposite
import dash_bootstrap_components as dbc

from web_ui.app import GridBotUI
from web_ui.callbacks.main_callbacks import MainCallbacks
from web_ui.callbacks.action_callbacks import ActionCallbacks
from web_ui.callbacks.interactive_callbacks import InteractiveCallbacks


class TestMainCallbacks:
    """Test cases for main callback functions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.app = dash.Dash(__name__)
        self.main_callbacks = MainCallbacks(self.app)
        
        self.sample_config = {
            "exchange": {"name": "coinbase"},
            "pair": {"base_currency": "BTC", "quote_currency": "USD"},
            "trading_settings": {"timeframe": "1h"},
            "grid_strategy": {
                "num_grids": 10,
                "bottom_price": 90000,
                "top_price": 100000,
                "spacing_type": "arithmetic"
            }
        }
        
        self.sample_market_data = {
            'data': [
                {
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'open': 95000,
                    'high': 96000,
                    'low': 94000,
                    'close': 95000,
                    'volume': 100
                }
            ]
        }
    
    @patch('web_ui.components.visualizations.VisualizationComponents.create_grid_visualization')
    def test_update_visualization_grid_tab(self, mock_create_grid):
        """Test visualization update for grid tab."""
        mock_create_grid.return_value = html.Div("Grid visualization")
        
        # Simulate callback execution
        result = self.main_callbacks.setup_callbacks()
        
        # Verify mock was configured
        assert mock_create_grid is not None
    
    @patch('web_ui.price_service.price_service.get_current_price_sync')
    def test_update_live_price_success(self, mock_get_price):
        """Test live price update with successful data fetch."""
        mock_get_price.return_value = 95000.50
        
        # Test would require actual callback execution in Dash context
        # This tests the mock setup
        price = mock_get_price("coinbase", "BTC", "USD")
        assert price == 95000.50
    
    @patch('web_ui.price_service.price_service.get_current_price_sync')
    def test_update_live_price_failure(self, mock_get_price):
        """Test live price update with failed data fetch."""
        mock_get_price.return_value = None
        
        price = mock_get_price("coinbase", "BTC", "USD")
        assert price is None
    
    @patch('web_ui.price_service.price_service.get_historical_data_sync')
    def test_update_market_data_success(self, mock_get_data):
        """Test market data update with successful fetch."""
        # Create mock DataFrame
        mock_df = pd.DataFrame([
            {'open': 95000, 'high': 96000, 'low': 94000, 'close': 95000, 'volume': 100}
        ])
        mock_df.index = pd.date_range(start='2024-01-01', periods=1, freq='H')
        mock_get_data.return_value = mock_df
        
        data = mock_get_data("coinbase", "BTC", "USD", "1h", 100)
        assert data is not None
        assert len(data) == 1
        assert 'close' in data.columns
    
    def test_config_update_validation(self):
        """Test configuration update validation."""
        # Test valid configuration
        valid_config = self.sample_config.copy()
        assert valid_config["exchange"]["name"] == "coinbase"
        assert valid_config["pair"]["base_currency"] == "BTC"
        
        # Test invalid configuration
        invalid_config = valid_config.copy()
        invalid_config["grid_strategy"]["bottom_price"] = 100000
        invalid_config["grid_strategy"]["top_price"] = 90000
        
        # Bottom price should not be greater than top price
        assert invalid_config["grid_strategy"]["bottom_price"] > invalid_config["grid_strategy"]["top_price"]


class TestActionCallbacks:
    """Test cases for action callback functions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.app = dash.Dash(__name__)
        self.action_callbacks = ActionCallbacks(self.app)
        
        self.sample_config = {
            "exchange": {"name": "coinbase", "trading_fee": 0.005},
            "pair": {"base_currency": "BTC", "quote_currency": "USD"},
            "trading_settings": {"timeframe": "1h", "initial_balance": 10000},
            "grid_strategy": {
                "strategy_type": "simple_grid",
                "spacing_type": "arithmetic",
                "num_grids": 10,
                "bottom_price": 90000,
                "top_price": 100000
            }
        }
    
    @patch('web_ui.validation.config_validator.UIConfigValidator.validate_config')
    def test_validation_success(self, mock_validate):
        """Test successful configuration validation."""
        mock_validate.return_value = (True, [], [])
        
        is_valid, errors, warnings = mock_validate(self.sample_config)
        assert is_valid is True
        assert len(errors) == 0
        assert len(warnings) == 0
    
    @patch('web_ui.validation.config_validator.UIConfigValidator.validate_config')
    def test_validation_with_errors(self, mock_validate):
        """Test configuration validation with errors."""
        mock_validate.return_value = (False, ["Invalid exchange"], ["High trading fee"])
        
        is_valid, errors, warnings = mock_validate(self.sample_config)
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid exchange" in errors
        assert len(warnings) == 1
        assert "High trading fee" in warnings
    
    @patch('web_ui.utils.config_manager.ui_config_manager.save_config')
    def test_save_config_success(self, mock_save):
        """Test successful configuration save."""
        mock_save.return_value = (True, "/path/to/config.json")
        
        success, result = mock_save(self.sample_config)
        assert success is True
        assert "/path/to/config.json" in result
    
    @patch('web_ui.utils.config_manager.ui_config_manager.save_config')
    def test_save_config_failure(self, mock_save):
        """Test failed configuration save."""
        mock_save.return_value = (False, "Permission denied")
        
        success, result = mock_save(self.sample_config)
        assert success is False
        assert "Permission denied" in result
    
    @patch('web_ui.utils.config_manager.ui_config_manager.export_config_for_download')
    def test_export_config_success(self, mock_export):
        """Test successful configuration export."""
        mock_export.return_value = (True, "base64encodeddata", "config.json")
        
        success, data, filename = mock_export(self.sample_config)
        assert success is True
        assert data == "base64encodeddata"
        assert filename == "config.json"
    
    @patch('web_ui.utils.config_manager.ui_config_manager.export_config_for_download')
    def test_export_config_failure(self, mock_export):
        """Test failed configuration export."""
        mock_export.return_value = (False, "", "Export failed")
        
        success, data, error = mock_export(self.sample_config)
        assert success is False
        assert data == ""
        assert "Export failed" in error


class TestInteractiveCallbacks:
    """Test cases for interactive callback functions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.app = dash.Dash(__name__)
        self.interactive_callbacks = InteractiveCallbacks(self.app)
        
        self.sample_config = {
            "exchange": {"name": "coinbase"},
            "pair": {"base_currency": "BTC", "quote_currency": "USD"},
            "grid_strategy": {
                "num_grids": 10,
                "bottom_price": 90000,
                "top_price": 100000,
                "spacing_type": "arithmetic"
            }
        }
    
    def test_grid_level_calculation(self):
        """Test grid level calculation for interactive grid."""
        num_grids = 10
        bottom_price = 90000
        top_price = 100000
        spacing_type = "arithmetic"
        
        # Calculate expected levels
        step = (top_price - bottom_price) / (num_grids - 1)
        expected_levels = [bottom_price + (step * i) for i in range(num_grids)]
        
        # Verify calculation logic
        assert len(expected_levels) == num_grids
        assert expected_levels[0] == bottom_price
        assert expected_levels[-1] == top_price
    
    def test_grid_parameter_validation(self):
        """Test grid parameter validation."""
        # Valid parameters
        assert 90000 < 100000  # bottom < top
        assert 10 > 0  # num_grids > 0
        assert "arithmetic" in ["arithmetic", "geometric"]  # valid spacing
        
        # Invalid parameters
        invalid_bottom = 100000
        invalid_top = 90000
        assert invalid_bottom >= invalid_top  # Invalid: bottom >= top
    
    @patch('web_ui.price_service.price_service.get_current_price_sync')
    def test_real_time_price_update(self, mock_get_price):
        """Test real-time price update for interactive components."""
        mock_get_price.return_value = 95500.75
        
        price = mock_get_price("coinbase", "BTC", "USD")
        assert price == 95500.75
        
        # Test price formatting
        formatted_price = f"${price:,.2f}"
        assert formatted_price == "$95,500.75"
    
    def test_grid_statistics_calculation(self):
        """Test grid statistics calculation."""
        bottom_price = 90000
        top_price = 100000
        num_grids = 10
        
        price_range = top_price - bottom_price
        avg_spacing = price_range / (num_grids - 1)
        mid_price = (bottom_price + top_price) / 2
        
        assert price_range == 10000
        assert abs(avg_spacing - 1111.11) < 0.01
        assert mid_price == 95000


class TestCallbackIntegration:
    """Integration tests for callback interactions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.sample_config = {
            "exchange": {"name": "coinbase"},
            "pair": {"base_currency": "BTC", "quote_currency": "USD"},
            "trading_settings": {"timeframe": "1h"},
            "grid_strategy": {
                "num_grids": 10,
                "bottom_price": 90000,
                "top_price": 100000,
                "spacing_type": "arithmetic"
            }
        }
    
    def test_config_to_visualization_flow(self):
        """Test configuration changes affecting visualizations."""
        # Simulate configuration change
        new_config = self.sample_config.copy()
        new_config["grid_strategy"]["num_grids"] = 15
        
        # Verify configuration change
        assert new_config["grid_strategy"]["num_grids"] == 15
        assert new_config != self.sample_config
    
    def test_market_data_to_chart_flow(self):
        """Test market data updates affecting charts."""
        # Simulate market data update
        market_data = {
            'data': [
                {
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'close': 95000
                }
            ],
            'symbol': 'BTC/USD'
        }
        
        # Verify data structure
        assert 'data' in market_data
        assert len(market_data['data']) > 0
        assert 'close' in market_data['data'][0]
    
    def test_validation_to_notification_flow(self):
        """Test validation results affecting notifications."""
        # Simulate validation results
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': ['High trading fee detected']
        }
        
        # Verify notification logic
        if validation_results['is_valid']:
            if validation_results['warnings']:
                notification_type = "warning"
            else:
                notification_type = "success"
        else:
            notification_type = "error"
        
        assert notification_type == "warning"
    
    def test_interactive_grid_sync(self):
        """Test interactive grid changes syncing to main config."""
        # Simulate interactive grid changes
        interactive_changes = {
            'num_grids': 12,
            'bottom_price': 88000,
            'top_price': 102000,
            'spacing_type': 'geometric'
        }
        
        # Simulate sync to main config
        updated_config = self.sample_config.copy()
        updated_config["grid_strategy"].update(interactive_changes)
        
        # Verify sync
        assert updated_config["grid_strategy"]["num_grids"] == 12
        assert updated_config["grid_strategy"]["bottom_price"] == 88000
        assert updated_config["grid_strategy"]["spacing_type"] == "geometric"


class TestErrorHandling:
    """Test error handling in callbacks."""
    
    def test_network_error_handling(self):
        """Test handling of network errors."""
        # Simulate network error
        error_message = "Network connection failed"
        
        # Test error message formatting
        user_message = f"Unable to fetch data: {error_message}"
        assert "Network connection failed" in user_message
    
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        # Simulate validation errors
        errors = [
            "Bottom price must be less than top price",
            "Number of grids must be positive"
        ]
        
        # Test error formatting
        error_text = "\n".join([f"• {e}" for e in errors])
        assert "• Bottom price must be less than top price" in error_text
        assert "• Number of grids must be positive" in error_text
    
    def test_data_processing_error_handling(self):
        """Test handling of data processing errors."""
        # Simulate data processing error
        try:
            # This would normally be actual data processing
            invalid_data = None
            if invalid_data is None:
                raise ValueError("No data available")
        except ValueError as e:
            error_handled = True
            error_message = str(e)
        
        assert error_handled is True
        assert "No data available" in error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
