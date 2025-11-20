# 交易功能架构设计

本文档为未来添加交易功能提供架构设计和实现指南。

**当前状态：** 系统设计为监控和分析工具，不包含交易功能。
**未来扩展：** 可以基于此架构添加自动交易功能。

---

## 📋 目录

- [当前架构](#当前架构)
- [交易功能设计](#交易功能设计)
- [风险管理](#风险管理)
- [实现路线图](#实现路线图)
- [配置示例](#配置示例)
- [安全考虑](#安全考虑)

---

## 当前架构

### 系统组件

```
┌─────────────────┐      ┌─────────────────┐
│  Hyperliquid    │      │  Interactive    │
│  (Perpetuals)   │      │  Brokers (Spot) │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │  Fetch Price Data      │  Fetch Price Data
         ▼                        ▼
    ┌────────────────────────────────┐
    │      Data Collection Layer     │
    │      ├─ hl_fetcher/            │
    │      └─ ib_fetcher/            │
    └──────────────┬─────────────────┘
                   │
                   ▼
    ┌─────────────────────────────┐
    │  Analysis & Monitoring      │
    │  - Calculate arbitrage      │
    │  - Track funding rate       │
    │  - Monitor basis            │
    └──────────────┬──────────────┘
                   │
                   ▼
    ┌─────────────────────────────┐
    │  Prometheus Push Gateway    │
    │  (Time Series Metrics)      │
    └─────────────────────────────┘
```

### 当前功能

✅ **数据采集**

- Hyperliquid 永续合约价格
- IBKR 股票现货价格
- 资金费率和基差

✅ **分析监控**

- 套利机会识别
- 价差计算
- 实时指标推送

❌ **交易执行**（未实现）

- 自动下单
- 持仓管理
- 风险控制

---

## 交易功能设计

### 建议架构

```
                    ┌─────────────────┐
                    │  Main Trading   │
                    │     Loop        │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Signal     │ │   Strategy   │ │     Risk     │
    │  Generator   │ │   Manager    │ │   Manager    │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           └────────────────┼────────────────┘
                            ▼
               ┌─────────────────────────────┐
               │    Order Execution Layer    │
               │  ├─ Order Builder           │
               │  ├─ Order Validator         │
               │  └─ Order Tracker           │
               └──────────┬──────────────────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
        ┌─────────────────┐      ┌─────────────────┐
        │  Hyperliquid    │      │  Interactive    │
        │  Trading API    │      │  Brokers API    │
        └─────────────────┘      └─────────────────┘
```

### 模块设计

#### 1. 信号生成器 (Signal Generator)

```python
# src/signals/arbitrage_signal.py
class ArbitrageSignalGenerator:
    """生成套利交易信号"""

    def __init__(self, threshold: float = 0.001):
        self.threshold = threshold  # 最小价差阈值

    def generate_signal(self, perp_price, spot_price, funding_rate):
        """
        生成交易信号

        Returns:
            {
                'action': 'long_spot' | 'long_perp' | 'close' | 'hold',
                'confidence': float,
                'expected_profit': float
            }
        """
        # 计算基差
        basis = (perp_price - spot_price) / spot_price

        # 考虑手续费和资金费率
        total_cost = self._calculate_costs(funding_rate)

        if basis > self.threshold + total_cost:
            return {
                'action': 'long_spot',  # 买现货，卖永续
                'confidence': min(basis / 0.01, 1.0),
                'expected_profit': basis - total_cost
            }
        elif basis < -self.threshold - total_cost:
            return {
                'action': 'long_perp',  # 买永续，卖现货
                'confidence': min(abs(basis) / 0.01, 1.0),
                'expected_profit': abs(basis) - total_cost
            }
        else:
            return {
                'action': 'hold',
                'confidence': 0.0,
                'expected_profit': 0.0
            }
```

#### 2. 策略管理器 (Strategy Manager)

```python
# src/strategies/arbitrage_strategy.py
class ArbitrageStrategy:
    """套利策略管理"""

    def __init__(self, signal_generator, risk_manager):
        self.signal_generator = signal_generator
        self.risk_manager = risk_manager
        self.positions = {}  # 持仓记录

    def on_tick(self, market_data):
        """每次价格更新时调用"""
        # 1. 生成信号
        signal = self.signal_generator.generate_signal(
            perp_price=market_data['perp_ask'],
            spot_price=market_data['spot_ask'],
            funding_rate=market_data['funding_rate']
        )

        # 2. 风险检查
        if not self.risk_manager.check_signal(signal, self.positions):
            return None

        # 3. 生成订单
        if signal['action'] != 'hold':
            return self._create_orders(signal, market_data)

        return None

    def _create_orders(self, signal, market_data):
        """根据信号创建订单"""
        if signal['action'] == 'long_spot':
            return [
                {'side': 'BUY', 'symbol': 'NVDA', 'exchange': 'IBKR'},
                {'side': 'SELL', 'symbol': 'xyz:NVDA', 'exchange': 'Hyperliquid'}
            ]
        # ... 其他情况
```

#### 3. 风险管理器 (Risk Manager)

```python
# src/risk/risk_manager.py
class RiskManager:
    """风险管理和控制"""

    def __init__(self, config):
        self.max_position_size = config.get('max_position_size', 10000)
        self.max_daily_loss = config.get('max_daily_loss', 500)
        self.max_leverage = config.get('max_leverage', 3.0)
        self.current_pnl = 0.0

    def check_signal(self, signal, positions):
        """检查信号是否符合风险要求"""
        # 1. 检查置信度
        if signal['confidence'] < 0.5:
            return False

        # 2. 检查每日亏损限制
        if self.current_pnl < -self.max_daily_loss:
            print("⚠ 达到每日最大亏损限制")
            return False

        # 3. 检查仓位大小
        total_position = sum(p['size'] for p in positions.values())
        if total_position >= self.max_position_size:
            print("⚠ 达到最大仓位限制")
            return False

        return True

    def validate_order(self, order):
        """验证订单是否安全"""
        # 检查订单大小、价格合理性等
        pass
```

#### 4. 订单执行器 (Order Executor)

```python
# src/execution/order_executor.py
class OrderExecutor:
    """订单执行和跟踪"""

    def __init__(self, hl_trader, ibkr_trader):
        self.hl_trader = hl_trader
        self.ibkr_trader = ibkr_trader
        self.active_orders = {}

    def execute_orders(self, orders):
        """执行一组订单"""
        results = []

        for order in orders:
            if order['exchange'] == 'Hyperliquid':
                result = self._execute_hl_order(order)
            elif order['exchange'] == 'IBKR':
                result = self._execute_ibkr_order(order)

            results.append(result)

        return results

    def _execute_hl_order(self, order):
        """在 Hyperliquid 执行订单"""
        # 实现 Hyperliquid 下单逻辑
        pass

    def _execute_ibkr_order(self, order):
        """在 IBKR 执行订单"""
        # 实现 IBKR 下单逻辑
        pass
```

---

## 风险管理

### 必须实现的安全措施

#### 1. 仓位限制

```python
# 配置示例
risk_config = {
    'max_position_size': 10000,  # 最大仓位（USD）
    'max_position_per_trade': 2000,  # 单笔最大金额
    'max_leverage': 3.0,  # 最大杠杆
}
```

#### 2. 损失限制

```python
# 每日损失限制
daily_loss_limit = 500  # USD

# 单笔损失限制
max_loss_per_trade = 100  # USD

# 止损价格
stop_loss_pct = 0.02  # 2%
```

#### 3. 价格偏离保护

```python
def check_price_deviation(current_price, reference_price, max_deviation=0.05):
    """检查价格是否偏离过大"""
    deviation = abs(current_price - reference_price) / reference_price
    if deviation > max_deviation:
        raise ValueError(f"价格偏离过大: {deviation * 100:.2f}%")
```

#### 4. 订单确认机制

```python
# 高风险操作需要确认
if order_value > 5000:
    confirmation = input(f"确认执行 ${order_value} 订单? (yes/no): ")
    if confirmation.lower() != 'yes':
        return False
```

---

## 实现路线图

### 阶段 1: 基础架构 ✅（已完成）

- [x] 数据采集框架
- [x] IBKR 连接和账户管理
- [x] Prometheus 集成
- [x] 市场时段检测

### 阶段 2: 交易基础设施（建议）

- [ ] 创建 Hyperliquid 交易模块
- [ ] 扩展 IBKR 下单功能
- [ ] 实现订单状态跟踪
- [ ] 添加持仓管理

### 阶段 3: 策略实现（建议）

- [ ] 实现套利信号生成器
- [ ] 实现基础套利策略
- [ ] 添加回测框架
- [ ] 纸交易测试

### 阶段 4: 风险管理（必需）

- [ ] 实现风险管理器
- [ ] 添加止损止盈
- [ ] 实现资金管理
- [ ] 添加告警系统

### 阶段 5: 生产部署（建议）

- [ ] 完整的日志系统
- [ ] 监控和告警
- [ ] 灾难恢复
- [ ] 合规审计

---

## 配置示例

### 交易配置

```bash
# .env - 交易模式配置

# =================
# 基础配置
# =================
SYMBOL=xyz:NVDA
STOCK_SYMBOL=NVDA

# =================
# IBKR 配置
# =================
IBKR_HOST=127.0.0.1
IBKR_PORT=7497                    # 纸交易
IBKR_ACCOUNT_ID=DU1234567         # 你的账户ID
IBKR_CLIENT_ID=1

# =================
# 交易功能（未来）
# =================
TRADING_ENABLED=false             # 启用交易功能
TRADING_MODE=paper                # paper | live

# =================
# 风险管理
# =================
MAX_POSITION_SIZE=10000           # 最大仓位（USD）
MAX_POSITION_PER_TRADE=2000       # 单笔最大
MAX_DAILY_LOSS=500                # 每日最大亏损
MAX_LEVERAGE=3.0                  # 最大杠杆
STOP_LOSS_PCT=0.02                # 止损百分比

# =================
# 策略参数
# =================
ARB_THRESHOLD=0.001               # 最小套利阈值
MIN_PROFIT_PCT=0.002              # 最小利润率
FUNDING_RATE_WEIGHT=0.5           # 资金费率权重
```

---

## 安全考虑

### ⚠️ 警告

在实施交易功能之前，必须考虑：

#### 1. 测试要求

```
✅ 必须先在纸交易测试
✅ 小额实盘验证
✅ 完整的回测
✅ 压力测试
```

#### 2. 合规要求

```
✅ 了解交易规则
✅ 风险披露
✅ 可能需要许可
✅ 税务申报
```

#### 3. 技术要求

```
✅ 完整的日志
✅ 错误处理
✅ 断线重连
✅ 数据备份
```

#### 4. 资金安全

```
✅ 使用 Read-Only API（监控时）
✅ 限制 API 权限
✅ 启用 2FA
✅ 定期审计
```

### 建议的安全检查清单

- [ ] 在纸交易账户测试至少 1 个月
- [ ] 实现完整的风险管理系统
- [ ] 添加紧急停止机制
- [ ] 设置实时告警
- [ ] 备份所有配置和数据
- [ ] 编写详细的操作文档
- [ ] 进行灾难恢复演练
- [ ] 咨询专业人士（法律、财务）

---

## 代码示例

### 完整的交易流程示例

```python
# trading_main.py (未来实现)
from signals import ArbitrageSignalGenerator
from strategies import ArbitrageStrategy
from risk import RiskManager
from execution import OrderExecutor


def main():
    # 1. 初始化组件
    signal_gen = ArbitrageSignalGenerator(threshold=0.001)
    risk_mgr = RiskManager(config=risk_config)
    strategy = ArbitrageStrategy(signal_gen, risk_mgr)
    executor = OrderExecutor(hl_trader, ibkr_trader)

    # 2. 主循环
    while True:
        # 获取市场数据
        market_data = get_market_data()

        # 生成交易信号
        signal = strategy.on_tick(market_data)

        if signal:
            # 风险检查
            if risk_mgr.check_signal(signal, positions):
                # 执行订单
                orders = strategy.create_orders(signal)
                results = executor.execute_orders(orders)

                # 记录结果
                log_trade_results(results)

        time.sleep(interval)
```

---

## 下一步

### 如果要开始实现交易功能：

1. **先在纸交易环境测试**
   ```bash
   IBKR_PORT=7497  # TWS 纸交易
   IBKR_ACCOUNT_ID=DU1234567
   TRADING_MODE=paper
   ```

2. **实现基础订单功能**
    - 从简单的市价单开始
    - 添加订单状态跟踪
    - 实现基本的错误处理

3. **建立风险管理**
    - 实现仓位限制
    - 添加止损功能
    - 设置告警系统

4. **充分测试**
    - 至少纸交易 30 天
    - 验证所有边界情况
    - 压力测试

5. **小额实盘验证**
    - 使用最小仓位
    - 密切监控
    - 逐步增加

---

## 参考资源

- [Hyperliquid Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [IB-Insync 文档](https://ib-insync.readthedocs.io/)
- [IBKR API 文档](https://interactivebrokers.github.io/tws-api/)

---

**重要提示：**

本文档仅供参考，实际实施前请：

1. 充分了解交易风险
2. 咨询专业顾问
3. 在纸交易环境充分测试
4. 遵守所有相关法律法规

---

**文档版本：** 1.0
**最后更新：** 2025-11-20
**状态：** 架构设计阶段
