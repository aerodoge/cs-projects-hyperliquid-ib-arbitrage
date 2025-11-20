# Hyperliquid NVDA 数据采集器

从 Hyperliquid TradeXYZ 获取 NVDA 永续合约数据，并可选择性集成 Interactive Brokers 获取实际股票价格，用于套利分析和监控。

## ⚡ 快速开始

```bash
# 1. 安装依赖
./quickstart.sh

# 2. 配置（设置 Prometheus Push Gateway URL）
cp .env.example .env
nano .env

# 3. 运行
python src/main.py                    # 仅 Hyperliquid
python src/main_with_ibkr.py          # 包含 IBKR 套利分析
```

## 📊 功能特性

### 核心功能

- ✅ **Hyperliquid xyz:NVDA 永续合约数据**
    - 订单簿价格（Bid/Ask）
    - K 线数据（Open/Close）
    - 资金费率（Funding Rate）

- ✅ **Interactive Brokers 集成**（可选）
    - 实时 NVDA 股票价格
    - 套利机会计算
    - 基差分析

- ✅ **Prometheus 集成**
    - Push Gateway 支持
    - 完整时序数据
    - Grafana 可视化

### 数据采集

| 指标                 | 来源          | 说明      |
|--------------------|-------------|---------|
| perp_bid, perp_ask | Hyperliquid | 永续合约买卖价 |
| spot_bid, spot_ask | IBKR        | 实际股票买卖价 |
| open, close        | Hyperliquid | K 线开平仓价 |
| funding_rate       | Hyperliquid | 资金费率    |

## 📖 完整文档

**👉 查看 [完整中文文档](docs/README_CN.md) 获取详细说明**

### 文档索引

| 文档                                 | 内容                          |
|------------------------------------|-----------------------------|
| **[完整中文文档](docs/README_CN.md)**    | 项目说明、安装、配置、使用、常见问题          |
| **[部署指南](docs/DEPLOYMENT.md)**          | 生产环境部署、Docker、Systemd、监控    |
| **[IBKR 集成](docs/IBKR_INTEGRATION.md)** | Interactive Brokers 集成和套利分析 |
| **[项目总结](docs/PROJECT_SUMMARY.md)**     | 功能总览、技术栈、使用场景               |
| **[文档索引](docs/INDEX.md)**               | 所有文档的导航索引                   |

## 🎯 使用场景

### 1. 监控永续合约价格

```bash
python src/main.py
```

适合：实时监控 NVDA 永续合约价格和资金费率

### 2. 套利分析

```bash
# 需要先启动 TWS/IB Gateway
python src/main_with_ibkr.py
```

适合：对比永续合约和实际股票价格，发现套利机会

## 🛠️ 配置示例

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

## 📈 Prometheus 指标

采集的所有指标都会推送到 Prometheus：

```promql
# 永续合约价格（Hyperliquid）
hyib_arb_perp_bid
hyib_arb_perp_ask

# 现货价格（IBKR）
hyib_arb_spot_bid
hyib_arb_spot_ask

# 其他指标
hyib_arb_open_price
hyib_arb_close_price
hyib_arb_funding_rate
hyib_arb_spread
hyib_arb_perp_mid_price
hyib_arb_spot_mid_price
```

## 🧪 测试

```bash
# 测试 Hyperliquid 连接
python src/test_final.py

# 测试 IBKR 连接
python src/test_ibkr.py

# 查看可用资产
python src/list_assets.py
```

## 📦 项目结构

```
.
├── src/                          # 📦 源代码
│   ├── hl_fetcher/               # 🔵 Hyperliquid 数据获取包
│   ├── ib_fetcher/               # 🟢 IBKR 数据获取包
│   ├── prom_pusher/              # 🟡 Prometheus 推送包
│   ├── utils/                    # 🛠️ 工具脚本包
│   ├── main.py                   # ⚡ 主程序（仅 Hyperliquid）
│   ├── main_with_ibkr.py         # ⚡ 主程序（含 IBKR）
│   ├── test_final.py             # 🧪 完整功能测试
│   └── test_ibkr.py              # 🧪 IBKR 连接测试
├── docs/                         # 📚 完整文档
│   ├── README_CN.md              # 📖 详细中文文档
│   ├── DEPLOYMENT.md             # 🚀 部署指南
│   ├── IBKR_INTEGRATION.md       # 💹 IBKR 集成文档
│   ├── PROJECT_SUMMARY.md        # 📊 项目总结
│   ├── PROJECT_STRUCTURE.md      # 📁 项目结构说明
│   └── INDEX.md                  # 🗂️ 文档索引
├── requirements.txt              # 📋 Python 依赖
├── .env.example                  # ⚙️ 配置模板
└── quickstart.sh                 # 🚀 快速开始脚本
```

**详细结构说明：** 查看 [项目结构文档](docs/PROJECT_STRUCTURE.md)

## 💡 关键概念

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

## ⚙️ 采集频率

```bash
# 高频监控（适合套利）
FETCH_INTERVAL=30

# 标准监控（推荐）
FETCH_INTERVAL=60

# 低频监控（节省资源）
FETCH_INTERVAL=300
```

## 🚀 生产部署

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

## ❓ 常见问题

### Q: 为什么找不到 NVDA？

A: 必须使用完整名称 `xyz:NVDA`，不能只用 `NVDA`

### Q: IBKR 连接失败？

A: 检查 TWS/Gateway 是否运行，API 是否启用。详见 [IBKR 集成文档](docs/IBKR_INTEGRATION.md)

### Q: 需要实盘账户吗？

A: 不需要！IBKR 纸交易账户完全免费且功能完整

### Q: 可以监控其他股票吗？

A: 可以！TradeXYZ 还部署了 TSLA、AAPL 等。运行 `python src/list_assets.py` 查看

更多问题：[完整文档 - 常见问题](docs/README_CN.md#常见问题)

## 🔗 相关链接

- [Hyperliquid 官网](https://hyperliquid.xyz/)
- [TradeXYZ](https://trade.xyz/)
- [Hyperliquid Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [Interactive Brokers API](https://www.interactivebrokers.com/en/trading/ib-api.php)
- [ib_insync 文档](https://ib-insync.readthedocs.io/)

## 📄 许可证

MIT License

---

**开始使用：** 查看 [完整中文文档](docs/README_CN.md) 📖

**快速测试：** 运行 `./quickstart.sh` ⚡

**获取帮助：** 查看 [文档索引](docs/INDEX.md) 📚
