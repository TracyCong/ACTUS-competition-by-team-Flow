#!/usr/bin/env python3
"""Compute liquidity gap + LCR-style metrics from unified cashflows.csv."""
import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path


BUCKETS = [
    ("0-1D", 1),
    ("2-7D", 7),
    ("8-30D", 30),
    ("31-90D", 90),
    ("91-180D", 180),
    ("181-365D", 365),
    ("1-2Y", 730),
    (">2Y", 10_000),
]


def bucket_name(days: int) -> str:
    for name, maxd in BUCKETS:
        if days <= maxd:
            return name
    return BUCKETS[-1][0]


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--hqla", type=float, default=0.0)
    args = ap.parse_args()

    rows = []
    with open(args.inp, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if not row.get("time"):
                continue
            row["_t"] = parse_time(row["time"])
            try:
                row["_payoff"] = float(row.get("payoff") or 0.0)
            except ValueError:
                row["_payoff"] = 0.0
            rows.append(row)

    if not rows:
        raise SystemExit("No cashflows")

    asof = min(r["_t"] for r in rows)

    # bucketed per scenario+behavior
    buckets = defaultdict(lambda: {b[0]: {"inflow": 0.0, "outflow": 0.0, "net": 0.0} for b in BUCKETS})
    summary = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0})

    for r in rows:
        key = (r["scenario_id"], r["behavior_mode"])
        days = (r["_t"].date() - asof.date()).days
        if days < 0:
            continue
        bname = bucket_name(days)
        payoff = r["_payoff"]
        if payoff >= 0:
            buckets[key][bname]["inflow"] += payoff
            summary[key]["inflow"] += payoff
        else:
            buckets[key][bname]["outflow"] += -payoff
            summary[key]["outflow"] += -payoff
        buckets[key][bname]["net"] += payoff

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # liquidity_gap.csv
    gap_path = outdir / "liquidity_gap.csv"
    with gap_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scenario_id", "behavior_mode", "bucket", "inflow", "outflow", "net"])
        for (scn, beh), bmap in buckets.items():
            for bname, vals in bmap.items():
                w.writerow([scn, beh, bname, round(vals["inflow"], 6), round(vals["outflow"], 6), round(vals["net"], 6)])

    # LCR-style 30D
    lcr_path = outdir / "lcr_30d.csv"
    with lcr_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scenario_id", "behavior_mode", "inflow_30d", "outflow_30d", "net_outflow_30d", "LCR_proxy"])
        for (scn, beh), bmap in buckets.items():
            inflow_30d = bmap["0-1D"]["inflow"] + bmap["2-7D"]["inflow"] + bmap["8-30D"]["inflow"]
            outflow_30d = bmap["0-1D"]["outflow"] + bmap["2-7D"]["outflow"] + bmap["8-30D"]["outflow"]
            net_out = max(0.0, outflow_30d - inflow_30d)
            lcr = (args.hqla / net_out) if net_out > 0 else float("inf")
            w.writerow([scn, beh, round(inflow_30d, 6), round(outflow_30d, 6), round(net_out, 6), lcr])

    # scenario_summary.csv
    summ_path = outdir / "scenario_summary.csv"
    with summ_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scenario_id", "behavior_mode", "total_inflow", "total_outflow"])
        for (scn, beh), vals in summary.items():
            w.writerow([scn, beh, round(vals["inflow"], 6), round(vals["outflow"], 6)])


if __name__ == "__main__":
    main()
