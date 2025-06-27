"""
Base Exchange Service for Grid Trading Bot

Provides common functionality and patterns for all exchange service implementations.
This reduces code duplication and ensures consistent behavior across different exchange types.
"""

import logging
import time
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Callable
import ccxt
import pandas as pd
from config.config_manager import ConfigManager
from .exchange_interface import ExchangeInterface
from .exceptions import (
    UnsupportedExchangeError, DataFetchError, MissingEnvironmentVariableError,
    UnsupportedTimeframeError, UnsupportedPairError
)
from core.error_handling import (
    ErrorContext, ErrorCategory, ErrorSeverity,
    NetworkError, ExchangeError, error_handler, handle_error_decorator
)


class BaseExchangeService(ExchangeInterface, ABC):
    """
    Base class for all exchange services providing common functionality.
    
    This class implements common patterns like:
    - Exchange initialization
    - Error handling
    - Retry mechanisms
    - Data formatting
    - Validation
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize base exchange service.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exchange_name = self.config_manager.get_exchange_name()
        self.exchange = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the service with common setup."""
        try:
            self.exchange = self._create_exchange_instance()
            self._validate_exchange_configuration()
            self.logger.info(f"Initialized {self.__class__.__name__} for {self.exchange_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            raise
    
    @abstractmethod
    def _create_exchange_instance(self) -> ccxt.Exchange:
        """Create and configure the exchange instance. Must be implemented by subclasses."""
        pass
    
    def _validate_exchange_configuration(self):
        """Validate exchange configuration. Can be overridden by subclasses."""
        if not self.exchange_name:
            raise ValueError("Exchange name is required")
        
        if not hasattr(ccxt, self.exchange_name):
            raise UnsupportedExchangeError(f"Exchange '{self.exchange_name}' is not supported by ccxt")
    
    def _get_env_variable(self, key: str, required: bool = True) -> Optional[str]:
        """
        Get environment variable with optional requirement check.
        
        Args:
            key: Environment variable key
            required: Whether the variable is required
            
        Returns:
            Environment variable value or None if not required and not found
            
        Raises:
            MissingEnvironmentVariableError: If required variable is missing
        """
        value = os.getenv(key)
        if required and value is None:
            raise MissingEnvironmentVariableError(f"Missing required environment variable: {key}")
        return value
    
    @handle_error_decorator(
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        recovery_suggestions=[
            "Check network connectivity",
            "Verify exchange API status",
            "Try again in a few moments"
        ]
    )
    def _fetch_with_retry(
        self,
        method: Callable,
        *args,
        retries: int = 3,
        delay: float = 2.0,
        backoff_factor: float = 2.0,
        **kwargs
    ) -> Any:
        """
        Execute a method with retry logic and exponential backoff.
        
        Args:
            method: Method to execute
            *args: Positional arguments for the method
            retries: Maximum number of retry attempts
            delay: Initial delay between retries in seconds
            backoff_factor: Factor to multiply delay by after each retry
            **kwargs: Keyword arguments for the method
            
        Returns:
            Result of the method execution
            
        Raises:
            DataFetchError: If all retry attempts fail
        """
        last_exception = None
        current_delay = delay
        
        for attempt in range(retries + 1):  # +1 for initial attempt
            try:
                result = method(*args, **kwargs)
                if attempt > 0:
                    self.logger.info(f"Retry successful after {attempt} attempts")
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < retries:
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{retries + 1} failed: {str(e)}. "
                        f"Retrying in {current_delay:.1f} seconds..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    self.logger.error(f"All {retries + 1} attempts failed. Last error: {str(e)}")
        
        # Create error context for the final failure
        context = ErrorContext(
            operation=method.__name__ if hasattr(method, '__name__') else str(method),
            component=self.__class__.__name__,
            additional_data={
                "args": str(args),
                "kwargs": str(kwargs),
                "retries": retries,
                "final_delay": current_delay / backoff_factor
            }
        )
        
        raise DataFetchError(
            f"Failed to execute {method.__name__ if hasattr(method, '__name__') else 'method'} "
            f"after {retries + 1} attempts: {str(last_exception)}"
        )
    
    def _format_ohlcv_data(self, ohlcv_data: list, until_timestamp: Optional[int] = None) -> pd.DataFrame:
        """
        Format OHLCV data into a standardized DataFrame.
        
        Args:
            ohlcv_data: Raw OHLCV data from exchange
            until_timestamp: Optional timestamp to filter data until
            
        Returns:
            Formatted DataFrame with timestamp index
        """
        if not ohlcv_data:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        
        try:
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime and set as index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Filter by until_timestamp if provided
            if until_timestamp:
                until_dt = pd.to_datetime(until_timestamp, unit='ms')
                df = df[df.index <= until_dt]
            
            # Ensure numeric types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            self.logger.debug(f"Formatted {len(df)} OHLCV records")
            return df
            
        except Exception as e:
            self.logger.error(f"Error formatting OHLCV data: {e}")
            raise DataFetchError(f"Failed to format OHLCV data: {str(e)}")
    
    def _validate_trading_pair(self, pair: str) -> bool:
        """
        Validate if a trading pair is supported by the exchange.
        
        Args:
            pair: Trading pair to validate (e.g., 'BTC/USDT')
            
        Returns:
            True if pair is supported, False otherwise
        """
        try:
            if not self.exchange:
                return False
            
            # Load markets if not already loaded
            if not hasattr(self.exchange, 'markets') or not self.exchange.markets:
                self.exchange.load_markets()
            
            return pair in self.exchange.markets
            
        except Exception as e:
            self.logger.warning(f"Could not validate trading pair {pair}: {e}")
            return False
    
    def _validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate if a timeframe is supported by the exchange.
        
        Args:
            timeframe: Timeframe to validate (e.g., '1h', '1d')
            
        Returns:
            True if timeframe is supported, False otherwise
        """
        try:
            if not self.exchange:
                return False
            
            return timeframe in self.exchange.timeframes
            
        except Exception as e:
            self.logger.warning(f"Could not validate timeframe {timeframe}: {e}")
            return False
    
    def _standardize_order_response(self, order_response: Dict[str, Any]) -> Dict[str, Union[str, float]]:
        """
        Standardize order response format across different exchanges.
        
        Args:
            order_response: Raw order response from exchange
            
        Returns:
            Standardized order response
        """
        try:
            standardized = {
                'id': str(order_response.get('id', '')),
                'symbol': str(order_response.get('symbol', '')),
                'side': str(order_response.get('side', '')),
                'type': str(order_response.get('type', '')),
                'amount': float(order_response.get('amount', 0.0)),
                'price': float(order_response.get('price', 0.0)),
                'status': str(order_response.get('status', 'unknown')),
                'timestamp': order_response.get('timestamp', 0),
                'filled': float(order_response.get('filled', 0.0)),
                'remaining': float(order_response.get('remaining', 0.0)),
                'cost': float(order_response.get('cost', 0.0)),
                'fee': order_response.get('fee', {})
            }
            
            return standardized
            
        except Exception as e:
            self.logger.error(f"Error standardizing order response: {e}")
            raise DataFetchError(f"Failed to standardize order response: {str(e)}")
    
    def _log_operation(self, operation: str, **kwargs):
        """
        Log operation with consistent format and additional context.
        
        Args:
            operation: Name of the operation
            **kwargs: Additional context to log
        """
        context_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"[{self.exchange_name.upper()}] {operation}: {context_str}")
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information and capabilities.
        
        Returns:
            Dictionary with exchange information
        """
        try:
            info = {
                'name': self.exchange_name,
                'class': self.__class__.__name__,
                'has_markets': hasattr(self.exchange, 'markets') and bool(self.exchange.markets),
                'timeframes': getattr(self.exchange, 'timeframes', {}),
                'capabilities': {
                    'fetch_ticker': getattr(self.exchange, 'has', {}).get('fetchTicker', False),
                    'fetch_ohlcv': getattr(self.exchange, 'has', {}).get('fetchOHLCV', False),
                    'fetch_balance': getattr(self.exchange, 'has', {}).get('fetchBalance', False),
                    'create_order': getattr(self.exchange, 'has', {}).get('createOrder', False),
                    'cancel_order': getattr(self.exchange, 'has', {}).get('cancelOrder', False),
                    'websocket': getattr(self.exchange, 'has', {}).get('ws', False)
                }
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting exchange info: {e}")
            return {
                'name': self.exchange_name,
                'class': self.__class__.__name__,
                'error': str(e)
            }


class ExchangeServiceMixin:
    """
    Mixin class providing additional utility methods for exchange services.
    """
    
    def calculate_order_cost(self, amount: float, price: float, fee_rate: float = 0.001) -> Dict[str, float]:
        """
        Calculate order cost including fees.
        
        Args:
            amount: Order amount
            price: Order price
            fee_rate: Fee rate (default 0.1%)
            
        Returns:
            Dictionary with cost breakdown
        """
        base_cost = amount * price
        fee = base_cost * fee_rate
        total_cost = base_cost + fee
        
        return {
            'base_cost': base_cost,
            'fee': fee,
            'total_cost': total_cost,
            'fee_rate': fee_rate
        }
    
    def format_trading_pair(self, base: str, quote: str) -> str:
        """
        Format trading pair in exchange-specific format.
        
        Args:
            base: Base currency
            quote: Quote currency
            
        Returns:
            Formatted trading pair
        """
        return f"{base.upper()}/{quote.upper()}"
    
    def parse_trading_pair(self, pair: str) -> tuple:
        """
        Parse trading pair into base and quote currencies.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            
        Returns:
            Tuple of (base, quote) currencies
        """
        try:
            base, quote = pair.split('/')
            return base.upper(), quote.upper()
        except ValueError:
            raise ValueError(f"Invalid trading pair format: {pair}. Expected format: 'BASE/QUOTE'")


# Export base classes for use by implementations
__all__ = ['BaseExchangeService', 'ExchangeServiceMixin']
