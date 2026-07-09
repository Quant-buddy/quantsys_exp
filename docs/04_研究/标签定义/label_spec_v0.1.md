# 标签定义 v0.1

版本：v0.1
阶段：第 1 个月 MVP 冲刺第 1 周  
负责岗位：量化研究员  
下游使用方：策略研发工程师  

## 1. 目的

本文件定义第 1 周用于研究评估和后续回测的未来收益标签。标签不参与 T 日实时决策，只用于事后评估因子和策略效果。

第 1 周先定义：

```text
forward_return_10d
forward_return_20d
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
```

可选字段：

```text
open
high
low
is_suspended
is_limit_up
is_limit_down
```

第 1 周标签先使用 `close` 计算，不处理复杂成交约束。交易约束由后续回测和计划单模块处理。

## 3. 输出格式

建议输出为：

```text
data/week1/feature/label_forward_return.csv
```

最少字段：

```text
symbol
trade_date
horizon
forward_return
label_version
start_rule
end_rule
run_id
update_time
```

其中：

```text
label_version = week1_v0.1
start_rule = T_plus_1
end_rule = T_plus_horizon_close
```

## 4. 标签计算原则

### 4.1 从 T+1 开始

T 日生成因子和排名，真实计划单只能在 T+1 执行。因此标签不能从 T 日收盘直接开始。

第 1 周统一采用：

```text
start_price = close_{T+1}
end_price = close_{T+horizon}
```

### 4.2 标签公式

对于 horizon = 10：

```text
forward_return_10d = close_{T+10} / close_{T+1} - 1
```

对于 horizon = 20：

```text
forward_return_20d = close_{T+20} / close_{T+1} - 1
```

其中 T+1、T+10、T+20 都按该股票可交易日序列向后偏移，不按自然日。

## 5. 缺失处理

| 情况 | 处理 |
|---|---|
| 没有 T+1 价格 | `forward_return = null` |
| 没有 T+horizon 价格 | `forward_return = null` |
| T+1 或 T+horizon 的 close 缺失 | `forward_return = null` |
| start_price <= 0 | `forward_return = null` |
| 股票在样本末尾不足 horizon | `forward_return = null` |

不要向前填充未来价格，不要用指数收益替代个股缺失标签。

## 6. 未来函数检查

标签是未来收益，本身会使用未来价格，但只能用于：

```text
因子评估
回测评估
训练样本构建
```

禁止用于：

```text
T 日选股
T 日打分
T+1 计划单生成
```

研发实现时必须保证：

```text
feature_factor_value 的计算不引用 label_forward_return
signal_score 的 T 日打分不引用 T 日之后价格
```

## 7. 与回测成交规则的关系

第 1 周标签使用收盘到收盘口径，主要为了简单评估因子方向。

后续正式回测应使用：

```text
买入价 = T+1 开盘价 + 滑点
卖出价 = 后续卖出日开盘价 - 滑点
```

因此标签收益不等于真实回测收益。两者用途不同：

```text
标签：评价因子是否有预测方向
回测：评价策略和交易规则后的组合表现
```

## 8. 输出示例

```text
symbol,trade_date,horizon,forward_return,label_version,start_rule,end_rule,run_id,update_time
000001,2026-01-05,10,0.0321,week1_v0.1,T_plus_1,T_plus_horizon_close,...
000001,2026-01-05,20,0.0487,week1_v0.1,T_plus_1,T_plus_horizon_close,...
```

## 9. 验收标准

第 1 周验收时应满足：

```text
能对样例股票生成 10 日和 20 日标签
标签从 T+1 开始计算
样本末尾不足 horizon 的标签为空
随机抽一只股票可以人工复算 forward_return_10d
标签结果带 run_id
```

## 10. 后续增强

第 2 周后可以补充：

```text
forward_return_5d
excess_return_vs_index
max_drawdown_next_20d
hit_take_profit_flag
hit_stop_loss_flag
基于 T+1 open 的更贴近交易标签
```
