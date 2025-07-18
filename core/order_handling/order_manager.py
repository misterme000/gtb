import logging
from typing import Union, Optional
from datetime import datetime
import pandas as pd
from .order import Order, OrderSide, OrderStatus
from ..order_handling.balance_tracker import BalanceTracker
from ..order_handling.order_book import OrderBook
from ..grid_management.grid_manager import GridManager
from ..grid_management.grid_level import GridLevel
from ..validation.order_validator import OrderValidator
from core.bot_management.event_bus import EventBus, Events
from .execution_strategy.order_execution_strategy_interface import OrderExecutionStrategyInterface
from core.bot_management.notification.notification_handler import NotificationHandler
from core.bot_management.notification.notification_content import NotificationType
from strategies.strategy_type import StrategyType
from config.trading_mode import TradingMode
from .exceptions import OrderExecutionFailedError
from core.error_handling import (
    ErrorContext, ErrorCategory, ErrorSeverity,
    OrderExecutionError, error_handler, handle_error_decorator
)

class OrderManager:
    def __init__(
        self, 
        grid_manager: GridManager,
        order_validator: OrderValidator, 
        balance_tracker: BalanceTracker, 
        order_book: OrderBook,
        event_bus: EventBus,
        order_execution_strategy: OrderExecutionStrategyInterface,
        notification_handler: NotificationHandler,
        trading_mode: TradingMode,
        trading_pair: str,
        strategy_type: StrategyType
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.grid_manager = grid_manager
        self.order_validator = order_validator
        self.balance_tracker = balance_tracker
        self.order_book = order_book
        self.event_bus = event_bus
        self.order_execution_strategy = order_execution_strategy
        self.notification_handler = notification_handler
        self.trading_mode: TradingMode = trading_mode
        self.trading_pair = trading_pair
        self.strategy_type: StrategyType = strategy_type
        self.event_bus.subscribe(Events.ORDER_FILLED, self._on_order_filled)
        self.event_bus.subscribe(Events.ORDER_CANCELLED, self._on_order_cancelled)
    
    async def initialize_grid_orders(
        self, 
        current_price: float
    ):
        """
        Places initial buy orders for grid levels below the current price.
        """
        for price in self.grid_manager.sorted_buy_grids:
            if price >= current_price:
                self.logger.info(f"Skipping grid level at price: {price} for BUY order: Above current price.")
                continue

            grid_level = self.grid_manager.grid_levels[price]
            total_balance_value = self.balance_tracker.get_total_balance_value(current_price)
            order_quantity = self.grid_manager.get_order_size_for_grid_level(total_balance_value, current_price)

            if self.grid_manager.can_place_order(grid_level, OrderSide.BUY):
                try:
                    adjusted_buy_order_quantity = self.order_validator.adjust_and_validate_buy_quantity(
                        balance=self.balance_tracker.balance,
                        order_quantity=order_quantity,
                        price=price
                    )

                    self.logger.info(f"Placing initial buy limit order at grid level {price} for {adjusted_buy_order_quantity} {self.trading_pair}.")
                    order = await self.order_execution_strategy.execute_limit_order(
                        OrderSide.BUY, 
                        self.trading_pair, 
                        adjusted_buy_order_quantity, 
                        price
                    )

                    if order is None:
                        self.logger.error(f"Failed to place buy order at {price}: No order returned.")
                        continue

                    self.balance_tracker.reserve_funds_for_buy(adjusted_buy_order_quantity * price)
                    self.grid_manager.mark_order_pending(grid_level, order)
                    self.order_book.add_order(order, grid_level)

                except OrderExecutionFailedError as e:
                    self.logger.error(f"Failed to initialize buy order at grid level {price} - {str(e)}", exc_info=True)
                    await self.notification_handler.async_send_notification(NotificationType.ORDER_FAILED, error_details=f"Error while placing initial buy order. {e}")

                except Exception as e:
                    self.logger.error(f"Unexpected error during buy order initialization at grid level {price}: {e}", exc_info=True)
                    await self.notification_handler.async_send_notification(NotificationType.ERROR_OCCURRED, error_details=f"Error while placing initial buy order: {str(e)}")
        
        for price in self.grid_manager.sorted_sell_grids:
            if price <= current_price:
                self.logger.info(f"Skipping grid level at price: {price} for SELL order: Below or equal to current price.")
                continue

            grid_level = self.grid_manager.grid_levels[price]
            total_balance_value = self.balance_tracker.get_total_balance_value(current_price)
            order_quantity = self.grid_manager.get_order_size_for_grid_level(total_balance_value, current_price)

            if self.grid_manager.can_place_order(grid_level, OrderSide.SELL):
                try:
                    adjusted_sell_order_quantity = self.order_validator.adjust_and_validate_sell_quantity(
                        crypto_balance=self.balance_tracker.crypto_balance,
                        order_quantity=order_quantity
                    )

                    self.logger.info(f"Placing initial sell limit order at grid level {price} for {adjusted_sell_order_quantity} {self.trading_pair}.")
                    order = await self.order_execution_strategy.execute_limit_order(
                        OrderSide.SELL, 
                        self.trading_pair, 
                        adjusted_sell_order_quantity, 
                        price
                    )

                    if order is None:
                        self.logger.error(f"Failed to place sell order at {price}: No order returned.")
                        continue

                    self.balance_tracker.reserve_funds_for_sell(adjusted_sell_order_quantity)
                    self.grid_manager.mark_order_pending(grid_level, order)
                    self.order_book.add_order(order, grid_level)

                except OrderExecutionFailedError as e:
                    self.logger.error(f"Failed to initialize sell order at grid level {price} - {str(e)}", exc_info=True)
                    await self.notification_handler.async_send_notification(NotificationType.ORDER_FAILED, error_details=f"Error while placing initial sell order. {e}")

                except Exception as e:
                    self.logger.error(f"Unexpected error during sell order initialization at grid level {price}: {e}", exc_info=True)
                    await self.notification_handler.async_send_notification(NotificationType.ERROR_OCCURRED, error_details=f"Error while placing initial sell order: {str(e)}")

    async def _on_order_cancelled(
        self,
        order: Order
    ) -> None:
        """
        Handles cancelled orders by attempting to replace them with new limit orders.

        Args:
            order: The cancelled Order instance.
        """
        try:
            self.logger.info(f"Handling cancelled order: {order.identifier} at price {order.price}")

            # Get the grid level associated with the cancelled order
            grid_level = self.order_book.get_grid_level_for_order(order)

            if not grid_level:
                self.logger.warning(f"No grid level found for cancelled order {order.identifier}. Cannot replace order.")
                await self.notification_handler.async_send_notification(
                    NotificationType.ORDER_CANCELLED,
                    order_details=f"Order cancelled but cannot be replaced: {str(order)}"
                )
                return

            # Mark the grid level as available for new orders
            self.grid_manager.mark_order_cancelled(grid_level, order)

            # Remove the cancelled order from the order book
            self.order_book.remove_order(order.identifier)

            # Release reserved funds based on order type
            if order.side == OrderSide.BUY:
                reserved_amount = order.amount * order.price
                self.balance_tracker.release_reserved_buy_funds(reserved_amount)
                self.logger.info(f"Released {reserved_amount} reserved buy funds for cancelled order")
            else:  # SELL order
                self.balance_tracker.release_reserved_sell_funds(order.amount)
                self.logger.info(f"Released {order.amount} reserved sell funds for cancelled order")

            # Attempt to place a replacement order at the same grid level
            await self._place_replacement_order(order, grid_level)

        except Exception as e:
            context = ErrorContext(
                operation="handle_cancelled_order",
                component="OrderManager",
                additional_data={
                    "order_id": order.identifier,
                    "order_price": order.price,
                    "order_side": order.side.value
                }
            )

            error = OrderExecutionError(
                message=f"Error handling cancelled order {order.identifier}: {str(e)}",
                context=context,
                original_exception=e,
                severity=ErrorSeverity.HIGH,
                recovery_suggestions=[
                    "Check order status manually",
                    "Verify grid level state",
                    "Review balance allocation"
                ]
            )

            handled_error = await error_handler.handle_error(error)
            if handled_error:
                await self.notification_handler.async_send_notification(
                    NotificationType.ERROR_OCCURRED,
                    error_details=handled_error.user_message
                )

    async def _place_replacement_order(
        self,
        cancelled_order: Order,
        grid_level: GridLevel
    ) -> None:
        """
        Places a replacement order for a cancelled order at the same grid level.

        Args:
            cancelled_order: The original cancelled order
            grid_level: The grid level where the replacement order should be placed
        """
        try:
            # Check if we can still place an order at this grid level
            if not self.grid_manager.can_place_order(grid_level, cancelled_order.side):
                self.logger.info(f"Cannot place replacement order at grid level {grid_level.price} - conditions not met")
                await self.notification_handler.async_send_notification(
                    NotificationType.ORDER_CANCELLED,
                    order_details=f"Cancelled order not replaced - grid conditions changed: {str(cancelled_order)}"
                )
                return

            # Calculate the replacement order quantity
            if cancelled_order.side == OrderSide.BUY:
                # For buy orders, validate against current balance
                adjusted_quantity = self.order_validator.adjust_and_validate_buy_quantity(
                    balance=self.balance_tracker.balance,
                    order_quantity=cancelled_order.amount,
                    price=grid_level.price
                )
            else:
                # For sell orders, validate against crypto balance
                adjusted_quantity = self.order_validator.adjust_and_validate_sell_quantity(
                    crypto_balance=self.balance_tracker.crypto_balance,
                    order_quantity=cancelled_order.amount
                )

            if adjusted_quantity <= 0:
                self.logger.warning(f"Cannot place replacement order - insufficient balance for {cancelled_order.side.value} order")
                await self.notification_handler.async_send_notification(
                    NotificationType.ORDER_CANCELLED,
                    order_details=f"Cancelled order not replaced - insufficient balance: {str(cancelled_order)}"
                )
                return

            # Place the replacement limit order
            self.logger.info(f"Placing replacement {cancelled_order.side.value} order at grid level {grid_level.price} for {adjusted_quantity}")
            replacement_order = await self.order_execution_strategy.execute_limit_order(
                cancelled_order.side,
                self.trading_pair,
                adjusted_quantity,
                grid_level.price
            )

            if replacement_order:
                # Reserve funds for the new order
                if cancelled_order.side == OrderSide.BUY:
                    self.balance_tracker.reserve_funds_for_buy(adjusted_quantity * grid_level.price)
                else:
                    self.balance_tracker.reserve_funds_for_sell(adjusted_quantity)

                # Update grid manager and order book
                self.grid_manager.mark_order_pending(grid_level, replacement_order)
                self.order_book.add_order(replacement_order, grid_level)

                self.logger.info(f"Successfully placed replacement order {replacement_order.identifier}")
                await self.notification_handler.async_send_notification(
                    NotificationType.ORDER_PLACED,
                    order_details=f"Replacement order placed: {str(replacement_order)}"
                )
            else:
                self.logger.error(f"Failed to place replacement order at grid level {grid_level.price}")
                await self.notification_handler.async_send_notification(
                    NotificationType.ORDER_FAILED,
                    error_details=f"Failed to place replacement order for cancelled order: {str(cancelled_order)}"
                )

        except OrderExecutionFailedError as e:
            self.logger.error(f"Failed to place replacement order: {str(e)}", exc_info=True)
            await self.notification_handler.async_send_notification(
                NotificationType.ORDER_FAILED,
                error_details=f"Failed to place replacement order: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error placing replacement order: {e}", exc_info=True)
            await self.notification_handler.async_send_notification(
                NotificationType.ERROR_OCCURRED,
                error_details=f"Unexpected error placing replacement order: {str(e)}"
            )

    async def _on_order_filled(
        self, 
        order: Order
    ) -> None:
        """
        Handles filled orders and places paired orders as needed.

        Args:
            order: The filled Order instance.
        """
        try:
            grid_level = self.order_book.get_grid_level_for_order(order)

            if not grid_level:
                self.logger.warning(f"Could not handle Order completion - No grid level found for the given filled order {order}")
                return

            await self._handle_order_completion(order, grid_level)

        except OrderExecutionFailedError as e:
            self.logger.error(f"Failed while handling filled order - {str(e)}", exc_info=True)
            await self.notification_handler.async_send_notification(NotificationType.ORDER_FAILED, error_details=f"Failed handling filled order. {e}")

        except Exception as e:
            self.logger.error(f"Error while handling filled order {order.identifier}: {e}", exc_info=True)
            await self.notification_handler.async_send_notification(NotificationType.ORDER_FAILED, error_details=f"Failed handling filled order. {e}")
    
    async def _handle_order_completion(
        self, 
        order: Order, 
        grid_level: GridLevel
    ) -> None:
        """
        Handles the completion of an order (buy or sell).

        Args:
            order: The filled Order instance.
            grid_level: The grid level associated with the filled order.
        """
        if order.side == OrderSide.BUY:
            await self._handle_buy_order_completion(order, grid_level)

        elif order.side == OrderSide.SELL:
            await self._handle_sell_order_completion(order, grid_level)
    
    async def _handle_buy_order_completion(
        self, 
        order: Order, 
        grid_level: GridLevel
    ) -> None:
        """
        Handles the completion of a buy order.

        Args:
            order: The completed Buy Order instance.
            grid_level: The grid level associated with the completed buy order.
        """
        self.logger.info(f"Buy order completed at grid level {grid_level}.")
        self.grid_manager.complete_order(grid_level, OrderSide.BUY)
        paired_sell_level = self.grid_manager.get_paired_sell_level(grid_level)

        if paired_sell_level and self.grid_manager.can_place_order(paired_sell_level, OrderSide.SELL):
            await self._place_sell_order(grid_level, paired_sell_level, order.filled)
        else:
            self.logger.warning(f"No valid sell grid level found for buy grid level {grid_level}. Skipping sell order placement.")
    
    async def _handle_sell_order_completion(
        self, 
        order: Order, 
        grid_level: GridLevel
    ) -> None:
        """
        Handles the completion of a sell order.

        Args:
            order: The completed Sell Order instance.
            grid_level: The grid level associated with the completed sell order.
        """
        self.logger.info(f"Sell order completed at grid level {grid_level}.")
        self.grid_manager.complete_order(grid_level, OrderSide.SELL)
        paired_buy_level = self._get_or_create_paired_buy_level(grid_level)

        if paired_buy_level:
            await self._place_buy_order(grid_level, paired_buy_level, order.filled)
        else:
            self.logger.error(f"Failed to find or create a paired buy grid level for grid level {grid_level}.")

    def _get_or_create_paired_buy_level(self, sell_grid_level: GridLevel) -> Optional[GridLevel]:
        """
        Retrieves or creates a paired buy grid level for the given sell grid level.

        Args:
            sell_grid_level: The sell grid level to find a paired buy level for.

        Returns:
            The paired buy grid level, or None if a valid level cannot be found.
        """
        paired_buy_level = sell_grid_level.paired_buy_level

        if paired_buy_level and self.grid_manager.can_place_order(paired_buy_level, OrderSide.BUY):
            self.logger.info(f"Found valid paired buy level {paired_buy_level} for sell level {sell_grid_level}.")
            return paired_buy_level

        fallback_buy_level = self.grid_manager.get_grid_level_below(sell_grid_level)

        if fallback_buy_level:
            self.logger.info(f"Paired fallback buy level {fallback_buy_level} with sell level {sell_grid_level}.")
            return fallback_buy_level

        self.logger.warning(f"No valid fallback buy level found below sell level {sell_grid_level}.")
        return None
    
    async def _place_buy_order(
        self, 
        sell_grid_level: GridLevel, 
        buy_grid_level: GridLevel, 
        quantity: float
    ) -> None:
        """
        Places a buy order at the specified grid level.

        Args:
            grid_level: The grid level to place the buy order on.
            quantity: The quantity of the buy order.
        """
        adjusted_quantity = self.order_validator.adjust_and_validate_buy_quantity(self.balance_tracker.balance, quantity, buy_grid_level.price)
        buy_order = await self.order_execution_strategy.execute_limit_order(
            OrderSide.BUY, 
            self.trading_pair, 
            adjusted_quantity, 
            buy_grid_level.price
        )

        if buy_order:
            self.grid_manager.pair_grid_levels(sell_grid_level, buy_grid_level, pairing_type="buy")
            self.balance_tracker.reserve_funds_for_buy(buy_order.amount * buy_grid_level.price)
            self.grid_manager.mark_order_pending(buy_grid_level, buy_order)
            self.order_book.add_order(buy_order, buy_grid_level)
            await self.notification_handler.async_send_notification(NotificationType.ORDER_PLACED, order_details=str(buy_order))  
        else:
            self.logger.error(f"Failed to place buy order at grid level {buy_grid_level}")

    async def _place_sell_order(
        self, 
        buy_grid_level: GridLevel, 
        sell_grid_level: GridLevel, 
        quantity: float
    ) -> None:
        """
        Places a sell order at the specified grid level.

        Args:
            grid_level: The grid level to place the sell order on.
            quantity: The quantity of the sell order.
        """
        adjusted_quantity = self.order_validator.adjust_and_validate_sell_quantity(self.balance_tracker.crypto_balance, quantity)
        sell_order = await self.order_execution_strategy.execute_limit_order(
            OrderSide.SELL, 
            self.trading_pair, 
            adjusted_quantity, 
            sell_grid_level.price
        )

        if sell_order:
            self.grid_manager.pair_grid_levels(buy_grid_level, sell_grid_level, pairing_type="sell")
            self.balance_tracker.reserve_funds_for_sell(sell_order.amount)
            self.grid_manager.mark_order_pending(sell_grid_level, sell_order)
            self.order_book.add_order(sell_order, sell_grid_level)
            await self.notification_handler.async_send_notification(NotificationType.ORDER_PLACED, order_details=str(sell_order))  
        else:
            self.logger.error(f"Failed to place sell order at grid level {sell_grid_level}.")
                
    async def perform_initial_purchase(
        self, 
        current_price: float
    ) -> None:
        """
        Handles the initial crypto purchase for grid trading strategy if required.

        Args:
            current_price: The current price of the trading pair.
        """
        initial_quantity = self.grid_manager.get_initial_order_quantity(
            current_fiat_balance=self.balance_tracker.balance,
            current_crypto_balance=self.balance_tracker.crypto_balance,
            current_price=current_price
        )
        
        if initial_quantity <= 0:
            self.logger.warning("Initial purchase quantity is zero or negative. Skipping initial purchase.")
            return

        self.logger.info(f"Performing initial crypto purchase: {initial_quantity} at price {current_price}.")

        try:
            buy_order = await self.order_execution_strategy.execute_market_order(
                OrderSide.BUY, 
                self.trading_pair, 
                initial_quantity, 
                current_price
            )
            self.logger.info(f"Initial crypto purchase completed. Order details: {buy_order}")
            self.order_book.add_order(buy_order)
            await self.notification_handler.async_send_notification(NotificationType.ORDER_PLACED, order_details=f"Initial purchase done: {str(buy_order)}")  

            if self.trading_mode == TradingMode.BACKTEST:
                await self._simulate_fill(buy_order, buy_order.timestamp)
            else:
                # Update fiat and crypto balance in LIVE & PAPER_TRADING modes without simulating it
                self.balance_tracker.update_after_initial_purchase(initial_order=buy_order)

        except OrderExecutionFailedError as e:
            self.logger.error(f"Failed while executing initial purchase - {str(e)}", exc_info=True)
            await self.notification_handler.async_send_notification(NotificationType.ORDER_FAILED, error_details=f"Error while performing initial purchase. {e}")

        except Exception as e:
            self.logger.error(f"Failed to perform initial purchase at current_price: {current_price} - error: {e}", exc_info=True)
            await self.notification_handler.async_send_notification(NotificationType.ORDER_FAILED, error_details=f"Error while performing initial purchase. {e}")

    async def execute_take_profit_or_stop_loss_order(
        self,
        current_price: float,
        take_profit_order: bool = False,
        stop_loss_order: bool = False
    ) -> None:
        """
        Executes a sell order triggered by either a take-profit or stop-loss event.

        This method checks whether a take-profit or stop-loss condition has been met
        and places a market sell order accordingly. It uses the crypto balance tracked
        by the `BalanceTracker` and sends notifications upon success or failure.

        Args:
            current_price (float): The current market price triggering the event.
            take_profit_order (bool): Indicates whether this is a take-profit event.
            stop_loss_order (bool): Indicates whether this is a stop-loss event.
        """
        if not (take_profit_order or stop_loss_order):
            self.logger.warning("No take profit or stop loss action specified.")
            return

        event = "Take profit" if take_profit_order else "Stop loss"
        try:
            quantity = self.balance_tracker.crypto_balance
            order = await self.order_execution_strategy.execute_market_order(OrderSide.SELL, self.trading_pair, quantity, current_price)

            if not order:
                self.logger.error(f"Order execution failed: {order}")
                raise Exception

            self.order_book.add_order(order)
            await self.notification_handler.async_send_notification(
                NotificationType.TAKE_PROFIT_TRIGGERED if take_profit_order else NotificationType.STOP_LOSS_TRIGGERED,
                order_details=str(order)
            )            
            self.logger.info(f"{event} triggered at {current_price} and sell order executed.")
        
        except OrderExecutionFailedError as e:
            self.logger.error(f"Order execution failed: {str(e)}")
            await self.notification_handler.async_send_notification(NotificationType.ORDER_FAILED, error_details=f"Failed to place {event} order: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to execute {event} sell order at {current_price}: {e}")
            await self.notification_handler.async_send_notification(NotificationType.ERROR_OCCURRED, error_details=f"Failed to place {event} order: {e}")
    
    async def simulate_order_fills(
        self, 
        high_price: float, 
        low_price: float, 
        timestamp: Union[int, pd.Timestamp]
    ) -> None:
        """
        Simulates the execution of limit orders based on crossed grid levels within the high-low price range.

        Args:
            high_price: The highest price reached in this time interval.
            low_price: The lowest price reached in this time interval.
            timestamp: The current timestamp in the backtest simulation.
        """
        timestamp_val = int(timestamp.timestamp()) if isinstance(timestamp, pd.Timestamp) else int(timestamp)
        pending_orders = self.order_book.get_open_orders()
        crossed_buy_levels = [level for level in self.grid_manager.sorted_buy_grids if low_price <= level <= high_price]
        crossed_sell_levels = [level for level in self.grid_manager.sorted_sell_grids if low_price <= level <= high_price]

        self.logger.debug(f"Simulating fills: High {high_price}, Low {low_price}, Pending orders: {len(pending_orders)}")
        self.logger.debug(f"Crossed buy levels: {crossed_buy_levels}, Crossed sell levels: {crossed_sell_levels}")

        for order in pending_orders:
            if order.side == OrderSide.BUY and order.price in crossed_buy_levels:
                await self._simulate_fill(order, timestamp_val)

            elif order.side == OrderSide.SELL and order.price in crossed_sell_levels:
                await self._simulate_fill(order, timestamp_val)

    async def _simulate_fill(
        self, 
        order: Order, 
        timestamp: int
    ) -> None:
        """
        Simulates filling an order by marking it as completed and publishing an event.

        Args:
            order: The order to simulate a fill for.
            timestamp: The timestamp at which the order is filled.
        """
        order.filled = order.amount
        order.remaining = 0.0
        order.status = OrderStatus.CLOSED 
        order.timestamp = timestamp
        order.last_trade_timestamp = timestamp
        timestamp_in_seconds = timestamp / 1000 if timestamp > 10**10 else timestamp
        formatted_timestamp = datetime.fromtimestamp(timestamp_in_seconds).strftime('%Y-%m-%d %H:%M:%S')
        self.logger.info(f"Simulated fill for {order.side.value.upper()} order at price {order.price} with amount {order.amount}. Filled at timestamp {formatted_timestamp}")
        await self.event_bus.publish(Events.ORDER_FILLED, order)