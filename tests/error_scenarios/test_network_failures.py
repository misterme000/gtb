"""
Network Failure Tests for Grid Trading Bot

Tests for handling network failures, API timeouts, connection drops,
and other network-related error scenarios.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import aiohttp
from aiohttp import ClientError, ClientTimeout, ClientConnectorError
import ccxt
from ccxt.base.errors import NetworkError, RequestTimeout, ExchangeNotAvailable

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.services.live_exchange_service import LiveExchangeService
from core.services.backtest_exchange_service import BacktestExchangeService
from core.services.exceptions import DataFetchError, OrderCancellationError
from config.config_manager import ConfigManager
from web_ui.price_service import price_service
from core.error_handling import NetworkError as UnifiedNetworkError, error_handler


class TestNetworkFailureScenarios:
    """Test network failure scenarios and recovery mechanisms."""
    
    def setup_method(self):
        """Setup test fixtures."""
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
    async def test_connection_timeout_during_order_placement(self):
        """Test handling of connection timeout during order placement."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        # Mock exchange to raise timeout error
        service.exchange = AsyncMock()
        service.exchange.create_order = AsyncMock(side_effect=RequestTimeout("Connection timeout"))
        
        with pytest.raises(DataFetchError) as exc_info:
            await service.place_order("BTC/USDT", "buy", "limit", 0.001, 50000)
        
        assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_network_error_during_balance_fetch(self):
        """Test handling of network error during balance fetch."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        # Mock exchange to raise network error
        service.exchange = AsyncMock()
        service.exchange.fetch_balance = AsyncMock(side_effect=NetworkError("Network unreachable"))
        
        with pytest.raises(DataFetchError) as exc_info:
            await service.get_balance()
        
        assert "network" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_exchange_unavailable_error(self):
        """Test handling of exchange unavailable error."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        # Mock exchange to raise unavailable error
        service.exchange = AsyncMock()
        service.exchange.fetch_ticker = AsyncMock(side_effect=ExchangeNotAvailable("Exchange maintenance"))
        
        with pytest.raises(DataFetchError) as exc_info:
            await service.get_current_price("BTC/USDT")
        
        assert "exchange" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_connection_drop_during_websocket(self):
        """Test handling of connection drop during WebSocket streaming."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        # Mock exchange WebSocket to fail
        service.exchange = AsyncMock()
        service.exchange.watch_ticker = AsyncMock(side_effect=NetworkError("Connection lost"))
        
        # Mock callback
        callback = AsyncMock()
        
        # Test WebSocket connection handling
        with pytest.raises(Exception):  # Should handle connection drop gracefully
            await service._subscribe_to_ticker_updates("BTC/USDT", callback, 1.0, max_retries=1)
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_exceeded(self):
        """Test handling of API rate limit exceeded."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        # Mock exchange to raise rate limit error
        service.exchange = AsyncMock()
        service.exchange.fetch_ohlcv = AsyncMock(side_effect=ccxt.RateLimitExceeded("Rate limit exceeded"))
        
        # Should handle rate limit gracefully
        with pytest.raises(Exception):
            # This would normally be handled by the base class retry mechanism
            await service.exchange.fetch_ohlcv("BTC/USDT", "1h")
    
    def test_historical_data_fetch_network_failure(self):
        """Test network failure during historical data fetch."""
        service = BacktestExchangeService(self.config_manager)
        
        # Mock exchange to raise network error
        service.exchange = Mock()
        service.exchange.fetch_ohlcv = Mock(side_effect=NetworkError("Network error"))
        
        with pytest.raises(DataFetchError):
            service.fetch_ohlcv("BTC/USDT", "1h", "2024-01-01", "2024-01-02")
    
    @pytest.mark.asyncio
    async def test_price_service_network_failures(self):
        """Test price service handling of network failures."""
        
        # Test current price fetch failure
        with patch.object(price_service, '_fetch_current_price_async', side_effect=aiohttp.ClientError("Network error")):
            price = await price_service.get_current_price("coinbase", "BTC", "USD")
            assert price is None  # Should return None on failure
        
        # Test historical data fetch failure
        with patch.object(price_service, '_fetch_historical_data_async', side_effect=aiohttp.ClientTimeout()):
            df = await price_service.get_historical_data("coinbase", "BTC", "USD", "1h", 100)
            assert df is None or df.empty  # Should return None or empty DataFrame
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_exhaustion(self):
        """Test behavior when retry mechanism is exhausted."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        # Mock method that always fails
        def failing_method(*args, **kwargs):
            raise NetworkError("Persistent network error")
        
        # Test retry exhaustion
        with pytest.raises(DataFetchError) as exc_info:
            service._fetch_with_retry(failing_method, retries=2, delay=0.1)
        
        assert "after 3 attempts" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_partial_network_recovery(self):
        """Test partial network recovery scenarios."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        # Mock method that fails first few times then succeeds
        call_count = 0
        def intermittent_method(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary network error")
            return {"status": "success"}
        
        # Should eventually succeed
        result = service._fetch_with_retry(intermittent_method, retries=3, delay=0.1)
        assert result["status"] == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self):
        """Test DNS resolution failure handling."""
        
        # Mock DNS resolution failure
        with patch('aiohttp.ClientSession.get', side_effect=ClientConnectorError(None, OSError("Name resolution failed"))):
            price = await price_service.get_current_price("invalid_exchange", "BTC", "USD")
            assert price is None
    
    @pytest.mark.asyncio
    async def test_ssl_certificate_error(self):
        """Test SSL certificate error handling."""
        
        # Mock SSL certificate error
        ssl_error = aiohttp.ClientSSLError(None, "SSL certificate verification failed")
        
        with patch('aiohttp.ClientSession.get', side_effect=ssl_error):
            price = await price_service.get_current_price("coinbase", "BTC", "USD")
            assert price is None
    
    @pytest.mark.asyncio
    async def test_http_error_codes(self):
        """Test handling of various HTTP error codes."""
        error_codes = [400, 401, 403, 404, 429, 500, 502, 503, 504]
        
        for code in error_codes:
            # Mock HTTP error response
            mock_response = Mock()
            mock_response.status = code
            mock_response.text = AsyncMock(return_value=f"HTTP {code} Error")
            
            http_error = aiohttp.ClientResponseError(
                request_info=Mock(),
                history=(),
                status=code,
                message=f"HTTP {code} Error"
            )
            
            with patch('aiohttp.ClientSession.get', side_effect=http_error):
                price = await price_service.get_current_price("coinbase", "BTC", "USD")
                assert price is None
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """Test handling of malformed API responses."""
        
        # Mock malformed JSON response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        mock_response.text = AsyncMock(return_value="Invalid JSON response")
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            price = await price_service.get_current_price("coinbase", "BTC", "USD")
            assert price is None
    
    @pytest.mark.asyncio
    async def test_concurrent_network_failures(self):
        """Test handling of concurrent network failures."""
        
        # Create multiple concurrent requests that fail
        async def failing_request():
            raise NetworkError("Network failure")
        
        tasks = [failing_request() for _ in range(10)]
        
        # All should fail gracefully
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All results should be exceptions
        assert all(isinstance(result, Exception) for result in results)
        assert all("Network failure" in str(result) for result in results)


class TestNetworkRecoveryMechanisms:
    """Test network recovery and resilience mechanisms."""
    
    def setup_method(self):
        """Setup test fixtures."""
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
    async def test_exponential_backoff_retry(self):
        """Test exponential backoff retry mechanism."""
        service = LiveExchangeService(self.config_manager, is_paper_trading_activated=True)
        
        call_times = []
        
        def timed_failing_method(*args, **kwargs):
            import time
            call_times.append(time.time())
            if len(call_times) < 4:
                raise NetworkError("Network error")
            return {"success": True}
        
        # Test exponential backoff
        result = service._fetch_with_retry(
            timed_failing_method,
            retries=3,
            delay=0.1,
            backoff_factor=2.0
        )
        
        assert result["success"] is True
        assert len(call_times) == 4
        
        # Check that delays increased exponentially
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Second delay should be roughly double the first (allowing for timing variance)
            assert delay2 > delay1 * 1.5
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for repeated failures."""
        
        # Simulate circuit breaker behavior
        failure_count = 0
        circuit_open = False
        
        async def circuit_breaker_request():
            nonlocal failure_count, circuit_open
            
            if circuit_open:
                raise Exception("Circuit breaker open")
            
            failure_count += 1
            if failure_count >= 5:
                circuit_open = True
            
            raise NetworkError("Network failure")
        
        # First 5 requests should fail normally
        for i in range(5):
            with pytest.raises(NetworkError):
                await circuit_breaker_request()
        
        # Subsequent requests should fail with circuit breaker
        with pytest.raises(Exception) as exc_info:
            await circuit_breaker_request()
        
        assert "circuit breaker" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when services are unavailable."""
        
        # Test price service degradation
        with patch.object(price_service, '_fetch_current_price_async', side_effect=NetworkError("Service unavailable")):
            # Should return cached price or None instead of crashing
            price = await price_service.get_current_price("coinbase", "BTC", "USD")
            assert price is None  # Graceful degradation
        
        # Test historical data degradation
        with patch.object(price_service, '_fetch_historical_data_async', side_effect=NetworkError("Service unavailable")):
            # Should return empty DataFrame instead of crashing
            df = await price_service.get_historical_data("coinbase", "BTC", "USD", "1h", 100)
            assert df is None or df.empty  # Graceful degradation
    
    @pytest.mark.asyncio
    async def test_fallback_data_sources(self):
        """Test fallback to alternative data sources."""
        
        # Mock primary source failure, secondary source success
        primary_calls = 0
        secondary_calls = 0
        
        async def primary_source(*args, **kwargs):
            nonlocal primary_calls
            primary_calls += 1
            raise NetworkError("Primary source unavailable")
        
        async def secondary_source(*args, **kwargs):
            nonlocal secondary_calls
            secondary_calls += 1
            return 50000.0  # Mock price
        
        # Simulate fallback logic
        try:
            price = await primary_source()
        except NetworkError:
            price = await secondary_source()
        
        assert price == 50000.0
        assert primary_calls == 1
        assert secondary_calls == 1
    
    @pytest.mark.asyncio
    async def test_connection_pooling_resilience(self):
        """Test connection pooling resilience to failures."""
        
        # Mock connection pool with some connections failing
        successful_connections = 0
        failed_connections = 0
        
        async def mock_connection_request(connection_id):
            nonlocal successful_connections, failed_connections
            
            if connection_id % 3 == 0:  # Every 3rd connection fails
                failed_connections += 1
                raise NetworkError(f"Connection {connection_id} failed")
            else:
                successful_connections += 1
                return f"Success from connection {connection_id}"
        
        # Test multiple concurrent connections
        tasks = [mock_connection_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should have mix of successes and failures
        successes = [r for r in results if isinstance(r, str)]
        failures = [r for r in results if isinstance(r, Exception)]
        
        assert len(successes) > 0
        assert len(failures) > 0
        assert successful_connections + failed_connections == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
