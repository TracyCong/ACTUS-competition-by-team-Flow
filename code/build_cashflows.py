#!/usr/bin/env python3
"""Build unified cashflow table from ACTUS JSON outputs."""
import argparse
import csv
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="Root outputs dir with scenario/behavior/batch_*.json")
    ap.add_argument("--meta", required=True, help="contracts_meta.csv")
    ap.add_argument("--out", required=True, help="cashflows.csv")
    args = ap.parse_args()

    meta = {}
    with open(args.meta, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            meta[row["contract_id"]] = row

    raw_root = Path(args.raw)
    rows = []

    for json_path in raw_root.rglob("batch_*.json"):
        # parse scenario and behavior from path
        behavior = json_path.parent.name
        scenario_id = json_path.parent.parent.name

        data = json.loads(json_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for item in data:
            cid = item.get("contractID", "")
            fam = meta.get(cid, {}).get("family", "")
            for e in item.get("events", []) or []:
                rows.append({
                    "scenario_id": scenario_id,
                    "behavior_mode": behavior,
                    "contract_id": cid,
                    "product_family": fam,
                    "time": e.get("time", ""),
                    "type": e.get("type", ""),
                    "payoff": e.get("payoff", ""),
                    "currency": e.get("currency", ""),
                    "nominalValue": e.get("nominalValue", ""),
                    "nominalRate": e.get("nominalRate", ""),
                    "nominalAccrued": e.get("nominalAccrued", ""),
                })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
