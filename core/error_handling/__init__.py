"""
Error Handling Module for Grid Trading Bot

This module provides unified error handling capabilities across the entire application.
"""

from .error_framework import (
    # Base classes
    GridTradingBotError,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    
    # Specific error types
    ConfigurationError,
    NetworkError,
    ExchangeError,
    OrderExecutionError,
    ValidationError,
    DataProcessingError,
    
    # Recovery mechanisms
    ErrorRecoveryStrategy,
    RetryRecoveryStrategy,
    ErrorHandler,
    
    # Global instances and decorators
    error_handler,
    handle_error_decorator
)

__all__ = [
    # Base classes
    'GridTradingBotError',
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    
    # Specific error types
    'ConfigurationError',
    'NetworkError',
    'ExchangeError',
    'OrderExecutionError',
    'ValidationError',
    'DataProcessingError',
    
    # Recovery mechanisms
    'ErrorRecoveryStrategy',
    'RetryRecoveryStrategy',
    'ErrorHandler',
    
    # Global instances and decorators
    'error_handler',
    'handle_error_decorator'
]
