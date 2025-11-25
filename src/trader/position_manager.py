"""Position state management and persistence."""

from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
from pathlib import Path


class PositionStatus(Enum):
    """仓位状态."""
    OPEN = "open"      # 持仓中
    CLOSED = "closed"  # 已平仓
    ERROR = "error"    # 异常


@dataclass
class Position:
    """套利仓位信息."""
    # 仓位ID
    position_id: str

    # 交易对信息
    symbol: str          # 股票代码（如 "NVDA"）
    hl_symbol: str       # Hyperliquid 符号（如 "xyz:NVDA"）

    # 仓位数量
    quantity: float      # 持仓数量

    # 开仓信息
    entry_time: float            # 开仓时间戳
    entry_spread: float          # 开仓时价差
    entry_funding_rate: float    # 开仓时资金费率

    # IB 开仓价格
    ib_entry_price: float        # IB 买入价
    ib_order_id: Optional[int] = None

    # HL 开仓价格
    hl_entry_price: float        # HL 开空价
    hl_order_id: Optional[str] = None

    # 平仓信息（如果已平仓）
    exit_time: Optional[float] = None
    exit_spread: Optional[float] = None
    ib_exit_price: Optional[float] = None
    hl_exit_price: Optional[float] = None

    # 状态
    status: PositionStatus = PositionStatus.OPEN

    # 备注
    notes: str = ""

    def to_dict(self) -> Dict:
        """转换为字典."""
        d = asdict(self)
        d['status'] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        """从字典创建."""
        data['status'] = PositionStatus(data['status'])
        return cls(**data)

    def calculate_pnl(self) -> Optional[float]:
        """计算盈亏.

        Returns:
            盈亏金额（USD），None 表示仓位未平仓或数据不全
        """
        if self.status != PositionStatus.CLOSED:
            return None

        if not all([
            self.ib_entry_price, self.ib_exit_price,
            self.hl_entry_price, self.hl_exit_price
        ]):
            return None

        # IB 现货：买入成本 - 卖出收入
        ib_pnl = (self.ib_exit_price - self.ib_entry_price) * self.quantity

        # HL 永续：开空收入 - 平空成本
        hl_pnl = (self.hl_entry_price - self.hl_exit_price) * self.quantity

        # 总盈亏
        total_pnl = ib_pnl + hl_pnl

        return total_pnl


class PositionManager:
    """仓位管理器."""

    def __init__(self, data_file: str = "positions.json"):
        """初始化仓位管理器.

        Args:
            data_file: 仓位数据文件路径
        """
        self.data_file = Path(data_file)
        self.positions: Dict[str, Position] = {}

        # 通知回调（预留给 Slack 等）
        self.notification_callback: Optional[Callable] = None

        # 加载已有仓位
        self.load()

    def set_notification_callback(self, callback: Callable):
        """设置通知回调函数.

        Args:
            callback: 回调函数，签名为 callback(event_type: str, data: Dict)

        Example:
            def slack_notifier(event_type, data):
                if event_type == "position_opened":
                    send_slack_message(f"开仓: {data}")
                elif event_type == "position_closed":
                    send_slack_message(f"平仓: {data}")

            manager.set_notification_callback(slack_notifier)
        """
        self.notification_callback = callback

    def _notify(self, event_type: str, data: Dict):
        """触发通知（内部方法）."""
        if self.notification_callback:
            try:
                self.notification_callback(event_type, data)
            except Exception as e:
                print(f"Warning: Notification callback error: {e}")

    def add_position(self, position: Position):
        """添加新仓位.

        Args:
            position: 仓位对象
        """
        self.positions[position.position_id] = position
        self.save()

        # 触发通知
        self._notify("position_opened", {
            "position_id": position.position_id,
            "symbol": position.symbol,
            "quantity": position.quantity,
            "entry_spread": position.entry_spread,
            "ib_entry_price": position.ib_entry_price,
            "hl_entry_price": position.hl_entry_price,
        })

        print(f"✓ Position added: {position.position_id}")

    def close_position(
        self,
        position_id: str,
        ib_exit_price: float,
        hl_exit_price: float,
        exit_spread: float
    ):
        """平仓.

        Args:
            position_id: 仓位ID
            ib_exit_price: IB 卖出价
            hl_exit_price: HL 平空价
            exit_spread: 平仓时价差
        """
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")

        position = self.positions[position_id]
        position.exit_time = time.time()
        position.exit_spread = exit_spread
        position.ib_exit_price = ib_exit_price
        position.hl_exit_price = hl_exit_price
        position.status = PositionStatus.CLOSED

        self.save()

        # 计算盈亏
        pnl = position.calculate_pnl()

        # 触发通知
        self._notify("position_closed", {
            "position_id": position.position_id,
            "symbol": position.symbol,
            "quantity": position.quantity,
            "entry_spread": position.entry_spread,
            "exit_spread": exit_spread,
            "ib_entry_price": position.ib_entry_price,
            "ib_exit_price": ib_exit_price,
            "hl_entry_price": position.hl_entry_price,
            "hl_exit_price": hl_exit_price,
            "pnl": pnl,
        })

        print(f"✓ Position closed: {position_id}")
        if pnl is not None:
            print(f"  PnL: ${pnl:.2f}")

    def get_open_positions(self) -> List[Position]:
        """获取所有开仓中的仓位.

        Returns:
            开仓仓位列表
        """
        return [
            pos for pos in self.positions.values()
            if pos.status == PositionStatus.OPEN
        ]

    def get_position(self, position_id: str) -> Optional[Position]:
        """获取指定仓位.

        Args:
            position_id: 仓位ID

        Returns:
            仓位对象，如果不存在返回 None
        """
        return self.positions.get(position_id)

    def save(self):
        """保存仓位数据到文件."""
        try:
            data = {
                pid: pos.to_dict()
                for pid, pos in self.positions.items()
            }

            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error saving positions: {e}")

    def load(self):
        """从文件加载仓位数据."""
        if not self.data_file.exists():
            return

        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)

            self.positions = {
                pid: Position.from_dict(pos_data)
                for pid, pos_data in data.items()
            }

            print(f"✓ Loaded {len(self.positions)} positions from {self.data_file}")

        except Exception as e:
            print(f"Error loading positions: {e}")

    def get_statistics(self) -> Dict:
        """获取仓位统计信息.

        Returns:
            统计信息字典
        """
        open_positions = self.get_open_positions()
        closed_positions = [
            pos for pos in self.positions.values()
            if pos.status == PositionStatus.CLOSED
        ]

        # 计算总盈亏
        total_pnl = sum(
            pos.calculate_pnl() or 0
            for pos in closed_positions
        )

        return {
            "total_positions": len(self.positions),
            "open_positions": len(open_positions),
            "closed_positions": len(closed_positions),
            "total_pnl": total_pnl,
        }
