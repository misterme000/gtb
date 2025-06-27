"""
Visualization Components for Grid Trading Bot Web UI

Contains all chart and visualization components.
"""

import logging
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any
from web_ui.price_service import price_service
from web_ui.services.backtest_service import backtest_service
from web_ui.components.notifications import notification_system

logger = logging.getLogger(__name__)


class VisualizationComponents:
    """Class containing all visualization components."""

    @staticmethod
    def create_grid_visualization(config_data: Dict[str, Any]):
        """Create enhanced grid visualization chart with better UX."""
        try:
            if not config_data:
                return dbc.Alert("No configuration data available", color="warning")

            grid_config = config_data.get("grid_strategy", {})
            bottom = grid_config.get("range", {}).get("bottom", 100)
            top = grid_config.get("range", {}).get("top", 200)
            num_grids = grid_config.get("num_grids", 10)
            spacing_type = grid_config.get("spacing", "arithmetic")

            # Validate inputs
            if bottom >= top:
                return dbc.Alert("Bottom price must be less than top price", color="danger")
            if num_grids < 3:
                return dbc.Alert("Number of grids must be at least 3", color="danger")

            # Calculate grid levels
            if spacing_type == "arithmetic":
                grid_levels = np.linspace(bottom, top, num_grids)
            else:  # geometric
                ratio = (top / bottom) ** (1 / (num_grids - 1))
                grid_levels = [bottom * (ratio ** i) for i in range(num_grids)]

            # Create enhanced visualization
            fig = go.Figure()

            # Add background gradient
            fig.add_hrect(
                y0=bottom, y1=top,
                fillcolor="rgba(59, 130, 246, 0.1)",
                layer="below",
                line_width=0
            )

            # Add grid lines with enhanced styling
            for i, level in enumerate(grid_levels):
                is_buy_level = i < len(grid_levels) // 2
                color = "#10b981" if is_buy_level else "#ef4444"  # Green for buy, red for sell
                line_width = 2 if i == 0 or i == len(grid_levels) - 1 else 1

                fig.add_hline(
                    y=level,
                    line_dash="solid" if i == 0 or i == len(grid_levels) - 1 else "dash",
                    line_color=color,
                    line_width=line_width,
                    annotation_text=f"${level:,.2f} {'(BUY)' if is_buy_level else '(SELL)'}",
                    annotation_position="right",
                    annotation=dict(
                        bgcolor=color,
                        bordercolor=color,
                        font=dict(color="white", size=10)
                    )
                )

            # Try to get real current price
            try:
                exchange_name = config_data.get("exchange", {}).get("name", "coinbase")
                base_currency = config_data.get("pair", {}).get("base_currency", "BTC")
                quote_currency = config_data.get("pair", {}).get("quote_currency", "USDT")
                current_price = price_service.get_current_price_sync(exchange_name, base_currency, quote_currency)
            except:
                current_price = None

            # Add current price indicator
            if not current_price:
                current_price = (top + bottom) / 2  # Fallback to middle

            fig.add_hline(
                y=current_price,
                line_color="#3b82f6",
                line_width=4,
                annotation_text=f"Current: ${current_price:,.2f}",
                annotation_position="left",
                annotation=dict(
                    bgcolor="#3b82f6",
                    bordercolor="#3b82f6",
                    font=dict(color="white", size=12, family="monospace")
                )
            )

            # Enhanced styling
            fig.update_layout(
                title=dict(
                    text="Grid Trading Strategy Visualization",
                    font=dict(size=18, family="Inter"),
                    x=0.5
                ),
                yaxis_title="Price (USD)",
                height=500,
                showlegend=False,
                yaxis=dict(
                    range=[bottom * 0.9, top * 1.1],
                    tickformat="$,.2f",
                    gridcolor="rgba(0,0,0,0.1)"
                ),
                xaxis=dict(visible=False),
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=80, r=80, t=60, b=40)
            )

            # Calculate detailed statistics
            price_range = top - bottom
            grid_spacing = price_range / (num_grids - 1) if spacing_type == "arithmetic" else "Variable"
            range_percentage = (price_range / current_price) * 100 if current_price else 0

            # Calculate potential profit per grid
            trading_fee = config_data.get("exchange", {}).get("trading_fee", 0.005)
            if spacing_type == "arithmetic":
                avg_spacing = grid_spacing
                profit_per_grid = (avg_spacing / current_price - 2 * trading_fee) * 100 if current_price else 0
            else:
                avg_spacing = price_range / num_grids  # Approximation
                profit_per_grid = (avg_spacing / current_price - 2 * trading_fee) * 100 if current_price else 0

            # Enhanced summary cards
            summary_cards = dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-layer-group fa-2x text-primary mb-2"),
                                html.H4(str(num_grids), className="mb-1"),
                                html.P("Grid Levels", className="mb-0 text-muted small")
                            ], className="text-center")
                        ])
                    ], className="h-100")
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-arrows-alt-v fa-2x text-info mb-2"),
                                html.H4(f"${price_range:,.0f}", className="mb-1"),
                                html.P("Price Range", className="mb-0 text-muted small")
                            ], className="text-center")
                        ])
                    ], className="h-100")
                ], width=3)
            ], className="g-3 mt-3")

            return html.Div([
                dcc.Graph(
                    figure=fig,
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': 'grid_strategy_visualization',
                            'height': 500,
                            'width': 800,
                            'scale': 2
                        }
                    }
                ),
                summary_cards
            ])

        except Exception as e:
            logger.error(f"Error creating grid visualization: {e}")
            return dbc.Alert(f"Error creating grid visualization: {str(e)}", color="danger")

    @staticmethod
    def create_price_chart(config_data: Dict[str, Any], market_data: Dict[str, Any]):
        """Create enhanced price chart with grid overlay."""
        try:
            if not config_data:
                return dbc.Alert("No configuration data available", color="warning")

            # Simple price chart for now
            return dbc.Card([
                dbc.CardBody([
                    html.H6("Price Chart with Grid Overlay", className="mb-3"),
                    html.P("Price chart functionality will be implemented here."),
                    dbc.Alert("Historical data integration coming soon!", color="info")
                ])
            ])

        except Exception as e:
            logger.error(f"Error creating price chart: {e}")
            return dbc.Alert(f"Error creating price chart: {str(e)}", color="danger")

    @staticmethod
    def create_backtest_preview(config_data: Dict[str, Any]):
        """Create comprehensive backtest preview with enhanced analysis."""
        try:
            if not config_data:
                return dbc.Alert("No configuration data available for backtest preview", color="warning")

            # Generate backtest preview
            try:
                preview_data = backtest_service.generate_backtest_preview(config_data)
            except Exception as e:
                logger.error(f"Error generating backtest preview: {e}")
                return dbc.Alert([
                    html.H6("Backtest Preview Unavailable", className="alert-heading"),
                    html.P("Unable to generate backtest preview with current configuration."),
                    html.Hr(),
                    html.P(f"Error: {str(e)}", className="mb-0 small")
                ], color="warning")

            if "error" in preview_data:
                return dbc.Alert(f"Error generating preview: {preview_data['error']}", color="danger")

            performance = preview_data.get("performance_estimate", {})
            recommendations = preview_data.get("recommendations", [])

            # Simple backtest preview to avoid Row width error
            return dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Backtest Preview & Strategy Analysis"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        "This preview is based on historical analysis and market conditions. Actual results may vary."
                    ], color="info", className="mb-3"),

                    # Simple performance metrics
                    html.H6("Expected Performance Metrics", className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.H4(f"{performance.get('estimated_roi', 0):.1f}%", className="text-success"),
                            html.P("Expected ROI", className="text-muted")
                        ], width=3),
                        dbc.Col([
                            html.H4(f"{performance.get('estimated_trades', 0)}", className="text-info"),
                            html.P("Estimated Trades", className="text-muted")
                        ], width=3),
                        dbc.Col([
                            html.H4(f"{performance.get('max_drawdown', 0):.1f}%", className="text-warning"),
                            html.P("Max Drawdown", className="text-muted")
                        ], width=3),
                        dbc.Col([
                            html.H4(f"{performance.get('sharpe_ratio', 0):.2f}", className="text-primary"),
                            html.P("Sharpe Ratio", className="text-muted")
                        ], width=3)
                    ], className="mb-4"),

                    # Simple recommendations
                    html.H6("Recommendations", className="mb-3"),
                    html.Div([
                        dbc.Alert(rec, color="info", className="mb-2")
                        for rec in recommendations[:3]
                    ]) if recommendations else dbc.Alert("No specific recommendations available.", color="light"),

                    # Action buttons
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-play me-2"),
                                "Run Full Backtest"
                            ], id="run-full-backtest-btn", color="primary", className="w-100")
                        ], width=6),
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-refresh me-2"),
                                "Refresh Analysis"
                            ], id="refresh-analysis-btn", color="outline-secondary", className="w-100")
                        ], width=6)
                    ])
                ])
            ])

        except Exception as e:
            logger.error(f"Error creating backtest preview: {e}")
            return dbc.Alert([
                html.H6("Backtest Preview Error", className="alert-heading"),
                html.P("Unable to generate backtest preview."),
                html.Hr(),
                html.P(f"Error details: {str(e)}", className="mb-0 small")
            ], color="danger")