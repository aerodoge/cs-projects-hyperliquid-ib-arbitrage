"""Interactive Brokers data fetcher with streaming/subscription mode."""

from typing import Dict, Optional
import time


class IBKRFetcherStreaming:
    """Fetches stock price data from IBKR using subscription mode."""

    def __init__(self, symbol: str = "NVDA", host: str = "127.0.0.1", port: int = 7497,
                 client_id: int = 1, account_id: str = None):
        """Initialize the IBKR data fetcher with streaming mode.

        Args:
            symbol: Stock symbol (e.g., "NVDA")
            host: IB Gateway/TWS host
            port: IB Gateway/TWS port
            client_id: Unique client ID
            account_id: IBKR account ID (optional)
        """
        self.symbol = symbol
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account_id = account_id
        self.ib = None
        self.connected = False
        self.ticker = None  # 保持订阅的 ticker 对象
        self.contract = None

    def connect(self) -> bool:
        """Connect to Interactive Brokers and subscribe to market data.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            from ib_insync import IB, Stock

            self.ib = IB()
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            print(f"✓ Connected to IBKR at {self.host}:{self.port}")

            # 创建合约并订阅市场数据（只订阅一次）
            self.contract = Stock(self.symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(self.contract)

            # 设置市场数据类型: 1=实时, 3=延迟
            # 如果没有实时数据订阅，使用延迟数据（15分钟延迟，免费）
            # 订阅实时数据后改为 reqMarketDataType(1)
            self.ib.reqMarketDataType(1)

            # 订阅市场数据（持续订阅，不取消）
            self.ticker = self.ib.reqMktData(self.contract, '', False, False)
            print(f"✓ Subscribed to {self.symbol} market data stream")

            # 等待初始数据
            timeout = 10
            start_time = time.time()
            import math
            while (time.time() - start_time < timeout):
                self.ib.sleep(0.1)
                if (self.ticker.bid and not math.isnan(self.ticker.bid) and
                    self.ticker.ask and not math.isnan(self.ticker.ask)):
                    print(f"✓ Initial market data received")
                    break

            return True

        except ImportError:
            print("Error: ib_insync not installed. Install with: pip install ib_insync")
            return False
        except Exception as e:
            print(f"Error connecting to IBKR: {e}")
            return False

    def disconnect(self):
        """Disconnect from Interactive Brokers and cancel subscriptions."""
        if self.ib and self.connected:
            # 取消市场数据订阅
            if self.contract:
                self.ib.cancelMktData(self.contract)
                print(f"✓ Unsubscribed from {self.symbol} market data")

            self.ib.disconnect()
            self.connected = False
            print("✓ Disconnected from IBKR")

    def get_stock_price(self) -> Dict[str, Optional[float]]:
        """Get current stock bid/ask prices from subscribed data stream.

        Returns:
            Dictionary containing bid, ask, last, and mid prices

        Note:
            This method reads from the live-updating ticker object.
            Calls ib.sleep(0) to process incoming market data updates.
        """
        if not self.connected or not self.ticker:
            print("Not connected or not subscribed to market data")
            return {"bid": None, "ask": None, "last": None, "mid": None}

        try:
            import math

            def is_valid_price(price):
                """检查价格是否有效"""
                return price is not None and not math.isnan(price)

            # 处理消息队列，让 ticker 接收最新更新
            # 这很关键！不调用 sleep() 的话 ticker 不会自动更新
            self.ib.sleep(0.1)  # 100ms 处理消息

            # 从 ticker 读取最新数据
            bid = self.ticker.bid if is_valid_price(self.ticker.bid) else None
            ask = self.ticker.ask if is_valid_price(self.ticker.ask) else None
            last = self.ticker.last if is_valid_price(self.ticker.last) else None

            # Calculate mid price
            mid = None
            if bid is not None and ask is not None:
                mid = (bid + ask) / 2

            return {
                "bid": bid,
                "ask": ask,
                "last": last,
                "mid": mid
            }

        except Exception as e:
            print(f"Error reading stock price: {e}")
            return {"bid": None, "ask": None, "last": None, "mid": None}

    def get_account_id(self) -> str:
        """获取账户ID.

        Returns:
            账户ID字符串
        """
        if self.account_id:
            return self.account_id

        if self.ib and self.connected:
            accounts = self.ib.managedAccounts()
            if accounts:
                self.account_id = accounts[0]
                return self.account_id

        return None

    def get_market_session(self) -> str:
        """获取当前市场时段.

        Returns:
            'pre_market', 'regular', 'after_hours', 'closed'
        """
        try:
            import datetime
            from dateutil import tz

            eastern = tz.gettz('America/New_York')
            now = datetime.datetime.now(eastern)

            if now.weekday() >= 5:
                return 'closed'

            current_minutes = now.hour * 60 + now.minute

            if 240 <= current_minutes < 570:
                return 'pre_market'
            elif 570 <= current_minutes < 960:
                return 'regular'
            elif 960 <= current_minutes < 1200:
                return 'after_hours'
            else:
                return 'closed'

        except Exception as e:
            print(f"Error getting market session: {e}")
            return 'closed'

    def is_market_open(self) -> bool:
        """Check if market is open.

        Returns:
            True if in regular hours
        """
        return self.get_market_session() == 'regular'

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
