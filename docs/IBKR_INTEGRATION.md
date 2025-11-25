# Interactive Brokers 集成文档

本文档说明如何集成 Interactive Brokers (IBKR) 来获取 NVDA 实际股票价格，用于与 Hyperliquid 永续合约价格进行套利分析。

## 目录

- [为什么需要 IBKR 集成](#为什么需要-ibkr-集成)
- [IBKR 账户设置](#ibkr-账户设置)
- [安装和配置](#安装和配置)
- [使用方法](#使用方法)
- [市场时段和时区处理](#市场时段和时区处理)
- [套利分析](#套利分析)
- [常见问题](#常见问题)
- [进阶配置](#进阶配置)

## 为什么需要 IBKR 集成

### 问题

Hyperliquid 上只有 **xyz:NVDA 永续合约**，没有实际的 NVDA 股票现货市场。如果想要：

- 监控永续合约价格与实际股票价格的差异
- 发现套利机会
- 分析基差（永续合约价格 - 现货价格）

就需要从传统券商获取真实的股票价格。

### 解决方案

通过 Interactive Brokers API 获取实时 NVDA 股票买卖价，与 Hyperliquid 永续合约价格进行对比：

```
套利机会 = Hyperliquid 永续合约价格 - IBKR 实际股票价格
```

## IBKR 账户设置

### 1. 注册 IBKR 账户

访问 [Interactive Brokers](https://www.interactivebrokers.com/) 注册账户。

**推荐使用纸交易账户（Paper Trading）：**

- 免费
- 实时市场数据
- 适合测试和开发

### 2. 下载并安装软件

有两个选择：

#### 选项 A: TWS (Trader Workstation) - 推荐新手

下载地址：https://www.interactivebrokers.com/en/trading/tws.php

**端口配置：**

- 纸交易：7497
- 实盘交易：7496

#### 选项 B: IB Gateway - 推荐自动化

下载地址：https://www.interactivebrokers.com/en/trading/ibgateway-stable.php

**端口配置：**

- 纸交易：4002
- 实盘交易：4001

**Gateway 优势：**

- 更轻量级
- 无 GUI，适合服务器部署
- 更稳定

### 3. 启用 API 连接

#### TWS 设置：

1. 打开 TWS
2. 点击 **File** → **Global Configuration**
3. 选择 **API** → **Settings**
4. 勾选以下选项：
    - ✅ Enable ActiveX and Socket Clients
    - ✅ Allow connections from localhost only （本地测试）
    - ✅ Read-Only API
5. 设置 **Socket port**: 7497 (纸交易) 或 7496 (实盘)
6. 点击 **Apply** 和 **OK**

#### IB Gateway 设置：

1. 启动 IB Gateway
2. 登录纸交易或实盘账户
3. 点击右上角 **Configure** (齿轮图标)
4. 在 **API** 标签页中：
    - ✅ Enable ActiveX and Socket Clients
    - ✅ Allow connections from localhost only
    - ✅ Read-Only API
5. 设置端口: 4002 (纸交易) 或 4001 (实盘)
6. 点击 **Apply**

### 4. 市场数据订阅

确保你的账户有美股市场数据权限：

1. 登录 [IBKR 账户管理](https://www.interactivebrokers.com/sso/Login)
2. 进入 **Settings** → **User Settings** → **Market Data Subscriptions**
3. 订阅 **US Securities Snapshot and Futures Value Bundle** (纸交易账户免费)

## 安装和配置

### 1. 安装依赖

```bash
# 安装 ib_insync (IBKR Python API)
pip install ib_insync python-dateutil

# 或者使用 requirements.txt
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# Hyperliquid 配置
SYMBOL=xyz:NVDA
PERP_DEXS=xyz

# IBKR 配置
STOCK_SYMBOL=NVDA
IBKR_HOST=127.0.0.1
IBKR_PORT=7497          # TWS 纸交易
# IBKR_PORT=7496        # TWS 实盘
# IBKR_PORT=4002        # Gateway 纸交易
# IBKR_PORT=4001        # Gateway 实盘

# 如果不想使用 IBKR，设置为 true
DISABLE_IBKR=false

# 是否仅在常规交易时段（9:30 AM - 4:00 PM ET）获取 IBKR 数据
# true: 盘前、盘后、休市时只采集 Hyperliquid 数据
# false: 24/7 采集 IBKR 数据（盘前盘后可能有延迟）
IBKR_REGULAR_HOURS_ONLY=false

# Prometheus 配置
PUSH_GATEWAY_URL=localhost:9091
JOB_NAME=hyperliquid_nvda
FETCH_INTERVAL=60
```

### 3. 测试 IBKR 连接

创建测试脚本 `test_ibkr.py`：

```python
from ibkr_fetcher import IBKRFetcher

# 初始化
fetcher = IBKRFetcher(
    symbol="NVDA",
    host="127.0.0.1",
    port=7497  # TWS 纸交易端口
)

# 连接
if fetcher.connect():
    print("✓ 连接成功")

    # 获取价格
    prices = fetcher.get_stock_price()
    print(f"Bid: ${prices['bid']}")
    print(f"Ask: ${prices['ask']}")
    print(f"Last: ${prices['last']}")

    # 断开连接
    fetcher.disconnect()
else:
    print("✗ 连接失败")
```

运行测试：

```bash
python test_ibkr.py
```

## 使用方法

### 方式一：使用集成版本（推荐）

使用 `main_with_ibkr.py` 同时获取 Hyperliquid 和 IBKR 数据：

```bash
# 确保 TWS/Gateway 正在运行
# 然后启动采集器
python src/main_with_ibkr.py

# 使用自定义参数
python src/main_with_ibkr.py \
  --symbol xyz:NVDA \
  --stock-symbol NVDA \
  --ibkr-host 127.0.0.1 \
  --ibkr-port 7497 \
  --interval 60 \
  --push-gateway localhost:9091
```

### 方式二：仅在盘中时段采集 IBKR 数据（推荐）

只在美股常规交易时段（9:30 AM - 4:00 PM ET）获取 IBKR 数据：

```bash
# 在 .env 中设置
IBKR_REGULAR_HOURS_ONLY=true

# 或使用命令行参数
python src/main_with_ibkr.py --ibkr-regular-hours-only
```

**效果：**

- 盘中（9:30 AM - 4:00 PM ET）：采集 Hyperliquid + IBKR 数据 ✓
- 盘前（4:00 AM - 9:30 AM ET）：仅采集 Hyperliquid 数据
- 盘后（4:00 PM - 8:00 PM ET）：仅采集 Hyperliquid 数据
- 休市（8:00 PM - 4:00 AM ET & 周末）：仅采集 Hyperliquid 数据

**优势：**

- 避免盘前盘后数据延迟
- 只在流动性最好的时段获取 spot 价格
- 节省 API 调用

### 方式三：禁用 IBKR（仅 Hyperliquid）

如果暂时不需要实际股票价格：

```bash
# 使用命令行参数
python src/main_with_ibkr.py --no-ibkr

# 或者在 .env 中设置
DISABLE_IBKR=true
```

### 方式四：单独使用 IBKR 获取器

```python
from ibkr_fetcher import IBKRFetcher

# 使用 context manager
with IBKRFetcher("NVDA", "127.0.0.1", 7497) as fetcher:
    # 获取简单价格
    prices = fetcher.get_stock_price()
    print(f"Bid: {prices['bid']}, Ask: {prices['ask']}")

    # 获取完整市场数据
    snapshot = fetcher.get_market_snapshot()
    print(f"Open: {snapshot['open']}")
    print(f"High: {snapshot['high']}")
    print(f"Low: {snapshot['low']}")
    print(f"Close: {snapshot['close']}")
    print(f"Volume: {snapshot['volume']}")

    # 检查市场是否开盘
    is_open = fetcher.is_market_open()
    print(f"Market Open: {is_open}")

    # 获取当前市场时段
    session = fetcher.get_market_session()
    # 返回: 'pre_market', 'regular', 'after_hours', 'closed'
    print(f"Market Session: {session}")
```

## 市场时段和时区处理

### 美股交易时间

美股有不同的交易时段（均为美国东部时间 ET）：

| 时段       | 时间范围 (ET)          | 说明                       |
|----------|--------------------|--------------------------|
| 盘前交易     | 04:00 - 09:30      | Pre-market，流动性较低         |
| **常规交易** | **09:30 - 16:00**  | **Regular hours，最佳时段** ⭐ |
| 盘后交易     | 16:00 - 20:00      | After-hours，流动性较低        |
| 休市       | 20:00 - 04:00 & 周末 | Closed，无实时数据             |

### 时区转换（转换为北京时间 UTC+8）

#### 夏令时期间（3月第2个周日 - 11月第1个周日）

美东时间 = UTC-4

```
盘前: 16:00 - 21:30 (北京时间)
盘中: 21:30 - 04:00+1 (北京时间，次日凌晨)
盘后: 04:00 - 08:00+1 (北京时间，次日)
```

#### 冬令时期间（11月第1个周日 - 3月第2个周日）

美东时间 = UTC-5

```
盘前: 17:00 - 22:30 (北京时间)
盘中: 22:30 - 05:00+1 (北京时间，次日凌晨)
盘后: 05:00 - 09:00+1 (北京时间，次日)
```

### 自动时区处理

**重要：** 代码会自动处理时区转换和夏令时切换，**无论服务器部署在哪里都能正确判断**。

```python
from dateutil import tz
import datetime

# 获取美国东部时间（自动处理夏令时）
eastern = tz.gettz('America/New_York')
now = datetime.datetime.now(eastern)  # ← 这是美东时间，不是服务器本地时间

# 无论服务器在：
# - 中国 (UTC+8)
# - 欧洲 (UTC+1/+2)
# - 美国 (UTC-5/-4)
# 都能正确获取美东时间并判断市场时段
```

### 市场时段检测

使用 `get_market_session()` 方法：

```python
from ib_fetcher import IBKRFetcher

fetcher = IBKRFetcher("NVDA")
session = fetcher.get_market_session()

if session == 'regular':
    print("盘中交易 - 最佳数据质量")
elif session == 'pre_market':
    print("盘前交易 - 数据可能有延迟")
elif session == 'after_hours':
    print("盘后交易 - 数据可能有延迟")
else:
    print("休市 - 将显示上次收盘价")
```

### 测试市场时段

运行测试脚本验证：

```bash
python src/test_market_hours.py
```

输出示例：

```
美股市场时段检测测试
============================================================

当前时间信息：
  本地时间: 2025-11-20 22:30:00 CST  (你的服务器时区)
  美东时间: 2025-11-20 09:30:00 EST  (自动转换)
  星期: 周三
  时区模式: 冬令时 (UTC-5)

市场时段分析：
  当前状态: 盘中交易 (Regular hours) ✓
  时段范围: 09:30 - 16:00 ET

配置建议：
  ✓ 当前是最佳采集时段
  ✓ IBKR 数据质量最高
```

### 配置建议

根据你的需求选择合适的配置：

#### 场景 1: 24/7 监控（包括盘前盘后）

```bash
IBKR_REGULAR_HOURS_ONLY=false
```

适合：需要全天候数据，不介意盘前盘后的延迟

#### 场景 2: 仅盘中监控（推荐）

```bash
IBKR_REGULAR_HOURS_ONLY=true
```

适合：只关注流动性最好的时段，数据质量优先

#### 场景 3: 完全禁用 IBKR

```bash
DISABLE_IBKR=true
```

适合：只需要 Hyperliquid 永续合约数据

### 数据质量对比

| 时段                  | IBKR 数据质量 | 建议    |
|---------------------|-----------|-------|
| 盘中 (9:30-16:00 ET)  | ✓✓✓ 最佳    | 推荐采集  |
| 盘前 (4:00-9:30 ET)   | ⚠ 可能延迟    | 可选采集  |
| 盘后 (16:00-20:00 ET) | ⚠ 可能延迟    | 可选采集  |
| 休市 (周末/非交易时间)       | ✗ 显示上次收盘价 | 不推荐采集 |

### 国际部署说明

**无论在哪里部署服务器，都能正确判断美股市场时段：**

✓ 中国服务器 (UTC+8)
✓ 欧洲服务器 (UTC+1/+2)
✓ 亚洲其他地区
✓ 美国本土
✓ 任何其他时区

代码使用 `America/New_York` 时区，自动转换，不依赖服务器本地时间。

## 套利分析

### 理解基差

**基差 (Basis)** = 永续合约价格 - 现货价格

- **正基差**：永续合约比现货贵，说明市场预期看涨
- **负基差**：永续合约比现货便宜，说明市场预期看跌

### 套利机会

#### 1. 正向套利（Long Spot, Short Perp）

**条件：**

```
永续合约买价 > 现货卖价 + 手续费 + 资金费率成本
```

**操作：**

1. 在 IBKR 买入 NVDA 股票（现货做多）
2. 在 Hyperliquid 卖出 NVDA 永续合约（永续做空）
3. 赚取价差，并收取资金费率（如果为正）

**风险：**

- 资金费率变化
- 交易手续费
- 滑点

#### 2. 反向套利（Short Spot, Long Perp）

**条件：**

```
现货买价 > 永续合约卖价 + 手续费 - 资金费率收入
```

**操作：**

1. 在 IBKR 卖空 NVDA 股票（现货做空）
2. 在 Hyperliquid 买入 NVDA 永续合约（永续做多）
3. 赚取价差，并支付资金费率（如果为正）

**风险：**

- 股票借券成本
- 保证金要求
- 资金费率支出

### 示例输出

运行 `main_with_ibkr.py` 时会显示套利机会：

```
[2025-11-20 14:30:00] Iteration 1
Fetching metrics from Hyperliquid...
Fetching metrics from IBKR...

Fetched metrics:
  [Hyperliquid Perp]
    Perp Bid:     $197.16
    Perp Ask:     $197.25
  [IBKR Spot]
    Spot Bid:     $196.85
    Spot Ask:     $196.90
  [Prices]
    Open Price:   $197.25
    Close Price:  $197.16
  [Arbitrage Opportunity]
    Long Spot:    $0.26 (0.13%)     # 买现货，卖永续
    Long Perp:    $-0.40 (-0.20%)   # 买永续，卖现货
  [Funding Rate]
    Rate:         0.0003%
```

在这个例子中：

- **正向套利**：可以买现货 $196.90，卖永续 $197.16，赚 $0.26 (0.13%)
- 但要考虑手续费和资金费率

### 计算实际收益

```python
# 假设
spot_ask = 196.90  # 买现货价格
perp_bid = 197.16  # 卖永续价格
position_size = 10000  # 头寸大小 (USDC)

# 毛利润
gross_profit = (perp_bid - spot_ask) * (position_size / spot_ask)
print(f"毛利润: ${gross_profit:.2f}")

# 扣除成本
ibkr_fee = position_size * 0.0005  # IBKR 手续费 0.05%
hyperliquid_fee = position_size * 0.0002  # Hyperliquid 手续费 0.02%
funding_rate = 0.0003  # 每 8 小时
funding_cost = position_size * funding_rate * 3  # 每天 3 次

# 净利润（每天）
daily_profit = gross_profit - ibkr_fee - hyperliquid_fee - funding_cost
print(f"净利润（每天）: ${daily_profit:.2f}")
print(f"年化收益率: {daily_profit * 365 / position_size * 100:.2f}%")
```

## 常见问题

### Q1: 连接 IBKR 失败怎么办？

**A:** 检查：

1. TWS 或 IB Gateway 是否正在运行
2. API 设置中是否启用了 Socket Clients
3. 端口号是否正确（7497/7496 或 4002/4001）
4. 防火墙是否阻止连接
5. 是否已登录账户

```bash
# 测试端口是否开放
telnet 127.0.0.1 7497
```

### Q2: 获取不到价格数据？

**A:** 可能原因：

1. **市场未开盘**：美股交易时间是周一至周五 9:30 AM - 4:00 PM ET
2. **数据订阅**：确保有市场数据权限
3. **延迟数据**：纸交易账户可能有延迟
4. **连接超时**：增加等待时间

### Q3: 市场休市时怎么办？

**A:** 有两种处理方式：

#### 方式1: 仅在盘中采集 IBKR 数据（推荐）

在 `.env` 中设置：

```bash
IBKR_REGULAR_HOURS_ONLY=true
```

效果：

- 盘中（9:30 AM - 4:00 PM ET）：采集 IBKR + Hyperliquid 数据
- 其他时段：只采集 Hyperliquid 数据，IBKR 指标显示 N/A

优势：

- 避免获取延迟或过期的数据
- 只在最佳时段获取 spot 价格
- Hyperliquid 永续合约 24/7 正常采集

#### 方式2: 24/7 采集（包括休市）

```bash
IBKR_REGULAR_HOURS_ONLY=false
```

休市时行为：

- IBKR 返回上次收盘价（不是实时数据）
- Hyperliquid 永续合约继续 24/7 交易
- 可以用于观察永续合约与收盘价的偏离

#### 检测市场状态

在代码中检测：

```python
from ib_fetcher import IBKRFetcher

fetcher = IBKRFetcher("NVDA")
session = fetcher.get_market_session()

if session == 'regular':
    print("盘中交易 - 数据实时")
elif session in ['pre_market', 'after_hours']:
    print("盘前/盘后 - 数据可能延迟")
else:
    print("休市 - 显示上次收盘价")
```

查看详细说明：[市场时段和时区处理](#市场时段和时区处理)

### Q4: 需要实盘账户吗？

**A:** 不需要！纸交易账户就足够：

- 免费注册
- 实时市场数据
- API 功能完整
- 适合测试和监控

### Q5: 可以监控其他股票吗？

**A:** 可以！只需修改配置：

```bash
# 监控 TSLA
STOCK_SYMBOL=TSLA
SYMBOL=xyz:TSLA

# 监控 AAPL
STOCK_SYMBOL=AAPL
SYMBOL=xyz:AAPL
```

### Q6: 同时运行多个采集器会冲突吗？

**A:** 会！每个 IBKR 连接需要唯一的 Client ID：

```python
# 采集器 1 (NVDA)
fetcher1 = IBKRFetcher("NVDA", client_id=1)

# 采集器 2 (TSLA)
fetcher2 = IBKRFetcher("TSLA", client_id=2)
```

或者在命令行中：

```bash
# 添加 client_id 参数（需要修改代码支持）
python src/main_with_ibkr.py --client-id 1
```

### Q7: 如何处理连接断开？

**A:** `IBKRFetcher` 会自动尝试重连。如果频繁断开：

1. 检查 TWS/Gateway 是否稳定
2. 增加超时时间
3. 添加重连逻辑：

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        if fetcher.connect():
            break
    except Exception as e:
        print(f"Retry {attempt + 1}/{max_retries}: {e}")
        time.sleep(5)
```

### Q8: 数据延迟多少？

**A:**

- **实盘账户**：实时数据（几毫秒延迟）
- **纸交易**：通常也是实时，但可能有 1-2 秒延迟
- **API 调用**：通常在 100-500ms 之间

### Q9: 安全吗？

**A:** 是的：

- 使用 **Read-Only API**，只读取数据，不能下单
- 连接限制在 localhost，外部无法访问
- 纸交易账户没有真实资金

### Q10: 成本如何？

**A:**

- **纸交易账户**：完全免费
- **实盘账户**：
    - 市场数据费用：$0-10/月（取决于订阅）
    - 没有 API 使用费
    - 交易手续费另算

## 进阶配置

### 1. 使用 IB Gateway (无 GUI)

适合服务器部署：

```bash
# 下载 IB Gateway
wget https://download2.interactivebrokers.com/installers/ibgateway/latest-standalone/ibgateway-latest-standalone-linux-x64.sh

# 安装
chmod +x ibgateway-latest-standalone-linux-x64.sh
./ibgateway-latest-standalone-linux-x64.sh -q

# 配置
# ~/.TWS/jts.ini 中设置：
# 1. socket=true
# 2. api.port=4002 (纸交易) 或 4001 (实盘)
```

### 2. Docker 部署

创建 `docker-compose-with-ibkr.yml`：

```yaml
version: '3.8'

services:
  ib-gateway:
    image: ghcr.io/voyz/ib-gateway:latest
    container_name: ib-gateway
    environment:
      TWS_USERID: ${IB_USER}
      TWS_PASSWORD: ${IB_PASSWORD}
      TRADING_MODE: paper
      TWS_PORT: 4002
    ports:
      - "4002:4002"
    volumes:
      - ./ib-gateway-config:/root/Jts

  collector:
    build: .
    container_name: hyperliquid-ibkr-collector
    depends_on:
      - ib-gateway
    environment:
      - SYMBOL=xyz:NVDA
      - STOCK_SYMBOL=NVDA
      - IBKR_HOST=ib-gateway
      - IBKR_PORT=4002
      - PUSH_GATEWAY_URL=pushgateway:9091
    command: python src/main_with_ibkr.py
```

### 3. 自动重启 TWS/Gateway

创建监控脚本：

```bash
#!/bin/bash
# monitor_tws.sh

while true; do
    if ! pgrep -f "ibgateway" > /dev/null; then
        echo "TWS/Gateway not running, restarting..."
        /opt/IBGateway/ibgateway &
    fi
    sleep 60
done
```

## 资源链接

- [Interactive Brokers API 文档](https://interactivebrokers.github.io/tws-api/)
- [ib_insync 文档](https://ib-insync.readthedocs.io/)
- [IBKR API 论坛](https://groups.io/g/twsapi)
- [IBKR 市场数据订阅](https://www.interactivebrokers.com/en/trading/market-data.php)

---

**提示：** 建议先在纸交易账户中测试，确保一切正常后再考虑实盘部署。
