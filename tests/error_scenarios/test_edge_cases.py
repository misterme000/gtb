"""
Edge Case Tests for Grid Trading Bot

Tests for edge cases, boundary conditions, data corruption scenarios,
and other unusual conditions that could cause system failures.
"""

import pytest
import sys
import math
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.services.data_formatting_service import data_formatter, data_validator
from core.services.live_exchange_service import LiveExchangeService
from core.services.backtest_exchange_service import BacktestExchangeService
from core.services.exceptions import DataFetchError, ValidationError
from core.grid_strategy.grid_calculator import GridCalculator
from config.config_manager import ConfigManager
from web_ui.price_service import price_service


class TestDataCorruptionScenarios:
    """Test handling of corrupted or malformed data."""
    
    def test_corrupted_ohlcv_data_handling(self):
        """Test handling of corrupted OHLCV data."""
        
        # Test various corruption scenarios
        corruption_scenarios = [
            # Missing values
            [[1640995200000, None, 51000, 49000, 50000, 100]],
            # Negative prices
            [[1640995200000, -50000, 51000, 49000, 50000, 100]],
            # Invalid high/low relationship
            [[1640995200000, 50000, 49000, 51000, 50000, 100]],  # high < low
            # Extreme values
            [[1640995200000, float('inf'), 51000, 49000, 50000, 100]],
            # NaN values
            [[1640995200000, float('nan'), 51000, 49000, 50000, 100]],
            # String values where numbers expected
            [[1640995200000, "invalid", 51000, 49000, 50000, 100]],
            # Missing columns
            [[1640995200000, 50000, 51000]],  # Only 3 values instead of 6
            # Extra columns
            [[1640995200000, 50000, 51000, 49000, 50000, 100, "extra", "data"]],
        ]
        
        for i, corrupted_data in enumerate(corruption_scenarios):
            try:
                df = data_formatter.format_ohlcv_data(
                    corrupted_data, 
                    "BTC/USD", 
                    "1h", 
                    validate=True
                )
                
                # If formatting succeeds, data should be cleaned
                if not df.empty:
                    assert not df.isnull().any().any(), f"Scenario {i}: NaN values remain"
                    assert (df['high'] >= df['low']).all(), f"Scenario {i}: Invalid high/low relationship"
                    assert (df > 0).all().all(), f"Scenario {i}: Non-positive values remain"
                
            except (ValidationError, ValueError, DataFetchError):
                # Expected for severely corrupted data
                pass
    
    def test_malformed_order_data_handling(self):
        """Test handling of malformed order data."""
        
        malformed_orders = [
            # Missing required fields
            {'symbol': 'BTC/USD', 'side': 'buy'},
            # Invalid side
            {'id': 'order1', 'symbol': 'BTC/USD', 'side': 'invalid', 'amount': 0.001, 'price': 50000},
            # Negative amounts
            {'id': 'order2', 'symbol': 'BTC/USD', 'side': 'buy', 'amount': -0.001, 'price': 50000},
            # Zero price
            {'id': 'order3', 'symbol': 'BTC/USD', 'side': 'buy', 'amount': 0.001, 'price': 0},
            # String amounts
            {'id': 'order4', 'symbol': 'BTC/USD', 'side': 'buy', 'amount': "invalid", 'price': 50000},
            # Infinite values
            {'id': 'order5', 'symbol': 'BTC/USD', 'side': 'buy', 'amount': float('inf'), 'price': 50000},
            # NaN values
            {'id': 'order6', 'symbol': 'BTC/USD', 'side': 'buy', 'amount': float('nan'), 'price': 50000},
        ]
        
        for order in malformed_orders:
            with pytest.raises((ValidationError, ValueError, DataFetchError)):
                data_validator.validate_and_format_order(order, "binance")
    
    def test_extreme_numerical_values(self):
        """Test handling of extreme numerical values."""
        
        extreme_values = [
            1e-18,  # Very small
            1e18,   # Very large
            sys.float_info.max,  # Maximum float
            sys.float_info.min,  # Minimum positive float
            Decimal('0.000000000000000001'),  # Very small decimal
            Decimal('999999999999999999999'),  # Very large decimal
        ]
        
        for value in extreme_values:
            try:
                # Test price formatting
                formatted_price = data_formatter.format_price_data(value, "BTC/USD")
                assert isinstance(formatted_price, Decimal)
                assert formatted_price >= 0
                
            except (ValueError, InvalidOperation, OverflowError):
                # Expected for some extreme values
                pass
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters in data."""
        
        special_strings = [
            "BTC/USD\x00",  # Null character
            "BTC/USD\n\r\t",  # Whitespace characters
            "BTC/USD🚀",  # Unicode emoji
            "BTC/USD\u200b",  # Zero-width space
            "BTC/USD' OR 1=1--",  # SQL injection attempt
            "<script>alert('xss')</script>",  # XSS attempt
            "../../etc/passwd",  # Path traversal attempt
        ]
        
        for special_string in special_strings:
            try:
                # Test order data with special characters
                order = {
                    'id': special_string,
                    'symbol': special_string,
                    'side': 'buy',
                    'amount': 0.001,
                    'price': 50000,
                    'status': 'open'
                }
                
                formatted_order = data_formatter.format_order_data(order, "binance", validate=False)
                
                # Should sanitize or handle special characters
                assert isinstance(formatted_order['id'], str)
                assert isinstance(formatted_order['symbol'], str)
                
            except (ValidationError, ValueError):
                # Expected for invalid data
                pass


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_grid_calculation_edge_cases(self):
        """Test grid calculation with edge case parameters."""
        calculator = GridCalculator()
        
        edge_cases = [
            # Minimum grids
            (2, 50000, 60000, "arithmetic"),
            # Maximum reasonable grids
            (1000, 50000, 60000, "arithmetic"),
            # Very small price range
            (10, 50000.00, 50000.01, "arithmetic"),
            # Very large price range
            (10, 1, 1000000, "geometric"),
            # Equal bottom and top prices
            (10, 50000, 50000, "arithmetic"),
            # Reversed prices (should be handled)
            (10, 60000, 50000, "arithmetic"),
        ]
        
        for num_grids, bottom, top, spacing in edge_cases:
            try:
                levels = calculator.calculate_grid_levels(num_grids, bottom, top, spacing)
                
                if bottom != top and bottom < top:
                    assert len(levels) == num_grids
                    assert levels[0] == bottom
                    assert levels[-1] == top
                
            except (ValueError, ZeroDivisionError):
                # Expected for invalid parameters
                pass
    
    def test_timestamp_edge_cases(self):
        """Test timestamp handling edge cases."""
        
        edge_timestamps = [
            0,  # Unix epoch
            -1,  # Before epoch
            2147483647,  # 32-bit max timestamp
            4294967295,  # 32-bit unsigned max
            1640995200000,  # Normal millisecond timestamp
            1640995200,  # Normal second timestamp
            16409952000000,  # Future timestamp
        ]
        
        for timestamp in edge_timestamps:
            try:
                # Test OHLCV data with edge case timestamps
                data = [[timestamp, 50000, 51000, 49000, 50000, 100]]
                df = data_formatter.format_ohlcv_data(data, "BTC/USD", "1h", validate=False)
                
                if not df.empty:
                    assert isinstance(df.index[0], pd.Timestamp)
                
            except (ValueError, OverflowError, pd.errors.OutOfBoundsDatetime):
                # Expected for invalid timestamps
                pass
    
    def test_empty_and_null_data_handling(self):
        """Test handling of empty and null data."""
        
        empty_scenarios = [
            [],  # Empty list
            [[]],  # List with empty sublist
            None,  # None value
            pd.DataFrame(),  # Empty DataFrame
            [[None, None, None, None, None, None]],  # All None values
        ]
        
        for empty_data in empty_scenarios:
            try:
                if empty_data is not None:
                    df = data_formatter.format_ohlcv_data(empty_data, "BTC/USD", "1h", validate=False)
                    # Should return empty DataFrame or handle gracefully
                    assert isinstance(df, pd.DataFrame)
                
            except (ValueError, TypeError):
                # Expected for some invalid inputs
                pass
    
    def test_configuration_boundary_values(self):
        """Test configuration with boundary values."""
        
        boundary_configs = [
            # Minimum values
            {
                "exchange": {"name": "a", "trading_fee": 0.0},
                "pair": {"base_currency": "A", "quote_currency": "B"},
                "grid_strategy": {"num_grids": 1, "bottom_price": 0.01, "top_price": 0.02}
            },
            # Maximum reasonable values
            {
                "exchange": {"name": "a" * 100, "trading_fee": 1.0},
                "pair": {"base_currency": "A" * 10, "quote_currency": "B" * 10},
                "grid_strategy": {"num_grids": 10000, "bottom_price": 1e6, "top_price": 1e9}
            },
            # Zero values
            {
                "exchange": {"name": "binance", "trading_fee": 0.0},
                "pair": {"base_currency": "BTC", "quote_currency": "USD"},
                "grid_strategy": {"num_grids": 0, "bottom_price": 0, "top_price": 0}
            },
        ]
        
        for config in boundary_configs:
            try:
                # Test configuration validation
                is_valid, errors = data_formatter.validate_trading_data(config.get("grid_strategy", {}))
                
                # Should either validate successfully or provide clear errors
                assert isinstance(is_valid, bool)
                assert isinstance(errors, list)
                
            except (ValueError, TypeError):
                # Expected for invalid configurations
                pass


class TestConcurrencyEdgeCases:
    """Test edge cases in concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_race_condition_simulation(self):
        """Test potential race conditions in concurrent operations."""
        
        # Shared state that could cause race conditions
        shared_counter = {'value': 0}
        results = []
        
        async def concurrent_operation(operation_id):
            """Simulate operation that modifies shared state."""
            # Read current value
            current_value = shared_counter['value']
            
            # Simulate processing delay
            await asyncio.sleep(0.001)
            
            # Modify shared state (potential race condition)
            shared_counter['value'] = current_value + 1
            results.append(operation_id)
            
            return operation_id
        
        # Run many concurrent operations
        tasks = [concurrent_operation(i) for i in range(100)]
        completed_operations = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for race condition effects
        assert len(completed_operations) == 100
        assert len(results) == 100
        
        # The final counter value might be less than 100 due to race conditions
        # This test documents the behavior rather than asserting correctness
        print(f"Final counter value: {shared_counter['value']} (expected: 100)")
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_simulation(self):
        """Test behavior under resource exhaustion."""
        
        # Simulate resource-intensive operations
        async def resource_intensive_operation(size):
            """Operation that consumes significant resources."""
            # Create large data structure
            data = [i for i in range(size)]
            
            # Simulate processing
            await asyncio.sleep(0.01)
            
            return len(data)
        
        # Try to exhaust resources with many large operations
        large_tasks = [resource_intensive_operation(10000) for _ in range(50)]
        
        try:
            results = await asyncio.gather(*large_tasks, return_exceptions=True)
            
            # Count successful operations
            successful = [r for r in results if isinstance(r, int)]
            failed = [r for r in results if isinstance(r, Exception)]
            
            print(f"Successful operations: {len(successful)}")
            print(f"Failed operations: {len(failed)}")
            
            # System should handle resource pressure gracefully
            assert len(successful) + len(failed) == 50
            
        except MemoryError:
            # Expected under extreme resource pressure
            pass
    
    def test_deadlock_prevention(self):
        """Test deadlock prevention in multi-threaded scenarios."""
        import threading
        import time
        
        # Simulate potential deadlock scenario
        lock1 = threading.Lock()
        lock2 = threading.Lock()
        results = []
        
        def thread1_operation():
            """Thread 1 acquires lock1 then lock2."""
            try:
                if lock1.acquire(timeout=1.0):
                    time.sleep(0.1)  # Hold lock1
                    if lock2.acquire(timeout=1.0):
                        results.append("thread1_success")
                        lock2.release()
                    else:
                        results.append("thread1_timeout")
                    lock1.release()
                else:
                    results.append("thread1_failed")
            except Exception as e:
                results.append(f"thread1_error: {e}")
        
        def thread2_operation():
            """Thread 2 acquires lock2 then lock1."""
            try:
                if lock2.acquire(timeout=1.0):
                    time.sleep(0.1)  # Hold lock2
                    if lock1.acquire(timeout=1.0):
                        results.append("thread2_success")
                        lock1.release()
                    else:
                        results.append("thread2_timeout")
                    lock2.release()
                else:
                    results.append("thread2_failed")
            except Exception as e:
                results.append(f"thread2_error: {e}")
        
        # Start threads that could deadlock
        thread1 = threading.Thread(target=thread1_operation)
        thread2 = threading.Thread(target=thread2_operation)
        
        thread1.start()
        thread2.start()
        
        # Wait for completion with timeout
        thread1.join(timeout=5.0)
        thread2.join(timeout=5.0)
        
        # Both threads should complete (no deadlock)
        assert not thread1.is_alive(), "Thread 1 should have completed"
        assert not thread2.is_alive(), "Thread 2 should have completed"
        assert len(results) == 2, f"Expected 2 results, got {len(results)}: {results}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
