"""生成第 1 周数据工程师交付物。

输出会放到项目约定目录：
- data/week1/... 保存交接用 CSV 数据文件
- docs/03_数据/交付记录/第1周/... 保存接口探查、问题清单和交接说明

运行示例：
    python jobs/week1_data_engineer_run.py --end-date 2026-07-07
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.paths import DATA_DIR, DOCS_DIR, ensure_dir
from src.common.run_id import make_run_id
from src.data_ingest.week1_sample_data import (
    SAMPLE_SYMBOLS,
    ProbeResult,
    build_stock_status,
    fetch_daily_bars,
    fetch_index_bars,
    fetch_stock_list,
    fetch_trade_calendar,
    write_probe_report,
)
from src.data_quality.week1_quality import build_quality_report


def _write_csv(df: pd.DataFrame, path: Path, *, preserve_existing_on_empty: bool = False) -> str:
    if preserve_existing_on_empty and df.empty and path.exists():
        return "skipped_empty_preserved"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return "written"


def _csv_file_metadata(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"rows": 0, "columns": [], "source": ""}
    try:
        existing = pd.read_csv(path, nrows=0, dtype=str)
        columns = list(existing.columns)
        rows = sum(1 for _ in path.open("r", encoding="utf-8-sig")) - 1
        source = ""
        if "source" in columns:
            source_values = pd.read_csv(path, usecols=["source"], dtype=str)["source"].dropna().unique()
            source = ",".join(sorted(str(item) for item in source_values))
        return {"rows": max(rows, 0), "columns": columns, "source": source}
    except Exception:
        return {"rows": 0, "columns": [], "source": ""}


def _write_markdown(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}", encoding="utf-8")


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def _write_manifest(
    path: Path,
    *,
    run_id: str,
    operator: str,
    started_at: str,
    ended_at: str,
    command: str,
    outputs: list[dict[str, object]],
) -> None:
    manifest = {
        "run_id": run_id,
        "task": "week1_data_engineer",
        "operator": operator,
        "command": command,
        "git_commit": _git_commit(),
        "started_at": started_at,
        "ended_at": ended_at,
        "outputs": outputs,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _output_item(
    path: Path,
    df: pd.DataFrame,
    *,
    layer: str,
    dataset: str,
    description: str,
    write_status: str,
) -> dict[str, object]:
    source = ""
    rows = int(len(df))
    columns = list(df.columns)
    if "source" in df.columns and not df.empty:
        source = ",".join(sorted(df["source"].dropna().astype(str).unique()))
    item: dict[str, object] = {
        "path": path.relative_to(PROJECT_ROOT).as_posix(),
        "layer": layer,
        "dataset": dataset,
        "description": description,
        "rows": rows,
        "columns": columns,
        "source": source,
        "schema_version": "v0.1",
        "write_status": write_status,
    }
    if write_status in {"skipped_empty_preserved", "skipped_incomplete_run_preserved"}:
        preserved = _csv_file_metadata(path)
        item.update({
            "attempted_rows": rows,
            "attempted_columns": columns,
            "preserved_rows": preserved["rows"],
            "preserved_columns": preserved["columns"],
            "preserved_source": preserved["source"],
            "rows": preserved["rows"],
            "columns": preserved["columns"],
            "source": preserved["source"],
        })
    return item


def _probe_pytdx() -> list[ProbeResult]:
    probes: list[ProbeResult] = []
    try:
        from pytdx.hq import TdxHq_API  # type: ignore

        api = TdxHq_API()
        connected = api.connect("119.147.212.81", 7709, time_out=2)
        if not connected:
            probes.append(ProbeResult("pytdx", "connect:119.147.212.81:7709", False, "连接返回 False"))
            return probes
        data = api.get_security_bars(9, 0, "000001", 0, 5)
        probes.append(ProbeResult("pytdx", "get_security_bars:000001", bool(data), f"rows={len(data) if data else 0}"))
        api.disconnect()
    except Exception as exc:  # pragma: no cover - depends on network/source
        probes.append(ProbeResult("pytdx", "import/connect/get_security_bars", False, repr(exc)))
    return probes


def main() -> int:
    started_at = datetime.now().isoformat(timespec="seconds")
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="2023-01-01")
    parser.add_argument("--end-date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--operator", default="数据工程师", help="本次运行的执行人姓名或账号，写入 manifest.json")
    args = parser.parse_args()

    run_id = args.run_id or make_run_id("week1_data_engineer", args.end_date)
    week_data = ensure_dir(DATA_DIR / "week1")
    raw_dir = ensure_dir(week_data / "raw")
    clean_dir = ensure_dir(week_data / "clean")
    quality_dir = ensure_dir(week_data / "quality")
    data_docs = ensure_dir(DOCS_DIR / "03_数据" / "交付记录" / "第1周")

    all_probes: list[ProbeResult] = []

    stock_list, probes = fetch_stock_list(run_id)
    all_probes.extend(probes)
    trade_calendar, probes = fetch_trade_calendar(run_id)
    all_probes.extend(probes)

    if "symbol" in stock_list.columns:
        sample_stocks = stock_list[stock_list["symbol"].isin(SAMPLE_SYMBOLS)].copy()
    else:
        sample_stocks = pd.DataFrame(columns=[
            "symbol", "exchange", "stock_name", "list_date", "delist_date",
            "is_active", "source", "run_id", "update_time",
        ])
    # 如果固定样例池里有股票不在当前股票列表中，就保留可用部分，
    # 并把缺口写进问题清单。第 1 周下游验收要求是至少 20 只样例股票。
    missing_sample_symbols = sorted(set(SAMPLE_SYMBOLS) - set(sample_stocks.get("symbol", [])))

    daily_bars, probes = fetch_daily_bars(
        sample_stocks["symbol"].tolist(),
        sample_stocks,
        args.start_date,
        args.end_date,
        run_id,
    )
    all_probes.extend(probes)

    index_bars, probes = fetch_index_bars(args.start_date, args.end_date, run_id)
    all_probes.extend(probes)
    all_probes.extend(_probe_pytdx())

    stock_status = pd.DataFrame()
    if not sample_stocks.empty and not daily_bars.empty and not trade_calendar.empty:
        stock_status = build_stock_status(sample_stocks, daily_bars, trade_calendar, args.start_date, args.end_date, run_id)

    quality = build_quality_report(sample_stocks, trade_calendar, daily_bars, stock_status, run_id)

    outputs: list[dict[str, object]] = []

    # 原始探查类交接文件。
    akshare_sample = stock_list.head(200)
    akshare_sample_path = raw_dir / "akshare_sample_output.csv"
    write_status = _write_csv(akshare_sample, akshare_sample_path, preserve_existing_on_empty=True)
    outputs.append(_output_item(akshare_sample_path, akshare_sample, layer="raw", dataset="akshare_sample_output", description="AKShare 股票列表接口样例输出", write_status=write_status))

    probe_report = pd.DataFrame([p.__dict__ for p in all_probes])
    probe_report_path = raw_dir / "data_source_probe.csv"
    write_probe_report(all_probes, probe_report_path)
    outputs.append(_output_item(probe_report_path, probe_report, layer="raw", dataset="data_source_probe", description="AKShare 与 pytdx 数据源探查结果", write_status="written"))

    pytdx_sample = pd.DataFrame([p.__dict__ for p in all_probes if p.source == "pytdx"])
    pytdx_sample_path = raw_dir / "pytdx_sample_output.csv"
    write_status = _write_csv(pytdx_sample, pytdx_sample_path)
    outputs.append(_output_item(pytdx_sample_path, pytdx_sample, layer="raw", dataset="pytdx_sample_output", description="pytdx 备用行情源探查结果", write_status=write_status))

    # 标准化后的 MVP 样例表。
    core_data_ready = not stock_list.empty and not sample_stocks.empty and not daily_bars.empty
    clean_outputs = [
        (clean_dir / "dim_stock.csv", stock_list, "clean", "dim_stock", "A 股股票主数据维表"),
        (clean_dir / "dim_trade_calendar.csv", trade_calendar, "clean", "dim_trade_calendar", "交易日历维表"),
        (clean_dir / "sample_stock_pool.csv", sample_stocks, "clean", "sample_stock_pool", "第 1 周样例股票池"),
        (clean_dir / "fact_daily_bar.csv", daily_bars, "clean", "fact_daily_bar", "样例股票前复权日线行情"),
        (clean_dir / "fact_index_daily_bar.csv", index_bars, "clean", "fact_index_daily_bar", "主要指数日线行情"),
        (clean_dir / "fact_stock_status.csv", stock_status, "clean", "fact_stock_status", "样例股票停牌、ST、涨跌停等交易状态"),
        (quality_dir / "quality_report_v0.1.csv", quality, "quality", "quality_report_v0.1", "第 1 周数据质量检查报告"),
    ]
    for path, df, layer, dataset, description in clean_outputs:
        if layer == "clean" and not core_data_ready and path.exists():
            write_status = "skipped_incomplete_run_preserved"
        else:
            preserve_existing = layer == "clean" and df.empty
            write_status = _write_csv(df, path, preserve_existing_on_empty=preserve_existing)
        outputs.append(_output_item(path, df, layer=layer, dataset=dataset, description=description, write_status=write_status))

    available_daily_symbols = set(daily_bars["symbol"].astype(str).str.zfill(6)) if not daily_bars.empty else set()
    failed = [p for p in all_probes if not p.ok]
    issue_lines = [
        "| 问题编号 | 发现日期 | 模块 | 优先级 | 问题描述 | 是否阻塞主链路 | 负责人 | 状态 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    if missing_sample_symbols:
        issue_lines.append(
            f"| DATA-001 | {datetime.now().date()} | 样例股票池 | P2 | 固定样例池中缺失: {', '.join(missing_sample_symbols)} | 否 | 数据工程师 | 待确认 |"
        )
    for i, item in enumerate(failed, start=2):
        failed_symbol = item.target.split(":")[-1].replace("sh", "").replace("sz", "").replace("bj", "")
        fallback_succeeded = failed_symbol in available_daily_symbols
        blocks = "是" if item.source == "akshare" and "stock_zh_a_hist" in item.target and not fallback_succeeded else "否"
        issue_status = "已由备用接口补齐" if fallback_succeeded else "待处理"
        issue_lines.append(
            f"| DATA-{i:03d} | {datetime.now().date()} | {item.source} | P1 | {item.target} 失败: {item.detail} | {blocks} | 数据工程师 | {issue_status} |"
        )
    if len(issue_lines) == 2:
        issue_lines.append(f"| DATA-000 | {datetime.now().date()} | 数据采集 | P3 | 暂无阻塞问题 | 否 | 数据工程师 | 已记录 |")

    probe_summary = pd.DataFrame([p.__dict__ for p in all_probes])
    ok_count = int(probe_summary["ok"].sum()) if not probe_summary.empty else 0
    total_count = len(probe_summary)

    _write_markdown(
        data_docs / "akshare_probe.md",
        "AKShare 接口探查报告",
        "\n".join(
            [
                f"运行批次：`{run_id}`",
                "",
                f"探查结果：{ok_count}/{total_count} 个接口调用成功。",
                "",
                "已生成股票列表、交易日历、样例日线、指数日线相关输出，详见 `data/week1/`。",
                "",
                "字段口径：股票代码使用 6 位 `symbol`，交易所使用 `exchange`，日期使用 `YYYY-MM-DD`。",
            ]
        ),
    )
    _write_markdown(
        data_docs / "pytdx_probe.md",
        "pytdx 接口探查报告",
        "\n".join(
            [
                f"运行批次：`{run_id}`",
                "",
                "pytdx 作为日线行情备用源探查。",
                "",
                *[f"- {p.target}: {'成功' if p.ok else '失败'}，{p.detail}" for p in all_probes if p.source == "pytdx"],
                "",
                "说明：第 1 周主链路优先使用 AKShare，pytdx 失败不阻断样例数据交付，但需要第 2 周继续补备用源。",
            ]
        ),
    )
    _write_markdown(
        data_docs / "data_source_probe.md",
        "数据源探查汇总",
        "\n".join(
            [
                f"运行批次：`{run_id}`",
                "",
                f"样例股票数量：{sample_stocks['symbol'].nunique() if not sample_stocks.empty else 0}",
                f"样例日线行数：{len(daily_bars)}",
                f"指数日线行数：{len(index_bars)}",
                f"股票状态行数：{len(stock_status)}",
                "",
                "输出位置：",
                "",
                "- `data/week1/raw/data_source_probe.csv`",
                "- `data/week1/clean/dim_stock.csv`",
                "- `data/week1/clean/dim_trade_calendar.csv`",
                "- `data/week1/clean/sample_stock_pool.csv`",
                "- `data/week1/clean/fact_daily_bar.csv`",
                "- `data/week1/clean/fact_index_daily_bar.csv`",
                "- `data/week1/clean/fact_stock_status.csv`",
                "- `data/week1/quality/quality_report_v0.1.csv`",
            ]
        ),
    )
    _write_markdown(data_docs / "data_issue_list.md", "数据问题清单", "\n".join(issue_lines))

    ended_at = datetime.now().isoformat(timespec="seconds")
    command = "python " + " ".join(sys.argv)
    manifest_path = week_data / "manifest.json"
    _write_manifest(
        manifest_path,
        run_id=run_id,
        operator=args.operator,
        started_at=started_at,
        ended_at=ended_at,
        command=command,
        outputs=outputs,
    )

    print(f"run_id={run_id}")
    print(f"operator={args.operator}")
    print(f"manifest={manifest_path.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"sample_stocks={sample_stocks['symbol'].nunique() if not sample_stocks.empty else 0}")
    print(f"daily_bar_rows={len(daily_bars)}")
    print(f"index_bar_rows={len(index_bars)}")
    print(f"status_rows={len(stock_status)}")
    print(f"quality_checks={len(quality)}")
    print(f"failed_probes={len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
