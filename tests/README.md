# 测试套件

所有测试脚本已整理到 `tests/` 目录。

## 📋 测试文件列表

| 测试文件 | 功能 | 依赖 |
|---------|------|------|
| `test_final.py` | 完整的 Hyperliquid 数据获取测试 | Hyperliquid SDK |
| `test_ibkr.py` | IBKR 连接和数据获取测试 | TWS/Gateway, ib_insync |
| `test_account.py` | 获取 IBKR 账户信息 | TWS/Gateway, ib_insync |
| `test_market_hours.py` | 市场时段检测测试 | dateutil |
| `test_fetch.py` | 基础数据获取测试 | Hyperliquid SDK |

## 🚀 运行测试

### 前提条件

确保已激活虚拟环境并安装依赖：

```bash
# 激活虚拟环境
source .venv/bin/activate  # Mac/Linux
# 或
.venv\Scripts\activate     # Windows

# 安装依赖（如果还没安装）
pip install -r requirements.txt
```

### 运行测试

#### 1. 测试 Hyperliquid 连接

```bash
python tests/test_final.py
```

**预期输出：**
```
============================================================
Final Integration Test: Hyperliquid xyz:NVDA Data Fetcher
============================================================

Initializing fetcher...
✓ Fetcher initialized successfully

Fetching all metrics from Hyperliquid...
✓ Successfully fetched all metrics

...

✓ ALL TESTS PASSED
```

#### 2. 测试 IBKR 连接

**前提：** 确保 TWS 或 IB Gateway 正在运行

```bash
python tests/test_ibkr.py
```

**预期输出：**
```
============================================================
Interactive Brokers Connection Test
============================================================

Configuration:
  Symbol: NVDA
  Host: 127.0.0.1
  Port: 7497

1. Testing connection...
✓ Connected successfully

...

Test Complete!
```

#### 3. 获取 IBKR 账户信息

**前提：** 确保 TWS 或 IB Gateway 正在运行

```bash
python tests/test_account.py
```

**预期输出：**
```
============================================================
IBKR 账户信息获取
============================================================

账户数量: 1
账户列表: ['DU1234567']

账户 1: DU1234567
  类型: 纸交易账户 (Paper Trading)
  账户摘要:
    NetLiquidation     : 1000000.00 USD
    TotalCashValue     : 1000000.00 USD
    BuyingPower        : 4000000.00 USD

配置建议：
IBKR_ACCOUNT_ID=DU1234567
```

#### 4. 测试市场时段检测

```bash
python tests/test_market_hours.py
```

**预期输出：**
```
============================================================
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
```

#### 5. 基础数据获取测试

```bash
python tests/test_fetch.py
```

## ⚠️ 常见问题

### Q1: ModuleNotFoundError

**问题：** `ModuleNotFoundError: No module named 'hyperliquid'`

**解决：**
```bash
# 确保虚拟环境已激活
source .venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### Q2: IBKR 连接失败

**问题：** `Connection refused` 或 `Could not connect to IBKR`

**解决：**
1. 确保 TWS 或 IB Gateway 正在运行
2. 检查 API 设置是否启用
3. 验证端口配置：
   - TWS 纸交易: 7497
   - TWS 实盘: 7496
   - Gateway 纸交易: 4002
   - Gateway 实盘: 4001

### Q3: 导入错误

**问题：** 测试文件无法导入 src 模块

**解决：**
测试文件已配置自动添加 src 目录到 Python 路径，确保从项目根目录运行：
```bash
# 正确（从项目根目录）
python tests/test_final.py

# 错误（从 tests 目录内）
cd tests
python test_final.py  # ✗ 不推荐
```

## 🧪 批量运行测试

如果想一次运行所有测试（需要 IBKR 连接）：

```bash
# 运行所有测试
for test in tests/test_*.py; do
    echo "Running $test..."
    python "$test"
    echo "---"
done
```

## 📊 测试覆盖

- ✅ Hyperliquid 数据获取
- ✅ IBKR 连接和数据获取
- ✅ 账户信息检测
- ✅ 市场时段检测
- ✅ 时区自动处理

## 🔗 相关文档

- [IBKR 集成文档](../docs/IBKR_INTEGRATION.md)
- [项目结构](../docs/PROJECT_STRUCTURE.md)
- [完整中文文档](../docs/README_CN.md)

---

**提示：** 所有测试都可以独立运行，根据需要选择性执行。
