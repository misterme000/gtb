from typing import List, Dict, Optional, Tuple
from .order import Order, OrderSide, OrderStatus
from ..grid_management.grid_level import GridLevel

class OrderBook:
    def __init__(self):
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        self.non_grid_orders: List[Order] = []  # Orders that are not linked to any grid level
        self.order_to_grid_map: Dict[Order, GridLevel] = {}  # Mapping of Order -> GridLevel
    
    def add_order(
        self,
        order: Order,
        grid_level: Optional[GridLevel] = None
    ) -> None:
        if order.side == OrderSide.BUY:
            self.buy_orders.append(order)
        else:
            self.sell_orders.append(order)

        if grid_level:
            self.order_to_grid_map[order] = grid_level # Store the grid level associated with this order
        else:
            self.non_grid_orders.append(order) # This is a non-grid order like take profit or stop loss
    
    def get_buy_orders_with_grid(self) -> List[Tuple[Order, Optional[GridLevel]]]:
        return [(order, self.order_to_grid_map.get(order, None)) for order in self.buy_orders]
    
    def get_sell_orders_with_grid(self) -> List[Tuple[Order, Optional[GridLevel]]]:
        return [(order, self.order_to_grid_map.get(order, None)) for order in self.sell_orders]

    def get_all_buy_orders(self) -> List[Order]:
        return self.buy_orders

    def get_all_sell_orders(self) -> List[Order]:
        return self.sell_orders
    
    def get_open_orders(self) -> List[Order]:
        return [order for order in self.buy_orders + self.sell_orders if order.is_open()]

    def get_completed_orders(self) -> List[Order]:
        return [order for order in self.buy_orders + self.sell_orders if order.is_filled()]

    def get_grid_level_for_order(self, order: Order) -> Optional[GridLevel]:
        return self.order_to_grid_map.get(order)

    def update_order_status(
        self,
        order_id: str,
        new_status: OrderStatus
    ) -> None:
        for order in self.buy_orders + self.sell_orders:
            if order.identifier == order_id:
                order.status = new_status
                break

    def remove_order(self, order_id: str) -> Optional[Order]:
        """
        Removes an order from the order book by its identifier.

        Args:
            order_id: The identifier of the order to remove.

        Returns:
            The removed Order object if found, None otherwise.
        """
        # Check buy orders
        for i, order in enumerate(self.buy_orders):
            if order.identifier == order_id:
                removed_order = self.buy_orders.pop(i)
                # Remove from grid mapping if it exists
                if removed_order in self.order_to_grid_map:
                    del self.order_to_grid_map[removed_order]
                # Remove from non-grid orders if it exists
                if removed_order in self.non_grid_orders:
                    self.non_grid_orders.remove(removed_order)
                return removed_order

        # Check sell orders
        for i, order in enumerate(self.sell_orders):
            if order.identifier == order_id:
                removed_order = self.sell_orders.pop(i)
                # Remove from grid mapping if it exists
                if removed_order in self.order_to_grid_map:
                    del self.order_to_grid_map[removed_order]
                # Remove from non-grid orders if it exists
                if removed_order in self.non_grid_orders:
                    self.non_grid_orders.remove(removed_order)
                return removed_order

        return None