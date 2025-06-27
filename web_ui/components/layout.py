"""
Layout Components for Grid Trading Bot Web UI

Contains all layout-related functions for creating the UI structure.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Dict, Any


class LayoutComponents:
    """Class containing all layout components for the Grid Trading Bot UI."""
    
    def __init__(self, current_config: Dict[str, Any]):
        """Initialize with current configuration."""
        self.current_config = current_config
    
    def create_header(self):
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
                ]),

                # Hidden file upload component
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
            ], width=4, className="text-end")
        ], className="mb-4 pb-3 border-bottom")
    
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
                    dbc.Tab(label="Price Chart", tab_id="chart-tab"),
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
            
        ], fluid=True, className="px-4")
