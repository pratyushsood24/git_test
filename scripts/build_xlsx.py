#!/usr/bin/env python3
"""
Build deliverables/canberra_str_model.xlsx from analysis/inputs.json.

Sheets: Summary · Inputs · Scenarios · Sensitivity · Management · Leverage & Tax.
All results are live formulas referencing the Inputs sheet (blue = editable levers).
Verified against analysis/model.py. Uses only SUM/arithmetic (universally supported),
and sets fullCalcOnLoad so Excel/Sheets/LibreOffice recalculate on open.

    python scripts/build_xlsx.py
"""
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

inp = json.load(open('analysis/inputs.json'))
S = inp['str']['scenarios']; OC = inp['operating_costs']; CAP = inp['setup_capex']
FIN = inp['financing']; L = inp['long_term_rental']; P = inp['property']
LEV = inp['leverage']; TAX = inp['tax']; GROW = inp['capital_growth_rate']

A = 'Arial'
BLUE = Font(name=A, color='0000FF'); BLACK = Font(name=A); BOLD = Font(name=A, bold=True)
WB_ = Font(name=A, bold=True, color='FFFFFF', size=11); TITLE = Font(name=A, bold=True, size=14)
ITAL = Font(name=A, italic=True, size=9, color='555555'); SMALL = Font(name=A, italic=True, size=8, color='777777')
YEL = PatternFill('solid', fgColor='FFF2CC'); HDR = PatternFill('solid', fgColor='1F4E78')
SUB = PatternFill('solid', fgColor='DDEBF7'); GRN = PatternFill('solid', fgColor='E2EFDA')
CUR = '$#,##0;($#,##0);-'; PCT = '0.0%'; PCT2 = '0.00%'

wb = Workbook()
cell = {}
def ref(n): return f"Inputs!{cell[n]}"

# ---------------- Inputs ----------------
ws = wb.active; ws.title = 'Inputs'
ws.column_dimensions['A'].width = 36
for c in 'BCDE': ws.column_dimensions[c].width = 15
ws['A1'] = 'Canberra STR Decision Model — Inputs'; ws['A1'].font = TITLE
ws['A2'] = '54 Ashburner St, Higgins ACT 2615 · AUD · blue = editable, yellow = key assumption'; ws['A2'].font = ITAL
r = 4
def section(t):
    global r
    ws.cell(r, 1, t).font = WB_
    for c in range(1, 6): ws.cell(r, c).fill = HDR
    r += 1
def row(label, value, name=None, fmt=None, font=BLUE, key=False, note=None):
    global r
    ws.cell(r, 1, label).font = BLACK
    cc = ws.cell(r, 2, value); cc.font = font
    if fmt: cc.number_format = fmt
    if key: cc.fill = YEL
    if note: ws.cell(r, 3, note).font = SMALL
    if name: cell[name] = f'B{r}'
    r += 1
section('Property')
row('Market value', P['market_value'], 'value', CUR, key=True, note='USER-PROVIDED')
row('Bedrooms / Bathrooms / Guests', f"{P['bedrooms']} / {P['bathrooms']} / {P['max_guests']}", font=BLACK)
section('STR scenarios — AirROI percentiles for THIS property')
ws.cell(r, 2, 'Conservative').font = BOLD; ws.cell(r, 3, 'Base').font = BOLD; ws.cell(r, 4, 'Aggressive').font = BOLD
for c in range(2, 5): ws.cell(r, c).fill = SUB; ws.cell(r, c).alignment = Alignment(horizontal='center')
r += 1
def scen(label, key, fmt, names, yellow=False):
    global r
    ws.cell(r, 1, label).font = BLACK
    for cidx, scn, nm in zip((2, 3, 4), ('conservative', 'base', 'aggressive'), names):
        cc = ws.cell(r, cidx, S[scn][key]); cc.font = BLUE; cc.number_format = fmt
        if yellow: cc.fill = YEL
        cell[nm] = f'{get_column_letter(cidx)}{r}'
    r += 1
scen('Occupancy', 'occupancy', PCT, ['occ_c', 'occ_b', 'occ_a'])
scen('ADR (avg nightly rate)', 'adr', CUR, ['adr_c', 'adr_b', 'adr_a'])
scen('Gross annual revenue (AirROI)', 'gross_revenue', CUR, ['rev_c', 'rev_b', 'rev_a'], yellow=True)
section('ACT short-term rental levy')
row('Levy rate — current', inp['str']['act_levy_rate'], 'levy', PCT, key=True, note='5% (ACT Gov)')
row('Levy rate — from 1 Jul 2027', inp['str']['act_levy_rate_2027'], 'levy27', PCT, note='7.5% legislated')
section('STR operating costs')
row('Management fee (% of revenue)', OC['management_fee_pct_of_revenue'], 'mgmt', PCT, note='0 if self-managed')
row('Platform fee (% of revenue)', OC['platform_fee_pct'], 'plat', PCT)
row('Utilities + internet (annual)', OC['utilities_internet_annual'], 'util', CUR)
row('Insurance (annual)', OC['insurance_annual'], 'ins', CUR)
row('Consumables / linen (annual)', OC['consumables_annual'], 'cons', CUR)
row('Maintenance (annual)', OC['maintenance_annual'], 'maint', CUR)
row('Council rates (annual)', OC['council_rates_annual'], 'rates', CUR)
row('Listing supplies (annual)', OC['listing_supplies_annual'], 'supp', CUR)
section('Setup & financing')
row('Furnishing & setup (one-off)', CAP['furnishing_and_setup'], 'furn', CUR, key=True)
row('Amortisation period (years)', CAP['amortization_years'], 'amort', font=BLUE)
section('Leverage, tax & growth')
row('Mortgage interest rate', LEV['interest_rate'], 'irate', PCT, key=True, note='edit to your rate')
row('Marginal tax rate (incl Medicare)', TAX['marginal_rate'], 'mtax', PCT, key=True, note='37%+2% assumed')
row('STR depreciation (annual)', TAX['str_depreciation_annual'], 'deps', CUR, note='new $30k fit-out')
row('LTR depreciation (annual)', TAX['ltr_depreciation_annual'], 'depl', CUR, note='minimal, older home')
row('Capital growth rate (p.a.)', GROW, 'grow', PCT, key=True, note='common to STR & LTR')
row('Income growth (rent/rev, p.a.)', inp['projection']['income_growth_rate'], 'ig', PCT)
row('Cost inflation (p.a.)', inp['projection']['cost_inflation_rate'], 'ci', PCT)
section('Long-term rental baseline')
row('Weekly rent', L['weekly_rent'], 'wrent', CUR, key=True, note='USER-PROVIDED')
row('Vacancy (weeks/year)', L['annual_vacancy_weeks'], 'vac', font=BLUE)
row('Management fee (%)', L['mgmt_fee_pct'], 'lmgmt', PCT)
row('Maintenance (annual)', L['annual_maintenance'], 'lmaint', CUR)
row('Council rates (annual)', L['council_rates_annual'], 'lrates', CUR)
row('Insurance (annual)', L['insurance_annual'], 'lins', CUR)

FIX = f"({ref('util')}+{ref('ins')}+{ref('cons')}+{ref('maint')}+{ref('rates')}+{ref('supp')})"
VARR = f"(1-{ref('levy')}-{ref('plat')}-{ref('mgmt')})"

# ---------------- Scenarios ----------------
sc = wb.create_sheet('Scenarios')
sc.column_dimensions['A'].width = 34
for c in 'BCDE': sc.column_dimensions[c].width = 14
sc['A1'] = 'STR Scenarios vs Long-Term Rental (AUD/yr)'; sc['A1'].font = TITLE
for i, h in enumerate(['Line', 'Conservative', 'Base', 'Aggressive']):
    cc = sc.cell(3, i + 1, h); cc.font = WB_; cc.fill = HDR
    cc.alignment = Alignment(horizontal='center' if i else 'left')
colin = {'C': ('occ_c', 'adr_c', 'rev_c'), 'D': ('occ_b', 'adr_b', 'rev_b'), 'E': ('occ_a', 'adr_a', 'rev_a')}
def line(rr, label, fn, fmt=CUR, bold=False, fill=None):
    sc.cell(rr, 1, label).font = BOLD if bold else BLACK
    if fill: sc.cell(rr, 1).fill = fill
    for col in ('C', 'D', 'E'):
        cc = sc.cell(rr, ord(col) - 64, fn(col)); cc.number_format = fmt; cc.font = BOLD if bold else BLACK
        if fill: cc.fill = fill
r = 4
line(r, 'Occupancy', lambda c: f"={ref(colin[c][0])}", PCT); r += 1
line(r, 'ADR', lambda c: f"={ref(colin[c][1])}", CUR); r += 1
line(r, 'Nights booked', lambda c: f"={ref(colin[c][0])}*365", '0'); r += 1
rev = r; line(r, 'Gross revenue', lambda c: f"={ref(colin[c][2])}", CUR, bold=True, fill=SUB); r += 1
line(r, '  less ACT levy', lambda c: f"=-{c}{rev}*{ref('levy')}", CUR); r += 1
line(r, '  less platform fee', lambda c: f"=-{c}{rev}*{ref('plat')}", CUR); r += 1
line(r, '  less management fee', lambda c: f"=-{c}{rev}*{ref('mgmt')}", CUR); r += 1
line(r, '  less fixed opex', lambda c: f"=-{FIX}", CUR); r += 1
noi = r; line(r, 'Net operating income (NOI)', lambda c: f"={c}{rev}+SUM({c}{rev+1}:{c}{rev+4})", CUR, bold=True, fill=GRN); r += 1
line(r, '  less furnishing amortisation', lambda c: f"=-{ref('furn')}/{ref('amort')}", CUR); r += 1
line(r, 'Net cash flow (all-cash)', lambda c: f"={c}{noi}+{c}{noi+1}", CUR, bold=True); r += 1
r += 1
line(r, 'Gross yield (rev / value)', lambda c: f"={c}{rev}/{ref('value')}", PCT2); r += 1
line(r, 'Net yield (NOI / value)', lambda c: f"={c}{noi}/{ref('value')}", PCT2, bold=True); r += 2
sc.cell(r, 1, 'Long-term rental baseline').font = WB_
for c in range(1, 5): sc.cell(r, c).fill = HDR
r += 1
lg = r; sc.cell(r, 1, 'LTR gross income').font = BLACK
sc.cell(r, 2, f"={ref('wrent')}*(52-{ref('vac')})").number_format = CUR; r += 1
ln = r; sc.cell(r, 1, 'LTR NOI').font = BOLD
sc.cell(r, 2, f"=B{lg}-B{lg}*{ref('lmgmt')}-{ref('lmaint')}-{ref('lrates')}-{ref('lins')}").number_format = CUR; sc.cell(r, 2).font = BOLD; r += 1
sc.cell(r, 1, 'LTR net yield').font = BLACK
sc.cell(r, 2, f"=B{ln}/{ref('value')}").number_format = PCT2; r += 2
sc.cell(r, 1, 'STR NOI − LTR NOI').font = BOLD
for col in ('C', 'D', 'E'):
    cc = sc.cell(r, ord(col) - 64, f"={col}{noi}-$B${ln}"); cc.number_format = CUR; cc.font = BOLD
adv = r; r += 1
be = r; sc.cell(r, 1, 'Break-even gross rev to match LTR').font = BLACK
sc.cell(r, 2, f"=(B{ln}+{FIX})/{VARR}").number_format = CUR; r += 1
sc.cell(r, 1, '  → implied occupancy at Base ADR').font = BLACK
sc.cell(r, 2, f"=B{be}/({ref('adr_b')}*365)").number_format = PCT

# refs to Scenarios cells used elsewhere
SC_NOI_BASE = f"Scenarios!D{noi}"; SC_REV_BASE = f"Scenarios!D{rev}"; SC_LTR_NOI = f"Scenarios!B{ln}"

# ---------------- Sensitivity ----------------
se = wb.create_sheet('Sensitivity')
se['A1'] = 'Sensitivity — STR Net Yield by Occupancy × ADR'; se['A1'].font = TITLE
se['A2'] = 'NOI ÷ property value, current levy & costs. Compare to LTR net yield (below).'; se['A2'].font = ITAL
se.column_dimensions['A'].width = 14
occs = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]; adrs = [250, 300, 350, 400, 450, 500]
se.cell(4, 1, 'ADR ↓ / Occ →').font = BOLD
for j, o in enumerate(occs):
    cc = se.cell(4, 2 + j, o); cc.number_format = PCT; cc.font = BOLD; cc.fill = SUB; cc.alignment = Alignment(horizontal='center')
    se.column_dimensions[get_column_letter(2 + j)].width = 11
for i, a in enumerate(adrs):
    rr = 5 + i
    ca = se.cell(rr, 1, a); ca.number_format = CUR; ca.font = BOLD; ca.fill = SUB
    for j, o in enumerate(occs):
        col = get_column_letter(2 + j)
        f = f"=($A{rr}*{col}$4*365*{VARR}-{FIX})/{ref('value')}"
        se.cell(rr, 2 + j, f).number_format = PCT2
lref = 5 + len(adrs) + 1
se.cell(lref, 1, 'LTR net yield:').font = BOLD
se.cell(lref, 2, f"={SC_LTR_NOI}/{ref('value')}").number_format = PCT2

# ---------------- Management (self vs managed) ----------------
mg = wb.create_sheet('Management')
mg.column_dimensions['A'].width = 34; mg.column_dimensions['B'].width = 16; mg.column_dimensions['C'].width = 16
mg['A1'] = 'Self-managed vs Professionally managed (base case)'; mg['A1'].font = TITLE
for i, h in enumerate(['Base case — per year', 'Managed', 'Self-managed']):
    cc = mg.cell(3, i + 1, h); cc.font = WB_; cc.fill = HDR; cc.alignment = Alignment(horizontal='center' if i else 'left')
mg.cell(4, 1, 'Gross revenue').font = BLACK
mg.cell(4, 2, f"={SC_REV_BASE}").number_format = CUR; mg.cell(4, 3, f"={SC_REV_BASE}").number_format = CUR
mg.cell(5, 1, 'Management fee').font = BLACK
mg.cell(5, 2, f"=-{SC_REV_BASE}*{ref('mgmt')}").number_format = CUR; mg.cell(5, 3, 0).number_format = CUR
mg.cell(6, 1, 'Other costs (levy+platform+fixed)').font = BLACK
oth = f"-{SC_REV_BASE}*({ref('levy')}+{ref('plat')})-{FIX}"
mg.cell(6, 2, f"={oth}").number_format = CUR; mg.cell(6, 3, f"={oth}").number_format = CUR
mg.cell(7, 1, 'Net operating income').font = BOLD; mg.cell(7, 1).fill = GRN
for c in (2, 3):
    cc = mg.cell(7, c, f"={get_column_letter(c)}4+{get_column_letter(c)}5+{get_column_letter(c)}6"); cc.number_format = CUR; cc.font = BOLD; cc.fill = GRN
mg.cell(8, 1, 'Net yield').font = BLACK
for c in (2, 3): mg.cell(8, c, f"={get_column_letter(c)}7/{ref('value')}").number_format = PCT2
mg.cell(9, 1, 'vs long-term rent NOI').font = BLACK
for c in (2, 3):
    cc = mg.cell(9, c, f"={get_column_letter(c)}7-{SC_LTR_NOI}"); cc.number_format = CUR
mg.cell(11, 1, 'Self-managing adds (per year)').font = BOLD
mg.cell(11, 2, f"=C7-B7").number_format = CUR; mg.cell(11, 2).font = BOLD; mg.cell(11, 2).fill = YEL
mg.cell(12, 1, 'Note: self-managing saves the fee but is your unpaid time (guest comms, cleaning coordination, pricing).').font = SMALL

# ---------------- Leverage & Tax ----------------
lv = wb.create_sheet('Leverage & Tax')
lv.column_dimensions['A'].width = 34
for c in 'BCD': lv.column_dimensions[c].width = 15
lv['A1'] = 'Leverage, Tax & Total Return'; lv['A1'].font = TITLE
lv['A2'] = 'Base STR (managed) vs long-term rent, by loan-to-value. Capital growth is common to both.'; lv['A2'].font = ITAL

def block(top, title, noi_ref, dep_ref, extra_equity):
    lv.cell(top, 1, title).font = WB_
    for c in range(1, 5): lv.cell(top, c).fill = HDR
    hdr = ['Per year (AUD)', 'All-cash', '60% LVR', '80% LVR']; lvrs = [0.0, 0.60, 0.80]
    for i, h in enumerate(hdr):
        cc = lv.cell(top + 1, i + 1, h); cc.font = BOLD; cc.fill = SUB
        cc.alignment = Alignment(horizontal='center' if i else 'left')
    # store LVR as editable blue inputs on the header+1 row? put LVR row
    labels = ['LVR', 'Loan', 'Your equity', 'Interest cost', 'Pre-tax cash flow',
              'Taxable income', 'Tax / (refund)', 'After-tax cash flow',
              'Cash-on-cash (after tax)', 'Capital gain', 'Total return on equity']
    base = top + 2
    for k, lab in enumerate(labels):
        lv.cell(base + k, 1, lab).font = BOLD if lab == 'Total return on equity' else BLACK
        if lab == 'Total return on equity': lv.cell(base + k, 1).fill = GRN
    for j, lvr in enumerate(lvrs):
        col = get_column_letter(2 + j)
        R = {lab: base + k for k, lab in enumerate(labels)}
        lv.cell(R['LVR'], 2 + j, lvr).number_format = PCT; lv.cell(R['LVR'], 2 + j).font = BLUE
        lv.cell(R['Loan'], 2 + j, f"={ref('value')}*{col}{R['LVR']}").number_format = CUR
        lv.cell(R['Your equity'], 2 + j, f"={ref('value')}*(1-{col}{R['LVR']})+{extra_equity}").number_format = CUR
        lv.cell(R['Interest cost'], 2 + j, f"=-{col}{R['Loan']}*{ref('irate')}").number_format = CUR
        lv.cell(R['Pre-tax cash flow'], 2 + j, f"={noi_ref}+{col}{R['Interest cost']}").number_format = CUR
        lv.cell(R['Taxable income'], 2 + j, f"={noi_ref}+{col}{R['Interest cost']}-{dep_ref}").number_format = CUR
        lv.cell(R['Tax / (refund)'], 2 + j, f"=-{col}{R['Taxable income']}*{ref('mtax')}").number_format = CUR
        lv.cell(R['After-tax cash flow'], 2 + j, f"={col}{R['Pre-tax cash flow']}+{col}{R['Tax / (refund)']}").number_format = CUR
        lv.cell(R['Cash-on-cash (after tax)'], 2 + j, f"={col}{R['After-tax cash flow']}/{col}{R['Your equity']}").number_format = PCT2
        lv.cell(R['Capital gain'], 2 + j, f"={ref('value')}*{ref('grow')}").number_format = CUR
        tr = lv.cell(R['Total return on equity'], 2 + j, f"=({col}{R['After-tax cash flow']}+{col}{R['Capital gain']})/{col}{R['Your equity']}")
        tr.number_format = PCT2; tr.font = BOLD; tr.fill = GRN
    return base + len(labels)

end1 = block(4, 'Base STR (managed)', SC_NOI_BASE, ref('deps'), ref('furn'))
end2 = block(end1 + 2, 'Long-term rental', SC_LTR_NOI, ref('depl'), 0)
lv.cell(end2 + 2, 1, 'Negative cash-on-cash under leverage = negative gearing (loss offsets other income at your marginal rate). Total return rises with leverage because it amplifies capital growth on a smaller equity base. Indicative only — not tax advice.').font = SMALL

# ---------------- 10-Year Projection ----------------
pj = wb.create_sheet('10-Year Projection')
pj['A1'] = '10-Year Wealth Projection (all-cash, after-tax)'; pj['A1'].font = TITLE
pj['A2'] = 'Rent/revenue grow at income growth; costs at cost inflation; levy steps to 7.5% in 2027; capital growth on value.'; pj['A2'].font = ITAL
start = inp['projection']['start_year']; yrs = inp['projection']['years']
heads = ['Year', 'STR self cash', 'STR self cum', 'STR mgd cash', 'STR mgd cum',
         'LTR cash', 'LTR cum', 'Property value', 'Wealth: self', 'Wealth: mgd', 'Wealth: LTR']
for j, h in enumerate(heads):
    cc = pj.cell(4, j + 1, h); cc.font = WB_; cc.fill = HDR
    cc.alignment = Alignment(horizontal='center' if j else 'left')
    pj.column_dimensions[get_column_letter(j + 1)].width = 14 if j else 8
value0 = ref('value')
plat_mgmt = f"{ref('plat')}+{ref('mgmt')}"
FIXe = lambda t: f"{FIX}*(1+{ref('ci')})^({t}-1)"          # inflated STR fixed opex
LTRFIX = f"({ref('lmaint')}+{ref('lrates')}+{ref('lins')})"
base_gross = SC_REV_BASE
for t in range(1, yrs + 1):
    r = 4 + t; yr = start + t - 1
    Y = get_column_letter(1)  # A
    pj.cell(r, 1, yr).font = BLACK
    gi = f"(1+{ref('ig')})^({t}-1)"; ck = f"(1+{ref('ci')})^({t}-1)"
    levy = f"IF({yr}>=2027,{ref('levy27')},{ref('levy')})"
    # STR self (mgmt=0): NOI = gross*gi*(1-levy-plat) - fixed*ck ; after-tax = NOI - (NOI-dep)*mtax
    noi_self = f"({base_gross}*{gi}*(1-{levy}-{ref('plat')})-{FIXe(t)})"
    noi_mgd = f"({base_gross}*{gi}*(1-{levy}-{plat_mgmt})-{FIXe(t)})"
    noi_ltr = f"({SC_LTR_NOI}/1)"  # placeholder; use escalated below
    ltr_gross = f"{ref('wrent')}*(52-{ref('vac')})*{gi}"
    noi_ltr = f"({ltr_gross}*(1-{ref('lmgmt')})-{LTRFIX}*{ck})"
    at = lambda noi, dep: f"({noi}-({noi}-{dep})*{ref('mtax')})"
    pj.cell(r, 2, f"={at(noi_self, ref('deps'))}").number_format = CUR
    pj.cell(r, 3, (f"=B{r}" if t == 1 else f"=C{r-1}+B{r}")).number_format = CUR
    pj.cell(r, 4, f"={at(noi_mgd, ref('deps'))}").number_format = CUR
    pj.cell(r, 5, (f"=D{r}" if t == 1 else f"=E{r-1}+D{r}")).number_format = CUR
    pj.cell(r, 6, f"={at(noi_ltr, ref('depl'))}").number_format = CUR
    pj.cell(r, 7, (f"=F{r}" if t == 1 else f"=G{r-1}+F{r}")).number_format = CUR
    pj.cell(r, 8, f"={value0}*(1+{ref('grow')})^{t}").number_format = CUR
    pj.cell(r, 9, f"=H{r}+C{r}-{ref('furn')}").number_format = CUR
    pj.cell(r, 10, f"=H{r}+E{r}-{ref('furn')}").number_format = CUR
    pj.cell(r, 11, f"=H{r}+G{r}").number_format = CUR
r10 = 4 + yrs
pj.cell(r10 + 2, 1, 'Year-10 total wealth vs LTR:').font = BOLD
pj.cell(r10 + 2, 9, f"=I{r10}-K{r10}").number_format = CUR; pj.cell(r10 + 2, 9).font = BOLD; pj.cell(r10 + 2, 9).fill = YEL
pj.cell(r10 + 2, 10, f"=J{r10}-K{r10}").number_format = CUR; pj.cell(r10 + 2, 10).font = BOLD; pj.cell(r10 + 2, 10).fill = YEL
pj.cell(r10 + 3, 1, 'Capital gain over 10 yrs (common to all):').font = BLACK
pj.cell(r10 + 3, 8, f"=H{r10}-{value0}").number_format = CUR
pj.cell(r10 + 4, 1, 'Wealth: self = value + cumulative self-managed cash − furnishing. Growth dominates and is identical for all three.').font = SMALL
PJ_SELF_VS = f"'10-Year Projection'!I{r10+2}"

# ---------------- Summary ----------------
su = wb.create_sheet('Summary', 0)
su.column_dimensions['A'].width = 46; su.column_dimensions['B'].width = 15
su['A1'] = 'Decision Summary — STR vs Long-Term Rental'; su['A1'].font = TITLE
su['A2'] = '54 Ashburner St, Higgins ACT 2615'; su['A2'].font = ITAL
data = [('Property value', f"={ref('value')}", CUR), ('', None, None),
    ('Base STR gross revenue (AirROI median)', f"={SC_REV_BASE}", CUR),
    ('Base STR NOI (managed)', f"={SC_NOI_BASE}", CUR),
    ('Base STR NOI (self-managed)', "=Management!C7", CUR),
    ('Long-term rental NOI', f"={SC_LTR_NOI}", CUR),
    ('Base STR advantage vs LTR (managed)', f"={SC_NOI_BASE}-{SC_LTR_NOI}", CUR),
    ('Self-managing adds', "=Management!B11", CUR), ('', None, None),
    ('Conservative STR NOI (p25)', f"=Scenarios!C{noi}", CUR),
    ('Aggressive STR NOI (p75)', f"=Scenarios!E{noi}", CUR), ('', None, None),
    ('STR base net yield', f"={SC_NOI_BASE}/{ref('value')}", PCT2),
    ('LTR net yield', f"={SC_LTR_NOI}/{ref('value')}", PCT2),
    ('Break-even occupancy to match LTR', f"=Scenarios!B{be}/({ref('adr_b')}*365)", PCT),
    ("Total return on equity (all-cash, STR)", "='Leverage & Tax'!B14", PCT2),
    ("10-yr wealth: self-managed STR vs LTR", PJ_SELF_VS, CUR)]
rr = 4
for lbl, fn, fmt in data:
    su.cell(rr, 1, lbl).font = BLACK
    if fn:
        cc = su.cell(rr, 2, fn); cc.font = BOLD
        if fmt: cc.number_format = fmt
    rr += 1
rr += 1
su.cell(rr, 1, 'Verdict').font = WB_; su.cell(rr, 1).fill = HDR; su.cell(rr, 2).fill = HDR; rr += 1
v = ('Managed, short-term is line-ball with a $750/wk long-term rent; SELF-MANAGED it clears it by '
     '~$9-10k/yr. Add capital growth + leverage and the two nearly converge on total return — because '
     'growth (common to both) dominates. Decision hinges on: do you self-manage, and is the operating '
     'work worth the modest income edge. Both are low-yield on a $1M asset.')
su.cell(rr, 1, v).alignment = Alignment(wrap_text=True, vertical='top')
su.merge_cells(start_row=rr, start_column=1, end_row=rr + 4, end_column=2); rr += 6
su.cell(rr, 1, 'Source: AirROI API (8 Aug 2026). Edit blue cells in Inputs; all results recalculate. Tax indicative — confirm with an accountant.').font = SMALL

wb.calculation.fullCalcOnLoad = True
wb.save('deliverables/canberra_str_model.xlsx')
print('saved:', wb.sheetnames)
print('anchors: rev', rev, 'noi', noi, 'ltr_noi', ln, 'be', be)
