"""
Unified Error Handling Framework for Grid Trading Bot

This module provides a comprehensive error handling framework that standardizes
error types, recovery mechanisms, and user-facing error messages across the entire codebase.
"""

import logging
import traceback
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels for categorizing errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for better organization and handling."""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    EXCHANGE = "exchange"
    ORDER_EXECUTION = "order_execution"
    DATA_PROCESSING = "data_processing"
    VALIDATION = "validation"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class ErrorContext:
    """Context information for errors to provide better debugging and recovery."""
    
    def __init__(
        self,
        operation: str,
        component: str,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.component = component
        self.additional_data = additional_data or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary for logging and serialization."""
        return {
            "operation": self.operation,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "additional_data": self.additional_data
        }


class GridTradingBotError(Exception):
    """
    Base exception class for all Grid Trading Bot errors.
    
    Provides standardized error handling with severity, category, context,
    and recovery suggestions.
    """
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: Optional[ErrorContext] = None,
        original_exception: Optional[Exception] = None,
        recovery_suggestions: Optional[List[str]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context
        self.original_exception = original_exception
        self.recovery_suggestions = recovery_suggestions or []
        self.user_message = user_message or self._generate_user_message()
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID for tracking."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{self.category.value}_{timestamp}"
    
    def _generate_user_message(self) -> str:
        """Generate a user-friendly error message."""
        if self.category == ErrorCategory.CONFIGURATION:
            return "There's an issue with the configuration. Please check your settings."
        elif self.category == ErrorCategory.NETWORK:
            return "Network connection issue. Please check your internet connection and try again."
        elif self.category == ErrorCategory.EXCHANGE:
            return "Exchange service issue. The trading platform may be temporarily unavailable."
        elif self.category == ErrorCategory.ORDER_EXECUTION:
            return "Order execution failed. Please check your account balance and try again."
        elif self.category == ErrorCategory.VALIDATION:
            return "Invalid input detected. Please check your parameters and try again."
        else:
            return "An unexpected error occurred. Please try again or contact support."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging and serialization."""
        return {
            "error_id": self.error_id,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context.to_dict() if self.context else None,
            "recovery_suggestions": self.recovery_suggestions,
            "original_exception": str(self.original_exception) if self.original_exception else None,
            "traceback": traceback.format_exc() if self.original_exception else None
        }


class ConfigurationError(GridTradingBotError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.CONFIGURATION)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        super().__init__(message, **kwargs)


class NetworkError(GridTradingBotError):
    """Network-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.NETWORK)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        kwargs.setdefault('recovery_suggestions', [
            "Check your internet connection",
            "Verify firewall settings",
            "Try again in a few moments"
        ])
        super().__init__(message, **kwargs)


class ExchangeError(GridTradingBotError):
    """Exchange service-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.EXCHANGE)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('recovery_suggestions', [
            "Check exchange API credentials",
            "Verify exchange service status",
            "Try again later"
        ])
        super().__init__(message, **kwargs)


class OrderExecutionError(GridTradingBotError):
    """Order execution-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.ORDER_EXECUTION)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('recovery_suggestions', [
            "Check account balance",
            "Verify order parameters",
            "Check market conditions"
        ])
        super().__init__(message, **kwargs)


class ValidationError(GridTradingBotError):
    """Validation-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.VALIDATION)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        super().__init__(message, **kwargs)


class DataProcessingError(GridTradingBotError):
    """Data processing-related errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.DATA_PROCESSING)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        super().__init__(message, **kwargs)


class ErrorRecoveryStrategy(ABC):
    """Abstract base class for error recovery strategies."""
    
    @abstractmethod
    async def can_recover(self, error: GridTradingBotError) -> bool:
        """Check if this strategy can recover from the given error."""
        pass
    
    @abstractmethod
    async def recover(self, error: GridTradingBotError) -> bool:
        """Attempt to recover from the error. Returns True if successful."""
        pass


class RetryRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy that retries the operation with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def can_recover(self, error: GridTradingBotError) -> bool:
        """Can recover from network and temporary exchange errors."""
        return error.category in [ErrorCategory.NETWORK, ErrorCategory.EXCHANGE]
    
    async def recover(self, error: GridTradingBotError) -> bool:
        """Implement retry logic with exponential backoff."""
        # This would be implemented by the calling code
        # This is a placeholder for the recovery mechanism
        return False


class ErrorHandler:
    """
    Centralized error handler that provides consistent error processing,
    logging, and recovery across the application.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.recovery_strategies: List[ErrorRecoveryStrategy] = []
        self.error_callbacks: List[Callable[[GridTradingBotError], None]] = []
    
    def add_recovery_strategy(self, strategy: ErrorRecoveryStrategy):
        """Add a recovery strategy to the handler."""
        self.recovery_strategies.append(strategy)
    
    def add_error_callback(self, callback: Callable[[GridTradingBotError], None]):
        """Add a callback to be called when errors occur."""
        self.error_callbacks.append(callback)
    
    async def handle_error(
        self,
        error: Union[Exception, GridTradingBotError],
        context: Optional[ErrorContext] = None,
        attempt_recovery: bool = True
    ) -> Optional[GridTradingBotError]:
        """
        Handle an error with logging, recovery attempts, and notifications.
        
        Args:
            error: The error to handle
            context: Additional context information
            attempt_recovery: Whether to attempt automatic recovery
            
        Returns:
            The processed GridTradingBotError or None if recovered
        """
        # Convert to GridTradingBotError if needed
        if not isinstance(error, GridTradingBotError):
            grid_error = GridTradingBotError(
                message=str(error),
                context=context,
                original_exception=error
            )
        else:
            grid_error = error
            if context and not grid_error.context:
                grid_error.context = context
        
        # Log the error
        self._log_error(grid_error)
        
        # Attempt recovery if enabled
        if attempt_recovery:
            recovery_successful = await self._attempt_recovery(grid_error)
            if recovery_successful:
                self.logger.info(f"Successfully recovered from error {grid_error.error_id}")
                return None
        
        # Call error callbacks
        for callback in self.error_callbacks:
            try:
                callback(grid_error)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
        
        return grid_error
    
    def _log_error(self, error: GridTradingBotError):
        """Log the error with appropriate level based on severity."""
        error_dict = error.to_dict()
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR [{error.error_id}]: {error.message}", extra=error_dict)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"ERROR [{error.error_id}]: {error.message}", extra=error_dict)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"WARNING [{error.error_id}]: {error.message}", extra=error_dict)
        else:
            self.logger.info(f"INFO [{error.error_id}]: {error.message}", extra=error_dict)
    
    async def _attempt_recovery(self, error: GridTradingBotError) -> bool:
        """Attempt to recover from the error using available strategies."""
        for strategy in self.recovery_strategies:
            try:
                if await strategy.can_recover(error):
                    self.logger.info(f"Attempting recovery for error {error.error_id} using {strategy.__class__.__name__}")
                    if await strategy.recover(error):
                        return True
            except Exception as e:
                self.logger.error(f"Recovery strategy {strategy.__class__.__name__} failed: {e}")
        
        return False


# Global error handler instance
error_handler = ErrorHandler()


def handle_error_decorator(
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_suggestions: Optional[List[str]] = None
):
    """
    Decorator for automatic error handling in functions.
    
    Usage:
        @handle_error_decorator(category=ErrorCategory.ORDER_EXECUTION)
        async def place_order(...):
            # function implementation
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except GridTradingBotError:
                raise  # Re-raise GridTradingBotError as-is
            except Exception as e:
                context = ErrorContext(
                    operation=func.__name__,
                    component=func.__module__,
                    additional_data={"args": str(args), "kwargs": str(kwargs)}
                )
                
                grid_error = GridTradingBotError(
                    message=f"Error in {func.__name__}: {str(e)}",
                    category=category,
                    severity=severity,
                    context=context,
                    original_exception=e,
                    recovery_suggestions=recovery_suggestions
                )
                
                handled_error = await error_handler.handle_error(grid_error)
                if handled_error:
                    raise handled_error
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except GridTradingBotError:
                raise  # Re-raise GridTradingBotError as-is
            except Exception as e:
                context = ErrorContext(
                    operation=func.__name__,
                    component=func.__module__,
                    additional_data={"args": str(args), "kwargs": str(kwargs)}
                )
                
                grid_error = GridTradingBotError(
                    message=f"Error in {func.__name__}: {str(e)}",
                    category=category,
                    severity=severity,
                    context=context,
                    original_exception=e,
                    recovery_suggestions=recovery_suggestions
                )
                
                # For sync functions, we can't use async recovery
                error_handler._log_error(grid_error)
                raise grid_error
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
