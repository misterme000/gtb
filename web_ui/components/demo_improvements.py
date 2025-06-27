"""
Demo Components showcasing UI/UX improvements for Grid Trading Bot

This file demonstrates the enhanced components and can be used to preview
the improvements before full integration.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from web_ui.components.enhanced_ui import EnhancedUIComponents
from web_ui.components.notifications import create_step_indicator


def create_demo_layout():
    """Create a demo layout showcasing all UI improvements."""
    
    # Sample data for demonstrations
    sample_metrics = [
        {
            "title": "Current Price",
            "value": 45250.75,
            "previous_value": 44800.50,
            "format": "${:.2f}",
            "color": "primary",
            "icon": "fas fa-dollar-sign"
        },
        {
            "title": "Grid Levels",
            "value": 12,
            "previous_value": 10,
            "format": "{}",
            "color": "info",
            "icon": "fas fa-layer-group"
        },
        {
            "title": "Est. Profit",
            "value": 0.085,
            "previous_value": 0.072,
            "format": "{:.1%}",
            "color": "success",
            "icon": "fas fa-chart-line"
        },
        {
            "title": "Risk Level",
            "value": 0.25,
            "previous_value": 0.30,
            "format": "{:.0%}",
            "color": "warning",
            "icon": "fas fa-shield-alt"
        }
    ]
    
    # Sample price data
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='H')
    np.random.seed(42)
    prices = 45000 + np.cumsum(np.random.randn(len(dates)) * 50)
    
    sample_data = {
        'data': pd.DataFrame({
            'open': prices + np.random.randn(len(dates)) * 20,
            'high': prices + np.abs(np.random.randn(len(dates)) * 30),
            'low': prices - np.abs(np.random.randn(len(dates)) * 30),
            'close': prices,
            'volume': np.random.randint(100, 1000, len(dates))
        }, index=dates)
    }
    
    grid_levels = [44000, 44500, 45000, 45500, 46000, 46500]
    
    return dbc.Container([
        # Header
        html.Div([
            html.H1([
                html.I(className="fas fa-palette me-3"),
                "UI/UX Improvements Demo"
            ], className="text-white mb-2"),
            html.P("Preview of enhanced Grid Trading Bot interface", 
                  className="text-white-50 mb-0")
        ], className="app-header mb-4"),
        
        # Metrics Dashboard Demo
        html.H3("Enhanced Metrics Dashboard", className="mb-3"),
        EnhancedUIComponents.create_metric_dashboard(sample_metrics),
        
        html.Hr(className="my-5"),
        
        # Smart Input Components Demo
        html.H3("Smart Input Components", className="mb-3"),
        dbc.Row([
            dbc.Col([
                EnhancedUIComponents.create_smart_input_group(
                    label="Bottom Price",
                    input_id="demo-bottom-price",
                    input_type="number",
                    value=44000,
                    prefix="$",
                    help_text="Lowest price level for your grid strategy",
                    validation_rules={"min": 0, "required": True}
                )
            ], width=6),
            dbc.Col([
                EnhancedUIComponents.create_smart_input_group(
                    label="Trading Fee",
                    input_id="demo-trading-fee",
                    input_type="number",
                    value=0.5,
                    suffix="%",
                    help_text="Exchange trading fee percentage",
                    validation_rules={"min": 0, "max": 5, "required": True}
                )
            ], width=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                EnhancedUIComponents.create_smart_input_group(
                    label="Exchange",
                    input_id="demo-exchange",
                    input_type="select",
                    value="coinbase",
                    options=[
                        {"label": "Coinbase", "value": "coinbase"},
                        {"label": "Kraken", "value": "kraken"},
                        {"label": "Bitfinex", "value": "bitfinex"}
                    ],
                    help_text="Select your preferred cryptocurrency exchange"
                )
            ], width=6),
            dbc.Col([
                EnhancedUIComponents.create_smart_input_group(
                    label="Strategy Notes",
                    input_id="demo-notes",
                    input_type="textarea",
                    placeholder="Enter your strategy notes here...",
                    help_text="Optional notes about your trading strategy",
                    rows=3
                )
            ], width=6)
        ]),
        
        html.Hr(className="my-5"),
        
        # Interactive Chart Demo
        html.H3("Enhanced Price Chart", className="mb-3"),
        dbc.Card([
            dbc.CardBody([
                EnhancedUIComponents.create_interactive_price_chart(
                    data=sample_data,
                    grid_levels=grid_levels,
                    height=400,
                    show_volume=True
                )
            ])
        ]),
        
        html.Hr(className="my-5"),
        
        # Step Indicator Demo
        html.H3("Configuration Wizard Steps", className="mb-3"),
        dbc.Card([
            dbc.CardBody([
                create_step_indicator(
                    steps=["Exchange Setup", "Trading Pair", "Grid Strategy", "Risk Management", "Review & Launch"],
                    current_step=2
                ),
                html.P("This step indicator shows progress through the configuration wizard.", 
                      className="text-muted mt-3")
            ])
        ]),
        
        html.Hr(className="my-5"),
        
        # Enhanced Cards Demo
        html.H3("Enhanced Card Components", className="mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6([
                            html.I(className="fas fa-cog me-2"),
                            "Configuration Status"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-check-circle fa-3x text-success mb-3"),
                            html.H5("Configuration Complete", className="text-success"),
                            html.P("Your grid trading strategy is ready to deploy.", 
                                  className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="h-100 border-success")
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6([
                            html.I(className="fas fa-chart-bar me-2"),
                            "Performance Preview"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.H4("8.5%", className="text-primary mb-1"),
                            html.P("Expected Annual Return", className="text-muted small mb-2"),
                            dbc.Progress(value=85, color="primary", className="mb-2"),
                            html.Small("Based on historical data", className="text-muted")
                        ])
                    ])
                ], className="h-100")
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6([
                            html.I(className="fas fa-shield-alt me-2"),
                            "Risk Assessment"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            dbc.Badge("LOW RISK", color="success", className="mb-2"),
                            html.P("Conservative grid strategy with stop-loss protection.", 
                                  className="text-muted small mb-0")
                        ])
                    ])
                ], className="h-100 border-warning")
            ], width=4)
        ], className="g-3"),
        
        html.Hr(className="my-5"),
        
        # Action Buttons Demo
        html.H3("Enhanced Action Buttons", className="mb-3"),
        html.Div([
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-play me-2"),
                    "Start Trading"
                ], color="success", size="lg"),
                dbc.Button([
                    html.I(className="fas fa-pause me-2"),
                    "Pause"
                ], color="warning", outline=True, size="lg"),
                dbc.Button([
                    html.I(className="fas fa-stop me-2"),
                    "Stop"
                ], color="danger", outline=True, size="lg")
            ], className="me-3"),
            
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-download me-2"),
                    "Export Config"
                ], color="primary", outline=True),
                dbc.Button([
                    html.I(className="fas fa-upload me-2"),
                    "Import Config"
                ], color="secondary", outline=True),
                dbc.Button([
                    html.I(className="fas fa-history me-2"),
                    "View History"
                ], color="info", outline=True)
            ])
        ], className="d-flex flex-wrap gap-2"),
        
        # Footer
        html.Hr(className="my-5"),
        html.Div([
            html.P([
                "This demo showcases the enhanced UI/UX components. ",
                html.A("View implementation details", href="#", className="text-decoration-none"),
                " for integration instructions."
            ], className="text-muted text-center mb-0")
        ])
        
    ], fluid=True, className="py-4")


def create_before_after_comparison():
    """Create a before/after comparison of UI improvements."""
    return dbc.Container([
        html.H2("Before vs After Comparison", className="text-center mb-5"),
        
        dbc.Row([
            dbc.Col([
                html.H4("Before", className="text-center mb-3"),
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Basic Input"),
                        dbc.Input(placeholder="Enter value", className="mb-2"),
                        html.Small("Basic form input", className="text-muted")
                    ])
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Simple Metric"),
                        html.H3("$45,250"),
                        html.P("Current Price")
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                html.H4("After", className="text-center mb-3"),
                EnhancedUIComponents.create_smart_input_group(
                    label="Enhanced Input",
                    input_id="comparison-input",
                    input_type="number",
                    prefix="$",
                    help_text="Smart input with validation and prefix",
                    validation_rules={"required": True}
                ),
                
                EnhancedUIComponents.create_metric_dashboard([{
                    "title": "Current Price",
                    "value": 45250,
                    "previous_value": 44800,
                    "format": "${:.0f}",
                    "color": "primary",
                    "icon": "fas fa-dollar-sign"
                }])
            ], width=6)
        ])
    ], className="py-4")
