# 研究文档产出说明

版本：v0.1  
日期：2026-07-07  
阶段：第 1 个月 MVP 冲刺第 1 周  
负责岗位：量化研究员  

## 1. 产出目标

本目录用于把数据工程师已经落地的第 1 周样例数据，转化为策略研发工程师可以实现的研究规则。

本轮需要产出 4 份文档：

```text
股票池规则/stock_pool_rule_v0.1.md
因子定义/factor_spec_week1.md
标签定义/label_spec_v0.1.md
打分规则/score_formula_v0.1.md
```

它们服务于第一个月 MVP 主链路中的这几步：

```text
数据清洗与质检 -> 日频因子生成 -> 标签生成 -> 打分排名 -> 组合生成
```

## 2. 需要用到的数据

| 数据文件 | 用途 |
|---|---|
| `data/week1/clean/sample_stock_pool.csv` | 第 1 周样例股票池，用于确认股票池规则可以在 20-50 只股票上跑通。 |
| `data/week1/clean/fact_daily_bar.csv` | 样例股票日线行情，用于定义并计算收益、均线偏离、波动率、成交额均值等因子。 |
| `data/week1/clean/fact_stock_status.csv` | 样例股票交易状态，用于股票池过滤和交易限制，例如 ST、停牌、涨停、跌停、上市天数。 |
| `data/week1/clean/dim_stock.csv` | 股票基础信息，用于股票代码、名称、交易所和 active 状态判断。 |
| `data/week1/clean/fact_index_daily_bar.csv` | 指数行情，第 1 周不直接进入打分，但可作为后续基准和市场环境输入。 |
| `data/week1/quality/quality_report_v0.1.csv` | 数据质量报告。正式联调前应要求核心检查通过；当前研究文档先基于已落地 clean 样例数据定义规则。 |
| `data/week1/manifest.json` | 数据运行追踪文件，用于确认数据文件来源、run_id、执行命令和保留状态。 |

## 3. 需要参考的文档

| 文档 | 用途 |
|---|---|
| `docs/00_架构/量化系统架构.md` | 确认系统定位为日频波段、多因子、TopN、基础风控，不做高频和复杂模型。 |
| `docs/01_项目管理/第1个月/第一个月MVP冲刺任务书.md` | 确认第一个月主链路、必须做和不做事项。 |
| `docs/01_项目管理/第1个月/第1周/第1周任务清单.md` | 确认第 1 周目标是 3-5 个基础因子、标签、排名和计划单模板。 |
| `docs/01_项目管理/第1个月/第1周/第1周任务分配表.md` | 确认量化研究员本周任务编号和验收标准。 |
| `docs/01_项目管理/第1个月/第1周/6个岗位任务卡.md` | 确认研究员产物要交给策略研发和组合风控使用。 |
| `docs/03_数据/交付记录/第1周/data_handoff_notes.md` | 确认数据字段口径、已知问题和复跑命令。 |

## 4. 需要参考的配置

| 配置文件 | 用途 |
|---|---|
| `configs/model.yaml` | 提供第 1 周规则打分模式、因子分组、打分权重、标签周期。 |
| `configs/risk_limits.yaml` | 提供股票池过滤和交易限制参数，例如 ST、停牌、上市天数、20 日均成交额阈值。 |
| `configs/portfolio.yaml` | 提供 TopN、等权、现金缓冲、单票权重和交易成本假设。 |

## 5. 需要对接的代码

当前这 4 份文档本身不是代码，但必须让后续代码可以直接实现。

后续策略研发工程师应基于这些文档新增或完善：

```text
src/factors/
src/labels/
src/models/ 或 src/reports/
jobs/week1_research_signal_run.py
```

推荐输出文件：

```text
data/week1/feature/feature_factor_value.csv
data/week1/feature/label_forward_return.csv
data/week1/feature/signal_score.csv
data/week1/quality/factor_quality_report_v0.1.csv
```

## 6. 产出过程

### 6.1 股票池规则

先根据 `risk_limits.yaml` 和 `fact_stock_status.csv` 定义可交易股票池。第 1 周规则只做硬过滤：

```text
非 ST
非停牌
上市天数 >= 120
20 日均成交额 >= 3000 万
买入日不涨停
卖出日不跌停
```

注意：`listed_days` 当前部分来自近似口径，正式全市场运行前需要数据工程师补上市日期。

### 6.2 因子定义

根据第 1 周任务清单，优先定义 5 个可以只用日线行情计算的因子：

```text
ret_20d
ret_60d
ma_gap_20d
volatility_20d
amount_ma_20d
```

选择这些因子的原因：

```text
只依赖 close 和 amount，数据工程第 1 周已经提供。
能覆盖中期趋势、低吸位置、风险波动、流动性。
计算简单，适合第 1 周联调。
```

### 6.3 标签定义

标签只用于研究评估和回测，不用于当天选股打分。第 1 周定义：

```text
forward_return_10d
forward_return_20d
```

标签必须从 T+1 开始，避免用 T 日之后不可得信息污染 T 日决策。

### 6.4 打分规则

第 1 周不训练机器学习模型，采用规则打分：

```text
score = 0.4 * trend_score
      + 0.3 * pullback_score
      + 0.2 * liquidity_score
      - 0.1 * risk_score
```

其中趋势、低吸、流动性、风险分数都由第 1 周因子按截面排名或标准化后得到。

## 7. 交付给下游的约定

策略研发工程师实现时，因子输出最少包含：

```text
symbol
trade_date
factor_name
factor_value
factor_version
run_id
```

标签输出最少包含：

```text
symbol
trade_date
horizon
forward_return
run_id
```

打分输出最少包含：

```text
signal_version
symbol
trade_date
alpha_score
rank_num
score_reason
do_not_trade_reason
run_id
```

## 8. 当前约束和风险

1. 当前还没有数据库，研究规则先以 CSV 文件为输入输出。
2. 当前质量报告记录的是一次失败复跑状态；正式联调前需要数据工程师复跑并产出通过的质量报告。
3. 第 1 周暂不使用财务、行业、事件数据做硬过滤。
4. 第 1 周不做 LightGBM，不优化收益，只验证主链路能接上。
