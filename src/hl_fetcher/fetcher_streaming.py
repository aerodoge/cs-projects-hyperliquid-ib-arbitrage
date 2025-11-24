"""Hyperliquid data fetcher with real WebSocket streaming mode."""

from typing import Dict, Optional, Any
from hyperliquid.info import Info
from hyperliquid.utils import constants
import time
import threading


class HyperliquidFetcherStreaming:
    """Fetches market data from Hyperliquid using WebSocket subscriptions."""

    def __init__(self, symbol: str = "xyz:NVDA", use_testnet: bool = False, perp_dexs: list = None):
        """Initialize the Hyperliquid data fetcher with WebSocket streaming.

        Args:
            symbol: The trading symbol to fetch data for (e.g., "xyz:NVDA")
            use_testnet: Whether to use testnet or mainnet
            perp_dexs: List of perp DEXs to initialize (e.g., ["xyz"])
        """
        self.symbol = symbol
        # Extract coin name from symbol (e.g., "xyz:NVDA" -> "NVDA")
        self.coin = symbol.split(":")[-1] if ":" in symbol else symbol

        base_url = constants.TESTNET_API_URL if use_testnet else constants.MAINNET_API_URL

        # Default to xyz DEX if not specified
        if perp_dexs is None:
            perp_dexs = ["xyz"]

        # Initialize with WebSocket enabled (skip_ws=False)
        print(f"Initializing Hyperliquid WebSocket for {symbol}...")
        self.info = Info(base_url, skip_ws=False, perp_dexs=perp_dexs)
        print(f"✓ WebSocket connection established")

        # Cache for latest data (will be updated by WebSocket callbacks)
        self._lock = threading.Lock()  # Thread safety for callbacks
        self._latest_orderbook = {"perp_bid": None, "perp_ask": None, "timestamp": None}
        self._latest_candle = {"open": None, "close": None, "timestamp": None}
        self._latest_funding_rate = None

        # Subscription IDs for cleanup
        self._l2_sub_id = None
        self._candle_sub_id = None

        # Subscribe to WebSocket data streams
        self._subscribe_to_feeds()

    def _subscribe_to_feeds(self):
        """订阅 WebSocket 数据流 - 真正的推送模式."""
        print("Setting up WebSocket subscriptions...")

        try:
            # 订阅 L2 orderbook（实时 bid/ask 更新）
            # 尝试使用完整 symbol (xyz:NVDA) 而不是简化名称 (NVDA)
            print(f"  Subscribing to L2 orderbook for {self.symbol}...")
            self._l2_sub_id = self.info.subscribe(
                {"type": "l2Book", "coin": self.symbol},  # 使用完整 symbol
                self._on_l2_book_update
            )
            print(f"  ✓ L2 orderbook subscribed (ID: {self._l2_sub_id})")

            # 订阅 1 分钟 K 线（open/close 价格）
            print(f"  Subscribing to 1m candles for {self.symbol}...")
            self._candle_sub_id = self.info.subscribe(
                {"type": "candle", "coin": self.symbol, "interval": "1m"},  # 使用完整 symbol
                self._on_candle_update
            )
            print(f"  ✓ Candle stream subscribed (ID: {self._candle_sub_id})")

            # Funding rate 使用 HTTP 获取（更新频率低，每小时一次）
            print(f"  Initializing funding rate (HTTP)...")
            self._update_funding_rate_cache()
            print(f"  ✓ Funding rate initialized")

            print("✓ All subscriptions ready")

        except Exception as e:
            import traceback
            print(f"Warning: Could not set up subscriptions: {e}")
            print(f"Error details: {traceback.format_exc()}")

    def _on_l2_book_update(self, msg: Dict[str, Any]):
        """WebSocket 回调：处理 L2 orderbook 更新.

        消息格式:
        {
            "channel": "l2Book",
            "data": {
                "coin": "NVDA",
                "levels": [[bids], [asks]],
                "time": timestamp_ms
            }
        }
        """
        try:
            data = msg["data"]
            levels = data.get("levels", [[], []])
            timestamp = data.get("time")

            perp_bid = None
            perp_ask = None

            # levels[0] = bids, levels[1] = asks
            if levels[0] and len(levels[0]) > 0:
                perp_bid = float(levels[0][0]["px"])

            if levels[1] and len(levels[1]) > 0:
                perp_ask = float(levels[1][0]["px"])

            # 线程安全更新缓存
            with self._lock:
                self._latest_orderbook = {
                    "perp_bid": perp_bid,
                    "perp_ask": perp_ask,
                    "timestamp": timestamp
                }

        except Exception as e:
            print(f"Error processing L2 book update: {e}")

    def _on_candle_update(self, msg: Dict[str, Any]):
        """WebSocket 回调：处理 K 线更新.

        消息格式:
        {
            "channel": "candle",
            "data": {
                "t": timestamp_ms,
                "T": timestamp_ms,
                "s": "NVDA",
                "i": "1m",
                "o": "140.25",
                "c": "140.30",
                "h": "140.35",
                "l": "140.20",
                "v": "1000",
                "n": 50
            }
        }
        """
        try:
            data = msg["data"]

            open_price = float(data["o"]) if "o" in data else None
            close_price = float(data["c"]) if "c" in data else None
            timestamp = data.get("t")

            # 线程安全更新缓存
            with self._lock:
                self._latest_candle = {
                    "open": open_price,
                    "close": close_price,
                    "timestamp": timestamp
                }

        except Exception as e:
            print(f"Error processing candle update: {e}")

    def _update_funding_rate_cache(self):
        """更新资金费率缓存（HTTP 请求）.

        Note: predictedFundings API 只支持加密货币，不支持 xyz DEX 的股票永续合约
              因此使用 funding_history 获取最近的 funding rate
        """
        try:
            end_time = int(time.time() * 1000)
            start_time = end_time - 86400000  # 24 hours ago

            funding_history = self.info.funding_history(
                self.symbol,
                startTime=start_time,
                endTime=end_time
            )

            if funding_history and len(funding_history) > 0:
                latest_funding = funding_history[-1]
                funding_rate_str = latest_funding.get("fundingRate")
                if funding_rate_str:
                    self._latest_funding_rate = float(funding_rate_str)
        except Exception as e:
            print(f"Error updating funding rate cache: {e}")

    def get_orderbook_prices(self) -> Dict[str, Optional[float]]:
        """Get best bid/ask prices from the orderbook.

        Returns:
            Dictionary containing perp_bid and perp_ask prices

        Note: 数据来自 WebSocket 推送，无需主动请求！
        """
        with self._lock:
            return {
                "perp_bid": self._latest_orderbook["perp_bid"],
                "perp_ask": self._latest_orderbook["perp_ask"]
            }

    def get_spot_prices(self) -> Dict[str, Optional[float]]:
        """Get spot market prices.

        Note: For xyz:NVDA, spot market doesn't exist.

        Returns:
            Dictionary containing spot_bid and spot_ask prices (None for xyz:NVDA)
        """
        return {"spot_bid": None, "spot_ask": None}

    def get_spread_prices(self) -> Dict[str, Optional[float]]:
        """Get open and close prices from recent candles.

        Returns:
            Dictionary containing open and close prices

        Note: 数据来自 WebSocket 推送，无需主动请求！
        """
        with self._lock:
            return {
                "open": self._latest_candle["open"],
                "close": self._latest_candle["close"]
            }

    def get_funding_rate(self) -> Optional[float]:
        """Get current funding rate for the perpetual contract.

        Returns:
            Current funding rate as a float

        Note: Funding rate 每小时更新一次，可以低频调用 HTTP API
        """
        # 每次调用时更新（因为外层循环间隔较长，这里不会造成频繁请求）
        self._update_funding_rate_cache()
        return self._latest_funding_rate

    def get_all_metrics(self) -> Dict[str, Any]:
        """Fetch all metrics at once.

        Returns:
            Dictionary containing all market metrics

        Note: orderbook 和 candle 数据来自 WebSocket 缓存（零 HTTP 请求）
              只有 funding_rate 会触发一次 HTTP 请求
        """
        orderbook = self.get_orderbook_prices()
        spot = self.get_spot_prices()
        spread = self.get_spread_prices()
        funding_rate = self.get_funding_rate()

        return {
            "perp_bid": orderbook["perp_bid"],
            "perp_ask": orderbook["perp_ask"],
            "spot_bid": spot["spot_bid"],
            "spot_ask": spot["spot_ask"],
            "open": spread["open"],
            "close": spread["close"],
            "funding_rate": funding_rate
        }

    def close(self):
        """关闭 WebSocket 连接并取消订阅."""
        try:
            print("Unsubscribing from WebSocket feeds...")

            # 取消 L2 orderbook 订阅
            if self._l2_sub_id is not None:
                self.info.unsubscribe(
                    {"type": "l2Book", "coin": self.symbol},  # 使用完整 symbol
                    self._l2_sub_id
                )
                print("  ✓ L2 orderbook unsubscribed")

            # 取消 candle 订阅
            if self._candle_sub_id is not None:
                self.info.unsubscribe(
                    {"type": "candle", "coin": self.symbol, "interval": "1m"},  # 使用完整 symbol
                    self._candle_sub_id
                )
                print("  ✓ Candle stream unsubscribed")

            # 断开 WebSocket 连接
            # Note: SDK 会自动管理连接，这里不需要显式断开
            print("✓ Hyperliquid WebSocket connection closed")

        except Exception as e:
            print(f"Warning: Error closing connection: {e}")

    def __del__(self):
        """析构函数，确保连接关闭."""
        self.close()
