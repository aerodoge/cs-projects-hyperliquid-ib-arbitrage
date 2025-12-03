# Hyperliquid-IB 套利交易系统

从 Hyperliquid TradeXYZ 和 Interactive Brokers 获取 NVDA 数据，支持数据采集、监控和自动套利交易。

## 快速开始

```bash
# 1. 安装依赖
./quickstart.sh

# 2. 配置（设置 Prometheus Push Gateway URL）
cp .env.example .env
nano .env

# 3. 运行
python src/main.py                    # 数据采集 + Prometheus 推送
python src/main_trading.py            # 自动交易（需先配置私钥）
```

## 功能特性

### 核心功能

- **Hyperliquid xyz:NVDA 永续合约数据**
    - 订单簿价格（Bid/Ask）
    - 资金费率（Funding Rate）

- **Interactive Brokers 股票数据**
    - 实时 NVDA 股票价格（Bid/Ask）
    - 市场时段检测
    - 自动时区处理

- **自动套利交易**
    - 开仓/平仓信号检测
    - 自动交易执行
    - 仓位管理和 PnL 追踪

- **Prometheus 集成**
    - Push Gateway 支持
    - 完整时序数据
    - Grafana 可视化

### 数据采集

| 指标                 | 来源          | 说明        |
|--------------------|-------------|-----------|
| perp_bid, perp_ask | Hyperliquid | 永续合约买卖价   |
| spot_bid, spot_ask | IBKR        | 现货股票买卖价   |
| funding_rate       | Hyperliquid | 资金费率（8小时） |

## 完整文档

| 文档                                      | 内容                          |
|-----------------------------------------|-----------------------------|
| **[文档索引](docs/INDEX.md)**               | 从这里开始浏览所有文档                 |
| **[交易指南](docs/TRADING_GUIDE.md)**       | 自动套利交易完整指南                  |
| **[部署指南](docs/DEPLOYMENT.md)**          | 生产环境部署、Docker、Systemd、监控    |
| **[IBKR 集成](docs/IBKR_INTEGRATION.md)** | Interactive Brokers 集成和数据采集 |
| **[项目结构](docs/PROJECT_STRUCTURE.md)**   | 详细的代码结构和包说明（开发者用）           |
| **[开发日志](DEVELOPMENT_LOG.md)**         | 开发记录和会话历史（包含技术细节和问题解决）    |

## 使用场景

### 1. 数据采集和监控

```bash
# 需要先启动 TWS/IB Gateway
python src/main.py
```

功能：

- 实时采集 Hyperliquid 永续合约数据
- 实时采集 IBKR 现货价格数据
- 推送到 Prometheus
- 适合在 Grafana 中可视化监控

### 2. 自动套利交易

```bash
# 监控模式（不执行交易）
python src/main_trading.py

# 实际交易模式（需配置私钥）
python src/main_trading.py --enable-trading
```

功能：

- 计算开仓/平仓价差
- 检测套利信号
- 自动执行交易（可选）
- 详见 [交易指南](docs/TRADING_GUIDE.md)

## 配置示例

### 基础配置（.env）

```bash
# Hyperliquid
SYMBOL=xyz:NVDA
PERP_DEXS=xyz

# Prometheus
PUSH_GATEWAY_URL=localhost:9091

# 采集间隔（秒）
FETCH_INTERVAL=60
```

### 完整配置（包含 IBKR）

```bash
# Interactive Brokers
STOCK_SYMBOL=NVDA
IBKR_HOST=127.0.0.1
IBKR_PORT=7497                    # TWS 纸交易 (或 4002 Gateway 纸交易)
DISABLE_IBKR=false                # 设为 true 禁用 IBKR

# 市场时段配置（推荐启用）
IBKR_REGULAR_HOURS_ONLY=true     # 仅在盘中（9:30-16:00 ET）采集 IBKR 数据
                                  # false: 24/7 采集（包括盘前盘后）
```

**市场时段说明：**

- 启用后只在美股常规交易时段采集 IBKR 数据
- 盘前、盘后、休市时只采集 Hyperliquid 数据
- 自动处理时区转换和夏令时，适合国际部署
- 详见：[IBKR 集成 - 市场时段](docs/IBKR_INTEGRATION.md#市场时段和时区处理)

## Prometheus 指标

采集的所有指标都会推送到 Prometheus：

```promql
# 永续合约价格（Hyperliquid）
hyib_arb_perp_bid              # 永续合约买价
hyib_arb_perp_ask              # 永续合约卖价

# 现货价格（IBKR）
hyib_arb_spot_bid              # 现货买价
hyib_arb_spot_ask              # 现货卖价

# 其他指标
hyib_arb_funding_rate          # 资金费率（8小时）
```

## 测试

```bash
# 测试 Hyperliquid 连接
python src/test_final.py

# 测试 IBKR 连接
python src/test_ibkr.py

# 查看可用资产
python src/list_assets.py
```

## 项目结构

```
.
├── src/                          # 源代码
│   ├── hl_fetcher/               # Hyperliquid 数据获取包
│   ├── ib_fetcher/               # IBKR 数据获取包
│   ├── trader/                   # 交易策略和执行模块
│   ├── prom_pusher/              # Prometheus 推送包
│   ├── utils/                    # 工具脚本包
│   ├── main.py                   # 数据采集主程序
│   ├── main_trading.py           # 自动交易主程序
│   ├── test_final.py             # 完整功能测试
│   └── test_ibkr.py              # IBKR 连接测试
├── docs/                         # 完整文档
│   ├── INDEX.md                  # 文档索引（从这里开始）
│   ├── TRADING_GUIDE.md          # 交易指南
│   ├── DEPLOYMENT.md             # 部署指南
│   ├── IBKR_INTEGRATION.md       # IBKR 集成文档
│   └── PROJECT_STRUCTURE.md      # 项目结构说明
├── requirements.txt              # Python 依赖
├── .env.example                  # 配置模板
└── quickstart.sh                 # 快速开始脚本
```

**详细结构说明：** 查看 [项目结构文档](docs/PROJECT_STRUCTURE.md)

## 关键概念

### xyz:NVDA 是什么？

- TradeXYZ 通过 HIP-3 在 Hyperliquid 上部署的 NVDA 永续合约
- 24/7 交易，即使股市休市
- 最高 10x 杠杆
- USDC 结算

### 为什么需要 IBKR？

- Hyperliquid 上只有永续合约，没有实际股票
- 通过 IBKR 获取真实股票价格
- 计算永续合约与现货的价差（基差）
- 发现套利机会

## 采集频率

```bash
# 高频监控（适合套利）
FETCH_INTERVAL=30

# 标准监控（推荐）
FETCH_INTERVAL=60

# 低频监控（节省资源）
FETCH_INTERVAL=300
```

## 生产部署

### 使用 Systemd

```bash
# 创建服务
sudo systemctl enable hyperliquid-collector
sudo systemctl start hyperliquid-collector
```

### 使用 Docker

```bash
docker-compose up -d
```

详见：[部署指南](docs/DEPLOYMENT.md)

## 常见问题

### Q: 如何开始使用？

A:

1. **仅数据监控**：运行 `python src/main.py`
2. **自动交易**：先阅读 [交易指南](docs/TRADING_GUIDE.md)，配置私钥后运行 `python src/main_trading.py`

### Q: 为什么找不到 NVDA？

A: 必须使用完整名称 `xyz:NVDA`，不能只用 `NVDA`

### Q: IBKR 连接失败？

A: 检查 TWS/Gateway 是否运行，API 是否启用。详见 [IBKR 集成文档](docs/IBKR_INTEGRATION.md)

### Q: 需要实盘账户吗？

A: 不需要！建议先用 IBKR Paper Trading 和 Hyperliquid Testnet 测试

### Q: 交易功能安全吗？

A: 系统包含多重风险控制，但**务必先在测试网测试**。详见 [交易指南 - 风险控制](docs/TRADING_GUIDE.md#风险控制)

## 美股交易时段

### 夏令时

| 时段 | 时间 (ET)           | 北京时间          | 价格变化频率  |
|----|-------------------|---------------|---------|
| 盘前 | 4:00 AM - 9:30 AM | 16:00 - 21:30 | 低       |
| 盘中 | 9:30 AM - 4:00 PM | 21:30 - 04:00 | 高（每秒多次） |
| 盘后 | 4:00 PM - 8:00 PM | 04:00 - 08:00 | 中低      |
| 休市 | 8:00 PM - 4:00 AM | 08:00 - 16:00 | 无交易     |

### 冬令时

| 时段 | 美东时间 (ET)         | 北京时间          |
|----|-------------------|---------------|
| 盘前 | 4:00 AM - 9:30 AM | 17:00 - 22:30 |
| 盘中 | 9:30 AM - 4:00 PM | 22:30 - 05:00 |
| 盘后 | 4:00 PM - 8:00 PM | 05:00 - 09:00 |
| 休市 | 8:00 PM - 4:00 AM | 09:00 - 17:00 |

## 相关链接

- [Hyperliquid 官网](https://hyperliquid.xyz/)
- [TradeXYZ](https://trade.xyz/)
- [Hyperliquid Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [Interactive Brokers API](https://www.interactivebrokers.com/en/trading/ib-api.php)
- [ib_insync 文档](https://ib-insync.readthedocs.io/)

