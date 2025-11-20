"""Main script to fetch Hyperliquid NVDA data and push to Prometheus."""

import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

from hl_fetcher import HyperliquidFetcher
from prom_pusher import PrometheusMetricsPusher


def main():
    """Main function to run the data collection and push loop."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Fetch NVDA data from Hyperliquid and push to Prometheus"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=os.getenv("SYMBOL", "xyz:NVDA"),
        help="Trading symbol (default: xyz:NVDA)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("FETCH_INTERVAL", "60")),
        help="Fetch interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--push-gateway",
        type=str,
        default=os.getenv("PUSH_GATEWAY_URL"),
        help="Prometheus Push Gateway URL (e.g., localhost:9091)"
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        default=os.getenv("USE_TESTNET", "false").lower() == "true",
        help="Use Hyperliquid testnet instead of mainnet"
    )
    parser.add_argument(
        "--job-name",
        type=str,
        default=os.getenv("JOB_NAME", "hyperliquid_nvda"),
        help="Prometheus job name (default: hyperliquid_nvda)"
    )
    parser.add_argument(
        "--perp-dexs",
        type=str,
        default=os.getenv("PERP_DEXS", "xyz"),
        help="Comma-separated list of perp DEXs to use (default: xyz)"
    )

    args = parser.parse_args()

    # Validate push gateway URL
    if not args.push_gateway:
        print("Error: Push Gateway URL is required. Set PUSH_GATEWAY_URL in .env or use --push-gateway")
        return

    print(f"Starting Hyperliquid {args.symbol} data collector")
    print(f"Symbol: {args.symbol}")
    print(f"Interval: {args.interval}s")
    print(f"Push Gateway: {args.push_gateway}")
    print(f"Using {'testnet' if args.testnet else 'mainnet'}")
    print("-" * 50)

    # Parse perp_dexs
    perp_dexs = [dex.strip() for dex in args.perp_dexs.split(",")] if args.perp_dexs else ["xyz"]

    # Initialize fetcher and pusher
    fetcher = HyperliquidFetcher(
        symbol=args.symbol,
        use_testnet=args.testnet,
        perp_dexs=perp_dexs
    )
    pusher = PrometheusMetricsPusher(
        push_gateway_url=args.push_gateway,
        job_name=args.job_name
    )

    # Main loop
    iteration = 0
    while True:
        try:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n[{timestamp}] Iteration {iteration}")

            # Fetch all metrics
            print("Fetching metrics from Hyperliquid...")
            metrics = fetcher.get_all_metrics()

            # Display fetched metrics
            print("\nFetched metrics:")
            print(f"  Perp Bid:     ${metrics.get('perp_bid', 'N/A')}")
            print(f"  Perp Ask:     ${metrics.get('perp_ask', 'N/A')}")
            print(f"  Spot Bid:     ${metrics.get('spot_bid', 'N/A')}")
            print(f"  Spot Ask:     ${metrics.get('spot_ask', 'N/A')}")
            print(f"  Open Price:   ${metrics.get('open', 'N/A')}")
            print(f"  Close Price:  ${metrics.get('close', 'N/A')}")

            funding_rate = metrics.get('funding_rate')
            if funding_rate is not None:
                funding_pct = funding_rate * 100
                print(f"  Funding Rate: {funding_pct:.4f}%")
            else:
                print(f"  Funding Rate: N/A")

            # Push to Prometheus
            print("\nPushing metrics to Prometheus...")
            success = pusher.update_and_push(metrics)

            if success:
                print("Successfully pushed metrics to Prometheus")
            else:
                print("Failed to push metrics to Prometheus")

            # Wait for next iteration
            print(f"\nWaiting {args.interval} seconds until next fetch...")
            time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\n\nReceived interrupt signal. Shutting down...")
            break
        except Exception as e:
            print(f"\nError in main loop: {e}")
            print(f"Retrying in {args.interval} seconds...")
            time.sleep(args.interval)

    print("\nData collector stopped.")


if __name__ == "__main__":
    main()
