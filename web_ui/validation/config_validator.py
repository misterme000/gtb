"""
Configuration Validation for Grid Trading Bot Web UI

Provides comprehensive validation for all configuration parameters.
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class UIConfigValidator:
    """Comprehensive configuration validator for the Web UI."""
    
    # Supported exchanges
    SUPPORTED_EXCHANGES = [
        "coinbase", "kraken", "bitfinex", "bitstamp", "huobi", 
        "okex", "bybit", "bittrex", "poloniex", "gate", "kucoin"
    ]
    
    # Supported timeframes
    SUPPORTED_TIMEFRAMES = [
        "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"
    ]
    
    # Trading modes
    SUPPORTED_TRADING_MODES = ["backtest", "paper_trading", "live"]
    
    # Strategy types
    SUPPORTED_STRATEGY_TYPES = ["simple_grid", "hedged_grid"]
    
    # Spacing types
    SUPPORTED_SPACING_TYPES = ["arithmetic", "geometric"]
    
    def __init__(self):
        """Initialize the validator."""
        self.errors = []
        self.warnings = []
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the entire configuration.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        try:
            # Validate each section
            self._validate_exchange_config(config.get("exchange", {}))
            self._validate_pair_config(config.get("pair", {}))
            self._validate_trading_settings(config.get("trading_settings", {}))
            self._validate_grid_strategy(config.get("grid_strategy", {}))
            self._validate_risk_management(config.get("risk_management", {}))
            
            # Cross-validation checks
            self._validate_cross_dependencies(config)
            
        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_exchange_config(self, exchange_config: Dict[str, Any]):
        """Validate exchange configuration."""
        # Exchange name
        exchange_name = exchange_config.get("name", "").lower()
        if not exchange_name:
            self.errors.append("Exchange name is required")
        elif exchange_name not in self.SUPPORTED_EXCHANGES:
            self.errors.append(f"Unsupported exchange: {exchange_name}. Supported: {', '.join(self.SUPPORTED_EXCHANGES)}")
        
        # Trading mode
        trading_mode = exchange_config.get("trading_mode", "")
        if not trading_mode:
            self.errors.append("Trading mode is required")
        elif trading_mode not in self.SUPPORTED_TRADING_MODES:
            self.errors.append(f"Invalid trading mode: {trading_mode}. Supported: {', '.join(self.SUPPORTED_TRADING_MODES)}")
        
        # Trading fee
        trading_fee = exchange_config.get("trading_fee", 0)
        if not isinstance(trading_fee, (int, float)):
            self.errors.append("Trading fee must be a number")
        elif trading_fee < 0:
            self.errors.append("Trading fee cannot be negative")
        elif trading_fee > 0.1:  # 10%
            self.warnings.append("Trading fee seems unusually high (>10%)")
    
    def _validate_pair_config(self, pair_config: Dict[str, Any]):
        """Validate trading pair configuration."""
        # Base currency
        base_currency = pair_config.get("base_currency", "").upper()
        if not base_currency:
            self.errors.append("Base currency is required")
        elif not re.match(r'^[A-Z]{2,10}$', base_currency):
            self.errors.append("Base currency must be 2-10 uppercase letters")
        
        # Quote currency
        quote_currency = pair_config.get("quote_currency", "").upper()
        if not quote_currency:
            self.errors.append("Quote currency is required")
        elif not re.match(r'^[A-Z]{2,10}$', quote_currency):
            self.errors.append("Quote currency must be 2-10 uppercase letters")
        
        # Check if same currency
        if base_currency and quote_currency and base_currency == quote_currency:
            self.errors.append("Base and quote currencies cannot be the same")
    
    def _validate_trading_settings(self, trading_settings: Dict[str, Any]):
        """Validate trading settings."""
        # Timeframe
        timeframe = trading_settings.get("timeframe", "")
        if not timeframe:
            self.errors.append("Timeframe is required")
        elif timeframe not in self.SUPPORTED_TIMEFRAMES:
            self.errors.append(f"Unsupported timeframe: {timeframe}. Supported: {', '.join(self.SUPPORTED_TIMEFRAMES)}")
        
        # Initial balance
        initial_balance = trading_settings.get("initial_balance", 0)
        if not isinstance(initial_balance, (int, float)):
            self.errors.append("Initial balance must be a number")
        elif initial_balance <= 0:
            self.errors.append("Initial balance must be positive")
        elif initial_balance < 100:
            self.warnings.append("Initial balance is very low (<$100)")
        
        # Period validation
        period = trading_settings.get("period", {})
        start_date = period.get("start_date", "")
        end_date = period.get("end_date", "")
        
        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                
                if start_dt >= end_dt:
                    self.errors.append("Start date must be before end date")
                
                # Check if date range is reasonable
                days_diff = (end_dt - start_dt).days
                if days_diff > 365:
                    self.warnings.append("Date range is very long (>1 year)")
                elif days_diff < 1:
                    self.warnings.append("Date range is very short (<1 day)")
                    
            except ValueError as e:
                self.errors.append(f"Invalid date format: {str(e)}")
    
    def _validate_grid_strategy(self, grid_strategy: Dict[str, Any]):
        """Validate grid strategy configuration."""
        # Strategy type
        strategy_type = grid_strategy.get("type", "")
        if not strategy_type:
            self.errors.append("Strategy type is required")
        elif strategy_type not in self.SUPPORTED_STRATEGY_TYPES:
            self.errors.append(f"Unsupported strategy type: {strategy_type}")
        
        # Spacing type
        spacing_type = grid_strategy.get("spacing", "")
        if not spacing_type:
            self.errors.append("Spacing type is required")
        elif spacing_type not in self.SUPPORTED_SPACING_TYPES:
            self.errors.append(f"Unsupported spacing type: {spacing_type}")
        
        # Number of grids
        num_grids = grid_strategy.get("num_grids", 0)
        if not isinstance(num_grids, int):
            self.errors.append("Number of grids must be an integer")
        elif num_grids < 3:
            self.errors.append("Number of grids must be at least 3")
        elif num_grids > 100:
            self.errors.append("Number of grids cannot exceed 100")
        elif num_grids > 50:
            self.warnings.append("Large number of grids (>50) may impact performance")
        
        # Price range
        price_range = grid_strategy.get("range", {})
        bottom_price = price_range.get("bottom", 0)
        top_price = price_range.get("top", 0)
        
        if not isinstance(bottom_price, (int, float)):
            self.errors.append("Bottom price must be a number")
        elif bottom_price <= 0:
            self.errors.append("Bottom price must be positive")
        
        if not isinstance(top_price, (int, float)):
            self.errors.append("Top price must be a number")
        elif top_price <= 0:
            self.errors.append("Top price must be positive")
        
        if bottom_price > 0 and top_price > 0:
            if bottom_price >= top_price:
                self.errors.append("Bottom price must be less than top price")
            else:
                # Calculate price range percentage
                range_percentage = ((top_price - bottom_price) / bottom_price) * 100
                if range_percentage < 5:
                    self.warnings.append("Price range is very narrow (<5%)")
                elif range_percentage > 100:
                    self.warnings.append("Price range is very wide (>100%)")
    
    def _validate_risk_management(self, risk_management: Dict[str, Any]):
        """Validate risk management configuration."""
        # Take profit
        take_profit = risk_management.get("take_profit", {})
        if take_profit.get("enabled", False):
            threshold = take_profit.get("threshold", 0)
            if not isinstance(threshold, (int, float)):
                self.errors.append("Take profit threshold must be a number")
            elif threshold <= 0:
                self.errors.append("Take profit threshold must be positive")
        
        # Stop loss
        stop_loss = risk_management.get("stop_loss", {})
        if stop_loss.get("enabled", False):
            threshold = stop_loss.get("threshold", 0)
            if not isinstance(threshold, (int, float)):
                self.errors.append("Stop loss threshold must be a number")
            elif threshold <= 0:
                self.errors.append("Stop loss threshold must be positive")
    
    def _validate_cross_dependencies(self, config: Dict[str, Any]):
        """Validate cross-dependencies between different config sections."""
        try:
            # Check if take profit/stop loss are within grid range
            grid_range = config.get("grid_strategy", {}).get("range", {})
            bottom_price = grid_range.get("bottom", 0)
            top_price = grid_range.get("top", 0)
            
            risk_mgmt = config.get("risk_management", {})
            
            # Take profit validation
            take_profit = risk_mgmt.get("take_profit", {})
            if take_profit.get("enabled", False):
                tp_threshold = take_profit.get("threshold", 0)
                if tp_threshold > 0 and top_price > 0 and tp_threshold < top_price:
                    self.warnings.append("Take profit threshold is below grid top price")
            
            # Stop loss validation
            stop_loss = risk_mgmt.get("stop_loss", {})
            if stop_loss.get("enabled", False):
                sl_threshold = stop_loss.get("threshold", 0)
                if sl_threshold > 0 and bottom_price > 0 and sl_threshold > bottom_price:
                    self.warnings.append("Stop loss threshold is above grid bottom price")
            
            # Check if initial balance is sufficient for grid strategy
            initial_balance = config.get("trading_settings", {}).get("initial_balance", 0)
            num_grids = config.get("grid_strategy", {}).get("num_grids", 0)
            
            if initial_balance > 0 and num_grids > 0:
                min_order_size = initial_balance / (num_grids * 2)  # Rough estimate
                if min_order_size < 10:  # $10 minimum
                    self.warnings.append("Initial balance may be too low for the number of grids")
                    
        except Exception as e:
            logger.warning(f"Error in cross-validation: {e}")
    
    def validate_field(self, field_name: str, value: Any, config_context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Validate a single field.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if field_name == "exchange_name":
                if not value or value.lower() not in self.SUPPORTED_EXCHANGES:
                    return False, f"Invalid exchange. Supported: {', '.join(self.SUPPORTED_EXCHANGES)}"
            
            elif field_name == "trading_fee":
                if not isinstance(value, (int, float)) or value < 0:
                    return False, "Trading fee must be a non-negative number"
                if value > 0.1:
                    return False, "Trading fee cannot exceed 10%"
            
            elif field_name == "num_grids":
                if not isinstance(value, int) or value < 3 or value > 100:
                    return False, "Number of grids must be between 3 and 100"
            
            elif field_name == "price_range":
                if config_context:
                    bottom = config_context.get("bottom", 0)
                    top = config_context.get("top", 0)
                    if bottom >= top:
                        return False, "Bottom price must be less than top price"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
