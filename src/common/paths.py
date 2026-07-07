"""项目路径工具。

第 1 周数据任务先采用文件交付，是为了在数据库链路完全确定前，
让团队可以直接检查每个交接产物。
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR = PROJECT_ROOT / "reports"


def ensure_dir(path: Path) -> Path:
    """确保目录存在，并返回该目录路径。"""
    path.mkdir(parents=True, exist_ok=True)
    return path
