"""Final integration test for the complete system."""

from hl_fetcher import HyperliquidFetcher


def test_complete_fetcher():
    """Test the complete fetcher with updated configuration."""
    print("=" * 60)
    print("Final Integration Test: Hyperliquid xyz:NVDA Data Fetcher")
    print("=" * 60)

    # Initialize fetcher with correct parameters
    print("\nInitializing fetcher...")
    fetcher = HyperliquidFetcher(symbol="xyz:NVDA", use_testnet=False, perp_dexs=["xyz"])
    print("✓ Fetcher initialized successfully")

    # Fetch all metrics
    print("\nFetching all metrics from Hyperliquid...")
    metrics = fetcher.get_all_metrics()

    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print("\n1. Perpetual Contract Prices (from L2 Orderbook):")
    if metrics.get('perp_bid') is not None:
        print(f"   Perp Bid:  ${metrics['perp_bid']:.2f}")
    else:
        print(f"   Perp Bid:  N/A")

    if metrics.get('perp_ask') is not None:
        print(f"   Perp Ask:  ${metrics['perp_ask']:.2f}")
    else:
        print(f"   Perp Ask:  N/A")

    print("\n2. Spot Market Prices:")
    print(f"   Spot Bid:  N/A (spot market doesn't exist for xyz:NVDA)")
    print(f"   Spot Ask:  N/A (spot market doesn't exist for xyz:NVDA)")

    print("\n3. Spread Prices (from Recent Candles):")
    if metrics.get('open') is not None:
        print(f"   Open:      ${metrics['open']:.2f}")
    else:
        print(f"   Open:      N/A")

    if metrics.get('close') is not None:
        print(f"   Close:     ${metrics['close']:.2f}")
    else:
        print(f"   Close:     N/A")

    if metrics.get('open') is not None and metrics.get('close') is not None:
        spread = metrics['close'] - metrics['open']
        print(f"   Spread:    ${spread:.2f} ({spread/metrics['open']*100:.2f}%)")

    print("\n4. Funding Rate:")
    if metrics.get('funding_rate') is not None:
        funding_pct = metrics['funding_rate'] * 100
        print(f"   Rate:      {funding_pct:.4f}%")
    else:
        print(f"   Rate:      N/A")

    print("\n" + "=" * 60)

    # Check if all critical metrics were retrieved
    critical_metrics = ['perp_bid', 'perp_ask', 'open', 'close', 'funding_rate']
    success_count = sum(1 for m in critical_metrics if metrics.get(m) is not None)

    print(f"\nTest Summary: {success_count}/{len(critical_metrics)} critical metrics retrieved")

    if success_count == len(critical_metrics):
        print("✓ ALL TESTS PASSED")
    elif success_count >= 3:
        print("⚠ PARTIAL SUCCESS - Some metrics unavailable")
    else:
        print("✗ TEST FAILED - Most metrics unavailable")

    print("=" * 60)

    return metrics


if __name__ == "__main__":
    test_complete_fetcher()
