"""Test script to verify Hyperliquid data fetching."""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from hl_fetcher import HyperliquidFetcher


def test_fetch_all_metrics():
    """Test fetching all metrics from Hyperliquid."""
    print("Testing Hyperliquid Data Fetcher")
    print("=" * 50)

    # Initialize fetcher (using mainnet by default)
    print("\nInitializing fetcher for NVDA...")
    fetcher = HyperliquidFetcher(symbol="NVDA", use_testnet=False)

    # Test orderbook prices
    print("\n1. Testing orderbook prices...")
    orderbook = fetcher.get_orderbook_prices()
    print(f"   Perp Bid: ${orderbook.get('perp_bid', 'N/A')}")
    print(f"   Perp Ask: ${orderbook.get('perp_ask', 'N/A')}")

    # Test spot prices
    print("\n2. Testing spot prices...")
    spot = fetcher.get_spot_prices()
    print(f"   Spot Bid: ${spot.get('spot_bid', 'N/A')}")
    print(f"   Spot Ask: ${spot.get('spot_ask', 'N/A')}")

    # Test spread prices
    print("\n3. Testing spread prices (from candles)...")
    spread = fetcher.get_spread_prices()
    print(f"   Open:  ${spread.get('open', 'N/A')}")
    print(f"   Close: ${spread.get('close', 'N/A')}")

    # Test funding rate
    print("\n4. Testing funding rate...")
    funding_rate = fetcher.get_funding_rate()
    if funding_rate is not None:
        funding_pct = funding_rate * 100
        print(f"   Funding Rate: {funding_pct:.4f}%")
    else:
        print(f"   Funding Rate: N/A")

    # Test get_all_metrics
    print("\n5. Testing get_all_metrics()...")
    all_metrics = fetcher.get_all_metrics()
    print("\n   All metrics:")
    for key, value in all_metrics.items():
        if value is not None:
            if key == "funding_rate":
                print(f"   {key}: {value * 100:.4f}%")
            else:
                print(f"   {key}: ${value:.2f}")
        else:
            print(f"   {key}: N/A")

    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    test_fetch_all_metrics()
