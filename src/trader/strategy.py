"""Arbitrage strategy logic for Hyperliquid-IB trading."""

from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import time

from .config import StrategyConfig, DEFAULT_CONFIG


class SignalType(Enum):
    """Trading signal types."""
    NONE = "none"              # 无信号，不交易
    OPEN_LONG_SPOT_SHORT_PERP = "open_long_spot_short_perp"  # 情况1：买现货+开空永续
    CLOSE_POSITION = "close_position"  # 平仓信号


@dataclass
class MarketData:
    """市场数据结构."""
    # Hyperliquid 永续合约数据
    perp_bid: Optional[float] = None
    perp_ask: Optional[float] = None
    mark_price: Optional[float] = None
    funding_rate: Optional[float] = None

    # IB 现货数据
    spot_bid: Optional[float] = None
    spot_ask: Optional[float] = None

    # 数据时间戳
    timestamp: Optional[float] = None


@dataclass
class SpreadAnalysis:
    """价差分析结果."""
    # 价差（百分比）
    spread: Optional[float] = None

    # 用于计算的价格
    ib_buy_price: Optional[float] = None   # IB 买入成本（spot_ask）
    hl_sell_price: Optional[float] = None  # HL 开空成交价（perp_bid）

    # 资金费率
    funding_rate: Optional[float] = None

    # 信号类型
    signal: SignalType = SignalType.NONE

    # 信号原因（便于调试）
    reason: str = ""

    # 数据有效性
    is_valid: bool = False


class ArbitrageStrategy:
    """套利策略类."""

    def __init__(self, config: StrategyConfig = None):
        """初始化策略.

        Args:
            config: 策略配置，如果不提供则使用默认配置
        """
        self.config = config or DEFAULT_CONFIG

    def calculate_spread(self, market_data: MarketData) -> SpreadAnalysis:
        """计算开仓价差并分析.

        Args:
            market_data: 市场数据

        Returns:
            SpreadAnalysis: 价差分析结果

        计算逻辑：
            情况1：正价差套利（买现货+开空永续）
            - ib_buy_price = spot_ask（IB 买入成本）
            - hl_sell_price = perp_bid（HL 开空成交价）
            - spread = (hl_sell_price / ib_buy_price) - 1
        """
        analysis = SpreadAnalysis()

        # 1. 数据有效性检查
        if not self._validate_market_data(market_data):
            analysis.reason = "Invalid or incomplete market data"
            return analysis

        # 2. 提取价格
        ib_buy_price = market_data.spot_ask    # IB 买入价（ask）
        hl_sell_price = market_data.perp_bid   # HL 开空价（bid）
        funding_rate = market_data.funding_rate

        # 3. 计算价差
        spread = (hl_sell_price / ib_buy_price) - 1

        # 4. 填充分析结果
        analysis.spread = spread
        analysis.ib_buy_price = ib_buy_price
        analysis.hl_sell_price = hl_sell_price
        analysis.funding_rate = funding_rate
        analysis.is_valid = True

        return analysis

    def calculate_close_spread(self, market_data: MarketData) -> SpreadAnalysis:
        """计算平仓价差.

        Args:
            market_data: 市场数据

        Returns:
            SpreadAnalysis: 价差分析结果

        计算逻辑：
            平仓时（卖现货+平空永续）：
            - ib_sell_price = spot_bid（IB 卖出能拿到的价格）
            - hl_buy_price = perp_ask（HL 平空需要支付的价格）
            - spread = (hl_buy_price / ib_sell_price) - 1

            注意：平仓spread通常是负数（因为bid<ask），这是正常的
        """
        analysis = SpreadAnalysis()

        # 1. 数据有效性检查（平仓时也需要spot_bid和perp_ask）
        if not market_data.spot_bid or market_data.spot_bid <= 0:
            analysis.reason = "Invalid spot_bid"
            return analysis

        if not market_data.perp_ask or market_data.perp_ask <= 0:
            analysis.reason = "Invalid perp_ask"
            return analysis

        if market_data.funding_rate is None:
            analysis.reason = "Missing funding_rate"
            return analysis

        # 2. 提取平仓价格
        ib_sell_price = market_data.spot_bid   # IB 卖出价（bid）
        hl_buy_price = market_data.perp_ask    # HL 平空价（ask）
        funding_rate = market_data.funding_rate

        # 3. 计算平仓价差
        spread = (hl_buy_price / ib_sell_price) - 1

        # 4. 填充分析结果（注意字段含义在平仓时不同）
        analysis.spread = spread
        analysis.ib_buy_price = ib_sell_price   # 实际是卖出价
        analysis.hl_sell_price = hl_buy_price  # 实际是买入价
        analysis.funding_rate = funding_rate
        analysis.is_valid = True

        return analysis

    def get_open_signal(self, analysis: SpreadAnalysis) -> Tuple[SignalType, str]:
        """判断是否有开仓信号.

        Args:
            analysis: 价差分析结果

        Returns:
            (信号类型, 原因说明)

        开仓条件（情况1）：
            1. spread > open_spread_threshold（价差足够大）
            2. funding_rate > min_funding_rate（资金费率为正）
        """
        if not analysis.is_valid:
            return SignalType.NONE, "Invalid spread analysis"

        spread = analysis.spread
        funding_rate = analysis.funding_rate

        # 检查价差是否足够大
        if spread <= self.config.open_spread_threshold:
            return SignalType.NONE, f"Spread {spread*100:.4f}% < threshold {self.config.open_spread_threshold*100:.4f}%"

        # 检查资金费率是否为正
        if funding_rate is None or funding_rate <= self.config.min_funding_rate:
            return SignalType.NONE, f"Funding rate {funding_rate*100:.4f}% <= threshold {self.config.min_funding_rate*100:.4f}%"

        # 满足开仓条件
        reason = (
            f"Spread {spread*100:.4f}% > {self.config.open_spread_threshold*100:.4f}%, "
            f"Funding {funding_rate*100:.4f}% > {self.config.min_funding_rate*100:.4f}%"
        )
        return SignalType.OPEN_LONG_SPOT_SHORT_PERP, reason

    def get_close_signal(self, analysis: SpreadAnalysis, entry_spread: float) -> Tuple[SignalType, str]:
        """判断是否有平仓信号.

        Args:
            analysis: 当前价差分析结果
            entry_spread: 开仓时的价差

        Returns:
            (信号类型, 原因说明)

        平仓条件：
            1. 价差收敛：spread < close_spread_threshold（获利平仓）
            2. 价差反转：spread < reverse_spread_threshold（止损平仓）
            3. 资金费率反转：funding_rate < reverse_funding_threshold（可选）
        """
        if not analysis.is_valid:
            return SignalType.NONE, "Invalid spread analysis"

        spread = analysis.spread
        funding_rate = analysis.funding_rate

        # 1. 价差收敛（获利平仓）
        if spread < self.config.close_spread_threshold:
            reason = f"Spread converged {spread*100:.4f}% < {self.config.close_spread_threshold*100:.4f}% (profit taking)"
            return SignalType.CLOSE_POSITION, reason

        # 2. 价差反转（止损平仓）
        if spread < self.config.reverse_spread_threshold:
            reason = f"Spread reversed {spread*100:.4f}% < {self.config.reverse_spread_threshold*100:.4f}% (stop loss)"
            return SignalType.CLOSE_POSITION, reason

        # 3. 资金费率反转（可选）
        if (self.config.reverse_funding_threshold is not None and
            funding_rate is not None and
            funding_rate < self.config.reverse_funding_threshold):
            reason = f"Funding rate reversed {funding_rate*100:.4f}% < {self.config.reverse_funding_threshold*100:.4f}%"
            return SignalType.CLOSE_POSITION, reason

        return SignalType.NONE, "No close signal"

    def _validate_market_data(self, market_data: MarketData) -> bool:
        """验证市场数据有效性.

        Args:
            market_data: 市场数据

        Returns:
            bool: 数据是否有效
        """
        # 检查必需的价格数据
        if market_data.spot_ask is None or market_data.spot_ask <= 0:
            return False

        if market_data.perp_bid is None or market_data.perp_bid <= 0:
            return False

        if market_data.funding_rate is None:
            return False

        # 检查数据时效性（如果提供了时间戳）
        if market_data.timestamp is not None:
            age = time.time() - market_data.timestamp
            if age > self.config.max_data_age:
                return False

        # 检查价格合理性（bid < ask）
        if market_data.spot_bid and market_data.spot_ask:
            if market_data.spot_bid >= market_data.spot_ask:
                return False

        if market_data.perp_bid and market_data.perp_ask:
            if market_data.perp_bid >= market_data.perp_ask:
                return False

        return True

    def format_analysis(self, analysis: SpreadAnalysis) -> str:
        """格式化价差分析结果为可读字符串.

        Args:
            analysis: 价差分析结果

        Returns:
            str: 格式化的分析结果
        """
        if not analysis.is_valid:
            return f"Invalid analysis: {analysis.reason}"

        lines = [
            "=== Spread Analysis ===",
            f"IB Buy Price (spot ask):  ${analysis.ib_buy_price:.2f}",
            f"HL Sell Price (perp bid): ${analysis.hl_sell_price:.2f}",
            f"Spread: {analysis.spread*100:+.4f}%",
            f"Funding Rate: {analysis.funding_rate*100:+.4f}%",
            f"Signal: {analysis.signal.value}",
        ]

        if analysis.reason:
            lines.append(f"Reason: {analysis.reason}")

        return "\n".join(lines)
