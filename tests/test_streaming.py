"""Test IBKR streaming/subscription mode."""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ib_fetcher.fetcher_streaming import IBKRFetcherStreaming

def main():
    print("=" * 60)
    print("Testing IBKR Streaming Mode")
    print("=" * 60)

    # 初始化并连接（自动订阅）
    fetcher = IBKRFetcherStreaming(
        symbol="NVDA",
        host="127.0.0.1",
        port=4001,  # 或 4002 for paper
        client_id=1
    )

    if not fetcher.connect():
        print("Failed to connect")
        return

    # 获取账户信息
    account_id = fetcher.get_account_id()
    print(f"\n使用账户: {account_id}")

    print("\n开始实时读取数据（订阅模式）...")
    print("按 Ctrl+C 停止\n")

    try:
        iteration = 0
        while True:
            iteration += 1

            # 直接读取（无需等待，ticker 已经是最新的）
            price_data = fetcher.get_stock_price()

            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] #{iteration:3d} | "
                  f"Bid: ${price_data.get('bid', 'N/A'):>7} | "
                  f"Ask: ${price_data.get('ask', 'N/A'):>7} | "
                  f"Last: ${price_data.get('last', 'N/A'):>7}")

            # 等待 1 秒（可以更频繁，因为是订阅模式）
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n停止测试...")

    # 断开连接（自动取消订阅）
    fetcher.disconnect()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
