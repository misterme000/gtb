"""
UI Component Tests for Grid Trading Bot Web UI

Tests for individual UI components including layout, forms, and visualizations.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from web_ui.components.layout import LayoutComponents
from web_ui.components.config_forms import ConfigForms
from web_ui.components.visualizations import VisualizationComponents
from web_ui.components.notifications import notification_system, NotificationType
from web_ui.components.interactive_grid import interactive_grid


class TestLayoutComponents:
    """Test cases for layout components."""
    
    def setup_method(self):
        """Setup test fixtures."""
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
            },
            "risk_management": {
                "take_profit": {"enabled": False, "threshold": 5.0},
                "stop_loss": {"enabled": False, "threshold": 10.0}
            }
        }
        self.layout_components = LayoutComponents(self.sample_config)
    
    def test_create_header(self):
        """Test header creation."""
        header = self.layout_components.create_header()
        
        assert header is not None
        assert isinstance(header, dbc.Navbar)
        
        # Check for brand and title
        header_html = str(header)
        assert "Grid Trading Bot" in header_html
        assert "Configuration" in header_html
    
    def test_create_config_panel(self):
        """Test configuration panel creation."""
        config_panel = self.layout_components.create_config_panel()
        
        assert config_panel is not None
        assert isinstance(config_panel, dbc.Card)
        
        # Check for configuration sections
        panel_html = str(config_panel)
        assert "Configuration" in panel_html
    
    def test_create_visualization_panel(self):
        """Test visualization panel creation."""
        viz_panel = self.layout_components.create_visualization_panel()
        
        assert viz_panel is not None
        assert isinstance(viz_panel, dbc.Card)
        
        # Check for tabs
        panel_html = str(viz_panel)
        assert "Grid Layout" in panel_html
        assert "Interactive Grid" in panel_html
        assert "Price Chart" in panel_html
        assert "Real-time Monitor" in panel_html
        assert "Backtest Preview" in panel_html
    
    def test_create_footer(self):
        """Test footer creation."""
        footer = self.layout_components.create_footer()
        
        assert footer is not None
        
        # Check for action buttons
        footer_html = str(footer)
        assert "validate-btn" in footer_html
        assert "save-btn" in footer_html
        assert "export-btn" in footer_html
    
    def test_create_main_layout(self):
        """Test main layout creation."""
        layout = self.layout_components.create_main_layout()
        
        assert layout is not None
        assert isinstance(layout, dbc.Container)
        
        # Check for data stores
        layout_html = str(layout)
        assert "config-store" in layout_html
        assert "market-data-store" in layout_html
        assert "toast-container" in layout_html


class TestConfigForms:
    """Test cases for configuration forms."""
    
    def setup_method(self):
        """Setup test fixtures."""
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
        self.config_forms = ConfigForms(self.sample_config)
    
    def test_create_exchange_config(self):
        """Test exchange configuration form."""
        exchange_form = self.config_forms.create_exchange_config()
        
        assert exchange_form is not None
        
        # Check for exchange selection
        form_html = str(exchange_form)
        assert "exchange-select" in form_html
        assert "trading-fee-input" in form_html
    
    def test_create_pair_config(self):
        """Test trading pair configuration form."""
        pair_form = self.config_forms.create_pair_config()
        
        assert pair_form is not None
        
        # Check for currency inputs
        form_html = str(pair_form)
        assert "base-currency-input" in form_html
        assert "quote-currency-input" in form_html
    
    def test_create_grid_config(self):
        """Test grid strategy configuration form."""
        grid_form = self.config_forms.create_grid_config()
        
        assert grid_form is not None
        
        # Check for grid parameters
        form_html = str(grid_form)
        assert "num-grids-input" in form_html
        assert "bottom-price-input" in form_html
        assert "top-price-input" in form_html
        assert "spacing-type-select" in form_html
    
    def test_create_trading_config(self):
        """Test trading settings configuration form."""
        trading_form = self.config_forms.create_trading_config()
        
        assert trading_form is not None
        
        # Check for trading parameters
        form_html = str(trading_form)
        assert "timeframe-select" in form_html
        assert "initial-balance-input" in form_html


class TestVisualizationComponents:
    """Test cases for visualization components."""
    
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
        
        # Sample market data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
        self.sample_market_data = {
            'data': [
                {
                    'timestamp': int(date.timestamp() * 1000),
                    'open': 95000 + np.random.randn() * 1000,
                    'high': 96000 + np.random.randn() * 1000,
                    'low': 94000 + np.random.randn() * 1000,
                    'close': 95000 + np.random.randn() * 1000,
                    'volume': 100 + np.random.randn() * 10
                }
                for date in dates
            ],
            'symbol': 'BTC/USD',
            'exchange': 'coinbase',
            'timeframe': '1h'
        }
    
    def test_create_grid_visualization(self):
        """Test grid visualization creation."""
        grid_viz = VisualizationComponents.create_grid_visualization(self.sample_config)
        
        assert grid_viz is not None
        
        # Check for grid elements
        viz_html = str(grid_viz)
        assert "Grid Levels" in viz_html or "grid" in viz_html.lower()
    
    @patch('web_ui.price_service.price_service.get_historical_data_sync')
    def test_create_price_chart_with_data(self, mock_get_data):
        """Test price chart creation with market data."""
        # Mock historical data
        mock_df = pd.DataFrame(self.sample_market_data['data'])
        mock_df['timestamp'] = pd.to_datetime(mock_df['timestamp'], unit='ms')
        mock_df.set_index('timestamp', inplace=True)
        mock_get_data.return_value = mock_df
        
        chart = VisualizationComponents.create_price_chart(self.sample_config, self.sample_market_data)
        
        assert chart is not None
        
        # Should contain a graph component
        chart_html = str(chart)
        assert "dcc.Graph" in chart_html or "graph" in chart_html.lower()
    
    @patch('web_ui.price_service.price_service.get_historical_data_sync')
    def test_create_price_chart_no_data(self, mock_get_data):
        """Test price chart creation with no data."""
        mock_get_data.return_value = None
        
        chart = VisualizationComponents.create_price_chart(self.sample_config, {})
        
        assert chart is not None
        
        # Should show loading or error state
        chart_html = str(chart)
        assert "loading" in chart_html.lower() or "error" in chart_html.lower() or "no data" in chart_html.lower()
    
    @patch('web_ui.services.backtest_service.backtest_service.generate_backtest_preview')
    def test_create_backtest_preview(self, mock_backtest):
        """Test backtest preview creation."""
        # Mock backtest data
        mock_backtest.return_value = {
            "performance_estimate": {
                "total_return": 15.5,
                "max_drawdown": 5.2,
                "sharpe_ratio": 1.8
            },
            "market_analysis": {
                "volatility": 12.3,
                "trend": "sideways"
            },
            "recommendations": [
                "Consider increasing grid levels",
                "Monitor market volatility"
            ]
        }
        
        preview = VisualizationComponents.create_backtest_preview(self.sample_config)
        
        assert preview is not None
        
        # Check for performance metrics
        preview_html = str(preview)
        assert "performance" in preview_html.lower() or "backtest" in preview_html.lower()


class TestNotificationSystem:
    """Test cases for notification system."""
    
    def test_create_toast_container(self):
        """Test toast container creation."""
        container = notification_system.create_toast_container()
        
        assert container is not None
        assert isinstance(container, html.Div)
        assert container.id == "toast-container"
    
    def test_create_toast_success(self):
        """Test success toast creation."""
        toast = notification_system.create_toast(
            "Operation successful",
            NotificationType.SUCCESS,
            title="Success"
        )
        
        assert toast is not None
        assert isinstance(toast, dbc.Toast)
        
        # Check toast properties
        toast_html = str(toast)
        assert "success" in toast_html
        assert "Operation successful" in toast_html
    
    def test_create_toast_error(self):
        """Test error toast creation."""
        toast = notification_system.create_toast(
            "Operation failed",
            NotificationType.ERROR,
            title="Error"
        )
        
        assert toast is not None
        assert isinstance(toast, dbc.Toast)
        
        # Check toast properties
        toast_html = str(toast)
        assert "danger" in toast_html
        assert "Operation failed" in toast_html
    
    def test_create_loading_spinner(self):
        """Test loading spinner creation."""
        spinner = notification_system.create_loading_spinner(
            size="lg",
            text="Loading data..."
        )
        
        assert spinner is not None
        assert isinstance(spinner, html.Div)
        
        # Check for spinner and text
        spinner_html = str(spinner)
        assert "Loading data..." in spinner_html
    
    def test_create_progress_bar(self):
        """Test progress bar creation."""
        progress = notification_system.create_progress_bar(
            value=75,
            max_value=100,
            label="Processing..."
        )
        
        assert progress is not None
        assert isinstance(progress, html.Div)
        
        # Check for progress elements
        progress_html = str(progress)
        assert "Processing..." in progress_html
        assert "75" in progress_html
    
    def test_create_status_indicator(self):
        """Test status indicator creation."""
        indicator = notification_system.create_status_indicator(
            "success",
            "Operation completed",
            details=["Step 1 completed", "Step 2 completed"]
        )
        
        assert indicator is not None
        assert isinstance(indicator, dbc.Alert)
        
        # Check for status content
        indicator_html = str(indicator)
        assert "Operation completed" in indicator_html
        assert "Step 1 completed" in indicator_html


class TestInteractiveGrid:
    """Test cases for interactive grid components."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.sample_config = {
            "grid_strategy": {
                "num_grids": 10,
                "bottom_price": 90000,
                "top_price": 100000,
                "spacing_type": "arithmetic"
            }
        }
        
        self.sample_market_data = {
            'data': [{'close': 95000}],
            'symbol': 'BTC/USD'
        }
    
    def test_create_interactive_grid_editor(self):
        """Test interactive grid editor creation."""
        editor = interactive_grid.create_interactive_grid_editor(self.sample_config)
        
        assert editor is not None
        assert isinstance(editor, dbc.Card)
        
        # Check for interactive elements
        editor_html = str(editor)
        assert "interactive" in editor_html.lower()
        assert "grid" in editor_html.lower()
    
    def test_create_real_time_price_overlay(self):
        """Test real-time price overlay creation."""
        overlay = interactive_grid.create_real_time_price_overlay(
            self.sample_config, 
            self.sample_market_data
        )
        
        assert overlay is not None
        
        # Check for price display elements
        overlay_html = str(overlay)
        assert "price" in overlay_html.lower() or "btc" in overlay_html.lower()
    
    def test_generate_grid_levels_arithmetic(self):
        """Test arithmetic grid level generation."""
        levels = interactive_grid._generate_grid_levels(10, 90000, 100000, "arithmetic")
        
        assert len(levels) == 10
        assert levels[0] == 90000
        assert levels[-1] == 100000
        
        # Check arithmetic progression
        step = (100000 - 90000) / 9
        for i in range(1, len(levels)):
            expected = 90000 + (step * i)
            assert abs(levels[i] - expected) < 0.01
    
    def test_generate_grid_levels_geometric(self):
        """Test geometric grid level generation."""
        levels = interactive_grid._generate_grid_levels(10, 90000, 100000, "geometric")
        
        assert len(levels) == 10
        assert levels[0] == 90000
        assert levels[-1] == 100000
        
        # Check geometric progression
        ratio = (100000 / 90000) ** (1 / 9)
        for i in range(1, len(levels)):
            expected = 90000 * (ratio ** i)
            assert abs(levels[i] - expected) < 0.01
    
    def test_create_grid_level_indicators(self):
        """Test grid level indicators creation."""
        levels = [90000, 92000, 94000, 96000, 98000, 100000]
        current_price = 95000
        
        indicators = interactive_grid._create_grid_level_indicators(levels, current_price)
        
        assert len(indicators) == len(levels)
        assert all(isinstance(indicator, dbc.Row) for indicator in indicators)
        
        # Check that indicators contain price information
        indicators_html = str(indicators)
        assert "90000" in indicators_html
        assert "100000" in indicators_html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
