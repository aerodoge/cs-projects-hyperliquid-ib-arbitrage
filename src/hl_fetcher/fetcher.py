"""Hyperliquid data fetcher for NVDA stock metrics."""

from typing import Dict, Optional
from hyperliquid.info import Info
from hyperliquid.utils import constants


class HyperliquidFetcher:
    """Fetches market data from Hyperliquid exchange."""

    def __init__(self, symbol: str = "xyz:NVDA", use_testnet: bool = False, perp_dexs: list = None):
        """Initialize the Hyperliquid data fetcher.

        Args:
            symbol: The trading symbol to fetch data for (e.g., "xyz:NVDA" for TradeXYZ NVDA)
            use_testnet: Whether to use testnet or mainnet
            perp_dexs: List of perp DEXs to initialize (e.g., ["xyz"] for TradeXYZ)
        """
        self.symbol = symbol
        base_url = constants.TESTNET_API_URL if use_testnet else constants.MAINNET_API_URL

        # Default to xyz DEX if not specified
        if perp_dexs is None:
            perp_dexs = ["xyz"]

        self.info = Info(base_url, skip_ws=True, perp_dexs=perp_dexs)

    def get_orderbook_prices(self) -> Dict[str, Optional[float]]:
        """Get best bid/ask prices from the orderbook.

        Returns:
            Dictionary containing perp_bid and perp_ask prices
        """
        try:
            l2_data = self.info.l2_snapshot(self.symbol)

            # L2 book structure: levels[0] = bids, levels[1] = asks
            # Each level is a list of {px: price, sz: size, n: number}
            levels = l2_data.get("levels", [[], []])

            perp_bid = None
            perp_ask = None

            # Get best bid (highest buy price)
            if levels[0] and len(levels[0]) > 0:
                perp_bid = float(levels[0][0]["px"])

            # Get best ask (lowest sell price)
            if levels[1] and len(levels[1]) > 0:
                perp_ask = float(levels[1][0]["px"])

            return {
                "perp_bid": perp_bid,
                "perp_ask": perp_ask
            }
        except Exception as e:
            print(f"Error fetching orderbook: {e}")
            return {"perp_bid": None, "perp_ask": None}

    def get_spot_prices(self) -> Dict[str, Optional[float]]:
        """Get spot market prices.

        Note: For xyz:NVDA, spot market doesn't exist. This returns None values.
        The perp mid price can be used as a proxy if needed.

        Returns:
            Dictionary containing spot_bid and spot_ask prices (None for xyz:NVDA)
        """
        # xyz:NVDA is a perp contract, not spot
        # Return None values as spot market doesn't exist
        return {"spot_bid": None, "spot_ask": None}

    def get_spread_prices(self) -> Dict[str, Optional[float]]:
        """Get open and close prices from recent candles.

        Returns:
            Dictionary containing open and close prices
        """
        try:
            import time

            # Get 1 minute candle for the last hour
            end_time = int(time.time() * 1000)
            start_time = end_time - 3600000  # 1 hour ago

            candles = self.info.candles_snapshot(
                self.symbol,
                interval="1m",
                startTime=start_time,
                endTime=end_time
            )

            if candles and len(candles) > 0:
                # Get the most recent candle
                latest_candle = candles[-1]

                return {
                    "open": float(latest_candle["o"]),
                    "close": float(latest_candle["c"])
                }

            return {"open": None, "close": None}
        except Exception as e:
            print(f"Error fetching spread prices: {e}")
            return {"open": None, "close": None}

    def get_funding_rate(self) -> Optional[float]:
        """Get current funding rate for the perpetual contract.

        Returns:
            Current funding rate as a float (e.g., 0.0001 for 0.01%)
        """
        try:
            import time

            # Get funding history for the last 24 hours
            end_time = int(time.time() * 1000)
            start_time = end_time - 86400000  # 24 hours ago

            funding_history = self.info.funding_history(
                self.symbol,
                startTime=start_time,
                endTime=end_time
            )

            if funding_history and len(funding_history) > 0:
                # Get the most recent funding rate
                latest_funding = funding_history[-1]
                funding_rate_str = latest_funding.get("fundingRate")
                if funding_rate_str:
                    return float(funding_rate_str)

            return None
        except Exception as e:
            print(f"Error fetching funding rate: {e}")
            return None

    def get_all_metrics(self) -> Dict[str, any]:
        """Fetch all metrics at once.

        Returns:
            Dictionary containing all market metrics
        """
        orderbook = self.get_orderbook_prices()
        spot = self.get_spot_prices()
        spread = self.get_spread_prices()
        funding_rate = self.get_funding_rate()

        return {
            "perp_bid": orderbook["perp_bid"],
            "perp_ask": orderbook["perp_ask"],
            "spot_bid": spot["spot_bid"],
            "spot_ask": spot["spot_ask"],
            "open": spread["open"],
            "close": spread["close"],
            "funding_rate": funding_rate
        }
