"""Test fetching xyz:NVDA data with proper initialization."""

from hyperliquid.info import Info
from hyperliquid.utils import constants


def test_xyz_nvda_v2():
    """Test fetching NVDA data from xyz DEX with proper initialization."""
    print("Testing xyz:NVDA Data Fetching (v2)")
    print("=" * 50)

    # Initialize Info with xyz perp_dexs
    info = Info(
        constants.MAINNET_API_URL,
        skip_ws=True,
        perp_dexs=["xyz"]
    )

    print("\n1. Checking name_to_coin mapping...")
    if "NVDA" in info.name_to_coin:
        print(f"   ✓ Found 'NVDA' mapping to: '{info.name_to_coin['NVDA']}'")
    else:
        print("   ✗ 'NVDA' not in name_to_coin")

    if "xyz:NVDA" in info.name_to_coin:
        print(f"   ✓ Found 'xyz:NVDA' mapping to: '{info.name_to_coin['xyz:NVDA']}'")
    else:
        print("   ✗ 'xyz:NVDA' not in name_to_coin")

    # Try different name variations
    for name in ["NVDA", "xyz:NVDA"]:
        if name in info.name_to_coin:
            coin = info.name_to_coin[name]
            print(f"\n2. Testing L2 orderbook with '{name}' (coin: '{coin}')...")
            try:
                l2_data = info.l2_snapshot(name)
                levels = l2_data.get("levels", [[], []])

                if levels[0] and len(levels[0]) > 0:
                    best_bid = float(levels[0][0]["px"])
                    print(f"   Best Bid: ${best_bid}")

                if levels[1] and len(levels[1]) > 0:
                    best_ask = float(levels[1][0]["px"])
                    print(f"   Best Ask: ${best_ask}")
            except Exception as e:
                print(f"   Error: {e}")

            print(f"\n3. Testing candles with '{name}'...")
            try:
                import time
                end_time = int(time.time() * 1000)
                start_time = end_time - 3600000  # 1 hour ago

                candles = info.candles_snapshot(
                    name,
                    interval="1m",
                    startTime=start_time,
                    endTime=end_time
                )

                if candles and len(candles) > 0:
                    latest = candles[-1]
                    print(f"   Latest candle:")
                    print(f"     Open:  ${latest['o']}")
                    print(f"     Close: ${latest['c']}")
                    print(f"     High:  ${latest['h']}")
                    print(f"     Low:   ${latest['l']}")
                else:
                    print("   No candles found")
            except Exception as e:
                print(f"   Error: {e}")

            print(f"\n4. Testing funding rate with '{name}'...")
            try:
                import time
                end_time = int(time.time() * 1000)
                start_time = end_time - 86400000  # 24 hours ago

                funding_history = info.funding_history(
                    name,
                    startTime=start_time,
                    endTime=end_time
                )

                if funding_history and len(funding_history) > 0:
                    latest_funding = funding_history[-1]
                    funding_rate = float(latest_funding.get("fundingRate", 0))
                    print(f"   Latest Funding Rate: {funding_rate * 100:.4f}%")
                else:
                    print("   No funding history found")
            except Exception as e:
                print(f"   Error: {e}")

            # Only test first valid name
            break

    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    test_xyz_nvda_v2()
