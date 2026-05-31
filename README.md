# Python可转债双低策略程序

## 项目简介
基于双低策略的可转债量化交易系统，包含选股、风控、组合管理等功能。

## 技术栈
- Python 3.9+
- FastAPI (Web API)
- Akshare (数据源，集思录全量数据)
- Efinance (备用数据源)
- PyCryptodome (AES 加密登录)
- SQLite (数据库)
- Tailscale (网络连接)

## 数据源说明
- **主要数据源**：集思录 (jisilu.cn)，通过 akshare + Cookie 获取 322 只可转债全量数据
- **自动登录**：`jisilu_login.py` 实现 AES-128-CBC 加密登录，Cookie 自动刷新
- **备用数据源**：东方财富 (efinance)，当 akshare 不足 50 条时自动回退
- **环境变量**：需设置 `JISILU_USER` / `JISILU_PASS`（集思录账号密码）

# 📋 可转债双低策略系统 - 最终功能汇总

---

## 🎯 项目总览

**项目名称：** 可转债双低策略量化交易系统
**当前版本：** v1.0.0
**开发状态：** ✅ 核心功能完成 (100%)
**总体评分：** ⭐⭐⭐⭐ (5/5)

---

## 📊 核心功能模块

### 1️⃣ 数据层

**功能描述：** 获取可转债实时数据和历史数据

**子模块：**
- ✅ **数据源抽象** (`provider.py`)
  - 定义标准数据接口
  - 支持多数据源扩展
  
- ✅ **Akshare数据源** (`akshare_provider.py`)
  - 获取实时转债数据（322只全量，集思录源）
  - 自动 Cookie 管理：失效自动刷新登录
  - 字段映射（中文→英文）
  - 百分比字段清洗
  - ST/退市转债过滤
  - 智能重试：Cookie 过期自动重新加密登录
  
- ✅ **东方财富备用源** (`efinance_provider.py`)
  - Akshare 不足 50 条时自动回退
  - 提供基础行情数据

- ✅ **集思录自动登录** (`jisilu_login.py`)
  - AES-128-CBC 加密登录，无需浏览器
  - Cookie 持久化存储 + 自动刷新
  - 环境变量管理账号密码

- ✅ **真实数据提供者** (`real_data_provider.py`)
  - 整合 Akshare + Efinance
  - Akshare ≥50条时优先使用全量数据
  - 故障自动回退
  
- ✅ **历史数据提供者** (`historical_data_provider.py`)
  - 模拟历史数据生成
  - 支持指定日期范围
  - 支持随机种子设置

**核心功能：**
- 获取实时转债列表（代码、名称、价格、溢价率、规模、评级等）
- 支持列名映射（自动适配不同数据源）
- 支持数据清洗（百分比、空值处理）
- 支持ST/退市转债过滤

---

### 2️⃣ 策略层

**功能描述：** 执行双低策略，筛选优质转债

**子模块：**
- ✅ **策略抽象基类** (`base_strategy.py`)
  - 定义标准策略接口
  - 支持多策略扩展
  
- ✅ **双低策略实现** (`double_low_strategy.py`)
  - 计算双低值（价格 + 溢价率）
  - 多条件筛选（价格、规模、评级）
  - 支持负溢价率处理
  - 支持未知评级处理

**核心功能：**
- 双低值计算（价格 + 溢价率）
- 价格限制筛选
- 溢价率限制筛选
- 剩余规模筛选
- 评级筛选（支持A-、A、A+等）
- 可选负溢价率过滤
- 可选未知评级允许

**筛选条件：**
- 价格 ≤ 130元
- 溢价率 ≤ 30%
- 剩余规模：0.5 ~ 10亿元
- 评级 ≥ A

---

### 3️⃣ 交易层

**功能描述：** 模拟交易，管理资金和持仓

**子模块：**
- ✅ **订单定义** (`order.py`)
  - 订单工厂方法（买入/卖出）
  - 订单状态管理
  
- ✅ **投资组合管理** (`portfolio.py`)
  - 资金管理
  - 持仓管理
  - 手续费计算（买入佣金、卖出佣金、印花税）
  - 平均成本计算（不含手续费）
  - 按手交易（1手=10张）
  - 交易历史记录
  
- ✅ **交易执行器** (`executor.py`)
  - 轮动调仓逻辑
  - 回测/实盘模式分离
  - 订单管理

**核心功能：**
- 按金额买入（自动计算可买手数）
- 按数量卖出
- 手续费计算（万三佣金+千一印花税）
- 按手交易（1手=10张）
- 轮动调仓（卖出掉榜，买入上榜）
- 回测/实盘模式分离
- 交易历史记录

**手续费设置：**
- 买入佣金：0.03%（万三）
- 卖出佣金：0.03%（万三）
- 印花税：0.1%（千一，仅卖出）
- 最低佣金：5元

---

### 4️⃣ 回测系统

**功能描述：** 历史数据回测，计算性能指标

**子模块：**
- ✅ **模拟数据回测** (`run_backtest.py`)
  - 模拟100只转债数据
  - 双低策略筛选
  - 模拟买入交易
  - 持仓和收益显示
  
- ✅ **真实数据回测** (`run_backtest_real.py`)
  - 使用Akshare实时数据
  - 双低策略筛选
  - 模拟买入交易
  - 持仓和收益显示
  
- ✅ **历史数据回测** (`run_backtest_historical.py`)
  - 模拟多日历史数据
  - 逐日策略筛选和调仓
  - 性能指标计算

**核心功能：**
- 模拟数据回测
- 真实数据回测
- 历史数据回测
- 定期调仓（可配置周期）
- 性能指标计算

**性能指标：**
- 总收益率
- 年化收益率
- 年化波动率
- 夏普比率
- 最大回撤
- 胜率

---

### 5️⃣ Web API

**功能描述：** 提供REST API接口，支持远程访问

**子模块：**
- ✅ **数据模型** (`api/schemas.py`)
  - Pydantic数据验证
  - 请求/响应模型定义
  
- ✅ **业务控制器** (`api/controller.py`)
  - 策略控制器
  - 投资组合控制器
  - 回测控制器
  
- ✅ **路由接口**
  - 策略接口 (`api/routes/strategy.py`)
  - 投资组合接口 (`api/routes/portfolio.py`)
  - 回测接口 (`api/routes/backtest.py`)
  
- ✅ **FastAPI应用** (`api/app.py`)
  - CORS支持
  - API文档自动生成

**核心功能：**
- 健康检查接口
- 策略执行接口
- 持仓查询接口
- 交易历史接口
- 回测执行接口
- 参数配置接口

---

## 🌐 API 接口列表

### 基础接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 根路径 |
| `/health` | GET | 健康检查 |

**响应示例：**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-02T10:00:00"
}
```

---

### 策略接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/strategy/run` | POST | 运行双低策略 |
| `/api/strategy/candidates` | GET | 获取候选转债（简化版） |

**请求示例：**
```json
{
  "max_price": 130.0,
  "max_premium": 30.0,
  "min_amount": 0.5,
  "max_amount": 10.0,
  "min_rating": "A",
  "top_n": 10
}
```

**响应示例：**
```json
{
  "candidates": [
    {
      "code": "123001",
      "name": "转债001",
      "price": 100.0,
      "premium_rate": 5.0,
      "remain_amount": 5.0,
      "rating": "AA",
      "dual_low_score": 50.0
    }
  ],
  "total_count": 10,
  "run_time": "2026-01-02T10:00:00"
}
```

---

### 投资组合接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/portfolio/execute` | POST | 执行交易（买入候选转债） |
| `/api/portfolio/summary` | GET | 获取投资组合汇总 |
| `/api/portfolio/history` | GET | 获取交易历史 |

**请求示例：**
```json
{
  "initial_cash": 100000.0,
  "cash_per_trade": 10000.0,
  "strategy_config": {
    "max_price": 130.0,
    "max_premium": 30.0,
    "min_rating": "A",
    "top_n": 10
  },
  "is_backtest": true
}
```

**响应示例：**
```json
{
  "positions": [
    {
      "symbol": "123001",
      "quantity": 100,
      "quantity_hands": 10,
      "avg_price": 100.0,
      "current_price": 105.0,
      "market_value": 10500.0,
      "profit": 500.0,
      "profit_rate": 5.0
    }
  ],
  "cash": 5000.0,
  "market_value": 95000.0,
  "total_asset": 100000.0,
  "total_profit": 0.0,
  "profit_rate": 0.0,
  "initial_cash": 100000.0,
  "position_count": 10
}
```

---

### 回测接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/backtest/run` | POST | 运行历史回测 |

**请求示例：**
```json
{
  "start_date": "2025-12-01",
  "end_date": "2026-01-01",
  "initial_cash": 100000.0,
  "top_n": 10,
  "cash_per_trade": 10000.0,
  "max_price": 130.0,
  "max_premium": 30.0,
  "min_amount": 0.5,
  "max_amount": 10.0,
  "rebalance_days": 5,
  "random_seed": 42
}
```

**响应示例：**
```json
{
  "performance": {
    "total_return": 0.15,
    "annualized_return": 0.18,
    "annualized_volatility": 0.12,
    "sharpe_ratio": 1.5,
    "max_drawdown": -0.05,
    "win_rate": 0.6
  },
  "portfolio": {
    "positions": [
      {
        "symbol": "123001",
        "quantity": 100,
        "quantity_hands": 10,
        "avg_price": 100.0,
        "current_price": 105.0,
        "market_value": 10500.0,
        "profit": 500.0,
        "profit_rate": 5.0
      }
    ],
    "cash": 5000.0,
    "market_value": 95000.0,
    "total_asset": 100000.0,
    "total_profit": 0.0,
    "profit_rate": 0.0,
    "initial_cash": 100000.0,
    "position_count": 10
  },
  "trade_history": [
    {
      "symbol": "123001",
      "action": "buy",
      "quantity": 100,
      "price": 100.0,
      "amount": 10000.0,
      "commission": 5.0,
      "trade_time": "2026-01-02T10:00:00"
    }
  ],
  "start_date": "2025-12-01",
  "end_date": "2026-01-01",
  "trading_days": 20,
  "run_time": "2026-01-02T10:00:00"
}
```

---

## 🛠️ 技术栈总结

| 层级 | 技术栈 | 版本 | 用途 |
|------|--------|------|------|
| **数据层** | Python | 3.8+ | 核心开发语言 |
| | Pandas | 1.5+ | 数据处理和分析 |
| | NumPy | 1.21+ | 数值计算 |
| | Akshare | 1.10+ | 金融数据获取 |
| | Logging | 0.4+ | 日志系统 |
| **策略层** | Python | 3.8+ | 策略实现 |
| | 抽象基类 | - | 策略接口定义 |
| | 工厂方法 | - | 订单创建 |
| **交易层** | Python | 3.8+ | 交易实现 |
| | Dataclasses | - | 数据模型定义 |
| | 数学计算 | - | 成本和收益计算 |
| **API层** | FastAPI | 0.95+ | Web框架 |
| | Pydantic | 1.10+ | 数据验证 |
| | Uvicorn | 0.22+ | ASGI服务器 |
| | CORS | - | 跨域支持 |

---

## 📂 项目结构

```
convertible-bond-strategy/
├── api/                            # API层
│   ├── __init__.py
│   ├── app.py                     # FastAPI应用入口
│   ├── schemas.py                 # Pydantic数据模型
│   ├── controller.py              # 业务控制器
│   └── routes/
│       ├── __init__.py
│       ├── strategy.py             # 策略接口
│       ├── portfolio.py            # 投资组合接口
│       └── backtest.py              # 回测接口
├── data/                           # 数据层
│   ├── __init__.py
│   ├── provider.py                # 数据源抽象基类
│   ├── akshare_provider.py        # Akshare数据源（集思录全量，自动Cookie）
│   ├── efinance_provider.py       # 东方财富备用数据源
│   ├── real_data_provider.py      # 真实数据提供者（akshare优先）
│   └── historical_data_provider.py # 历史数据提供者
├── jisilu_login.py                 # 集思录自动登录（AES加密+Cookie刷新）
├── strategy/                       # 策略层
│   ├── __init__.py
│   ├── base_strategy.py            # 策略抽象基类
│   └── double_low_strategy.py      # 双低策略实现
├── trading/                        # 交易层
│   ├── __init__.py
│   ├── order.py                   # 订单定义
│   ├── portfolio.py               # 投资组合管理
│   └── executor.py                # 交易执行器
├── test_data.py                    # 数据层测试
├── test_strategy.py                # 策略层测试
├── run_backtest.py                 # 模拟数据回测
├── run_backtest_real.py            # 真实数据回测
├── run_backtest_historical.py      # 历史数据回测
├── backtest.log                    # 日志文件
├── backtest_real.log               # 日志文件
├── backtest_historical.log          # 日志文件
├── api.log                         # 日志文件
├── requirements.txt                # 依赖管理
├── .gitignore                       # Git忽略文件
├── README.md                        # 项目说明
└── venv/                            # 虚拟环境
```

---

## 📈 功能完成度

| 模块 | 功能 | 完成度 | 状态 |
|------|------|--------|------|
| **数据层** | 数据获取 | 100% | ✅ 完成 |
| | 数据清洗 | 100% | ✅ 完成 |
| | 数据验证 | 100% | ✅ 完成 |
| **策略层** | 双低策略 | 100% | ✅ 完成 |
| | 多条件筛选 | 100% | ✅ 完成 |
| | 参数验证 | 100% | ✅ 完成 |
| **交易层** | 订单管理 | 100% | ✅ 完成 |
| | 投资组合管理 | 100% | ✅ 完成 |
| | 手续费计算 | 100% | ✅ 完成 |
| | 轮动调仓 | 100% | ✅ 完成 |
| **回测系统** | 模拟回测 | 100% | ✅ 完成 |
| | 真实回测 | 100% | ✅ 完成 |
| | 历史回测 | 100% | ✅ 完成 |
| | 性能指标 | 100% | ✅ 完成 |
| **Web API** | 数据模型 | 100% | ✅ 完成 |
| | 业务控制器 | 100% | ✅ 完成 |
| | 策略接口 | 100% | ✅ 完成 |
| | 投资组合接口 | 100% | ✅ 完成 |
| | 回测接口 | 100% | ✅ 完成 |
| | CORS支持 | 100% | ✅ 完成 |
| | API文档 | 100% | ✅ 完成 |

---

## 🚀 启动和使用

### 配置环境变量

```bash
export JISILU_USER='your_phone_or_email'
export JISILU_PASS='your_password'
```

### 启动API服务

```bash
# 确保虚拟环境已激活
source .venv/bin/activate

# 启动服务（端口 48000）
uvicorn api.app:app --host 0.0.0.0 --port 48000
```

### 访问API文档

- Swagger UI: http://localhost:48000/docs
- ReDoc: http://localhost:48000/redoc

### 健康检查

```bash
curl http://localhost:8000/health
```

---

## 🎉 总结

**✅ 核心功能已完成100%！**

系统具备以下能力：
1. 📊 数据获取（实时+历史）
2. 🎯 策略筛选（双低策略）
3. 💰 模拟交易（买卖+手续费）
4. 📈 回测分析（性能指标）
5. 🌐 Web API（REST接口）

