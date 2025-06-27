"""
Main Callbacks for Grid Trading Bot Web UI

Contains all callback functions for the Dash application.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

import dash
from dash import Input, Output, State, ctx
from web_ui.price_service import price_service
from web_ui.components.visualizations import VisualizationComponents
from web_ui.components.interactive_grid import interactive_grid
from config.config_validator import ConfigValidator

logger = logging.getLogger(__name__)


class MainCallbacks:
    """Class containing all main callback functions."""
    
    def __init__(self, app):
        """Initialize callbacks with the Dash app."""
        self.app = app
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """Setup all the callbacks for the application."""
        
        @self.app.callback(
            Output('viz-content', 'children'),
            [Input('viz-tabs', 'active_tab'),
             Input('config-store', 'data'),
             Input('market-data-store', 'data')]
        )
        def update_visualization(active_tab, config_data, market_data):
            """Update visualization based on active tab and configuration."""
            if active_tab == "grid-tab":
                return VisualizationComponents.create_grid_visualization(config_data)
            elif active_tab == "interactive-tab":
                return interactive_grid.create_interactive_grid_editor(config_data)
            elif active_tab == "chart-tab":
                return VisualizationComponents.create_price_chart(config_data, market_data)
            elif active_tab == "realtime-tab":
                return interactive_grid.create_real_time_price_overlay(config_data, market_data)
            elif active_tab == "backtest-tab":
                return VisualizationComponents.create_backtest_preview(config_data)
            return "Select a tab to view visualization"
        
        @self.app.callback(
            Output('config-store', 'data'),
            [Input('exchange-select', 'value'),
             Input('trading-mode-select', 'value'),
             Input('trading-fee-input', 'value'),
             Input('base-currency-input', 'value'),
             Input('quote-currency-input', 'value'),
             Input('strategy-type-select', 'value'),
             Input('spacing-type-select', 'value'),
             Input('num-grids-input', 'value'),
             Input('bottom-price-input', 'value'),
             Input('top-price-input', 'value'),
             Input('take-profit-enabled', 'value'),
             Input('take-profit-threshold', 'value'),
             Input('stop-loss-enabled', 'value'),
             Input('stop-loss-threshold', 'value'),
             Input('timeframe-select', 'value'),
             Input('initial-balance-input', 'value'),
             Input('start-date-input', 'value'),
             Input('end-date-input', 'value')],
            [State('config-store', 'data')]
        )
        def update_config(exchange, trading_mode, trading_fee, base_currency, quote_currency,
                         strategy_type, spacing_type, num_grids, bottom_price, top_price,
                         tp_enabled, tp_threshold, sl_enabled, sl_threshold,
                         timeframe, initial_balance, start_date, end_date, current_config):
            """Update configuration based on form inputs."""
            
            if not current_config:
                # Load default config if none exists
                from web_ui.app import GridBotUI
                current_config = GridBotUI()._load_default_config()
            
            # Update configuration
            current_config["exchange"]["name"] = exchange or "coinbase"
            current_config["exchange"]["trading_mode"] = trading_mode or "backtest"
            current_config["exchange"]["trading_fee"] = (trading_fee or 0.5) / 100
            
            current_config["pair"]["base_currency"] = (base_currency or "BTC").upper()
            current_config["pair"]["quote_currency"] = (quote_currency or "USDT").upper()
            
            current_config["grid_strategy"]["type"] = strategy_type or "simple_grid"
            current_config["grid_strategy"]["spacing"] = spacing_type or "arithmetic"
            current_config["grid_strategy"]["num_grids"] = num_grids or 10
            current_config["grid_strategy"]["range"]["bottom"] = bottom_price or 90000
            current_config["grid_strategy"]["range"]["top"] = top_price or 100000
            
            current_config["risk_management"]["take_profit"]["enabled"] = "enabled" in (tp_enabled or [])
            current_config["risk_management"]["take_profit"]["threshold"] = tp_threshold or 0
            current_config["risk_management"]["stop_loss"]["enabled"] = "enabled" in (sl_enabled or [])
            current_config["risk_management"]["stop_loss"]["threshold"] = sl_threshold or 0
            
            current_config["trading_settings"]["timeframe"] = timeframe or "1h"
            current_config["trading_settings"]["initial_balance"] = initial_balance or 10000
            
            if start_date:
                current_config["trading_settings"]["period"]["start_date"] = start_date + "Z"
            if end_date:
                current_config["trading_settings"]["period"]["end_date"] = end_date + "Z"
            
            return current_config
        
        @self.app.callback(
            [Output('live-price-badge', 'children'),
             Output('live-price-badge', 'color')],
            [Input('price-update-interval', 'n_intervals'),
             Input('base-currency-input', 'value'),
             Input('quote-currency-input', 'value'),
             Input('exchange-select', 'value')]
        )
        def update_live_price(n_intervals, base_currency, quote_currency, exchange):
            """Update live price badge with real data."""
            try:
                if not base_currency or not quote_currency or not exchange:
                    return "Live Price: $--", "secondary"

                # Get current price using synchronous wrapper with timeout
                price = price_service.get_current_price_sync(exchange, base_currency, quote_currency)

                if price:
                    pair = f"{base_currency}/{quote_currency}"
                    return f"Live Price: ${price:,.2f} ({pair})", "success"
                else:
                    return f"Live Price: Unable to fetch", "warning"

            except Exception as e:
                logger.error(f"Error fetching live price: {e}")
                return f"Live Price: Error", "danger"
        
        @self.app.callback(
            Output('market-data-store', 'data'),
            [Input('chart-update-interval', 'n_intervals'),
             Input('base-currency-input', 'value'),
             Input('quote-currency-input', 'value'),
             Input('exchange-select', 'value'),
             Input('timeframe-select', 'value')]
        )
        def update_market_data(n_intervals, base_currency, quote_currency, exchange, timeframe):
            """Update market data for charts."""
            if not base_currency or not quote_currency or not exchange:
                return {}
            
            try:
                # Get historical data
                df = price_service.get_historical_data_sync(
                    exchange, base_currency, quote_currency, timeframe, limit=168
                )
                
                if df is not None and not df.empty:
                    # Convert DataFrame to dict for storage
                    market_data = {
                        'symbol': f"{base_currency}/{quote_currency}",
                        'exchange': exchange,
                        'timeframe': timeframe,
                        'data': df.to_dict('records'),
                        'timestamps': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        'last_update': datetime.now().isoformat()
                    }
                    return market_data
                else:
                    return {'error': 'Failed to fetch market data'}
                    
            except Exception as e:
                logger.error(f"Error updating market data: {e}")
                return {'error': str(e)}
