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
        self._latest_funding_rate = None
        self._latest_mark_price = None

        # Subscription IDs for cleanup
        self._l2_sub_id = None
        self._asset_ctx_sub_id = None

        # Subscribe to WebSocket data streams
        self._subscribe_to_feeds()

    def _subscribe_to_feeds(self):
        """订阅 WebSocket 数据流 - 真正的推送模式."""
        print("Setting up WebSocket subscriptions...")

        try:
            # 订阅 L2 orderbook（实时 bid/ask 更新）
            print(f"  Subscribing to L2 orderbook for {self.symbol}...")
            self._l2_sub_id = self.info.subscribe(
                {"type": "l2Book", "coin": self.symbol},
                self._on_l2_book_update
            )
            print(f"  ✓ L2 orderbook subscribed (ID: {self._l2_sub_id})")

            # 订阅 activeAssetCtx（实时 funding rate 更新）
            print(f"  Subscribing to activeAssetCtx for {self.symbol}...")
            self._asset_ctx_sub_id = self.info.subscribe(
                {"type": "activeAssetCtx", "coin": self.symbol},
                self._on_asset_ctx_update
            )
            print(f"  ✓ activeAssetCtx subscribed (ID: {self._asset_ctx_sub_id})")

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

    def _on_asset_ctx_update(self, msg: Dict[str, Any]):
        """WebSocket 回调：处理 activeAssetCtx 更新（包含 funding rate）.

        消息格式:
        {
            "channel": "activeAssetCtx",
            "data": {
                "coin": "xyz:NVDA",
                "ctx": {
                    "funding": "0.00012345",  # 当前 funding rate
                    "openInterest": "1234567.89",
                    "prevDayPx": "180.50",
                    "dayNtlVlm": "12345678.90",
                    "premium": "0.0001",
                    "oraclePx": "180.60",
                    "markPx": "180.61",
                    "midPx": "180.615"
                }
            }
        }
        """
        try:
            data = msg["data"]
            ctx = data.get("ctx", {})

            funding_str = ctx.get("funding")
            if funding_str:
                funding_rate = float(funding_str)

                # 线程安全更新缓存
                with self._lock:
                    self._latest_funding_rate = funding_rate

        except Exception as e:
            print(f"Error processing asset ctx update: {e}")

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

    def get_funding_rate(self) -> Optional[float]:
        """Get current funding rate for the perpetual contract.

        Returns:
            Current funding rate as a float

        Note: 数据来自 activeAssetCtx WebSocket 推送，实时更新，无需 HTTP 请求
        """
        with self._lock:
            return self._latest_funding_rate

    def _update_mark_price_cache(self):
        """更新 Mark Price 缓存（HTTP 请求）.

        使用 meta_and_asset_ctxs API 获取完整的市场数据，包括：
        - markPx: Mark Price
        - midPx: Mid Price
        - funding: 资金费率
        - openInterest: 持仓量
        等
        """
        try:
            # 调用 API 获取所有资产的市场数据
            data = self.info.meta_and_asset_ctxs()

            # data[0] = universe (元数据)
            # data[1] = assetCtxs (市场数据数组)
            if not data or len(data) < 2:
                print("Warning: meta_and_asset_ctxs returned invalid data")
                return

            universe = data[0]
            asset_ctxs = data[1]

            # 找到对应 symbol 的索引
            # universe 包含所有资产的名称列表
            symbol_index = None
            for idx, asset in enumerate(universe):
                asset_name = asset.get("name", "")
                # 匹配 symbol（例如 "xyz:NVDA" 或 "NVDA"）
                if asset_name == self.symbol or asset_name == self.coin:
                    symbol_index = idx
                    break

            if symbol_index is None:
                print(f"Warning: Symbol {self.symbol} not found in universe")
                return

            # 获取对应的市场数据
            if symbol_index < len(asset_ctxs):
                ctx = asset_ctxs[symbol_index]

                # 检查 ctx 类型
                if isinstance(ctx, str):
                    # 如果是字符串，可能需要解析
                    print(f"Warning: asset_ctx is string, not dict: {ctx[:100]}")
                    return

                if not isinstance(ctx, dict):
                    print(f"Warning: asset_ctx is not a dict: {type(ctx)}")
                    return

                mark_price_str = ctx.get("markPx")

                if mark_price_str:
                    self._latest_mark_price = float(mark_price_str)

        except Exception as e:
            print(f"Error updating mark price cache: {e}")
            import traceback
            traceback.print_exc()

    def get_mark_price(self) -> Optional[float]:
        """Get current mark price for the perpetual contract.

        Returns:
            Current mark price as a float

        Note: Mark Price 从 HTTP API 获取，建议适度调用频率
        """
        # 每次调用时更新
        self._update_mark_price_cache()
        return self._latest_mark_price

    def get_all_metrics(self) -> Dict[str, Any]:
        """Fetch all metrics at once.

        Returns:
            Dictionary containing all market metrics

        Note: 所有数据均来自 WebSocket 实时推送（零 HTTP 请求）
              - orderbook: l2Book 订阅
              - funding_rate: activeAssetCtx 订阅
        """
        orderbook = self.get_orderbook_prices()
        spot = self.get_spot_prices()
        funding_rate = self.get_funding_rate()

        return {
            "perp_bid": orderbook["perp_bid"],
            "perp_ask": orderbook["perp_ask"],
            "spot_bid": spot["spot_bid"],
            "spot_ask": spot["spot_ask"],
            "funding_rate": funding_rate
        }

    def close(self):
        """关闭 WebSocket 连接并取消订阅."""
        try:
            print("Unsubscribing from WebSocket feeds...")

            # 取消 L2 orderbook 订阅
            if self._l2_sub_id is not None:
                self.info.unsubscribe(
                    {"type": "l2Book", "coin": self.symbol},
                    self._l2_sub_id
                )
                print("  ✓ L2 orderbook unsubscribed")

            # 取消 activeAssetCtx 订阅
            if self._asset_ctx_sub_id is not None:
                self.info.unsubscribe(
                    {"type": "activeAssetCtx", "coin": self.symbol},
                    self._asset_ctx_sub_id
                )
                print("  ✓ activeAssetCtx unsubscribed")

            # 断开 WebSocket 连接
            # Note: SDK 会自动管理连接，这里不需要显式断开
            print("✓ Hyperliquid WebSocket connection closed")

        except Exception as e:
            print(f"Warning: Error closing connection: {e}")

    def __del__(self):
        """析构函数，确保连接关闭."""
        self.close()
