# 数据工程师第 1 周交接说明

版本：v0.1
运行批次：见各 CSV 的 `run_id` 字段  

---

## 1. 交付范围

本次交付覆盖数据工程师第 1 周任务：

```text
DE-W1-01 测试 AKShare 股票列表接口
DE-W1-02 测试 AKShare/pytdx 日线接口
DE-W1-03 拉取股票列表
DE-W1-04 拉取交易日历
DE-W1-05 拉取 20-50 只样例股票 3 年日线
DE-W1-06 拉取 1-2 个指数日线
DE-W1-07 初步识别停牌/涨跌停
DE-W1-08 输出数据质量报告草案
```

---

## 2. 输出位置

样例数据：

```text
data/week1/manifest.json
data/week1/raw/akshare_sample_output.csv
data/week1/raw/data_source_probe.csv
data/week1/raw/pytdx_sample_output.csv
data/week1/clean/dim_stock.csv
data/week1/clean/dim_trade_calendar.csv
data/week1/clean/sample_stock_pool.csv
data/week1/clean/fact_daily_bar.csv
data/week1/clean/fact_index_daily_bar.csv
data/week1/clean/fact_stock_status.csv
data/week1/quality/quality_report_v0.1.csv
```

文档：

```text
docs/03_数据/交付记录/第1周/akshare_probe.md
docs/03_数据/交付记录/第1周/pytdx_probe.md
docs/03_数据/交付记录/第1周/data_source_probe.md
docs/03_数据/交付记录/第1周/data_issue_list.md
docs/03_数据/交付记录/第1周/data_handoff_notes.md
```

代码：

```text
src/data_ingest/week1_sample_data.py
src/data_quality/week1_quality.py
jobs/week1_data_engineer_run.py
```

---

## 3. 字段口径

### 3.1 股票代码

`symbol` 使用 6 位股票代码，例如：

```text
000001
600000
300750
688981
```

注意：

```text
读取 CSV 时必须把 symbol 当作字符串读取。
不要让 pandas 默认转成整数，否则 000001 会显示成 1。
```

建议读取方式：

```python
import pandas as pd

daily_bar = pd.read_csv("data/week1/clean/fact_daily_bar.csv", dtype={"symbol": str})
```

### 3.2 日期

`trade_date` 使用：

```text
YYYY-MM-DD
```

### 3.3 价格

个股日线价格来自 AKShare 免费接口，优先探查：

```text
akshare.stock_zh_a_hist(adjust="qfq")
```

如果该接口失败，自动 fallback：

```text
akshare.stock_zh_a_daily(adjust="qfq")
```

第 1 周样例数据中的 `source` 字段会标明实际来源。

### 3.4 成交量和成交额

当前样例中：

```text
volume：股
amount：元
```

第 2 周扩展全市场前，需要继续抽样确认不同接口的单位是否完全一致。

### 3.5 复权

第 1 周使用前复权价格，`adj_factor` 暂为空。

原因：

```text
当前免费接口直接返回前复权价格，但没有稳定提供逐日复权因子。
第 2 周需要补充复权因子校验或自算方案。
```

---

## 4. 股票状态口径

`fact_stock_status.csv` 当前字段：

```text
is_st
is_suspended
is_limit_up
is_limit_down
up_limit_price
down_limit_price
listed_days
```

说明：

```text
is_suspended：由交易日历与个股日线缺失交叉判断。
is_limit_up/is_limit_down：按涨跌幅近似判断。
listed_days：当前样例股票列表接口未提供上市日期时填 9999。
```

第 2 周必须增强：

```text
补上市日期
补 ST 历史状态
补更严谨的涨跌停规则
```

---

## 5. 质量报告结论

质量报告位置：

```text
data/week1/quality/quality_report_v0.1.csv
```

当前检查项：

```text
股票列表存在
交易日历存在
日线数据存在
OHLC 合法
成交量成交额非负
核心字段非空
样例日线覆盖率
股票状态字段存在
```

质量报告所有检查项应为 PASS，才能交给研发继续使用。

---

## 6. 运行追踪

运行清单位置：

```text
data/week1/manifest.json
```

该文件记录：

```text
run_id
operator
command
git_commit
started_at
ended_at
outputs
```

如果本次数据源异常导致核心 clean 层数据为空，脚本会保留已有 clean 层文件，并在 manifest 的 `write_status` 中记录 `skipped_incomplete_run_preserved` 或 `skipped_empty_preserved`。

---

## 7. 已知问题

已知问题记录在：

```text
docs/03_数据/交付记录/第1周/data_issue_list.md
```

当前主要问题：

```text
1. akshare.stock_zh_a_hist 在本次运行中多只股票被远端断开。
2. 已使用 akshare.stock_zh_a_daily 备用接口补齐样例日线。
3. pytdx 当前连接失败，暂不阻塞第 1 周主链路。
4. 上市日期、历史 ST 状态、复权因子需要第 2 周增强。
```

---

## 8. 复跑命令

在项目根目录执行：

```bash
python jobs/week1_data_engineer_run.py --start-date 2023-01-01 --end-date 2026-07-07 --operator 数据工程师姓名或账号
```

如果需要指定 run_id：

```bash
python jobs/week1_data_engineer_run.py --start-date 2023-01-01 --end-date 2026-07-07 --run-id 手工指定run_id --operator 数据工程师姓名或账号
```

