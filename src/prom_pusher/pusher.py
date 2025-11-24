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

    def _is_valid_price(self, value: Optional[float]) -> bool:
        """验证价格数据是否有效（非空且非负）.

        Args:
            value: 价格值

        Returns:
            True if valid, False otherwise
        """
        return value is not None and value >= 0

    def update_metrics(self, metrics: Dict[str, Optional[float]]) -> None:
        """Update all metrics with new values.

        Args:
            metrics: Dictionary containing all metric values

        Note:
            价格数据小于 0 的会被过滤掉不推送
            Funding rate 可以为负数，不过滤
        """
        # Update primary metrics (价格类数据需要验证非负)
        if self._is_valid_price(metrics.get("perp_bid")):
            self.perp_bid_gauge.set(metrics["perp_bid"])

        if self._is_valid_price(metrics.get("perp_ask")):
            self.perp_ask_gauge.set(metrics["perp_ask"])

        if self._is_valid_price(metrics.get("spot_bid")):
            self.spot_bid_gauge.set(metrics["spot_bid"])

        if self._is_valid_price(metrics.get("spot_ask")):
            self.spot_ask_gauge.set(metrics["spot_ask"])

        if self._is_valid_price(metrics.get("open")):
            self.open_price_gauge.set(metrics["open"])

        if self._is_valid_price(metrics.get("close")):
            self.close_price_gauge.set(metrics["close"])

        # Funding rate 可以为负数，只检查非空
        if metrics.get("funding_rate") is not None:
            self.funding_rate_gauge.set(metrics["funding_rate"])

        # Calculate and update derived metrics (也需要验证有效性)
        # Spread between open and close
        if self._is_valid_price(metrics.get("open")) and self._is_valid_price(metrics.get("close")):
            spread = metrics["close"] - metrics["open"]
            self.spread_gauge.set(spread)

        # Perp mid price
        if self._is_valid_price(metrics.get("perp_bid")) and self._is_valid_price(metrics.get("perp_ask")):
            perp_mid = (metrics["perp_bid"] + metrics["perp_ask"]) / 2
            self.perp_mid_price_gauge.set(perp_mid)

        # Spot mid price
        if self._is_valid_price(metrics.get("spot_bid")) and self._is_valid_price(metrics.get("spot_ask")):
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
