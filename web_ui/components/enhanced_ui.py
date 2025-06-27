"""
Enhanced UI Components for Grid Trading Bot Web UI

Provides modern, interactive components with improved user experience,
accessibility, and visual feedback.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class EnhancedUIComponents:
    """Enhanced UI components with modern design patterns."""
    
    @staticmethod
    def create_smart_input_group(
        label: str,
        input_id: str,
        input_type: str = "number",
        value: Any = None,
        placeholder: str = "",
        help_text: str = "",
        prefix: str = "",
        suffix: str = "",
        validation_rules: Dict[str, Any] = None,
        **kwargs
    ):
        """
        Create a smart input group with validation, help text, and visual feedback.
        
        Args:
            label: Input label
            input_id: Unique ID for the input
            input_type: Type of input (number, text, email, etc.)
            value: Default value
            placeholder: Placeholder text
            help_text: Help text to display
            prefix: Text/symbol to show before input (e.g., "$")
            suffix: Text/symbol to show after input (e.g., "%")
            validation_rules: Dictionary of validation rules
            **kwargs: Additional props for the input component
        """
        # Create input component based on type
        if input_type == "select":
            input_component = dbc.Select(
                id=input_id,
                value=value,
                placeholder=placeholder,
                **kwargs
            )
        elif input_type == "textarea":
            input_component = dbc.Textarea(
                id=input_id,
                value=value,
                placeholder=placeholder,
                **kwargs
            )
        else:
            input_component = dbc.Input(
                id=input_id,
                type=input_type,
                value=value,
                placeholder=placeholder,
                **kwargs
            )
        
        # Wrap with prefix/suffix if provided
        if prefix or suffix:
            input_component = dbc.InputGroup([
                dbc.InputGroupText(prefix) if prefix else None,
                input_component,
                dbc.InputGroupText(suffix) if suffix else None
            ])
        
        # Build the complete input group
        components = [
            dbc.Label(label, html_for=input_id, className="form-label"),
            input_component
        ]
        
        # Add help text if provided
        if help_text:
            components.append(
                dbc.FormText(help_text, className="text-muted")
            )
        
        # Add validation feedback placeholder
        components.extend([
            dbc.FormFeedback("", id=f"{input_id}-feedback", type="invalid"),
            dbc.FormFeedback("Looks good!", id=f"{input_id}-valid-feedback", type="valid")
        ])
        
        return html.Div(components, className="mb-3")
    
    @staticmethod
    def create_metric_dashboard(metrics: List[Dict[str, Any]]):
        """
        Create a metrics dashboard with animated counters and trend indicators.
        
        Args:
            metrics: List of metric dictionaries with keys:
                - title: Metric title
                - value: Current value
                - previous_value: Previous value for trend calculation
                - format: Format string (e.g., "${:.2f}", "{:.1%}")
                - color: Color theme (primary, success, warning, danger)
                - icon: FontAwesome icon class
        """
        metric_cards = []
        
        for metric in metrics:
            title = metric.get("title", "")
            value = metric.get("value", 0)
            previous_value = metric.get("previous_value")
            format_str = metric.get("format", "{}")
            color = metric.get("color", "primary")
            icon = metric.get("icon", "fas fa-chart-line")
            
            # Calculate trend
            trend = None
            trend_icon = ""
            trend_color = ""
            
            if previous_value is not None and previous_value != 0:
                change = ((value - previous_value) / previous_value) * 100
                if change > 0:
                    trend = f"+{change:.1f}%"
                    trend_icon = "fas fa-arrow-up"
                    trend_color = "success"
                elif change < 0:
                    trend = f"{change:.1f}%"
                    trend_icon = "fas fa-arrow-down"
                    trend_color = "danger"
                else:
                    trend = "0%"
                    trend_icon = "fas fa-minus"
                    trend_color = "secondary"
            
            # Format the value
            try:
                formatted_value = format_str.format(value)
            except:
                formatted_value = str(value)
            
            card_content = [
                html.Div([
                    html.I(className=f"{icon} fa-2x text-{color} mb-3"),
                    html.H3(formatted_value, className="mb-1 fw-bold", 
                           style={"font-family": "monospace"}),
                    html.P(title, className="mb-2 text-muted small text-uppercase"),
                    
                    # Trend indicator
                    html.Div([
                        html.I(className=f"{trend_icon} me-1"),
                        html.Span(trend)
                    ], className=f"text-{trend_color} small fw-bold") if trend else None
                    
                ], className="text-center")
            ]
            
            metric_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody(card_content)
                    ], className="metric-card-enhanced h-100 border-0 shadow-sm")
                ], width=12, md=6, lg=3, className="mb-3")
            )
        
        return dbc.Row(metric_cards, className="g-3")
    
    @staticmethod
    def create_interactive_price_chart(
        data: Dict[str, Any],
        grid_levels: List[float] = None,
        height: int = 500,
        show_volume: bool = True
    ):
        """
        Create an interactive price chart with grid overlay and enhanced features.
        
        Args:
            data: Price data dictionary with OHLCV data
            grid_levels: List of grid price levels to overlay
            height: Chart height in pixels
            show_volume: Whether to show volume subplot
        """
        if not data or 'data' not in data:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line fa-3x text-muted mb-3"),
                    html.H5("No Data Available", className="text-muted"),
                    html.P("Configure your trading pair to load price data", 
                          className="text-muted")
                ], className="text-center py-5")
            ])
        
        df = data['data']
        
        # Create subplots
        from plotly.subplots import make_subplots
        
        subplot_titles = ["Price"] + (["Volume"] if show_volume else [])
        fig = make_subplots(
            rows=2 if show_volume else 1,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=subplot_titles,
            row_heights=[0.7, 0.3] if show_volume else [1.0]
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="Price",
                increasing_line_color='#10b981',
                decreasing_line_color='#ef4444'
            ),
            row=1, col=1
        )
        
        # Add grid levels if provided
        if grid_levels:
            for i, level in enumerate(grid_levels):
                fig.add_hline(
                    y=level,
                    line_dash="dot",
                    line_color="#3b82f6" if i % 2 == 0 else "#f59e0b",
                    line_width=1,
                    annotation_text=f"${level:.2f}",
                    annotation_position="right",
                    row=1, col=1
                )
        
        # Add volume if requested
        if show_volume and 'volume' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name="Volume",
                    marker_color='rgba(59, 130, 246, 0.3)',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Update layout
        fig.update_layout(
            height=height,
            showlegend=False,
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            margin=dict(l=0, r=0, t=30, b=0),
            hovermode='x unified'
        )
        
        # Update axes
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        return dcc.Graph(
            figure=fig,
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'grid_trading_chart',
                    'height': height,
                    'width': 1200,
                    'scale': 2
                }
            },
            className="border rounded"
        )
    
    @staticmethod
    def create_configuration_wizard(steps: List[Dict[str, Any]], current_step: int = 0):
        """
        Create a configuration wizard with step navigation.
        
        Args:
            steps: List of step dictionaries with keys:
                - title: Step title
                - description: Step description
                - content: Step content (Dash component)
                - validation: Validation function (optional)
            current_step: Current active step index
        """
        # Create step indicator
        step_names = [step['title'] for step in steps]
        step_indicator = create_step_indicator(step_names, current_step)
        
        # Get current step content
        current_step_data = steps[current_step] if current_step < len(steps) else steps[0]
        
        # Navigation buttons
        nav_buttons = []
        
        if current_step > 0:
            nav_buttons.append(
                dbc.Button([
                    html.I(className="fas fa-arrow-left me-2"),
                    "Previous"
                ], id="wizard-prev-btn", color="outline-secondary")
            )
        
        if current_step < len(steps) - 1:
            nav_buttons.append(
                dbc.Button([
                    "Next",
                    html.I(className="fas fa-arrow-right ms-2")
                ], id="wizard-next-btn", color="primary")
            )
        else:
            nav_buttons.append(
                dbc.Button([
                    html.I(className="fas fa-check me-2"),
                    "Complete"
                ], id="wizard-complete-btn", color="success")
            )
        
        return dbc.Card([
            dbc.CardBody([
                # Step indicator
                step_indicator,
                
                # Current step content
                html.Div([
                    html.H4(current_step_data['title'], className="mb-2"),
                    html.P(current_step_data['description'], className="text-muted mb-4"),
                    current_step_data['content']
                ]),
                
                # Navigation
                html.Hr(),
                html.Div(
                    nav_buttons,
                    className="d-flex justify-content-between"
                )
            ])
        ])


# Helper function for step indicator (imported from notifications)
from web_ui.components.notifications import create_step_indicator
