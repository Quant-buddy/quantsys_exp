# 第 1 周量化研究文档检查报告

检查日期：2026-07-08  
检查对象：量化研究员第 1 周 4 份产出  
检查结论：有条件通过

## 1. 检查范围

| 文档 | 状态 | 结论 |
|---|---|---|
| `docs/04_研究/股票池规则/stock_pool_rule_v0.1.md` | 已交付 | 通过 |
| `docs/04_研究/因子定义/factor_spec_week1.md` | 已交付 | 通过 |
| `docs/04_研究/标签定义/label_spec_v0.1.md` | 已交付 | 通过 |
| `docs/04_研究/打分规则/score_formula_v0.1.md` | 已交付 | 有条件通过 |

## 2. 检查方法

本次从五个角度检查：

```text
字段是否能被现有数据支撑
公式是否可实现
是否存在未来函数风险
上下游接口是否明确
是否与 configs 配置一致
```

## 3. 检查结论

### 3.1 股票池规则

结论：通过。

理由：

```text
输入字段可由 sample_stock_pool.csv、fact_daily_bar.csv、fact_stock_status.csv 支撑
ST、停牌、上市天数、流动性、涨停买入限制口径明确
filter_reason 枚举可被组合风控复用
```

注意事项：

```text
listed_days 当前样例多为 9999，是数据兜底值，不是真实上市天数
跌停卖出限制不应简单作为买入候选池过滤条件，应由组合风控处理
```

### 3.2 因子定义

结论：通过。

理由：

```text
5 个第 1 周因子均可由 fact_daily_bar.csv 计算
窗口都只使用 T 日及以前数据
缺失值处理明确为 null
输出长表格式清楚
```

需研发确认：

```text
ret_20d 使用 close_T / close_{T-20} - 1，实际需要至少 21 行价格
volatility_20d 使用 20 个 daily_ret，实际需要至少 21 行价格
rolling std 需要统一 ddof 口径，建议第 1 周使用 pandas 默认样本标准差并在实现说明中记录
```

### 3.3 标签定义

结论：通过。

理由：

```text
forward_return_10d/20d 从 T+1 开始
明确标签只用于评估，不进入 T 日打分
样本末尾不足 horizon 时输出 null
```

需研发确认：

```text
T+1、T+10、T+20 按该股票可用交易序列偏移，还是按全市场交易日历偏移后再检查个股是否有价格
第 1 周可以先按个股价格序列实现，但第 2 周应与回测交易日历口径统一
```

### 3.4 打分规则

结论：有条件通过。

理由：

```text
股票池 -> 因子 -> 标准化 -> 分组分数 -> alpha_score -> rank_num 链路完整
权重清楚，score_reason 可解释
不入池股票的 do_not_trade_reason 处理明确
```

已修复问题：

```text
configs/model.yaml 原先 trend 里包含 ma_gap_20d，pullback 里残留 ret_5d、price_to_ma20
已调整为 trend=[ret_20d, ret_60d]，pullback=[ma_gap_20d]
```

仍需研发确认：

```text
rank_pct 并列值处理方式
valid_count=1 时 rank_pct 是否允许为 1
缺失部分分组时 alpha_score 是否按原权重直接求和，还是按有效权重重归一
```

建议第 1 周采用：缺失分组不重归一，至少 3 组有效才计算，保持规则简单可复现。

## 4. 量化研究员本周进度

按 `第1周任务分配表.md`，量化研究员本周任务进度如下：

| 编号 | 任务 | 产物 | 当前状态 |
|---|---|---|---|
| QR-W1-01 | 定股票池过滤规则 | `stock_pool_rule_v0.1.md` | 已完成 |
| QR-W1-02 | 定第 1 周因子公式 | `factor_spec_week1.md` | 已完成 |
| QR-W1-03 | 定标签计算规则 | `label_spec_v0.1.md` | 已完成 |
| QR-W1-04 | 检查因子实现结果 | `factor_check_notes.md` | 未开始/待下游输出 |
| QR-W1-05 | 定综合打分公式 | `score_formula_v0.1.md` | 已完成，配置已同步 |

当前进度判断：

```text
规则定义类任务完成约 80%
依赖策略研发输出的实现检查尚未完成
第 1 周验收前还需要形成 factor_check_notes.md 和 research_issue_list.md
```

## 5. 剩余任务

量化研究员本周剩余任务：

```text
1. 等策略研发生成 feature_factor_value.csv 后，抽样复算 ret_20d、amount_ma_20d、volatility_20d。
2. 检查 label_forward_return.csv 是否从 T+1 开始，样本尾部是否正确置空。
3. 检查 signal_score.csv 是否只对 in_stock_pool=True 的股票排名。
4. 输出 factor_check_notes.md。
5. 输出 research_issue_list.md，列出第 2 周需要补充的因子、标签和未来函数检查项。
```

## 6. 对下游的验收建议

策略研发工程师交付后，按以下最小检查执行：

```text
随机抽 1 只股票、1 个交易日，人工复算 ret_20d
随机抽 1 只股票、1 个交易日，人工复算 amount_ma_20d
检查窗口不足时 factor_value 是否为空
检查标签是否没有进入 signal_score
检查 rank_num 是否从 1 开始且同日无重复
检查 do_not_trade_reason 是否覆盖不入池原因
```

## 7. 风险与建议

| 风险 | 影响 | 建议 |
|---|---|---|
| 上市天数字段当前为兜底值 | 新股过滤暂不真实 | 第 2 周由数据工程师补真实 list_date/listed_days |
| 样例池只有 30 只股票 | 截面排名稳定性有限 | 第 2 周扩展到全市场或至少更大样例池 |
| 尚无实现输出 | 不能完成因子公式一致性检查 | 策略研发先产出最小 feature/label/signal 文件 |
| 财务和行业未接入 | 行业中性和基本面过滤暂不可做 | 不阻塞第 1 周主链路，进入第 2 周任务 |
