"""
Configuration Forms for Grid Trading Bot Web UI

Contains all form components for configuring the grid trading bot.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Dict, Any
from utils.constants import TIMEFRAME_MAPPINGS
from web_ui.components.help_system import help_system

# Supported exchanges
SUPPORTED_EXCHANGES = [
    "coinbase", "kraken", "bitfinex", "bitstamp", "huobi", 
    "okex", "bybit", "bittrex", "poloniex", "gate", "kucoin"
]


class ConfigForms:
    """Class containing all configuration form components."""
    
    def __init__(self, current_config: Dict[str, Any]):
        """Initialize with current configuration."""
        self.current_config = current_config
    
    def create_exchange_config(self):
        """Create exchange configuration section."""
        return html.Div([
            html.H6([
                html.I(className="fas fa-exchange-alt me-2"),
                "Exchange Settings",
                help_system.create_help_icon("exchange")
            ], className="text-primary"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label([
                        "Exchange",
                        help_system.create_help_icon("exchange", "exchange_name")
                    ], html_for="exchange-select"),
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
    
    def create_pair_config(self):
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
    
    def create_grid_config(self):
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
    
    def create_risk_config(self):
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
    
    def create_trading_config(self):
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
