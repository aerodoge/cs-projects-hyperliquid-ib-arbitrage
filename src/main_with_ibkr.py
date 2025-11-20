"""Main script with IBKR integration to fetch NVDA data and push to Prometheus."""

import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

from hl_fetcher import HyperliquidFetcher
from ib_fetcher import IBKRFetcher
from prom_pusher import PrometheusMetricsPusher


def main():
    """Main function to run the data collection and push loop."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Fetch NVDA data from Hyperliquid and IBKR, push to Prometheus"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=os.getenv("SYMBOL", "xyz:NVDA"),
        help="Trading symbol for Hyperliquid (default: xyz:NVDA)"
    )
    parser.add_argument(
        "--stock-symbol",
        type=str,
        default=os.getenv("STOCK_SYMBOL", "NVDA"),
        help="Stock symbol for IBKR (default: NVDA)"
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
    parser.add_argument(
        "--ibkr-host",
        type=str,
        default=os.getenv("IBKR_HOST", "127.0.0.1"),
        help="IBKR Gateway/TWS host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--ibkr-port",
        type=int,
        default=int(os.getenv("IBKR_PORT", "7497")),
        help="IBKR Gateway/TWS port (default: 7497 for TWS paper)"
    )
    parser.add_argument(
        "--ibkr-account-id",
        type=str,
        default=os.getenv("IBKR_ACCOUNT_ID", ""),
        help="IBKR account ID (e.g., DU1234567 for paper, U1234567 for live)"
    )
    parser.add_argument(
        "--ibkr-client-id",
        type=int,
        default=int(os.getenv("IBKR_CLIENT_ID", "1")),
        help="IBKR client ID (default: 1)"
    )
    parser.add_argument(
        "--no-ibkr",
        action="store_true",
        default=os.getenv("DISABLE_IBKR", "false").lower() == "true",
        help="Disable IBKR data fetching"
    )
    parser.add_argument(
        "--ibkr-regular-hours-only",
        action="store_true",
        default=os.getenv("IBKR_REGULAR_HOURS_ONLY", "false").lower() == "true",
        help="Only fetch IBKR data during regular market hours (9:30 AM - 4:00 PM ET)"
    )

    args = parser.parse_args()

    # Validate push gateway URL
    if not args.push_gateway:
        print("Error: Push Gateway URL is required. Set PUSH_GATEWAY_URL in .env or use --push-gateway")
        return

    print(f"Starting Hyperliquid + IBKR {args.stock_symbol} data collector")
    print(f"Hyperliquid Symbol: {args.symbol}")
    print(f"Stock Symbol: {args.stock_symbol}")
    print(f"Interval: {args.interval}s")
    print(f"Push Gateway: {args.push_gateway}")
    print(f"Using {'testnet' if args.testnet else 'mainnet'}")
    if args.no_ibkr:
        print(f"IBKR: Disabled")
    else:
        ibkr_mode = f"Enabled ({args.ibkr_host}:{args.ibkr_port})"
        if args.ibkr_regular_hours_only:
            ibkr_mode += " - Regular hours only (9:30 AM - 4:00 PM ET)"
        print(f"IBKR: {ibkr_mode}")
    print("-" * 50)

    # Parse perp_dexs
    perp_dexs = [dex.strip() for dex in args.perp_dexs.split(",")] if args.perp_dexs else ["xyz"]

    # Initialize Hyperliquid fetcher
    hl_fetcher = HyperliquidFetcher(
        symbol=args.symbol,
        use_testnet=args.testnet,
        perp_dexs=perp_dexs
    )

    # Initialize IBKR fetcher
    ibkr_fetcher = None
    if not args.no_ibkr:
        # 处理账户ID（空字符串转为 None）
        account_id = args.ibkr_account_id if args.ibkr_account_id else None

        ibkr_fetcher = IBKRFetcher(
            symbol=args.stock_symbol,
            host=args.ibkr_host,
            port=args.ibkr_port,
            client_id=args.ibkr_client_id,
            account_id=account_id
        )
        # Try to connect
        if not ibkr_fetcher.connect():
            print("Warning: Could not connect to IBKR. Continuing without IBKR data.")
            ibkr_fetcher = None
        else:
            # 显示账户信息
            detected_account = ibkr_fetcher.get_account_id()
            if detected_account:
                print(f"使用 IBKR 账户: {detected_account}")
                if detected_account.startswith('DU'):
                    print("  账户类型: 纸交易 (Paper Trading)")
                elif detected_account.startswith('U'):
                    print("  账户类型: 实盘 (Live Trading)")
            print("-" * 50)

    # Initialize Prometheus pusher
    pusher = PrometheusMetricsPusher(
        push_gateway_url=args.push_gateway,
        job_name=args.job_name
    )

    # Main loop
    iteration = 0
    try:
        while True:
            try:
                iteration += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                print(f"\n[{timestamp}] Iteration {iteration}")

                # Fetch Hyperliquid metrics
                print("Fetching metrics from Hyperliquid...")
                hl_metrics = hl_fetcher.get_all_metrics()

                # Fetch IBKR metrics
                ibkr_metrics = {"spot_bid": None, "spot_ask": None}
                if ibkr_fetcher:
                    # 检查市场时段（如果启用了仅常规交易时段）
                    should_fetch_ibkr = True
                    market_session = ibkr_fetcher.get_market_session()

                    if args.ibkr_regular_hours_only:
                        should_fetch_ibkr = (market_session == 'regular')
                        if not should_fetch_ibkr:
                            session_names = {
                                'pre_market': '盘前',
                                'after_hours': '盘后',
                                'closed': '休市'
                            }
                            print(f"Market session: {session_names.get(market_session, market_session)} - Skipping IBKR data (regular hours only mode)")

                    if should_fetch_ibkr:
                        session_indicator = ""
                        if market_session == 'pre_market':
                            session_indicator = " [盘前]"
                        elif market_session == 'after_hours':
                            session_indicator = " [盘后]"
                        elif market_session == 'regular':
                            session_indicator = " [盘中]"

                        print(f"Fetching metrics from IBKR...{session_indicator}")
                        ibkr_data = ibkr_fetcher.get_stock_price()
                        ibkr_metrics = {
                            "spot_bid": ibkr_data.get("bid"),
                            "spot_ask": ibkr_data.get("ask")
                        }

                # Merge metrics
                metrics = {**hl_metrics, **ibkr_metrics}

                # Display fetched metrics
                print("\nFetched metrics:")
                print(f"  Perp Bid:     ${metrics.get('perp_bid', 'N/A')}")
                print(f"  Perp Ask:     ${metrics.get('perp_ask', 'N/A')}")
                print(f"  Spot Bid:     ${metrics.get('spot_bid', 'N/A')}")
                print(f"  Spot Ask:     ${metrics.get('spot_ask', 'N/A')}")
                print(f"  Open:         ${metrics.get('open', 'N/A')}")
                print(f"  Close:        ${metrics.get('close', 'N/A')}")

                funding_rate = metrics.get('funding_rate')
                if funding_rate is not None:
                    print(f"  Funding Rate: {funding_rate * 100:.4f}%")
                else:
                    print(f"  Funding Rate: N/A")

                # Push to Prometheus
                print("\nPushing metrics to Prometheus...")
                success = pusher.update_and_push(metrics)

                if success:
                    print("✓ Successfully pushed metrics to Prometheus")
                else:
                    print("✗ Failed to push metrics to Prometheus")

                # Wait for next iteration
                print(f"\nWaiting {args.interval} seconds until next fetch...")
                time.sleep(args.interval)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\nError in main loop: {e}")
                print(f"Retrying in {args.interval} seconds...")
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\nReceived interrupt signal. Shutting down...")
    finally:
        # Cleanup
        if ibkr_fetcher:
            ibkr_fetcher.disconnect()

    print("\nData collector stopped.")


if __name__ == "__main__":
    main()
