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


def advanced(inp: dict, scenarios: dict, ltr: dict) -> dict:
    """Management, leverage/cash-on-cash, and after-tax total-return frameworks."""
    value = inp["property"]["market_value"]
    furn = inp["setup_capex"]["furnishing_and_setup"]
    base = scenarios["base"]

    # --- 1. Self-managed vs professionally managed (base scenario) ---
    inp_self = json.loads(json.dumps(inp)); inp_self["operating_costs"]["self_managed"] = True
    base_self = str_scenario(inp_self, inp["str"]["scenarios"]["base"], inp["str"]["act_levy_rate"])
    management = {
        "managed": {"mgmt_fee": base["management_fee"], "noi": base["noi"],
                    "net_yield_pct": base["net_yield_pct"]},
        "self_managed": {"mgmt_fee": 0, "noi": base_self["noi"],
                         "net_yield_pct": base_self["net_yield_pct"],
                         "extra_income_vs_managed": round(base_self["noi"] - base["noi"], 0)},
    }

    # --- 2 & 3. Leverage + after-tax total return, STR(base, managed) vs LTR ---
    rate = inp["leverage"]["interest_rate"]
    mrate = inp["tax"]["marginal_rate"]
    growth = inp["capital_growth_rate"]
    dep_str = inp["tax"]["str_depreciation_annual"]
    dep_ltr = inp["tax"]["ltr_depreciation_annual"]
    capital_gain = value * growth

    def leg(noi, dep, invest_extra):
        rows = {}
        for label, lvr in inp["leverage"]["scenarios"].items():
            loan = value * lvr
            equity = value * (1 - lvr) + invest_extra
            interest = loan * rate
            pre_tax_cash = noi - interest
            taxable = noi - interest - dep
            tax = taxable * mrate                     # negative => negative-gearing refund
            after_tax_cash = pre_tax_cash - tax
            rows[label] = {
                "lvr": lvr, "loan": round(loan), "equity_invested": round(equity),
                "interest": round(interest), "pre_tax_cash_flow": round(pre_tax_cash),
                "taxable_income": round(taxable), "tax_or_refund": round(tax),
                "after_tax_cash_flow": round(after_tax_cash),
                "cash_on_cash_pretax_pct": round(100 * pre_tax_cash / equity, 2) if equity else None,
                "cash_on_cash_aftertax_pct": round(100 * after_tax_cash / equity, 2) if equity else None,
                "capital_gain": round(capital_gain),
                "total_return_pct": round(100 * (after_tax_cash + capital_gain) / equity, 2) if equity else None,
            }
        return rows

    return {
        "management_comparison": management,
        "assumptions": {"interest_rate": rate, "marginal_rate": mrate,
                        "capital_growth_rate": growth, "capital_gain_pa": round(capital_gain),
                        "str_depreciation": dep_str, "ltr_depreciation": dep_ltr,
                        "note": inp.get("tax_disclaimer", "")},
        "leverage_and_tax": {
            "str_base_managed": leg(base["noi"], dep_str, furn),
            "long_term_rental": leg(ltr["noi"], dep_ltr, 0),
        },
    }


def projection(inp: dict, scenarios: dict, ltr: dict) -> dict:
    """10-year, all-cash wealth build: after-tax cash flow + equity growth, STR vs LTR."""
    pj = inp["projection"]
    years = pj["years"]; start = pj["start_year"]
    ig = pj["income_growth_rate"]; ci = pj["cost_inflation_rate"]
    value0 = inp["property"]["market_value"]; growth = inp["capital_growth_rate"]
    mrate = inp["tax"]["marginal_rate"]; furn = inp["setup_capex"]["furnishing_and_setup"]
    OC = inp["operating_costs"]; L = inp["long_term_rental"]
    plat = OC["platform_fee_pct"]; mgmt = OC["management_fee_pct_of_revenue"]
    fixed0 = sum(OC[k] for k in ("utilities_internet_annual", "insurance_annual", "consumables_annual",
                                 "maintenance_annual", "council_rates_annual", "listing_supplies_annual"))
    base = inp["str"]["scenarios"]["base"]
    gross0 = base["gross_revenue"]
    ltr_gross0 = L["weekly_rent"] * (52 - L["annual_vacancy_weeks"])
    ltr_fixed0 = L["annual_maintenance"] + L["council_rates_annual"] + L["insurance_annual"]
    dep_s = inp["tax"]["str_depreciation_annual"]; dep_l = inp["tax"]["ltr_depreciation_annual"]

    def levy_for(year):
        return inp["str"]["act_levy_rate_2027"] if year >= 2027 else inp["str"]["act_levy_rate"]

    def series(kind):
        rows = []; cum = 0.0
        for t in range(1, years + 1):
            year = start + t - 1
            gi = (1 + ig) ** (t - 1); ck = (1 + ci) ** (t - 1)
            if kind == "ltr":
                gross = ltr_gross0 * gi
                noi = gross * (1 - L["mgmt_fee_pct"]) - ltr_fixed0 * ck
                dep = dep_l
            else:
                gross = gross0 * gi
                m = 0.0 if kind == "str_self" else mgmt
                noi = gross * (1 - levy_for(year) - plat - m) - fixed0 * ck
                dep = dep_s
            tax = (noi - dep) * mrate
            after_tax = noi - tax
            cum += after_tax
            value_t = value0 * (1 + growth) ** t
            capex = furn if kind != "ltr" else 0
            wealth = value_t + cum - capex
            rows.append({"year": year, "noi": round(noi), "after_tax_cash": round(after_tax),
                         "cumulative_cash": round(cum), "property_value": round(value_t),
                         "total_wealth": round(wealth)})
        return rows

    out = {k: series(k) for k in ("str_self", "str_managed", "ltr")}
    y = years - 1
    return {
        "assumptions": {"years": years, "start_year": start, "income_growth": ig,
                        "cost_inflation": ci, "capital_growth": growth, "basis": "all-cash, after-tax"},
        "series": out,
        "summary_year10": {
            "property_value": out["ltr"][y]["property_value"],
            "capital_gain_10yr": round(out["ltr"][y]["property_value"] - value0),
            "cumulative_cash": {k: out[k][y]["cumulative_cash"] for k in out},
            "total_wealth": {k: out[k][y]["total_wealth"] for k in out},
            "str_self_vs_ltr_wealth": round(out["str_self"][y]["total_wealth"] - out["ltr"][y]["total_wealth"]),
            "str_managed_vs_ltr_wealth": round(out["str_managed"][y]["total_wealth"] - out["ltr"][y]["total_wealth"]),
        },
    }


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
        "advanced": advanced(inp, scenarios, ltr),
        "projection_10yr": projection(inp, scenarios, ltr),
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

    adv = res["advanced"]; m = adv["management_comparison"]
    print(f"\n--- Self-managed vs managed (base) ---")
    print(f"Managed NOI {cur} {m['managed']['noi']:,.0f} ({m['managed']['net_yield_pct']}%)  |  "
          f"Self-managed NOI {cur} {m['self_managed']['noi']:,.0f} ({m['self_managed']['net_yield_pct']}%)  "
          f"→ +{cur} {m['self_managed']['extra_income_vs_managed']:,.0f}/yr for your time")
    print(f"\n--- Leverage & after-tax total return (base STR, managed vs LTR) ---")
    a = adv["assumptions"]
    print(f"(rate {a['interest_rate']*100:.1f}%, tax {a['marginal_rate']*100:.0f}%, "
          f"growth {a['capital_growth_rate']*100:.1f}% = {cur} {a['capital_gain_pa']:,.0f}/yr capital gain, common to both)")
    for label in adv["leverage_and_tax"]["str_base_managed"]:
        s = adv["leverage_and_tax"]["str_base_managed"][label]
        l = adv["leverage_and_tax"]["long_term_rental"][label]
        print(f"  {label:9}: STR CoC(after-tax) {s['cash_on_cash_aftertax_pct']:>5.1f}% "
              f"total {s['total_return_pct']:>5.1f}%   |   LTR CoC {l['cash_on_cash_aftertax_pct']:>5.1f}% "
              f"total {l['total_return_pct']:>5.1f}%   (equity {cur}{s['equity_invested']:,.0f})")

    pj = res["projection_10yr"]["summary_year10"]
    print(f"\n--- 10-year wealth (all-cash, after-tax) ---")
    print(f"Property value yr10 {cur} {pj['property_value']:,.0f} "
          f"(capital gain +{cur} {pj['capital_gain_10yr']:,.0f}, common to all)")
    print(f"Cumulative after-tax cash: self {cur} {pj['cumulative_cash']['str_self']:,.0f} | "
          f"managed {cur} {pj['cumulative_cash']['str_managed']:,.0f} | LTR {cur} {pj['cumulative_cash']['ltr']:,.0f}")
    print(f"Total wealth vs LTR: self-managed {cur} {pj['str_self_vs_ltr_wealth']:+,.0f} | "
          f"managed {cur} {pj['str_managed_vs_ltr_wealth']:+,.0f}")


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
