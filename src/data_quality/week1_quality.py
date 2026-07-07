"""第 1 周样例行情数据质量检查。"""

from __future__ import annotations

from datetime import datetime

import pandas as pd


def build_quality_report(
    stock_list: pd.DataFrame,
    trade_calendar: pd.DataFrame,
    daily_bars: pd.DataFrame,
    stock_status: pd.DataFrame,
    run_id: str,
    min_coverage: float = 0.99,
) -> pd.DataFrame:
    """生成符合第 1 周验收清单的轻量数据质量报告。"""
    checks: list[dict[str, object]] = []

    def add(
        check_name: str,
        ok: bool,
        severity: str,
        affected_rows: int,
        detail: str,
        should_block: bool,
    ) -> None:
        checks.append({
            "report_id": f"{run_id}_{len(checks) + 1:03d}",
            "trade_date": "",
            "check_name": check_name,
            "check_status": "PASS" if ok else "FAIL",
            "severity": severity,
            "affected_rows": affected_rows,
            "threshold_text": "",
            "detail": detail,
            "should_block_plan": bool(should_block),
            "run_id": run_id,
            "update_time": datetime.now().isoformat(timespec="seconds"),
        })

    add(
        "stock_list_exists",
        not stock_list.empty,
        "P0",
        0 if not stock_list.empty else 1,
        f"stock_count={len(stock_list)}",
        stock_list.empty,
    )
    add(
        "trade_calendar_exists",
        not trade_calendar.empty,
        "P0",
        0 if not trade_calendar.empty else 1,
        f"calendar_rows={len(trade_calendar)}",
        trade_calendar.empty,
    )
    add(
        "daily_bar_exists",
        not daily_bars.empty,
        "P0",
        0 if not daily_bars.empty else 1,
        f"daily_bar_rows={len(daily_bars)}",
        daily_bars.empty,
    )

    if not daily_bars.empty:
        illegal_ohlc = daily_bars[
            (daily_bars["high"] < daily_bars[["open", "close", "low"]].max(axis=1))
            | (daily_bars["low"] > daily_bars[["open", "close", "high"]].min(axis=1))
        ]
        add(
            "ohlc_legal",
            illegal_ohlc.empty,
            "P0",
            len(illegal_ohlc),
            "high must be >= open/close/low and low must be <= open/close/high",
            not illegal_ohlc.empty,
        )

        negative_amount = daily_bars[
            (pd.to_numeric(daily_bars["volume"], errors="coerce") < 0)
            | (pd.to_numeric(daily_bars["amount"], errors="coerce") < 0)
        ]
        add(
            "volume_amount_non_negative",
            negative_amount.empty,
            "P0",
            len(negative_amount),
            "volume and amount must be non-negative",
            not negative_amount.empty,
        )

        missing_core = daily_bars[["open", "high", "low", "close", "volume", "amount"]].isna().any(axis=1)
        add(
            "daily_bar_core_fields_not_null",
            not missing_core.any(),
            "P1",
            int(missing_core.sum()),
            "open/high/low/close/volume/amount should be present",
            bool(missing_core.any()),
        )

    if not trade_calendar.empty and not stock_list.empty and not daily_bars.empty:
        bar_dates = pd.to_datetime(daily_bars["trade_date"])
        min_bar_date = bar_dates.min()
        max_bar_date = bar_dates.max()
        calendar_dates = pd.to_datetime(trade_calendar["trade_date"])
        active_calendar = trade_calendar[(calendar_dates >= min_bar_date) & (calendar_dates <= max_bar_date)]
        sample_symbols = daily_bars["symbol"].nunique()
        trade_days = pd.to_datetime(active_calendar["trade_date"]).nunique()
        expected = sample_symbols * trade_days
        actual = len(daily_bars[["symbol", "trade_date"]].drop_duplicates())
        coverage = actual / expected if expected else 0
        add(
            "sample_daily_bar_coverage",
            coverage >= min_coverage,
            "P1",
            max(expected - actual, 0),
            f"coverage={coverage:.4f}, expected={expected}, actual={actual}",
            coverage < min_coverage,
        )

    if not stock_status.empty:
        required_cols = {"is_st", "is_suspended", "is_limit_up", "is_limit_down", "listed_days"}
        missing_cols = required_cols - set(stock_status.columns)
        add(
            "stock_status_fields_exist",
            not missing_cols,
            "P0",
            len(missing_cols),
            f"missing_cols={sorted(missing_cols)}",
            bool(missing_cols),
        )

    return pd.DataFrame(checks)
