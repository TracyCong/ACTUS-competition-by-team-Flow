#!/usr/bin/env python3
"""Create IR + Equity risk factors and scenarios in ACTUS risk server.

Creates:
- IR paths: ir_up, ir_down, ir_vup, ir_vdown
- Equity paths: eq_base, eq_down, eq_deep
- Scenario IDs: scn_{ir}_{eq}
"""
import argparse
import requests
from datetime import datetime

RISK_URL = "http://localhost:8082"


def post(path, payload):
    r = requests.post(f"{RISK_URL}{path}", json=payload)
    r.raise_for_status()
    return r.text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-date", default="2015-01-01T00:00:00")
    args = ap.parse_args()

    # Simple deterministic paths (extendable)
    ir_paths = {
        "ir_up": [0.03, 0.032, 0.034, 0.036, 0.038, 0.040],
        "ir_down": [0.03, 0.028, 0.026, 0.024, 0.022, 0.020],
        "ir_vup": [0.03, 0.035, 0.040, 0.045, 0.050, 0.055],
        "ir_vdown": [0.03, 0.025, 0.020, 0.015, 0.010, 0.005],
    }
    eq_paths = {
        "eq_base": [100, 102, 105, 108, 110, 112],
        "eq_down": [100, 95, 90, 88, 85, 82],
        "eq_deep": [100, 90, 80, 70, 65, 60],
    }

    times = [
        "2014-01-01T00:00:00",
        "2015-03-01T00:00:00",
        "2016-06-01T00:00:00",
        "2017-12-01T00:00:00",
        "2018-02-01T00:00:00",
        "2019-05-01T00:00:00",
    ]

    # IR risk factors
    for k, vals in ir_paths.items():
        payload = {
            "riskFactorID": k,
            "marketObjectCode": "ust5Y",
            "base": 1.0,
            "data": [{"time": t, "value": v} for t, v in zip(times, vals)],
        }
        post("/addReferenceIndex", payload)

    # Equity risk factors
    for k, vals in eq_paths.items():
        payload = {
            "riskFactorID": k,
            "marketObjectCode": "MSFT",
            "base": 1.0,
            "data": [{"time": t, "value": v} for t, v in zip(times, vals)],
        }
        post("/addReferenceIndex", payload)

    # Scenarios: combine IR + EQ
    for ir in ir_paths.keys():
        for eq in eq_paths.keys():
            scn_id = f"scn_{ir}_{eq}"
            payload = {
                "scenarioID": scn_id,
                "riskFactorDescriptors": [
                    {"riskFactorID": ir, "riskFactorType": "ReferenceIndex"},
                    {"riskFactorID": eq, "riskFactorType": "ReferenceIndex"},
                ],
            }
            post("/addScenario", payload)

    print("OK")


if __name__ == "__main__":
    main()
