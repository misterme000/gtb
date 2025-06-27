"""
Action Callbacks for Grid Trading Bot Web UI

Contains callbacks for user actions like validation, saving, and price suggestions.
"""

import json
import logging
import base64
from typing import Dict, Any

import dash
from dash import Input, Output, State, ctx, dcc, html
from web_ui.price_service import price_service
from web_ui.validation.config_validator import UIConfigValidator
from web_ui.utils.config_manager import ui_config_manager

logger = logging.getLogger(__name__)


class ActionCallbacks:
    """Class containing all action callback functions."""
    
    def __init__(self, app):
        """Initialize callbacks with the Dash app."""
        self.app = app
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """Setup all action callbacks."""
        
        @self.app.callback(
            [Output('status-alert', 'children'),
             Output('status-alert', 'color'),
             Output('status-alert', 'is_open')],
            [Input('validate-btn', 'n_clicks'),
             Input('save-btn', 'n_clicks'),
             Input('export-btn', 'n_clicks')],
            [State('config-store', 'data')]
        )
        def handle_actions(validate_clicks, save_clicks, export_clicks, config_data):
            """Handle action button clicks."""
            if not ctx.triggered:
                return "", "info", False
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'validate-btn' and validate_clicks:
                try:
                    # Comprehensive validation
                    validator = UIConfigValidator()
                    is_valid, errors, warnings = validator.validate_config(config_data)

                    if is_valid:
                        if warnings:
                            warning_text = "\n".join([f"• {w}" for w in warnings])
                            return f"✅ Configuration is valid!\n\nWarnings:\n{warning_text}", "warning", True
                        else:
                            return "✅ Configuration is valid! No issues found.", "success", True
                    else:
                        error_text = "\n".join([f"• {e}" for e in errors])
                        warning_text = "\n".join([f"• {w}" for w in warnings]) if warnings else ""

                        message = f"❌ Configuration has errors:\n{error_text}"
                        if warning_text:
                            message += f"\n\nWarnings:\n{warning_text}"

                        return message, "danger", True

                except Exception as e:
                    return f"❌ Validation error: {str(e)}", "danger", True
            
            elif button_id == 'save-btn' and save_clicks:
                try:
                    # Save configuration using config manager
                    success, result = ui_config_manager.save_config(config_data)
                    if success:
                        return f"✅ Configuration saved to {result}", "success", True
                    else:
                        return f"❌ Save error: {result}", "danger", True
                except Exception as e:
                    return f"❌ Save error: {str(e)}", "danger", True

            elif button_id == 'export-btn' and export_clicks:
                try:
                    # Export configuration for download
                    success, base64_data, filename = ui_config_manager.export_config_for_download(config_data)
                    if success:
                        return f"✅ Configuration ready for download as {filename}", "success", True
                    else:
                        return f"❌ Export error: {base64_data}", "danger", True
                except Exception as e:
                    return f"❌ Export error: {str(e)}", "danger", True
            
            return "", "info", False
        
        @self.app.callback(
            [Output('bottom-price-input', 'value'),
             Output('top-price-input', 'value'),
             Output('status-alert', 'children', allow_duplicate=True),
             Output('status-alert', 'color', allow_duplicate=True),
             Output('status-alert', 'is_open', allow_duplicate=True)],
            [Input('suggest-range-btn', 'n_clicks')],
            [State('base-currency-input', 'value'),
             State('quote-currency-input', 'value'),
             State('exchange-select', 'value')],
            prevent_initial_call=True
        )
        def suggest_price_range(n_clicks, base_currency, quote_currency, exchange):
            """Suggest price range based on current market price."""
            if not n_clicks or not base_currency or not quote_currency or not exchange:
                return dash.no_update, dash.no_update, "", "info", False
            
            try:
                # Get current price
                current_price = price_service.get_current_price_sync(exchange, base_currency, quote_currency)
                
                if current_price:
                    # Suggest range based on current price
                    bottom, top = price_service.get_price_range_suggestion(current_price)
                    message = f"Range suggested based on current price ${current_price:,.2f}"
                    return bottom, top, message, "success", True
                else:
                    return dash.no_update, dash.no_update, "Unable to fetch current price", "danger", True
                    
            except Exception as e:
                logger.error(f"Error suggesting price range: {e}")
                return dash.no_update, dash.no_update, f"Error: {str(e)}", "danger", True

        # Real-time field validation callbacks
        @self.app.callback(
            [Output('trading-fee-input', 'valid'),
             Output('trading-fee-input', 'invalid')],
            [Input('trading-fee-input', 'value')]
        )
        def validate_trading_fee(value):
            """Real-time validation for trading fee."""
            if value is None:
                return None, None

            validator = UIConfigValidator()
            is_valid, _ = validator.validate_field("trading_fee", value / 100 if value else 0)
            return is_valid, not is_valid

        @self.app.callback(
            [Output('num-grids-input', 'valid'),
             Output('num-grids-input', 'invalid')],
            [Input('num-grids-input', 'value')]
        )
        def validate_num_grids(value):
            """Real-time validation for number of grids."""
            if value is None:
                return None, None

            validator = UIConfigValidator()
            is_valid, _ = validator.validate_field("num_grids", value)
            return is_valid, not is_valid

        @self.app.callback(
            [Output('bottom-price-input', 'valid'),
             Output('bottom-price-input', 'invalid'),
             Output('top-price-input', 'valid'),
             Output('top-price-input', 'invalid')],
            [Input('bottom-price-input', 'value'),
             Input('top-price-input', 'value')]
        )
        def validate_price_range(bottom_price, top_price):
            """Real-time validation for price range."""
            if bottom_price is None or top_price is None:
                return None, None, None, None

            # Individual validations
            bottom_valid = bottom_price > 0 if bottom_price is not None else False
            top_valid = top_price > 0 if top_price is not None else False

            # Range validation
            if bottom_price and top_price and bottom_price >= top_price:
                bottom_valid = False
                top_valid = False

            return bottom_valid, not bottom_valid, top_valid, not top_valid

        # Import/Export callbacks
        @self.app.callback(
            [Output('config-store', 'data', allow_duplicate=True),
             Output('status-alert', 'children', allow_duplicate=True),
             Output('status-alert', 'color', allow_duplicate=True),
             Output('status-alert', 'is_open', allow_duplicate=True)],
            [Input('upload-config', 'contents')],
            [State('upload-config', 'filename')],
            prevent_initial_call=True
        )
        def import_config(contents, filename):
            """Import configuration from uploaded file."""
            if contents is None:
                return dash.no_update, "", "info", False

            try:
                # Decode the uploaded file
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string).decode('utf-8')

                # Import configuration
                success, config, message = ui_config_manager.import_config_from_upload(decoded)

                if success:
                    return config, f"✅ {message}", "success", True
                else:
                    return dash.no_update, f"❌ Import failed: {message}", "danger", True

            except Exception as e:
                return dash.no_update, f"❌ Import error: {str(e)}", "danger", True

        @self.app.callback(
            Output('download-config', 'children'),
            [Input('export-btn', 'n_clicks')],
            [State('config-store', 'data')],
            prevent_initial_call=True
        )
        def export_config_download(n_clicks, config_data):
            """Create download link for configuration export."""
            if not n_clicks or not config_data:
                return ""

            try:
                success, base64_data, filename = ui_config_manager.export_config_for_download(config_data)

                if success:
                    # Create download link
                    download_link = html.A(
                        "Download Configuration",
                        id="download-link",
                        download=filename,
                        href=f"data:application/json;base64,{base64_data}",
                        target="_blank",
                        style={"display": "none"}
                    )

                    # Auto-trigger download
                    return html.Div([
                        download_link,
                        dcc.Interval(
                            id="download-trigger",
                            interval=100,
                            n_intervals=0,
                            max_intervals=1
                        )
                    ])
                else:
                    return ""

            except Exception as e:
                logger.error(f"Export download error: {e}")
                return ""
