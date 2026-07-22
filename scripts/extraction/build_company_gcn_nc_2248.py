#!/usr/bin/env python3
"""Dispatch the private GCN-NC-2248 builder outside the public repository.

The source report, extracted values, and source-specific builder are private
assets.  Set ``CNT_COMPANY_DATA_DIR`` to the external ``company`` directory;
the private builder is expected at ``<dir>/scripts/build_company_gcn_nc_2248.py``.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def company_data_dir() -> Path:
    configured = os.environ.get("CNT_COMPANY_DATA_DIR", "").strip()
    if not configured:
        raise RuntimeError(
            "CNT_COMPANY_DATA_DIR is required for private company-data workflows"
        )
    directory = Path(configured).expanduser().resolve()
    if ROOT.resolve() == directory or ROOT.resolve() in directory.parents:
        raise RuntimeError("company data directory must be outside the public repository")
    return directory


def main() -> None:
    builder = company_data_dir() / "scripts/build_company_gcn_nc_2248.py"
    if not builder.is_file():
        raise FileNotFoundError(
            f"private builder not found: {builder}; restore it from the private archive"
        )
    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    runpy.run_path(str(builder), run_name="__main__")


if __name__ == "__main__":
    main()
