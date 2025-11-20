# 市场时段配置更新总结

## 📋 更新概述

添加了市场时段智能检测功能，支持仅在美股常规交易时段采集 IBKR 数据，自动处理时区转换和夏令时。

**更新日期：** 2025-11-20

## ✅ 完成的更新

### 1. 核心功能实现

#### `src/ib_fetcher/fetcher.py`
- ✅ 新增 `get_market_session()` 方法
  - 识别四种市场时段：`'pre_market'`, `'regular'`, `'after_hours'`, `'closed'`
  - 自动处理夏令时（DST）和标准时间转换
  - 使用 `America/New_York` 时区，不依赖服务器本地时间
- ✅ 更新 `is_market_open()` 方法
- ✅ 新增 `is_regular_hours()` 方法

**时段定义：**
```
盘前：04:00 - 09:30 ET
盘中：09:30 - 16:00 ET  ⭐ 最佳时段
盘后：16:00 - 20:00 ET
休市：20:00 - 04:00 ET & 周末
```

#### `src/main_with_ibkr.py`
- ✅ 新增 `--ibkr-regular-hours-only` 命令行参数
- ✅ 在主循环中检测市场时段
- ✅ 根据配置决定是否采集 IBKR 数据
- ✅ 显示当前市场时段（盘前/盘中/盘后）

### 2. 配置文件更新

#### `.env.example`
- ✅ 新增配置项：`IBKR_REGULAR_HOURS_ONLY`
  ```bash
  # Set to true to only fetch IBKR data during regular market hours (9:30 AM - 4:00 PM ET)
  # During pre-market, after-hours, and closed hours, only Hyperliquid data will be fetched
  # Automatically handles daylight saving time (DST) and standard time
  IBKR_REGULAR_HOURS_ONLY=false
  ```

### 3. 测试脚本

#### `src/test_market_hours.py`（新增）
- ✅ 测试市场时段检测功能
- ✅ 显示本地时间和美东时间对比
- ✅ 自动识别夏令时/冬令时
- ✅ 提供配置建议

**运行测试：**
```bash
python src/test_market_hours.py
```

### 4. 文档更新

#### `docs/IBKR_INTEGRATION.md`
- ✅ 更新目录，添加"市场时段和时区处理"章节
- ✅ 在"安装和配置"部分添加 `IBKR_REGULAR_HOURS_ONLY` 说明
- ✅ 在"使用方法"部分添加"方式二：仅在盘中时段采集"
- ✅ 新增完整的"市场时段和时区处理"章节，包含：
  - 美股交易时间表
  - 时区转换（转换为北京时间）
  - 自动时区处理说明
  - 市场时段检测示例
  - 测试脚本使用
  - 配置建议
  - 数据质量对比
  - 国际部署说明
- ✅ 更新 Q3（市场休市时怎么办）

#### `docs/README_CN.md`
- ✅ 在"完整配置（包含 IBKR）"部分添加市场时段配置
- ✅ 添加市场时段说明和链接
- ✅ 更新 Prometheus 指标前缀（`hyperliquid_nvda_` → `hyib_arb_`）

### 5. 指标前缀更新

#### `src/prom_pusher/pusher.py`
- ✅ 所有 Prometheus 指标前缀从 `hyperliquid_nvda_` 改为 `hyib_arb_`

**更新后的指标：**
```
hyib_arb_perp_bid
hyib_arb_perp_ask
hyib_arb_spot_bid
hyib_arb_spot_ask
hyib_arb_open_price
hyib_arb_close_price
hyib_arb_funding_rate
hyib_arb_spread
hyib_arb_perp_mid_price
hyib_arb_spot_mid_price
```

## 🎯 使用方式

### 方式 1: 仅在盘中采集 IBKR 数据（推荐）

**配置：**
```bash
# .env
IBKR_REGULAR_HOURS_ONLY=true
```

**效果：**
- ✅ 盘中（9:30 AM - 4:00 PM ET）：采集 IBKR + Hyperliquid
- ⏸️ 盘前/盘后/休市：只采集 Hyperliquid

**优势：**
- 避免盘前盘后数据延迟
- 只在流动性最好的时段获取 spot 价格
- 节省 API 调用

### 方式 2: 24/7 采集（包括盘前盘后）

**配置：**
```bash
# .env
IBKR_REGULAR_HOURS_ONLY=false
```

**效果：**
- ✅ 全天候采集 IBKR 和 Hyperliquid 数据
- ⚠️ 盘前盘后可能有数据延迟

### 方式 3: 完全禁用 IBKR

**配置：**
```bash
# .env
DISABLE_IBKR=true
```

## 🌍 时区处理

### 自动时区转换

代码使用 `dateutil.tz.gettz('America/New_York')` 获取美东时间，**无论服务器部署在哪里都能正确判断**：

✅ 中国服务器 (UTC+8)
✅ 欧洲服务器 (UTC+1/+2)
✅ 美国服务器 (UTC-5/-4)
✅ 任何其他时区

### 夏令时自动处理

```
夏令时（3月-11月）：美东 = UTC-4
冬令时（11月-3月）：美东 = UTC-5
```

`dateutil` 库自动识别并切换，无需手动配置。

### 时区转换示例（转换为北京时间）

#### 夏令时期间
```
盘前：16:00 - 21:30 (北京时间)
盘中：21:30 - 04:00+1 (北京时间，次日凌晨)
盘后：04:00 - 08:00+1 (北京时间，次日)
```

#### 冬令时期间
```
盘前：17:00 - 22:30 (北京时间)
盘中：22:30 - 05:00+1 (北京时间，次日凌晨)
盘后：05:00 - 09:00+1 (北京时间，次日)
```

## 📊 数据质量对比

| 时段 | IBKR 数据质量 | Hyperliquid | 建议 |
|------|--------------|-------------|------|
| 盘中 (9:30-16:00 ET) | ✅ 最佳 | ✅ 正常 | 推荐采集 |
| 盘前 (4:00-9:30 ET) | ⚠️ 可能延迟 | ✅ 正常 | 可选采集 |
| 盘后 (16:00-20:00 ET) | ⚠️ 可能延迟 | ✅ 正常 | 可选采集 |
| 休市 (周末/非交易时间) | ❌ 上次收盘价 | ✅ 正常 | 不推荐采集 |

## 🧪 测试

### 测试市场时段检测

```bash
python src/test_market_hours.py
```

输出示例：
```
美股市场时段检测测试
============================================================

当前时间信息：
  本地时间: 2025-11-20 22:30:00 CST
  美东时间: 2025-11-20 09:30:00 EST
  星期: 周三
  时区模式: 冬令时 (UTC-5)

市场时段分析：
  当前状态: 盘中交易 (Regular hours) ✓
  时段范围: 09:30 - 16:00 ET

配置建议：
  ✓ 当前是最佳采集时段
  ✓ IBKR 数据质量最高
```

### 测试 IBKR 连接

```bash
python src/test_ibkr.py
```

### 运行完整程序

```bash
# 使用新配置运行
python src/main_with_ibkr.py

# 查看市场时段信息
# 程序会显示：Fetching metrics from IBKR... [盘中]
```

## 📝 配置建议

### 生产部署（推荐）

```bash
# .env
SYMBOL=xyz:NVDA
STOCK_SYMBOL=NVDA
IBKR_HOST=127.0.0.1
IBKR_PORT=4002                    # IB Gateway 纸交易
DISABLE_IBKR=false
IBKR_REGULAR_HOURS_ONLY=true      # ⭐ 推荐启用
PUSH_GATEWAY_URL=你的地址:9091
FETCH_INTERVAL=60
```

### 开发测试

```bash
# .env
IBKR_REGULAR_HOURS_ONLY=false     # 24/7 采集，方便测试
```

## 🔗 相关文档

- [IBKR 集成文档 - 市场时段和时区处理](docs/IBKR_INTEGRATION.md#市场时段和时区处理)
- [完整中文文档](README_CN.md)
- [部署指南](docs/DEPLOYMENT.md)
- [项目结构](docs/PROJECT_STRUCTURE.md)

## ✨ 主要优势

1. **智能时段检测**
   - 自动识别盘前、盘中、盘后、休市
   - 根据配置灵活控制数据采集

2. **时区自动处理**
   - 无论服务器在哪里都能正确判断
   - 自动处理夏令时和冬令时切换

3. **数据质量优先**
   - 只在最佳时段采集 IBKR 数据
   - 避免盘前盘后的延迟数据

4. **国际化友好**
   - 支持任意时区部署
   - 中国、欧洲、美国服务器均可使用

5. **节省资源**
   - 减少不必要的 API 调用
   - 降低 IBKR 连接负担

## 🎓 技术细节

### 时区处理原理

```python
from dateutil import tz
import datetime

# 获取美国东部时间（自动处理夏令时）
eastern = tz.gettz('America/New_York')
now = datetime.datetime.now(eastern)

# 无论服务器本地时间是什么，now 都是准确的美东时间
# dateutil 会自动查询时区数据库，确定当前是夏令时还是标准时间
```

### 市场时段判断逻辑

```python
# 转换为分钟便于比较
current_minutes = now.hour * 60 + now.minute

# 时段定义
if 240 <= current_minutes < 570:      # 04:00 - 09:30
    return 'pre_market'
elif 570 <= current_minutes < 960:    # 09:30 - 16:00
    return 'regular'
elif 960 <= current_minutes < 1200:   # 16:00 - 20:00
    return 'after_hours'
else:
    return 'closed'
```

---

**更新完成！** 🎉

所有功能已实现、测试并文档化。现在可以智能地根据市场时段采集数据，适合国际部署。
