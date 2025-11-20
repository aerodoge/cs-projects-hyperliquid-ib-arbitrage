"""
Interactive Brokers 数据获取模块

提供从 Interactive Brokers 获取实时股票数据的功能。
"""

from .fetcher import IBKRFetcher

__all__ = ['IBKRFetcher']
