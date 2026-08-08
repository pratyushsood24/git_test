# Canberra STR Market Research — 54 Ashburner St, Higgins ACT 2615

Data-driven analysis to decide whether to convert the property to a **short-term
rental (Airbnb)** vs keep it as a **long-term rental**. Answers: nights/year a
comparable Canberra property rents, the rental yield STR would fetch, and the
scenarios/frameworks behind an informed decision.

## Layout
```
scripts/airroi_pull.py            AirROI API client (key via env var; saves raw JSON to data/)
analysis/inputs.example.json      Template of every model input, with sources/assumptions labelled
analysis/inputs.json              The live inputs (real property numbers + AirROI-anchored scenarios)
analysis/model.py                 STR-vs-LTR calculation engine -> analysis/results.json
data/                             Raw AirROI responses (market summaries, calculator, 25 comps, seasonality)
deliverables/report.html          Interactive decision report (open in a browser / published as an Artifact)
deliverables/canberra_str_model.xlsx  Editable financial model (blue cells = your levers)
```

## Deliverables
- **`deliverables/report.html`** — the decision report: verdict, scenario returns vs long-term
  rent, cost waterfall, comparables dispersion, sensitivity heatmap, seasonality, market context,
  regulatory & risk. Theme-aware and self-contained.
- **`deliverables/canberra_str_model.xlsx`** — Summary / Inputs / Scenarios / Sensitivity /
  **Management** (self-managed vs managed) / **Leverage & Tax** (cash-on-cash + after-tax total
  return by LVR) tabs. Edit the blue cells and every result recalculates. Rebuild with
  `python scripts/build_xlsx.py`. 169 formulas, verified against `analysis/model.py`;
  force-recalculates on open.

## Headline result (AirROI data, 8 Aug 2026)
For this 4bd/2ba home, AirROI projects ~**$62k median** annual STR revenue (p25 $38k / p75 $87k),
ADR ~$346–383, occupancy ~52%. After costs and the 5% ACT levy that nets ~**$27k** — essentially
**line-ball with a $750/wk long-term rent (~$28.6k)**. STR only clearly wins with top-quartile
execution (~$45k NOI). Break-even vs long-term rent ≈ 51% occupancy. Both are low yields on a $1M
asset — Canberra is a capital-growth, low-yield market.

**Decision drivers (added frameworks):** self-managing adds ~**$11k/yr** (drops the 18% fee) and
tips the median case clearly past long-term rent. With capital growth (~3.5%, common to both) and
leverage, STR and LTR **converge on total return** (~5.2% all-cash → ~10–11% at 80% LVR); leverage
turns cash-on-cash negative (negative gearing) but amplifies growth. So the real question is
whether you self-manage and whether the operating work is worth a modest income edge — the wealth
comes mostly from the asset appreciating, which is identical either way.

## Prerequisites
- **AirROI API key** — export it, never commit it:
  ```bash
  export AIRROI_API_KEY="your-key"
  ```
- **`api.airroi.com` must be allowlisted** in this environment's egress policy.
  It is currently **blocked** (403 CONNECT). Until allowlisted, run `airroi_pull.py`
  on a machine with open network access and copy the JSON into `data/`.

## Run
```bash
# 1) Pull market + comps data (once the key + allowlist are in place)
python scripts/airroi_pull.py --lat -35.2360 --lng 149.0330 \
    --radius-km 5 --bedrooms 3 --guests 6 --market north-canberra --out data/

# 2) Set your inputs
cp analysis/inputs.example.json analysis/inputs.json   # then edit with real numbers

# 3) Compute scenarios
python analysis/model.py --inputs analysis/inputs.json
```

## What the model computes
- Occupancy → nights/year for **Conservative / Base / Aggressive** cases
- Gross & net STR revenue after the **ACT STR levy** (5%, rising to 7.5% on 1 Jul 2027),
  management, platform, utilities, insurance, consumables, maintenance, rates
- **Gross yield, net yield, cap rate, cash-on-cash** (if a mortgage is set)
- **STR vs long-term rent** opportunity cost, furnishing-capex payback, and
  **break-even occupancy** to match the long-term-rental return
- Both current-levy and 2027-levy views

## Data sources & caveats
- Primary: **AirROI** Airbnb Data API (market summary, seasonality, listing comps, calculator).
- Grounding (used to sanity-check the API, see the report): AirROI 2026 Canberra market
  (~46% occupancy, ADR ~$172; North Canberra ~48% / ~$153), Airbtics 2025 (higher),
  htag/propertyvalue Higgins house prices, ACT Revenue Office STR levy.
- Every assumption in `inputs.example.json` is labelled and overridable. Replace
  `ASSUMPTION`-tagged values with AirROI pulls and your own actuals before relying on results.
- All figures are **AUD**; the report states the source for each number.

## API notes (verified against the live API)
- Base `https://api.airroi.com`; auth via the **`x-api-key`** header (no `Authorization` header —
  API Gateway parses it as AWS SigV4 and rejects the call).
- Market endpoints are **POST** with a `{market:{country,region,locality,district}, currency, num_months}`
  body; `calculator/estimate` and `listings/comparables` are **GET** with `bedrooms/baths/guests`.
- `currency=native` returns AUD. The property resolves to the *Higgins, District of Belconnen* market.

## Status
Complete: data pulled, model built and verified, both deliverables produced and pushed.
