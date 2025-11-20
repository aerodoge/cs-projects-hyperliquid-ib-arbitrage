"""Search for stock-related assets on Hyperliquid."""

from hyperliquid.info import Info
from hyperliquid.utils import constants


def search_for_stocks():
    """Search for potential stock symbols."""
    print("Searching for Stock Symbols on Hyperliquid")
    print("=" * 50)

    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    # Get all perpetual assets
    meta = info.meta()

    # Common stock symbols to search for
    stock_symbols = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX']

    print("\nSearching for common stock symbols...\n")

    found_stocks = []
    for symbol in stock_symbols:
        exists = any(asset['name'] == symbol for asset in meta['universe'])
        status = "✓ FOUND" if exists else "✗ Not found"
        print(f"{symbol}: {status}")
        if exists:
            found_stocks.append(symbol)

    if found_stocks:
        print(f"\nFound stocks: {', '.join(found_stocks)}")
    else:
        print("\nNo traditional stock symbols found.")

    # Show all assets (for reference)
    print(f"\n\nAll {len(meta['universe'])} available perpetual assets:")
    print("-" * 50)

    for asset in meta['universe']:
        print(asset['name'])


if __name__ == "__main__":
    search_for_stocks()
