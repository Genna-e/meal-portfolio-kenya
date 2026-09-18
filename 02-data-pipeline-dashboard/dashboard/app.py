"""
KDRSIP M&E Dashboard — Streamlit app

Reports on the indicators defined in Piece 1 (01-measurement-system.md):
  OP1  reach                -> reach_pct
  OP2  FFS completion       -> ffs_completion_pct
  IR2  practice adoption    -> adoption_pct
  OC1  yield / volatility   -> mean_yield_kg_per_acre, yield_cv
  OC1  household income     -> median_crop_income_kes
  IR3  group marketing      -> group_sale_pct
  OC2  price share          -> mean_price_share_pct
  Impact proxy              -> high_coping_pct (lower is better)

Run with: streamlit run app.py
"""
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="KDRSIP M&E Dashboard", layout="wide", page_icon="🌾")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data", "clean")

# Targets from Piece 1's results framework — the dashboard always shows
# performance against these, never against an arbitrary trend line.
TARGETS = {
    "reach_pct":             {"Baseline": 0,    "Y1": 25,   "Y2": 58,   "Y3": 83,   "Y4": 100},
    "ffs_completion_pct":    {"Baseline": 0,    "Y1": 18,   "Y2": 40,   "Y3": 58,   "Y4": 70},
    "adoption_pct":          {"Baseline": 9,    "Y1": 20,   "Y2": 35,   "Y3": 47,   "Y4": 55},
    "group_sale_pct":        {"Baseline": 6,    "Y1": 15,   "Y2": 27,   "Y3": 36,   "Y4": 45},
    "mean_yield_kg_per_acre":{"Baseline": 310,  "Y1": 365,  "Y2": 425,  "Y3": 475,  "Y4": 520},
    "median_crop_income_kes":{"Baseline": 18400,"Y1": 21500,"Y2": 25500,"Y3": 29000,"Y4": 32000},
}
ROUND_ORDER = ["Baseline", "Y1", "Y2", "Y3", "Y4"]


@st.cache_data
def load_data():
    summary = pd.read_csv(f"{DATA_DIR}/indicators_by_round.csv")
    summary["survey_round"] = pd.Categorical(summary["survey_round"], categories=ROUND_ORDER, ordered=True)
    summary = summary.sort_values("survey_round")

    subcounty = pd.read_csv(f"{DATA_DIR}/indicators_by_subcounty_latest.csv")

    records = pd.read_csv(f"{DATA_DIR}/household_survey_clean.csv")
    records["survey_round"] = pd.Categorical(records["survey_round"], categories=ROUND_ORDER, ordered=True)

    cleaning_log = pd.read_csv(f"{DATA_DIR}/cleaning_log.csv")
    return summary, subcounty, records, cleaning_log


try:
    summary, subcounty, records, cleaning_log = load_data()
except FileNotFoundError:
    st.error(
        "Clean data not found. Run `python data_pipeline/generate_synthetic_data.py` "
        "then `python data_pipeline/clean_data.py` before launching this dashboard."
    )
    st.stop()

SUBCOUNTY_LABELS = {"kitui_rural": "Kitui Rural", "mwingi_west": "Mwingi West", "kitui_south": "Kitui South"}

# ---------- Sidebar ----------
st.sidebar.title("🌾 KDRSIP M&E Dashboard")
st.sidebar.caption("Kitui Drought Resilience and Smallholder Income Programme — illustrative portfolio exercise")
selected_round = st.sidebar.selectbox("Reporting round", ROUND_ORDER, index=len(ROUND_ORDER) - 1)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Indicators shown here are defined in **Piece 1** of this portfolio "
    "(theory of change, logframe, and PIRS). All data is synthetic and "
    "clearly illustrative — see the [full methodology on GitHub]"
    "(https://github.com/Genna-e/meal-portfolio-kenya)."
)

row = summary[summary["survey_round"] == selected_round].iloc[0]


def kpi_delta(value, target, higher_is_better=True):
    diff = value - target
    return f"{diff:+.1f} vs target" if higher_is_better else f"{diff:+.1f} vs target"


# ---------- Header ----------
st.title("KDRSIP Results Dashboard")
st.caption(f"Reporting round: **{selected_round}**  ·  n = {int(row['n_households'])} households")

# ---------- KPI row ----------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(
        "Advisory reach (OP1)",
        f"{row['reach_pct']:.0f}%",
        kpi_delta(row["reach_pct"], TARGETS["reach_pct"][selected_round]),
    )
with c2:
    st.metric(
        "Practice adoption (IR2)",
        f"{row['adoption_pct']:.0f}%",
        kpi_delta(row["adoption_pct"], TARGETS["adoption_pct"][selected_round]),
    )
with c3:
    st.metric(
        "Median crop income (OC1)",
        f"KES {row['median_crop_income_kes']:,.0f}",
        kpi_delta(row["median_crop_income_kes"], TARGETS["median_crop_income_kes"][selected_round]),
    )
with c4:
    st.metric(
        "Mean yield (OC1)",
        f"{row['mean_yield_kg_per_acre']:.0f} kg/acre",
        kpi_delta(row["mean_yield_kg_per_acre"], TARGETS["mean_yield_kg_per_acre"][selected_round]),
    )

c5, c6, c7, c8 = st.columns(4)
with c5:
    st.metric("FFS completion (OP2)", f"{row['ffs_completion_pct']:.0f}%",
               kpi_delta(row["ffs_completion_pct"], TARGETS["ffs_completion_pct"][selected_round]))
with c6:
    st.metric("Group marketing (IR3)", f"{row['group_sale_pct']:.0f}%",
               kpi_delta(row["group_sale_pct"], TARGETS["group_sale_pct"][selected_round]))
with c7:
    st.metric("Farm-gate price share (OC2)", f"{row['mean_price_share_pct']:.0f}%")
with c8:
    st.metric("Households using negative coping (resilience proxy)", f"{row['high_coping_pct']:.0f}%",
               help="Lower is better. Not a Piece 1 indicator on its own — tracked as a resilience proxy.")

st.markdown("---")

# ---------- Trend vs target charts ----------
st.subheader("Progress against target, by round")

trend_col1, trend_col2 = st.columns(2)


def trend_chart(indicator, title, y_suffix=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ROUND_ORDER, y=[summary.set_index("survey_round").loc[r, indicator] for r in ROUND_ORDER],
        mode="lines+markers", name="Actual", line=dict(color="#2d5016", width=3), marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=ROUND_ORDER, y=[TARGETS[indicator][r] for r in ROUND_ORDER],
        mode="lines+markers", name="Target", line=dict(color="#c98a2b", width=2, dash="dash"),
    ))
    fig.update_layout(title=title, height=360, margin=dict(t=50, b=60, l=10, r=10),
                       legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
    return fig


with trend_col1:
    st.plotly_chart(trend_chart("adoption_pct", "IR2 — Practice adoption (%)"), use_container_width=True)
    st.plotly_chart(trend_chart("mean_yield_kg_per_acre", "OC1 — Mean yield (kg/acre)"), use_container_width=True)

with trend_col2:
    st.plotly_chart(trend_chart("median_crop_income_kes", "OC1 — Median crop income (KES)"), use_container_width=True)
    st.plotly_chart(trend_chart("reach_pct", "OP1 — Advisory reach (%)"), use_container_width=True)

st.markdown("---")

# ---------- Disaggregation ----------
st.subheader(f"Disaggregation — {selected_round}")

d1, d2 = st.columns(2)

with d1:
    st.markdown("**Reach by household head sex**")
    sex_fig = go.Figure(go.Bar(
        x=["Female-headed", "Male-headed"],
        y=[row["reach_pct_female_head"], row["reach_pct_male_head"]],
        marker_color=["#c98a2b", "#4a6fa5"],
    ))
    sex_fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Reach (%)")
    st.plotly_chart(sex_fig, use_container_width=True)
    if row["reach_pct_female_head"] < 45 and selected_round != "Baseline":
        st.warning(
            "Female-headed household reach is below the 45% operational threshold set in the PIRS. "
            "This should trigger a review of the delivery channel mix at the next reflection session."
        )

with d2:
    st.markdown("**Latest-round indicators by sub-county**")
    sc = subcounty.copy()
    sc["sub_county"] = sc["sub_county"].map(SUBCOUNTY_LABELS).fillna(sc["sub_county"])
    sc_fig = go.Figure()
    sc_fig.add_trace(go.Bar(name="Reach %", x=sc["sub_county"], y=sc["reach_pct"], marker_color="#4a6fa5"))
    sc_fig.add_trace(go.Bar(name="Adoption %", x=sc["sub_county"], y=sc["adoption_pct"], marker_color="#5a8f4a"))
    sc_fig.update_layout(barmode="group", height=300, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(sc_fig, use_container_width=True)

st.markdown("---")

# ---------- Data quality ----------
with st.expander("Data quality log for this dataset (per the DQA plan in Piece 1)"):
    st.dataframe(cleaning_log, use_container_width=True, hide_index=True)
    st.caption(
        "Every value shown on this dashboard has passed the range constraints, deduplication, "
        "and documented missing-data rules set out in Piece 1, Section 5. Flagged values are set "
        "to missing and excluded from the relevant indicator's denominator — never imputed."
    )

with st.expander("Household-level data (sampled)"):
    show_cols = [
        "household_id", "survey_round", "sub_county", "ward", "household_head_sex",
        "landholding_acres", "reached_flag", "ffs_flag", "n_practices_adopted",
        "adopter_flag", "yield_kg_per_acre", "crop_income_kes", "group_sale_flag",
    ]
    st.dataframe(
        records[records["survey_round"] == selected_round][show_cols].sample(
            min(50, len(records[records["survey_round"] == selected_round])), random_state=1
        ),
        use_container_width=True, hide_index=True,
    )

st.caption(
    "KDRSIP is a fictional programme built as a professional portfolio exercise. "
    "All data on this dashboard is synthetic and illustrative."
)
