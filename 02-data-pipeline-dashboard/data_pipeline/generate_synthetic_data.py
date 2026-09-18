"""
Generates synthetic KDRSIP household survey data across 5 annual rounds
(Baseline, Y1, Y2, Y3, Y4), calibrated to the baseline values and targets
defined in Piece 1 (01-measurement-system.md).

This is illustrative synthetic data for a fictional programme. It is built
to demonstrate a realistic data pipeline, not to represent real households.
Column names deliberately mimic a raw KoboToolbox export (group/field
naming, repeat-group flattening) so that clean_data.py has genuine
cleaning work to do.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N_HOUSEHOLDS = 1080
ROUNDS = ["Baseline", "Y1", "Y2", "Y3", "Y4"]
ROUND_YEAR = {"Baseline": 2026, "Y1": 2027, "Y2": 2028, "Y3": 2029, "Y4": 2030}

SUBCOUNTIES = ["kitui_rural", "mwingi_west", "kitui_south"]
WARDS = {
    "kitui_rural": ["township", "mbitini"],
    "mwingi_west": ["kwa_vonza", "waita"],
    "kitui_south": ["kyome_thaana", "mutonguni"],
}

# Targets from Piece 1, used to calibrate the synthetic trajectory
TARGETS = {
    "reach_pct":        {"Baseline": 0.00, "Y1": 0.25, "Y2": 0.58, "Y3": 0.83, "Y4": 1.00},
    "ffs_pct":          {"Baseline": 0.00, "Y1": 0.18, "Y2": 0.40, "Y3": 0.58, "Y4": 0.70},
    "adoption_pct":     {"Baseline": 0.09, "Y1": 0.20, "Y2": 0.35, "Y3": 0.47, "Y4": 0.55},
    "group_sale_pct":   {"Baseline": 0.06, "Y1": 0.15, "Y2": 0.27, "Y3": 0.36, "Y4": 0.45},
    "yield_mean":       {"Baseline": 310,  "Y1": 365,  "Y2": 425,  "Y3": 475,  "Y4": 520},
    "income_median":    {"Baseline": 18400,"Y1": 21500,"Y2": 25500,"Y3": 29000,"Y4": 32000},
    "csi_high_pct":     {"Baseline": 0.62, "Y1": 0.55, "Y2": 0.48, "Y3": 0.42, "Y4": 0.38},
}

PRACTICES = ["drought_tolerant_seed", "min_tillage", "mulching", "water_harvesting",
             "intercropping", "organic_amendment", "staggered_planting"]
CROPS = ["green_grams", "sorghum", "pigeon_peas", "cowpeas", "maize", "cassava"]
BUYERS = ["local_trader", "producer_group", "market_vendor", "processor"]

# Fixed household-level attributes (panel)
household_ids = [f"KDRSIP-{i:05d}" for i in range(1, N_HOUSEHOLDS + 1)]
subcounty_assign = RNG.choice(SUBCOUNTIES, size=N_HOUSEHOLDS, p=[0.4, 0.32, 0.28])
ward_assign = [RNG.choice(WARDS[sc]) for sc in subcounty_assign]
head_sex_assign = RNG.choice(["male", "female"], size=N_HOUSEHOLDS, p=[0.63, 0.37])
landholding_assign = np.clip(RNG.gamma(shape=2.2, scale=1.1, size=N_HOUSEHOLDS), 0.25, 5.0)

# A little household-level "quality" latent trait so income/yield/adoption correlate
# sensibly within a household across rounds and across variables (richer households
# adopt more, sell more through groups, etc.)
household_quality = RNG.normal(0, 1, size=N_HOUSEHOLDS)

rows = []
for r_idx, rnd in enumerate(ROUNDS):
    year = ROUND_YEAR[rnd]
    # rainfall shock per sub-county-round: -1 poor, 0 normal, 1 good
    rainfall_by_subcounty = {sc: RNG.choice([-1, 0, 1], p=[0.3, 0.45, 0.25]) for sc in SUBCOUNTIES}

    for i in range(N_HOUSEHOLDS):
        hh_id = household_ids[i]
        sc = subcounty_assign[i]
        ward = ward_assign[i]
        head_sex = head_sex_assign[i]
        landholding = landholding_assign[i]
        q = household_quality[i]
        rainfall = rainfall_by_subcounty[sc]

        # --- reach, training, adoption ---
        p_reach = np.clip(TARGETS["reach_pct"][rnd] + 0.08 * q, 0, 1)
        reached = RNG.random() < p_reach

        p_ffs = np.clip(TARGETS["ffs_pct"][rnd] * (1.1 if reached else 0.3) + 0.05 * q, 0, 1)
        ffs_done = RNG.random() < p_ffs

        p_adopt_hh = np.clip(TARGETS["adoption_pct"][rnd] + 0.10 * q + (0.05 if ffs_done else 0), 0, 1)
        is_adopter = RNG.random() < p_adopt_hh
        n_practices = RNG.integers(3, 8) if is_adopter else RNG.integers(0, 3)
        practices_used = list(RNG.choice(PRACTICES, size=n_practices, replace=False)) if n_practices > 0 else []

        # --- yield ---
        rainfall_effect = {-1: -0.15, 0: 0.0, 1: 0.10}[rainfall]
        practice_bonus = 0.10 if is_adopter else 0.0
        yield_mean_r = TARGETS["yield_mean"][rnd] * (1 + rainfall_effect + practice_bonus)
        yield_kg_per_acre = max(50, RNG.normal(yield_mean_r + 15 * q, 70))

        # --- group marketing & price share ---
        p_group = np.clip(TARGETS["group_sale_pct"][rnd] + 0.08 * q, 0, 1)
        sold_through_group = RNG.random() < p_group
        price_share = np.clip(
            (0.58 + (TARGETS["group_sale_pct"][rnd]) * 0.3 + (0.08 if sold_through_group else 0) + 0.03 * q),
            0.35, 0.95
        )

        # --- crop sales repeat group, flattened to 1-2 rows worth of summary fields ---
        n_crops_sold = RNG.integers(1, 3)
        crops_sold = list(RNG.choice(CROPS, size=n_crops_sold, replace=False))
        main_crop = crops_sold[0]
        low_bound = min(0.2, landholding * 0.5)
        area_planted = round(min(landholding, RNG.uniform(low_bound, landholding)), 2)
        qty_harvested = round(max(10, yield_kg_per_acre * area_planted * RNG.uniform(0.85, 1.15)), 1)
        qty_sold = round(qty_harvested * RNG.uniform(0.4, 0.9), 1)
        buyer = "producer_group" if sold_through_group else RNG.choice(["local_trader", "market_vendor", "processor"])

        # Realistic farm-gate price per kg (KES), independent of the income target,
        # boosted modestly by group marketing and household "quality"
        price_per_kg = np.clip(
            RNG.uniform(60, 160) * (1.12 if sold_through_group else 1.0) * (1 + 0.05 * q),
            35, 300
        )

        # Base revenue from the main crop, plus a top-up for additional crops sold
        other_crop_multiplier = 1 + 0.28 * (n_crops_sold - 1)
        base_income = price_per_kg * qty_sold * other_crop_multiplier
        base_income *= (1 + rainfall_effect * 0.6 + practice_bonus * 0.5) * (1 + 0.05 * q)
        income_kes = max(0, base_income)

        # --- coping strategies (depends on income computed above) ---
        target_median = TARGETS["income_median"][rnd]
        p_high_csi = np.clip(
            TARGETS["csi_high_pct"][rnd] - 0.10 * q - (0.05 if income_kes > target_median else 0), 0, 1
        )
        high_coping = RNG.random() < p_high_csi
        if high_coping:
            n_cop = RNG.integers(1, 4)
            coping_used = list(RNG.choice(
                ["sold_productive_asset", "borrowed_food", "reduced_meals", "child_labour"],
                size=n_cop, replace=False))
        else:
            coping_used = ["none"]

        # --- inject realistic messiness for the cleaning script to catch ---
        messy_landholding = landholding
        messy_price = price_per_kg
        messy_id = hh_id
        if RNG.random() < 0.015:
            messy_landholding = landholding * 100  # decimal entry slip
        if RNG.random() < 0.02:
            messy_price = price_per_kg * 5  # implausible price entry (enumerator unit error)
        if RNG.random() < 0.008:
            messy_id = hh_id + " "  # trailing whitespace -> dedup/merge issue

        rows.append({
            "_uuid": f"uuid-{rnd}-{i}",
            "start": f"{year}-06-01T08:00:00",
            "end": f"{year}-06-01T08:35:00",
            "today": f"{year}-06-01",
            "survey_round": rnd,
            "group_identification/household_id": messy_id,
            "group_identification/enumerator_name": RNG.choice(
                ["J. Mwendwa", "P. Kioko", "A. Ndaka", "M. Wanjiru", "S. Kamau"]),
            "group_identification/survey_date": f"{year}-06-{RNG.integers(1,28):02d}",
            "group_identification/sub_county": sc,
            "group_identification/ward": ward,
            "group_identification/household_head_sex": head_sex,
            "group_identification/landholding_acres": round(messy_landholding, 2),
            "group_advisory/reached_advisory": "yes" if reached else "no",
            "group_advisory/advisory_channels": " ".join(
                RNG.choice(["sms", "ivr", "whatsapp", "in_person", "radio"],
                           size=RNG.integers(1, 3), replace=False)) if reached else "",
            "group_training/ffs_completed": "yes" if ffs_done else "no",
            "group_training/practices_used": " ".join(practices_used),
            "crop_sales/crop_name": main_crop,
            "crop_sales/area_planted_acres": area_planted,
            "crop_sales/quantity_harvested_kg": qty_harvested,
            "crop_sales/quantity_sold_kg": qty_sold,
            "crop_sales/price_received_kes_per_kg": round(messy_price, 2),
            "crop_sales/buyer_type": buyer,
            "crop_sales/sold_through_group": "yes" if sold_through_group else "no",
            "group_resilience/coping_strategies_used": " ".join(coping_used),
            "yield_kg_per_acre": round(yield_kg_per_acre, 1),
            "crop_income_kes": round(income_kes, 0),
            "price_share_pct": round(price_share * 100, 1),
        })

    # rescale this round's income so the median lands near Piece 1's target,
    # while keeping price_per_kg realistic and untouched
    round_start = len(rows) - N_HOUSEHOLDS
    round_incomes = np.array([rows[j]["crop_income_kes"] for j in range(round_start, len(rows))])
    empirical_median = np.median(round_incomes)
    scale = TARGETS["income_median"][rnd] / max(empirical_median, 1)
    for j in range(round_start, len(rows)):
        rows[j]["crop_income_kes"] = round(rows[j]["crop_income_kes"] * scale, 0)

    # inject a handful of exact duplicate submissions per round (double-synced records)
    dup_offsets = RNG.choice(N_HOUSEHOLDS, size=3, replace=False)
    for off in dup_offsets:
        rows.append(rows[round_start + off].copy())

df = pd.DataFrame(rows)
out_path = "/home/claude/piece2/data/raw/kdrsip_household_survey_raw_export.csv"
df.to_csv(out_path, index=False)
print(f"Written {len(df)} rows to {out_path}")
print(df["survey_round"].value_counts())
