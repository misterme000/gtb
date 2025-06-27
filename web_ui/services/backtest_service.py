"""
Backtest Service for Grid Trading Bot Web UI

Provides backtesting functionality and performance preview.
"""

import logging
import asyncio
import tempfile
import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import pandas as pd
import numpy as np

from web_ui.price_service import price_service
from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from core.bot_management.grid_trading_bot import GridTradingBot
from core.bot_management.event_bus import EventBus
from core.bot_management.notification.notification_handler import NotificationHandler
from config.trading_mode import TradingMode

logger = logging.getLogger(__name__)


class BacktestService:
    """Service for running backtests and generating performance previews."""
    
    def __init__(self):
        """Initialize the backtest service."""
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def quick_performance_estimate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a quick performance estimate without running full backtest.
        
        Args:
            config: Trading configuration
            
        Returns:
            Dictionary with estimated performance metrics
        """
        try:
            # Get basic parameters
            grid_config = config.get("grid_strategy", {})
            bottom_price = grid_config.get("range", {}).get("bottom", 90000)
            top_price = grid_config.get("range", {}).get("top", 100000)
            num_grids = grid_config.get("num_grids", 10)
            initial_balance = config.get("trading_settings", {}).get("initial_balance", 10000)
            trading_fee = config.get("exchange", {}).get("trading_fee", 0.005)
            
            # Calculate basic metrics
            price_range = top_price - bottom_price
            range_percentage = (price_range / bottom_price) * 100
            grid_spacing = price_range / (num_grids - 1)
            
            # Estimate profit per grid level
            avg_price = (top_price + bottom_price) / 2
            profit_per_grid = grid_spacing - (avg_price * trading_fee * 2)  # Buy and sell fees
            
            # Estimate number of trades (rough approximation)
            estimated_trades = min(num_grids * 4, 200)  # Cap at 200 trades
            
            # Estimate total profit
            estimated_profit = profit_per_grid * (estimated_trades / 2)  # Half are profitable
            estimated_roi = (estimated_profit / initial_balance) * 100
            
            # Estimate max drawdown (rough approximation)
            max_drawdown = min(range_percentage / 2, 25)  # Cap at 25%
            
            # Estimate Sharpe ratio (simplified)
            volatility = range_percentage / 4  # Rough volatility estimate
            sharpe_ratio = max(0.5, estimated_roi / max(volatility, 1))
            
            return {
                "estimated_roi": round(estimated_roi, 1),
                "estimated_trades": int(estimated_trades),
                "estimated_profit": round(estimated_profit, 2),
                "max_drawdown": round(max_drawdown, 1),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "profit_per_grid": round(profit_per_grid, 2),
                "grid_spacing": round(grid_spacing, 2),
                "range_percentage": round(range_percentage, 1),
                "avg_price": round(avg_price, 2),
                "total_fees_estimate": round(avg_price * trading_fee * estimated_trades, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance estimate: {e}")
            return {
                "estimated_roi": 0,
                "estimated_trades": 0,
                "estimated_profit": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "error": str(e)
            }
    
    def get_market_analysis(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get market analysis for the configured trading pair.
        
        Args:
            config: Trading configuration
            
        Returns:
            Dictionary with market analysis data
        """
        try:
            exchange_name = config.get("exchange", {}).get("name", "coinbase")
            base_currency = config.get("pair", {}).get("base_currency", "BTC")
            quote_currency = config.get("pair", {}).get("quote_currency", "USDT")
            timeframe = config.get("trading_settings", {}).get("timeframe", "1h")
            
            # Get current price
            current_price = price_service.get_current_price_sync(exchange_name, base_currency, quote_currency)
            
            # Get historical data for analysis
            df = price_service.get_historical_data_sync(exchange_name, base_currency, quote_currency, timeframe, 168)
            
            if df is None or df.empty:
                return {"error": "Unable to fetch market data"}
            
            # Calculate market metrics
            price_change_24h = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24]) * 100 if len(df) >= 24 else 0
            volatility = df['close'].pct_change().std() * 100
            avg_volume = df['volume'].mean()
            
            # Support and resistance levels (simplified)
            recent_high = df['high'].tail(48).max() if len(df) >= 48 else df['high'].max()
            recent_low = df['low'].tail(48).min() if len(df) >= 48 else df['low'].min()
            
            # Grid range analysis
            grid_config = config.get("grid_strategy", {})
            bottom_price = grid_config.get("range", {}).get("bottom", 90000)
            top_price = grid_config.get("range", {}).get("top", 100000)
            
            # Check if current price is within grid range
            price_in_range = bottom_price <= current_price <= top_price if current_price else False
            
            # Calculate how much of recent price action is covered by grid
            coverage = 0
            if recent_high > recent_low:
                overlap_top = min(top_price, recent_high)
                overlap_bottom = max(bottom_price, recent_low)
                if overlap_top > overlap_bottom:
                    coverage = ((overlap_top - overlap_bottom) / (recent_high - recent_low)) * 100
            
            return {
                "current_price": current_price,
                "price_change_24h": round(price_change_24h, 2),
                "volatility": round(volatility, 2),
                "avg_volume": round(avg_volume, 2),
                "recent_high": round(recent_high, 2),
                "recent_low": round(recent_low, 2),
                "price_in_range": price_in_range,
                "grid_coverage": round(coverage, 1),
                "data_points": len(df),
                "analysis_period": f"{len(df)} {timeframe} candles"
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return {"error": str(e)}
    
    async def run_quick_backtest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a quick backtest with limited data for preview.
        
        Args:
            config: Trading configuration
            
        Returns:
            Dictionary with backtest results
        """
        try:
            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(config, f, indent=2)
                config_path = f.name
            
            try:
                # Initialize components
                config_manager = ConfigManager(config_path, ConfigValidator())
                event_bus = EventBus()
                notification_handler = NotificationHandler(event_bus, [], TradingMode.BACKTEST)
                
                # Create bot with limited data
                bot = GridTradingBot(
                    config_path=config_path,
                    config_manager=config_manager,
                    notification_handler=notification_handler,
                    event_bus=event_bus,
                    save_performance_results_path=None,
                    no_plot=True
                )
                
                # Run backtest
                await bot.run()
                
                # Get results
                strategy = bot.strategy
                performance_report, formatted_orders = strategy.generate_performance_report()
                
                # Clean up
                await event_bus.shutdown()
                
                return {
                    "success": True,
                    "performance_report": performance_report,
                    "orders": formatted_orders[:10],  # Limit to first 10 orders
                    "data_points": len(strategy.data) if hasattr(strategy, 'data') else 0
                }
                
            finally:
                # Clean up temp file
                import os
                os.unlink(config_path)
                
        except Exception as e:
            logger.error(f"Error running quick backtest: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_backtest_preview(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive backtest preview combining estimates and market analysis.
        
        Args:
            config: Trading configuration
            
        Returns:
            Dictionary with complete preview data
        """
        try:
            # Get performance estimates
            performance_estimate = self.quick_performance_estimate(config)
            
            # Get market analysis
            market_analysis = self.get_market_analysis(config)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(config, performance_estimate, market_analysis)
            
            return {
                "performance_estimate": performance_estimate,
                "market_analysis": market_analysis,
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating backtest preview: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, config: Dict[str, Any], performance: Dict[str, Any], market: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on configuration and market analysis."""
        recommendations = []
        
        try:
            # Check grid range vs market
            if not market.get("price_in_range", True):
                recommendations.append("⚠️ Current price is outside your grid range. Consider adjusting the range.")
            
            # Check grid coverage
            coverage = market.get("grid_coverage", 0)
            if coverage < 50:
                recommendations.append("📊 Your grid covers less than 50% of recent price action. Consider widening the range.")
            elif coverage > 90:
                recommendations.append("✅ Excellent grid coverage of recent price movements.")
            
            # Check volatility vs grid spacing
            volatility = market.get("volatility", 0)
            if volatility > 5:
                recommendations.append("⚡ High volatility detected. Consider more grids for better capture.")
            elif volatility < 1:
                recommendations.append("😴 Low volatility. Fewer grids might be more efficient.")
            
            # Check estimated ROI
            roi = performance.get("estimated_roi", 0)
            if roi < 5:
                recommendations.append("💡 Low estimated ROI. Consider adjusting grid parameters or range.")
            elif roi > 50:
                recommendations.append("🚀 High estimated ROI, but verify with actual backtest.")
            
            # Check number of grids
            num_grids = config.get("grid_strategy", {}).get("num_grids", 10)
            if num_grids > 30:
                recommendations.append("🔧 Many grids may increase complexity. Consider reducing for simplicity.")
            elif num_grids < 5:
                recommendations.append("📈 Few grids may miss opportunities. Consider increasing.")
            
            if not recommendations:
                recommendations.append("✅ Configuration looks good! Consider running a full backtest.")
                
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations.append("⚠️ Unable to generate recommendations due to analysis error.")
        
        return recommendations


# Global instance
backtest_service = BacktestService()
