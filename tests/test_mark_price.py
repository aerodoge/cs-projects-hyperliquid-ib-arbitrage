"""Test script for Mark Price retrieval from Hyperliquid."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from hl_fetcher.fetcher_streaming import HyperliquidFetcherStreaming


def main():
    """Test Mark Price fetching."""
    print("=" * 60)
    print("Testing Hyperliquid Mark Price Retrieval")
    print("=" * 60)

    symbol = "xyz:NVDA"
    print(f"\nInitializing fetcher for {symbol}...")

    # Initialize fetcher
    fetcher = HyperliquidFetcherStreaming(
        symbol=symbol,
        use_testnet=False,
        perp_dexs=["xyz"]
    )

    print("\n" + "=" * 60)
    print("Fetching market data (5 iterations)")
    print("=" * 60)

    try:
        for i in range(5):
            print(f"\nIteration {i+1}/5:")

            # Get all metrics
            metrics = fetcher.get_all_metrics()

            perp_bid = metrics.get('perp_bid')
            perp_ask = metrics.get('perp_ask')
            mark_price = metrics.get('mark_price')
            funding_rate = metrics.get('funding_rate')

            # Calculate mid price for comparison
            mid_price = None
            if perp_bid and perp_ask:
                mid_price = (perp_bid + perp_ask) / 2

            print(f"  Perp Bid:     ${perp_bid if perp_bid else 'N/A'}")
            print(f"  Perp Ask:     ${perp_ask if perp_ask else 'N/A'}")
            print(f"  Mid Price:    ${mid_price if mid_price else 'N/A'}")
            print(f"  Mark Price:   ${mark_price if mark_price else 'N/A'}")

            # Compare Mark Price with Mid Price
            if mark_price and mid_price:
                diff = mark_price - mid_price
                diff_pct = (diff / mid_price) * 100
                print(f"  Difference:   ${diff:.4f} ({diff_pct:+.4f}%)")

            if funding_rate is not None:
                print(f"  Funding Rate: {funding_rate * 100:.4f}%")
            else:
                print(f"  Funding Rate: N/A")

            if i < 4:  # Don't sleep after last iteration
                time.sleep(2)

        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        import traceback
        print(f"\n✗ Error during test: {e}")
        print("\nFull traceback:")
        print(traceback.format_exc())
    finally:
        print("\nClosing connection...")
        fetcher.close()
        print("✓ Connection closed")


if __name__ == "__main__":
    main()
