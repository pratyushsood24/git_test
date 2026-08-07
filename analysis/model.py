#!/usr/bin/env python3
"""
STR-vs-Long-Term financial model for 54 Ashburner St, Higgins ACT 2615.

Pure-Python calculation engine (no third-party deps). Reads analysis/inputs.json
(copy from inputs.example.json), computes Conservative/Base/Aggressive short-term
rental scenarios plus the long-term-rental baseline, and writes analysis/results.json.

    python analysis/model.py --inputs analysis/inputs.json

The numbers here are only as good as the inputs — replace the ASSUMPTION-labelled
values with AirROI API pulls and your own actuals before relying on the output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NIGHTS_PER_YEAR = 365
WEEKS_PER_YEAR = 52


def str_scenario(inp: dict, occupancy: float, levy_rate: float) -> dict:
    """Compute one short-term-rental scenario at the given occupancy & ACT levy rate."""
    s = inp["str"]
    oc = inp["operating_costs"]
    cap = inp["setup_capex"]
    value = inp["property"]["market_value"]

    adr = s["adr"]
    nights = NIGHTS_PER_YEAR * occupancy
    gross_revenue = adr * nights                      # RevPAR * 365 == adr * occ * 365

    # Cleaning is charged to guests but also incurred; treat as pass-through-neutral by default.
    stays = nights / max(s.get("avg_length_of_stay_nights", 3), 1)

    act_levy = gross_revenue * levy_rate
    platform_fee = gross_revenue * oc.get("platform_fee_pct", 0.0)
    mgmt_fee = 0.0 if oc.get("self_managed") else gross_revenue * oc.get("management_fee_pct_of_revenue", 0.0)

    fixed_opex = (
        oc.get("utilities_internet_annual", 0)
        + oc.get("insurance_annual", 0)
        + oc.get("consumables_annual", 0)
        + oc.get("maintenance_annual", 0)
        + oc.get("council_rates_annual", 0)
        + oc.get("listing_supplies_annual", 0)
    )
    total_costs = act_levy + platform_fee + mgmt_fee + fixed_opex
    noi = gross_revenue - total_costs

    capex_amort = cap.get("furnishing_and_setup", 0) / max(cap.get("amortization_years", 5), 1)
    net_after_amort = noi - capex_amort

    interest = 0.0
    if inp["financing"].get("has_mortgage"):
        interest = inp["financing"].get("loan_balance", 0) * inp["financing"].get("interest_rate", 0)
    cash_flow = net_after_amort - interest

    cash_invested = cap.get("furnishing_and_setup", 0)
    if inp["financing"].get("has_mortgage"):
        cash_invested += max(value - inp["financing"].get("loan_balance", 0), 0)
    else:
        cash_invested += value

    return {
        "occupancy": round(occupancy, 4),
        "nights_booked": round(nights, 1),
        "adr": adr,
        "gross_revenue": round(gross_revenue, 0),
        "estimated_stays": round(stays, 1),
        "act_levy": round(act_levy, 0),
        "platform_fee": round(platform_fee, 0),
        "management_fee": round(mgmt_fee, 0),
        "fixed_opex": round(fixed_opex, 0),
        "total_costs": round(total_costs, 0),
        "noi": round(noi, 0),
        "capex_amortized": round(capex_amort, 0),
        "net_after_amort": round(net_after_amort, 0),
        "mortgage_interest": round(interest, 0),
        "cash_flow": round(cash_flow, 0),
        "gross_yield_pct": round(100 * gross_revenue / value, 2),
        "net_yield_pct": round(100 * noi / value, 2),
        "cap_rate_pct": round(100 * noi / value, 2),
        "cash_on_cash_pct": round(100 * cash_flow / cash_invested, 2) if cash_invested else None,
    }


def ltr_baseline(inp: dict) -> dict:
    """Long-term-rental baseline for the opportunity-cost comparison."""
    l = inp["long_term_rental"]
    value = inp["property"]["market_value"]
    weeks_let = WEEKS_PER_YEAR - l.get("annual_vacancy_weeks", 0)
    gross = l["weekly_rent"] * weeks_let
    mgmt = gross * l.get("mgmt_fee_pct", 0)
    costs = mgmt + l.get("annual_maintenance", 0) + l.get("council_rates_annual", 0) + l.get("insurance_annual", 0)
    noi = gross - costs
    return {
        "weekly_rent": l["weekly_rent"],
        "weeks_let": weeks_let,
        "gross_income": round(gross, 0),
        "total_costs": round(costs, 0),
        "noi": round(noi, 0),
        "gross_yield_pct": round(100 * gross / value, 2),
        "net_yield_pct": round(100 * noi / value, 2),
    }


def breakeven_occupancy(inp: dict, target_noi: float, levy_rate: float) -> float:
    """Occupancy at which STR NOI equals target_noi (e.g. the LTR NOI)."""
    s, oc = inp["str"], inp["operating_costs"]
    adr = s["adr"]
    var_rate = levy_rate + oc.get("platform_fee_pct", 0.0)
    if not oc.get("self_managed"):
        var_rate += oc.get("management_fee_pct_of_revenue", 0.0)
    fixed = sum(oc.get(k, 0) for k in (
        "utilities_internet_annual", "insurance_annual", "consumables_annual",
        "maintenance_annual", "council_rates_annual", "listing_supplies_annual"))
    # noi = adr*365*occ*(1-var_rate) - fixed = target  ->  occ = (target+fixed)/(adr*365*(1-var_rate))
    denom = adr * NIGHTS_PER_YEAR * (1 - var_rate)
    return (target_noi + fixed) / denom if denom else float("nan")


def run(inp: dict) -> dict:
    levy = inp["str"]["act_levy_rate"]
    levy_2027 = inp["str"].get("act_levy_rate_2027", levy)
    occ = inp["str"]["occupancy"]
    scenarios = {name: str_scenario(inp, occ[name], levy) for name in ("conservative", "base", "aggressive")}
    scenarios_2027 = {name: str_scenario(inp, occ[name], levy_2027) for name in ("conservative", "base", "aggressive")}
    ltr = ltr_baseline(inp)

    be_vs_ltr = breakeven_occupancy(inp, ltr["noi"], levy)
    be_vs_zero = breakeven_occupancy(inp, 0.0, levy)

    base = scenarios["base"]
    return {
        "currency": inp.get("currency", "AUD"),
        "property": inp["property"],
        "str_scenarios_current_levy": scenarios,
        "str_scenarios_2027_levy": scenarios_2027,
        "long_term_rental": ltr,
        "comparison_base_case": {
            "str_net_noi": base["noi"],
            "ltr_net_noi": ltr["noi"],
            "str_advantage": round(base["noi"] - ltr["noi"], 0),
            "str_advantage_after_amort": round(base["net_after_amort"] - ltr["noi"], 0),
            "payback_years_on_setup":
                round(inp["setup_capex"]["furnishing_and_setup"] / max(base["noi"] - ltr["noi"], 1), 1)
                if base["noi"] > ltr["noi"] else None,
        },
        "breakeven": {
            "occupancy_to_match_ltr": round(be_vs_ltr, 4),
            "nights_to_match_ltr": round(be_vs_ltr * NIGHTS_PER_YEAR, 0),
            "occupancy_to_cover_costs": round(be_vs_zero, 4),
        },
    }


def print_table(res: dict) -> None:
    cur = res["currency"]
    print(f"\n=== STR scenarios (current 5% levy) — {res['property']['address']} ===")
    hdr = f"{'scenario':13}{'occ':>7}{'nights':>8}{'gross':>11}{'NOI':>11}{'net yld':>9}{'vs LTR':>11}"
    print(hdr)
    ltr_noi = res["long_term_rental"]["noi"]
    for name, sc in res["str_scenarios_current_levy"].items():
        print(f"{name:13}{sc['occupancy']*100:>6.0f}%{sc['nights_booked']:>8.0f}"
              f"{sc['gross_revenue']:>11,.0f}{sc['noi']:>11,.0f}{sc['net_yield_pct']:>8.2f}%"
              f"{sc['noi']-ltr_noi:>+11,.0f}")
    l = res["long_term_rental"]
    print(f"\nLong-term rent: {cur} {l['weekly_rent']}/wk -> NOI {cur} {l['noi']:,.0f} "
          f"(net yield {l['net_yield_pct']}%)")
    be = res["breakeven"]
    print(f"Break-even occupancy to match LTR: {be['occupancy_to_match_ltr']*100:.0f}% "
          f"(~{be['nights_to_match_ltr']:.0f} nights/yr)")
    c = res["comparison_base_case"]
    print(f"Base-case STR advantage over LTR (pre-amort): {cur} {c['str_advantage']:+,.0f}; "
          f"after furnishing amort: {cur} {c['str_advantage_after_amort']:+,.0f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default="analysis/inputs.json")
    ap.add_argument("--out", default="analysis/results.json")
    args = ap.parse_args()
    path = Path(args.inputs)
    if not path.exists():
        raise SystemExit(f"{path} not found — copy analysis/inputs.example.json to it and edit.")
    inp = json.loads(path.read_text())
    res = run(inp)
    Path(args.out).write_text(json.dumps(res, indent=2))
    print_table(res)
    print(f"\nFull results -> {args.out}")


if __name__ == "__main__":
    main()
