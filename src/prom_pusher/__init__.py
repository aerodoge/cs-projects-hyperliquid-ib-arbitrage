"""
Prometheus 指标推送模块

提供将数据推送到 Prometheus Push Gateway 的功能。
"""

from .pusher import PrometheusMetricsPusher

__all__ = ['PrometheusMetricsPusher']
