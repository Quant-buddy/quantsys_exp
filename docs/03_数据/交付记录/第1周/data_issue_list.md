# 数据问题清单

| 问题编号 | 发现日期 | 模块 | 优先级 | 问题描述 | 是否阻塞主链路 | 负责人 | 状态 |
|---|---|---|---|---|---|---|---|
| DATA-001 | 2026-07-07 | 样例股票池 | P2 | 固定样例池中缺失: 000001, 000002, 000333, 000651, 000858, 002230, 002241, 002415, 002475, 002594, 300059, 300124, 300274, 300308, 300750, 600000, 600030, 600036, 600276, 600309, 600436, 600519, 601012, 601318, 601899, 688008, 688012, 688036, 688111, 688981 | 否 | 数据工程师 | 待确认 |
| DATA-002 | 2026-07-07 | akshare | P1 | stock_info_a_code_name 失败: SSLError(MaxRetryError("HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /sseQuery/commonQuery.do?STOCK_TYPE=1&REG_PROVINCE=&CSRC_CODE=&STOCK_CODE=&sqlId=COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L&COMPANY_STATUS=2%2C4%2C5%2C7%2C8&type=inParams&isPagination=true&pageHelp.cacheSize=1&pageHelp.beginPage=1&pageHelp.pageSize=10000&pageHelp.pageNo=1&pageHelp.endPage=1 (Caused by SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol (_ssl.c:997)')))")) | 否 | 数据工程师 | 待处理 |
| DATA-003 | 2026-07-07 | akshare | P1 | tool_trade_date_hist_sina 失败: SSLError(MaxRetryError("HTTPSConnectionPool(host='finance.sina.com.cn', port=443): Max retries exceeded with url: /realstock/company/klc_td_sh.txt (Caused by SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol (_ssl.c:997)')))")) | 否 | 数据工程师 | 待处理 |
| DATA-004 | 2026-07-07 | pytdx | P1 | connect:119.147.212.81:7709 失败: 连接返回 False | 否 | 数据工程师 | 待处理 |
