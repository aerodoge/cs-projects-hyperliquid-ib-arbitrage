"""Find NVDA in community-deployed perp markets."""

from hyperliquid.info import Info
from hyperliquid.utils import constants


def find_nvda_in_dexs():
    """Search for NVDA in all perp dexs including community-deployed ones."""
    print("Searching for NVDA in Perpetual DEXs")
    print("=" * 50)

    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    # Get all perp dexs
    perp_dexs = info.perp_dexs()

    print(f"\nFound {len(perp_dexs)} perpetual DEXs:\n")

    nvda_found_in_dexs = []

    for idx, dex in enumerate(perp_dexs):
        if dex is None:
            print(f"{idx + 1}. DEX: None (skipping)")
            continue

        dex_name = dex.get('name', '')
        print(f"{idx + 1}. DEX: '{dex_name}' (Builder: {dex.get('builder', 'N/A')})")

        try:
            # Get metadata for this dex
            meta = info.meta(dex=dex_name)

            # Search for NVDA
            for asset in meta['universe']:
                if 'NVDA' in asset['name'].upper():
                    nvda_found_in_dexs.append({
                        'dex_name': dex_name,
                        'dex_builder': dex.get('builder', 'N/A'),
                        'asset_name': asset['name'],
                        'sz_decimals': asset['szDecimals']
                    })
                    print(f"   ✓ FOUND NVDA: {asset['name']}")

        except Exception as e:
            print(f"   Error fetching metadata: {e}")

    print("\n" + "=" * 50)
    if nvda_found_in_dexs:
        print(f"\nSummary: Found NVDA in {len(nvda_found_in_dexs)} DEX(s):")
        for item in nvda_found_in_dexs:
            print(f"  DEX: '{item['dex_name']}'")
            print(f"  Builder: {item['dex_builder']}")
            print(f"  Asset: {item['asset_name']}")
            print(f"  Decimals: {item['sz_decimals']}")
            print()
    else:
        print("\nNo NVDA markets found in any DEX.")


if __name__ == "__main__":
    find_nvda_in_dexs()
