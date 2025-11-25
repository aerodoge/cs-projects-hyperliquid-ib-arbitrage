"""Test script for arbitrage strategy logic."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from trader.strategy import ArbitrageStrategy, MarketData, SignalType
from trader.config import StrategyConfig


def test_spread_calculation():
    """测试价差计算逻辑."""
    print("=" * 60)
    print("Testing Spread Calculation")
    print("=" * 60)

    strategy = ArbitrageStrategy()

    # 测试用例1：正价差，应该有开仓信号
    print("\n### Test Case 1: Positive Spread (Should Open)")
    market_data = MarketData(
        perp_bid=180.50,      # HL 开空价
        perp_ask=180.51,
        spot_bid=180.30,
        spot_ask=180.32,      # IB 买入价
        funding_rate=0.0002,  # 0.02%
    )

    analysis = strategy.calculate_spread(market_data)
    print(f"Spread: {analysis.spread*100:.4f}%")
    print(f"Expected: (180.50 / 180.32 - 1) = {(180.50/180.32 - 1)*100:.4f}%")

    signal, reason = strategy.get_open_signal(analysis)
    print(f"Signal: {signal.value}")
    print(f"Reason: {reason}")
    print(strategy.format_analysis(analysis))

    # 测试用例2：价差不足，不应该开仓
    print("\n### Test Case 2: Insufficient Spread (Should NOT Open)")
    market_data = MarketData(
        perp_bid=180.40,      # HL 开空价
        perp_ask=180.41,
        spot_bid=180.38,
        spot_ask=180.39,      # IB 买入价
        funding_rate=0.0002,
    )

    analysis = strategy.calculate_spread(market_data)
    print(f"Spread: {analysis.spread*100:.4f}%")

    signal, reason = strategy.get_open_signal(analysis)
    print(f"Signal: {signal.value}")
    print(f"Reason: {reason}")

    # 测试用例3：资金费率为负，不应该开仓
    print("\n### Test Case 3: Negative Funding Rate (Should NOT Open)")
    market_data = MarketData(
        perp_bid=180.50,
        perp_ask=180.51,
        spot_bid=180.30,
        spot_ask=180.32,
        funding_rate=-0.0002,  # 负资金费率
    )

    analysis = strategy.calculate_spread(market_data)
    signal, reason = strategy.get_open_signal(analysis)
    print(f"Signal: {signal.value}")
    print(f"Reason: {reason}")

    # 测试用例4：价差收敛，应该平仓
    print("\n### Test Case 4: Spread Convergence (Should Close)")
    market_data = MarketData(
        perp_bid=180.35,      # 价差缩小
        perp_ask=180.36,
        spot_bid=180.33,
        spot_ask=180.34,
        funding_rate=0.0002,
    )

    analysis = strategy.calculate_spread(market_data)
    print(f"Spread: {analysis.spread*100:.4f}%")

    # 假设开仓时价差是 0.1%
    entry_spread = 0.001
    signal, reason = strategy.get_close_signal(analysis, entry_spread)
    print(f"Signal: {signal.value}")
    print(f"Reason: {reason}")

    # 测试用例5：价差反转，应该止损
    print("\n### Test Case 5: Spread Reversal (Should Stop Loss)")
    market_data = MarketData(
        perp_bid=180.20,      # 价差变负
        perp_ask=180.21,
        spot_bid=180.35,
        spot_ask=180.36,
        funding_rate=0.0002,
    )

    analysis = strategy.calculate_spread(market_data)
    print(f"Spread: {analysis.spread*100:.4f}%")

    signal, reason = strategy.get_close_signal(analysis, entry_spread)
    print(f"Signal: {signal.value}")
    print(f"Reason: {reason}")


def test_with_real_data():
    """使用模拟实时数据测试."""
    print("\n" + "=" * 60)
    print("Testing with Simulated Real-Time Data")
    print("=" * 60)

    import time

    strategy = ArbitrageStrategy()

    # 模拟数据序列
    data_sequence = [
        # 时间, perp_bid, spot_ask, funding_rate
        ("Initial", 180.50, 180.30, 0.0003),
        ("After 1h", 180.45, 180.32, 0.0002),
        ("After 2h", 180.40, 180.35, 0.0001),
        ("After 3h", 180.35, 180.36, -0.0001),
    ]

    for label, perp_bid, spot_ask, funding_rate in data_sequence:
        print(f"\n### {label}")

        market_data = MarketData(
            perp_bid=perp_bid,
            perp_ask=perp_bid + 0.01,
            spot_bid=spot_ask - 0.02,
            spot_ask=spot_ask,
            funding_rate=funding_rate,
            timestamp=time.time()
        )

        analysis = strategy.calculate_spread(market_data)

        print(f"Perp Bid: ${perp_bid:.2f}")
        print(f"Spot Ask: ${spot_ask:.2f}")
        print(f"Spread: {analysis.spread*100:+.4f}%")
        print(f"Funding: {funding_rate*100:+.4f}%")

        # 检查开仓信号
        signal, reason = strategy.get_open_signal(analysis)
        if signal != SignalType.NONE:
            print(f"📢 {signal.value.upper()}: {reason}")


def main():
    """运行所有测试."""
    test_spread_calculation()
    test_with_real_data()

    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
