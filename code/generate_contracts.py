#!/usr/bin/env python3
"""Generate ANN contract inputs across product families.

No real data available -> uses paramized product families + stratified sampling.
Outputs:
- contracts.json (list of contracts for ACTUS)
- contracts_meta.csv (contract_id, family, params)
"""
import argparse
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True, help="Output contracts.json path")
    ap.add_argument("--meta", required=True, help="Output contracts_meta.csv path")
    args = ap.parse_args()

    rnd = random.Random(args.seed)

    # Base dates
    deal_date = datetime(2015, 1, 1)
    ied = datetime(2015, 1, 2)
    status = datetime(2015, 1, 1)

    # Product families (3–5). Keep ANN but vary economic terms.
    families = [
        {
            "family": "A_basic",
            "nominal_rate_mu": 0.020,
            "nominal_rate_sigma": 0.003,
            "rate_spread": 0.010,
            "maturity_years": 5,
            "pay_cycle": "P6ML0",
            "rate_reset_cycle": "P1YL1",
        },
        {
            "family": "B_longer",
            "nominal_rate_mu": 0.025,
            "nominal_rate_sigma": 0.004,
            "rate_spread": 0.012,
            "maturity_years": 8,
            "pay_cycle": "P6ML0",
            "rate_reset_cycle": "P1YL1",
        },
        {
            "family": "C_high_fee",
            "nominal_rate_mu": 0.018,
            "nominal_rate_sigma": 0.003,
            "rate_spread": 0.015,
            "maturity_years": 6,
            "pay_cycle": "P3ML0",
            "rate_reset_cycle": "P6ML1",
        },
        {
            "family": "D_short",
            "nominal_rate_mu": 0.022,
            "nominal_rate_sigma": 0.002,
            "rate_spread": 0.008,
            "maturity_years": 3,
            "pay_cycle": "P3ML0",
            "rate_reset_cycle": "P1YL1",
        },
    ]

    # Stratified sampling across families
    per_family = args.n // len(families)
    remainder = args.n % len(families)

    contracts = []
    meta_rows = []
    cid = 1

    for i, fam in enumerate(families):
        n_f = per_family + (1 if i < remainder else 0)
        for _ in range(n_f):
            nominal_rate = max(0.0, rnd.gauss(fam["nominal_rate_mu"], fam["nominal_rate_sigma"]))
            notional = rnd.uniform(50_000, 250_000)
            maturity = ied + timedelta(days=365 * fam["maturity_years"])

            contract_id = f"ann-{cid:04d}"
            cid += 1

            contract = {
                "calendar": "WEEKDAY",
                "businessDayConvention": "SCF",
                "contractType": "ANN",
                "statusDate": iso(status),
                "contractRole": "RPA",
                "contractID": contract_id,
                "cycleAnchorDateOfInterestPayment": iso(ied.replace(year=ied.year + 1)),
                "cycleOfInterestPayment": fam["pay_cycle"],
                "cycleAnchorDateOfPrincipalRedemption": iso(ied.replace(year=ied.year + 1)),
                "cycleOfPrincipalRedemption": fam["pay_cycle"],
                "nominalInterestRate": round(nominal_rate, 6),
                "dayCountConvention": "30E360",
                "currency": "USD",
                "contractDealDate": iso(deal_date),
                "initialExchangeDate": iso(ied),
                "maturityDate": iso(maturity),
                "notionalPrincipal": round(notional, 2),
                "premiumDiscountAtIED": 0,
                "cycleAnchorDateOfRateReset": iso(ied.replace(month=7, day=2)),
                "cycleOfRateReset": fam["rate_reset_cycle"],
                "rateSpread": fam["rate_spread"],
                "marketObjectCodeOfRateReset": "ust5Y",
            }
            contracts.append(contract)

            meta_rows.append({
                "contract_id": contract_id,
                "family": fam["family"],
                "nominal_rate": contract["nominalInterestRate"],
                "rate_spread": fam["rate_spread"],
                "notional": contract["notionalPrincipal"],
                "maturity_years": fam["maturity_years"],
                "pay_cycle": fam["pay_cycle"],
                "rate_reset_cycle": fam["rate_reset_cycle"],
            })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"contracts": contracts}, indent=2), encoding="utf-8")

    meta = Path(args.meta)
    meta.parent.mkdir(parents=True, exist_ok=True)
    with meta.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(meta_rows[0].keys()))
        w.writeheader()
        w.writerows(meta_rows)


if __name__ == "__main__":
    main()
