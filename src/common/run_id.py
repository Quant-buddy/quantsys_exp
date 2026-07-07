"""生成可追踪的 run_id，供 MVP 阶段各类任务共用。"""

from __future__ import annotations

from datetime import datetime


def make_run_id(task_name: str, trade_date: str | None = None) -> str:
    """生成一个便于人工阅读和排查的 run_id。

    格式遵循第 1 周技术负责人规范：
    任务名_交易日期_运行时间。
    """
    now = datetime.now()
    safe_task = task_name.strip().lower().replace("-", "_").replace(" ", "_")
    date_part = (trade_date or now.strftime("%Y-%m-%d")).replace("-", "")
    return f"{safe_task}_{date_part}_{now.strftime('%Y%m%dT%H%M%S')}"
