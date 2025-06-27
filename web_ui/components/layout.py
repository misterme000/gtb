"""
Layout Components for Grid Trading Bot Web UI

Contains all layout-related functions for creating the UI structure.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Dict, Any
from web_ui.components.help_system import help_system
from web_ui.components.notifications import notification_system


class LayoutComponents:
    """Class containing all layout components for the Grid Trading Bot UI."""
    
    def __init__(self, current_config: Dict[str, Any]):
        """Initialize with current configuration."""
        self.current_config = current_config
    
    def create_header(self):
        """Create an enhanced header section with better visual hierarchy."""
        return html.Div([
            # Main header with gradient background
            html.Div([
                dbc.Container([
                    dbc.Row([
                        dbc.Col([
                            html.H1([
                                html.I(className="fas fa-robot me-3"),
                                "Grid Trading Bot"
                            ], className="mb-2"),
                            html.P("Configure your automated trading strategy with real-time insights",
                                  className="mb-0 opacity-75")
                        ], width=8),
                        dbc.Col([
                            # Status indicator
                            html.Div([
                                html.Div(className="status-indicator status-success"),
                                html.Span("System Online", className="text-white-50 small")
                            ], className="d-flex align-items-center justify-content-end mb-2"),

                            # Action buttons
                            dbc.ButtonGroup([
                                dbc.Button([
                                    html.I(className="fas fa-upload me-2"),
                                    "Import"
                                ], id="import-btn", color="light", outline=True, size="sm"),
                                dbc.Button([
                                    html.I(className="fas fa-download me-2"),
                                    "Export"
                                ], id="export-btn", color="light", outline=True, size="sm"),
                                dbc.Button([
                                    html.I(className="fas fa-play me-2"),
                                    "Run Backtest"
                                ], id="run-backtest-btn", color="warning", size="sm")
                            ], className="d-flex")
                        ], width=4, className="d-flex flex-column align-items-end")
                    ])
                ])
            ], className="app-header"),

            # Quick stats bar
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        self._create_quick_stat("Current Price", "$0.00", "fas fa-dollar-sign", "primary")
                    ], width=3),
                    dbc.Col([
                        self._create_quick_stat("Grid Levels", "0", "fas fa-layer-group", "info")
                    ], width=3),
                    dbc.Col([
                        self._create_quick_stat("Est. Profit", "0%", "fas fa-chart-line", "success")
                    ], width=3),
                    dbc.Col([
                        self._create_quick_stat("Risk Level", "Low", "fas fa-shield-alt", "warning")
                    ], width=3)
                ], className="g-3")
            ], className="mb-4"),

            # Hidden components for file operations
            dcc.Upload(
                id='upload-config',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px',
                    'display': 'none'  # Hidden by default
                },
                multiple=False,
                accept='.json'
            ),

            # Hidden download component
            html.Div(id="download-config", style={"display": "none"})
        ])
    
    def create_config_panel(self):
        """Create the configuration panel."""
        from web_ui.components.config_forms import ConfigForms
        config_forms = ConfigForms(self.current_config)
        
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-cog me-2"),
                    "Configuration"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                # Quick Start Guide
                help_system.create_quick_start_guide(),

                # Exchange Configuration
                config_forms.create_exchange_config(),
                html.Hr(),

                # Trading Pair Configuration
                config_forms.create_pair_config(),
                html.Hr(),

                # Grid Strategy Configuration
                config_forms.create_grid_config(),
                html.Hr(),

                # Risk Management Configuration
                config_forms.create_risk_config(),
                html.Hr(),

                # Trading Settings Configuration
                config_forms.create_trading_config()
            ])
        ], className="h-100")
    
    def create_visualization_panel(self):
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
                    dbc.Tab(label="Interactive Grid", tab_id="interactive-tab"),
                    dbc.Tab(label="Price Chart", tab_id="chart-tab"),
                    dbc.Tab(label="Real-time Monitor", tab_id="realtime-tab"),
                    dbc.Tab(label="Backtest Preview", tab_id="backtest-tab")
                ], id="viz-tabs", active_tab="grid-tab"),
                
                html.Div(id="viz-content", className="mt-3")
            ])
        ], className="h-100")
    
    def create_footer(self):
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
    
    def create_main_layout(self):
        """Create the main application layout."""
        return dbc.Container([
            # Header
            self.create_header(),
            
            # Main content
            dbc.Row([
                # Left panel - Configuration forms
                dbc.Col([
                    self.create_config_panel()
                ], width=4),
                
                # Right panel - Visualization and preview
                dbc.Col([
                    self.create_visualization_panel()
                ], width=8)
            ], className="mt-3"),
            
            # Footer with action buttons
            self.create_footer(),
            
            # Hidden components for data storage
            dcc.Store(id='config-store', data=self.current_config),
            dcc.Store(id='market-data-store', data={}),
            dcc.Interval(id='price-update-interval', interval=30000, n_intervals=0),  # 30 seconds
            dcc.Interval(id='chart-update-interval', interval=60000, n_intervals=0),  # 1 minute for charts

            # Notification system
            notification_system.create_toast_container(),

            # Help system components
            help_system.create_help_modal()
            
        ], fluid=True, className="px-4")

    def _create_quick_stat(self, label: str, value: str, icon: str, color: str):
        """Create a quick stat card for the header."""
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"{icon} fa-2x text-{color} mb-2"),
                    html.H4(value, className="mb-1 fw-bold", id=f"stat-{label.lower().replace(' ', '-')}"),
                    html.P(label, className="mb-0 text-muted small")
                ], className="text-center")
            ], className="py-3")
        ], className="metric-card-enhanced h-100")

    def create_enhanced_config_panel(self):
        """Create an enhanced configuration panel with better organization."""
        from web_ui.components.config_forms import ConfigForms
        config_forms = ConfigForms(self.current_config)

        return dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.H5([
                        html.I(className="fas fa-cog me-2"),
                        "Configuration"
                    ], className="mb-0"),
                    dbc.Badge("Live", color="success", className="ms-2")
                ])
            ]),
            dbc.CardBody([
                # Configuration wizard steps
                html.Div([
                    dbc.Nav([
                        dbc.NavItem(dbc.NavLink("Exchange", href="#exchange", active=True)),
                        dbc.NavItem(dbc.NavLink("Trading Pair", href="#pair")),
                        dbc.NavItem(dbc.NavLink("Grid Strategy", href="#grid")),
                        dbc.NavItem(dbc.NavLink("Risk Management", href="#risk")),
                        dbc.NavItem(dbc.NavLink("Settings", href="#settings"))
                    ], pills=True, className="mb-4")
                ]),

                # Quick Start Guide
                help_system.create_quick_start_guide(),
                html.Hr(),

                # Exchange Configuration
                config_forms.create_exchange_config(),
                html.Hr(),

                # Trading Pair Configuration
                config_forms.create_pair_config(),
                html.Hr(),

                # Grid Strategy Configuration
                config_forms.create_grid_config(),
                html.Hr(),

                # Risk Management Configuration
                config_forms.create_risk_config(),
                html.Hr(),

                # Trading Settings Configuration
                config_forms.create_trading_config(),

                # Configuration summary
                html.Hr(),
                self._create_config_summary()
            ])
        ], className="h-100")

    def _create_config_summary(self):
        """Create a configuration summary section."""
        return dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-clipboard-check me-2"),
                    "Configuration Summary"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.Div(id="config-summary-content", children=[
                    html.P("Configure your settings above to see a summary here.",
                          className="text-muted text-center")
                ])
            ])
        ], color="light", outline=True)
