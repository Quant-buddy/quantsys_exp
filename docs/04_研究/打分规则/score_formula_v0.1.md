# 综合打分规则 v0.1

版本：v0.1   
阶段：第 1 个月 MVP 冲刺第 1 周  
负责岗位：量化研究员  
下游使用方：策略研发工程师、组合风控/交易运维  

## 1. 目的

本文件定义第 1 周规则打分方法，用于把基础因子转成股票排名。

第 1 周不训练机器学习模型，只使用可解释的规则分数，目标是跑通：

```text
股票池 -> 因子 -> 综合分 -> 排名 -> TopN 组合
```

## 2. 输入数据

| 输入 | 用途 |
|---|---|
| `data/week1/feature/stock_pool_filtered.csv` | 限定可打分股票范围。 |
| `data/week1/feature/feature_factor_value.csv` | 提供第 1 周 5 个因子。 |
| `configs/model.yaml` | 提供规则打分模式、因子分组和权重。 |
| `configs/risk_limits.yaml` | 提供不可交易原因和过滤阈值。 |

需要的因子：

```text
ret_20d
ret_60d
ma_gap_20d
volatility_20d
amount_ma_20d
```

## 3. 输出格式

建议输出为：

```text
data/week1/feature/signal_score.csv
```

最少字段：

```text
signal_version
symbol
trade_date
alpha_score
rank_num
score_reason
do_not_trade_reason
run_id
update_time
```

其中：

```text
signal_version = rule_topn_v0.1
```

## 4. 打分范围

只对股票池规则中：

```text
in_stock_pool = True
```

的股票计算排名。

不入池股票可以保留在输出中，但必须满足：

```text
alpha_score = null
rank_num = null
do_not_trade_reason = filter_reason
```

## 5. 因子标准化

第 1 周使用按交易日截面排名的方式把因子转成 0-1 分数。

### 5.1 越大越好的因子

适用：

```text
ret_20d
ret_60d
amount_ma_20d
```

分数：

```text
rank_pct = rank(factor_value ascending=True) / valid_count
factor_score = rank_pct
```

含义：值越大，分数越高。

### 5.2 越小越好的因子

适用：

```text
volatility_20d
```

分数：

```text
rank_pct = rank(factor_value ascending=True) / valid_count
risk_score = rank_pct
```

注意：`risk_score` 表示风险大小，越大代表波动越高。最终总分中使用负权重。

### 5.3 适度偏低更好的因子

适用：

```text
ma_gap_20d
```

第 1 周简化为低吸分：

```text
pullback_raw = -ma_gap_20d
pullback_score = rank(pullback_raw ascending=True) / valid_count
```

含义：

```text
ma_gap_20d 越低，pullback_score 越高。
```

注意：如果后续发现极端下跌股票被过度奖励，需要加入趋势保护或异常过滤。

## 6. 分组分数

### 6.1 trend_score

趋势分数：

```text
trend_score = mean(ret_20d_score, ret_60d_score)
```

如果其中一个缺失：

```text
使用非缺失项平均
```

如果两个都缺失：

```text
trend_score = null
```

### 6.2 pullback_score

低吸分数：

```text
pullback_score = score(-ma_gap_20d)
```

### 6.3 liquidity_score

流动性分数：

```text
liquidity_score = amount_ma_20d_score
```

### 6.4 risk_score

风险分数：

```text
risk_score = volatility_20d_score
```

其中风险分数越高表示风险越大。

## 7. 综合分公式

第 1 周采用 `configs/model.yaml` 中的权重：

```text
alpha_score = 0.4 * trend_score
            + 0.3 * pullback_score
            + 0.2 * liquidity_score
            - 0.1 * risk_score
```

解释：

```text
趋势分：偏向中期表现更强的股票
低吸分：偏向趋势内回撤位置
流动性分：偏向更容易成交的股票
风险分：惩罚高波动股票
```

## 8. 排名规则

按每个 `trade_date` 截面：

```text
rank_num = rank(alpha_score descending=True)
```

并列处理：

```text
alpha_score 相同则按 symbol 升序稳定排序
```

无综合分的股票：

```text
rank_num = null
```

## 9. 缺失处理

如果某只股票在某日缺少部分因子：

```text
只要 trend_score、pullback_score、liquidity_score、risk_score 中至少 3 组有效，可以计算 alpha_score。
```

如果有效组少于 3 组：

```text
alpha_score = null
do_not_trade_reason = insufficient_factor_coverage
```

## 10. score_reason

`score_reason` 用于给组合风控和技术负责人解释排名来源。

建议格式：

```text
trend=0.72;pullback=0.63;liquidity=0.81;risk=0.35
```

第 1 周先用字符串即可，后续可以改成结构化 JSON。

## 11. do_not_trade_reason

常见原因：

```text
st_stock
suspended
newly_listed
low_liquidity
limit_up_no_buy
missing_basic_data
insufficient_factor_coverage
data_quality_failed
```

如果股票正常参与排名：

```text
do_not_trade_reason = ""
```

## 12. 验收标准

第 1 周验收时，策略研发工程师应能做到：

```text
对样例股票生成 signal_score.csv
每个交易日可按 alpha_score 排名
rank_num 从 1 开始且无重复
不入池股票有 do_not_trade_reason
随机抽一只股票可以解释综合分来自哪些分组
```

## 13. 后续增强

第 2 周后可以改进：

```text
ma_gap_20d 加入极端下跌惩罚
按行业中性排名
加入指数环境过滤
加入更多趋势、回撤、风险和流动性因子
加入因子 winsorize 和 z-score 标准化
基于历史标签评估权重是否合理
```
