"""Prometheus metrics pusher for Hyperliquid data."""

from typing import Dict, Optional
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


class PrometheusMetricsPusher:
    """Pushes Hyperliquid metrics to Prometheus Push Gateway."""

    def __init__(self, push_gateway_url: str, job_name: str = "hyperliquid_nvda"):
        """Initialize the Prometheus metrics pusher.

        Args:
            push_gateway_url: URL of the Prometheus Push Gateway (e.g., "localhost:9091")
            job_name: Job name for the metrics in Prometheus
        """
        self.push_gateway_url = push_gateway_url
        self.job_name = job_name
        self.registry = CollectorRegistry()

        # Define all metrics
        self.perp_bid_gauge = Gauge(
            "hyib_arb_perp_bid",
            "Perpetual contract bid price for NVDA",
            registry=self.registry
        )

        self.perp_ask_gauge = Gauge(
            "hyib_arb_perp_ask",
            "Perpetual contract ask price for NVDA",
            registry=self.registry
        )

        self.spot_bid_gauge = Gauge(
            "hyib_arb_spot_bid",
            "Spot market bid price for NVDA",
            registry=self.registry
        )

        self.spot_ask_gauge = Gauge(
            "hyib_arb_spot_ask",
            "Spot market ask price for NVDA",
            registry=self.registry
        )

        self.open_price_gauge = Gauge(
            "hyib_arb_open_price",
            "Open price for NVDA (from recent candle)",
            registry=self.registry
        )

        self.close_price_gauge = Gauge(
            "hyib_arb_close_price",
            "Close price for NVDA (from recent candle)",
            registry=self.registry
        )

        self.funding_rate_gauge = Gauge(
            "hyib_arb_funding_rate",
            "Funding rate for NVDA perpetual contract",
            registry=self.registry
        )

        # Additional computed metrics
        self.spread_gauge = Gauge(
            "hyib_arb_spread",
            "Spread between open and close prices",
            registry=self.registry
        )

        self.perp_mid_price_gauge = Gauge(
            "hyib_arb_perp_mid_price",
            "Mid price between perp bid and ask",
            registry=self.registry
        )

        self.spot_mid_price_gauge = Gauge(
            "hyib_arb_spot_mid_price",
            "Mid price between spot bid and ask",
            registry=self.registry
        )

    def update_metrics(self, metrics: Dict[str, Optional[float]]) -> None:
        """Update all metrics with new values.

        Args:
            metrics: Dictionary containing all metric values
        """
        # Update primary metrics
        if metrics.get("perp_bid") is not None:
            self.perp_bid_gauge.set(metrics["perp_bid"])

        if metrics.get("perp_ask") is not None:
            self.perp_ask_gauge.set(metrics["perp_ask"])

        if metrics.get("spot_bid") is not None:
            self.spot_bid_gauge.set(metrics["spot_bid"])

        if metrics.get("spot_ask") is not None:
            self.spot_ask_gauge.set(metrics["spot_ask"])

        if metrics.get("open") is not None:
            self.open_price_gauge.set(metrics["open"])

        if metrics.get("close") is not None:
            self.close_price_gauge.set(metrics["close"])

        if metrics.get("funding_rate") is not None:
            self.funding_rate_gauge.set(metrics["funding_rate"])

        # Calculate and update derived metrics
        # Spread between open and close
        if metrics.get("open") is not None and metrics.get("close") is not None:
            spread = metrics["close"] - metrics["open"]
            self.spread_gauge.set(spread)

        # Perp mid price
        if metrics.get("perp_bid") is not None and metrics.get("perp_ask") is not None:
            perp_mid = (metrics["perp_bid"] + metrics["perp_ask"]) / 2
            self.perp_mid_price_gauge.set(perp_mid)

        # Spot mid price
        if metrics.get("spot_bid") is not None and metrics.get("spot_ask") is not None:
            spot_mid = (metrics["spot_bid"] + metrics["spot_ask"]) / 2
            self.spot_mid_price_gauge.set(spot_mid)

    def push_metrics(self) -> bool:
        """Push metrics to Prometheus Push Gateway.

        Returns:
            True if push was successful, False otherwise
        """
        try:
            push_to_gateway(
                self.push_gateway_url,
                job=self.job_name,
                registry=self.registry
            )
            return True
        except Exception as e:
            print(f"Error pushing metrics to Prometheus: {e}")
            return False

    def update_and_push(self, metrics: Dict[str, Optional[float]]) -> bool:
        """Update metrics and push to gateway in one call.

        Args:
            metrics: Dictionary containing all metric values

        Returns:
            True if push was successful, False otherwise
        """
        self.update_metrics(metrics)
        return self.push_metrics()
