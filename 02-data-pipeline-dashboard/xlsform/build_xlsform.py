"""
Builds the KDRSIP Household Survey as a KoboToolbox-ready XLSForm.

Run this script to regenerate kdrsip_household_survey_xlsform.xlsx.
The form directly operationalises the indicators defined in Piece 1
(01-measurement-system.md): OP1 (reach), OP2 (FFS completion),
IR2 (practice adoption), OC1 (yield/income), OC2/IR3 (group marketing),
and the resilience proxy (coping strategies).
"""
import pandas as pd

survey = [
    # type, name, label, hint, required, relevant, constraint, constraint_message, repeat_count, appearance
    ("start", "start", "", "", "", "", "", "", "", ""),
    ("end", "end", "", "", "", "", "", "", "", ""),
    ("today", "today", "", "", "", "", "", "", "", ""),
    ("deviceid", "deviceid", "", "", "", "", "", "", "", ""),

    ("note", "note_intro", "KDRSIP Household Survey — Annual Round", "", "", "", "", "", "", ""),

    ("select_one yes_no", "consent", "Do you consent to take part in this survey? Your answers are confidential and will only be used for programme monitoring.", "Read the consent statement aloud in full before proceeding.", "yes", "", ".='yes'", "This survey cannot continue without consent.", "", ""),

    # --- Identification ---
    ("text", "household_id", "Household ID", "Scan or enter the pre-printed household ID.", "yes", "${consent}='yes'", "", "", "", ""),
    ("text", "enumerator_name", "Enumerator name", "", "yes", "${consent}='yes'", "", "", "", ""),
    ("date", "survey_date", "Survey date", "", "yes", "${consent}='yes'", "", "", "", ""),
    ("select_one sub_county", "sub_county", "Sub-county", "", "yes", "${consent}='yes'", "", "", "", ""),
    ("select_one ward", "ward", "Ward", "", "yes", "${consent}='yes'", "", "", "", ""),
    ("geopoint", "gps_point", "GPS location of household", "Capture at the homestead, not the field.", "yes", "${consent}='yes'", "", "", "", ""),
    ("select_one sex", "household_head_sex", "Sex of household head", "", "yes", "${consent}='yes'", "", "", "", ""),
    ("select_one sex", "respondent_sex", "Sex of respondent (if different from household head)", "", "yes", "${consent}='yes'", "", "", "", ""),
    ("decimal", "landholding_acres", "Total landholding (acres)", "", "yes", "${consent}='yes'", ". > 0 and . <= 20", "Landholding must be between 0 and 20 acres. Re-confirm with the respondent.", "", ""),

    # --- OP1: Advisory reach ---
    ("note", "note_advisory", "SECTION: Agro-advisory information (OP1)", "", "", "${consent}='yes'", "", "", "", ""),
    ("select_one yes_no", "reached_advisory", "In the last 12 months, has anyone in this household received crop or market advisory information from the programme?", "", "yes", "${consent}='yes'", "", "", "", ""),
    ("select_multiple advisory_channel", "advisory_channels", "Through which channel(s)?", "", "yes", "${reached_advisory}='yes'", "", "", "", ""),
    ("integer", "advisory_messages_count", "Approximately how many advisory messages or sessions were received this year?", "", "no", "${reached_advisory}='yes'", ". >= 0 and . < 200", "", "", ""),

    # --- OP2 / IR2: Training and practice adoption ---
    ("note", "note_training", "SECTION: Training and climate-smart practices (OP2, IR2)", "", "", "${consent}='yes'", "", "", "", ""),
    ("select_one yes_no", "ffs_completed", "Did anyone in this household complete a full Farmer Field School (FFS) cycle in the last 12 months?", "", "yes", "${consent}='yes'", "", "", "", ""),
    ("select_multiple csa_practice", "practices_used", "Which of the following practices were used on any plot in the last completed season? (select all that apply)", "Read out each practice.", "yes", "${consent}='yes'", "", "", "", ""),
    ("photo", "practice_photo", "Photo of a physical practice observed (mulching, zai pits, or terracing), if any", "Optional — for verification only.", "no", "${consent}='yes'", "", "", "", ""),

    # --- OC1 / OC2: Crop production, sales, and marketing (repeat group) ---
    ("note", "note_crops", "SECTION: Crop production and sales (OC1, OC2) — repeat for each crop sold", "", "", "${consent}='yes'", "", "", "", ""),
    ("begin_repeat", "crop_sales", "Crop sold", "", "", "${consent}='yes'", "", "", "", ""),
    ("select_one crop", "crop_name", "Crop", "", "yes", "", "", "", "", ""),
    ("decimal", "area_planted_acres", "Area planted to this crop (acres)", "", "yes", "", ". >= 0 and . <= ${landholding_acres}", "Area planted cannot exceed total landholding.", "", ""),
    ("decimal", "quantity_harvested_kg", "Quantity harvested (kg)", "Convert local units using the conversion table if needed.", "yes", "", ". >= 0 and . < 50000", "", "", ""),
    ("decimal", "quantity_sold_kg", "Quantity sold (kg)", "", "yes", "", ". >= 0 and . <= ${quantity_harvested_kg}", "Quantity sold cannot exceed quantity harvested.", "", ""),
    ("decimal", "price_received_kes_per_kg", "Price received (KES per kg)", "", "yes", ". > 0", ". > 0 and . < 500", "Check this price — it looks implausible.", "", ""),
    ("select_one buyer_type", "buyer_type", "Who was the main buyer?", "", "yes", "", "", "", "", ""),
    ("select_one yes_no", "sold_through_group", "Was this sale made through a producer group?", "", "yes", "", "", "", "", ""),
    ("end_repeat", "crop_sales", "", "", "", "", "", "", "", ""),

    # --- Resilience proxy ---
    ("note", "note_resilience", "SECTION: Coping strategies (resilience proxy)", "", "", "${consent}='yes'", "", "", "", ""),
    ("select_multiple coping_strategy", "coping_strategies_used", "In the last 30 days, has this household had to do any of the following because of a lack of food or money?", "", "yes", "${consent}='yes'", "", "", "", ""),

    ("note", "note_close", "Thank the respondent for their time.", "", "", "${consent}='yes'", "", "", "", ""),
]

survey_df = pd.DataFrame(survey, columns=[
    "type", "name", "label", "hint", "required", "relevant",
    "constraint", "constraint_message", "repeat_count", "appearance"
])

choices = [
    ("yes_no", "yes", "Yes"),
    ("yes_no", "no", "No"),

    ("sex", "male", "Male"),
    ("sex", "female", "Female"),

    ("sub_county", "kitui_rural", "Kitui Rural"),
    ("sub_county", "mwingi_west", "Mwingi West"),
    ("sub_county", "kitui_south", "Kitui South"),

    ("ward", "township", "Township"),
    ("ward", "mbitini", "Mbitini"),
    ("ward", "kwa_vonza", "Kwa Vonza / Yatta"),
    ("ward", "waita", "Waita"),
    ("ward", "kyome_thaana", "Kyome / Thaana"),
    ("ward", "mutonguni", "Mutonguni"),

    ("advisory_channel", "sms", "SMS"),
    ("advisory_channel", "ivr", "Voice call / IVR"),
    ("advisory_channel", "whatsapp", "WhatsApp group"),
    ("advisory_channel", "in_person", "In-person session"),
    ("advisory_channel", "radio", "Radio programme"),

    ("csa_practice", "drought_tolerant_seed", "Drought-tolerant certified seed"),
    ("csa_practice", "min_tillage", "Conservation / minimum tillage"),
    ("csa_practice", "mulching", "Mulching"),
    ("csa_practice", "water_harvesting", "Zai pits or terracing (water harvesting)"),
    ("csa_practice", "intercropping", "Intercropping with a legume"),
    ("csa_practice", "organic_amendment", "Organic soil amendment"),
    ("csa_practice", "staggered_planting", "Staggered planting"),

    ("crop", "green_grams", "Green grams"),
    ("crop", "sorghum", "Sorghum"),
    ("crop", "pigeon_peas", "Pigeon peas"),
    ("crop", "cowpeas", "Cowpeas"),
    ("crop", "maize", "Maize"),
    ("crop", "cassava", "Cassava"),
    ("crop", "other_crop", "Other"),

    ("buyer_type", "local_trader", "Local trader / broker"),
    ("buyer_type", "producer_group", "Producer / marketing group"),
    ("buyer_type", "market_vendor", "Open-air market vendor"),
    ("buyer_type", "processor", "Processor / aggregator company"),
    ("buyer_type", "other_buyer", "Other"),

    ("coping_strategy", "sold_productive_asset", "Sold a productive asset (livestock, tools) to buy food"),
    ("coping_strategy", "borrowed_food", "Borrowed food or relied on help from relatives"),
    ("coping_strategy", "reduced_meals", "Reduced the number of meals eaten per day"),
    ("coping_strategy", "child_labour", "Sent a child to work for food or money"),
    ("coping_strategy", "none", "None of the above"),
]

choices_df = pd.DataFrame(choices, columns=["list_name", "name", "label"])

settings_df = pd.DataFrame([{
    "form_title": "KDRSIP Household Survey",
    "form_id": "kdrsip_household_survey",
    "version": "2026090100",
    "default_language": "English",
    "style": "pages",
}])

out_path = "/home/claude/piece2/xlsform/kdrsip_household_survey_xlsform.xlsx"
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    survey_df.to_excel(writer, sheet_name="survey", index=False)
    choices_df.to_excel(writer, sheet_name="choices", index=False)
    settings_df.to_excel(writer, sheet_name="settings", index=False)

print(f"Written {out_path}")
