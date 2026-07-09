# 股票池过滤规则 v0.1

版本：v0.1
阶段：第 1 个月 MVP 冲刺第 1 周  
负责岗位：量化研究员  
下游使用方：策略研发工程师、组合风控/交易运维  

## 1. 目的

本规则用于从第 1 周样例股票数据中筛选出可参与因子计算、打分排名和组合生成的候选股票。

第 1 周目标不是形成最终股票池，而是先建立可执行、可解释、可被风控复用的最小过滤规则。

## 2. 输入数据

| 数据 | 必要字段 | 用途 |
|---|---|---|
| `data/week1/clean/sample_stock_pool.csv` | `symbol`, `exchange`, `stock_name`, `is_active` | 第 1 周样例股票池。 |
| `data/week1/clean/fact_daily_bar.csv` | `symbol`, `trade_date`, `close`, `amount` | 计算 20 日均成交额和确认行情可用性。 |
| `data/week1/clean/fact_stock_status.csv` | `symbol`, `trade_date`, `is_st`, `is_suspended`, `is_limit_up`, `is_limit_down`, `listed_days` | 执行 ST、停牌、涨跌停、上市天数过滤。 |
| `configs/risk_limits.yaml` | `stock_filter`, `trade_restriction` | 读取过滤阈值和交易限制参数。 |

## 3. 输出结果

建议输出为：

```text
data/week1/feature/stock_pool_filtered.csv
```

最少字段：

```text
symbol
trade_date
in_stock_pool
filter_reason
amount_ma_20d
is_st
is_suspended
is_limit_up
is_limit_down
listed_days
run_id
```

## 4. 过滤规则

### 4.1 基础有效性

股票必须满足：

```text
symbol 存在于 sample_stock_pool.csv
is_active = True
trade_date 当天有可用日线行情
close 非空且大于 0
```

不满足时：

```text
in_stock_pool = False
filter_reason = missing_basic_data
```

### 4.2 ST 过滤

规则：

```text
is_st = False
```

不满足时：

```text
filter_reason = st_stock
```

说明：第 1 周的 ST 状态来自 `fact_stock_status.csv`，后续需要数据工程师补充历史 ST 状态的更严谨口径。

### 4.3 停牌过滤

规则：

```text
is_suspended = False
```

不满足时：

```text
filter_reason = suspended
```

说明：停牌股票不参与买入、卖出和新组合生成。

### 4.4 上市天数过滤

规则：

```text
listed_days >= 120
```

不满足时：

```text
filter_reason = newly_listed
```

注意：当前第 1 周数据中 `listed_days` 可能因缺少真实上市日期而填充为 `9999`。第 2 周需要由数据工程师补上市日期，届时本规则保持不变，只替换数据口径。

### 4.5 流动性过滤

规则：

```text
amount_ma_20d >= 30000000
```

其中：

```text
amount_ma_20d = mean(amount over last 20 trading days, including T)
```

不满足时：

```text
filter_reason = low_liquidity
```

说明：第 1 周先使用 3000 万元作为最小成交额阈值，对应 `configs/risk_limits.yaml` 中 `min_amount_ma_20d`。

### 4.6 涨跌停交易限制

买入限制：

```text
is_limit_up = False
```

如果涨停：

```text
filter_reason = limit_up_no_buy
```

卖出限制：

```text
is_limit_down = False
```

如果跌停：

```text
filter_reason = limit_down_no_sell
```

说明：股票池过滤主要服务买入候选池，因此默认涨停股票不进入买入候选。跌停限制主要由后续组合风控在卖出计划中处理。

## 5. 第 1 周候选池定义

第 1 周用于打分排名的候选池：

```text
基础有效性通过
非 ST
非停牌
上市天数 >= 120
20 日均成交额 >= 3000 万
非涨停
```

候选池表达式：

```text
in_stock_pool =
    is_active
    and has_daily_bar
    and close > 0
    and not is_st
    and not is_suspended
    and listed_days >= 120
    and amount_ma_20d >= 30000000
    and not is_limit_up
```

## 6. 缺失值处理

| 字段 | 缺失处理 |
|---|---|
| `is_st` | 缺失视为不可确认，默认不进入股票池。 |
| `is_suspended` | 缺失视为不可确认，默认不进入股票池。 |
| `listed_days` | 缺失时默认不进入股票池；第 1 周样例中 `9999` 视为数据源未提供上市日期的兜底值。 |
| `amount_ma_20d` | 不足 20 个交易日或缺失时，不进入股票池。 |
| `close` | 缺失或非正数，不进入股票池。 |

## 7. 与下游的关系

策略研发工程师使用本规则生成 `stock_pool_filtered.csv`。  
量化研究员使用候选池检查因子覆盖率。  
组合风控/交易运维复用本规则中的 ST、停牌、涨跌停和流动性限制。

## 8. 验收标准

第 1 周验收时，本规则满足：

```text
可以对 sample_stock_pool 中每只股票、每个 trade_date 给出是否入池
被排除股票有 filter_reason
过滤结果可与 signal_score 和 order_plan 通过 symbol、trade_date、run_id 串联
```

## 9. 后续增强

第 2 周后补充：

```text
真实上市日期
历史 ST 状态
更严谨涨跌停规则
行业覆盖检查
全市场股票池过滤
数据质量失败时整体阻断股票池生成
```
