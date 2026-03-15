#!/usr/bin/env python3
"""Plot basic figures from liquidity_gap.csv and lcr_30d.csv."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    gap_path = outdir / "liquidity_gap.csv"
    lcr_path = outdir / "lcr_30d.csv"
    figdir = outdir / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    # Gap curve by scenario (stack buckets in order)
    bucket_order = ["0-1D","2-7D","8-30D","31-90D","91-180D","181-365D","1-2Y",">2Y"]
    gap = defaultdict(lambda: {b: 0.0 for b in bucket_order})

    with gap_path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            key = f"{row['scenario_id']}|{row['behavior_mode']}"
            gap[key][row["bucket"]] = float(row["net"])

    plt.figure(figsize=(10,6))
    for key, bmap in gap.items():
        vals = [bmap[b] for b in bucket_order]
        plt.plot(bucket_order, vals, marker="o", alpha=0.6, label=key)
    plt.title("Gap Curve (net by bucket)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend(fontsize=6, ncol=2)
    plt.savefig(figdir / "gap_curve_by_scenario.png", dpi=200)
    plt.close()

    # LCR comparison
    lcr = defaultdict(dict)
    with lcr_path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            key = f"{row['scenario_id']}|{row['behavior_mode']}"
            lcr[key] = float(row["LCR_proxy"]) if row["LCR_proxy"] not in ("inf","Infinity") else 1e9

    labels = list(lcr.keys())
    vals = [lcr[k] for k in labels]
    plt.figure(figsize=(10,6))
    plt.bar(range(len(labels)), vals)
    plt.xticks(range(len(labels)), labels, rotation=90, fontsize=6)
    plt.title("LCR 30D Proxy by Scenario")
    plt.tight_layout()
    plt.savefig(figdir / "lcr_30d_comparison.png", dpi=200)
    plt.close()

    # Inflow/outflow bars by scenario
    inflow_outflow = defaultdict(lambda: {"inflow":0.0, "outflow":0.0})
    with gap_path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            key = f"{row['scenario_id']}|{row['behavior_mode']}"
            inflow_outflow[key]["inflow"] += float(row["inflow"])
            inflow_outflow[key]["outflow"] += float(row["outflow"])

    labels = list(inflow_outflow.keys())
    inflows = [inflow_outflow[k]["inflow"] for k in labels]
    outflows = [inflow_outflow[k]["outflow"] for k in labels]
    x = range(len(labels))
    plt.figure(figsize=(10,6))
    plt.bar(x, inflows, label="Inflow")
    plt.bar(x, outflows, bottom=inflows, label="Outflow")
    plt.xticks(x, labels, rotation=90, fontsize=6)
    plt.title("Total Inflow/Outflow by Scenario")
    plt.tight_layout()
    plt.legend()
    plt.savefig(figdir / "inflow_outflow_bars.png", dpi=200)
    plt.close()

    # Stress coverage ratio (proxy: inflow/outflow)
    plt.figure(figsize=(10,6))
    ratios = []
    for k in labels:
        infl = inflow_outflow[k]["inflow"]
        out = inflow_outflow[k]["outflow"]
        ratios.append(infl / out if out > 0 else 0)
    plt.bar(range(len(labels)), ratios)
    plt.xticks(range(len(labels)), labels, rotation=90, fontsize=6)
    plt.title("Stress Coverage Ratio (Inflow/Outflow)")
    plt.tight_layout()
    plt.savefig(figdir / "stress_coverage_ratio.png", dpi=200)
    plt.close()


if __name__ == "__main__":
    main()
