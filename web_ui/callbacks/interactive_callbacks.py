"""
Interactive Callbacks for Grid Trading Bot Web UI

Contains callbacks for interactive features, real-time updates,
and enhanced user interactions.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import html, Input, Output, State, ctx, callback
import plotly.graph_objects as go
from web_ui.components.interactive_grid import interactive_grid
from web_ui.components.notifications import notification_system, NotificationType
from web_ui.price_service import price_service

logger = logging.getLogger(__name__)


class InteractiveCallbacks:
    """Class containing all interactive callback functions."""
    
    def __init__(self, app):
        """Initialize callbacks with the Dash app."""
        self.app = app
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """Setup all interactive callbacks."""
        
        @self.app.callback(
            [Output('interactive-grid-plot', 'figure'),
             Output('grid-stats', 'children')],
            [Input('grid-levels-input', 'value'),
             Input('bottom-price-interactive', 'value'),
             Input('top-price-interactive', 'value'),
             Input('spacing-interactive', 'value'),
             Input('refresh-grid-btn', 'n_clicks')],
            [State('config-store', 'data')],
            prevent_initial_call=True
        )
        def update_interactive_grid(num_grids, bottom_price, top_price, spacing_type, refresh_clicks, config_data):
            """Update interactive grid visualization in real-time."""
            try:
                if not all([num_grids, bottom_price, top_price, spacing_type]):
                    return {}, "Please fill in all grid parameters"
                
                if bottom_price >= top_price:
                    return {}, "Bottom price must be less than top price"
                
                # Generate grid levels
                grid_levels = interactive_grid._generate_grid_levels(
                    num_grids, bottom_price, top_price, spacing_type
                )
                
                # Create figure
                fig = go.Figure()
                
                # Add grid lines with different colors for buy/sell levels
                mid_price = (bottom_price + top_price) / 2
                
                for i, level in enumerate(grid_levels):
                    color = "green" if level < mid_price else "red"
                    line_style = "solid" if i % 2 == 0 else "dash"
                    
                    fig.add_hline(
                        y=level,
                        line_dash=line_style,
                        line_color=color,
                        line_width=2,
                        annotation_text=f"${level:.2f}",
                        annotation_position="right",
                        annotation=dict(
                            bgcolor=color,
                            bordercolor=color,
                            font=dict(color="white", size=10)
                        )
                    )
                
                # Add price range background
                fig.add_hrect(
                    y0=bottom_price,
                    y1=top_price,
                    fillcolor="lightblue",
                    opacity=0.1,
                    layer="below",
                    line_width=0
                )
                
                # Add mid-line
                fig.add_hline(
                    y=mid_price,
                    line_dash="dot",
                    line_color="purple",
                    line_width=3,
                    annotation_text=f"Mid: ${mid_price:.2f}",
                    annotation_position="left"
                )
                
                # Configure layout
                fig.update_layout(
                    title=f"Interactive Grid - {num_grids} Levels ({spacing_type.title()} Spacing)",
                    xaxis_title="Time",
                    yaxis_title="Price ($)",
                    height=400,
                    showlegend=False,
                    yaxis=dict(
                        range=[bottom_price * 0.95, top_price * 1.05],
                        tickformat=".2f"
                    ),
                    xaxis=dict(
                        range=[0, 100],  # Dummy time range
                        showticklabels=False
                    ),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                
                # Generate statistics
                price_range = top_price - bottom_price
                avg_spacing = price_range / (num_grids - 1)
                
                if spacing_type == "geometric":
                    ratio = (top_price / bottom_price) ** (1 / (num_grids - 1))
                    spacing_info = f"Ratio: {ratio:.4f}"
                else:
                    spacing_info = f"Step: ${avg_spacing:.2f}"
                
                stats = dbc.Row([
                    dbc.Col([
                        html.Small([
                            html.Strong("Range: "),
                            f"${price_range:.2f}"
                        ])
                    ], width=3),
                    dbc.Col([
                        html.Small([
                            html.Strong("Avg Spacing: "),
                            f"${avg_spacing:.2f}"
                        ])
                    ], width=3),
                    dbc.Col([
                        html.Small([
                            html.Strong("Spacing Info: "),
                            spacing_info
                        ])
                    ], width=3),
                    dbc.Col([
                        html.Small([
                            html.Strong("Mid Price: "),
                            f"${mid_price:.2f}"
                        ])
                    ], width=3)
                ], className="text-muted")
                
                return fig, stats
                
            except Exception as e:
                logger.error(f"Error updating interactive grid: {e}")
                error_fig = go.Figure()
                error_fig.add_annotation(
                    text=f"Error: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="red")
                )
                error_fig.update_layout(height=400)
                return error_fig, f"Error: {str(e)}"
        
        # Temporarily disabled - grid-level-indicators only exists in interactive tab
        # @self.app.callback(
        #     [Output('current-price-display', 'children'),
        #      Output('grid-level-indicators', 'children')],
        #     [Input('price-update-interval', 'n_intervals')],
        #     [State('config-store', 'data'),
        #      State('market-data-store', 'data')],
        #     prevent_initial_call=True
        # )
        # def update_real_time_price_display(n_intervals, config_data, market_data):
        #     """Update real-time price display and grid level indicators."""
        #     try:
        #         if not config_data:
        #             return "No configuration", []
        #
        #         # Extract configuration
        #         exchange_name = config_data["exchange"]["name"]
        #         base_currency = config_data["pair"]["base_currency"]
        #         quote_currency = config_data["pair"]["quote_currency"]
        #
        #         # Get current price
        #         current_price = None
        #         if market_data and 'data' in market_data and market_data['data']:
        #             latest_data = market_data['data'][-1]
        #             current_price = latest_data.get('close', None)
        #
        #         # If no market data, try to fetch current price
        #         if not current_price:
        #             try:
        #                 current_price = price_service.get_current_price_sync(
        #                     exchange_name, base_currency, quote_currency
        #                 )
        #             except Exception as e:
        #                 logger.warning(f"Failed to fetch current price: {e}")
        #
        #         # Format price display
        #         if current_price:
        #             price_display = f"${current_price:,.2f}"
        #         else:
        #             price_display = "Loading..."
        #
        #         # Generate grid levels and indicators
        #         grid_config = config_data.get("grid_strategy", {})
        #         num_grids = grid_config.get("num_grids", 10)
        #         bottom_price = grid_config.get("bottom_price", 100)
        #         top_price = grid_config.get("top_price", 200)
        #         spacing_type = grid_config.get("spacing_type", "arithmetic")
        #
        #         grid_levels = interactive_grid._generate_grid_levels(
        #             num_grids, bottom_price, top_price, spacing_type
        #         )
        #
        #         indicators = interactive_grid._create_grid_level_indicators(
        #             grid_levels, current_price
        #         )
        #
        #         return price_display, indicators
        #
        #     except Exception as e:
        #         logger.error(f"Error updating real-time price display: {e}")
        #         return "Error", [html.Div(f"Error: {str(e)}", className="text-danger")]
        
        @self.app.callback(
            Output('config-store', 'data', allow_duplicate=True),
            [Input('grid-levels-input', 'value'),
             Input('bottom-price-interactive', 'value'),
             Input('top-price-interactive', 'value'),
             Input('spacing-interactive', 'value')],
            [State('config-store', 'data')],
            prevent_initial_call=True
        )
        def sync_interactive_grid_to_config(num_grids, bottom_price, top_price, spacing_type, current_config):
            """Sync interactive grid changes back to main configuration."""
            try:
                if not current_config:
                    return current_config
                
                # Update grid strategy configuration
                if all([num_grids, bottom_price, top_price, spacing_type]):
                    current_config["grid_strategy"]["num_grids"] = num_grids
                    current_config["grid_strategy"]["bottom_price"] = bottom_price
                    current_config["grid_strategy"]["top_price"] = top_price
                    current_config["grid_strategy"]["spacing_type"] = spacing_type
                
                return current_config
                
            except Exception as e:
                logger.error(f"Error syncing interactive grid to config: {e}")
                return current_config
        
        @self.app.callback(
            Output('toast-container', 'children', allow_duplicate=True),
            [Input('refresh-grid-btn', 'n_clicks')],
            [State('toast-container', 'children'),
             State('config-store', 'data')],
            prevent_initial_call=True
        )
        def handle_grid_refresh(n_clicks, current_toasts, config_data):
            """Handle grid refresh button click with user feedback."""
            if not n_clicks:
                return current_toasts or []
            
            toasts = current_toasts or []
            
            try:
                # Add success toast
                success_toast = notification_system.create_toast(
                    "Grid configuration refreshed successfully!",
                    NotificationType.SUCCESS,
                    title="Grid Refreshed",
                    duration=3000
                )
                toasts.append(success_toast)
                
                return toasts
                
            except Exception as e:
                logger.error(f"Error handling grid refresh: {e}")
                error_toast = notification_system.create_toast(
                    f"Failed to refresh grid: {str(e)}",
                    NotificationType.ERROR,
                    title="Refresh Failed"
                )
                toasts.append(error_toast)
                return toasts
