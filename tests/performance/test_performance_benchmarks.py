"""
Performance Benchmark Tests for Grid Trading Bot

Comprehensive performance tests including:
- Data processing benchmarks
- Memory usage tests
- Concurrent operation tests
- Load testing scenarios
"""

import pytest
import asyncio
import time
import sys
import psutil
import gc
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.services.live_exchange_service import LiveExchangeService
from core.services.backtest_exchange_service import BacktestExchangeService
from core.services.data_formatting_service import data_formatter, data_validator
from config.config_manager import ConfigManager
from web_ui.price_service import price_service
from core.grid_strategy.grid_calculator import GridCalculator


class PerformanceBenchmark:
    """Base class for performance benchmarks."""
    
    def __init__(self):
        """Initialize benchmark utilities."""
        self.process = psutil.Process()
        self.start_memory = None
        self.start_time = None
    
    def start_benchmark(self):
        """Start performance measurement."""
        gc.collect()  # Clean up before measurement
        self.start_memory = self.process.memory_info().rss
        self.start_time = time.time()
    
    def end_benchmark(self) -> Dict[str, Any]:
        """End performance measurement and return results."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        
        return {
            'duration': end_time - self.start_time,
            'memory_start': self.start_memory,
            'memory_end': end_memory,
            'memory_delta': end_memory - self.start_memory,
            'memory_peak': self.process.memory_info().peak_wss if hasattr(self.process.memory_info(), 'peak_wss') else None
        }


class TestDataProcessingPerformance:
    """Test data processing performance benchmarks."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.benchmark = PerformanceBenchmark()
        
        # Generate large test datasets
        self.small_dataset = self._generate_ohlcv_data(1000)    # 1K records
        self.medium_dataset = self._generate_ohlcv_data(10000)  # 10K records
        self.large_dataset = self._generate_ohlcv_data(100000)  # 100K records
    
    def _generate_ohlcv_data(self, size: int) -> List[List]:
        """Generate synthetic OHLCV data for testing."""
        base_price = 50000
        data = []
        
        for i in range(size):
            timestamp = int((datetime.now() - timedelta(hours=size-i)).timestamp() * 1000)
            price_variation = np.random.normal(0, 1000)
            
            open_price = base_price + price_variation
            high_price = open_price + abs(np.random.normal(0, 500))
            low_price = open_price - abs(np.random.normal(0, 500))
            close_price = open_price + np.random.normal(0, 200)
            volume = abs(np.random.normal(100, 20))
            
            data.append([timestamp, open_price, high_price, low_price, close_price, volume])
        
        return data
    
    def test_small_dataset_formatting_performance(self):
        """Test performance with small dataset (1K records)."""
        self.benchmark.start_benchmark()
        
        # Format data multiple times
        for _ in range(100):
            df = data_formatter.format_ohlcv_data(
                self.small_dataset, 
                "BTC/USD", 
                "1h", 
                validate=True
            )
            assert len(df) == 1000
        
        results = self.benchmark.end_benchmark()
        
        # Performance assertions
        assert results['duration'] < 10.0  # Should complete within 10 seconds
        assert results['memory_delta'] < 100 * 1024 * 1024  # Less than 100MB memory increase
    
    def test_medium_dataset_formatting_performance(self):
        """Test performance with medium dataset (10K records)."""
        self.benchmark.start_benchmark()
        
        # Format data multiple times
        for _ in range(10):
            df = data_formatter.format_ohlcv_data(
                self.medium_dataset, 
                "BTC/USD", 
                "1h", 
                validate=True
            )
            assert len(df) == 10000
        
        results = self.benchmark.end_benchmark()
        
        # Performance assertions
        assert results['duration'] < 30.0  # Should complete within 30 seconds
        assert results['memory_delta'] < 500 * 1024 * 1024  # Less than 500MB memory increase
    
    def test_large_dataset_formatting_performance(self):
        """Test performance with large dataset (100K records)."""
        self.benchmark.start_benchmark()
        
        # Format data once (large dataset)
        df = data_formatter.format_ohlcv_data(
            self.large_dataset, 
            "BTC/USD", 
            "1h", 
            validate=True
        )
        assert len(df) == 100000
        
        results = self.benchmark.end_benchmark()
        
        # Performance assertions
        assert results['duration'] < 60.0  # Should complete within 60 seconds
        assert results['memory_delta'] < 1024 * 1024 * 1024  # Less than 1GB memory increase
    
    def test_data_validation_performance(self):
        """Test data validation performance."""
        # Generate test orders
        test_orders = []
        for i in range(1000):
            order = {
                'id': f'order_{i}',
                'symbol': 'BTC/USD',
                'side': 'buy' if i % 2 == 0 else 'sell',
                'type': 'limit',
                'amount': 0.001 + (i * 0.0001),
                'price': 50000 + (i * 10),
                'status': 'open',
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            test_orders.append(order)
        
        self.benchmark.start_benchmark()
        
        # Validate all orders
        for order in test_orders:
            formatted_order = data_validator.validate_and_format_order(order, "binance")
            assert formatted_order['id'] == order['id']
        
        results = self.benchmark.end_benchmark()
        
        # Performance assertions
        assert results['duration'] < 5.0  # Should complete within 5 seconds
        assert results['memory_delta'] < 50 * 1024 * 1024  # Less than 50MB memory increase
    
    def test_grid_calculation_performance(self):
        """Test grid calculation performance."""
        calculator = GridCalculator()
        
        self.benchmark.start_benchmark()
        
        # Perform many grid calculations
        for i in range(1000):
            num_grids = 10 + (i % 40)  # 10-50 grids
            bottom_price = 45000 + (i * 10)
            top_price = 55000 + (i * 10)
            
            # Test both arithmetic and geometric spacing
            arithmetic_levels = calculator.calculate_grid_levels(
                num_grids, bottom_price, top_price, "arithmetic"
            )
            geometric_levels = calculator.calculate_grid_levels(
                num_grids, bottom_price, top_price, "geometric"
            )
            
            assert len(arithmetic_levels) == num_grids
            assert len(geometric_levels) == num_grids
        
        results = self.benchmark.end_benchmark()
        
        # Performance assertions
        assert results['duration'] < 2.0  # Should complete within 2 seconds
        assert results['memory_delta'] < 20 * 1024 * 1024  # Less than 20MB memory increase


class TestConcurrentOperationPerformance:
    """Test concurrent operation performance."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.benchmark = PerformanceBenchmark()
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get_exchange_name.return_value = "binance"
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'EXCHANGE_API_KEY': 'test_api_key',
            'EXCHANGE_SECRET_KEY': 'test_secret_key'
        })
        self.env_patcher.start()
    
    def teardown_method(self):
        """Cleanup after tests."""
        self.env_patcher.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_price_fetching(self):
        """Test concurrent price fetching performance."""
        
        # Mock price service responses
        async def mock_price_fetch(exchange, base, quote):
            await asyncio.sleep(0.1)  # Simulate network delay
            return 50000 + np.random.normal(0, 1000)
        
        with patch.object(price_service, 'get_current_price', side_effect=mock_price_fetch):
            self.benchmark.start_benchmark()
            
            # Create concurrent price fetch tasks
            tasks = []
            pairs = [("BTC", "USD"), ("ETH", "USD"), ("ADA", "USD"), ("DOT", "USD")]
            exchanges = ["coinbase", "kraken", "binance"]
            
            for exchange in exchanges:
                for base, quote in pairs:
                    task = price_service.get_current_price(exchange, base, quote)
                    tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify results
            successful_results = [r for r in results if isinstance(r, (int, float))]
            assert len(successful_results) >= len(tasks) * 0.8  # At least 80% success
            
            benchmark_results = self.benchmark.end_benchmark()
            
            # Performance assertions
            assert benchmark_results['duration'] < 5.0  # Should complete within 5 seconds
            assert len(tasks) == 12  # 3 exchanges * 4 pairs
    
    @pytest.mark.asyncio
    async def test_concurrent_order_processing(self):
        """Test concurrent order processing performance."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        # Mock exchange responses
        async def mock_create_order(*args, **kwargs):
            await asyncio.sleep(0.05)  # Simulate processing time
            return {
                'id': f'order_{np.random.randint(1000, 9999)}',
                'symbol': args[0],
                'side': args[2],
                'amount': args[3],
                'price': args[4],
                'status': 'open',
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
        
        service.exchange = AsyncMock()
        service.exchange.create_order = mock_create_order
        
        self.benchmark.start_benchmark()
        
        # Create concurrent order tasks
        order_tasks = []
        for i in range(50):
            task = service.place_order(
                "BTC/USDT",
                "buy" if i % 2 == 0 else "sell",
                "limit",
                0.001,
                50000 + (i * 10)
            )
            order_tasks.append(task)
        
        # Execute orders concurrently
        results = await asyncio.gather(*order_tasks, return_exceptions=True)
        
        # Verify results
        successful_orders = [r for r in results if isinstance(r, dict) and 'id' in r]
        assert len(successful_orders) >= 40  # At least 80% success
        
        benchmark_results = self.benchmark.end_benchmark()
        
        # Performance assertions
        assert benchmark_results['duration'] < 10.0  # Should complete within 10 seconds
    
    def test_thread_pool_performance(self):
        """Test thread pool performance for CPU-intensive tasks."""
        
        def cpu_intensive_task(data_size):
            """Simulate CPU-intensive data processing."""
            data = np.random.randn(data_size, 5)  # 5 columns like OHLCV
            df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'])
            
            # Perform calculations
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['volatility'] = df['close'].rolling(window=20).std()
            df['returns'] = df['close'].pct_change()
            
            return len(df)
        
        self.benchmark.start_benchmark()
        
        # Execute tasks in thread pool
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(20):
                future = executor.submit(cpu_intensive_task, 1000)
                futures.append(future)
            
            # Collect results
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        benchmark_results = self.benchmark.end_benchmark()
        
        # Verify all tasks completed
        assert len(results) == 20
        assert all(result == 1000 for result in results)
        
        # Performance assertions
        assert benchmark_results['duration'] < 30.0  # Should complete within 30 seconds


class TestMemoryUsagePatterns:
    """Test memory usage patterns and potential leaks."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.benchmark = PerformanceBenchmark()
    
    def test_memory_usage_during_large_data_processing(self):
        """Test memory usage during large data processing."""
        initial_memory = self.benchmark.process.memory_info().rss
        
        # Process increasingly large datasets
        dataset_sizes = [1000, 5000, 10000, 20000, 50000]
        memory_measurements = []
        
        for size in dataset_sizes:
            # Generate data
            data = self._generate_test_data(size)
            
            # Process data
            df = data_formatter.format_ohlcv_data(data, "BTC/USD", "1h", validate=True)
            
            # Measure memory
            current_memory = self.benchmark.process.memory_info().rss
            memory_measurements.append(current_memory - initial_memory)
            
            # Clean up
            del df, data
            gc.collect()
        
        # Memory should not grow excessively
        max_memory_increase = max(memory_measurements)
        assert max_memory_increase < 500 * 1024 * 1024  # Less than 500MB
        
        # Memory should be released after processing
        final_memory = self.benchmark.process.memory_info().rss
        memory_retained = final_memory - initial_memory
        assert memory_retained < 100 * 1024 * 1024  # Less than 100MB retained
    
    def test_memory_leak_detection(self):
        """Test for potential memory leaks in repeated operations."""
        initial_memory = self.benchmark.process.memory_info().rss
        
        # Perform repeated operations
        for iteration in range(100):
            # Create and process data
            data = self._generate_test_data(1000)
            df = data_formatter.format_ohlcv_data(data, "BTC/USD", "1h", validate=True)
            
            # Simulate order processing
            order = {
                'id': f'order_{iteration}',
                'symbol': 'BTC/USD',
                'side': 'buy',
                'type': 'limit',
                'amount': 0.001,
                'price': 50000,
                'status': 'open',
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            formatted_order = data_formatter.format_order_data(order, "binance", validate=True)
            
            # Clean up explicitly
            del data, df, order, formatted_order
            
            # Force garbage collection every 10 iterations
            if iteration % 10 == 0:
                gc.collect()
        
        # Final cleanup
        gc.collect()
        final_memory = self.benchmark.process.memory_info().rss
        
        # Memory increase should be minimal
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50 * 1024 * 1024  # Less than 50MB increase
    
    def test_concurrent_memory_usage(self):
        """Test memory usage under concurrent operations."""
        initial_memory = self.benchmark.process.memory_info().rss
        
        def memory_intensive_task(task_id):
            """Task that uses significant memory."""
            data = self._generate_test_data(5000)
            df = data_formatter.format_ohlcv_data(data, f"PAIR_{task_id}", "1h", validate=True)
            
            # Simulate processing
            time.sleep(0.1)
            
            return len(df)
        
        # Run concurrent memory-intensive tasks
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for i in range(20):
                future = executor.submit(memory_intensive_task, i)
                futures.append(future)
            
            # Monitor peak memory during execution
            peak_memory = initial_memory
            for future in as_completed(futures):
                current_memory = self.benchmark.process.memory_info().rss
                peak_memory = max(peak_memory, current_memory)
                result = future.result()
                assert result == 5000
        
        # Clean up and measure final memory
        gc.collect()
        final_memory = self.benchmark.process.memory_info().rss
        
        # Peak memory should be reasonable
        peak_increase = peak_memory - initial_memory
        assert peak_increase < 1024 * 1024 * 1024  # Less than 1GB peak
        
        # Memory should be released after completion
        final_increase = final_memory - initial_memory
        assert final_increase < 100 * 1024 * 1024  # Less than 100MB retained
    
    def _generate_test_data(self, size: int) -> List[List]:
        """Generate test OHLCV data."""
        data = []
        base_price = 50000
        
        for i in range(size):
            timestamp = int((datetime.now() - timedelta(hours=size-i)).timestamp() * 1000)
            price = base_price + np.random.normal(0, 1000)
            
            data.append([
                timestamp,
                price,  # open
                price + abs(np.random.normal(0, 500)),  # high
                price - abs(np.random.normal(0, 500)),  # low
                price + np.random.normal(0, 200),  # close
                abs(np.random.normal(100, 20))  # volume
            ])
        
        return data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
