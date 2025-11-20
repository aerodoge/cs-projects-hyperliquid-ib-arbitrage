"""Search for NVDA in spot markets."""

from hyperliquid.info import Info
from hyperliquid.utils import constants


def search_nvda_in_spot():
    """Search for NVDA in spot markets."""
    print("Searching for NVDA in Spot Markets")
    print("=" * 50)

    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    # Get spot metadata
    spot_meta = info.spot_meta()

    print(f"\nTotal spot pairs: {len(spot_meta['universe'])}\n")

    # Search for NVDA
    nvda_pairs = []
    for asset in spot_meta['universe']:
        if 'NVDA' in asset['name'].upper():
            tokens = asset['tokens']
            token_names = []
            for token_id in tokens:
                token_info = spot_meta['tokens'][token_id]
                token_names.append(token_info['name'])

            pair_name = f"{token_names[0]}/{token_names[1]}"
            nvda_pairs.append({
                'name': asset['name'],
                'pair': pair_name,
                'index': asset['index'],
                'tokens': token_names
            })

    if nvda_pairs:
        print(f"Found {len(nvda_pairs)} NVDA-related pairs:")
        for pair in nvda_pairs:
            print(f"  Name: {pair['name']}")
            print(f"  Pair: {pair['pair']}")
            print(f"  Index: {pair['index']}")
            print()
    else:
        print("No NVDA pairs found in spot markets.")

    # Also search in tokens
    print("\nSearching for NVDA in token list...")
    nvda_tokens = []
    for token_id, token_info in enumerate(spot_meta['tokens']):
        if 'NVDA' in token_info['name'].upper():
            nvda_tokens.append({
                'id': token_id,
                'name': token_info['name'],
                'index': token_info['index']
            })

    if nvda_tokens:
        print(f"Found {len(nvda_tokens)} NVDA tokens:")
        for token in nvda_tokens:
            print(f"  ID: {token['id']}, Name: {token['name']}, Index: {token['index']}")
    else:
        print("No NVDA tokens found.")


if __name__ == "__main__":
    search_nvda_in_spot()
