# Canberra STR Market Research — 54 Ashburner St, Higgins ACT 2615

Data-driven analysis to decide whether to convert the property to a **short-term
rental (Airbnb)** vs keep it as a **long-term rental**. Answers: nights/year a
comparable Canberra property rents, the rental yield STR would fetch, and the
scenarios/frameworks behind an informed decision.

## Layout
```
scripts/airroi_pull.py       AirROI API client (key via env var; saves raw JSON to data/)
analysis/inputs.example.json Template of every model input, with sources/assumptions labelled
analysis/model.py            STR-vs-LTR calculation engine -> analysis/results.json
data/                        Raw AirROI responses + normalized comps (created at run time)
```

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

## Status
Scaffold + calculation engine complete and tested. Pending: AirROI API key + domain
allowlist, your property/financial inputs, then the AirROI data pull, the .xlsx model,
and the interactive HTML report.
