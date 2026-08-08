#!/usr/bin/env python3
"""
STR-vs-Long-Term financial model for 54 Ashburner St, Higgins ACT 2615.

Pure-Python engine (no third-party deps). Reads analysis/inputs.json, computes
Conservative/Base/Aggressive short-term-rental scenarios (anchored to AirROI's
own revenue percentiles for this property) plus the long-term-rental baseline,
and writes analysis/results.json.

    python analysis/model.py --inputs analysis/inputs.json

Each STR scenario's GROSS REVENUE is taken directly from AirROI (authoritative);
ADR and occupancy are carried for description. Costs, yields, and the LTR
comparison are computed here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NIGHTS_PER_YEAR = 365
WEEKS_PER_YEAR = 52


def str_scenario(inp: dict, sc: dict, levy_rate: float) -> dict:
    """One STR scenario. sc = {occupancy, adr, gross_revenue}. gross_revenue is authoritative."""
    oc = inp["operating_costs"]
    cap = inp["setup_capex"]
    value = inp["property"]["market_value"]

    occ = sc["occupancy"]
    adr = sc["adr"]
    gross_revenue = sc.get("gross_revenue")
    if gross_revenue is None:                      # fall back to ADR x occupancy x 365
        gross_revenue = adr * NIGHTS_PER_YEAR * occ
    nights = NIGHTS_PER_YEAR * occ

    act_levy = gross_revenue * levy_rate
    platform_fee = gross_revenue * oc.get("platform_fee_pct", 0.0)
    mgmt_fee = 0.0 if oc.get("self_managed") else gross_revenue * oc.get("management_fee_pct_of_revenue", 0.0)
    fixed_opex = sum(oc.get(k, 0) for k in (
        "utilities_internet_annual", "insurance_annual", "consumables_annual",
        "maintenance_annual", "council_rates_annual", "listing_supplies_annual"))
    total_costs = act_levy + platform_fee + mgmt_fee + fixed_opex
    noi = gross_revenue - total_costs

    capex_amort = cap.get("furnishing_and_setup", 0) / max(cap.get("amortization_years", 5), 1)
    net_after_amort = noi - capex_amort

    interest = 0.0
    if inp["financing"].get("has_mortgage"):
        interest = inp["financing"].get("loan_balance", 0) * inp["financing"].get("interest_rate", 0)
    cash_flow = net_after_amort - interest

    cash_invested = cap.get("furnishing_and_setup", 0)
    cash_invested += (max(value - inp["financing"].get("loan_balance", 0), 0)
                      if inp["financing"].get("has_mortgage") else value)

    return {
        "occupancy": round(occ, 4),
        "nights_booked": round(nights, 0),
        "adr": round(adr, 0),
        "gross_revenue": round(gross_revenue, 0),
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
    l = inp["long_term_rental"]
    value = inp["property"]["market_value"]
    weeks_let = WEEKS_PER_YEAR - l.get("annual_vacancy_weeks", 0)
    gross = l["weekly_rent"] * weeks_let
    mgmt = gross * l.get("mgmt_fee_pct", 0)
    costs = mgmt + l.get("annual_maintenance", 0) + l.get("council_rates_annual", 0) + l.get("insurance_annual", 0)
    noi = gross - costs
    return {
        "weekly_rent": l["weekly_rent"], "weeks_let": weeks_let,
        "gross_income": round(gross, 0), "total_costs": round(costs, 0), "noi": round(noi, 0),
        "gross_yield_pct": round(100 * gross / value, 2), "net_yield_pct": round(100 * noi / value, 2),
    }


def gross_revenue_to_match(inp: dict, target_noi: float, levy_rate: float) -> float:
    """Gross STR revenue at which STR NOI == target_noi (solves the variable/fixed cost split)."""
    oc = inp["operating_costs"]
    var_rate = levy_rate + oc.get("platform_fee_pct", 0.0)
    if not oc.get("self_managed"):
        var_rate += oc.get("management_fee_pct_of_revenue", 0.0)
    fixed = sum(oc.get(k, 0) for k in (
        "utilities_internet_annual", "insurance_annual", "consumables_annual",
        "maintenance_annual", "council_rates_annual", "listing_supplies_annual"))
    return (target_noi + fixed) / (1 - var_rate)


def run(inp: dict) -> dict:
    levy = inp["str"]["act_levy_rate"]
    levy_2027 = inp["str"].get("act_levy_rate_2027", levy)
    scen = inp["str"]["scenarios"]
    names = ["conservative", "base", "aggressive"]
    scenarios = {n: str_scenario(inp, scen[n], levy) for n in names}
    scenarios_2027 = {n: str_scenario(inp, scen[n], levy_2027) for n in names}
    ltr = ltr_baseline(inp)
    base = scenarios["base"]

    # Break-even: gross revenue (and implied occupancy at base ADR) needed to match LTR NOI
    be_gross = gross_revenue_to_match(inp, ltr["noi"], levy)
    base_adr = scen["base"]["adr"]
    be_occ = be_gross / (base_adr * NIGHTS_PER_YEAR) if base_adr else None
    cover_gross = gross_revenue_to_match(inp, 0.0, levy)

    return {
        "currency": inp.get("currency", "AUD"),
        "property": inp["property"],
        "data_sources": inp.get("_sources", {}),
        "str_scenarios_current_levy": scenarios,
        "str_scenarios_2027_levy": scenarios_2027,
        "long_term_rental": ltr,
        "comparison_base_case": {
            "str_net_noi": base["noi"],
            "ltr_net_noi": ltr["noi"],
            "str_advantage_pre_amort": round(base["noi"] - ltr["noi"], 0),
            "str_advantage_after_amort": round(base["net_after_amort"] - ltr["noi"], 0),
            "payback_years_on_setup":
                round(inp["setup_capex"]["furnishing_and_setup"] / (base["noi"] - ltr["noi"]), 1)
                if base["noi"] > ltr["noi"] else None,
        },
        "breakeven": {
            "gross_revenue_to_match_ltr": round(be_gross, 0),
            "occupancy_to_match_ltr_at_base_adr": round(be_occ, 4) if be_occ else None,
            "nights_to_match_ltr_at_base_adr": round(be_occ * NIGHTS_PER_YEAR, 0) if be_occ else None,
            "gross_revenue_to_cover_costs": round(cover_gross, 0),
        },
    }


def print_table(res: dict) -> None:
    cur = res["currency"]
    print(f"\n=== STR scenarios (current {int(100*0.05)}% levy) — {res['property']['address']} ===")
    print(f"{'scenario':13}{'occ':>6}{'ADR':>7}{'gross':>11}{'NOI':>11}{'net yld':>9}{'vs LTR':>12}")
    ltr_noi = res["long_term_rental"]["noi"]
    for name, sc in res["str_scenarios_current_levy"].items():
        print(f"{name:13}{sc['occupancy']*100:>5.0f}%{sc['adr']:>7,.0f}{sc['gross_revenue']:>11,.0f}"
              f"{sc['noi']:>11,.0f}{sc['net_yield_pct']:>8.2f}%{sc['noi']-ltr_noi:>+12,.0f}")
    l = res["long_term_rental"]
    print(f"\nLong-term rent: {cur} {l['weekly_rent']}/wk -> NOI {cur} {l['noi']:,.0f} (net yield {l['net_yield_pct']}%)")
    be = res["breakeven"]
    print(f"Break-even to match LTR: gross {cur} {be['gross_revenue_to_match_ltr']:,.0f} "
          f"(~{be['occupancy_to_match_ltr_at_base_adr']*100:.0f}% occ / "
          f"{be['nights_to_match_ltr_at_base_adr']:.0f} nights at base ADR)")
    c = res["comparison_base_case"]
    print(f"Base-case STR vs LTR: {cur} {c['str_advantage_pre_amort']:+,.0f} pre-amort; "
          f"{cur} {c['str_advantage_after_amort']:+,.0f} after furnishing amort; "
          f"payback {c['payback_years_on_setup']} yrs")


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
