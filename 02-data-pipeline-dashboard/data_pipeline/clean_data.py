"""
Cleans the raw KDRSIP household survey export and computes the indicator
summary table that feeds the dashboard.

Applies the data quality rules set out in Piece 1
(01-measurement-system.md, Section 5): deduplication, range constraints,
documented missing-data handling, and group-prefix normalisation typical
of a raw KoboToolbox export.

Usage:
    python clean_data.py
Reads:  data/raw/kdrsip_household_survey_raw_export.csv
Writes: data/clean/household_survey_clean.csv
        data/clean/indicators_by_round.csv
        data/clean/cleaning_log.csv
"""
import numpy as np
import pandas as pd

RAW_PATH = "/home/claude/piece2/data/raw/kdrsip_household_survey_raw_export.csv"
CLEAN_DIR = "/home/claude/piece2/data/clean"

RANGE_CONSTRAINTS = {
    "landholding_acres": (0, 20),
    "price_received_kes_per_kg": (0, 500),
    "yield_kg_per_acre": (0, 2000),
    "crop_income_kes": (0, 500_000),
}

PRACTICE_LIST = ["drought_tolerant_seed", "min_tillage", "mulching", "water_harvesting",
                  "intercropping", "organic_amendment", "staggered_planting"]

cleaning_log = []


def log(step, detail, n_affected):
    cleaning_log.append({"step": step, "detail": detail, "rows_affected": n_affected})
    print(f"[{step}] {detail}: {n_affected} row(s)")


def main():
    df = pd.read_csv(RAW_PATH)
    n_start = len(df)
    log("load", "raw rows loaded", n_start)

    # --- 1. Normalise group-prefixed Kobo column names ---
    rename_map = {c: c.split("/")[-1] for c in df.columns}
    df = df.rename(columns=rename_map)

    # --- 2. Strip whitespace from ID and text fields, standardise case ---
    df["household_id"] = df["household_id"].astype(str).str.strip()
    for col in ["sub_county", "ward", "buyer_type", "crop_name"]:
        df[col] = df[col].astype(str).str.strip().str.lower()

    # --- 3. Deduplicate exact and near-duplicate submissions ---
    # Dedup key: household_id + survey_round (a household should appear once per round)
    before = len(df)
    df = df.drop_duplicates(subset=["household_id", "survey_round"], keep="first")
    log("dedup", "duplicate household+round submissions removed", before - len(df))

    # --- 4. Apply range constraints from the DQA plan; out-of-range -> missing, logged ---
    for col, (lo, hi) in RANGE_CONSTRAINTS.items():
        mask = ~df[col].between(lo, hi)
        n_flagged = int(mask.sum())
        if n_flagged:
            df.loc[mask, f"{col}_flagged_raw"] = df.loc[mask, col]
            df.loc[mask, col] = np.nan
            log("range_constraint", f"{col} outside [{lo}, {hi}] set to missing", n_flagged)

    # --- 5. Documented missing-data handling: no imputation, flag and report ---
    # Households with a missing income or yield after constraint checks are kept
    # in the dataset but excluded from the relevant indicator's denominator,
    # per the DQA plan's missing-data rule (Section 5.3).
    missing_income = df["crop_income_kes"].isna().sum()
    missing_yield = df["yield_kg_per_acre"].isna().sum()
    log("missing_data", "crop_income_kes missing (excluded from income indicator denominator)", int(missing_income))
    log("missing_data", "yield_kg_per_acre missing (excluded from yield indicator denominator)", int(missing_yield))

    # --- 6. Derive indicator fields ---
    df["reached_flag"] = (df["reached_advisory"] == "yes").astype(int)
    df["ffs_flag"] = (df["ffs_completed"] == "yes").astype(int)

    def count_practices(s):
        if pd.isna(s) or str(s).strip() == "":
            return 0
        return len([p for p in str(s).split() if p in PRACTICE_LIST])

    df["n_practices_adopted"] = df["practices_used"].apply(count_practices)
    df["adopter_flag"] = (df["n_practices_adopted"] >= 3).astype(int)
    df["group_sale_flag"] = (df["sold_through_group"] == "yes").astype(int)

    def high_coping(s):
        if pd.isna(s):
            return np.nan
        return int(str(s).strip() not in ("none", ""))

    df["high_coping_flag"] = df["coping_strategies_used"].apply(high_coping)

    # --- 7. Write cleaned record-level dataset ---
    import os
    os.makedirs(CLEAN_DIR, exist_ok=True)
    clean_path = f"{CLEAN_DIR}/household_survey_clean.csv"
    df.to_csv(clean_path, index=False)
    log("write", "clean record-level dataset written", len(df))

    # --- 8. Build the indicator summary table (round x sub_county x sex where relevant) ---
    ROUND_ORDER = ["Baseline", "Y1", "Y2", "Y3", "Y4"]
    summary_rows = []
    for rnd in ROUND_ORDER:
        sub = df[df["survey_round"] == rnd]
        n = len(sub)
        summary_rows.append({
            "survey_round": rnd,
            "n_households": n,
            "reach_pct": sub["reached_flag"].mean() * 100,
            "reach_pct_female_head": sub.loc[sub["household_head_sex"] == "female", "reached_flag"].mean() * 100,
            "reach_pct_male_head": sub.loc[sub["household_head_sex"] == "male", "reached_flag"].mean() * 100,
            "ffs_completion_pct": sub["ffs_flag"].mean() * 100,
            "adoption_pct": sub["adopter_flag"].mean() * 100,
            "mean_yield_kg_per_acre": sub["yield_kg_per_acre"].mean(),
            "yield_cv": sub["yield_kg_per_acre"].std() / sub["yield_kg_per_acre"].mean(),
            "median_crop_income_kes": sub["crop_income_kes"].median(),
            "group_sale_pct": sub["group_sale_flag"].mean() * 100,
            "mean_price_share_pct": sub["price_share_pct"].mean(),
            "high_coping_pct": sub["high_coping_flag"].mean() * 100,
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_path = f"{CLEAN_DIR}/indicators_by_round.csv"
    summary_df.to_csv(summary_path, index=False)
    log("write", "indicator summary table written", len(summary_df))

    # --- 9. Disaggregated summary by sub-county (latest round) for the dashboard's breakdown view ---
    latest = df[df["survey_round"] == ROUND_ORDER[-1]]
    subcounty_rows = []
    for sc in latest["sub_county"].dropna().unique():
        s = latest[latest["sub_county"] == sc]
        subcounty_rows.append({
            "sub_county": sc,
            "n_households": len(s),
            "reach_pct": s["reached_flag"].mean() * 100,
            "adoption_pct": s["adopter_flag"].mean() * 100,
            "median_crop_income_kes": s["crop_income_kes"].median(),
            "mean_yield_kg_per_acre": s["yield_kg_per_acre"].mean(),
        })
    pd.DataFrame(subcounty_rows).to_csv(f"{CLEAN_DIR}/indicators_by_subcounty_latest.csv", index=False)

    # --- 10. Save the cleaning log itself (this is the audit trail the DQA plan calls for) ---
    pd.DataFrame(cleaning_log).to_csv(f"{CLEAN_DIR}/cleaning_log.csv", index=False)

    print("\nDone. Rows: start", n_start, "-> clean", len(df))


if __name__ == "__main__":
    main()
