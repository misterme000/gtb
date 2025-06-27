#!/usr/bin/env python3
"""
Test Grid Trading Bot UI Functionality

This script tests the core functionality of the web UI including:
- Price data fetching
- Historical data retrieval
- Grid calculations
- Chart generation
"""

import sys
import asyncio
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from web_ui.price_service import price_service
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_price_service():
    """Test the price service functionality."""
    print("Testing Price Service Functionality")
    print("=" * 50)

    # Test exchanges and pairs
    test_cases = [
        ("coinbase", "BTC", "USD"),
        ("coinbase", "ETH", "USD"),
        ("kraken", "BTC", "USDT"),
    ]

    for exchange, base, quote in test_cases:
        print(f"\nTesting {exchange} - {base}/{quote}")
        print("-" * 30)

        # Test current price
        try:
            price = price_service.get_current_price(exchange, base, quote)
            if price:
                print(f"SUCCESS Current Price: ${price:,.2f}")
            else:
                print(f"FAILED to get current price")
        except Exception as e:
            print(f"ERROR Current price: {e}")

        # Test historical data
        try:
            df = price_service.get_historical_data(exchange, base, quote, "1h", 24)
            if df is not None and not df.empty:
                print(f"SUCCESS Historical Data: {len(df)} records")
                print(f"   Date range: {df.index[0]} to {df.index[-1]}")
                print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            else:
                print(f"FAILED to get historical data")
        except Exception as e:
            print(f"ERROR Historical data: {e}")

        # Test market summary
        try:
            summary = price_service.get_market_summary(exchange, base, quote)
            if summary:
                print(f"SUCCESS Market Summary:")
                print(f"   Volume: {summary.get('volume', 0):,.2f}")
                print(f"   24h Change: {summary.get('change_24h_percent', 0):.2f}%")
            else:
                print(f"FAILED to get market summary")
        except Exception as e:
            print(f"ERROR Market summary: {e}")

def test_sync_wrappers():
    """Test synchronous wrapper functions."""
    print("\nTesting Synchronous Wrappers")
    print("=" * 50)
    
    # Test sync current price
    try:
        price = price_service.get_current_price_sync("coinbase", "BTC", "USD")
        if price:
            print(f"SUCCESS Sync Current Price: ${price:,.2f}")
        else:
            print(f"FAILED Sync current price")
    except Exception as e:
        print(f"ERROR Sync current price: {e}")

    # Test sync historical data
    try:
        df = price_service.get_historical_data_sync("coinbase", "BTC", "USD", "1h", 24)
        if df is not None and not df.empty:
            print(f"SUCCESS Sync Historical Data: {len(df)} records")
        else:
            print(f"FAILED Sync historical data")
    except Exception as e:
        print(f"ERROR Sync historical data: {e}")

def test_grid_calculations():
    """Test grid calculation functionality."""
    print("\nTesting Grid Calculations")
    print("=" * 50)
    
    # Test price range suggestions
    test_prices = [50000, 95000, 150000]
    
    for price in test_prices:
        bottom, top = price_service.get_price_range_suggestion(price)
        print(f"Price ${price:,} -> Range: ${bottom:,} - ${top:,}")
    
    # Test grid metrics
    test_configs = [
        (90000, 100000, 10, "arithmetic"),
        (90000, 100000, 10, "geometric"),
        (50000, 60000, 8, "arithmetic"),
    ]
    
    for bottom, top, num_grids, spacing in test_configs:
        metrics = price_service.calculate_grid_metrics(bottom, top, num_grids, spacing)
        if metrics:
            print(f"\nGrid Config: ${bottom:,} - ${top:,}, {num_grids} grids, {spacing}")
            print(f"   Range: {metrics['range_percentage']:.1f}%")
            print(f"   Avg Spacing: {metrics['avg_spacing']}")
            print(f"   Grid Levels: {len(metrics['grid_levels'])} levels")
        else:
            print(f"FAILED to calculate grid metrics")

def test_ui_integration():
    """Test UI integration scenarios."""
    print("\nTesting UI Integration Scenarios")
    print("=" * 50)
    
    # Simulate UI configuration
    config_data = {
        "exchange": {"name": "coinbase"},
        "pair": {"base_currency": "BTC", "quote_currency": "USD"},
        "trading_settings": {"timeframe": "1h"},
        "grid_strategy": {
            "range": {"bottom": 90000, "top": 100000},
            "num_grids": 10,
            "spacing": "arithmetic"
        }
    }
    
    print("SUCCESS Sample configuration created")
    print(f"   Exchange: {config_data['exchange']['name']}")
    print(f"   Pair: {config_data['pair']['base_currency']}/{config_data['pair']['quote_currency']}")
    print(f"   Grid: {config_data['grid_strategy']['num_grids']} levels")
    
    # Test data fetching for this config
    try:
        df = price_service.get_historical_data_sync(
            config_data["exchange"]["name"],
            config_data["pair"]["base_currency"],
            config_data["pair"]["quote_currency"],
            config_data["trading_settings"]["timeframe"],
            100
        )
        
        if df is not None and not df.empty:
            print(f"SUCCESS Data fetch: {len(df)} records")

            # Check if price is within grid range
            current_price = df['close'].iloc[-1]
            bottom = config_data["grid_strategy"]["range"]["bottom"]
            top = config_data["grid_strategy"]["range"]["top"]

            if bottom <= current_price <= top:
                print(f"SUCCESS Current price ${current_price:,.2f} is within grid range")
            else:
                print(f"WARNING Current price ${current_price:,.2f} is outside grid range ${bottom:,} - ${top:,}")

        else:
            print(f"FAILED Data fetch for UI config")

    except Exception as e:
        print(f"ERROR UI integration test: {e}")

def main():
    """Run all tests."""
    print("Grid Trading Bot UI Functionality Tests")
    print("=" * 60)

    try:
        # Run tests
        test_price_service()
        test_sync_wrappers()
        test_grid_calculations()
        test_ui_integration()
        
        print("\n" + "=" * 60)
        print("SUCCESS All tests completed!")
        print("\nNOTE If you see errors above:")
        print("   * Check internet connection")
        print("   * Verify exchange APIs are accessible")
        print("   * Some exchanges may have geographic restrictions")
        print("   * Rate limiting may cause temporary failures")

    except Exception as e:
        print(f"\nERROR Test suite: {e}")
    
    finally:
        # Clean up
        price_service.close_exchanges()

if __name__ == "__main__":
    main()
