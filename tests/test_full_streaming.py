"""Test both Hyperliquid and IBKR in streaming mode."""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from hl_fetcher.fetcher_streaming import HyperliquidFetcherStreaming
from ib_fetcher.fetcher_streaming import IBKRFetcherStreaming

def main():
    print("=" * 70)
    print("Full Streaming Mode Test - Hyperliquid + IBKR")
    print("=" * 70)

    # 初始化 Hyperliquid WebSocket
    print("\n1. Initializing Hyperliquid WebSocket...")
    hl_fetcher = HyperliquidFetcherStreaming(
        symbol="xyz:NVDA",
        use_testnet=False,
        perp_dexs=["xyz"]
    )
    print("✓ Hyperliquid ready")

    # 初始化 IBKR 订阅
    print("\n2. Initializing IBKR subscription...")
    ibkr_fetcher = IBKRFetcherStreaming(
        symbol="NVDA",
        host="127.0.0.1",
        port=4001,  # 或 4002 for paper
        client_id=1
    )

    if not ibkr_fetcher.connect():
        print("✗ Failed to connect to IBKR")
        return

    account_id = ibkr_fetcher.get_account_id()
    print(f"✓ IBKR ready - Account: {account_id}")

    print("\n" + "=" * 70)
    print("Streaming data from both sources...")
    print("Press Ctrl+C to stop")
    print("=" * 70 + "\n")

    try:
        iteration = 0
        while True:
            iteration += 1
            timestamp = time.strftime("%H:%M:%S")

            # 从 Hyperliquid 获取数据（WebSocket）
            hl_metrics = hl_fetcher.get_all_metrics()

            # 从 IBKR 获取数据（订阅模式）
            ibkr_data = ibkr_fetcher.get_stock_price()

            # 显示数据（处理 None 值）
            perp_bid = hl_metrics.get('perp_bid')
            perp_ask = hl_metrics.get('perp_ask')
            open_price = hl_metrics.get('open')
            close_price = hl_metrics.get('close')
            funding_rate = hl_metrics.get('funding_rate', 0)
            spot_bid = ibkr_data.get('bid')
            spot_ask = ibkr_data.get('ask')

            print(f"[{timestamp}] Iteration {iteration:3d}")
            print(f"  Hyperliquid:")
            print(f"    Perp Bid: ${perp_bid if perp_bid else 'N/A':>7}  "
                  f"Perp Ask: ${perp_ask if perp_ask else 'N/A':>7}")
            print(f"    Open:     ${open_price if open_price else 'N/A':>7}  "
                  f"Close:    ${close_price if close_price else 'N/A':>7}")
            print(f"    Funding:  {funding_rate * 100:.4f}%")

            print(f"  IBKR:")
            print(f"    Spot Bid: ${spot_bid if spot_bid else 'N/A':>7}  "
                  f"Spot Ask: ${spot_ask if spot_ask else 'N/A':>7}")

            # 计算价差（套利机会指标）
            perp_mid = None
            spot_mid = None

            if hl_metrics.get('perp_bid') and hl_metrics.get('perp_ask'):
                perp_mid = (hl_metrics['perp_bid'] + hl_metrics['perp_ask']) / 2

            if ibkr_data.get('bid') and ibkr_data.get('ask'):
                spot_mid = (ibkr_data['bid'] + ibkr_data['ask']) / 2

            if perp_mid and spot_mid:
                spread = perp_mid - spot_mid
                spread_pct = (spread / spot_mid) * 100
                print(f"  Arbitrage:")
                print(f"    Spread:   ${spread:>7.2f} ({spread_pct:>+6.3f}%)")

            print()

            # 等待（可以很短，因为是流式数据）
            time.sleep(2)  # 2 秒一次，展示实时性

    except KeyboardInterrupt:
        print("\n\nStopping...")

    # 清理
    print("\nCleaning up...")
    ibkr_fetcher.disconnect()
    hl_fetcher.close()

    print("\n" + "=" * 70)
    print("Test completed")
    print("=" * 70)

if __name__ == "__main__":
    main()
