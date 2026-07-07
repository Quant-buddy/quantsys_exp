# run_id 规则草案

版本：v0.1
状态：第 1 周可先执行，后续可迭代  

---

## 1. run_id 的目的

run_id 用于追踪一次任务运行产生的所有结果。

任何关键产物都必须能够回答：

```text
它是哪次任务生成的？
使用了哪些输入？
生成了哪些输出？
能不能复跑？
```

---

## 2. run_id 格式

第一个月先采用简单可读格式：

```text
任务名_交易日期_运行时间
```

示例：

```text
daily_after_close_20260707_20260707T183000
build_factors_20260707_20260707T184500
generate_order_plan_20260707_20260707T191000
```

---

## 3. 命名规则

```text
1. 任务名使用小写英文和下划线。
2. 交易日期使用 YYYYMMDD。
3. 运行时间使用 YYYYMMDDTHHMMSS。
4. 同一任务重复运行必须生成新的 run_id。
5. 不允许手工复用旧 run_id 覆盖结果。
```

---

## 4. 必须携带 run_id 的产物

```text
raw 数据批次
clean 数据批次
quality_report
feature_factor_value
label_forward_return
signal_score
portfolio_target
risk_check_report
order_plan
execution_report
holding_snapshot
日报和回测报告
```

---

## 5. 第 1 周验收方法

周五验收时，技术负责人随机抽一只股票，检查：

```text
1. 它的日线数据来自哪个 run_id。
2. 它的因子来自哪个 run_id。
3. 它的排名来自哪个 run_id。
4. 它是否进入 portfolio_target。
5. 它是否被 risk_check_report 拦截。
6. 它是否进入 order_plan。
```

如果无法反查，则 run_id 规则未通过验收。

