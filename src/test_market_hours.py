"""测试市场时段检测功能"""

import datetime
from dateutil import tz


def test_market_session():
    """测试并显示当前市场时段信息"""
    print("=" * 60)
    print("美股市场时段检测测试")
    print("=" * 60)

    # 获取美国东部时间
    eastern = tz.gettz('America/New_York')
    now = datetime.datetime.now(eastern)

    # 获取当地时间（用户所在时区）
    local_now = datetime.datetime.now()
    local_tz = tz.tzlocal()

    print(f"\n当前时间信息：")
    print(f"  本地时间: {local_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  美东时间: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  星期: {['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()]}")

    # 判断是否夏令时
    is_dst = bool(now.dst())
    utc_offset = -4 if is_dst else -5
    print(f"  时区模式: {'夏令时 (DST)' if is_dst else '标准时间'} (UTC{utc_offset:+d})")

    # 判断市场时段
    current_minutes = now.hour * 60 + now.minute

    print(f"\n市场时段分析：")

    # 检查周末
    if now.weekday() >= 5:
        session = 'closed'
        print(f"  当前状态: 休市 (周末)")
    else:
        if 240 <= current_minutes < 570:
            session = 'pre_market'
            print(f"  当前状态: 盘前交易 (Pre-market)")
            print(f"  时段范围: 04:00 - 09:30 ET")
        elif 570 <= current_minutes < 960:
            session = 'regular'
            print(f"  当前状态: 盘中交易 (Regular hours) ✓")
            print(f"  时段范围: 09:30 - 16:00 ET")
        elif 960 <= current_minutes < 1200:
            session = 'after_hours'
            print(f"  当前状态: 盘后交易 (After-hours)")
            print(f"  时段范围: 16:00 - 20:00 ET")
        else:
            session = 'closed'
            print(f"  当前状态: 休市 (非交易时间)")

    print(f"\n市场时段详情：")
    print(f"  盘前交易: 04:00 - 09:30 ET")
    print(f"  常规交易: 09:30 - 16:00 ET  ⭐最佳时段")
    print(f"  盘后交易: 16:00 - 20:00 ET")

    # 转换为北京时间示例
    if is_dst:
        print(f"\n转换为北京时间（夏令时 UTC-4）：")
        print(f"  盘前: 16:00 - 21:30")
        print(f"  盘中: 21:30 - 04:00+1 (次日)")
        print(f"  盘后: 04:00 - 08:00+1 (次日)")
    else:
        print(f"\n转换为北京时间（冬令时 UTC-5）：")
        print(f"  盘前: 17:00 - 22:30")
        print(f"  盘中: 22:30 - 05:00+1 (次日)")
        print(f"  盘后: 05:00 - 09:00+1 (次日)")

    print(f"\n配置建议：")
    if session == 'regular':
        print(f"  ✓ 当前是最佳采集时段")
        print(f"  ✓ IBKR 数据质量最高")
        print(f"  ✓ 建议配置: IBKR_REGULAR_HOURS_ONLY=false")
    elif session in ['pre_market', 'after_hours']:
        print(f"  ⚠ 当前在盘前/盘后时段")
        print(f"  ⚠ IBKR 数据可能有延迟")
        print(f"  建议配置: IBKR_REGULAR_HOURS_ONLY=true (仅盘中采集)")
    else:
        print(f"  ⚠ 当前休市")
        print(f"  ⚠ IBKR 将返回上次收盘价")
        print(f"  建议配置: IBKR_REGULAR_HOURS_ONLY=true (仅盘中采集)")

    print("\n" + "=" * 60)
    print(f"测试完成！当前市场状态: {session}")
    print("=" * 60)

    return session


if __name__ == "__main__":
    try:
        from ib_fetcher import IBKRFetcher

        print("\n使用 IBKRFetcher 测试：")
        print("-" * 60)

        fetcher = IBKRFetcher()
        session = fetcher.get_market_session()

        session_names = {
            'pre_market': '盘前交易',
            'regular': '盘中交易',
            'after_hours': '盘后交易',
            'closed': '休市'
        }

        print(f"IBKRFetcher.get_market_session(): {session}")
        print(f"中文描述: {session_names.get(session, session)}")
        print(f"is_market_open(): {fetcher.is_market_open()}")
        print(f"is_regular_hours(): {fetcher.is_regular_hours()}")

        print("\n" + "-" * 60)

    except ImportError:
        print("\n注意: 未安装 ib_insync，跳过 IBKRFetcher 测试")

    # 运行独立测试
    test_market_session()
