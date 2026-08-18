"""Shared transform helpers for encounter and dashboard mart building."""

from __future__ import annotations

import pandas as pd


def hourly_snapshots(
    visits: pd.DataFrame,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for _, row in visits.iterrows():
        admission_ts = pd.Timestamp(row["admission_ts"])
        discharge_ts = pd.Timestamp(row["discharge_ts"])
        if pd.isna(discharge_ts):
            if end is None:
                continue
            discharge_ts = end
        snapshot_start = max(admission_ts, start) if start is not None else admission_ts
        snapshot_end = min(discharge_ts, end) if end is not None else discharge_ts
        first_hour = snapshot_start.ceil("h")
        if first_hour >= snapshot_end:
            continue
        hours = pd.date_range(first_hour, snapshot_end, freq="h", inclusive="left")
        if hours.empty:
            continue
        frames.append(
            pd.DataFrame(
                {
                    "visit_id": row["visit_id"],
                    "facility_id": row["facility_id"],
                    "service_id": row["service_id"],
                    "hour_ts": hours,
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=["visit_id", "facility_id", "service_id", "hour_ts"])
    return pd.concat(frames, ignore_index=True)


def reporting_window(capacity: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(capacity["capacity_date"].min())
    end = pd.Timestamp(capacity["capacity_date"].max()) + pd.to_timedelta(1, unit="D")
    return start, end


def visits_overlapping_window(
    visits: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    admission_ts = pd.to_datetime(visits["admission_ts"], errors="coerce")
    discharge_ts = pd.to_datetime(visits["discharge_ts"], errors="coerce")
    effective_discharge = discharge_ts.where(discharge_ts.notna(), end)
    clipped = visits[
        (effective_discharge > start)
        & (admission_ts < end)
    ].copy()
    clipped["admission_ts"] = admission_ts.loc[clipped.index].clip(lower=start)
    clipped["discharge_ts"] = effective_discharge.loc[clipped.index].clip(upper=end)
    return clipped.reset_index(drop=True)


def unit_changes_overlapping_window(
    unit_changes: pd.DataFrame,
    raw_visits: pd.DataFrame,
    visits: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    unit_changes = unit_changes.copy()
    unit_changes["event_ts"] = pd.to_datetime(unit_changes["event_ts"], errors="coerce")
    raw_visit_lookup = raw_visits.set_index("visit_id")

    for _, visit in visits.iterrows():
        visit_id = visit["visit_id"]
        admission_ts = pd.Timestamp(visit["admission_ts"])
        discharge_ts = pd.Timestamp(visit["discharge_ts"])
        visit_changes = unit_changes[unit_changes["visit_id"] == visit_id].sort_values("event_ts")
        in_window = visit_changes[
            (visit_changes["event_ts"] >= admission_ts)
            & (visit_changes["event_ts"] < discharge_ts)
        ]

        raw_admission_ts = pd.Timestamp(raw_visit_lookup.loc[visit_id, "admission_ts"])
        if admission_ts > raw_admission_ts:
            previous_changes = visit_changes[visit_changes["event_ts"] < admission_ts]
            if not previous_changes.empty and (
                in_window.empty or pd.Timestamp(in_window.iloc[0]["event_ts"]) > admission_ts
            ):
                previous = previous_changes.iloc[-1].to_dict()
                previous["unit_change_id"] = f"{previous['unit_change_id']}-CLIP"
                previous["event_ts"] = admission_ts
                rows.append(previous)

        rows.extend(in_window.to_dict("records"))

    if not rows:
        return unit_changes.iloc[0:0].copy()
    return pd.DataFrame(rows, columns=unit_changes.columns)
