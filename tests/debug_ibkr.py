"""Debug IBKR connection and market data."""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ib_insync import IB, Stock

def debug_ibkr(port=4002):
    """详细调试 IBKR 连接和数据."""
    print("=" * 60)
    print(f"IBKR Connection Debug (Port {port})")
    print("=" * 60)

    ib = IB()

    try:
        # 连接
        print(f"\n1. 正在连接到 127.0.0.1:{port}...")
        ib.connect('127.0.0.1', port, clientId=1)
        print(f"✓ 连接成功")

        # 获取账户信息
        print("\n2. 获取账户信息...")
        accounts = ib.managedAccounts()
        print(f"账户列表: {accounts}")
        if accounts:
            account_id = accounts[0]
            print(f"使用账户: {account_id}")
            if account_id.startswith('DU'):
                print("  类型: 纸交易")
            elif account_id.startswith('U'):
                print("  类型: 实盘")

        # 创建合约
        print("\n3. 创建 NVDA 合约...")
        contract = Stock('NVDA', 'SMART', 'USD')
        ib.qualifyContracts(contract)
        print(f"✓ 合约信息: {contract}")

        # 请求市场数据
        print("\n4. 请求市场数据...")
        ticker = ib.reqMktData(contract, '', False, False)
        print(f"✓ Ticker 对象创建: {ticker}")

        # 等待数据
        print("\n5. 等待数据到达 (最多 15 秒)...")
        for i in range(30):  # 30 * 0.5 = 15 秒
            ib.sleep(0.5)
            print(f"   [{i+1:2d}/30] Bid: {ticker.bid}, Ask: {ticker.ask}, Last: {ticker.last}")

            if ticker.bid and ticker.ask:
                print(f"\n✓ 数据到达！")
                break

        # 显示最终数据
        print("\n6. 最终数据:")
        print(f"   Bid:    {ticker.bid} (type: {type(ticker.bid)})")
        print(f"   Ask:    {ticker.ask} (type: {type(ticker.ask)})")
        print(f"   Last:   {ticker.last} (type: {type(ticker.last)})")
        print(f"   Volume: {ticker.volume}")
        print(f"   Time:   {ticker.time}")

        # 检查是否是 NaN
        import math
        if ticker.bid and math.isnan(ticker.bid):
            print("\n⚠️ Bid 是 NaN - 可能原因:")
            print("   1. 没有市场数据订阅")
            print("   2. 市场数据权限未启用")
            print("   3. 股票未在交易")

        # 取消市场数据
        ib.cancelMktData(contract)

        # 断开连接
        ib.disconnect()

        print("\n" + "=" * 60)
        if ticker.bid and ticker.ask and not (math.isnan(ticker.bid) or math.isnan(ticker.ask)):
            print("✓ 测试成功 - 获取到有效数据")
        else:
            print("✗ 测试失败 - 数据无效或为 NaN")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        ib.disconnect()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4002, help='IBKR port (4002 for paper, 4001 for live)')
    args = parser.parse_args()

    debug_ibkr(args.port)
