"""Trade executor - coordinates IB and Hyperliquid trading."""

from typing import Optional, Dict
import time
import uuid

from .ib_trader import IBTrader
from .hl_trader import HLTrader
from .position_manager import PositionManager, Position, PositionStatus
from .strategy import SpreadAnalysis


class TradeExecutor:
    """交易执行器 - 协调 IB 和 Hyperliquid 的双边交易."""

    def __init__(
        self,
        ib_trader: IBTrader,
        hl_trader: HLTrader,
        position_manager: PositionManager,
        symbol: str,
        hl_symbol: str
    ):
        """初始化交易执行器.

        Args:
            ib_trader: IB 交易接口
            hl_trader: Hyperliquid 交易接口
            position_manager: 仓位管理器
            symbol: 股票代码（如 "NVDA"）
            hl_symbol: Hyperliquid 符号（如 "xyz:NVDA"）
        """
        self.ib_trader = ib_trader
        self.hl_trader = hl_trader
        self.position_manager = position_manager
        self.symbol = symbol
        self.hl_symbol = hl_symbol

    def open_arbitrage_position(
        self,
        quantity: int,
        analysis: SpreadAnalysis,
        use_limit_orders: bool = False
    ) -> Optional[str]:
        """开仓套利仓位（买入现货 + 开空永续）.

        Args:
            quantity: 数量
            analysis: 价差分析结果
            use_limit_orders: 是否使用限价单（False=市价单）

        Returns:
            仓位ID（成功）或 None（失败）
        """
        print("\n" + "=" * 60)
        print("开仓套利仓位")
        print("=" * 60)
        print(f"Symbol: {self.symbol} / {self.hl_symbol}")
        print(f"Quantity: {quantity}")
        print(f"Entry Spread: {analysis.spread*100:.4f}%")
        print(f"IB Buy Price (spot ask): ${analysis.ib_buy_price:.2f}")
        print(f"HL Sell Price (perp bid): ${analysis.hl_sell_price:.2f}")
        print(f"Funding Rate: {analysis.funding_rate*100:.4f}%")
        print("=" * 60)

        # 生成仓位ID
        position_id = f"pos_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # 步骤1：IB 买入现货
        print("\n[1/2] Buying spot on IB...")
        ib_limit_price = analysis.ib_buy_price if use_limit_orders else None

        ib_result = self.ib_trader.buy_stock(
            self.symbol,
            quantity,
            limit_price=ib_limit_price
        )

        if not ib_result["success"]:
            print(f"❌ IB order failed: {ib_result['message']}")
            return None

        print(f"✅ IB order filled: {ib_result['filled_qty']} @ ${ib_result['avg_price']:.2f}")

        # 步骤2：Hyperliquid 开空永续
        print("\n[2/2] Opening short on Hyperliquid...")
        hl_limit_price = analysis.hl_sell_price if use_limit_orders else None

        hl_result = self.hl_trader.open_short(
            self.hl_symbol,
            quantity,
            limit_price=hl_limit_price
        )

        if not hl_result["success"]:
            print(f"❌ Hyperliquid order failed: {hl_result['message']}")
            print(f"⚠️  WARNING: IB position opened but HL failed!")
            print(f"🔄 Attempting to rollback IB position...")

            # 自动回滚：卖出刚才买入的股票
            rollback_result = self.ib_trader.sell_stock(
                self.symbol,
                int(ib_result["filled_qty"]),
                limit_price=None  # 使用市价单快速平仓
            )

            if rollback_result["success"]:
                print(f"✅ IB position rolled back successfully")
            else:
                print(f"❌ CRITICAL: Rollback failed! Manual intervention required!")
                print(f"   Need to manually sell {ib_result['filled_qty']} shares of {self.symbol}")

            return None

        print(f"✅ HL order filled: {hl_result['filled_qty']} @ ${hl_result['avg_price']:.2f}")

        # 步骤3：记录仓位
        position = Position(
            position_id=position_id,
            symbol=self.symbol,
            hl_symbol=self.hl_symbol,
            quantity=quantity,
            entry_time=time.time(),
            entry_spread=analysis.spread,
            entry_funding_rate=analysis.funding_rate,
            ib_entry_price=ib_result["avg_price"],
            ib_order_id=ib_result.get("order_id"),
            hl_entry_price=hl_result["avg_price"],
            hl_order_id=hl_result.get("order_id"),
            status=PositionStatus.OPEN,
            notes=f"Opened at spread {analysis.spread*100:.4f}%"
        )

        self.position_manager.add_position(position)

        print("\n" + "=" * 60)
        print(f"✅ Arbitrage position opened: {position_id}")
        print("=" * 60)

        return position_id

    def close_arbitrage_position(
        self,
        position_id: str,
        market_data,  # MarketData object
        use_limit_orders: bool = False
    ) -> bool:
        """平仓套利仓位（卖出现货 + 平空永续）.

        Args:
            position_id: 仓位ID
            market_data: 市场数据（需要包含 spot_bid 和 perp_ask）
            use_limit_orders: 是否使用限价单

        Returns:
            True if successful, False otherwise
        """
        from .strategy import ArbitrageStrategy

        position = self.position_manager.get_position(position_id)
        if not position:
            print(f"❌ Position {position_id} not found")
            return False

        if position.status != PositionStatus.OPEN:
            print(f"❌ Position {position_id} is not open")
            return False

        # 计算平仓价差
        strategy = ArbitrageStrategy()
        close_analysis = strategy.calculate_close_spread(market_data)

        if not close_analysis.is_valid:
            print(f"❌ Invalid market data for closing: {close_analysis.reason}")
            return False

        print("\n" + "=" * 60)
        print("平仓套利仓位")
        print("=" * 60)
        print(f"Position ID: {position_id}")
        print(f"Symbol: {self.symbol} / {self.hl_symbol}")
        print(f"Quantity: {position.quantity}")
        print(f"Entry Spread: {position.entry_spread*100:.4f}%")
        print(f"Exit Spread: {close_analysis.spread*100:.4f}%")
        print("=" * 60)

        # 获取退出价格（平仓时用 bid/ask 的另一边）
        # 平仓时：卖出现货用 spot_bid，平空永续用 perp_ask
        ib_exit_price = market_data.spot_bid   # IB 卖出价
        hl_exit_price = market_data.perp_ask   # HL 平空（买入）价

        # 步骤1：IB 卖出现货
        print("\n[1/2] Selling spot on IB...")
        ib_limit_price = ib_exit_price if use_limit_orders else None

        ib_result = self.ib_trader.sell_stock(
            self.symbol,
            int(position.quantity),
            limit_price=ib_limit_price
        )

        if not ib_result["success"]:
            print(f"❌ IB sell order failed: {ib_result['message']}")
            return False

        print(f"✅ IB sell filled: {ib_result['filled_qty']} @ ${ib_result['avg_price']:.2f}")

        # 步骤2：Hyperliquid 平空
        print("\n[2/2] Closing short on Hyperliquid...")
        hl_limit_price = hl_exit_price if use_limit_orders else None

        hl_result = self.hl_trader.close_short(
            self.hl_symbol,
            position.quantity,
            limit_price=hl_limit_price
        )

        if not hl_result["success"]:
            print(f"❌ Hyperliquid close failed: {hl_result['message']}")
            print(f"⚠️  WARNING: IB position closed but HL failed!")
            print(f"⚠️  Manual intervention required")
            return False

        print(f"✅ HL close filled: {hl_result['filled_qty']} @ ${hl_result['avg_price']:.2f}")

        # 步骤3：更新仓位状态
        self.position_manager.close_position(
            position_id,
            ib_exit_price=ib_result["avg_price"],
            hl_exit_price=hl_result["avg_price"],
            exit_spread=close_analysis.spread
        )

        # 计算盈亏
        pnl = position.calculate_pnl()

        print("\n" + "=" * 60)
        print(f"✅ Arbitrage position closed: {position_id}")
        if pnl is not None:
            print(f"PnL: ${pnl:.2f}")
        print("=" * 60)

        return True

    def check_and_execute_open_signal(
        self,
        quantity: int,
        analysis: SpreadAnalysis,
        max_positions: int = 1
    ) -> Optional[str]:
        """检查并执行开仓信号.

        Args:
            quantity: 开仓数量
            analysis: 价差分析
            max_positions: 最大持仓数

        Returns:
            仓位ID（开仓成功）或 None
        """
        # 检查当前持仓数
        open_positions = self.position_manager.get_open_positions()
        if len(open_positions) >= max_positions:
            print(f"⚠️  Max positions reached: {len(open_positions)}/{max_positions}")
            return None

        # 执行开仓
        return self.open_arbitrage_position(quantity, analysis)

    def check_and_execute_close_signal(
        self,
        market_data,  # MarketData object
        entry_spread: float
    ) -> bool:
        """检查并执行平仓信号.

        Args:
            market_data: 当前市场数据
            entry_spread: 开仓时的价差

        Returns:
            True if any position closed, False otherwise
        """
        open_positions = self.position_manager.get_open_positions()

        if not open_positions:
            return False

        closed_any = False

        # 检查每个开仓仓位
        for position in open_positions:
            # 这里可以添加平仓条件判断
            # 简化版：直接尝试平仓
            success = self.close_arbitrage_position(position.position_id, market_data)
            if success:
                closed_any = True

        return closed_any
