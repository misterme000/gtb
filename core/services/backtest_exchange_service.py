import ccxt, logging, time, os
from typing import Optional, Dict, Any, Union
import pandas as pd
from config.config_manager import ConfigManager
from utils.constants import CANDLE_LIMITS, TIMEFRAME_MAPPINGS
from .base_exchange_service import BaseExchangeService, ExchangeServiceMixin
from .data_formatting_service import data_formatter, data_validator
from .exceptions import UnsupportedExchangeError, DataFetchError, UnsupportedTimeframeError, HistoricalMarketDataFileNotFoundError, UnsupportedPairError

class BacktestExchangeService(BaseExchangeService, ExchangeServiceMixin):
    def __init__(self, config_manager: ConfigManager):
        self.historical_data_file = config_manager.get_historical_data_file()

        # Initialize base class
        super().__init__(config_manager)

    def _create_exchange_instance(self) -> ccxt.Exchange:
        """Create exchange instance for backtesting (no API credentials needed)."""
        try:
            exchange = getattr(ccxt, self.exchange_name)()
            self._log_operation("backtest_exchange_initialized")
            return exchange
        except AttributeError:
            raise UnsupportedExchangeError(f"The exchange '{self.exchange_name}' is not supported.")

    def _is_timeframe_supported(self, timeframe: str) -> bool:
        if timeframe not in self.exchange.timeframes:
            self.logger.error(f"Timeframe '{timeframe}' is not supported by {self.exchange_name}.")
            return False
        return True

    def _is_pair_supported(self, pair: str) -> bool:
        markets = self.exchange.load_markets()
        return pair in markets

    def fetch_ohlcv(
        self,
        pair: str,
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        if self.historical_data_file:
            if not os.path.exists(self.historical_data_file):
                raise HistoricalMarketDataFileNotFoundError(f"Failed to load OHLCV data from file: {self.historical_data_file}")

            self.logger.info(f"Loading OHLCV data from file: {self.historical_data_file}")
            return self._load_ohlcv_from_file(self.historical_data_file, start_date, end_date)

        if not self._is_pair_supported(pair):
            raise UnsupportedPairError(f"Pair: {pair} is not supported by {self.exchange_name}")

        if not self._is_timeframe_supported(timeframe):
            raise UnsupportedTimeframeError(f"Timeframe '{timeframe}' is not supported by {self.exchange_name}.")

        self.logger.info(f"Fetching OHLCV data for {pair} from {start_date} to {end_date}")
        try:
            since = self.exchange.parse8601(start_date)
            until = self.exchange.parse8601(end_date)
            candles_per_request = self._get_candle_limit()
            total_candles_needed = (until - since) // self._get_timeframe_in_ms(timeframe)

            if total_candles_needed > candles_per_request:
                return self._fetch_ohlcv_in_chunks(pair, timeframe, since, until, candles_per_request)
            else:
                return self._fetch_ohlcv_single_batch(pair, timeframe, since, until)
        except ccxt.NetworkError as e:
            raise DataFetchError(f"Network issue occurred while fetching OHLCV data: {str(e)}")
        except ccxt.BaseError as e:
            raise DataFetchError(f"Exchange-specific error occurred: {str(e)}")
        except Exception as e:
            raise DataFetchError(f"Failed to fetch OHLCV data {str(e)}.")

    def _load_ohlcv_from_file(
        self,
        file_path: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        try:
            df = pd.read_csv(file_path, parse_dates=['timestamp'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            start_timestamp = pd.to_datetime(start_date).tz_localize(None)
            end_timestamp = pd.to_datetime(end_date).tz_localize(None)
            filtered_df = df.loc[start_timestamp:end_timestamp]
            self.logger.debug(f"Loaded {len(filtered_df)} rows of OHLCV data from file.")
            return filtered_df

        except Exception as e:
            raise DataFetchError(f"Failed to load OHLCV data from file: {str(e)}")

    def _fetch_ohlcv_single_batch(
        self,
        pair: str,
        timeframe: str,
        since: int,
        until: int
    ) -> pd.DataFrame:
        raw_ohlcv = self._fetch_with_retry(self.exchange.fetch_ohlcv, pair, timeframe, since)
        formatted_df = data_formatter.format_ohlcv_data(raw_ohlcv, pair, timeframe, validate=True)

        # Apply until timestamp filter if provided
        if until:
            until_dt = pd.to_datetime(until, unit='ms')
            formatted_df = formatted_df[formatted_df.index <= until_dt]

        return formatted_df

    def _fetch_ohlcv_in_chunks(
        self,
        pair: str,
        timeframe: str,
        since: int,
        until: int,
        candles_per_request: int
    ) -> pd.DataFrame:
        all_ohlcv = []
        while since < until:
            ohlcv = self._fetch_with_retry(self.exchange.fetch_ohlcv, pair, timeframe, since, limit=candles_per_request)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            self.logger.info(f"Fetched up to {pd.to_datetime(since, unit='ms')}")
        formatted_df = data_formatter.format_ohlcv_data(all_ohlcv, pair, timeframe, validate=True)

        # Apply until timestamp filter if provided
        if until:
            until_dt = pd.to_datetime(until, unit='ms')
            formatted_df = formatted_df[formatted_df.index <= until_dt]

        return formatted_df

    # Removed duplicate _format_ohlcv method - now using base class _format_ohlcv_data method

    def _get_candle_limit(self) -> int:
        return CANDLE_LIMITS.get(self.exchange_name, 500)  # Default to 500 if not found

    def _get_timeframe_in_ms(self, timeframe: str) -> int:
        return TIMEFRAME_MAPPINGS.get(timeframe, 60 * 1000)  # Default to 1m if not found

    # Removed duplicate _fetch_with_retry method - now using base class implementation

    async def place_order(
        self,
        pair: str,
        order_side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None
    ) -> Dict[str, Union[str, float]]:
        raise NotImplementedError("place_order is not used in backtesting")

    async def get_balance(self) -> Dict[str, Any]:
        raise NotImplementedError("get_balance is not used in backtesting")

    async def get_current_price(
        self,
        pair: str
    ) -> float:
        raise NotImplementedError("get_current_price is not used in backtesting")

    async def cancel_order(
        self,
        order_id: str,
        pair: str
    ) -> Dict[str, Union[str, float]]:
        raise NotImplementedError("cancel_order is not used in backtesting")

    async def get_exchange_status(self) -> dict:
        raise NotImplementedError("get_exchange_status is not used in backtesting")

    async def close_connection(self) -> None:
        self.logger.info("[BACKTEST] Closing WebSocket connection...")
