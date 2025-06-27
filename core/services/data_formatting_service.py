"""
Unified Data Formatting Service for Grid Trading Bot

Provides standardized data formatting, validation, and transformation
across all components of the trading bot system.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Tuple
from decimal import Decimal, ROUND_HALF_UP
from core.error_handling import (
    ErrorContext, ErrorCategory, ErrorSeverity,
    DataProcessingError, ValidationError, error_handler, handle_error_decorator
)


class DataFormattingService:
    """
    Unified service for data formatting, validation, and transformation.
    
    This service ensures consistent data formats across the entire application
    and provides validation middleware for data integrity.
    """
    
    def __init__(self):
        """Initialize the data formatting service."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._precision_cache = {}
    
    @handle_error_decorator(
        category=ErrorCategory.DATA_PROCESSING,
        severity=ErrorSeverity.MEDIUM,
        recovery_suggestions=[
            "Check data format and structure",
            "Verify timestamp format",
            "Ensure numeric values are valid"
        ]
    )
    def format_ohlcv_data(
        self, 
        raw_data: Union[List, pd.DataFrame], 
        symbol: str,
        timeframe: str,
        validate: bool = True
    ) -> pd.DataFrame:
        """
        Format OHLCV data into standardized DataFrame.
        
        Args:
            raw_data: Raw OHLCV data (list of lists or DataFrame)
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1h', '1d')
            validate: Whether to validate the data
            
        Returns:
            Standardized OHLCV DataFrame
        """
        try:
            if isinstance(raw_data, pd.DataFrame):
                df = raw_data.copy()
            else:
                if not raw_data:
                    return self._create_empty_ohlcv_dataframe()
                
                df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Standardize column names
            df = self._standardize_ohlcv_columns(df)
            
            # Format timestamp
            df = self._format_timestamps(df)
            
            # Format numeric columns
            df = self._format_ohlcv_numeric_columns(df, symbol)
            
            # Add metadata
            df.attrs['symbol'] = symbol
            df.attrs['timeframe'] = timeframe
            df.attrs['formatted_at'] = datetime.now(timezone.utc).isoformat()
            
            # Validate if requested
            if validate:
                self._validate_ohlcv_data(df, symbol)
            
            self.logger.debug(f"Formatted {len(df)} OHLCV records for {symbol}")
            return df
            
        except Exception as e:
            context = ErrorContext(
                operation="format_ohlcv_data",
                component="DataFormattingService",
                additional_data={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data_length": len(raw_data) if raw_data else 0
                }
            )
            raise DataProcessingError(
                f"Failed to format OHLCV data for {symbol}: {str(e)}",
                context=context,
                original_exception=e
            )
    
    def format_order_data(
        self, 
        raw_order: Dict[str, Any], 
        exchange_name: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Format order data into standardized format.
        
        Args:
            raw_order: Raw order data from exchange
            exchange_name: Name of the exchange
            validate: Whether to validate the data
            
        Returns:
            Standardized order dictionary
        """
        try:
            formatted_order = {
                'id': self._safe_string(raw_order.get('id')),
                'symbol': self._safe_string(raw_order.get('symbol')),
                'side': self._safe_string(raw_order.get('side', '')).lower(),
                'type': self._safe_string(raw_order.get('type', '')).lower(),
                'amount': self._safe_decimal(raw_order.get('amount', 0)),
                'price': self._safe_decimal(raw_order.get('price', 0)),
                'status': self._safe_string(raw_order.get('status', 'unknown')).lower(),
                'filled': self._safe_decimal(raw_order.get('filled', 0)),
                'remaining': self._safe_decimal(raw_order.get('remaining', 0)),
                'cost': self._safe_decimal(raw_order.get('cost', 0)),
                'timestamp': self._safe_timestamp(raw_order.get('timestamp')),
                'datetime': self._safe_datetime(raw_order.get('datetime')),
                'fee': self._format_fee_data(raw_order.get('fee', {})),
                'exchange': exchange_name.lower(),
                'formatted_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Calculate derived fields
            if formatted_order['amount'] and formatted_order['filled']:
                formatted_order['fill_percentage'] = float(
                    (formatted_order['filled'] / formatted_order['amount']) * 100
                )
            else:
                formatted_order['fill_percentage'] = 0.0
            
            # Validate if requested
            if validate:
                self._validate_order_data(formatted_order)
            
            return formatted_order
            
        except Exception as e:
            context = ErrorContext(
                operation="format_order_data",
                component="DataFormattingService",
                additional_data={
                    "exchange": exchange_name,
                    "order_id": raw_order.get('id', 'unknown')
                }
            )
            raise DataProcessingError(
                f"Failed to format order data: {str(e)}",
                context=context,
                original_exception=e
            )
    
    def format_balance_data(
        self, 
        raw_balance: Dict[str, Any], 
        exchange_name: str
    ) -> Dict[str, Any]:
        """
        Format balance data into standardized format.
        
        Args:
            raw_balance: Raw balance data from exchange
            exchange_name: Name of the exchange
            
        Returns:
            Standardized balance dictionary
        """
        try:
            formatted_balance = {
                'exchange': exchange_name.lower(),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total': {},
                'free': {},
                'used': {},
                'currencies': []
            }
            
            # Process each currency
            for currency, balance_info in raw_balance.items():
                if currency in ['info', 'timestamp', 'datetime']:
                    continue
                
                if isinstance(balance_info, dict):
                    total = self._safe_decimal(balance_info.get('total', 0))
                    free = self._safe_decimal(balance_info.get('free', 0))
                    used = self._safe_decimal(balance_info.get('used', 0))
                else:
                    total = self._safe_decimal(balance_info)
                    free = total
                    used = Decimal('0')
                
                if total > 0:
                    formatted_balance['total'][currency] = float(total)
                    formatted_balance['free'][currency] = float(free)
                    formatted_balance['used'][currency] = float(used)
                    formatted_balance['currencies'].append(currency)
            
            return formatted_balance
            
        except Exception as e:
            context = ErrorContext(
                operation="format_balance_data",
                component="DataFormattingService",
                additional_data={"exchange": exchange_name}
            )
            raise DataProcessingError(
                f"Failed to format balance data: {str(e)}",
                context=context,
                original_exception=e
            )
    
    def format_price_data(
        self, 
        price: Union[str, int, float, Decimal], 
        symbol: str,
        precision: Optional[int] = None
    ) -> Decimal:
        """
        Format price data with appropriate precision.
        
        Args:
            price: Raw price value
            symbol: Trading symbol for precision lookup
            precision: Optional explicit precision
            
        Returns:
            Formatted price as Decimal
        """
        try:
            decimal_price = self._safe_decimal(price)
            
            if precision is None:
                precision = self._get_symbol_precision(symbol)
            
            # Round to appropriate precision
            quantize_exp = Decimal('0.1') ** precision
            formatted_price = decimal_price.quantize(quantize_exp, rounding=ROUND_HALF_UP)
            
            return formatted_price
            
        except Exception as e:
            raise DataProcessingError(f"Failed to format price {price} for {symbol}: {str(e)}")
    
    def validate_trading_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate trading data for completeness and correctness.
        
        Args:
            data: Trading data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Required fields validation
            required_fields = ['symbol', 'side', 'amount', 'price']
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Missing required field: {field}")
            
            # Data type validation
            if 'amount' in data:
                try:
                    amount = float(data['amount'])
                    if amount <= 0:
                        errors.append("Amount must be positive")
                except (ValueError, TypeError):
                    errors.append("Amount must be a valid number")
            
            if 'price' in data:
                try:
                    price = float(data['price'])
                    if price <= 0:
                        errors.append("Price must be positive")
                except (ValueError, TypeError):
                    errors.append("Price must be a valid number")
            
            # Side validation
            if 'side' in data:
                valid_sides = ['buy', 'sell']
                if str(data['side']).lower() not in valid_sides:
                    errors.append(f"Side must be one of: {valid_sides}")
            
            # Symbol format validation
            if 'symbol' in data:
                symbol = str(data['symbol'])
                if '/' not in symbol:
                    errors.append("Symbol must be in BASE/QUOTE format (e.g., BTC/USDT)")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def _standardize_ohlcv_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize OHLCV column names."""
        column_mapping = {
            'time': 'timestamp',
            'datetime': 'timestamp',
            'date': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume',
            'vol': 'volume'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                if col == 'volume':
                    df[col] = 0  # Default volume to 0 if missing
                else:
                    raise ValueError(f"Required column '{col}' not found in data")
        
        return df[required_columns]
    
    def _format_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format timestamp column and set as index."""
        if 'timestamp' in df.columns:
            # Convert to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
            
            # Remove any rows with invalid timestamps
            df = df.dropna(subset=['timestamp'])
            
            # Set as index
            df.set_index('timestamp', inplace=True)
        
        return df
    
    def _format_ohlcv_numeric_columns(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Format numeric columns in OHLCV data."""
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        
        for col in numeric_columns:
            if col in df.columns:
                # Convert to numeric, coercing errors to NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Remove rows with NaN values in price columns
                if col != 'volume':
                    df = df.dropna(subset=[col])
        
        return df
    
    def _create_empty_ohlcv_dataframe(self) -> pd.DataFrame:
        """Create an empty OHLCV DataFrame with proper structure."""
        df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        df.index = pd.DatetimeIndex([], name='timestamp')
        return df
    
    def _validate_ohlcv_data(self, df: pd.DataFrame, symbol: str):
        """Validate OHLCV data for consistency."""
        if df.empty:
            return
        
        # Check for negative prices
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if (df[col] < 0).any():
                raise ValidationError(f"Negative prices found in {col} column for {symbol}")
        
        # Check high >= low
        if (df['high'] < df['low']).any():
            raise ValidationError(f"High price less than low price found for {symbol}")
        
        # Check open, close within high-low range
        if ((df['open'] > df['high']) | (df['open'] < df['low'])).any():
            raise ValidationError(f"Open price outside high-low range for {symbol}")
        
        if ((df['close'] > df['high']) | (df['close'] < df['low'])).any():
            raise ValidationError(f"Close price outside high-low range for {symbol}")
    
    def _validate_order_data(self, order: Dict[str, Any]):
        """Validate order data for consistency."""
        # Check required fields
        required_fields = ['id', 'symbol', 'side', 'type', 'amount']
        for field in required_fields:
            if not order.get(field):
                raise ValidationError(f"Missing or empty required field: {field}")
        
        # Validate side
        if order['side'] not in ['buy', 'sell']:
            raise ValidationError(f"Invalid order side: {order['side']}")
        
        # Validate type
        valid_types = ['market', 'limit', 'stop', 'stop_limit']
        if order['type'] not in valid_types:
            raise ValidationError(f"Invalid order type: {order['type']}")
        
        # Validate amounts
        if order['amount'] <= 0:
            raise ValidationError("Order amount must be positive")
        
        if order['filled'] > order['amount']:
            raise ValidationError("Filled amount cannot exceed order amount")
    
    def _safe_string(self, value: Any) -> str:
        """Safely convert value to string."""
        if value is None:
            return ""
        return str(value)
    
    def _safe_decimal(self, value: Any) -> Decimal:
        """Safely convert value to Decimal."""
        if value is None or value == "":
            return Decimal('0')
        try:
            return Decimal(str(value))
        except:
            return Decimal('0')
    
    def _safe_timestamp(self, value: Any) -> Optional[int]:
        """Safely convert value to timestamp."""
        if value is None:
            return None
        try:
            return int(value)
        except:
            return None
    
    def _safe_datetime(self, value: Any) -> Optional[str]:
        """Safely convert value to datetime string."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
    
    def _format_fee_data(self, fee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format fee data."""
        if not fee_data:
            return {'cost': 0, 'currency': None, 'rate': None}
        
        return {
            'cost': float(self._safe_decimal(fee_data.get('cost', 0))),
            'currency': self._safe_string(fee_data.get('currency')),
            'rate': float(self._safe_decimal(fee_data.get('rate', 0))) if fee_data.get('rate') else None
        }
    
    def _get_symbol_precision(self, symbol: str) -> int:
        """Get precision for a trading symbol."""
        # Cache precision values to avoid repeated calculations
        if symbol in self._precision_cache:
            return self._precision_cache[symbol]
        
        # Default precision based on common patterns
        if 'USDT' in symbol or 'USD' in symbol:
            precision = 2
        elif 'BTC' in symbol:
            precision = 8
        else:
            precision = 4
        
        self._precision_cache[symbol] = precision
        return precision


class DataValidationMiddleware:
    """
    Middleware for data validation in the trading bot pipeline.

    This middleware can be used to validate data at various points
    in the application flow to ensure data integrity.
    """

    def __init__(self, formatter: DataFormattingService):
        """
        Initialize validation middleware.

        Args:
            formatter: Data formatting service instance
        """
        self.formatter = formatter
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_and_format_order(self, raw_order: Dict[str, Any], exchange_name: str) -> Dict[str, Any]:
        """
        Validate and format order data with comprehensive checks.

        Args:
            raw_order: Raw order data
            exchange_name: Exchange name

        Returns:
            Validated and formatted order data

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Format the order first
            formatted_order = self.formatter.format_order_data(raw_order, exchange_name, validate=False)

            # Perform comprehensive validation
            is_valid, errors = self.formatter.validate_trading_data(formatted_order)

            if not is_valid:
                raise ValidationError(f"Order validation failed: {'; '.join(errors)}")

            # Additional business logic validation
            self._validate_order_business_rules(formatted_order)

            self.logger.debug(f"Order validation passed for {formatted_order['id']}")
            return formatted_order

        except Exception as e:
            context = ErrorContext(
                operation="validate_and_format_order",
                component="DataValidationMiddleware",
                additional_data={
                    "exchange": exchange_name,
                    "order_id": raw_order.get('id', 'unknown')
                }
            )

            if isinstance(e, ValidationError):
                raise
            else:
                raise ValidationError(
                    f"Order validation failed: {str(e)}",
                    context=context,
                    original_exception=e
                )

    def validate_market_data(self, data: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Validate market data for trading operations.

        Args:
            data: Market data DataFrame
            symbol: Trading symbol
            timeframe: Data timeframe

        Returns:
            Validated DataFrame

        Raises:
            ValidationError: If validation fails
        """
        try:
            if data.empty:
                raise ValidationError(f"Empty market data for {symbol}")

            # Check for minimum data requirements
            min_required_points = 10
            if len(data) < min_required_points:
                raise ValidationError(
                    f"Insufficient market data for {symbol}: {len(data)} points, "
                    f"minimum {min_required_points} required"
                )

            # Check for data gaps
            self._check_data_continuity(data, timeframe)

            # Check for outliers
            self._check_price_outliers(data, symbol)

            self.logger.debug(f"Market data validation passed for {symbol}")
            return data

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Market data validation failed for {symbol}: {str(e)}")

    def _validate_order_business_rules(self, order: Dict[str, Any]):
        """Validate order against business rules."""
        # Minimum order size validation
        min_order_value = 10.0  # $10 minimum
        order_value = float(order['amount']) * float(order['price'])

        if order_value < min_order_value:
            raise ValidationError(
                f"Order value ${order_value:.2f} below minimum ${min_order_value:.2f}"
            )

        # Maximum order size validation (safety check)
        max_order_value = 100000.0  # $100k maximum
        if order_value > max_order_value:
            raise ValidationError(
                f"Order value ${order_value:.2f} exceeds maximum ${max_order_value:.2f}"
            )

    def _check_data_continuity(self, data: pd.DataFrame, timeframe: str):
        """Check for gaps in time series data."""
        if len(data) < 2:
            return

        # Expected time delta based on timeframe
        timeframe_deltas = {
            '1m': pd.Timedelta(minutes=1),
            '5m': pd.Timedelta(minutes=5),
            '15m': pd.Timedelta(minutes=15),
            '1h': pd.Timedelta(hours=1),
            '4h': pd.Timedelta(hours=4),
            '1d': pd.Timedelta(days=1)
        }

        expected_delta = timeframe_deltas.get(timeframe, pd.Timedelta(hours=1))

        # Check for gaps larger than 2x expected delta
        time_diffs = data.index.to_series().diff()
        large_gaps = time_diffs > (expected_delta * 2)

        if large_gaps.any():
            gap_count = large_gaps.sum()
            self.logger.warning(f"Found {gap_count} data gaps in {timeframe} data")

    def _check_price_outliers(self, data: pd.DataFrame, symbol: str):
        """Check for price outliers that might indicate data quality issues."""
        if len(data) < 10:
            return

        # Calculate price change percentages
        price_changes = data['close'].pct_change().abs()

        # Flag changes > 50% as potential outliers
        outlier_threshold = 0.5
        outliers = price_changes > outlier_threshold

        if outliers.any():
            outlier_count = outliers.sum()
            max_change = price_changes.max() * 100
            self.logger.warning(
                f"Found {outlier_count} potential price outliers in {symbol} data "
                f"(max change: {max_change:.1f}%)"
            )


# Global instances
data_formatter = DataFormattingService()
data_validator = DataValidationMiddleware(data_formatter)
