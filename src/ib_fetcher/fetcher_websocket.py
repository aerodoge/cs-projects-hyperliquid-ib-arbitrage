"""IBKR data fetcher using Client Portal WebSocket API (via ibeam)."""

from typing import Dict, Optional
import json
import time
import ssl
import threading
import requests
from websocket import WebSocketApp


class IBKRFetcherWebSocket:
    """Fetches market data from IBKR using Client Portal WebSocket API."""

    def __init__(
        self,
        symbol: str = "NVDA",
        base_url: str = "https://localhost:5000",
        account_id: Optional[str] = None
    ):
        """Initialize the IBKR WebSocket fetcher.

        Args:
            symbol: Stock symbol (e.g., "NVDA")
            base_url: Base URL for Client Portal Gateway (default: https://localhost:5000)
            account_id: IBKR account ID (optional)
        """
        self.symbol = symbol
        self.base_url = base_url
        self.account_id = account_id

        # Market data cache
        self._latest_data = {
            "bid": None,
            "ask": None,
            "last": None,
            "timestamp": None
        }

        # Connection state
        self.connected = False
        self.conid = None  # Contract ID
        self.ws = None
        self.ws_thread = None
        self._lock = threading.Lock()
        self._heartbeat_thread = None
        self._running = False

        # Session for REST API calls
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for localhost

        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _get_contract_id(self) -> Optional[int]:
        """查询股票的 Contract ID (CONID).

        Returns:
            Contract ID or None if not found
        """
        try:
            # Search for the contract
            url = f"{self.base_url}/v1/api/iserver/secdef/search"
            params = {"symbol": self.symbol}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Find the stock contract
            for contract in data:
                if contract.get("assetClass") == "STK":
                    conid = contract.get("conid")
                    print(f"✓ Found contract ID for {self.symbol}: {conid}")
                    return conid

            print(f"✗ No stock contract found for {self.symbol}")
            return None

        except Exception as e:
            print(f"Error getting contract ID: {e}")
            return None

    def _authenticate(self) -> bool:
        """验证 session 是否有效.

        Returns:
            True if authenticated, False otherwise
        """
        try:
            url = f"{self.base_url}/v1/api/iserver/auth/status"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            authenticated = data.get("authenticated", False)

            if authenticated:
                print("✓ Session authenticated")
                return True
            else:
                print("✗ Session not authenticated - make sure ibeam is running")
                return False

        except Exception as e:
            print(f"Error checking authentication: {e}")
            return False

    def _on_message(self, ws, message):
        """WebSocket 消息回调."""
        try:
            # Parse message
            # Format can be JSON or text
            if message.startswith("{"):
                data = json.loads(message)
                self._process_market_data(data)
            else:
                # Text message (e.g., confirmation)
                if "smd" in message:
                    print(f"✓ Subscription confirmed: {message}")

        except Exception as e:
            print(f"Error processing message: {e}")

    def _process_market_data(self, data: dict):
        """处理市场数据消息.

        Args:
            data: Market data message
        """
        try:
            # Market data format: {"conidEx": "123@SMART", "84": "1.23", "86": "1.24", ...}
            # Field 84 = bid, 86 = ask, 31 = last

            if "conidEx" not in data:
                return

            with self._lock:
                # Extract bid/ask/last
                if "84" in data:  # Bid
                    self._latest_data["bid"] = float(data["84"])
                if "86" in data:  # Ask
                    self._latest_data["ask"] = float(data["86"])
                if "31" in data:  # Last
                    self._latest_data["last"] = float(data["31"])

                self._latest_data["timestamp"] = time.time()

        except Exception as e:
            print(f"Error processing market data: {e}")

    def _on_error(self, ws, error):
        """WebSocket 错误回调."""
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket 关闭回调."""
        print(f"✗ WebSocket connection closed")
        self.connected = False

    def _on_open(self, ws):
        """WebSocket 打开回调."""
        print("✓ WebSocket connection opened")
        self.connected = True

        # Subscribe to market data
        if self.conid:
            # Format: smd+CONID+{"fields":["84","86","31"]}
            # 84=bid, 86=ask, 31=last
            subscribe_msg = f'smd+{self.conid}+{{"fields":["84","86","31"]}}'
            ws.send(subscribe_msg)
            print(f"✓ Subscribed to {self.symbol} market data")

    def _heartbeat_loop(self):
        """心跳循环（每10秒发送一次）."""
        while self._running and self.ws:
            try:
                if self.connected:
                    # Send heartbeat
                    self.ws.send("hb")
                time.sleep(10)
            except Exception as e:
                print(f"Error sending heartbeat: {e}")
                break

    def connect(self) -> bool:
        """连接到 IBKR Client Portal WebSocket.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # 1. Check authentication
            if not self._authenticate():
                return False

            # 2. Get contract ID
            self.conid = self._get_contract_id()
            if not self.conid:
                return False

            # 3. Establish WebSocket connection
            # Convert base_url to WebSocket URL (https -> wss, http -> ws)
            ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
            ws_url = f"{ws_url}/v1/api/ws"

            print(f"Connecting to WebSocket: {ws_url}")

            self.ws = WebSocketApp(
                ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )

            # Run WebSocket in separate thread
            self._running = True
            self.ws_thread = threading.Thread(
                target=self.ws.run_forever,
                kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}
            )
            self.ws_thread.daemon = True
            self.ws_thread.start()

            # Wait for connection
            for _ in range(50):  # Wait up to 5 seconds
                if self.connected:
                    break
                time.sleep(0.1)

            if not self.connected:
                print("✗ WebSocket connection timeout")
                return False

            # 4. Start heartbeat thread
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
            self._heartbeat_thread.daemon = True
            self._heartbeat_thread.start()

            # 5. Wait for initial data
            print("Waiting for initial market data...")
            for _ in range(50):  # Wait up to 5 seconds
                with self._lock:
                    if self._latest_data["bid"] is not None:
                        print("✓ Initial market data received")
                        return True
                time.sleep(0.1)

            print("Warning: No initial market data received (might be market closed)")
            return True

        except Exception as e:
            print(f"Error connecting to WebSocket: {e}")
            return False

    def disconnect(self):
        """断开 WebSocket 连接."""
        try:
            self._running = False

            if self.conid and self.connected:
                # Unsubscribe
                unsubscribe_msg = f'umd+{self.conid}+{{}}'
                self.ws.send(unsubscribe_msg)
                print(f"✓ Unsubscribed from {self.symbol} market data")

            if self.ws:
                self.ws.close()

            if self.ws_thread:
                self.ws_thread.join(timeout=2)

            if self._heartbeat_thread:
                self._heartbeat_thread.join(timeout=2)

            print("✓ Disconnected from IBKR WebSocket")

        except Exception as e:
            print(f"Error disconnecting: {e}")

    def get_stock_price(self) -> Dict[str, Optional[float]]:
        """获取当前股票价格.

        Returns:
            Dictionary containing bid, ask, last, and mid prices
        """
        with self._lock:
            bid = self._latest_data["bid"]
            ask = self._latest_data["ask"]
            last = self._latest_data["last"]

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

    def get_account_id(self) -> Optional[str]:
        """获取账户 ID.

        Returns:
            Account ID or None
        """
        try:
            url = f"{self.base_url}/v1/api/portfolio/accounts"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            accounts = response.json()
            if accounts and len(accounts) > 0:
                account = accounts[0].get("accountId")
                return account

            return None

        except Exception as e:
            print(f"Error getting account ID: {e}")
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
