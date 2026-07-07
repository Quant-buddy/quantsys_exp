"""第 1 周数据工程师样例数据采集模块。

本模块用于完成第 1 周任务卡要求的数据交接：
股票列表、交易日历、样例股票日线、指数日线和股票状态。

代码优先使用真实免费数据源。接口失败时会明确记录失败原因，
不会伪造行情数据；这是为了遵守 MVP 原则：核心数据异常时，
下游交易计划必须能被阻断或明确降级。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


SAMPLE_SYMBOLS = [
    # 大市值、高流动性的主板股票。
    "000001", "000002", "000333", "000651", "000858",
    "600000", "600030", "600036", "600519", "601318",
    # 创业板、科创板和科技成长类样例。
    "300059", "300124", "300274", "300308", "300750",
    "688008", "688012", "688036", "688111", "688981",
    # 中小市值及更多行业覆盖样例。
    "002230", "002241", "002415", "002475", "002594",
    "600276", "600309", "600436", "601012", "601899",
]

INDEX_SYMBOLS = {
    "000300": "sh000300",  # 沪深300
    "000905": "sh000905",  # 中证500
    "000852": "sh000852",  # 中证1000
    "000001": "sh000001",  # 上证指数
}


@dataclass
class ProbeResult:
    source: str
    target: str
    ok: bool
    detail: str


def _import_akshare() -> Any:
    import akshare as ak  # type: ignore

    return ak


def _exchange_from_symbol(symbol: str) -> str:
    if symbol.startswith(("600", "601", "603", "605", "688")):
        return "SH"
    if symbol.startswith(("000", "001", "002", "003", "300", "301")):
        return "SZ"
    if symbol.startswith(("4", "8", "9")):
        return "BJ"
    return "UNKNOWN"


def _akshare_prefixed_symbol(symbol: str) -> str:
    exchange = _exchange_from_symbol(symbol)
    if exchange == "SH":
        return f"sh{symbol}"
    if exchange == "SZ":
        return f"sz{symbol}"
    if exchange == "BJ":
        return f"bj{symbol}"
    return symbol


def _limit_threshold(symbol: str, stock_name: str = "") -> float:
    # 第 1 周先用近似规则打通风控链路：
    # 主板 10%，科创板/创业板 20%，北交所 30%，ST 5%。
    # 这足够支持初始风控联调，后续应替换为按交易所规则版本化的精确实现。
    if "ST" in str(stock_name).upper():
        return 0.05
    if symbol.startswith(("300", "301", "688")):
        return 0.20
    if symbol.startswith(("4", "8", "9")):
        return 0.30
    return 0.10


def fetch_stock_list(run_id: str) -> tuple[pd.DataFrame, list[ProbeResult]]:
    probes: list[ProbeResult] = []
    try:
        ak = _import_akshare()
        raw = ak.stock_info_a_code_name()
        probes.append(ProbeResult("akshare", "stock_info_a_code_name", True, f"rows={len(raw)}"))
    except Exception as exc:  # pragma: no cover - depends on network/source
        probes.append(ProbeResult("akshare", "stock_info_a_code_name", False, repr(exc)))
        return pd.DataFrame(), probes

    df = raw.rename(columns={"code": "symbol", "name": "stock_name"}).copy()
    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    df["exchange"] = df["symbol"].map(_exchange_from_symbol)
    df["list_date"] = pd.NA
    df["delist_date"] = pd.NA
    df["is_active"] = ~df["stock_name"].astype(str).str.contains("退", na=False)
    df["source"] = "akshare.stock_info_a_code_name"
    df["run_id"] = run_id
    df["update_time"] = datetime.now().isoformat(timespec="seconds")
    return df[[
        "symbol", "exchange", "stock_name", "list_date", "delist_date",
        "is_active", "source", "run_id", "update_time",
    ]], probes


def fetch_trade_calendar(run_id: str) -> tuple[pd.DataFrame, list[ProbeResult]]:
    probes: list[ProbeResult] = []
    try:
        ak = _import_akshare()
        raw = ak.tool_trade_date_hist_sina()
        probes.append(ProbeResult("akshare", "tool_trade_date_hist_sina", True, f"rows={len(raw)}"))
    except Exception as exc:  # pragma: no cover - depends on network/source
        probes.append(ProbeResult("akshare", "tool_trade_date_hist_sina", False, repr(exc)))
        return pd.DataFrame(), probes

    df = raw.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df = df.sort_values("trade_date").drop_duplicates("trade_date")
    df["is_open"] = True
    df["pre_trade_date"] = df["trade_date"].shift(1)
    df["next_trade_date"] = df["trade_date"].shift(-1)
    df["source"] = "akshare.tool_trade_date_hist_sina"
    df["run_id"] = run_id
    df["update_time"] = datetime.now().isoformat(timespec="seconds")
    return df[[
        "trade_date", "is_open", "pre_trade_date", "next_trade_date",
        "source", "run_id", "update_time",
    ]], probes


def fetch_daily_bars(
    symbols: list[str],
    stock_map: pd.DataFrame,
    start_date: str,
    end_date: str,
    run_id: str,
) -> tuple[pd.DataFrame, list[ProbeResult]]:
    probes: list[ProbeResult] = []
    frames: list[pd.DataFrame] = []
    try:
        ak = _import_akshare()
    except Exception as exc:
        return pd.DataFrame(), [ProbeResult("akshare", "import", False, repr(exc))]

    stock_names = dict(zip(stock_map.get("symbol", []), stock_map.get("stock_name", [])))
    for symbol in symbols:
        raw = pd.DataFrame()
        source_name = ""
        try:
            raw = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )
            probes.append(ProbeResult("akshare", f"stock_zh_a_hist:{symbol}", True, f"rows={len(raw)}"))
        except Exception as exc:  # pragma: no cover - depends on network/source
            probes.append(ProbeResult("akshare", f"stock_zh_a_hist:{symbol}", False, repr(exc)))
        if not raw.empty:
            source_name = "akshare.stock_zh_a_hist.qfq"
            df = raw.rename(columns={
                "日期": "trade_date",
                "股票代码": "symbol",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "涨跌幅": "pct_chg",
                "换手率": "turnover",
            }).copy()
        else:
            # 备用数据源：该接口字段结构不同，并且要求带交易所前缀的代码，
            # 例如 sz000001、sh600000。
            prefixed = _akshare_prefixed_symbol(symbol)
            try:
                raw = ak.stock_zh_a_daily(
                    symbol=prefixed,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust="qfq",
                )
                probes.append(ProbeResult("akshare", f"stock_zh_a_daily:{prefixed}", True, f"rows={len(raw)}"))
            except Exception as exc:  # pragma: no cover - depends on network/source
                probes.append(ProbeResult("akshare", f"stock_zh_a_daily:{prefixed}", False, repr(exc)))
                continue
            if raw.empty:
                continue
            source_name = "akshare.stock_zh_a_daily.qfq"
            df = raw.rename(columns={"date": "trade_date"}).copy()
            df["symbol"] = symbol
            df["pct_chg"] = df["close"].pct_change() * 100

        df["symbol"] = df["symbol"].astype(str).str.zfill(6)
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        df = df.sort_values(["symbol", "trade_date"])
        df["pre_close"] = df.groupby("symbol")["close"].shift(1)
        df["adj_factor"] = pd.NA
        df["stock_name"] = df["symbol"].map(stock_names)
        df["source"] = source_name
        df["run_id"] = run_id
        df["update_time"] = datetime.now().isoformat(timespec="seconds")
        frames.append(df[[
            "symbol", "stock_name", "trade_date", "open", "high", "low",
            "close", "pre_close", "volume", "amount", "adj_factor",
            "pct_chg", "turnover", "source", "run_id", "update_time",
        ]])

    if not frames:
        return pd.DataFrame(), probes
    return pd.concat(frames, ignore_index=True), probes


def fetch_index_bars(start_date: str, end_date: str, run_id: str) -> tuple[pd.DataFrame, list[ProbeResult]]:
    probes: list[ProbeResult] = []
    frames: list[pd.DataFrame] = []
    try:
        ak = _import_akshare()
    except Exception as exc:
        return pd.DataFrame(), [ProbeResult("akshare", "import", False, repr(exc))]

    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()
    for index_code, ak_symbol in INDEX_SYMBOLS.items():
        try:
            raw = ak.stock_zh_index_daily(symbol=ak_symbol)
            probes.append(ProbeResult("akshare", f"stock_zh_index_daily:{ak_symbol}", True, f"rows={len(raw)}"))
        except Exception as exc:  # pragma: no cover - depends on network/source
            probes.append(ProbeResult("akshare", f"stock_zh_index_daily:{ak_symbol}", False, repr(exc)))
            continue

        if raw.empty:
            continue
        df = raw.rename(columns={"date": "trade_date"}).copy()
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        df = df[(df["trade_date"] >= start) & (df["trade_date"] <= end)]
        df["index_code"] = index_code
        df["amount"] = pd.NA
        df["source"] = "akshare.stock_zh_index_daily"
        df["run_id"] = run_id
        df["update_time"] = datetime.now().isoformat(timespec="seconds")
        frames.append(df[[
            "index_code", "trade_date", "open", "high", "low", "close",
            "volume", "amount", "source", "run_id", "update_time",
        ]])

    if not frames:
        return pd.DataFrame(), probes
    return pd.concat(frames, ignore_index=True), probes


def build_stock_status(
    sample_stocks: pd.DataFrame,
    daily_bars: pd.DataFrame,
    trade_calendar: pd.DataFrame,
    start_date: str,
    end_date: str,
    run_id: str,
) -> pd.DataFrame:
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()
    cal = trade_calendar.copy()
    cal["trade_date"] = pd.to_datetime(cal["trade_date"]).dt.date
    cal = cal[(cal["trade_date"] >= start) & (cal["trade_date"] <= end)]

    base = (
        sample_stocks[["symbol", "stock_name", "list_date"]]
        .assign(_key=1)
        .merge(cal[["trade_date"]].assign(_key=1), on="_key")
        .drop(columns="_key")
    )
    bars = daily_bars[["symbol", "trade_date", "close", "pct_chg", "pre_close"]].copy()
    bars["trade_date"] = pd.to_datetime(bars["trade_date"]).dt.date
    status = base.merge(bars, on=["symbol", "trade_date"], how="left")

    status["is_st"] = status["stock_name"].astype(str).str.upper().str.contains("ST", na=False)
    status["is_suspended"] = status["close"].isna()
    thresholds = status.apply(lambda row: _limit_threshold(row["symbol"], row["stock_name"]), axis=1)
    status["is_limit_up"] = status["pct_chg"].fillna(0) >= ((thresholds * 100) - 0.2)
    status["is_limit_down"] = status["pct_chg"].fillna(0) <= (-(thresholds * 100) + 0.2)
    status["up_limit_price"] = (status["pre_close"] * (1 + thresholds)).round(2)
    status["down_limit_price"] = (status["pre_close"] * (1 - thresholds)).round(2)

    list_dates = pd.to_datetime(status["list_date"], errors="coerce").dt.date
    status["listed_days"] = (pd.to_datetime(status["trade_date"]) - pd.to_datetime(list_dates)).dt.days
    status.loc[status["listed_days"].isna(), "listed_days"] = 9999
    status["listed_days"] = status["listed_days"].astype(int)
    status["source"] = "derived_from_akshare_daily_bar"
    status["run_id"] = run_id
    status["update_time"] = datetime.now().isoformat(timespec="seconds")
    return status[[
        "symbol", "trade_date", "is_st", "is_suspended", "is_limit_up",
        "is_limit_down", "up_limit_price", "down_limit_price", "listed_days",
        "source", "run_id", "update_time",
    ]]


def write_probe_report(probes: list[ProbeResult], path: Path) -> None:
    rows = [
        {"source": p.source, "target": p.target, "ok": p.ok, "detail": p.detail}
        for p in probes
    ]
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
