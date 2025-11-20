"""测试获取 IBKR 账户信息"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ib_insync import IB


def get_account_info():
    """获取并显示 IBKR 账户信息"""
    print("=" * 60)
    print("IBKR 账户信息获取")
    print("=" * 60)

    # 配置
    host = "127.0.0.1"
    port = 7497  # TWS 纸交易，实盘改为 7496
    client_id = 1

    print(f"\n连接配置:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Client ID: {client_id}")

    ib = IB()

    try:
        # 连接
        print(f"\n正在连接到 IBKR...")
        ib.connect(host, port, clientId=client_id)
        print("✓ 连接成功\n")

        # 获取账户列表
        accounts = ib.managedAccounts()
        print(f"账户数量: {len(accounts)}")
        print(f"账户列表: {accounts}\n")

        if not accounts:
            print("⚠ 未找到账户")
            return None

        # 显示每个账户的详细信息
        for idx, account in enumerate(accounts, 1):
            print(f"账户 {idx}: {account}")
            print("-" * 40)

            # 判断账户类型
            if account.startswith('DU'):
                print(f"  类型: 纸交易账户 (Paper Trading)")
            elif account.startswith('U'):
                print(f"  类型: 实盘账户 (Live Trading)")
            elif account.startswith('F'):
                print(f"  类型: 顾问账户 (Advisor)")
            else:
                print(f"  类型: 其他")

            # 获取账户摘要信息
            print(f"\n  账户摘要:")
            account_values = ib.accountSummary(account)

            # 关键信息
            key_tags = [
                'NetLiquidation',    # 净资产
                'TotalCashValue',    # 现金总额
                'BuyingPower',       # 购买力
                'GrossPositionValue',# 持仓总值
                'UnrealizedPnL',     # 未实现盈亏
                'RealizedPnL'        # 已实现盈亏
            ]

            for value in account_values:
                if value.tag in key_tags:
                    print(f"    {value.tag:20s}: {value.value:>15s} {value.currency}")

            print()

        # 断开连接
        ib.disconnect()
        print("✓ 已断开连接\n")

        # 生成配置建议
        print("=" * 60)
        print("配置建议")
        print("=" * 60)
        print("\n在 .env 文件中添加：\n")
        print(f"IBKR_ACCOUNT_ID={accounts[0]}")

        if len(accounts) > 1:
            print("\n注意：检测到多个账户，默认使用第一个。")
            print("如需使用其他账户，请修改配置。")

        print("\n" + "=" * 60)

        return accounts

    except ConnectionRefusedError:
        print("\n✗ 连接被拒绝")
        print("\n请检查：")
        print("  1. TWS 或 IB Gateway 是否正在运行")
        print("  2. API 是否已启用")
        print("  3. 端口配置是否正确")
        print("     - TWS 纸交易: 7497")
        print("     - TWS 实盘: 7496")
        print("     - Gateway 纸交易: 4002")
        print("     - Gateway 实盘: 4001")
        return None

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    try:
        accounts = get_account_info()

        if accounts:
            print("\n✓ 账户信息获取成功！")
            sys.exit(0)
        else:
            print("\n✗ 未能获取账户信息")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)


if __name__ == "__main__":
    main()
