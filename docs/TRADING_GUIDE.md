# 交易功能使用指南

## 快速开始

### 1. 环境准备

#### 配置文件

复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

#### 必填配置项（Paper Trading）:

```bash
# IB Paper Trading
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # TWS Paper Trading 端口

# Hyperliquid Testnet
USE_TESTNET=true
HYPERLIQUID_PRIVATE_KEY=0x你的测试网私钥

# 启用交易
ENABLE_TRADING=true

# 策略参数（建议从保守值开始）
OPEN_SPREAD_THRESHOLD=0.002   # 0.2% 开仓阈值
MIN_FUNDING_RATE=0.0001       # 0.01% 最小资金费率
POSITION_SIZE=10              # 从小仓位开始测试
MAX_POSITIONS=1               # 最多1个仓位
```

### 2. 获取 Hyperliquid Testnet 私钥

1. 访问 https://app.hyperliquid-testnet.xyz
2. 连接钱包
3. 在设置中导出私钥
4. 复制到 `.env` 文件中的 `HYPERLIQUID_PRIVATE_KEY`

⚠️ **重要**: 测试网私钥与主网不同，不要混用！

### 3. 启动 IB TWS/Gateway

#### 使用 Docker 运行 IB Gateway (Paper Trading):

```bash
docker run -d \
  --name ib-gateway \
  -p 4002:4002 \
  -e TWS_USERID=your_username \
  -e TWS_PASSWORD=your_password \
  -e TRADING_MODE=paper \
  ghcr.io/unusualalpha/ib-gateway:latest
```

或使用本地 TWS:
- 打开 IB TWS (Paper Trading)
- API Settings -> Enable ActiveX and Socket Clients
- Socket port: 7497

## 运行模式

### 监控模式（不交易，只显示信号）

```bash
python src/main_trading.py
```

输出示例：
```
[2025-11-24 12:00:00] Iteration 1
  Perp Bid:     $180.50
  Perp Ask:     $180.51
  Spot Bid:     $180.30
  Spot Ask:     $180.32

  💹 Spread Analysis:
    IB Buy Price:  $180.32
    HL Sell Price: $180.50
    Spread: +0.0998%

  📢 Signal detected: open_long_spot_short_perp
     Spread 0.0998% > 0.1000%, Funding 0.0200% > 0.0100%
     (MONITOR MODE - no trade executed)
```

### 交易模式（自动执行）

```bash
python src/main_trading.py --enable-trading
```

或在 `.env` 中设置 `ENABLE_TRADING=true`

## 交易流程

### 开仓流程

当满足以下条件时自动开仓：
1. 价差 > `OPEN_SPREAD_THRESHOLD` (默认 0.1%)
2. 资金费率 > `MIN_FUNDING_RATE` (默认 0.01%)
3. 当前持仓数 < `MAX_POSITIONS`

执行步骤：
```
[1/2] Buying spot on IB...
✅ IB order filled: 100 @ $180.32

[2/2] Opening short on Hyperliquid...
✅ HL order filled: 100 @ $180.50

✅ Arbitrage position opened: pos_1732435200_abc123
```

### 平仓流程

当满足以下任一条件时自动平仓：
1. 价差收敛 < `CLOSE_SPREAD_THRESHOLD` (默认 0.05%)
2. 价差反转 < `REVERSE_SPREAD_THRESHOLD` (默认 -0.1%)
3. 资金费率反转 < -0.01%

执行步骤：
```
[1/2] Selling spot on IB...
✅ IB sell filled: 100 @ $180.40

[2/2] Closing short on Hyperliquid...
✅ HL close filled: 100 @ $180.42

✅ Arbitrage position closed: pos_1732435200_abc123
  PnL: $8.00
```

## 仓位管理

### 查看持仓

仓位数据保存在 `positions.json` 文件中（可配置）：

```json
{
  "pos_1732435200_abc123": {
    "position_id": "pos_1732435200_abc123",
    "symbol": "NVDA",
    "hl_symbol": "xyz:NVDA",
    "quantity": 100,
    "entry_time": 1732435200.0,
    "entry_spread": 0.001,
    "entry_funding_rate": 0.0002,
    "ib_entry_price": 180.32,
    "hl_entry_price": 180.50,
    "status": "open"
  }
}
```

### 统计信息

程序退出时会显示统计：
```
Session Statistics:
  Total Positions: 5
  Open Positions: 1
  Closed Positions: 4
  Total PnL: $125.50
```

## Slack 通知（预留接口）

代码已预留通知接口，将来可以轻松接入 Slack：

```python
from trader.position_manager import PositionManager

def slack_notifier(event_type, data):
    if event_type == "position_opened":
        send_slack_message(f"🟢 开仓: {data['symbol']} x{data['quantity']}")
    elif event_type == "position_closed":
        pnl = data.get('pnl', 0)
        emoji = "🟢" if pnl > 0 else "🔴"
        send_slack_message(f"{emoji} 平仓: PnL ${pnl:.2f}")

# 设置回调
position_manager = PositionManager()
position_manager.set_notification_callback(slack_notifier)
```

## 风险控制

### 内置风控

- ✅ 最大持仓数限制
- ✅ 最小账户余额检查
- ✅ 订单超时机制
- ✅ 价格有效性检查
- ✅ 数据时效性检查

### 建议的测试流程

1. **第一阶段：监控模式**
   - 运行 1-2 天，观察信号质量
   - 记录假设的交易结果
   - 调整阈值参数

2. **第二阶段：小仓位测试**
   - `POSITION_SIZE=10`（10股）
   - 在 testnet 和 paper trading 测试
   - 验证开平仓流程

3. **第三阶段：正常仓位**
   - 逐步增加 `POSITION_SIZE`
   - 监控滑点和成交情况
   - 优化执行价格

4. **第四阶段：实盘准备**
   - 切换到主网（谨慎！）
   - `USE_TESTNET=false`
   - 使用主网私钥
   - IB 切换到实盘端口

## 故障排查

### 常见问题

**Q: IB 连接失败**
```
Error connecting to IBKR: [Errno 61] Connection refused
```
A: 检查 IB TWS/Gateway 是否运行，端口是否正确

**Q: Hyperliquid 订单失败**
```
❌ Hyperliquid order failed: insufficient balance
```
A: 检查测试网账户余额，访问 faucet 获取测试币

**Q: 价差计算为负数**
```
⚠️  Invalid data: Invalid or incomplete market data
```
A: 检查 IB 是否在交易时间，休市时 spot 数据为 None

**Q: 仓位一直不平仓**
A: 检查平仓阈值是否过于严格，可以适当放宽 `CLOSE_SPREAD_THRESHOLD`

### 日志分析

程序会输出详细的执行日志：
- `📢` 信号检测
- `📤` 订单提交
- `✅` 订单成交
- `❌` 错误信息
- `⚠️` 警告信息

## 参数优化建议

### 保守策略（低频，高胜率）
```bash
OPEN_SPREAD_THRESHOLD=0.003    # 0.3%
MIN_FUNDING_RATE=0.0002        # 0.02%
CLOSE_SPREAD_THRESHOLD=0.001   # 0.1%
POSITION_SIZE=50
```

### 激进策略（高频，低胜率）
```bash
OPEN_SPREAD_THRESHOLD=0.0005   # 0.05%
MIN_FUNDING_RATE=0.00005       # 0.005%
CLOSE_SPREAD_THRESHOLD=0.0002  # 0.02%
POSITION_SIZE=100
FETCH_INTERVAL=1               # 1秒检查一次
```

### 平衡策略（推荐）
```bash
OPEN_SPREAD_THRESHOLD=0.001    # 0.1%
MIN_FUNDING_RATE=0.0001        # 0.01%
CLOSE_SPREAD_THRESHOLD=0.0005  # 0.05%
POSITION_SIZE=100
FETCH_INTERVAL=5               # 5秒检查一次
```

## 安全提示

1. ⚠️ **永远不要提交私钥到 Git**
   - `.env` 文件已在 `.gitignore` 中
   - 定期检查 `git status`

2. ⚠️ **测试网与主网隔离**
   - 测试网私钥 ≠ 主网私钥
   - 不要混用配置

3. ⚠️ **从小仓位开始**
   - 先测试 10-50 股
   - 逐步增加到目标仓位

4. ⚠️ **监控资金安全**
   - 定期检查账户余额
   - 设置合理的 `MIN_ACCOUNT_BALANCE`

5. ⚠️ **准备应急预案**
   - 了解如何手动平仓
   - 保存 IB 和 Hyperliquid 的紧急联系方式

## 支持

如有问题，检查：
1. 日志输出
2. `positions.json` 文件
3. IB TWS/Gateway 日志
4. Hyperliquid 网络状态

祝交易顺利！📈
