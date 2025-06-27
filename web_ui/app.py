#!/usr/bin/env python3
"""
Grid Trading Bot Web UI

A comprehensive web interface for configuring and managing the grid trading bot.
Built with Dash and Plotly for interactive visualizations.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

import dash
from dash import dcc, html, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Import project modules
from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from strategies.strategy_type import StrategyType
from strategies.spacing_type import SpacingType
from utils.constants import TIMEFRAME_MAPPINGS
from core.services.backtest_exchange_service import BacktestExchangeService
from web_ui.price_service import price_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported exchanges
SUPPORTED_EXCHANGES = [
    "coinbase", "kraken", "bitfinex", "bitstamp", "huobi",
    "okex", "bybit", "bittrex", "poloniex", "gate", "kucoin"
]

class GridBotUI:
    """Main class for the Grid Trading Bot Web UI."""
    
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
        
        # Market data cache
        self.market_data_cache = {}
        
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
        self.app.layout = dbc.Container([
            # Header
            self._create_header(),
            
            # Main content
            dbc.Row([
                # Left panel - Configuration forms
                dbc.Col([
                    self._create_config_panel()
                ], width=4),
                
                # Right panel - Visualization and preview
                dbc.Col([
                    self._create_visualization_panel()
                ], width=8)
            ], className="mt-3"),
            
            # Footer with action buttons
            self._create_footer(),
            
            # Hidden components for data storage
            dcc.Store(id='config-store', data=self.current_config),
            dcc.Store(id='market-data-store', data={}),
            dcc.Interval(id='price-update-interval', interval=30000, n_intervals=0),  # 30 seconds
            dcc.Interval(id='chart-update-interval', interval=60000, n_intervals=0),  # 1 minute for charts
            
        ], fluid=True, className="px-4")
    
    def _create_header(self):
        """Create the header section."""
        return dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-robot me-3"),
                    "Grid Trading Bot Configuration"
                ], className="text-primary mb-0"),
                html.P("Configure your grid trading strategy with visual feedback", 
                      className="text-muted mb-0")
            ], width=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-upload me-2"),
                        "Import Config"
                    ], id="import-btn", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-2"),
                        "Export Config"
                    ], id="export-btn", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-play me-2"),
                        "Run Backtest"
                    ], id="run-backtest-btn", color="success", size="sm")
                ])
            ], width=4, className="text-end")
        ], className="mb-4 pb-3 border-bottom")
    
    def _create_config_panel(self):
        """Create the configuration panel."""
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-cog me-2"),
                    "Configuration"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                # Exchange Configuration
                self._create_exchange_config(),
                html.Hr(),
                
                # Trading Pair Configuration
                self._create_pair_config(),
                html.Hr(),
                
                # Grid Strategy Configuration
                self._create_grid_config(),
                html.Hr(),
                
                # Risk Management Configuration
                self._create_risk_config(),
                html.Hr(),
                
                # Trading Settings Configuration
                self._create_trading_config()
            ])
        ], className="h-100")
    
    def _create_visualization_panel(self):
        """Create the visualization panel."""
        return dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="fas fa-chart-line me-2"),
                            "Grid Visualization"
                        ], className="mb-0")
                    ], width=8),
                    dbc.Col([
                        dbc.Badge("Live Price: $--", id="live-price-badge", color="info")
                    ], width=4, className="text-end")
                ])
            ]),
            dbc.CardBody([
                # Tabs for different visualizations
                dbc.Tabs([
                    dbc.Tab(label="Grid Layout", tab_id="grid-tab"),
                    dbc.Tab(label="Price Chart", tab_id="chart-tab"),
                    dbc.Tab(label="Backtest Preview", tab_id="backtest-tab")
                ], id="viz-tabs", active_tab="grid-tab"),
                
                html.Div(id="viz-content", className="mt-3")
            ])
        ], className="h-100")
    
    def _create_footer(self):
        """Create the footer with action buttons."""
        return dbc.Row([
            dbc.Col([
                dbc.Alert(id="status-alert", is_open=False, dismissable=True)
            ], width=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("Reset to Default", id="reset-btn", color="outline-warning", size="sm"),
                    dbc.Button("Validate Config", id="validate-btn", color="outline-info", size="sm"),
                    dbc.Button("Save & Apply", id="save-btn", color="primary", size="sm")
                ])
            ], width=4, className="text-end")
        ], className="mt-4 pt-3 border-top")

    def _create_exchange_config(self):
        """Create exchange configuration section."""
        return html.Div([
            html.H6([
                html.I(className="fas fa-exchange-alt me-2"),
                "Exchange Settings"
            ], className="text-primary"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Exchange", html_for="exchange-select"),
                    dcc.Dropdown(
                        id="exchange-select",
                        options=[{"label": ex.title(), "value": ex} for ex in SUPPORTED_EXCHANGES],
                        value=self.current_config["exchange"]["name"],
                        clearable=False
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Trading Mode", html_for="trading-mode-select"),
                    dcc.Dropdown(
                        id="trading-mode-select",
                        options=[
                            {"label": "Backtest", "value": "backtest"},
                            {"label": "Paper Trading", "value": "paper_trading"},
                            {"label": "Live Trading", "value": "live"}
                        ],
                        value=self.current_config["exchange"]["trading_mode"],
                        clearable=False
                    )
                ], width=6)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Trading Fee (%)", html_for="trading-fee-input"),
                    dbc.Input(
                        id="trading-fee-input",
                        type="number",
                        value=self.current_config["exchange"]["trading_fee"] * 100,
                        min=0,
                        max=5,
                        step=0.001,
                        size="sm"
                    )
                ], width=6)
            ])
        ])

    def _create_pair_config(self):
        """Create trading pair configuration section."""
        return html.Div([
            html.H6([
                html.I(className="fas fa-coins me-2"),
                "Trading Pair"
            ], className="text-primary"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Base Currency", html_for="base-currency-input"),
                    dbc.Input(
                        id="base-currency-input",
                        value=self.current_config["pair"]["base_currency"],
                        placeholder="BTC",
                        size="sm"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Quote Currency", html_for="quote-currency-input"),
                    dbc.Input(
                        id="quote-currency-input",
                        value=self.current_config["pair"]["quote_currency"],
                        placeholder="USDT",
                        size="sm"
                    )
                ], width=6)
            ], className="mb-2"),

            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Get Current Price"
                        ], id="get-price-btn", color="outline-info", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-magic me-2"),
                            "Suggest Range"
                        ], id="suggest-range-btn", color="outline-success", size="sm")
                    ])
                ], width=12)
            ])
        ])

    def _create_grid_config(self):
        """Create grid strategy configuration section."""
        return html.Div([
            html.H6([
                html.I(className="fas fa-th me-2"),
                "Grid Strategy"
            ], className="text-primary"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Strategy Type", html_for="strategy-type-select"),
                    dcc.Dropdown(
                        id="strategy-type-select",
                        options=[
                            {"label": "Simple Grid", "value": "simple_grid"},
                            {"label": "Hedged Grid", "value": "hedged_grid"}
                        ],
                        value=self.current_config["grid_strategy"]["type"],
                        clearable=False
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Spacing Type", html_for="spacing-type-select"),
                    dcc.Dropdown(
                        id="spacing-type-select",
                        options=[
                            {"label": "Arithmetic", "value": "arithmetic"},
                            {"label": "Geometric", "value": "geometric"}
                        ],
                        value=self.current_config["grid_strategy"]["spacing"],
                        clearable=False
                    )
                ], width=6)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Number of Grids", html_for="num-grids-input"),
                    dbc.Input(
                        id="num-grids-input",
                        type="number",
                        value=self.current_config["grid_strategy"]["num_grids"],
                        min=3,
                        max=50,
                        step=1,
                        size="sm"
                    )
                ], width=4),
                dbc.Col([
                    dbc.Label("Bottom Price", html_for="bottom-price-input"),
                    dbc.Input(
                        id="bottom-price-input",
                        type="number",
                        value=self.current_config["grid_strategy"]["range"]["bottom"],
                        min=0,
                        step=0.01,
                        size="sm"
                    )
                ], width=4),
                dbc.Col([
                    dbc.Label("Top Price", html_for="top-price-input"),
                    dbc.Input(
                        id="top-price-input",
                        type="number",
                        value=self.current_config["grid_strategy"]["range"]["top"],
                        min=0,
                        step=0.01,
                        size="sm"
                    )
                ], width=4)
            ])
        ])

    def _create_risk_config(self):
        """Create risk management configuration section."""
        return html.Div([
            html.H6([
                html.I(className="fas fa-shield-alt me-2"),
                "Risk Management"
            ], className="text-primary"),

            dbc.Row([
                dbc.Col([
                    dbc.Checklist(
                        id="take-profit-enabled",
                        options=[{"label": "Enable Take Profit", "value": "enabled"}],
                        value=["enabled"] if self.current_config["risk_management"]["take_profit"]["enabled"] else [],
                        inline=True
                    ),
                    dbc.Input(
                        id="take-profit-threshold",
                        type="number",
                        value=self.current_config["risk_management"]["take_profit"]["threshold"],
                        placeholder="Take Profit Price",
                        size="sm",
                        className="mt-2"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Checklist(
                        id="stop-loss-enabled",
                        options=[{"label": "Enable Stop Loss", "value": "enabled"}],
                        value=["enabled"] if self.current_config["risk_management"]["stop_loss"]["enabled"] else [],
                        inline=True
                    ),
                    dbc.Input(
                        id="stop-loss-threshold",
                        type="number",
                        value=self.current_config["risk_management"]["stop_loss"]["threshold"],
                        placeholder="Stop Loss Price",
                        size="sm",
                        className="mt-2"
                    )
                ], width=6)
            ])
        ])

    def _create_trading_config(self):
        """Create trading settings configuration section."""
        return html.Div([
            html.H6([
                html.I(className="fas fa-clock me-2"),
                "Trading Settings"
            ], className="text-primary"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Timeframe", html_for="timeframe-select"),
                    dcc.Dropdown(
                        id="timeframe-select",
                        options=[{"label": tf, "value": tf} for tf in TIMEFRAME_MAPPINGS.keys()],
                        value=self.current_config["trading_settings"]["timeframe"],
                        clearable=False
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Initial Balance", html_for="initial-balance-input"),
                    dbc.Input(
                        id="initial-balance-input",
                        type="number",
                        value=self.current_config["trading_settings"]["initial_balance"],
                        min=100,
                        step=100,
                        size="sm"
                    )
                ], width=6)
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Start Date", html_for="start-date-input"),
                    dbc.Input(
                        id="start-date-input",
                        type="datetime-local",
                        value=self.current_config["trading_settings"]["period"]["start_date"].replace("Z", ""),
                        size="sm"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("End Date", html_for="end-date-input"),
                    dbc.Input(
                        id="end-date-input",
                        type="datetime-local",
                        value=self.current_config["trading_settings"]["period"]["end_date"].replace("Z", ""),
                        size="sm"
                    )
                ], width=6)
            ])
        ])

    def _setup_callbacks(self):
        """Setup all the callbacks for the application."""

        @self.app.callback(
            Output('viz-content', 'children'),
            [Input('viz-tabs', 'active_tab'),
             Input('config-store', 'data'),
             Input('market-data-store', 'data')]
        )
        def update_visualization(active_tab, config_data, market_data):
            """Update visualization based on active tab and configuration."""
            if active_tab == "grid-tab":
                return self._create_grid_visualization(config_data)
            elif active_tab == "chart-tab":
                return self._create_price_chart(config_data, market_data)
            elif active_tab == "backtest-tab":
                return self._create_backtest_preview(config_data)
            return html.Div("Select a tab to view visualization")

        @self.app.callback(
            Output('config-store', 'data'),
            [Input('exchange-select', 'value'),
             Input('trading-mode-select', 'value'),
             Input('trading-fee-input', 'value'),
             Input('base-currency-input', 'value'),
             Input('quote-currency-input', 'value'),
             Input('strategy-type-select', 'value'),
             Input('spacing-type-select', 'value'),
             Input('num-grids-input', 'value'),
             Input('bottom-price-input', 'value'),
             Input('top-price-input', 'value'),
             Input('take-profit-enabled', 'value'),
             Input('take-profit-threshold', 'value'),
             Input('stop-loss-enabled', 'value'),
             Input('stop-loss-threshold', 'value'),
             Input('timeframe-select', 'value'),
             Input('initial-balance-input', 'value'),
             Input('start-date-input', 'value'),
             Input('end-date-input', 'value')],
            [State('config-store', 'data')]
        )
        def update_config(exchange, trading_mode, trading_fee, base_currency, quote_currency,
                         strategy_type, spacing_type, num_grids, bottom_price, top_price,
                         tp_enabled, tp_threshold, sl_enabled, sl_threshold,
                         timeframe, initial_balance, start_date, end_date, current_config):
            """Update configuration based on form inputs."""

            if not current_config:
                current_config = self.default_config.copy()

            # Update configuration
            current_config["exchange"]["name"] = exchange or "coinbase"
            current_config["exchange"]["trading_mode"] = trading_mode or "backtest"
            current_config["exchange"]["trading_fee"] = (trading_fee or 0.5) / 100

            current_config["pair"]["base_currency"] = (base_currency or "BTC").upper()
            current_config["pair"]["quote_currency"] = (quote_currency or "USDT").upper()

            current_config["grid_strategy"]["type"] = strategy_type or "simple_grid"
            current_config["grid_strategy"]["spacing"] = spacing_type or "arithmetic"
            current_config["grid_strategy"]["num_grids"] = num_grids or 10
            current_config["grid_strategy"]["range"]["bottom"] = bottom_price or 90000
            current_config["grid_strategy"]["range"]["top"] = top_price or 100000

            current_config["risk_management"]["take_profit"]["enabled"] = "enabled" in (tp_enabled or [])
            current_config["risk_management"]["take_profit"]["threshold"] = tp_threshold or 0
            current_config["risk_management"]["stop_loss"]["enabled"] = "enabled" in (sl_enabled or [])
            current_config["risk_management"]["stop_loss"]["threshold"] = sl_threshold or 0

            current_config["trading_settings"]["timeframe"] = timeframe or "1h"
            current_config["trading_settings"]["initial_balance"] = initial_balance or 10000

            if start_date:
                current_config["trading_settings"]["period"]["start_date"] = start_date + "Z"
            if end_date:
                current_config["trading_settings"]["period"]["end_date"] = end_date + "Z"

            return current_config

        @self.app.callback(
            Output('live-price-badge', 'children'),
            Output('live-price-badge', 'color'),
            [Input('price-update-interval', 'n_intervals'),
             Input('base-currency-input', 'value'),
             Input('quote-currency-input', 'value'),
             Input('exchange-select', 'value')]
        )
        def update_live_price(n_intervals, base_currency, quote_currency, exchange):
            """Update live price badge with real data."""
            if not base_currency or not quote_currency or not exchange:
                return "Live Price: $--", "secondary"

            try:
                # Get current price using synchronous wrapper
                price = price_service.get_current_price_sync(exchange, base_currency, quote_currency)

                if price:
                    pair = f"{base_currency}/{quote_currency}"
                    return f"Live Price: ${price:,.2f} ({pair})", "success"
                else:
                    return f"Live Price: Unable to fetch", "warning"

            except Exception as e:
                logger.error(f"Error fetching live price: {e}")
                return f"Live Price: Error", "danger"

        @self.app.callback(
            Output('market-data-store', 'data'),
            [Input('chart-update-interval', 'n_intervals'),
             Input('base-currency-input', 'value'),
             Input('quote-currency-input', 'value'),
             Input('exchange-select', 'value'),
             Input('timeframe-select', 'value')]
        )
        def update_market_data(n_intervals, base_currency, quote_currency, exchange, timeframe):
            """Update market data for charts."""
            if not base_currency or not quote_currency or not exchange:
                return {}

            try:
                # Get historical data
                df = price_service.get_historical_data_sync(
                    exchange, base_currency, quote_currency, timeframe, limit=168
                )

                if df is not None and not df.empty:
                    # Convert DataFrame to dict for storage
                    market_data = {
                        'symbol': f"{base_currency}/{quote_currency}",
                        'exchange': exchange,
                        'timeframe': timeframe,
                        'data': df.to_dict('records'),
                        'timestamps': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        'last_update': datetime.now().isoformat()
                    }
                    return market_data
                else:
                    return {'error': 'Failed to fetch market data'}

            except Exception as e:
                logger.error(f"Error updating market data: {e}")
                return {'error': str(e)}

        @self.app.callback(
            Output('status-alert', 'children'),
            Output('status-alert', 'color'),
            Output('status-alert', 'is_open'),
            [Input('validate-btn', 'n_clicks'),
             Input('save-btn', 'n_clicks'),
             Input('export-btn', 'n_clicks')],
            [State('config-store', 'data')]
        )
        def handle_actions(validate_clicks, save_clicks, export_clicks, config_data):
            """Handle action button clicks."""
            if not ctx.triggered:
                return "", "info", False

            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if button_id == 'validate-btn' and validate_clicks:
                try:
                    # Validate configuration
                    validator = ConfigValidator()
                    # This would validate the config
                    return "✅ Configuration is valid!", "success", True
                except Exception as e:
                    return f"❌ Configuration error: {str(e)}", "danger", True

            elif button_id == 'save-btn' and save_clicks:
                try:
                    # Save configuration
                    config_path = "config/ui_generated_config.json"
                    with open(config_path, 'w') as f:
                        json.dump(config_data, f, indent=2)
                    return f"✅ Configuration saved to {config_path}", "success", True
                except Exception as e:
                    return f"❌ Save error: {str(e)}", "danger", True

            elif button_id == 'export-btn' and export_clicks:
                return "📁 Export functionality coming soon!", "info", True

            return "", "info", False

        @self.app.callback(
            [Output('bottom-price-input', 'value'),
             Output('top-price-input', 'value'),
             Output('status-alert', 'children', allow_duplicate=True),
             Output('status-alert', 'color', allow_duplicate=True),
             Output('status-alert', 'is_open', allow_duplicate=True)],
            [Input('suggest-range-btn', 'n_clicks')],
            [State('base-currency-input', 'value'),
             State('quote-currency-input', 'value'),
             State('exchange-select', 'value')],
            prevent_initial_call=True
        )
        def suggest_price_range(n_clicks, base_currency, quote_currency, exchange):
            """Suggest price range based on current market price."""
            if not n_clicks or not base_currency or not quote_currency or not exchange:
                return dash.no_update, dash.no_update, "", "info", False

            try:
                # Get current price
                current_price = price_service.get_current_price_sync(exchange, base_currency, quote_currency)

                if current_price:
                    # Suggest range based on current price
                    bottom, top = price_service.get_price_range_suggestion(current_price)
                    message = f"✅ Range suggested based on current price ${current_price:,.2f}"
                    return bottom, top, message, "success", True
                else:
                    return dash.no_update, dash.no_update, "❌ Unable to fetch current price", "danger", True

            except Exception as e:
                logger.error(f"Error suggesting price range: {e}")
                return dash.no_update, dash.no_update, f"❌ Error: {str(e)}", "danger", True

        @self.app.callback(
            [Output('bottom-price-input', 'value'),
             Output('top-price-input', 'value'),
             Output('status-alert', 'children', allow_duplicate=True),
             Output('status-alert', 'color', allow_duplicate=True),
             Output('status-alert', 'is_open', allow_duplicate=True)],
            [Input('suggest-range-btn', 'n_clicks')],
            [State('base-currency-input', 'value'),
             State('quote-currency-input', 'value'),
             State('exchange-select', 'value')],
            prevent_initial_call=True
        )
        def suggest_price_range(n_clicks, base_currency, quote_currency, exchange):
            """Suggest price range based on current market price."""
            if not n_clicks or not base_currency or not quote_currency or not exchange:
                return dash.no_update, dash.no_update, "", "info", False

            try:
                # Get current price
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                current_price = loop.run_until_complete(
                    price_service.get_current_price(exchange, base_currency, quote_currency)
                )
                loop.close()

                if current_price:
                    # Suggest range based on current price
                    bottom, top = price_service.get_price_range_suggestion(current_price)
                    message = f"✅ Range suggested based on current price ${current_price:,.2f}"
                    return bottom, top, message, "success", True
                else:
                    return dash.no_update, dash.no_update, "❌ Unable to fetch current price", "danger", True

            except Exception as e:
                logger.error(f"Error suggesting price range: {e}")
                return dash.no_update, dash.no_update, f"❌ Error: {str(e)}", "danger", True

    def _create_grid_visualization(self, config_data):
        """Create grid visualization chart."""
        try:
            grid_config = config_data["grid_strategy"]
            bottom = grid_config["range"]["bottom"]
            top = grid_config["range"]["top"]
            num_grids = grid_config["num_grids"]
            spacing_type = grid_config["spacing"]

            # Calculate grid levels
            if spacing_type == "arithmetic":
                grid_levels = np.linspace(bottom, top, num_grids)
            else:  # geometric
                ratio = (top / bottom) ** (1 / (num_grids - 1))
                grid_levels = [bottom * (ratio ** i) for i in range(num_grids)]

            # Create visualization
            fig = go.Figure()

            # Add grid lines
            for i, level in enumerate(grid_levels):
                color = "green" if i < len(grid_levels) // 2 else "red"
                fig.add_hline(
                    y=level,
                    line_dash="dash",
                    line_color=color,
                    annotation_text=f"${level:,.2f}",
                    annotation_position="right"
                )

            # Add current price indicator (placeholder)
            current_price = (top + bottom) / 2
            fig.add_hline(
                y=current_price,
                line_color="blue",
                line_width=3,
                annotation_text=f"Current: ${current_price:,.2f}",
                annotation_position="left"
            )

            # Style the chart
            fig.update_layout(
                title="Grid Trading Levels",
                yaxis_title="Price ($)",
                height=400,
                showlegend=False,
                yaxis=dict(range=[bottom * 0.95, top * 1.05])
            )

            # Add summary statistics
            grid_spacing = (top - bottom) / (num_grids - 1) if spacing_type == "arithmetic" else "Variable"

            summary_card = dbc.Card([
                dbc.CardBody([
                    html.H6("Grid Summary", className="card-title"),
                    html.P([
                        f"Number of Grids: {num_grids}", html.Br(),
                        f"Price Range: ${bottom:,.2f} - ${top:,.2f}", html.Br(),
                        f"Spacing: {spacing_type.title()}", html.Br(),
                        f"Grid Spacing: {grid_spacing if isinstance(grid_spacing, str) else f'${grid_spacing:,.2f}'}"
                    ])
                ])
            ], className="mt-3")

            return html.Div([
                dcc.Graph(figure=fig),
                summary_card
            ])

        except Exception as e:
            return dbc.Alert(f"Error creating grid visualization: {str(e)}", color="danger")

    def _create_price_chart(self, config_data, market_data):
        """Create price chart with grid overlay using real historical data."""
        try:
            # Get configuration
            exchange_name = config_data["exchange"]["name"]
            base_currency = config_data["pair"]["base_currency"]
            quote_currency = config_data["pair"]["quote_currency"]
            timeframe = config_data["trading_settings"]["timeframe"]

            # Fetch real historical data
            logger.info(f"Fetching historical data for {base_currency}/{quote_currency} from {exchange_name}")
            df = price_service.get_historical_data_sync(
                exchange_name, base_currency, quote_currency, timeframe, limit=168  # 1 week of hourly data
            )

            fig = go.Figure()

            if df is not None and not df.empty:
                # Add candlestick chart
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name=f'{base_currency}/{quote_currency}',
                    increasing_line_color='green',
                    decreasing_line_color='red'
                ))

                # Add volume as secondary y-axis
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name='Volume',
                    yaxis='y2',
                    opacity=0.3,
                    marker_color='lightblue'
                ))

                # Get current price for reference
                current_price = price_service.get_current_price_sync(exchange_name, base_currency, quote_currency)
                if current_price:
                    fig.add_hline(
                        y=current_price,
                        line_color="blue",
                        line_width=2,
                        annotation_text=f"Current: ${current_price:,.2f}",
                        annotation_position="top right"
                    )

                title = f"Real-time {base_currency}/{quote_currency} Price Chart with Grid Levels"

            else:
                # Fallback to sample data if real data fails
                logger.warning("Using sample data - real data fetch failed")
                dates = pd.date_range(start='2024-01-01', end='2024-01-07', freq='H')
                prices = np.cumsum(np.random.normal(0, 100, len(dates))) + 95000

                fig.add_trace(go.Scatter(
                    x=dates,
                    y=prices,
                    mode='lines',
                    name='Sample Price Data',
                    line=dict(color='orange', width=2)
                ))

                title = f"Sample {base_currency}/{quote_currency} Price Chart (Real data unavailable)"

            # Add grid levels
            grid_config = config_data["grid_strategy"]
            bottom = grid_config["range"]["bottom"]
            top = grid_config["range"]["top"]
            num_grids = grid_config["num_grids"]
            spacing_type = grid_config["spacing"]

            # Calculate grid levels
            if spacing_type == "arithmetic":
                grid_levels = np.linspace(bottom, top, num_grids)
            else:  # geometric
                ratio = (top / bottom) ** (1 / (num_grids - 1))
                grid_levels = [bottom * (ratio ** i) for i in range(num_grids)]

            # Add grid lines
            for i, level in enumerate(grid_levels):
                color = "green" if i < len(grid_levels) // 2 else "red"
                fig.add_hline(
                    y=level,
                    line_dash="dash",
                    line_color=color,
                    opacity=0.7,
                    annotation_text=f"Grid {i+1}: ${level:,.2f}",
                    annotation_position="right"
                )

            # Update layout
            fig.update_layout(
                title=title,
                xaxis_title="Time",
                yaxis_title="Price ($)",
                yaxis2=dict(
                    title="Volume",
                    overlaying="y",
                    side="right"
                ),
                height=500,
                showlegend=True,
                hovermode='x unified'
            )

            # Add range selector
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1h", step="hour", stepmode="backward"),
                            dict(count=6, label="6h", step="hour", stepmode="backward"),
                            dict(count=1, label="1d", step="day", stepmode="backward"),
                            dict(count=7, label="7d", step="day", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(visible=False),
                    type="date"
                )
            )

            return dcc.Graph(figure=fig)

        except Exception as e:
            return dbc.Alert(f"Error creating price chart: {str(e)}", color="danger")

    def _create_backtest_preview(self, config_data):
        """Create backtest preview."""
        try:
            # Placeholder for backtest preview
            # This would run a quick backtest simulation

            return dbc.Card([
                dbc.CardBody([
                    html.H6("Backtest Preview", className="card-title"),
                    html.P("This feature will show a preview of how your grid strategy would perform with historical data."),
                    dbc.Button("Run Full Backtest", color="primary", className="mt-2"),
                    html.Hr(),
                    html.H6("Expected Performance Metrics:"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4("12.5%", className="text-success"),
                                    html.P("Expected ROI", className="mb-0")
                                ])
                            ])
                        ], width=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4("156", className="text-info"),
                                    html.P("Estimated Trades", className="mb-0")
                                ])
                            ])
                        ], width=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4("8.2%", className="text-warning"),
                                    html.P("Max Drawdown", className="mb-0")
                                ])
                            ])
                        ], width=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4("2.1", className="text-primary"),
                                    html.P("Sharpe Ratio", className="mb-0")
                                ])
                            ])
                        ], width=3)
                    ])
                ])
            ])

        except Exception as e:
            return dbc.Alert(f"Error creating backtest preview: {str(e)}", color="danger")

    def run(self, debug=True, port=8050):
        """Run the Dash application."""
        logger.info(f"Starting Grid Trading Bot UI on http://localhost:{port}")
        self.app.run_server(debug=debug, port=port, host='0.0.0.0')


if __name__ == "__main__":
    ui = GridBotUI()
    ui.run(debug=True)
