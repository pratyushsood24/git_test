#!/usr/bin/env python3
import json
D = json.load(open('/tmp/report_data.json'))
s = D['scenarios']; ltr = D['ltr']; be = D['breakeven']; adv = D['advanced']
mc = adv['management_comparison']; lt = adv['leverage_and_tax']; pj = D['projection']['summary_year10']
A = lambda n: '$'+format(round(n), ',')
PCT = lambda x: f'{x:.1f}%'

def scen_rows():
    out = ''
    for k, nm in [('conservative','Conservative (p25)'), ('base','Base / median'), ('aggressive','Aggressive (p75)')]:
        sc = s[k]; d = sc['noi']-ltr['noi']
        cls = 'pos' if d >= 0 else 'neg'
        out += (f"<tr><td>{nm}</td><td>{int(sc['occupancy']*100)}%</td><td>{A(sc['adr'])}</td>"
                f"<td>{A(sc['gross_revenue'])}</td><td><b>{A(sc['noi'])}</b></td>"
                f"<td class='{cls}'>{'+' if d>=0 else ''}{A(d)}</td></tr>")
    return out

HTML = f'''<title>Executive Summary — 54 Ashburner St</title>
<style>
:root{{--ink:#14191b;--sec:#535d59;--mut:#8a938d;--line:#dfe4df;--surf:#fbfcfb;--plane:#f2f4f2;
--accent:#0f6f5f;--accent-soft:#dff0eb;--up:#0f7a52;--down:#bf6a1e;--warn:#a9791a;--warn-soft:#f7edd6;}}
*{{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
@page{{size:A4;margin:11mm 11mm}}
body{{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);
font-size:10.3px;line-height:1.42;background:#fff}}
.num,td,.v{{font-variant-numeric:tabular-nums}}
h1{{font-size:19px;margin:0;letter-spacing:-.01em}}
.eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-size:8.5px;font-weight:700;color:var(--accent)}}
.sub{{color:var(--sec);font-size:10px;margin:2px 0 0}}
.hr{{height:1px;background:var(--line);margin:9px 0}}
.verdict{{background:var(--warn-soft);border:1px solid #eadfbf;border-left:4px solid var(--warn);
border-radius:9px;padding:10px 13px;margin:9px 0}}
.verdict .t{{text-transform:uppercase;letter-spacing:.06em;font-size:8.5px;font-weight:700;color:var(--warn)}}
.verdict .h{{font-size:12.5px;font-weight:700;margin:3px 0 4px}}
.verdict p{{margin:0;color:#4a463a;font-size:9.8px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin:9px 0}}
.stat{{border:1px solid var(--line);border-radius:8px;padding:7px 9px;background:var(--surf)}}
.stat .k{{font-size:7.6px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);font-weight:600}}
.stat .v{{font-size:15px;font-weight:700;margin-top:1px}}
.stat .s{{font-size:8px;color:var(--sec)}}
.up{{color:var(--up)}}.down{{color:var(--down)}}
.cols{{display:grid;grid-template-columns:1.35fr 1fr;gap:13px;align-items:start}}
h2{{font-size:11px;margin:0 0 5px;letter-spacing:-.01em}}
table{{border-collapse:collapse;width:100%;font-size:9.2px}}
th,td{{padding:4px 6px;text-align:right;border-bottom:1px solid var(--line)}}
th:first-child,td:first-child{{text-align:left}}
thead th{{background:var(--accent-soft);font-size:7.8px;text-transform:uppercase;letter-spacing:.04em;color:#26594e;font-weight:700;border:none}}
td.pos{{color:var(--up);font-weight:700}}td.neg{{color:var(--down);font-weight:700}}
tr.hi td{{background:#f0f7f4;font-weight:600}}
ul{{margin:3px 0 0;padding-left:15px}}li{{margin:3px 0}}
.rec{{background:var(--accent-soft);border-radius:8px;padding:9px 12px;margin-top:9px}}
.rec b{{color:#0c5a4d}}
.foot{{color:var(--mut);font-size:7.8px;margin-top:9px;border-top:1px solid var(--line);padding-top:6px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:13px}}
.mini td,.mini th{{padding:3px 5px;font-size:8.8px}}
</style>
<div class="eyebrow">Short-term rental feasibility · Executive summary</div>
<h1>54 Ashburner St, Higgins ACT 2615</h1>
<p class="sub">4 bed · 2 bath · sleeps 8 &nbsp;|&nbsp; Value $1.0M &nbsp;|&nbsp; Data: AirROI API, 8 Aug 2026 &nbsp;|&nbsp; All figures AUD</p>

<div class="verdict">
  <div class="t">● Verdict — a close call that hinges on how you run it</div>
  <div class="h">Short-term letting is roughly line-ball with a $750/week long-term rental — a clear win only if you self-manage and execute in the top quartile.</div>
  <p>AirROI's median projection nets <b>{A(s['base']['noi'])}</b> vs <b>{A(ltr['noi'])}</b> long-term (managed). Self-managing adds <b>+{A(mc['self_managed']['extra_income_vs_managed'])}/yr</b>, tipping it decisively ahead. Capital growth — the main wealth driver — is identical either way, so this is a cash-income and effort decision, not a wealth-strategy one.</p>
</div>

<div class="grid">
  <div class="stat"><div class="k">Base STR net income</div><div class="v">{A(s['base']['noi'])}</div><div class="s">managed · 2.7% net yield</div></div>
  <div class="stat"><div class="k">Long-term rent income</div><div class="v">{A(ltr['noi'])}</div><div class="s">$750/wk · 2.9% net yield</div></div>
  <div class="stat"><div class="k">Self-managing adds</div><div class="v up">+{A(mc['self_managed']['extra_income_vs_managed'])}</div><div class="s">per year (drops 18% fee)</div></div>
  <div class="stat"><div class="k">Break-even occupancy</div><div class="v">{PCT(be['occupancy_to_match_ltr_at_base_adr']*100)}</div><div class="s">to match long-term rent</div></div>
</div>

<div class="cols">
  <div>
    <h2>Scenario returns (AirROI, this property)</h2>
    <table><thead><tr><th>Scenario</th><th>Occ</th><th>ADR</th><th>Gross</th><th>Net income</th><th>vs LTR</th></tr></thead>
    <tbody>{scen_rows()}</tbody></table>
    <p style="font-size:8.4px;color:var(--sec);margin:4px 0 0">Anchored to AirROI revenue percentiles for this 4-bed home. Well-run local 4-beds achieve 58–71% occupancy at $340–425/night; weak ones under 30%. Execution, not location, drives the outcome.</p>

    <h2 style="margin-top:10px">10-year wealth (all-cash, after-tax)</h2>
    <table class="mini"><thead><tr><th>Strategy</th><th>Cumulative cash</th><th>Total wealth</th><th>vs LTR</th></tr></thead><tbody>
    <tr class="hi"><td>STR self-managed</td><td>{A(pj['cumulative_cash']['str_self'])}</td><td>{A(pj['total_wealth']['str_self'])}</td><td class="pos">+{A(pj['str_self_vs_ltr_wealth'])}</td></tr>
    <tr><td>STR managed</td><td>{A(pj['cumulative_cash']['str_managed'])}</td><td>{A(pj['total_wealth']['str_managed'])}</td><td class="neg">{A(pj['str_managed_vs_ltr_wealth'])}</td></tr>
    <tr><td>Long-term rent</td><td>{A(pj['cumulative_cash']['ltr'])}</td><td>{A(pj['total_wealth']['ltr'])}</td><td>—</td></tr>
    </tbody></table>
    <p style="font-size:8.4px;color:var(--sec);margin:4px 0 0">Incl. ~3%/yr income &amp; cost growth, 3.5% capital growth, levy → 7.5% in 2027. The {A(pj['capital_gain_10yr'])} capital gain is common to all three.</p>
  </div>
  <div>
    <h2>Leverage &amp; total return</h2>
    <table class="mini"><thead><tr><th>Base STR</th><th>All-cash</th><th>80% LVR</th></tr></thead><tbody>
    <tr><td>After-tax cash</td><td>{A(lt['str_base_managed']['All-cash']['after_tax_cash_flow'])}</td><td>{A(lt['str_base_managed']['80% LVR']['after_tax_cash_flow'])}</td></tr>
    <tr><td>Cash-on-cash</td><td>{lt['str_base_managed']['All-cash']['cash_on_cash_aftertax_pct']}%</td><td>{lt['str_base_managed']['80% LVR']['cash_on_cash_aftertax_pct']}%</td></tr>
    <tr class="hi"><td>Total return</td><td>{lt['str_base_managed']['All-cash']['total_return_pct']}%</td><td>{lt['str_base_managed']['80% LVR']['total_return_pct']}%</td></tr>
    </tbody></table>
    <p style="font-size:8.4px;color:var(--sec);margin:4px 0 0">Leverage turns cash flow negative (negative gearing — deductible) but lifts total return by amplifying growth. STR &amp; LTR total returns stay within ~1pt.</p>

    <h2 style="margin-top:10px">Key risks</h2>
    <ul style="font-size:8.8px;color:#3d443f">
      <li><b>ACT levy → 7.5%</b> from 1 Jul 2027 (from 5%).</li>
      <li><b>Performance dispersion</b> is huge — median-to-upside gap is management quality.</li>
      <li><b>Low absolute yield</b> (~3% net) on a $1M asset; growth-driven market.</li>
      <li><b>Operating intensity</b> — turnover, cleaning, reviews vs a hands-off tenant.</li>
    </ul>
  </div>
</div>

<div class="rec">
  <b>Recommendation.</b> If you want passive income, the long-term tenant wins on effort-adjusted return. Pursue short-term only if you'll <b>self-manage</b> (or accept ~break-even under a manager) and are comfortable with the operating work and the 2027 levy step-up — in which case it earns roughly <b>$9–11k/yr more</b> and builds <b>~{A(pj['str_self_vs_ltr_wealth'])}</b> more wealth over 10 years. Either way, the bulk of your return is the property appreciating, which is identical for both.
</div>
<div class="foot">Indicative decision aid, not financial or tax advice. Tax figures assume a ~39% marginal rate and are fact-specific — confirm with a registered tax agent. Source: AirROI Airbnb Data API (8 Aug 2026) + labelled market assumptions. Full report and editable model available separately.</div>
'''
open('deliverables/Canberra_STR_Executive_Summary.html', 'w').write(HTML)
print('exec summary html bytes:', len(HTML))
