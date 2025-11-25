"""Strategy configuration for Hyperliquid-IB arbitrage."""

from dataclasses import dataclass


@dataclass
class StrategyConfig:
    """Configuration for arbitrage strategy."""

    # ==================== 开仓条件参数 ====================

    # 价差阈值（百分比）
    # 计算方式：spread = (hl_sell_price / ib_buy_price) - 1
    # 例如：0.001 = 0.1%，表示永续卖价比现货买价高 0.1% 以上才开仓
    open_spread_threshold: float = 0.001  # 0.1%

    # 最小资金费率阈值
    # 确保资金费率为正（多头付费给空头）
    min_funding_rate: float = 0.0001  # 0.01% per hour

    # ==================== 平仓条件参数 ====================

    # 价差收敛阈值（获利平仓）
    # 当价差缩小到这个值时，认为套利空间消失，平仓获利
    close_spread_threshold: float = 0.0005  # 0.05%

    # 价差反转阈值（止损平仓）
    # 当价差变为负数且超过这个值时，止损平仓
    # 例如：-0.001 表示现货价格比永续价格高 0.1% 以上时止损
    reverse_spread_threshold: float = -0.001  # -0.1%

    # 资金费率反转阈值（可选）
    # 如果资金费率变为负数（空头付费），也考虑平仓
    # None 表示不使用此条件
    reverse_funding_threshold: float = -0.0001  # -0.01% per hour

    # ==================== 仓位管理参数 ====================

    # 每次交易的仓位大小（股数）
    position_size: int = 100

    # 最大同时持仓数
    max_positions: int = 1

    # ==================== 风控参数 ====================

    # 最大滑点容忍（百分比）
    max_slippage: float = 0.002  # 0.2%

    # 订单超时时间（秒）
    order_timeout: int = 30

    # 最小账户余额（USD）
    # 低于此值时不再开新仓
    min_account_balance: float = 10000.0

    # ==================== 数据有效性检查 ====================

    # 价格数据最大延迟（秒）
    # 如果数据超过这个时间没有更新，认为数据失效，不执行交易
    max_data_age: float = 5.0

    # 最小价格变化（用于判断市场是否活跃）
    min_price_change: float = 0.01  # $0.01


# 默认配置实例
DEFAULT_CONFIG = StrategyConfig()


def load_config_from_env():
    """从环境变量加载配置（如果需要）."""
    import os

    config = StrategyConfig()

    # 从环境变量读取（如果存在）
    if threshold := os.getenv("OPEN_SPREAD_THRESHOLD"):
        config.open_spread_threshold = float(threshold)

    if min_funding := os.getenv("MIN_FUNDING_RATE"):
        config.min_funding_rate = float(min_funding)

    if size := os.getenv("POSITION_SIZE"):
        config.position_size = int(size)

    return config
