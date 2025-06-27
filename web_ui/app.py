#!/usr/bin/env python3
"""
Grid Trading Bot Web UI - Refactored

A comprehensive web interface for configuring and managing the grid trading bot.
Built with Dash and Plotly for interactive visualizations.

This is the refactored version with organized components and fixed duplicate callbacks.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

import dash
import dash_bootstrap_components as dbc
from dotenv import load_dotenv

# Import organized components
from web_ui.components.layout import LayoutComponents
from web_ui.callbacks.main_callbacks import MainCallbacks
from web_ui.callbacks.action_callbacks import ActionCallbacks
from web_ui.callbacks.interactive_callbacks import InteractiveCallbacks

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GridBotUI:
    """Main class for the Grid Trading Bot Web UI - Refactored Version."""
    
    def __init__(self):
        """Initialize the Grid Bot UI."""
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
            ],
            title="Grid Trading Bot Configuration",
            suppress_callback_exceptions=True
        )
        
        # Default configuration
        self.default_config = self._load_default_config()
        self.current_config = self.default_config.copy()
        
        # Setup the layout and callbacks
        self._setup_layout()
        self._setup_callbacks()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
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
                    "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "initial_balance": 10000
            },
            "grid_strategy": {
                "type": "simple_grid",
                "spacing": "arithmetic",
                "num_grids": 10,
                "range": {
                    "top": 100000,
                    "bottom": 90000
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
    
    def _setup_layout(self):
        """Setup the main layout of the application."""
        layout_components = LayoutComponents(self.current_config)
        self.app.layout = layout_components.create_main_layout()
    
    def _setup_callbacks(self):
        """Setup all the callbacks for the application."""
        # Initialize callback classes
        main_callbacks = MainCallbacks(self.app)
        action_callbacks = ActionCallbacks(self.app)
        interactive_callbacks = InteractiveCallbacks(self.app)

        logger.info("All callbacks initialized successfully")
        logger.info(f"Initialized: {type(main_callbacks).__name__}, {type(action_callbacks).__name__}, {type(interactive_callbacks).__name__}")
    
    def run(self, debug=True, port=8050):
        """Run the Dash application."""
        logger.info(f"Starting Grid Trading Bot UI on http://localhost:{port}")
        self.app.run_server(debug=debug, port=port, host='0.0.0.0')


if __name__ == "__main__":
    ui = GridBotUI()
    ui.run(debug=True)
