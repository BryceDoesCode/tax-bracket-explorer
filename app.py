import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

# --- Tax Bracket Data ---
TAX_BRACKETS = {
    "Current": [
        {"min": 0, "max": 11000, "rate": 0.10},
        {"min": 11000, "max": 44725, "rate": 0.12},
        {"min": 44725, "max": 95375, "rate": 0.22},
        {"min": 95375, "max": 182100, "rate": 0.24},
        {"min": 182100, "max": 231250, "rate": 0.32},
        {"min": 231250, "max": 578125, "rate": 0.35},
        {"min": 578125, "max": float('inf'), "rate": 0.37},
    ],
    "1960s (High Tax)": [
        {"min": 0, "max": 2000, "rate": 0.20},
        {"min": 2000, "max": 4000, "rate": 0.22},
        {"min": 4000, "max": 6000, "rate": 0.26},
        {"min": 6000, "max": 8000, "rate": 0.30},
        {"min": 8000, "max": 10000, "rate": 0.34},
        {"min": 10000, "max": 12000, "rate": 0.38},
        {"min": 12000, "max": 14000, "rate": 0.43},
        {"min": 14000, "max": 16000, "rate": 0.47},
        {"min": 16000, "max": 18000, "rate": 0.50},
        {"min": 18000, "max": 20000, "rate": 0.53},
        {"min": 20000, "max": 22000, "rate": 0.56},
        {"min": 22000, "max": 26000, "rate": 0.59},
        {"min": 26000, "max": 32000, "rate": 0.62},
        {"min": 32000, "max": 38000, "rate": 0.65},
        {"min": 38000, "max": 44000, "rate": 0.69},
        {"min": 44000, "max": 50000, "rate": 0.72},
        {"min": 50000, "max": 60000, "rate": 0.75},
        {"min": 60000, "max": 70000, "rate": 0.78},
        {"min": 70000, "max": 80000, "rate": 0.81},
        {"min": 80000, "max": 90000, "rate": 0.84},
        {"min": 90000, "max": 100000, "rate": 0.87},
        {"min": 100000, "max": 150000, "rate": 0.89},
        {"min": 150000, "max": 200000, "rate": 0.90},
        {"min": 200000, "max": float('inf'), "rate": 0.91},
    ],
    "Lowest Brackets (Hypothetical)": [
        {"min": 0, "max": 20000, "rate": 0.05},
        {"min": 20000, "max": 100000, "rate": 0.10},
        {"min": 100000, "max": float('inf'), "rate": 0.15},
    ],
}

MEDIAN_INCOME = 74580

# --- Adjust 1960s brackets to 2023 dollars (CPI inflation factor) ---
ADJUST_1960S = 13.39
for b in TAX_BRACKETS["1960s (High Tax)"]:
    b["min"] = int(b["min"] * ADJUST_1960S)
    b["max"] = float('inf') if b["max"] == float('inf') else int(b["max"] * ADJUST_1960S)

# --- Helper Functions ---
def calculate_bracket_segments(income: float, brackets: List[Dict]) -> List[Dict]:
    segments = []
    for i, b in enumerate(brackets):
        lower = b["min"]
        upper = min(b["max"], income)
        if income > lower:
            amount = max(0, upper - lower)
            tax = amount * b["rate"]
            segments.append({
                "bracket": f"${lower:,.0f} - ${b['max'] if b['max'] != float('inf') else '∞'}",
                "amount": amount,
                "tax": tax,
                "rate": b["rate"],
                "lower": lower,
                "upper": upper
            })
    return segments

def get_skyblue_purple_cmap():
    # Sky blue: #87ceeb, Deep purple: #2e003e
    return LinearSegmentedColormap.from_list('SkyBluePurple', ['#87ceeb', '#2e003e'])

# --- Static color assignment for each regime's brackets ---
STATIC_COLORS = {}
def get_static_colors(regime):
    n = len(TAX_BRACKETS[regime])
    if regime not in STATIC_COLORS:
        cmap = get_skyblue_purple_cmap()
        STATIC_COLORS[regime] = [f"rgba{tuple(int(255*x) for x in cmap(i/(n-1))[:3]) + (0.85,)}" for i in range(n)]
    return STATIC_COLORS[regime]

def get_gradient_colors(n):
    cmap = get_skyblue_purple_cmap()
    return [f"rgba{tuple(int(255*x) for x in cmap(i/(n-1))[:3]) + (0.85,)}" for i in range(n)]

def make_stacked_bar(segments1, segments2=None, label1="Income 1", label2="Income 2", net_income1=None, net_income2=None, regime1=None, regime2=None):
    n = len(segments1)
    # Use static colors for regime (original behavior)
    colors = get_static_colors(regime1) if regime1 else get_gradient_colors(n)
    fig = go.Figure()
    # Bar 1
    cum = 0
    for i, seg in enumerate(segments1):
        fig.add_trace(go.Bar(
            x=[label1],
            y=[seg["amount"]],
            base=[cum],
            marker_color=colors[i],
            name=seg["bracket"],
            customdata=[[seg["amount"], seg["rate"], seg["tax"]]],
            hovertemplate="Bracket: %{name}<br>Amount: $%{customdata[0]:,.0f}<br>Rate: %{customdata[1]:.0%}<br>Tax: $%{customdata[2]:,.0f}<extra></extra>",
            width=0.5
        ))
        cum += seg["amount"]
    # Net income bar (green)
    if net_income1 is not None:
        fig.add_trace(go.Bar(
            x=[label1+" Net"],
            y=[net_income1],
            base=[0],
            marker_color="rgba(0,200,100,0.7)",
            name="Net Income",
            hovertemplate="Net Income: $%{y:,.0f}<extra></extra>",
            width=0.3
        ))
    # Bar 2 (comparison)
    cum2 = 0
    if segments2:
        n2 = len(segments2)
        colors2 = get_static_colors(regime2) if regime2 else get_gradient_colors(n2)
        for i, seg in enumerate(segments2):
            fig.add_trace(go.Bar(
                x=[label2],
                y=[seg["amount"]],
                base=[cum2],
                marker_color=colors2[i],
                name=seg["bracket"],
                customdata=[[seg["amount"], seg["rate"], seg["tax"]]],
                hovertemplate="Bracket: %{name}<br>Amount: $%{customdata[0]:,.0f}<br>Rate: %{customdata[1]:.0%}<br>Tax: $%{customdata[2]:,.0f}<extra></extra>",
                width=0.35
            ))
            cum2 += seg["amount"]
        # Net income bar for comparison
        if net_income2 is not None:
            fig.add_trace(go.Bar(
                x=[label2+" Net"],
                y=[net_income2],
                base=[0],
                marker_color="rgba(0,200,100,0.7)",
                name="Net Income (Comparison)",
                hovertemplate="Net Income: $%{y:,.0f}<extra></extra>",
                width=0.2
            ))
    # Median income reference line
    max_y = max(MEDIAN_INCOME*2, cum, cum2 if segments2 else 0, net_income1 or 0, net_income2 or 0) * 1.1
    fig.add_shape(type="line", x0=-0.5, x1=3, y0=MEDIAN_INCOME, y1=MEDIAN_INCOME,
                  line=dict(color="orange", width=2, dash="dash"),
                  xref="x", yref="y")
    fig.add_annotation(x=0.5, y=MEDIAN_INCOME, text="Median US Income ($74,580)",
                      showarrow=False, yshift=10, font=dict(color="orange", size=12))
    fig.update_layout(
        barmode="stack",
        xaxis_title="Individual",
        yaxis_title="Income ($)",
        yaxis=dict(range=[0, max_y]),
        legend_title="Tax Bracket",
        hovermode="x unified",
        bargap=0.25,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- Predefined income markers ---
INCOME_MARKERS = {
    'Top 0.1% of Earners': 3511455,
    'Top 1% of Earners': 868483,
    'Top 5% of Earners': 356044,
    'Top 10% of Earners': 177697
}

# --- Streamlit UI ---
st.set_page_config(page_title="Tax Bracket Bar Explorer", layout="wide")
st.title("🧮 Tax Bracket Bar Explorer")

col1, col2 = st.columns([2, 1])

def smart_slider(label, min_value, max_value, value):
    stops = list(range(min_value, 100_000, 1000))
    stops += list(range(100_000, 500_000, 5000))
    stops += list(range(500_000, 1_000_000, 25_000))
    stops += list(range(1_000_000, 5_000_001, 100_000))
    stops = sorted(set(stops))
    # Ensure value is in stops
    if value not in stops:
        # Find closest value in stops
        value = min(stops, key=lambda x: abs(x - value))
    return st.select_slider(label, options=stops, value=value)

with col2:
    st.header("Settings")
    regime = st.selectbox("Tax Bracket Regime", list(TAX_BRACKETS.keys()))
    st.markdown("**Quick Select Incomes:**")
    marker_cols = st.columns(len(INCOME_MARKERS))
    marker_clicked = None
    # Use session state to persist button clicks
    if 'income_marker' not in st.session_state:
        st.session_state['income_marker'] = MEDIAN_INCOME  # Default to median income
    for i, (label, val) in enumerate(INCOME_MARKERS.items()):
        if marker_cols[i].button(label):
            st.session_state['income_marker'] = val
    # Median income button below, full width, green with green hover
    st.markdown("""
        <style>
        div[data-testid="stButton"] > button.median-income-btn {
            background-color: #27ae60 !important;
            color: white !important;
            border: none !important;
            width: 100% !important;
            font-weight: 600 !important;
            font-size: 1.1em !important;
            margin-top: 0.5em !important;
            margin-bottom: 0.5em !important;
            transition: background 0.2s !important;
        }
        div[data-testid="stButton"] > button.median-income-btn:hover {
            background-color: #1e874b !important;
        }
        </style>
    """, unsafe_allow_html=True)
    median_btn = st.button("Median Income ($74,580)", key="median_btn", help="Set income to median")
    if median_btn:
        st.session_state['income_marker'] = MEDIAN_INCOME
    # Main income slider
    if st.session_state.get('income_marker') == MEDIAN_INCOME:
        income = MEDIAN_INCOME
    else:
        income = st.session_state.get('income_marker', MEDIAN_INCOME)
    if income is None:
        income = MEDIAN_INCOME
    income = smart_slider("Income", 0, 5_000_000, income)
    # Reset marker if slider is changed
    if income != st.session_state.get('income_marker', None):
        st.session_state['income_marker'] = None
    compare = st.checkbox("Compare with another income")
    if compare:
        marker2_clicked = None
        marker2_cols = st.columns(len(INCOME_MARKERS))
        # Add comparison regime selector
        regime2 = st.selectbox("Comparison Tax Bracket Regime", list(TAX_BRACKETS.keys()), key="regime2_select", index=list(TAX_BRACKETS.keys()).index(regime))
        if 'income2_marker' not in st.session_state:
            st.session_state['income2_marker'] = None
        for i, (label, val) in enumerate(INCOME_MARKERS.items()):
            if marker2_cols[i].button(label, key=f"cmp_{label}"):
                st.session_state['income2_marker'] = val
        cmp_median_btn = st.button("Median Income ($74,580)", key="cmp_median_btn", help="Set comparison income to median")
        if cmp_median_btn:
            st.session_state['income2_marker'] = MEDIAN_INCOME
        if st.session_state['income2_marker'] is not None:
            income2 = st.session_state['income2_marker']
        else:
            income2 = 100_000
        income2 = smart_slider("Comparison Income", 0, 5_000_000, income2)
        if income2 != st.session_state.get('income2_marker', None):
            st.session_state['income2_marker'] = None
    else:
        income2 = None
        regime2 = None
        st.session_state['income2_marker'] = None

with col1:
    segments1 = calculate_bracket_segments(income, TAX_BRACKETS[regime])
    segments2 = None
    total_tax1 = sum(s["tax"] for s in segments1)
    net_income1 = income - total_tax1
    eff_rate1 = total_tax1 / income if income > 0 else 0
    total_tax2 = None
    net_income2 = None
    eff_rate2 = None
    fig = make_stacked_bar(segments1, None, label1="Primary", net_income1=net_income1, regime1=regime)
    if compare and income2 is not None and regime2 is not None:
        segments2 = calculate_bracket_segments(income2, TAX_BRACKETS[regime2])
        total_tax2 = sum(s["tax"] for s in segments2)
        net_income2 = income2 - total_tax2
        eff_rate2 = total_tax2 / income2 if income2 > 0 else 0
        fig = make_stacked_bar(segments1, segments2, label1="Primary", label2="Comparison", net_income1=net_income1, net_income2=net_income2, regime1=regime, regime2=regime2)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    if compare and income2 is not None and segments2 is not None and total_tax2 is not None and net_income2 is not None and eff_rate2 is not None:
        st.markdown(f"**Primary:** Total Tax Paid: `${total_tax1:,.0f}` | Net Income: `${net_income1:,.0f}` | Effective Rate: `{eff_rate1*100:.2f}%`  ")
        st.markdown(f"**Comparison:** Total Tax Paid: `${total_tax2:,.0f}` | Net Income: `${net_income2:,.0f}` | Effective Rate: `{eff_rate2*100:.2f}%`  ")
    else:
        st.markdown(f"**Total Tax Paid:** `${total_tax1:,.0f}` | **Net Income:** `${net_income1:,.0f}` | **Effective Rate:** `{eff_rate1*100:.2f}%`")

# --- Final Income Spread: Population Percentiles + Income Markers ---
INCOME_SPREAD = [
    {"label": "$0 - $20,000", "min": 0, "max": 20000, "percent": 0.12},
    {"label": "$20,000 - $50,000", "min": 20000, "max": 50000, "percent": 0.28},
    {"label": "$50,000 - $75,000", "min": 50000, "max": 75000, "percent": 0.20},
    {"label": "$75,000 - $100,000", "min": 75000, "max": 100000, "percent": 0.15},
    {"label": "Top 10% ($177,697+)", "min": 177697, "max": 356044, "percent": 0.10},
    {"label": "Top 5% ($356,044+)", "min": 356044, "max": 868483, "percent": 0.05},
    {"label": "Top 1% ($868,483+)", "min": 868483, "max": 3511455, "percent": 0.01},
    {"label": "Top 0.1% ($3,511,455+)", "min": 3511455, "max": None, "percent": 0.001}
]
