# 项目结构说明

## 完整目录结构

```
cs-projects-hyperliquid-ib-arbitrage/
├── src/                                # 源代码目录
│   ├── __init__.py                     # 包初始化
│   │
│   ├── hl_fetcher/                     # Hyperliquid 数据获取包
│   │   ├── __init__.py                 # 包导出
│   │   └── fetcher.py                  # Hyperliquid 数据获取器
│   │
│   ├── ib_fetcher/                     # Interactive Brokers 数据获取包
│   │   ├── __init__.py                 # 包导出
│   │   └── fetcher.py                  # IBKR 数据获取器
│   │
│   ├── prom_pusher/                    # Prometheus 推送包
│   │   ├── __init__.py                 # 包导出
│   │   └── pusher.py                   # Prometheus 指标推送器
│   │
│   ├── utils/                          # 工具脚本包
│   │   ├── __init__.py                 # 包初始化
│   │   ├── find_nvda_dex.py            # 查找 NVDA DEX
│   │   ├── list_assets.py              # 列出所有资产
│   │   ├── search_stocks.py            # 搜索股票符号
│   │   ├── search_nvda_spot.py         # 搜索 NVDA 现货
│   │   ├── test_xyz_nvda.py            # xyz:NVDA 测试 v1
│   │   └── test_xyz_nvda_v2.py         # xyz:NVDA 测试 v2
│   │
│   ├── main.py                         # 主程序（仅 Hyperliquid）
│   ├── main_with_ibkr.py               # 主程序（含 IBKR 套利）
│   ├── test_final.py                   # 完整功能测试
│   ├── test_ibkr.py                    # IBKR 连接测试
│   └── test_fetch.py                   # 基础数据获取测试
│
├── docs/                               # 文档目录
│   ├── README_CN.md                    # 完整中文文档（主文档）
│   ├── DEPLOYMENT.md                   # 部署指南
│   ├── IBKR_INTEGRATION.md             # IBKR 集成文档
│   ├── PROJECT_SUMMARY.md              # 项目总结
│   ├── PROJECT_STRUCTURE.md            # 项目结构（本文件）
│   └── INDEX.md                        # 文档索引
│
├── pics/                               # 图片资源
│   └── img.png                         # 参考截图
│
├── .venv/                              # Python 虚拟环境
├── requirements.txt                    # Python 依赖
├── .env.example                        # ⚙配置模板
├── .gitignore                          # Git 忽略文件
├── quickstart.sh                       # 快速开始脚本
├── README.md                           # 英文 README
└── README_CN.md                        # 中文 README
```

## 📦 包说明

### 1. hl_fetcher - Hyperliquid 数据获取包

**作用：** 从 Hyperliquid 交易所获取 xyz:NVDA 永续合约数据

**主要功能：**

- 获取订单簿价格（Bid/Ask）
- 获取 K 线数据（Open/Close）
- 获取资金费率（Funding Rate）
- 支持多个 DEX（xyz, flx, vntl 等）

**使用示例：**

```python
from hl_fetcher import HyperliquidFetcher

# 初始化
fetcher = HyperliquidFetcher(
    symbol="xyz:NVDA",
    use_testnet=False,
    perp_dexs=["xyz"]
)

# 获取所有指标
metrics = fetcher.get_all_metrics()
```

**文件：**

- `fetcher.py`: 核心数据获取类

---

### 2. ib_fetcher - Interactive Brokers 数据获取包

**作用：** 从 Interactive Brokers 获取实际股票价格

**主要功能：**

- 连接 TWS/IB Gateway
- 获取实时股票价格
- 获取市场快照（OHLCV）
- 检测市场开盘状态
- 自动重连机制

**使用示例：**

```python
from ib_fetcher import IBKRFetcher

# 使用 context manager
with IBKRFetcher("NVDA", "127.0.0.1", 7497) as fetcher:
    prices = fetcher.get_stock_price()
    print(f"Bid: {prices['bid']}, Ask: {prices['ask']}")
```

**文件：**

- `fetcher.py`: IBKR 数据获取类

**依赖：**

- `ib_insync`: IBKR Python API
- `python-dateutil`: 日期时间处理

---

### 3. prom_pusher - Prometheus 推送包

**作用：** 将采集的指标推送到 Prometheus Push Gateway

**主要功能：**

- 定义所有 Prometheus 指标
- 更新指标值
- 推送到 Push Gateway
- 自动计算衍生指标

**使用示例：**

```python
from prom_pusher import PrometheusMetricsPusher

# 初始化
pusher = PrometheusMetricsPusher(
    push_gateway_url="localhost:9091",
    job_name="hyperliquid_nvda"
)

# 更新并推送
pusher.update_and_push(metrics)
```

**文件：**

- `pusher.py`: Prometheus 推送类

**依赖：**

- `prometheus-client`: Prometheus Python 客户端

---

### 4. utils - 工具脚本包

**作用：** 辅助工具和测试脚本

**包含脚本：**

| 脚本                    | 功能                  |
|-----------------------|---------------------|
| `list_assets.py`      | 列出所有可用的永续合约和现货资产    |
| `find_nvda_dex.py`    | 查找 NVDA 在哪个 DEX 中   |
| `search_stocks.py`    | 搜索常见股票符号            |
| `search_nvda_spot.py` | 搜索 NVDA 现货市场        |
| `test_xyz_nvda.py`    | 测试 xyz:NVDA 数据获取 v1 |
| `test_xyz_nvda_v2.py` | 测试 xyz:NVDA 数据获取 v2 |

**使用示例：**

```bash
# 列出所有资产
python src/utils/list_assets.py

# 查找 NVDA
python src/utils/find_nvda_dex.py
```

---

## 🔧 主程序

### main.py - 基础版本

**功能：** 仅从 Hyperliquid 获取数据

**适用场景：**

- 监控永续合约价格
- 追踪资金费率
- 不需要套利分析

**运行：**

```bash
python src/main.py
```

---

### main_with_ibkr.py - 完整版本

**功能：** 同时从 Hyperliquid 和 IBKR 获取数据

**适用场景：**

- 套利分析
- 基差监控
- 价格对比

**运行：**

```bash
python src/main_with_ibkr.py
```

**额外功能：**

- 自动计算套利机会
- 显示价差百分比
- 支持禁用 IBKR（`--no-ibkr`）

---

## 🧪 测试脚本

### test_final.py - 完整功能测试

**测试内容：**

- Hyperliquid 连接
- 所有数据获取功能
- 数据完整性验证

**运行：**

```bash
python src/test_final.py
```

---

### test_ibkr.py - IBKR 连接测试

**测试内容：**

- IBKR 连接
- 价格获取
- 市场快照
- 市场状态检测

**运行：**

```bash
python src/test_ibkr.py
```

---

### test_fetch.py - 基础测试

**测试内容：**

- 基础数据获取
- 简单验证

**运行：**

```bash
python src/test_fetch.py
```

---

## 📚 文档结构

### 主文档

| 文档                     | 内容      | 适合人群  |
|------------------------|---------|-------|
| `README_CN.md`         | 详细中文文档  | 所有用户  |
| `DEPLOYMENT.md`        | 部署指南    | 运维人员  |
| `IBKR_INTEGRATION.md`  | IBKR 集成 | 套利交易者 |
| `PROJECT_SUMMARY.md`   | 项目总结    | 开发者   |
| `PROJECT_STRUCTURE.md` | 项目结构    | 开发者   |
| `INDEX.md`             | 文档索引    | 所有用户  |

---

## 🎯 包的设计原则

### 1. 模块化

- 每个包负责单一功能
- 清晰的接口定义
- 最小化包之间的依赖

### 2. 易用性

```python
# 简单导入
from hl_fetcher import HyperliquidFetcher
from ib_fetcher import IBKRFetcher
from prom_pusher import PrometheusMetricsPusher

# 直观使用
fetcher = HyperliquidFetcher("xyz:NVDA")
metrics = fetcher.get_all_metrics()
```

### 3. 可扩展性

- 易于添加新的数据源
- 易于添加新的指标
- 易于添加新的功能

### 4. 可测试性

- 每个包都可以独立测试
- 提供专门的测试脚本
- 清晰的错误处理

---

## 🔄 数据流

```
┌─────────────────┐
│  Hyperliquid    │
│  xyz:NVDA       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  hl_fetcher     │      │  ib_fetcher     │
│  数据获取       │      │  数据获取       │
└────────┬────────┘      └────────┬────────┘
         │                        │
         └──────────┬─────────────┘
                    ▼
            ┌──────────────┐
            │  main*.py    │
            │  数据整合    │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ prom_pusher  │
            │ 指标推送     │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │  Prometheus  │
            │  Push Gateway│
            └──────────────┘
```

---

## 📊 依赖关系

```
main.py
├── hl_fetcher (必需)
│   └── hyperliquid-python-sdk
└── prom_pusher (必需)
    └── prometheus-client

main_with_ibkr.py
├── hl_fetcher (必需)
│   └── hyperliquid-python-sdk
├── ib_fetcher (可选)
│   ├── ib_insync
│   └── python-dateutil
└── prom_pusher (必需)
    └── prometheus-client
```

---

## 🚀 快速导航

**我想...**

| 任务                    | 文件/目录                                   |
|-----------------------|-----------------------------------------|
| 修改 Hyperliquid 数据获取逻辑 | `src/hl_fetcher/fetcher.py`             |
| 修改 IBKR 数据获取逻辑        | `src/ib_fetcher/fetcher.py`             |
| 修改 Prometheus 指标      | `src/prom_pusher/pusher.py`             |
| 修改主程序逻辑               | `src/main.py` 或 `src/main_with_ibkr.py` |
| 添加新的工具脚本              | `src/utils/`                            |
| 查看文档                  | `docs/`                                 |
| 修改配置                  | `.env` (基于 `.env.example`)              |

---

## 🔧 开发指南

### 添加新功能

1. **创建新包**（如果需要）
   ```bash
   mkdir src/new_package
   touch src/new_package/__init__.py
   touch src/new_package/module.py
   ```

2. **在 __init__.py 中导出**
   ```python
   from .module import NewClass
   __all__ = ['NewClass']
   ```

3. **在主程序中使用**
   ```python
   from new_package import NewClass
   ```

### 添加新的数据源

仿照 `hl_fetcher` 或 `ib_fetcher` 的结构：

```python
# src/new_source/fetcher.py
class NewSourceFetcher:
    def __init__(self, ...):
        pass

    def get_data(self):
        pass
```

### 添加新的指标

在 `prom_pusher/pusher.py` 中添加：

```python
self.new_metric_gauge = Gauge(
    "hyperliquid_nvda_new_metric",
    "Description of new metric",
    registry=self.registry
)
```

---

## 📝 代码风格

### Python 代码规范

- 使用 4 空格缩进
- 遵循 PEP 8 规范
- 使用中文注释（对中文用户友好）
- 函数和类添加 docstring

### 包命名规范

- 使用小写字母
- 用下划线分隔单词
- 避免与常用库冲突（如：用 `hl_fetcher` 而不是 `hyperliquid`）

---

## 🎓 学习路径

### 初学者

1. 阅读 `docs/README_CN.md`
2. 查看 `src/main.py`
3. 运行 `src/test_final.py`
4. 阅读 `src/hl_fetcher/fetcher.py`

### 进阶用户

1. 阅读所有包的 `__init__.py`
2. 理解数据流
3. 查看 `src/main_with_ibkr.py`
4. 阅读 `docs/IBKR_INTEGRATION.md`

### 贡献者

1. 理解完整项目结构
2. 阅读所有核心代码
3. 添加新功能
4. 编写测试和文档

---

**版本：** 2.0.0
**最后更新：** 2025-11-20
**维护者：** Hyperliquid-IBKR Arbitrage Collector Team
