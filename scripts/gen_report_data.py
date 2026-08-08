#!/usr/bin/env python3
"""
Assemble the compact data blob the report/exec-summary builders consume,
from analysis/results.json + data/. Writes /tmp/report_data.json.

    python scripts/gen_report_data.py
    python scripts/build_report.py       # -> deliverables/report.html
    python scripts/build_execsum.py      # -> deliverables/Canberra_STR_Executive_Summary.html
"""
import json
from pathlib import Path

res = json.load(open('analysis/results.json'))
est = json.load(open('data/calculator_estimate.json'))
comps = est['comparable_listings']


def summ(f):
    d = json.load(open(f'data/market_summary_{f}.json'))
    return {"occ": d['occupancy'], "adr": round(d['average_daily_rate']),
            "revpar": round(d['rev_par']), "revenue": round(d['revenue']),
            "listings": round(d['active_listings_count'])}


comp_pts = []
for c in comps:
    pm = c['performance_metrics']; pd = c['property_details']
    if pm.get('ttm_occupancy') is not None and pm.get('ttm_avg_rate'):
        comp_pts.append({"bd": pd.get('bedrooms'), "occ": round(pm['ttm_occupancy'], 3),
                         "adr": round(pm['ttm_avg_rate']), "rev": round(pm['ttm_revenue'])})

out = {
    "property": res['property'],
    "scenarios": res['str_scenarios_current_levy'],
    "scenarios_2027": res['str_scenarios_2027_levy'],
    "ltr": res['long_term_rental'],
    "compare": res['comparison_base_case'],
    "breakeven": res['breakeven'],
    "calc": {"revenue": round(est['revenue']), "adr": round(est['average_daily_rate']),
             "occ": round(est['occupancy'], 3), "pct": est['percentiles']},
    "markets": {k: summ(k) for k in ['higgins', 'belconnen', 'north_canberra', 'canberra']},
    "comps": comp_pts,
    "seasonality": [round(x, 4) for x in est['monthly_revenue_distributions']],
    "advanced": res['advanced'],
    "projection": res['projection_10yr'],
}
Path('/tmp/report_data.json').write_text(json.dumps(out, separators=(',', ':')))
print("wrote /tmp/report_data.json  (scenarios, comps, advanced, projection)")
