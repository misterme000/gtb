"""
Interactive Grid Components for Grid Trading Bot Web UI

Provides interactive grid manipulation, real-time updates, and enhanced
visualization features for better user experience.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging
from web_ui.components.notifications import notification_system

logger = logging.getLogger(__name__)


class InteractiveGridComponents:
    """Interactive grid visualization and manipulation components."""
    
    @staticmethod
    def create_interactive_grid_editor(config_data: Dict[str, Any]):
        """
        Create an interactive grid editor with drag-and-drop functionality.
        
        Args:
            config_data: Current configuration data
            
        Returns:
            Interactive grid editor component
        """
        try:
            # Extract grid configuration with correct key names
            grid_config = config_data.get("grid_strategy", {})
            num_grids = grid_config.get("num_grids", 10)
            bottom_price = grid_config.get("range", {}).get("bottom", 100)
            top_price = grid_config.get("range", {}).get("top", 200)
            spacing_type = grid_config.get("spacing", "arithmetic")
            
            # Generate grid levels
            grid_levels = InteractiveGridComponents._generate_grid_levels(
                num_grids, bottom_price, top_price, spacing_type
            )
            
            # Create interactive plot
            fig = go.Figure()
            
            # Add grid lines
            for i, level in enumerate(grid_levels):
                fig.add_hline(
                    y=level,
                    line_dash="dash",
                    line_color="blue" if i % 2 == 0 else "red",
                    annotation_text=f"${level:.2f}",
                    annotation_position="right"
                )
            
            # Add price range indicators
            fig.add_hrect(
                y0=bottom_price,
                y1=top_price,
                fillcolor="lightblue",
                opacity=0.1,
                layer="below",
                line_width=0
            )
            
            # Configure layout for interactivity
            fig.update_layout(
                title="Interactive Grid Configuration",
                xaxis_title="Time",
                yaxis_title="Price",
                height=500,
                showlegend=False,
                dragmode="pan",
                hovermode="y unified"
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
                    rangeslider=dict(visible=True),
                    type="date"
                )
            )
            
            return dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.I(className="fas fa-grip-lines me-2"),
                        "Interactive Grid Editor"
                    ], className="mb-0"),
                    dbc.Badge(f"{num_grids} levels", color="info", className="ms-2")
                ]),
                dbc.CardBody([
                    # Grid controls
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Grid Levels", size="sm"),
                            dbc.InputGroup([
                                dbc.Input(
                                    id="grid-levels-input",
                                    type="number",
                                    value=num_grids,
                                    min=3,
                                    max=50,
                                    size="sm"
                                ),
                                dbc.Button(
                                    html.I(className="fas fa-sync-alt"),
                                    id="refresh-grid-btn",
                                    color="outline-primary",
                                    size="sm"
                                )
                            ], size="sm")
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Bottom Price", size="sm"),
                            dbc.Input(
                                id="bottom-price-interactive",
                                type="number",
                                value=bottom_price,
                                step=0.01,
                                size="sm"
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Top Price", size="sm"),
                            dbc.Input(
                                id="top-price-interactive",
                                type="number",
                                value=top_price,
                                step=0.01,
                                size="sm"
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Spacing", size="sm"),
                            dcc.Dropdown(
                                id="spacing-interactive",
                                options=[
                                    {"label": "Arithmetic", "value": "arithmetic"},
                                    {"label": "Geometric", "value": "geometric"}
                                ],
                                value=spacing_type,
                                clearable=False,
                                style={"font-size": "0.875rem"}
                            )
                        ], width=3)
                    ], className="mb-3"),
                    
                    # Interactive plot
                    dcc.Graph(
                        id="interactive-grid-plot",
                        figure=fig,
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': 'grid_configuration',
                                'height': 500,
                                'width': 800,
                                'scale': 1
                            }
                        }
                    ),
                    
                    # Grid statistics
                    html.Div(id="grid-stats", className="mt-3")
                ])
            ])
            
        except Exception as e:
            logger.error(f"Error creating interactive grid editor: {e}")
            return notification_system.create_status_indicator(
                "error",
                "Failed to create interactive grid editor",
                details=[str(e)]
            )
    
    @staticmethod
    def create_real_time_price_overlay(config_data: Dict[str, Any], market_data: Dict[str, Any]):
        """
        Create a real-time price overlay with grid levels.
        
        Args:
            config_data: Current configuration data
            market_data: Real-time market data
            
        Returns:
            Real-time price overlay component
        """
        try:
            # Extract configuration
            exchange_name = config_data["exchange"]["name"]
            base_currency = config_data["pair"]["base_currency"]
            quote_currency = config_data["pair"]["quote_currency"]
            
            # Get current price from market data
            current_price = None
            if market_data and 'data' in market_data and market_data['data']:
                latest_data = market_data['data'][-1]
                current_price = latest_data.get('close', None)
            
            # Generate grid levels
            grid_config = config_data.get("grid_strategy", {})
            num_grids = grid_config.get("num_grids", 10)
            bottom_price = grid_config.get("bottom_price", 100)
            top_price = grid_config.get("top_price", 200)
            spacing_type = grid_config.get("spacing_type", "arithmetic")
            
            grid_levels = InteractiveGridComponents._generate_grid_levels(
                num_grids, bottom_price, top_price, spacing_type
            )
            
            # Create price indicator
            price_indicator = dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-chart-line me-2"),
                            f"{base_currency}/{quote_currency}"
                        ], className="mb-2"),
                        html.H2(
                            f"${current_price:,.2f}" if current_price else "Loading...",
                            className="text-primary mb-2",
                            id="realtime-price-display"
                        ),
                        dbc.Badge(
                            exchange_name.title(),
                            color="secondary",
                            className="me-2"
                        ),
                        dbc.Badge(
                            "LIVE" if current_price else "OFFLINE",
                            color="success" if current_price else "danger",
                            className="me-2"
                        )
                    ], className="text-center"),
                    
                    html.Hr(),
                    
                    # Grid level indicators
                    html.Div([
                        html.H6("Grid Levels", className="mb-2"),
                        html.Div(
                            InteractiveGridComponents._create_grid_level_indicators(
                                grid_levels, current_price
                            ),
                            id="grid-level-indicators"
                        )
                    ])
                ])
            ], className="mb-3")
            
            return price_indicator
            
        except Exception as e:
            logger.error(f"Error creating real-time price overlay: {e}")
            return notification_system.create_status_indicator(
                "error",
                "Failed to create price overlay",
                details=[str(e)]
            )
    
    @staticmethod
    def _generate_grid_levels(num_grids: int, bottom_price: float, top_price: float, spacing_type: str) -> List[float]:
        """Generate grid levels based on configuration."""
        if spacing_type == "geometric":
            # Geometric spacing
            ratio = (top_price / bottom_price) ** (1 / (num_grids - 1))
            levels = [bottom_price * (ratio ** i) for i in range(num_grids)]
        else:
            # Arithmetic spacing
            step = (top_price - bottom_price) / (num_grids - 1)
            levels = [bottom_price + (step * i) for i in range(num_grids)]
        
        return levels
    
    @staticmethod
    def _create_grid_level_indicators(grid_levels: List[float], current_price: Optional[float]) -> List:
        """Create visual indicators for grid levels."""
        indicators = []
        
        for i, level in enumerate(grid_levels):
            # Determine if level is above or below current price
            if current_price:
                if level > current_price:
                    color = "danger"  # Sell levels (above current price)
                    icon = "fas fa-arrow-up"
                    label = "SELL"
                else:
                    color = "success"  # Buy levels (below current price)
                    icon = "fas fa-arrow-down"
                    label = "BUY"
            else:
                color = "secondary"
                icon = "fas fa-minus"
                label = "LEVEL"
            
            indicator = dbc.Row([
                dbc.Col([
                    dbc.Badge([
                        html.I(className=icon, style={"margin-right": "4px"}),
                        label
                    ], color=color, className="badge-sm")
                ], width=3),
                dbc.Col([
                    html.Span(f"${level:.2f}", className="small")
                ], width=6),
                dbc.Col([
                    html.Span(
                        f"{((level - current_price) / current_price * 100):+.1f}%" if current_price else "N/A",
                        className="small text-muted"
                    )
                ], width=3)
            ], className="mb-1")
            
            indicators.append(indicator)
        
        return indicators


# Global instance
interactive_grid = InteractiveGridComponents()
