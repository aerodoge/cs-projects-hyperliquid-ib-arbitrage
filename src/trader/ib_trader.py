"""Interactive Brokers trading interface."""

from typing import Optional, Dict
from enum import Enum
import time


class OrderStatus(Enum):
    """订单状态."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    ERROR = "error"


class IBTrader:
    """IB 股票交易接口."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 2):
        """初始化 IB 交易接口.

        Args:
            host: IB Gateway/TWS 主机地址
            port: 端口号（7497=TWS Paper, 4002=Gateway Paper）
            client_id: 客户端 ID（与 fetcher 使用不同的 ID）
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.connected = False

    def connect(self) -> bool:
        """连接到 IB.

        Returns:
            True if successful, False otherwise
        """
        try:
            from ib_insync import IB

            self.ib = IB()
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            print(f"✓ IB Trader connected at {self.host}:{self.port}")
            return True

        except ImportError:
            print("Error: ib_insync not installed")
            return False
        except Exception as e:
            print(f"Error connecting IB Trader: {e}")
            return False

    def disconnect(self):
        """断开连接."""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            print("✓ IB Trader disconnected")

    def buy_stock(
        self,
        symbol: str,
        quantity: int,
        limit_price: Optional[float] = None,
        timeout: int = 30
    ) -> Dict:
        """买入股票.

        Args:
            symbol: 股票代码（如 "NVDA"）
            quantity: 数量
            limit_price: 限价（None = 市价单）
            timeout: 超时时间（秒）

        Returns:
            订单结果字典：
            {
                "success": bool,
                "order_id": int,
                "status": OrderStatus,
                "filled_qty": int,
                "avg_price": float,
                "message": str
            }
        """
        if not self.connected:
            return {
                "success": False,
                "status": OrderStatus.ERROR,
                "message": "Not connected to IB"
            }

        try:
            from ib_insync import Stock, MarketOrder, LimitOrder

            # 创建合约
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)

            # 创建订单
            if limit_price is None:
                order = MarketOrder('BUY', quantity)
                print(f"📤 Placing MARKET BUY order: {quantity} {symbol}")
            else:
                order = LimitOrder('BUY', quantity, limit_price)
                print(f"📤 Placing LIMIT BUY order: {quantity} {symbol} @ ${limit_price}")

            # 提交订单
            trade = self.ib.placeOrder(contract, order)

            # 等待订单完成
            start_time = time.time()
            while time.time() - start_time < timeout:
                self.ib.sleep(0.1)

                if trade.orderStatus.status in ['Filled', 'Cancelled']:
                    break

            # 获取订单状态
            status_map = {
                'Filled': OrderStatus.FILLED,
                'Cancelled': OrderStatus.CANCELLED,
                'Submitted': OrderStatus.PENDING,
                'PreSubmitted': OrderStatus.PENDING,
            }

            order_status = status_map.get(
                trade.orderStatus.status,
                OrderStatus.ERROR
            )

            result = {
                "success": order_status == OrderStatus.FILLED,
                "order_id": trade.order.orderId,
                "status": order_status,
                "filled_qty": int(trade.orderStatus.filled),
                "avg_price": float(trade.orderStatus.avgFillPrice) if trade.orderStatus.avgFillPrice else None,
                "message": f"Order {trade.orderStatus.status}"
            }

            if result["success"]:
                print(f"✅ Order FILLED: {result['filled_qty']} @ ${result['avg_price']:.2f}")
            else:
                print(f"❌ Order {order_status.value}: {result['message']}")

            return result

        except Exception as e:
            print(f"Error placing buy order: {e}")
            return {
                "success": False,
                "status": OrderStatus.ERROR,
                "message": str(e)
            }

    def sell_stock(
        self,
        symbol: str,
        quantity: int,
        limit_price: Optional[float] = None,
        timeout: int = 30
    ) -> Dict:
        """卖出股票.

        Args:
            symbol: 股票代码
            quantity: 数量
            limit_price: 限价（None = 市价单）
            timeout: 超时时间（秒）

        Returns:
            订单结果字典（格式同 buy_stock）
        """
        if not self.connected:
            return {
                "success": False,
                "status": OrderStatus.ERROR,
                "message": "Not connected to IB"
            }

        try:
            from ib_insync import Stock, MarketOrder, LimitOrder

            # 创建合约
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)

            # 创建订单
            if limit_price is None:
                order = MarketOrder('SELL', quantity)
                print(f"📤 Placing MARKET SELL order: {quantity} {symbol}")
            else:
                order = LimitOrder('SELL', quantity, limit_price)
                print(f"📤 Placing LIMIT SELL order: {quantity} {symbol} @ ${limit_price}")

            # 提交订单
            trade = self.ib.placeOrder(contract, order)

            # 等待订单完成
            start_time = time.time()
            while time.time() - start_time < timeout:
                self.ib.sleep(0.1)

                if trade.orderStatus.status in ['Filled', 'Cancelled']:
                    break

            # 获取订单状态
            status_map = {
                'Filled': OrderStatus.FILLED,
                'Cancelled': OrderStatus.CANCELLED,
                'Submitted': OrderStatus.PENDING,
                'PreSubmitted': OrderStatus.PENDING,
            }

            order_status = status_map.get(
                trade.orderStatus.status,
                OrderStatus.ERROR
            )

            result = {
                "success": order_status == OrderStatus.FILLED,
                "order_id": trade.order.orderId,
                "status": order_status,
                "filled_qty": int(trade.orderStatus.filled),
                "avg_price": float(trade.orderStatus.avgFillPrice) if trade.orderStatus.avgFillPrice else None,
                "message": f"Order {trade.orderStatus.status}"
            }

            if result["success"]:
                print(f"✅ Order FILLED: {result['filled_qty']} @ ${result['avg_price']:.2f}")
            else:
                print(f"❌ Order {order_status.value}: {result['message']}")

            return result

        except Exception as e:
            print(f"Error placing sell order: {e}")
            return {
                "success": False,
                "status": OrderStatus.ERROR,
                "message": str(e)
            }

    def get_position(self, symbol: str) -> Optional[int]:
        """获取持仓数量.

        Args:
            symbol: 股票代码

        Returns:
            持仓数量（正数=多头，负数=空头，None=无持仓或错误）
        """
        if not self.connected:
            return None

        try:
            positions = self.ib.positions()

            for pos in positions:
                if pos.contract.symbol == symbol:
                    return int(pos.position)

            return 0  # 无持仓

        except Exception as e:
            print(f"Error getting position: {e}")
            return None

    def get_account_summary(self) -> Dict:
        """获取账户信息.

        Returns:
            账户摘要字典
        """
        if not self.connected:
            return {}

        try:
            account_values = self.ib.accountSummary()

            summary = {}
            for item in account_values:
                summary[item.tag] = item.value

            return summary

        except Exception as e:
            print(f"Error getting account summary: {e}")
            return {}

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
