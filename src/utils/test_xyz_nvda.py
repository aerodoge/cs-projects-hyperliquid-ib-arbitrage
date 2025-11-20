"""Test fetching xyz:NVDA data."""

from hyperliquid.info import Info
from hyperliquid.utils import constants


def test_xyz_nvda():
    """Test fetching NVDA data from xyz DEX."""
    print("Testing xyz:NVDA Data Fetching")
    print("=" * 50)

    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    # Test 1: Get metadata for xyz dex
    print("\n1. Getting metadata for xyz DEX...")
    try:
        meta = info.meta(dex="xyz")
        print(f"   Found {len(meta['universe'])} assets in xyz DEX")

        # Find NVDA
        nvda_asset = None
        for asset in meta['universe']:
            if 'NVDA' in asset['name'].upper():
                nvda_asset = asset
                print(f"   ✓ Found: {asset['name']}")
                print(f"   Decimals: {asset['szDecimals']}")
                break

        if not nvda_asset:
            print("   ✗ NVDA not found")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # Test 2: Get L2 orderbook
    print("\n2. Getting L2 orderbook for xyz:NVDA...")
    try:
        l2_data = info.l2_snapshot("xyz:NVDA")
        levels = l2_data.get("levels", [[], []])

        if levels[0] and len(levels[0]) > 0:
            best_bid = float(levels[0][0]["px"])
            print(f"   Best Bid: ${best_bid}")

        if levels[1] and len(levels[1]) > 0:
            best_ask = float(levels[1][0]["px"])
            print(f"   Best Ask: ${best_ask}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Get all mids
    print("\n3. Getting mid prices for xyz DEX...")
    try:
        all_mids = info.all_mids(dex="xyz")
        nvda_mid = all_mids.get("xyz:NVDA")
        if nvda_mid:
            print(f"   NVDA Mid Price: ${nvda_mid}")
        else:
            print("   NVDA mid price not found")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 4: Get candles
    print("\n4. Getting recent candles...")
    try:
        import time
        end_time = int(time.time() * 1000)
        start_time = end_time - 3600000  # 1 hour ago

        candles = info.candles_snapshot(
            "xyz:NVDA",
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

    # Test 5: Try to get funding rate
    print("\n5. Getting funding rate...")
    try:
        # Try funding history
        import time
        end_time = int(time.time() * 1000)
        start_time = end_time - 86400000  # 24 hours ago

        funding_history = info.funding_history(
            "xyz:NVDA",
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

    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    test_xyz_nvda()
