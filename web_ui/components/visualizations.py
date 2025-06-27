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

logger = logging.getLogger(__name__)


class VisualizationComponents:
    """Class containing all visualization components."""
    
    @staticmethod
    def create_grid_visualization(config_data: Dict[str, Any]):
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
    
    @staticmethod
    def create_price_chart(config_data: Dict[str, Any], market_data: Dict[str, Any]):
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
    
    @staticmethod
    def create_backtest_preview(config_data: Dict[str, Any]):
        """Create comprehensive backtest preview with real analysis."""
        try:
            # Generate backtest preview
            preview_data = backtest_service.generate_backtest_preview(config_data)

            if "error" in preview_data:
                return dbc.Alert(f"Error generating preview: {preview_data['error']}", color="danger")

            performance = preview_data.get("performance_estimate", {})
            market = preview_data.get("market_analysis", {})
            recommendations = preview_data.get("recommendations", [])

            return dbc.Card([
                dbc.CardBody([
                    html.H6("Backtest Preview & Analysis", className="card-title"),

                    # Performance Metrics
                    html.H6("Expected Performance Metrics:", className="mt-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4(f"{performance.get('estimated_roi', 0)}%",
                                           className="text-success" if performance.get('estimated_roi', 0) > 0 else "text-danger"),
                                    html.P("Expected ROI", className="mb-0")
                                ])
                            ])
                        ], width=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4(f"{performance.get('estimated_trades', 0)}", className="text-info"),
                                    html.P("Estimated Trades", className="mb-0")
                                ])
                            ])
                        ], width=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4(f"{performance.get('max_drawdown', 0)}%", className="text-warning"),
                                    html.P("Max Drawdown", className="mb-0")
                                ])
                            ])
                        ], width=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H4(f"{performance.get('sharpe_ratio', 0)}", className="text-primary"),
                                    html.P("Sharpe Ratio", className="mb-0")
                                ])
                            ])
                        ], width=3)
                    ], className="mb-3"),

                    # Market Analysis
                    html.H6("Market Analysis:", className="mt-3"),
                    dbc.Row([
                        dbc.Col([
                            html.P([
                                html.Strong("Current Price: "),
                                f"${market.get('current_price', 0):,.2f}" if market.get('current_price') else "N/A"
                            ]),
                            html.P([
                                html.Strong("24h Change: "),
                                f"{market.get('price_change_24h', 0):+.2f}%"
                            ]),
                            html.P([
                                html.Strong("Volatility: "),
                                f"{market.get('volatility', 0):.2f}%"
                            ])
                        ], width=6),
                        dbc.Col([
                            html.P([
                                html.Strong("Grid Coverage: "),
                                f"{market.get('grid_coverage', 0):.1f}%"
                            ]),
                            html.P([
                                html.Strong("Price in Range: "),
                                "✅ Yes" if market.get('price_in_range', False) else "❌ No"
                            ]),
                            html.P([
                                html.Strong("Data Points: "),
                                f"{market.get('data_points', 0)}"
                            ])
                        ], width=6)
                    ], className="mb-3"),

                    # Recommendations
                    html.H6("Recommendations:", className="mt-3"),
                    html.Div([
                        dbc.Alert(rec, color="info", className="mb-2")
                        for rec in recommendations[:5]  # Limit to 5 recommendations
                    ]) if recommendations else html.P("No specific recommendations at this time."),

                    # Action Buttons
                    html.Hr(),
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-play me-2"),
                            "Run Full Backtest"
                        ], id="run-full-backtest-btn", color="primary"),
                        dbc.Button([
                            html.I(className="fas fa-refresh me-2"),
                            "Refresh Analysis"
                        ], id="refresh-analysis-btn", color="outline-secondary")
                    ])
                ])
            ])

        except Exception as e:
            logger.error(f"Error creating backtest preview: {e}")
            return dbc.Alert(f"Error creating backtest preview: {str(e)}", color="danger")
