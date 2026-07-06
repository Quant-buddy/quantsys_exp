# quantsys_exp
# 目录
configs/        放配置：数据源、风控阈值、组合参数、模型参数  
src/            核心代码，所有可复用模块都放这里  
jobs/           生产任务入口：每日收盘、周调仓、影子实盘、模型训练  
sql/            建表 SQL、迁移脚本、初始化脚本  
tests/          单元测试、集成测试、回测一致性测试  
notebooks/      研究员探索用 notebook，不能作为生产任务  
docs/           架构文档、数据字典、因子说明、模型说明  
runbooks/       运维手册、故障处理、影子实盘 SOP、实盘审批 SOP  
scripts/        一次性工具脚本、初始化脚本、数据修复脚本  
data/           本地数据目录，只放示例或小样本  
artifacts/      模型文件、回测结果、MLflow产物  
reports/        每日/每周报告模板或样例  

# src/quant_system/
代码主体，按模块划分为：  
common/：公共工具  
data_ingest/：数据采集  
data_quality/：数据质量检查  
warehouse/：数据仓库与存储  
factors/：因子计算  
labels/：标签构建  
models/：训练与推理  
backtest/：回测引擎  
portfolio/：组合构建  
risk/：风控规则  
trading/：计划单、成交回报、持仓  
attribution/：归因分析  
events/：公告与事件辅助  
reports/：报告输出  

# 数据分层  
系统采用四层数据仓库设计：  
raw：原始接口返回  
clean：标准化后的统一数据  
feature：因子、标签、预测结果  
trade：组合、计划单、成交、持仓、归因  