"""
Enhanced Configuration Forms for Grid Trading Bot Web UI

Contains all form components for configuring the grid trading bot with
improved UX, validation, and visual design.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Dict, Any, List, Optional
from utils.constants import TIMEFRAME_MAPPINGS
from web_ui.components.help_system import help_system
# from web_ui.components.enhanced_ui import EnhancedUIComponents  # Commented out for now

# Supported exchanges with additional metadata
SUPPORTED_EXCHANGES = [
    {"value": "coinbase", "label": "Coinbase", "fee": 0.5, "recommended": True, "description": "Beginner-friendly, high liquidity"},
    {"value": "kraken", "label": "Kraken", "fee": 0.26, "recommended": True, "description": "Low fees, advanced features"},
    {"value": "bitfinex", "label": "Bitfinex", "fee": 0.2, "recommended": False, "description": "Professional trading platform"},
    {"value": "bitstamp", "label": "Bitstamp", "fee": 0.5, "recommended": False, "description": "Established European exchange"},
    {"value": "huobi", "label": "Huobi", "fee": 0.2, "recommended": False, "description": "Global cryptocurrency exchange"},
    {"value": "okex", "label": "OKEx", "fee": 0.15, "recommended": False, "description": "Derivatives and spot trading"},
    {"value": "bybit", "label": "Bybit", "fee": 0.1, "recommended": False, "description": "Derivatives focused platform"},
    {"value": "bittrex", "label": "Bittrex", "fee": 0.25, "recommended": False, "description": "US-based exchange"},
    {"value": "poloniex", "label": "Poloniex", "fee": 0.25, "recommended": False, "description": "Wide variety of altcoins"},
    {"value": "gate", "label": "Gate.io", "fee": 0.2, "recommended": False, "description": "Comprehensive trading platform"},
    {"value": "kucoin", "label": "KuCoin", "fee": 0.1, "recommended": False, "description": "Low fees, many trading pairs"}
]

# Popular trading pairs
POPULAR_PAIRS = [
    {"base": "BTC", "quote": "USDT", "description": "Bitcoin/Tether - Most liquid pair"},
    {"base": "ETH", "quote": "USDT", "description": "Ethereum/Tether - High volume"},
    {"base": "BTC", "quote": "USD", "description": "Bitcoin/US Dollar - Traditional pair"},
    {"base": "ETH", "quote": "BTC", "description": "Ethereum/Bitcoin - Crypto-to-crypto"},
    {"base": "ADA", "quote": "USDT", "description": "Cardano/Tether - Popular altcoin"},
    {"base": "DOT", "quote": "USDT", "description": "Polkadot/Tether - DeFi token"}
]


class ConfigForms:
    """Enhanced configuration form components with improved UX."""

    def __init__(self, current_config: Dict[str, Any]):
        """Initialize with current configuration."""
        self.current_config = current_config
        self.validation_rules = self._get_validation_rules()

    def _get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Define validation rules for all form fields."""
        return {
            "trading_fee": {"min": 0, "max": 5, "required": True, "step": 0.001},
            "num_grids": {"min": 3, "max": 50, "required": True, "step": 1},
            "bottom_price": {"min": 0.01, "required": True, "step": 0.01},
            "top_price": {"min": 0.01, "required": True, "step": 0.01},
            "initial_balance": {"min": 100, "required": True, "step": 100},
            "take_profit_threshold": {"min": 0, "step": 0.01},
            "stop_loss_threshold": {"min": 0, "step": 0.01}
        }

    def _create_section_header(self, title: str, icon: str, description: str = "",
                              progress: Optional[int] = None) -> html.Div:
        """Create an enhanced section header with progress indicator."""
        header_content = [
            html.Div([
                html.I(className=f"{icon} fa-lg me-3 text-primary"),
                html.Div([
                    html.H5(title, className="mb-1 fw-bold"),
                    html.P(description, className="mb-0 text-muted small") if description else None
                ])
            ], className="d-flex align-items-center")
        ]

        if progress is not None:
            header_content.append(
                html.Div([
                    html.Small(f"{progress}% Complete", className="text-muted me-2"),
                    dbc.Progress(value=progress, color="primary", className="flex-grow-1", style={"height": "8px"})
                ], className="d-flex align-items-center mt-2", style={"width": "150px"})
            )

        return html.Div(
            header_content,
            className="config-section-header p-3 mb-3 bg-light rounded border-start border-primary border-4"
        )
    
    def create_exchange_config(self):
        """Create enhanced exchange configuration section."""
        return html.Div([
            self._create_section_header(
                "Exchange Settings",
                "fas fa-exchange-alt",
                "Choose your cryptocurrency exchange and trading mode",
                progress=25
            ),

            dbc.Card([
                dbc.CardBody([
                    # Exchange Selection with enhanced dropdown
                    html.Div([
                        dbc.Label([
                            "Select Exchange",
                            help_system.create_help_icon("exchange", "exchange_name")
                        ], className="form-label fw-semibold"),

                        dcc.Dropdown(
                            id="exchange-select",
                            options=[
                                {
                                    "label": html.Div([
                                        html.Div([
                                            html.Strong(ex["label"]),
                                            dbc.Badge("Recommended", color="success", className="ms-2 small") if ex["recommended"] else None
                                        ], className="d-flex align-items-center justify-content-between"),
                                        html.Small(f"{ex['description']} • Fee: {ex['fee']}%", className="text-muted")
                                    ]),
                                    "value": ex["value"]
                                } for ex in SUPPORTED_EXCHANGES
                            ],
                            value=self.current_config["exchange"]["name"],
                            clearable=False,
                            className="mb-3"
                        ),

                        # Exchange info card
                        html.Div(id="exchange-info-card", className="mb-4")
                    ]),

                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                dbc.Label("Trading Mode", className="form-label fw-semibold"),
                                dcc.Dropdown(
                                    id="trading-mode-select",
                                    options=[
                                        {"label": "📊 Backtest - Test with historical data", "value": "backtest"},
                                        {"label": "📝 Paper Trading - Simulate with live data", "value": "paper_trading"},
                                        {"label": "💰 Live Trading - Real money trading", "value": "live"}
                                    ],
                                    value=self.current_config["exchange"]["trading_mode"],
                                    clearable=False,
                                    className="mb-2"
                                ),
                                dbc.FormText("Choose your trading mode. Start with backtesting to validate your strategy.",
                                           className="text-muted")
                            ])
                        ], width=6),

                        dbc.Col([
                            html.Div([
                                dbc.Label("Trading Fee", className="form-label fw-semibold"),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="trading-fee-input",
                                        type="number",
                                        value=self.current_config["exchange"]["trading_fee"] * 100,
                                        min=0,
                                        max=5,
                                        step=0.001,
                                        className="form-control"
                                    ),
                                    dbc.InputGroupText("%")
                                ], className="mb-2"),
                                dbc.FormText("Exchange fee per trade. This affects your profit calculations.",
                                           className="text-muted")
                            ])
                        ], width=6)
                    ])
                ])
            ], className="shadow-sm")
        ], className="mb-4")
    
    def create_pair_config(self):
        """Create enhanced trading pair configuration section."""
        return html.Div([
            self._create_section_header(
                "Trading Pair",
                "fas fa-coins",
                "Select the cryptocurrency pair you want to trade",
                progress=50
            ),

            dbc.Card([
                dbc.CardBody([
                    # Popular pairs quick selection
                    html.Div([
                        html.Label("Popular Pairs", className="form-label fw-semibold mb-2"),
                        html.Div([
                            dbc.Button(
                                f"{pair['base']}/{pair['quote']}",
                                id=f"pair-btn-{pair['base']}-{pair['quote']}",
                                color="outline-primary",
                                size="sm",
                                className="me-2 mb-2"
                            ) for pair in POPULAR_PAIRS[:6]
                        ]),
                        html.Hr(className="my-3")
                    ]),

                    # Custom pair input
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                dbc.Label("Base Currency", className="form-label fw-semibold"),
                                dbc.Input(
                                    id="base-currency-input",
                                    type="text",
                                    value=self.current_config["pair"]["base_currency"],
                                    placeholder="BTC",
                                    className="mb-2"
                                ),
                                dbc.FormText("The cryptocurrency you want to trade (e.g., BTC, ETH, ADA)",
                                           className="text-muted")
                            ])
                        ], width=6),

                        dbc.Col([
                            html.Div([
                                dbc.Label("Quote Currency", className="form-label fw-semibold"),
                                dbc.Input(
                                    id="quote-currency-input",
                                    type="text",
                                    value=self.current_config["pair"]["quote_currency"],
                                    placeholder="USDT",
                                    className="mb-2"
                                ),
                                dbc.FormText("The currency to price the base currency in (e.g., USDT, USD, BTC)",
                                           className="text-muted")
                            ])
                        ], width=6)
                    ]),

                    # Current price and actions
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.H6("Current Price", className="mb-1"),
                                    html.H4("$0.00", id="current-price-display", className="text-primary mb-0 font-monospace")
                                ], className="text-center p-3 bg-light rounded")
                            ], width=4),

                            dbc.Col([
                                html.Div([
                                    dbc.Button([
                                        html.I(className="fas fa-sync me-2"),
                                        "Get Current Price"
                                    ], id="get-price-btn", color="primary", className="w-100 mb-2"),

                                    dbc.Button([
                                        html.I(className="fas fa-magic me-2"),
                                        "AI Suggest Range"
                                    ], id="suggest-range-btn", color="success", outline=True, className="w-100")
                                ])
                            ], width=8)
                        ])
                    ], className="mt-3 p-3 border rounded bg-white")
                ])
            ], className="shadow-sm")
        ], className="mb-4")
    
    def create_grid_config(self):
        """Create enhanced grid strategy configuration section."""
        return html.Div([
            self._create_section_header(
                "Grid Strategy",
                "fas fa-th",
                "Configure your grid trading parameters and price range",
                progress=75
            ),

            dbc.Card([
                dbc.CardBody([
                    # Strategy type selection with visual cards
                    html.Div([
                        html.Label("Strategy Type", className="form-label fw-semibold mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.I(className="fas fa-chart-line fa-2x text-primary mb-2"),
                                            html.H6("Simple Grid", className="mb-2"),
                                            html.P("Buy low, sell high with fixed grid levels. Best for beginners.",
                                                  className="small text-muted mb-0")
                                        ], className="text-center")
                                    ])
                                ], id="simple-grid-card", className="strategy-card h-100 cursor-pointer border-2",
                                   color="primary", outline=True)
                            ], width=6),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.I(className="fas fa-shield-alt fa-2x text-success mb-2"),
                                            html.H6("Hedged Grid", className="mb-2"),
                                            html.P("Advanced strategy with risk hedging. For experienced traders.",
                                                  className="small text-muted mb-0")
                                        ], className="text-center")
                                    ])
                                ], id="hedged-grid-card", className="strategy-card h-100 cursor-pointer border-2",
                                   color="success", outline=True)
                            ], width=6)
                        ], className="mb-4")
                    ]),

                    # Hidden dropdown for actual value storage
                    dcc.Dropdown(
                        id="strategy-type-select",
                        options=[
                            {"label": "Simple Grid", "value": "simple_grid"},
                            {"label": "Hedged Grid", "value": "hedged_grid"}
                        ],
                        value=self.current_config["grid_strategy"]["type"],
                        style={"display": "none"}
                    ),

                    # Grid parameters
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                dbc.Label("Spacing Type", className="form-label fw-semibold"),
                                dcc.Dropdown(
                                    id="spacing-type-select",
                                    options=[
                                        {"label": "📏 Arithmetic - Equal price differences", "value": "arithmetic"},
                                        {"label": "📈 Geometric - Equal percentage differences", "value": "geometric"}
                                    ],
                                    value=self.current_config["grid_strategy"]["spacing"],
                                    clearable=False,
                                    className="mb-2"
                                ),
                                dbc.FormText("Arithmetic spacing works better in ranging markets, geometric in trending markets.",
                                           className="text-muted")
                            ])
                        ], width=6),

                        dbc.Col([
                            html.Div([
                                dbc.Label("Number of Grids", className="form-label fw-semibold"),
                                dbc.Input(
                                    id="num-grids-input",
                                    type="number",
                                    value=self.current_config["grid_strategy"]["num_grids"],
                                    min=3,
                                    max=50,
                                    step=1,
                                    className="mb-2"
                                ),
                                dbc.FormText("More grids = more trades but smaller profits per trade. Recommended: 10-20",
                                           className="text-muted")
                            ])
                        ], width=6)
                    ]),

                    # Price range with visual feedback
                    html.Div([
                        html.Label("Price Range", className="form-label fw-semibold mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Label("Bottom Price", className="form-label fw-semibold"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id="bottom-price-input",
                                            type="number",
                                            value=self.current_config["grid_strategy"]["range"]["bottom"],
                                            min=0.01,
                                            step=0.01,
                                            className="form-control"
                                        )
                                    ], className="mb-2"),
                                    dbc.FormText("Lowest price level - bot will place buy orders here",
                                               className="text-muted")
                                ])
                            ], width=6),

                            dbc.Col([
                                html.Div([
                                    dbc.Label("Top Price", className="form-label fw-semibold"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id="top-price-input",
                                            type="number",
                                            value=self.current_config["grid_strategy"]["range"]["top"],
                                            min=0.01,
                                            step=0.01,
                                            className="form-control"
                                        )
                                    ], className="mb-2"),
                                    dbc.FormText("Highest price level - bot will place sell orders here",
                                               className="text-muted")
                                ])
                            ], width=6)
                        ])
                    ]),

                    # Grid preview
                    html.Div([
                        html.Hr(className="my-4"),
                        html.Div([
                            html.H6("Grid Preview", className="mb-3"),
                            html.Div(id="grid-preview-container", className="p-3 bg-light rounded")
                        ])
                    ])
                ])
            ], className="shadow-sm")
        ], className="mb-4")
    
    def create_risk_config(self):
        """Create enhanced risk management configuration section."""
        return html.Div([
            self._create_section_header(
                "Risk Management",
                "fas fa-shield-alt",
                "Set up safety measures to protect your investment",
                progress=90
            ),

            dbc.Card([
                dbc.CardBody([
                    # Risk level indicator
                    html.Div([
                        html.Label("Risk Assessment", className="form-label fw-semibold mb-3"),
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-shield-alt fa-2x text-success mb-2"),
                                html.H6("Low Risk", id="risk-level-display", className="text-success mb-1"),
                                html.P("Conservative strategy with safety measures",
                                      id="risk-description", className="small text-muted mb-0")
                            ], className="text-center p-3 bg-light rounded")
                        ], className="mb-4")
                    ]),

                    # Take Profit Configuration
                    html.Div([
                        dbc.Card([
                            dbc.CardHeader([
                                dbc.Switch(
                                    id="take-profit-enabled",
                                    label="Enable Take Profit",
                                    value=self.current_config["risk_management"]["take_profit"]["enabled"],
                                    className="fw-semibold"
                                )
                            ]),
                            dbc.Collapse([
                                dbc.CardBody([
                                    html.Div([
                                        dbc.Label("Take Profit Price", className="form-label fw-semibold"),
                                        dbc.InputGroup([
                                            dbc.InputGroupText("$"),
                                            dbc.Input(
                                                id="take-profit-threshold",
                                                type="number",
                                                value=self.current_config["risk_management"]["take_profit"]["threshold"],
                                                min=0,
                                                step=0.01,
                                                className="form-control"
                                            )
                                        ], className="mb-2"),
                                        dbc.FormText("Automatically close all positions when price reaches this level (profit target)",
                                                   className="text-muted")
                                    ])
                                ])
                            ], id="take-profit-collapse", is_open=self.current_config["risk_management"]["take_profit"]["enabled"])
                        ], color="success", outline=True, className="mb-3")
                    ]),

                    # Stop Loss Configuration
                    html.Div([
                        dbc.Card([
                            dbc.CardHeader([
                                dbc.Switch(
                                    id="stop-loss-enabled",
                                    label="Enable Stop Loss",
                                    value=self.current_config["risk_management"]["stop_loss"]["enabled"],
                                    className="fw-semibold"
                                )
                            ]),
                            dbc.Collapse([
                                dbc.CardBody([
                                    html.Div([
                                        dbc.Label("Stop Loss Price", className="form-label fw-semibold"),
                                        dbc.InputGroup([
                                            dbc.InputGroupText("$"),
                                            dbc.Input(
                                                id="stop-loss-threshold",
                                                type="number",
                                                value=self.current_config["risk_management"]["stop_loss"]["threshold"],
                                                min=0,
                                                step=0.01,
                                                className="form-control"
                                            )
                                        ], className="mb-2"),
                                        dbc.FormText("Automatically close all positions when price falls to this level (loss limit)",
                                                   className="text-muted")
                                    ])
                                ])
                            ], id="stop-loss-collapse", is_open=self.current_config["risk_management"]["stop_loss"]["enabled"])
                        ], color="danger", outline=True)
                    ])
                ])
            ], className="shadow-sm")
        ], className="mb-4")
    
    def create_trading_config(self):
        """Create enhanced trading settings configuration section."""
        return html.Div([
            self._create_section_header(
                "Trading Settings",
                "fas fa-clock",
                "Configure timing, balance, and execution parameters",
                progress=100
            ),

            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                dbc.Label("Chart Timeframe", className="form-label fw-semibold"),
                                dcc.Dropdown(
                                    id="timeframe-select",
                                    options=[
                                        {"label": f"📊 {tf} - {self._get_timeframe_description(tf)}", "value": tf}
                                        for tf in TIMEFRAME_MAPPINGS.keys()
                                    ],
                                    value=self.current_config["trading_settings"]["timeframe"],
                                    clearable=False,
                                    className="mb-2"
                                ),
                                dbc.FormText("Chart timeframe for analysis. 1h is good for beginners, 6h-1d for longer-term strategies.",
                                           className="text-muted")
                            ])
                        ], width=6),

                        dbc.Col([
                            html.Div([
                                dbc.Label("Initial Balance", className="form-label fw-semibold"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("$"),
                                    dbc.Input(
                                        id="initial-balance-input",
                                        type="number",
                                        value=self.current_config["trading_settings"]["initial_balance"],
                                        min=100,
                                        step=100,
                                        className="form-control"
                                    )
                                ], className="mb-2"),
                                dbc.FormText("Starting amount for trading. This will be divided across grid levels.",
                                           className="text-muted")
                            ])
                        ], width=6)
                    ]),

                    # Date range for backtesting
                    html.Div([
                        html.Hr(className="my-4"),
                        html.Label("Backtesting Period", className="form-label fw-semibold mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    dbc.Label("Start Date", className="form-label fw-semibold"),
                                    dbc.Input(
                                        id="start-date-input",
                                        type="datetime-local",
                                        value=self.current_config["trading_settings"]["period"]["start_date"].replace("Z", ""),
                                        className="mb-2"
                                    ),
                                    dbc.FormText("Start date for historical backtesting",
                                               className="text-muted")
                                ])
                            ], width=6),

                            dbc.Col([
                                html.Div([
                                    dbc.Label("End Date", className="form-label fw-semibold"),
                                    dbc.Input(
                                        id="end-date-input",
                                        type="datetime-local",
                                        value=self.current_config["trading_settings"]["period"]["end_date"].replace("Z", ""),
                                        className="mb-2"
                                    ),
                                    dbc.FormText("End date for historical backtesting",
                                               className="text-muted")
                                ])
                            ], width=6)
                        ]),

                        # Quick date range buttons
                        html.Div([
                            html.Label("Quick Select:", className="form-label small mb-2"),
                            dbc.ButtonGroup([
                                dbc.Button("Last 7 Days", id="date-7d", color="outline-secondary", size="sm"),
                                dbc.Button("Last 30 Days", id="date-30d", color="outline-secondary", size="sm"),
                                dbc.Button("Last 3 Months", id="date-3m", color="outline-secondary", size="sm"),
                                dbc.Button("Last Year", id="date-1y", color="outline-secondary", size="sm")
                            ])
                        ], className="mt-3")
                    ])
                ])
            ], className="shadow-sm")
        ], className="mb-4")

    def _get_timeframe_description(self, timeframe: str) -> str:
        """Get description for timeframe."""
        descriptions = {
            "1m": "Very short-term, high frequency",
            "5m": "Short-term scalping",
            "15m": "Short-term trading",
            "30m": "Medium-term intraday",
            "1h": "Hourly analysis (recommended)",
            "4h": "Medium-term swing trading",
            "6h": "Longer-term positioning",
            "12h": "Half-daily analysis",
            "1d": "Daily trend following",
            "1w": "Weekly trend analysis"
        }
        return descriptions.get(timeframe, "Custom timeframe")

    def create_configuration_summary(self):
        """Create a configuration summary card."""
        return dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-clipboard-check me-2"),
                    "Configuration Summary"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.Div(id="config-summary-content", children=[
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-exchange-alt fa-2x text-primary mb-2"),
                                html.H6("Exchange", className="mb-1"),
                                html.P(self.current_config["exchange"]["name"].title(), className="mb-0")
                            ], className="text-center")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-coins fa-2x text-info mb-2"),
                                html.H6("Trading Pair", className="mb-1"),
                                html.P(f"{self.current_config['pair']['base_currency']}/{self.current_config['pair']['quote_currency']}",
                                      className="mb-0")
                            ], className="text-center")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-th fa-2x text-success mb-2"),
                                html.H6("Grid Levels", className="mb-1"),
                                html.P(str(self.current_config["grid_strategy"]["num_grids"]), className="mb-0")
                            ], className="text-center")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-dollar-sign fa-2x text-warning mb-2"),
                                html.H6("Initial Balance", className="mb-1"),
                                html.P(f"${self.current_config['trading_settings']['initial_balance']:,}", className="mb-0")
                            ], className="text-center")
                        ], width=3)
                    ])
                ])
            ])
        ], color="light", className="mt-4")
