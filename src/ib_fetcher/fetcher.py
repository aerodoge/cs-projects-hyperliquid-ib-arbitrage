"""Interactive Brokers data fetcher for NVDA stock."""

from typing import Dict, Optional
import time


class IBKRFetcher:
    """Fetches real stock price data from Interactive Brokers."""

    def __init__(self, symbol: str = "NVDA", host: str = "127.0.0.1", port: int = 7497, client_id: int = 1, account_id: str = None):
        """Initialize the IBKR data fetcher.

        Args:
            symbol: Stock symbol (e.g., "NVDA")
            host: IB Gateway/TWS host
            port: IB Gateway/TWS port (7497 for TWS paper, 7496 for TWS live, 4002 for Gateway paper, 4001 for Gateway live)
            client_id: Unique client ID
            account_id: IBKR account ID (e.g., "DU1234567" for paper, "U1234567" for live)
                       If None, will use the first available account
        """
        self.symbol = symbol
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account_id = account_id
        self.ib = None
        self.connected = False

    def connect(self) -> bool:
        """Connect to Interactive Brokers.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            from ib_insync import IB, Stock

            self.ib = IB()
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            print(f"✓ Connected to IBKR at {self.host}:{self.port}")
            return True
        except ImportError:
            print("Error: ib_insync not installed. Install with: pip install ib_insync")
            return False
        except Exception as e:
            print(f"Error connecting to IBKR: {e}")
            print("Make sure IB Gateway or TWS is running and API is enabled.")
            return False

    def disconnect(self):
        """Disconnect from Interactive Brokers."""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            print("✓ Disconnected from IBKR")

    def get_account_id(self) -> str:
        """获取账户ID（自动检测或使用配置的账户ID）

        Returns:
            账户ID字符串，如果未连接或无账户则返回 None
        """
        # 如果已配置账户ID，直接返回
        if self.account_id:
            return self.account_id

        # 如果未配置，自动获取第一个可用账户
        if self.ib and self.connected:
            accounts = self.ib.managedAccounts()
            if accounts:
                # 自动使用第一个账户并保存
                self.account_id = accounts[0]
                return self.account_id

        return None

    def get_all_accounts(self) -> list:
        """获取所有可用账户列表

        Returns:
            账户ID列表
        """
        if not self.connected:
            if not self.connect():
                return []

        try:
            return self.ib.managedAccounts()
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []

    def get_stock_price(self) -> Dict[str, Optional[float]]:
        """Get current stock bid/ask prices.

        Returns:
            Dictionary containing bid, ask, and last prices
        """
        if not self.connected:
            if not self.connect():
                return {"bid": None, "ask": None, "last": None, "mid": None}

        try:
            from ib_insync import Stock

            # Create stock contract
            contract = Stock(self.symbol, 'SMART', 'USD')

            # Request market data
            self.ib.qualifyContracts(contract)
            ticker = self.ib.reqMktData(contract, '', False, False)

            # Wait for data
            timeout = 10  # seconds
            start_time = time.time()
            while (not ticker.bid or not ticker.ask) and (time.time() - start_time < timeout):
                self.ib.sleep(0.1)

            # Cancel market data subscription
            self.ib.cancelMktData(contract)

            # Calculate mid price
            mid = None
            if ticker.bid and ticker.ask:
                mid = (ticker.bid + ticker.ask) / 2

            return {
                "bid": ticker.bid if ticker.bid else None,
                "ask": ticker.ask if ticker.ask else None,
                "last": ticker.last if ticker.last else None,
                "mid": mid
            }

        except Exception as e:
            print(f"Error fetching stock price: {e}")
            return {"bid": None, "ask": None, "last": None, "mid": None}

    def get_market_snapshot(self) -> Dict[str, any]:
        """Get comprehensive market snapshot.

        Returns:
            Dictionary containing bid, ask, last, volume, open, high, low, close
        """
        if not self.connected:
            if not self.connect():
                return {
                    "bid": None,
                    "ask": None,
                    "last": None,
                    "mid": None,
                    "volume": None,
                    "open": None,
                    "high": None,
                    "low": None,
                    "close": None
                }

        try:
            from ib_insync import Stock

            # Create stock contract
            contract = Stock(self.symbol, 'SMART', 'USD')

            # Request market data
            self.ib.qualifyContracts(contract)
            ticker = self.ib.reqMktData(contract, '', False, False)

            # Wait for data
            timeout = 10  # seconds
            start_time = time.time()
            while (not ticker.bid or not ticker.ask) and (time.time() - start_time < timeout):
                self.ib.sleep(0.1)

            # Cancel market data subscription
            self.ib.cancelMktData(contract)

            # Calculate mid price
            mid = None
            if ticker.bid and ticker.ask:
                mid = (ticker.bid + ticker.ask) / 2

            return {
                "bid": ticker.bid if ticker.bid else None,
                "ask": ticker.ask if ticker.ask else None,
                "last": ticker.last if ticker.last else None,
                "mid": mid,
                "volume": ticker.volume if ticker.volume else None,
                "open": ticker.open if ticker.open else None,
                "high": ticker.high if ticker.high else None,
                "low": ticker.low if ticker.low else None,
                "close": ticker.close if ticker.close else None
            }

        except Exception as e:
            print(f"Error fetching market snapshot: {e}")
            return {
                "bid": None,
                "ask": None,
                "last": None,
                "mid": None,
                "volume": None,
                "open": None,
                "high": None,
                "low": None,
                "close": None
            }

    def get_market_session(self) -> str:
        """获取当前市场时段（自动处理夏令时和冬令时）

        Returns:
            'pre_market': 盘前交易 (4:00 AM - 9:30 AM ET)
            'regular': 常规交易 (9:30 AM - 4:00 PM ET)
            'after_hours': 盘后交易 (4:00 PM - 8:00 PM ET)
            'closed': 休市

        Note:
            时区转换会自动处理夏令时（DST）和标准时间
            - 夏令时: 3月第二个周日 - 11月第一个周日 (UTC-4)
            - 标准时间: 11月第一个周日 - 3月第二个周日 (UTC-5)
        """
        try:
            import datetime
            from dateutil import tz

            # 获取美国东部时间（自动处理夏令时）
            eastern = tz.gettz('America/New_York')
            now = datetime.datetime.now(eastern)

            # 周末休市
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return 'closed'

            # 转换为分钟便于比较
            current_minutes = now.hour * 60 + now.minute

            # 时段定义（美国东部时间）
            # 4:00 AM = 240 分钟
            # 9:30 AM = 570 分钟
            # 4:00 PM = 960 分钟
            # 8:00 PM = 1200 分钟

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
        """Check if the stock market is currently open (regular hours only).

        Returns:
            True if market is in regular trading hours, False otherwise

        Note:
            Automatically handles daylight saving time (DST) and standard time
        """
        return self.get_market_session() == 'regular'

    def is_regular_hours(self) -> bool:
        """检查是否在常规交易时段（9:30 AM - 4:00 PM ET）

        Returns:
            True if in regular hours, False otherwise
        """
        return self.get_market_session() == 'regular'

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
