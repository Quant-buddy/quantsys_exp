# 第 1 周因子定义

版本：v0.1
阶段：第 1 个月 MVP 冲刺第 1 周  
负责岗位：量化研究员  
下游使用方：策略研发工程师  

## 1. 目的

本文件定义第 1 周需要落地的 5 个基础日频波段因子。目标是让策略研发工程师可以在样例日线数据上生成 `feature_factor_value`，并为后续打分排名提供输入。

第 1 周不追求因子有效性最优，只追求：

```text
公式清楚
输入字段明确
没有未来函数
可以用现有 clean 数据计算
能支持数据 -> 因子 -> 排名 的第一次联调
```

## 2. 输入数据

主要输入：

```text
data/week1/clean/fact_daily_bar.csv
```

必要字段：

```text
symbol
trade_date
close
amount
```

可选字段：

```text
open
high
low
volume
pct_chg
turnover
```

股票状态输入：

```text
data/week1/clean/fact_stock_status.csv
```

用于后续股票池过滤，不直接参与本文件 5 个因子计算。

## 3. 输出格式

建议输出为长表：

```text
data/week1/feature/feature_factor_value.csv
```

最少字段：

```text
symbol
trade_date
factor_name
factor_value
factor_version
source_quality
run_id
update_time
```

其中：

```text
factor_version = week1_v0.1
source_quality = core
```

## 4. 通用计算规则

### 4.1 日期排序

每只股票必须按 `trade_date` 升序计算滚动窗口。

### 4.2 窗口口径

第 1 周所有因子都使用历史窗口，窗口包含 T 日，不包含 T 日之后数据。

例如 `ret_20d` 在 T 日使用：

```text
close_T
close_{T-20}
```

不使用 T+1 或更晚价格。

### 4.3 缺失值

如果窗口不足或必要字段缺失：

```text
factor_value = null
```

不要用 0 填充，避免把缺失误当成中性信号。

### 4.4 复权口径

第 1 周 `fact_daily_bar.csv` 中价格来自前复权接口或前复权备用接口。因子统一使用 `close` 字段。

后续如果补充 `adj_factor`，需要由数据工程师确认前复权口径是否一致。

## 5. 因子清单

### 5.1 ret_20d

含义：20 个交易日收益率，衡量中短期趋势。

输入字段：

```text
close
```

公式：

```text
ret_20d = close_T / close_{T-20} - 1
```

窗口：

```text
20 个交易日
```

方向：

```text
越大越好
```

缺失处理：

```text
如果 close_T 或 close_{T-20} 缺失，factor_value = null
如果历史不足 20 个交易日，factor_value = null
```

未来函数风险：

```text
无。只使用 T 日及以前的 close。
```

### 5.2 ret_60d

含义：60 个交易日收益率，衡量中期趋势。

输入字段：

```text
close
```

公式：

```text
ret_60d = close_T / close_{T-60} - 1
```

窗口：

```text
60 个交易日
```

方向：

```text
越大越好
```

缺失处理：

```text
如果 close_T 或 close_{T-60} 缺失，factor_value = null
如果历史不足 60 个交易日，factor_value = null
```

未来函数风险：

```text
无。只使用 T 日及以前的 close。
```

### 5.3 ma_gap_20d

含义：收盘价相对 20 日均线的偏离程度，用于判断价格是否处在低吸或过热位置。

输入字段：

```text
close
```

公式：

```text
ma20_T = mean(close over T-19 to T)
ma_gap_20d = close_T / ma20_T - 1
```

窗口：

```text
20 个交易日
```

方向：

```text
第 1 周用于低吸打分时，适度偏低更好。
```

建议打分解释：

```text
ma_gap_20d < 0 表示价格低于 20 日均线，可能处于回撤低吸区。
ma_gap_20d 过高表示短期偏热，不优先买入。
```

缺失处理：

```text
如果历史不足 20 个交易日，factor_value = null
```

未来函数风险：

```text
无。只使用 T 日及以前的 close。
```

### 5.4 volatility_20d

含义：20 日收益率波动率，衡量风险。

输入字段：

```text
close
```

中间变量：

```text
daily_ret_t = close_t / close_{t-1} - 1
```

公式：

```text
volatility_20d = std(daily_ret over T-19 to T)
```

窗口：

```text
20 个交易日收益率
```

方向：

```text
越小越好
```

缺失处理：

```text
如果历史不足 21 个交易日，factor_value = null
如果窗口内收益率有效数量不足 20，factor_value = null
```

未来函数风险：

```text
无。只使用 T 日及以前的 close。
```

### 5.5 amount_ma_20d

含义：20 日平均成交额，衡量流动性。

输入字段：

```text
amount
```

公式：

```text
amount_ma_20d = mean(amount over T-19 to T)
```

窗口：

```text
20 个交易日
```

方向：

```text
越大越好
```

用途：

```text
股票池过滤：amount_ma_20d >= 30000000
打分规则：作为流动性分数输入
```

缺失处理：

```text
如果历史不足 20 个交易日，factor_value = null
如果 amount 缺失，factor_value = null
```

未来函数风险：

```text
无。只使用 T 日及以前的 amount。
```

## 6. 因子分组

| 因子 | 分组 | 打分方向 |
|---|---|---|
| `ret_20d` | trend | 越大越好 |
| `ret_60d` | trend | 越大越好 |
| `ma_gap_20d` | pullback | 适度偏低更好 |
| `volatility_20d` | risk | 越小越好 |
| `amount_ma_20d` | liquidity | 越大越好 |

## 7. 与股票池规则的关系

`amount_ma_20d` 同时用于：

```text
股票池过滤
流动性打分
```

股票池过滤先执行，打分只对入池股票进行。

## 8. 验收标准

第 1 周验收时，策略研发工程师应能做到：

```text
对 sample_stock_pool 中每只股票生成上述 5 个因子
每个因子输出 symbol、trade_date、factor_name、factor_value、factor_version、run_id
窗口不足时输出 null，而不是 0
随机抽一只股票可以人工复算 ret_20d 和 amount_ma_20d
```

## 9. 后续增强

第 2 周后可以扩展：

```text
ret_5d
ret_10d
ma_gap_60d
ma_slope_20d
max_drawdown_20d
turnover_20d
industry_relative_return
```
