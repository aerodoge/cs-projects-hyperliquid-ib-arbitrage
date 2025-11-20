"""List available assets on Hyperliquid."""

from hyperliquid.info import Info
from hyperliquid.utils import constants


def list_perp_assets():
    """List all perpetual contract assets."""
    print("Fetching Perpetual Contract Assets")
    print("=" * 50)

    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    # Get metadata
    meta = info.meta()

    print(f"\nFound {len(meta['universe'])} perpetual assets:\n")

    for idx, asset in enumerate(meta['universe'][:50]):  # Show first 50
        print(f"{idx + 1}. {asset['name']} (szDecimals: {asset['szDecimals']})")

    # Check if NVDA exists
    nvda_found = any(asset['name'] == 'NVDA' for asset in meta['universe'])
    print(f"\nNVDA found: {nvda_found}")

    # Search for similar names
    print("\nSearching for stock-like assets...")
    stock_like = [asset['name'] for asset in meta['universe'] if any(c.isupper() for c in asset['name']) and len(asset['name']) <= 5]
    print(f"Found {len(stock_like)} potential stock symbols: {', '.join(stock_like[:20])}")


def list_spot_assets():
    """List all spot assets."""
    print("\n\nFetching Spot Assets")
    print("=" * 50)

    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    # Get spot metadata
    spot_meta = info.spot_meta()

    print(f"\nFound {len(spot_meta['universe'])} spot pairs:\n")

    for idx, asset in enumerate(spot_meta['universe'][:30]):  # Show first 30
        tokens = asset['tokens']
        token_names = []
        for token_id in tokens:
            token_info = spot_meta['tokens'][token_id]
            token_names.append(token_info['name'])

        pair_name = f"{token_names[0]}/{token_names[1]}"
        print(f"{idx + 1}. {asset['name']} ({pair_name})")


if __name__ == "__main__":
    list_perp_assets()
    list_spot_assets()
