"""Hyperliquid perpetual contract trading interface."""

from typing import Optional, Dict
import time


class HLTrader:
    """Hyperliquid 永续合约交易接口."""

    def __init__(
        self,
        private_key: str,
        use_testnet: bool = False,
        perp_dexs: list = None
    ):
        """初始化 Hyperliquid 交易接口.

        Args:
            private_key: 私钥（0x开头的十六进制字符串）
            use_testnet: 是否使用测试网
            perp_dexs: Perp DEX 列表（例如 ["xyz"]）
        """
        self.private_key = private_key
        self.use_testnet = use_testnet
        self.perp_dexs = perp_dexs or ["xyz"]

        self.exchange = None
        self.info = None
        self.connected = False

    def connect(self) -> bool:
        """连接到 Hyperliquid.

        Returns:
            True if successful, False otherwise
        """
        try:
            from hyperliquid.exchange import Exchange
            from hyperliquid.info import Info
            from hyperliquid.utils import constants

            base_url = constants.TESTNET_API_URL if self.use_testnet else constants.MAINNET_API_URL

            # 初始化 Exchange（用于交易）
            self.exchange = Exchange(
                self.private_key,
                base_url=base_url,
                perp_dexs=self.perp_dexs
            )

            # 初始化 Info（用于查询）
            self.info = Info(base_url, skip_ws=True, perp_dexs=self.perp_dexs)

            self.connected = True
            network = "TESTNET" if self.use_testnet else "MAINNET"
            print(f"✓ Hyperliquid Trader connected ({network})")
            return True

        except ImportError:
            print("Error: hyperliquid-python-sdk not installed")
            return False
        except Exception as e:
            print(f"Error connecting Hyperliquid Trader: {e}")
            return False

    def open_short(
        self,
        symbol: str,
        quantity: float,
        limit_price: Optional[float] = None,
        reduce_only: bool = False
    ) -> Dict:
        """开空永续合约.

        Args:
            symbol: 交易对符号（例如 "xyz:NVDA"）
            quantity: 数量（正数）
            limit_price: 限价（None = 市价单）
            reduce_only: 是否仅减仓

        Returns:
            订单结果字典
        """
        if not self.connected:
            return {
                "success": False,
                "message": "Not connected to Hyperliquid"
            }

        try:
            # 开空 = 卖出（负数量）
            size = -abs(quantity)

            if limit_price is None:
                # 市价单
                print(f"📤 Placing MARKET SHORT order: {abs(size)} {symbol}")
                order_result = self.exchange.market_open(
                    symbol,
                    is_buy=False,
                    sz=abs(size),
                    reduce_only=reduce_only
                )
            else:
                # 限价单
                print(f"📤 Placing LIMIT SHORT order: {abs(size)} {symbol} @ ${limit_price}")
                order_result = self.exchange.limit_order(
                    symbol,
                    is_buy=False,
                    sz=abs(size),
                    limit_px=limit_price,
                    reduce_only=reduce_only
                )

            # 解析结果
            if order_result and order_result.get("status") == "ok":
                response = order_result.get("response", {})
                data = response.get("data", {}) if isinstance(response, dict) else {}

                statuses = data.get("statuses", []) if isinstance(data, dict) else []

                if statuses and len(statuses) > 0:
                    status = statuses[0]
                    filled = status.get("filled", {})

                    result = {
                        "success": True,
                        "order_id": status.get("oid"),
                        "filled_qty": abs(float(filled.get("totalSz", 0))),
                        "avg_price": float(filled.get("avgPx", 0)) if filled.get("avgPx") else None,
                        "message": "Order placed successfully"
                    }

                    if result["filled_qty"] > 0:
                        print(f"✅ Order FILLED: {result['filled_qty']} @ ${result['avg_price']:.2f}")
                    else:
                        print(f"⏳ Order SUBMITTED (waiting for fill)")

                    return result

            # 失败情况
            print(f"❌ Order failed: {order_result}")
            return {
                "success": False,
                "message": str(order_result)
            }

        except Exception as e:
            print(f"Error placing short order: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": str(e)
            }

    def close_short(
        self,
        symbol: str,
        quantity: float,
        limit_price: Optional[float] = None
    ) -> Dict:
        """平空永续合约（买入平仓）.

        Args:
            symbol: 交易对符号
            quantity: 数量（正数）
            limit_price: 限价（None = 市价单）

        Returns:
            订单结果字典
        """
        if not self.connected:
            return {
                "success": False,
                "message": "Not connected to Hyperliquid"
            }

        try:
            # 平空 = 买入（正数量）
            size = abs(quantity)

            if limit_price is None:
                # 市价单 - 使用 market_open 配合 reduce_only 来指定数量
                print(f"📤 Placing MARKET CLOSE order: {size} {symbol}")
                order_result = self.exchange.market_open(
                    symbol,
                    is_buy=True,
                    sz=size,
                    reduce_only=True
                )
            else:
                # 限价单（使用 reduce_only）
                print(f"📤 Placing LIMIT CLOSE order: {size} {symbol} @ ${limit_price}")
                order_result = self.exchange.limit_order(
                    symbol,
                    is_buy=True,
                    sz=size,
                    limit_px=limit_price,
                    reduce_only=True
                )

            # 解析结果（同 open_short）
            if order_result and order_result.get("status") == "ok":
                response = order_result.get("response", {})
                data = response.get("data", {}) if isinstance(response, dict) else {}
                statuses = data.get("statuses", []) if isinstance(data, dict) else []

                if statuses and len(statuses) > 0:
                    status = statuses[0]
                    filled = status.get("filled", {})

                    result = {
                        "success": True,
                        "order_id": status.get("oid"),
                        "filled_qty": abs(float(filled.get("totalSz", 0))),
                        "avg_price": float(filled.get("avgPx", 0)) if filled.get("avgPx") else None,
                        "message": "Order placed successfully"
                    }

                    if result["filled_qty"] > 0:
                        print(f"✅ Order FILLED: {result['filled_qty']} @ ${result['avg_price']:.2f}")
                    else:
                        print(f"⏳ Order SUBMITTED (waiting for fill)")

                    return result

            print(f"❌ Order failed: {order_result}")
            return {
                "success": False,
                "message": str(order_result)
            }

        except Exception as e:
            print(f"Error closing short position: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": str(e)
            }

    def get_position(self, symbol: str) -> Optional[float]:
        """获取持仓数量.

        Args:
            symbol: 交易对符号

        Returns:
            持仓数量（正数=多头，负数=空头，None=错误）
        """
        if not self.connected:
            return None

        try:
            # 获取用户地址
            from eth_account import Account
            address = Account.from_key(self.private_key).address

            # 查询持仓
            user_state = self.info.user_state(address)

            if not user_state or "assetPositions" not in user_state:
                return 0.0

            # 查找对应 symbol 的持仓
            for pos in user_state["assetPositions"]:
                position = pos.get("position", {})
                if position.get("coin") == symbol:
                    szi = position.get("szi")
                    if szi:
                        return float(szi)

            return 0.0  # 无持仓

        except Exception as e:
            print(f"Error getting position: {e}")
            return None

    def get_account_value(self) -> Optional[float]:
        """获取账户总价值.

        Returns:
            账户价值（USD）
        """
        if not self.connected:
            return None

        try:
            from eth_account import Account
            address = Account.from_key(self.private_key).address

            user_state = self.info.user_state(address)

            if not user_state:
                return None

            # 账户价值
            account_value = user_state.get("marginSummary", {}).get("accountValue")
            if account_value:
                return float(account_value)

            return None

        except Exception as e:
            print(f"Error getting account value: {e}")
            return None
