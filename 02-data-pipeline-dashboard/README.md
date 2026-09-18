# Piece 2 — Data Pipeline & Dashboard

**Portfolio piece 2 of 3** — Prepared by Virginia Ngami Paul, M&E Specialist

This piece takes the results framework designed in [Piece 1](../01-measurement-system/01-measurement-system.md) and builds the full data pipeline that would actually measure it: a KoboToolbox-ready survey form, a data cleaning and quality-assurance script, and a Streamlit dashboard reporting on the exact indicators defined in Piece 1's logframe.

> **Note.** All data used here is synthetic, generated to be broadly consistent with the baseline values and Y1–Y4 targets set out in Piece 1. It is not real survey data. The pipeline and code are the deliverable being demonstrated — not the numbers themselves.

## What's in this folder

```
piece2/
├── xlsform/
│   ├── build_xlsform.py                       # generates the XLSForm
│   └── kdrsip_household_survey_xlsform.xlsx    # ready to upload to KoboToolbox
├── data_pipeline/
│   ├── generate_synthetic_data.py              # builds the synthetic raw dataset
│   └── clean_data.py                           # cleaning, DQA rules, indicator summary
├── data/
│   ├── raw/kdrsip_household_survey_raw_export.csv
│   └── clean/
│       ├── household_survey_clean.csv
│       ├── indicators_by_round.csv
│       ├── indicators_by_subcounty_latest.csv
│       └── cleaning_log.csv
├── dashboard/
│   └── app.py                                  # Streamlit dashboard
└── requirements.txt
```

## The survey form

`kdrsip_household_survey_xlsform.xlsx` is a standard three-sheet XLSForm (`survey`, `choices`, `settings`) that can be uploaded directly to [KoboToolbox](https://www.kobotoolbox.org/) or any ODK-compatible platform. It operationalises every indicator in Piece 1's logframe:

| Piece 1 indicator | Form section |
|---|---|
| OP1 — advisory reach | Agro-advisory information |
| OP2 — FFS completion | Training and climate-smart practices |
| IR2 — practice adoption | Training and climate-smart practices |
| OC1 — yield & income | Crop production and sales (repeat group) |
| OC2 / IR3 — group marketing & price share | Crop production and sales |
| Resilience proxy | Coping strategies |

It includes constraint logic (e.g. area planted cannot exceed landholding), skip logic (advisory channel questions only appear if the household was reached), and a consent gate at the start, consistent with the ethics section of Piece 1's DQA plan.

To regenerate it: `python xlsform/build_xlsform.py`

## The data pipeline

**`generate_synthetic_data.py`** produces a raw dataset shaped like an actual KoboToolbox export — group-prefixed column names, five annual survey rounds (Baseline, Y1–Y4), a 1,080-household panel sample matching the sample size specified in Piece 1's PIRS, and realistic messiness: a handful of duplicate submissions, decimal entry slips, and implausible price entries — the same kinds of problems a real DQA process has to catch.

**`clean_data.py`** applies the data quality rules from Piece 1, Section 5:
- Deduplicates on household ID + survey round
- Applies the range constraints from the PIRS (landholding, price, yield, income)
- Follows the documented missing-data rule: out-of-range values are set to missing and logged, never imputed or guessed
- Derives the indicator fields (reach flag, adoption flag, group-sale flag, etc.)
- Outputs a full audit trail (`cleaning_log.csv`) showing exactly what was changed and why

Run in order:
```bash
python data_pipeline/generate_synthetic_data.py
python data_pipeline/clean_data.py
```

## The dashboard

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

The dashboard reports on the same indicators as Piece 1's logframe — reach, FFS completion, practice adoption, yield, income, group marketing, price share — each shown against its Piece 1 target by round, plus a disaggregation view by household head sex and sub-county. A data-quality panel shows the full cleaning log, so every number on the dashboard can be traced back to the rule that shaped it.

## How this connects to the other pieces

Piece 1 defines *what* to measure and why. Piece 2 shows *how* that data would actually be collected, cleaned, and reported. Piece 3 (in progress) closes the loop: the learning agenda and reflection process that turns what this dashboard shows into programme decisions.
