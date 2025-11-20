"""Test IBKR connection and data fetching."""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ib_fetcher import IBKRFetcher


def test_ibkr_connection():
    """Test basic IBKR connection and data fetching."""
    print("=" * 60)
    print("Interactive Brokers Connection Test")
    print("=" * 60)

    # Configuration
    symbol = "NVDA"
    host = "127.0.0.1"
    port = 7497  # TWS Paper Trading

    print(f"\nConfiguration:")
    print(f"  Symbol: {symbol}")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print()

    # Test connection
    print("1. Testing connection...")
    fetcher = IBKRFetcher(symbol=symbol, host=host, port=port)

    if not fetcher.connect():
        print("✗ Connection failed!")
        print("\nTroubleshooting:")
        print("  1. Make sure TWS or IB Gateway is running")
        print("  2. Check that API is enabled in settings")
        print("  3. Verify the port number is correct")
        print("     - TWS Paper: 7497")
        print("     - TWS Live: 7496")
        print("     - Gateway Paper: 4002")
        print("     - Gateway Live: 4001")
        print("  4. Ensure you're logged into your account")
        sys.exit(1)

    print("✓ Connected successfully")

    # Test market status
    print("\n2. Checking market status...")
    is_open = fetcher.is_market_open()
    print(f"   Market is {'OPEN' if is_open else 'CLOSED'}")

    if not is_open:
        print("   Note: US stock market is closed")
        print("   Trading hours: Mon-Fri 9:30 AM - 4:00 PM ET")

    # Test price fetching
    print("\n3. Fetching stock prices...")
    prices = fetcher.get_stock_price()

    if not prices['bid'] or not prices['ask']:
        print("✗ Failed to get prices")
        print("   This could be because:")
        print("   - Market is closed")
        print("   - Data subscription is not active")
        print("   - Symbol is invalid")
    else:
        print("✓ Successfully retrieved prices:")
        print(f"   Bid:  ${prices['bid']:.2f}")
        print(f"   Ask:  ${prices['ask']:.2f}")
        print(f"   Last: ${prices['last']:.2f}" if prices['last'] else "   Last: N/A")
        print(f"   Mid:  ${prices['mid']:.2f}" if prices['mid'] else "   Mid: N/A")

        # Calculate spread
        if prices['bid'] and prices['ask']:
            spread = prices['ask'] - prices['bid']
            spread_pct = (spread / prices['ask']) * 100
            print(f"   Spread: ${spread:.2f} ({spread_pct:.3f}%)")

    # Test market snapshot
    print("\n4. Fetching market snapshot...")
    snapshot = fetcher.get_market_snapshot()

    if snapshot['open']:
        print("✓ Successfully retrieved market data:")
        print(f"   Open:   ${snapshot['open']:.2f}")
        print(f"   High:   ${snapshot['high']:.2f}")
        print(f"   Low:    ${snapshot['low']:.2f}")
        print(f"   Close:  ${snapshot['close']:.2f}" if snapshot['close'] else "   Close:  N/A")
        print(f"   Volume: {snapshot['volume']:,.0f}" if snapshot['volume'] else "   Volume: N/A")
    else:
        print("   No market data available (market may be closed)")

    # Disconnect
    print("\n5. Disconnecting...")
    fetcher.disconnect()
    print("✓ Disconnected")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run the main collector with IBKR:")
    print("     python src/main_with_ibkr.py")
    print()
    print("  2. Or disable IBKR if you only want Hyperliquid data:")
    print("     python src/main_with_ibkr.py --no-ibkr")
    print()


if __name__ == "__main__":
    try:
        test_ibkr_connection()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
