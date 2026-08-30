"""Small CSV loading and profiling helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


@st.cache_data
def read_csv_preview(path: str, modified_ns: int) -> pd.DataFrame:
    return pd.read_csv(path).head(100)


def format_date(value: object) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    return timestamp.date().isoformat() if pd.notna(timestamp) else "n/a"


@st.cache_data
def read_csv_profile(path: str, freshness_columns: tuple[str, ...], modified_ns: int) -> dict[str, object]:
    frame = pd.read_csv(path)
    latest_values = []
    for column in freshness_columns:
        if column in frame.columns:
            values = pd.to_datetime(frame[column], errors="coerce")
            if values.notna().any():
                latest_values.append(values.max())

    latest = max(latest_values) if latest_values else pd.NaT
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "latest": format_date(latest),
    }


def list_csvs(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.csv")) if folder.exists() else []
