import ccxt, logging, asyncio, os
from ccxt.base.errors import NetworkError, BaseError, ExchangeError, OrderNotFound
import ccxt.pro as ccxtpro
from typing import Dict, Union, Callable, Any, Optional
import pandas as pd
from config.config_manager import ConfigManager
from .exchange_interface import ExchangeInterface
from .exceptions import UnsupportedExchangeError, DataFetchError, OrderCancellationError, MissingEnvironmentVariableError
from core.error_handling import (
    ErrorContext, ErrorCategory, ErrorSeverity,
    NetworkError as UnifiedNetworkError, ExchangeError as UnifiedExchangeError,
    error_handler, handle_error_decorator
)

class LiveExchangeService(ExchangeInterface):
    def __init__(
        self, 
        config_manager: ConfigManager, 
        is_paper_trading_activated: bool
    ):
        self.config_manager = config_manager
        self.is_paper_trading_activated = is_paper_trading_activated
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exchange_name = self.config_manager.get_exchange_name()
        self.api_key = self._get_env_variable("EXCHANGE_API_KEY")
        self.secret_key = self._get_env_variable("EXCHANGE_SECRET_KEY")
        self.exchange = self._initialize_exchange()
        self.connection_active = False
    
    def _get_env_variable(self, key: str) -> str:
        value = os.getenv(key)
        if value is None:
            raise MissingEnvironmentVariableError(f"Missing required environment variable: {key}")
        return value

    def _initialize_exchange(self) -> None:
        try:
            exchange = getattr(ccxtpro, self.exchange_name)({
                'apiKey': self.api_key,
                'secret': self.secret_key,
                'enableRateLimit': True
            })

            if self.is_paper_trading_activated:
                self._enable_sandbox_mode(exchange)
            return exchange
        except AttributeError:
            raise UnsupportedExchangeError(f"The exchange '{self.exchange_name}' is not supported.")

    def _enable_sandbox_mode(self, exchange) -> None:
        if self.exchange_name == 'binance':
            exchange.urls['api'] = 'https://testnet.binance.vision/api'
        elif self.exchange_name == 'kraken':
            exchange.urls['api'] = 'https://api.demo-futures.kraken.com'
        elif self.exchange_name == 'bitmex':
            exchange.urls['api'] = 'https://testnet.bitmex.com'
        elif self.exchange_name == 'bybit':
            exchange.set_sandbox_mode(True)
        else:
            self.logger.warning(f"No sandbox mode available for {self.exchange_name}. Running in live mode.")
    
    async def _subscribe_to_ticker_updates(
        self,
        pair: str, 
        on_ticker_update: Callable[[float], None], 
        update_interval: float,
        max_retries: int = 5
    ) -> None:
        self.connection_active = True
        retry_count = 0
        
        while self.connection_active:
            try:
                ticker = await self.exchange.watch_ticker(pair)
                current_price: float = ticker['last']
                self.logger.info(f"Connected to WebSocket for {pair} ticker current price: {current_price}")

                if not self.connection_active:
                    break

                await on_ticker_update(current_price)
                await asyncio.sleep(update_interval)
                retry_count = 0  # Reset retry count after a successful operation

            except (NetworkError, ExchangeError) as e:
                retry_count += 1
                retry_interval = min(retry_count * 5, 60)
                self.logger.error(f"Error connecting to WebSocket for {pair}: {e}. Retrying in {retry_interval} seconds ({retry_count}/{max_retries}).")
                
                if retry_count >= max_retries:
                    self.logger.error("Max retries reached. Stopping WebSocket connection.")
                    self.connection_active = False
                    break

                await asyncio.sleep(retry_interval)
            
            except asyncio.CancelledError:
                self.logger.error(f"WebSocket subscription for {pair} was cancelled.")
                self.connection_active = False
                break

            except Exception as e:
                self.logger.error(f"WebSocket connection error: {e}. Reconnecting...")
                await asyncio.sleep(5)

            finally:
                if not self.connection_active:
                    try:
                        self.logger.info("Connection to Websocket no longer active.")
                        await self.exchange.close()

                    except Exception as e:
                        self.logger.error(f"Error while closing WebSocket connection: {e}", exc_info=True)

    async def listen_to_ticker_updates(
        self, 
        pair: str, 
        on_price_update: Callable[[float], None],
        update_interval: float
    ) -> None:
        await self._subscribe_to_ticker_updates(pair, on_price_update, update_interval)

    async def close_connection(self) -> None:
        self.connection_active = False
        self.logger.info("Closing WebSocket connection...")

    async def get_balance(self) -> Dict[str, Any]:
        try:
            balance = await self.exchange.fetch_balance()
            return balance

        except BaseError as e:
            raise DataFetchError(f"Error fetching balance: {str(e)}")
    
    async def get_current_price(self, pair: str) -> float:
        try:
            ticker = await self.exchange.fetch_ticker(pair)
            return ticker['last']

        except BaseError as e:
            raise DataFetchError(f"Error fetching current price: {str(e)}")

    @handle_error_decorator(
        category=ErrorCategory.ORDER_EXECUTION,
        severity=ErrorSeverity.HIGH,
        recovery_suggestions=[
            "Check account balance and available funds",
            "Verify order parameters (pair, amount, price)",
            "Check exchange connectivity",
            "Try again with adjusted parameters"
        ]
    )
    async def place_order(
        self,
        pair: str,
        order_type: str,
        order_side: str,
        amount: float,
        price: Optional[float] = None
    ) -> Dict[str, Union[str, float]]:
        context = ErrorContext(
            operation="place_order",
            component="LiveExchangeService",
            additional_data={
                "pair": pair,
                "order_type": order_type,
                "order_side": order_side,
                "amount": amount,
                "price": price
            }
        )

        try:
            order = await self.exchange.create_order(pair, order_type, order_side, amount, price)
            return order

        except NetworkError as e:
            network_error = UnifiedNetworkError(
                message=f"Network issue occurred while placing order: {str(e)}",
                context=context,
                original_exception=e
            )
            handled_error = await error_handler.handle_error(network_error)
            if handled_error:
                raise DataFetchError(handled_error.user_message)

        except BaseError as e:
            exchange_error = UnifiedExchangeError(
                message=f"Exchange error while placing order: {str(e)}",
                context=context,
                original_exception=e
            )
            handled_error = await error_handler.handle_error(exchange_error)
            if handled_error:
                raise DataFetchError(handled_error.user_message)

        except Exception as e:
            # Let the decorator handle unexpected errors
            raise

    async def fetch_order(
        self, 
        order_id: str,
        pair: str
    ) -> Dict[str, Union[str, float]]:
        try:
            return await self.exchange.fetch_order(order_id, pair)

        except NetworkError as e:
            raise DataFetchError(f"Network issue occurred while fetching order status: {str(e)}")

        except BaseError as e:
            raise DataFetchError(f"Exchange-specific error occurred: {str(e)}")

        except Exception as e:
            raise DataFetchError(f"Failed to fetch order status: {str(e)}")

    async def cancel_order(
        self, 
        order_id: str, 
        pair: str
    ) -> dict:
        try:
            self.logger.info(f"Attempting to cancel order {order_id} for pair {pair}")
            cancellation_result = await self.exchange.cancel_order(order_id, pair)
            
            if cancellation_result['status'] in ['canceled', 'closed']:
                self.logger.info(f"Order {order_id} successfully canceled.")
                return cancellation_result
            else:
                self.logger.warning(f"Order {order_id} cancellation status: {cancellation_result['status']}")
                return cancellation_result

        except OrderNotFound as e:
            raise OrderCancellationError(f"Order {order_id} not found for cancellation. It may already be completed or canceled.")

        except NetworkError as e:
            raise OrderCancellationError(f"Network error while canceling order {order_id}: {str(e)}")

        except BaseError as e:
            raise OrderCancellationError(f"Exchange error while canceling order {order_id}: {str(e)}")

        except Exception as e:
            raise OrderCancellationError(f"Unexpected error while canceling order {order_id}: {str(e)}")
    
    async def get_exchange_status(self) -> dict:
        try:
            status = await self.exchange.fetch_status()
            return {
                "status": status.get("status", "unknown"),
                "updated": status.get("updated"),
                "eta": status.get("eta"),
                "url": status.get("url"),
                "info": status.get("info", "No additional info available")
            }

        except AttributeError:
            return {"status": "unsupported", "info": "fetch_status not supported by this exchange."}

        except Exception as e:
            return {"status": "error", "info": f"Failed to fetch exchange status: {e}"}

    def fetch_ohlcv(
        self, 
        pair: str, 
        timeframe: str, 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        raise NotImplementedError("fetch_ohlcv is not used in live or paper trading mode.")