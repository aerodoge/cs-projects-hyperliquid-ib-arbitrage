"""Main trading program with automated arbitrage execution."""

import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

from hl_fetcher.fetcher_streaming import HyperliquidFetcherStreaming
from ib_fetcher.fetcher_streaming import IBKRFetcherStreaming
from trader.strategy import ArbitrageStrategy, MarketData, SignalType
from trader.ib_trader import IBTrader
from trader.hl_trader import HLTrader
from trader.executor import TradeExecutor
from trader.position_manager import PositionManager
from trader.config import StrategyConfig


def main():
    """Main trading loop."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Hyperliquid-IB Arbitrage Trading Bot"
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
        type=float,
        default=float(os.getenv("FETCH_INTERVAL", "5")),
        help="Check interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--enable-trading",
        action="store_true",
        default=os.getenv("ENABLE_TRADING", "false").lower() == "true",
        help="Enable automated trading (default: false, monitor only)"
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        default=os.getenv("USE_TESTNET", "false").lower() == "true",
        help="Use Hyperliquid testnet (default: false)"
    )
    parser.add_argument(
        "--ibkr-host",
        type=str,
        default=os.getenv("IBKR_HOST", "127.0.0.1"),
        help="IBKR host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--ibkr-port",
        type=int,
        default=int(os.getenv("IBKR_PORT", "7497")),
        help="IBKR port (default: 7497 for TWS paper)"
    )

    args = parser.parse_args()

    # Initialize strategy configuration
    config = StrategyConfig()

    # Load config from environment variables
    if threshold := os.getenv("OPEN_SPREAD_THRESHOLD"):
        config.open_spread_threshold = float(threshold)
    if min_funding := os.getenv("MIN_FUNDING_RATE"):
        config.min_funding_rate = float(min_funding)
    if position_size := os.getenv("POSITION_SIZE"):
        config.position_size = int(position_size)
    if max_positions := os.getenv("MAX_POSITIONS"):
        config.max_positions = int(max_positions)

    print("=" * 70)
    print("Hyperliquid-IB Arbitrage Trading Bot")
    print("=" * 70)
    print(f"Symbol: {args.stock_symbol} ({args.symbol})")
    print(f"Mode: {'LIVE TRADING' if args.enable_trading else 'MONITOR ONLY'}")
    print(f"Network: {'TESTNET' if args.testnet else 'MAINNET'}")
    print(f"Check Interval: {args.interval}s")
    print("\nStrategy Configuration:")
    print(f"  Open Spread Threshold: {config.open_spread_threshold*100:.2f}%")
    print(f"  Min Funding Rate: {config.min_funding_rate*100:.4f}%")
    print(f"  Position Size: {config.position_size} shares")
    print(f"  Max Positions: {config.max_positions}")
    print("=" * 70)

    if not args.enable_trading:
        print("\n⚠️  MONITOR MODE - No trades will be executed")
        print("Set ENABLE_TRADING=true or use --enable-trading to enable trading\n")

    # Initialize components
    print("\nInitializing components...")

    # 1. Data fetchers
    hl_fetcher = HyperliquidFetcherStreaming(
        symbol=args.symbol,
        use_testnet=args.testnet,
        perp_dexs=["xyz"]
    )

    ib_fetcher = IBKRFetcherStreaming(
        symbol=args.stock_symbol,
        host=args.ibkr_host,
        port=args.ibkr_port,
        client_id=1  # Data fetcher uses client_id=1
    )

    if not ib_fetcher.connect():
        print("❌ Failed to connect to IBKR")
        return

    # 2. Strategy
    strategy = ArbitrageStrategy(config)

    # 3. Trading components (only if trading enabled)
    executor = None
    position_manager = None

    if args.enable_trading:
        # Check for private key
        private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
        if not private_key:
            print("❌ HYPERLIQUID_PRIVATE_KEY not set in .env file")
            print("Trading mode requires a private key")
            ib_fetcher.disconnect()
            return

        # Position manager
        position_data_file = os.getenv("POSITION_DATA_FILE", "positions.json")
        position_manager = PositionManager(position_data_file)

        # Trading interfaces
        ib_trader = IBTrader(
            host=args.ibkr_host,
            port=args.ibkr_port,
            client_id=2  # Trader uses different client_id
        )

        hl_trader = HLTrader(
            private_key=private_key,
            use_testnet=args.testnet,
            perp_dexs=["xyz"]
        )

        # Connect traders
        if not ib_trader.connect():
            print("❌ Failed to connect IB Trader")
            ib_fetcher.disconnect()
            return

        if not hl_trader.connect():
            print("❌ Failed to connect HL Trader")
            ib_trader.disconnect()
            ib_fetcher.disconnect()
            return

        # Executor
        executor = TradeExecutor(
            ib_trader=ib_trader,
            hl_trader=hl_trader,
            position_manager=position_manager,
            symbol=args.stock_symbol,
            hl_symbol=args.symbol
        )

        print("✓ Trading components initialized")

        # Display existing positions
        open_positions = position_manager.get_open_positions()
        if open_positions:
            print(f"\n📊 Found {len(open_positions)} open position(s):")
            for pos in open_positions:
                print(f"  - {pos.position_id}: {pos.quantity} shares @ spread {pos.entry_spread*100:.4f}%")

    print("\n" + "=" * 70)
    print("Starting main loop...")
    print("=" * 70)

    # Main loop
    iteration = 0
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n[{timestamp}] Iteration {iteration}")

            # Fetch market data
            hl_metrics = hl_fetcher.get_all_metrics()
            ib_data = ib_fetcher.get_stock_price()

            # Create MarketData object
            market_data = MarketData(
                perp_bid=hl_metrics.get("perp_bid"),
                perp_ask=hl_metrics.get("perp_ask"),
                funding_rate=hl_metrics.get("funding_rate"),
                spot_bid=ib_data.get("bid"),
                spot_ask=ib_data.get("ask"),
                timestamp=time.time()
            )

            # Display current prices
            print(f"  Perp Bid:     ${market_data.perp_bid if market_data.perp_bid else 'N/A'}")
            print(f"  Perp Ask:     ${market_data.perp_ask if market_data.perp_ask else 'N/A'}")
            print(f"  Spot Bid:     ${market_data.spot_bid if market_data.spot_bid else 'N/A'}")
            print(f"  Spot Ask:     ${market_data.spot_ask if market_data.spot_ask else 'N/A'}")
            if market_data.funding_rate is not None:
                print(f"  Funding Rate: {market_data.funding_rate:.10f} (raw) = {market_data.funding_rate*100:.8f}%")

            # Calculate opening spread (for new positions)
            open_analysis = strategy.calculate_spread(market_data)

            if open_analysis.is_valid:
                print(f"\n  💹 Open Spread Analysis:")
                print(f"    IB Buy Price:  ${open_analysis.ib_buy_price:.2f}")
                print(f"    HL Sell Price: ${open_analysis.hl_sell_price:.2f}")
                print(f"    Open Spread: {open_analysis.spread*100:+.4f}%")

                # Check signals
                if args.enable_trading and executor and position_manager:
                    # Check for close signals first
                    open_positions = position_manager.get_open_positions()
                    if open_positions:
                        # Calculate closing spread (for existing positions)
                        close_analysis = strategy.calculate_close_spread(market_data)

                        if close_analysis.is_valid:
                            print(f"  💹 Close Spread: {close_analysis.spread*100:+.4f}%")

                            for pos in open_positions:
                                close_signal, close_reason = strategy.get_close_signal(
                                    close_analysis,
                                    pos.entry_spread
                                )

                                if close_signal == SignalType.CLOSE_POSITION:
                                    print(f"\n  🔔 CLOSE SIGNAL: {close_reason}")
                                    print(f"  Closing position {pos.position_id}...")
                                    executor.close_arbitrage_position(pos.position_id, market_data)
                        else:
                            print(f"  ⚠️  Cannot check close signals: {close_analysis.reason}")

                    # Check for open signals (if under max positions)
                    if len(open_positions) < config.max_positions:
                        open_signal, open_reason = strategy.get_open_signal(open_analysis)

                        if open_signal == SignalType.OPEN_LONG_SPOT_SHORT_PERP:
                            print(f"\n  🔔 OPEN SIGNAL: {open_reason}")
                            print(f"  Opening arbitrage position...")
                            executor.open_arbitrage_position(
                                config.position_size,
                                open_analysis
                            )
                else:
                    # Monitor mode - just show signals
                    open_signal, open_reason = strategy.get_open_signal(open_analysis)
                    if open_signal != SignalType.NONE:
                        print(f"\n  📢 Signal detected: {open_signal.value}")
                        print(f"     {open_reason}")
                        print(f"     (MONITOR MODE - no trade executed)")

            else:
                print(f"\n  ⚠️  Invalid data: {open_analysis.reason}")

            # Sleep
            print(f"\nWaiting {args.interval}s...")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down...")
    finally:
        # Cleanup
        print("\nCleaning up...")
        ib_fetcher.disconnect()
        hl_fetcher.close()

        if args.enable_trading and executor:
            executor.ib_trader.disconnect()
            print("Trading connections closed")

        # Display final statistics
        if position_manager:
            stats = position_manager.get_statistics()
            print("\n" + "=" * 70)
            print("Session Statistics:")
            print(f"  Total Positions: {stats['total_positions']}")
            print(f"  Open Positions: {stats['open_positions']}")
            print(f"  Closed Positions: {stats['closed_positions']}")
            print(f"  Total PnL: ${stats['total_pnl']:.2f}")
            print("=" * 70)

    print("\n✓ Trading bot stopped")


if __name__ == "__main__":
    main()
