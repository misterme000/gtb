"""
Help System Components for Grid Trading Bot Web UI

Provides tooltips, help sections, and documentation within the UI.
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, Any


class HelpSystem:
    """Class containing all help and documentation components."""
    
    # Help content for different sections
    HELP_CONTENT = {
        "exchange": {
            "title": "Exchange Settings",
            "description": "Configure which exchange to use and trading parameters.",
            "fields": {
                "exchange_name": "Select the cryptocurrency exchange. Coinbase and Kraken are recommended for beginners.",
                "trading_mode": "Backtest: Test with historical data. Paper Trading: Simulate with live data. Live: Real trading with actual funds.",
                "trading_fee": "The fee charged by the exchange per trade, typically 0.1% to 0.5%."
            }
        },
        "pair": {
            "title": "Trading Pair",
            "description": "Select the cryptocurrency pair to trade.",
            "fields": {
                "base_currency": "The cryptocurrency you want to trade (e.g., BTC, ETH).",
                "quote_currency": "The currency to price the base currency in (e.g., USD, USDT).",
                "get_price": "Fetch the current market price for this trading pair.",
                "suggest_range": "Get AI-powered suggestions for grid range based on current price and volatility."
            }
        },
        "grid_strategy": {
            "title": "Grid Strategy",
            "description": "Configure your grid trading strategy parameters.",
            "fields": {
                "strategy_type": "Simple Grid: Basic buy low, sell high. Hedged Grid: More complex with risk management.",
                "spacing_type": "Arithmetic: Equal price differences. Geometric: Equal percentage differences.",
                "num_grids": "Number of price levels in your grid. More grids = more trades but smaller profits per trade.",
                "bottom_price": "Lowest price level of your grid. Bot will place buy orders here.",
                "top_price": "Highest price level of your grid. Bot will place sell orders here."
            }
        },
        "risk_management": {
            "title": "Risk Management",
            "description": "Set up safety measures to protect your investment.",
            "fields": {
                "take_profit": "Automatically close all positions when price reaches this level (profit target).",
                "stop_loss": "Automatically close all positions when price falls to this level (loss limit)."
            }
        },
        "trading_settings": {
            "title": "Trading Settings",
            "description": "Configure timing and balance parameters.",
            "fields": {
                "timeframe": "Chart timeframe for analysis. 1h is good for beginners, 6h-1d for longer-term strategies.",
                "initial_balance": "Starting amount for trading. This will be divided across grid levels.",
                "start_date": "Start date for backtesting (historical testing).",
                "end_date": "End date for backtesting."
            }
        }
    }
    
    @staticmethod
    def create_tooltip(text: str, target_id: str) -> dbc.Tooltip:
        """Create a tooltip for a specific element."""
        return dbc.Tooltip(
            text,
            target=target_id,
            placement="top"
        )
    
    @staticmethod
    def create_help_icon(section: str, field: str = None) -> html.Span:
        """Create a help icon with tooltip."""
        help_id = f"help-{section}-{field}" if field else f"help-{section}"
        
        # Get help text
        if field and section in HelpSystem.HELP_CONTENT:
            help_text = HelpSystem.HELP_CONTENT[section]["fields"].get(field, "No help available")
        elif section in HelpSystem.HELP_CONTENT:
            help_text = HelpSystem.HELP_CONTENT[section]["description"]
        else:
            help_text = "No help available"
        
        return html.Span([
            html.I(
                className="fas fa-question-circle text-muted ms-1",
                id=help_id,
                style={"cursor": "pointer", "fontSize": "0.8rem"}
            ),
            dbc.Tooltip(help_text, target=help_id, placement="top")
        ])
    
    @staticmethod
    def create_help_modal() -> dbc.Modal:
        """Create a comprehensive help modal."""
        return dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Grid Trading Bot Help")),
            dbc.ModalBody([
                html.H5("What is Grid Trading?"),
                html.P([
                    "Grid trading is an automated strategy that places buy and sell orders at regular intervals ",
                    "around a set price range. It profits from market volatility by buying low and selling high ",
                    "within the defined range."
                ]),
                
                html.H5("How to Get Started:", className="mt-4"),
                html.Ol([
                    html.Li("Select an exchange (Coinbase recommended for beginners)"),
                    html.Li("Choose a trading pair (BTC/USD is popular)"),
                    html.Li("Click 'Get Current Price' to see the market price"),
                    html.Li("Click 'Suggest Range' for AI-powered range recommendations"),
                    html.Li("Set your grid parameters (10-20 grids is typical)"),
                    html.Li("Set your initial balance"),
                    html.Li("Click 'Validate Config' to check your settings"),
                    html.Li("Start with 'Paper Trading' mode to test without real money")
                ]),
                
                html.H5("Key Concepts:", className="mt-4"),
                html.Dl([
                    html.Dt("Grid Range"),
                    html.Dd("The price range where your bot will operate. Should cover expected price movements."),
                    
                    html.Dt("Number of Grids"),
                    html.Dd("More grids = more frequent trades but smaller profits. Fewer grids = larger profits but fewer trades."),
                    
                    html.Dt("Arithmetic vs Geometric Spacing"),
                    html.Dd("Arithmetic: Equal dollar amounts between levels. Geometric: Equal percentage amounts."),
                    
                    html.Dt("Paper Trading"),
                    html.Dd("Simulated trading with real market data but fake money. Perfect for testing strategies.")
                ]),
                
                html.H5("Risk Management Tips:", className="mt-4"),
                html.Ul([
                    html.Li("Always start with paper trading to test your strategy"),
                    html.Li("Never invest more than you can afford to lose"),
                    html.Li("Set stop-loss orders to limit potential losses"),
                    html.Li("Monitor your bot regularly, especially in volatile markets"),
                    html.Li("Start with conservative settings and adjust based on performance")
                ]),
                
                html.H5("Common Mistakes to Avoid:", className="mt-4"),
                html.Ul([
                    html.Li("Setting grid range too narrow (missing price movements)"),
                    html.Li("Setting grid range too wide (capital inefficiency)"),
                    html.Li("Using too many grids (over-complication)"),
                    html.Li("Not setting stop-loss orders"),
                    html.Li("Starting with live trading without testing")
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-help-modal", className="ms-auto", n_clicks=0)
            ])
        ], id="help-modal", size="lg", is_open=False)
    
    @staticmethod
    def create_quick_start_guide() -> dbc.Card:
        """Create a quick start guide card."""
        return dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-rocket me-2"),
                    "Quick Start Guide"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.Div([
                    dbc.Alert([
                        html.H6("👋 New to Grid Trading?", className="alert-heading"),
                        html.P("Follow these steps to set up your first grid trading strategy:", className="mb-2"),
                        html.Ol([
                            html.Li("Choose 'Coinbase' as your exchange"),
                            html.Li("Set BTC/USD as your trading pair"),
                            html.Li("Click 'Get Current Price' and 'Suggest Range'"),
                            html.Li("Use 10-15 grids for your first strategy"),
                            html.Li("Set trading mode to 'Paper Trading'"),
                            html.Li("Click 'Validate Config' to check everything"),
                            html.Li("Review the backtest preview"),
                            html.Li("Save your configuration for future use")
                        ], className="mb-2"),
                        html.P([
                            html.Strong("💡 Pro Tip: "),
                            "Always test with paper trading before using real money!"
                        ], className="mb-0")
                    ], color="info"),
                    
                    dbc.Button([
                        html.I(className="fas fa-question-circle me-2"),
                        "Open Full Help Guide"
                    ], id="open-help-modal", color="outline-primary", size="sm", className="mt-2")
                ])
            ])
        ], className="mb-3")
    
    @staticmethod
    def create_status_indicators() -> html.Div:
        """Create status indicators for different components."""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Badge([
                        html.I(className="fas fa-wifi me-1"),
                        "Live Data"
                    ], color="success", id="live-data-status")
                ], width="auto"),
                dbc.Col([
                    dbc.Badge([
                        html.I(className="fas fa-chart-line me-1"),
                        "Charts"
                    ], color="success", id="charts-status")
                ], width="auto"),
                dbc.Col([
                    dbc.Badge([
                        html.I(className="fas fa-cog me-1"),
                        "Config"
                    ], color="warning", id="config-status")
                ], width="auto"),
                dbc.Col([
                    dbc.Badge([
                        html.I(className="fas fa-shield-alt me-1"),
                        "Validation"
                    ], color="secondary", id="validation-status")
                ], width="auto")
            ], className="g-2")
        ], className="mb-3")
    
    @staticmethod
    def create_keyboard_shortcuts_help() -> dbc.Collapse:
        """Create keyboard shortcuts help section."""
        return dbc.Collapse([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Keyboard Shortcuts"),
                    html.Dl([
                        html.Dt("Ctrl + S"), html.Dd("Save configuration"),
                        html.Dt("Ctrl + E"), html.Dd("Export configuration"),
                        html.Dt("Ctrl + V"), html.Dd("Validate configuration"),
                        html.Dt("F1"), html.Dd("Open help"),
                        html.Dt("Escape"), html.Dd("Close modals")
                    ])
                ])
            ])
        ], id="shortcuts-collapse", is_open=False)
    
    @staticmethod
    def get_field_validation_message(field_name: str, is_valid: bool, value: Any = None) -> str:
        """Get validation message for a specific field."""
        if is_valid:
            return ""
        
        messages = {
            "trading_fee": "Trading fee must be between 0% and 10%",
            "num_grids": "Number of grids must be between 3 and 100",
            "bottom_price": "Bottom price must be positive and less than top price",
            "top_price": "Top price must be positive and greater than bottom price",
            "initial_balance": "Initial balance must be at least $100"
        }
        
        return messages.get(field_name, "Invalid value")


# Global help system instance
help_system = HelpSystem()
