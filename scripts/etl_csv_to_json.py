"""
scripts/etl_csv_to_json.py

One-time ETL that loads the three source CSVs and writes normalized JSON
files into ./data/.  Idempotent: rerunning overwrites the JSON files.

Source files expected (paths can be overridden via CLI):
    Business_Analyst_Test__Productivity_xlsx_-_Roster.csv
    Business_Analyst_Test__Productivity_xlsx_-_Contacts.csv
    Business_Analyst_Test__Productivity_xlsx_-_Productivity.csv

Outputs:
    data/roster.json
    data/contacts.json
    data/productivity.json
    data/etl_report.txt          (summary + any orphans / bad rows)

Usage:
    python scripts/etl_csv_to_json.py --source-dir ./raw --out-dir ./data
    python scripts/etl_csv_to_json.py                 # uses defaults
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Iterable


# ---------------------------------------------------------------- helpers


def parse_date(raw: str) -> str | None:
    """Convert 'M/D/YYYY' to ISO 'YYYY-MM-DD'. Returns None if unparseable."""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%m/%d/%Y", "%-m/%-d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    # Manual fallback in case of locale issues with %-m
    try:
        m, d, y = raw.split("/")
        return datetime(int(y), int(m), int(d)).date().isoformat()
    except (ValueError, AttributeError):
        return None


def to_int(raw: str, default: int = 0) -> int:
    """Tolerant integer cast: empty / non-numeric -> default."""
    if raw is None:
        return default
    raw = raw.strip()
    if not raw:
        return default
    try:
        # Some cells may have decimals like '12.0'
        return int(float(raw))
    except ValueError:
        return default


def clean(value: Any) -> str:
    """Strip whitespace + carriage returns from a string cell."""
    if value is None:
        return ""
    return str(value).strip().replace("\r", "").replace("\n", "")


def normalize_days_range(raw: str) -> str:
    """The CSV uses an en-dash (U+2013). Normalize to ASCII hyphen."""
    return clean(raw).replace("\u2013", "-").replace("\u2014", "-")


def short_id() -> str:
    return uuid.uuid4().hex[:10]


def stream_json_array(path: str, records: Iterable[dict]) -> int:
    """Write a JSON array to disk record by record (memory-safe for big files).
    Returns the number of records written."""
    tmp = path + ".tmp"
    count = 0
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("[\n")
        first = True
        for rec in records:
            if not first:
                f.write(",\n")
            json.dump(rec, f, ensure_ascii=False)
            first = False
            count += 1
        f.write("\n]\n")
    os.replace(tmp, path)
    return count


# ---------------------------------------------------------------- ROSTER


def transform_roster(csv_path: str):
    """Yields cleaned agent dicts. Skips blank / header-like rows."""
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            agent_id = clean(row.get("Agent"))
            if not agent_id or not agent_id.startswith("Agent"):
                continue                                            # blank row
            yield {
                "agent_id":     agent_id,
                "team_manager": clean(row.get("Team Manager")),
                "active_date":  parse_date(row.get("Active Date") or ""),
                "days_range":   normalize_days_range(row.get("Days") or ""),
                "tenurity":     clean(row.get("Tenurity")),
            }


# ---------------------------------------------------------------- CONTACTS


def transform_contacts(csv_path: str, valid_agents: set[str]):
    """Yields cleaned contact dicts. Also returns counters via attributes."""
    counters = {"total": 0, "orphans": 0, "bad_date": 0}

    def _iter():
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                counters["total"] += 1
                agent_id = clean(row.get("Agent"))
                date_iso = parse_date(row.get("Date") or "")
                if not date_iso:
                    counters["bad_date"] += 1
                    continue
                if agent_id not in valid_agents:
                    counters["orphans"] += 1
                    continue
                yield {
                    "contact_id":           short_id(),
                    "agent_id":             agent_id,
                    "date":                 date_iso,
                    "lob":                  clean(row.get("LOB")),
                    "channel":              clean(row.get("Channel")),
                    "acw":                  to_int(row.get("ACW")),
                    "dual_chat_aht":        to_int(row.get("Dual/Multiple_Chat_AHT")),
                    "inbound_tx":           to_int(row.get("Inbound_Transaction")),
                    "outbound_tx":          to_int(row.get("Outbound_Transaction")),
                    "handle_time":          to_int(row.get("Handle_Time")),
                    "hold_time":            to_int(row.get("Hold_Time")),
                    "outbound_handle_time": to_int(row.get("Outbound_Handle_Time")),
                    "missed_contacts":      to_int(row.get("Missed_Contacts")),
                }

    return _iter(), counters


# ---------------------------------------------------------------- PRODUCTIVITY


def transform_productivity(csv_path: str, valid_agents: set[str]):
    counters = {"total": 0, "orphans": 0, "bad_date": 0}

    def _iter():
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                counters["total"] += 1
                agent_id = clean(row.get("Agent"))
                date_iso = parse_date(row.get("Date") or "")
                if not date_iso:
                    counters["bad_date"] += 1
                    continue
                if agent_id not in valid_agents:
                    counters["orphans"] += 1
                    continue
                yield {
                    "record_id":             short_id(),
                    "agent_id":              agent_id,
                    "date":                  date_iso,
                    "aux_duration":          to_int(row.get("Aux_Duration")),
                    "break_1":               to_int(row.get("1st_BreakDuration")),
                    "break_2":               to_int(row.get("2nd_Break_Duration")),
                    "break_3":               to_int(row.get("3rd_Break_Duration")),
                    "email_duration":        to_int(row.get("Email_Duration")),
                    "lunch_duration":        to_int(row.get("Lunch_Duration")),
                    "meeting_duration":      to_int(row.get("Meeting_Duration_")),
                    "tech_issue_duration":   to_int(row.get("Technical_Issue_Duration")),
                    "personal_duration":     to_int(row.get("Personal_Duration")),
                    "task_duration":         to_int(row.get("Task_Duration")),
                    "training_duration":     to_int(row.get("Training_Duration")),
                    "available_duration":    to_int(row.get("Available_Duration")),
                    "busy_duration":         to_int(row.get("Busy_Duration")),
                    "login_duration":        to_int(row.get("Login_Duration")),
                }

    return _iter(), counters


# ---------------------------------------------------------------- MAIN


def main():
    parser = argparse.ArgumentParser(description="CSV -> JSON ETL")
    parser.add_argument("--source-dir", default=".",
                        help="Directory holding the 3 source CSVs")
    parser.add_argument("--out-dir", default="./data",
                        help="Where to write the JSON files")
    parser.add_argument("--roster-csv",
                        default="Business_Analyst_Test _Productivity_xlsx_-_Contacts.csv")
    parser.add_argument("--contacts-csv",
                        default="Business_Analyst_Test__Productivity_xlsx_-_Contacts.csv")
    parser.add_argument("--productivity-csv",
                        default="Business_Analyst_Test _Productivity_xlsx_-_Productivity.csv")
    args = parser.parse_args()

    src = args.source_dir
    out = args.out_dir
    os.makedirs(out, exist_ok=True)

    roster_csv = os.path.join(src, args.roster_csv)
    contacts_csv = os.path.join(src, args.contacts_csv)
    productivity_csv = os.path.join(src, args.productivity_csv)

    for p in (roster_csv, contacts_csv, productivity_csv):
        if not os.path.exists(p):
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            sys.exit(1)

    # --- 1. Roster (load entire set into memory; only 2.5K rows) ---------
    print("[1/3] Loading roster...")
    roster_records = list(transform_roster(roster_csv))
    valid_agents = {r["agent_id"] for r in roster_records}
    n_roster = stream_json_array(os.path.join(out, "roster.json"),
                                 iter(roster_records))
    print(f"      wrote {n_roster} agents, {len(valid_agents)} unique")

    # --- 2. Contacts (stream; 248K rows) ---------------------------------
    print("[2/3] Streaming contacts...")
    contacts_iter, c_counters = transform_contacts(contacts_csv, valid_agents)
    n_contacts = stream_json_array(os.path.join(out, "contacts.json"),
                                   contacts_iter)
    print(f"      wrote {n_contacts} contacts "
          f"(skipped {c_counters['orphans']} orphans, "
          f"{c_counters['bad_date']} bad dates)")

    # --- 3. Productivity (stream; 184K rows) -----------------------------
    print("[3/3] Streaming productivity...")
    prod_iter, p_counters = transform_productivity(productivity_csv,
                                                   valid_agents)
    n_prod = stream_json_array(os.path.join(out, "productivity.json"),
                               prod_iter)
    print(f"      wrote {n_prod} records "
          f"(skipped {p_counters['orphans']} orphans, "
          f"{p_counters['bad_date']} bad dates)")

    # --- ETL report ------------------------------------------------------
    report = [
        f"ETL run at {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"Roster:       {n_roster} agents",
        f"Contacts:     {n_contacts} written / {c_counters['total']} read "
        f"({c_counters['orphans']} orphan, {c_counters['bad_date']} bad-date)",
        f"Productivity: {n_prod} written / {p_counters['total']} read "
        f"({p_counters['orphans']} orphan, {p_counters['bad_date']} bad-date)",
        "",
        "Output files:",
        f"  {os.path.join(out, 'roster.json')}",
        f"  {os.path.join(out, 'contacts.json')}",
        f"  {os.path.join(out, 'productivity.json')}",
    ]
    with open(os.path.join(out, "etl_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("\n".join(["", "=== ETL DONE ===", *report[1:]]))


if __name__ == "__main__":
    main()