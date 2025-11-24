"""Test script for IBKRFetcherWebSocket (Client Portal API via ibeam)."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ib_fetcher.fetcher_websocket import IBKRFetcherWebSocket


def main():
    """Test IBKR WebSocket fetcher."""
    print("=" * 60)
    print("Testing IBKR WebSocket Fetcher (Client Portal API)")
    print("=" * 60)
    print("\nMake sure ibeam is running:")
    print("  docker run -p 5000:5000 voyz/ibeam")
    print("=" * 60)

    symbol = "NVDA"
    base_url = "https://localhost:5000"

    print(f"\nInitializing fetcher for {symbol}...")
    fetcher = IBKRFetcherWebSocket(
        symbol=symbol,
        base_url=base_url
    )

    try:
        # Connect and subscribe
        print("\nConnecting to IBKR Client Portal WebSocket...")
        if not fetcher.connect():
            print("\n✗ Failed to connect. Make sure:")
            print("  1. ibeam is running (docker run -p 5000:5000 voyz/ibeam)")
            print("  2. You are logged in to IBKR")
            print("  3. The session is authenticated")
            return

        # Get account info
        print("\nFetching account information...")
        account_id = fetcher.get_account_id()
        if account_id:
            print(f"  Account ID: {account_id}")
            if account_id.startswith('DU'):
                print("  Type: Paper Trading")
            elif account_id.startswith('U'):
                print("  Type: Live Trading")
        else:
            print("  Account ID: Not available")

        # Check market session
        market_session = fetcher.get_market_session()
        session_names = {
            'pre_market': 'Pre-Market (盘前)',
            'regular': 'Regular Hours (盘中)',
            'after_hours': 'After Hours (盘后)',
            'closed': 'Market Closed (休市)'
        }
        print(f"  Market Session: {session_names.get(market_session, market_session)}")

        # Fetch market data multiple times
        print("\n" + "=" * 60)
        print("Fetching market data (10 iterations, 2s interval)")
        print("=" * 60)

        for i in range(10):
            print(f"\nIteration {i+1}/10:")

            prices = fetcher.get_stock_price()

            bid = prices.get('bid')
            ask = prices.get('ask')
            last = prices.get('last')
            mid = prices.get('mid')

            print(f"  Bid:  ${bid if bid else 'N/A'}")
            print(f"  Ask:  ${ask if ask else 'N/A'}")
            print(f"  Last: ${last if last else 'N/A'}")
            print(f"  Mid:  ${mid if mid else 'N/A'}")

            if bid is None or ask is None:
                print("  ⚠️  No market data received (market may be closed)")
            else:
                spread = ask - bid
                print(f"  Spread: ${spread:.2f}")

            if i < 9:  # Don't sleep after last iteration
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
        print("\nDisconnecting...")
        fetcher.disconnect()
        print("✓ Disconnected")


if __name__ == "__main__":
    main()
