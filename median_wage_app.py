import streamlit as st
import plotly.graph_objects as go
import numpy as np

MEDIAN_INCOME = 74580
MIN_INCOME = 1000
MAX_INCOME = 5_000_000

st.set_page_config(page_title="Median Wage Tax Explorer", layout="wide")
st.title("🧮 Median Wage Tax Explorer")

st.markdown("### Explore the tax breakdown for the median American wage (top 50%)")

# Logarithmic horizontal slider for income
log_min = np.log10(MIN_INCOME)
log_max = np.log10(MAX_INCOME)
log_income = st.slider(
    label="Income (log scale)",
    min_value=log_min,
    max_value=log_max,
    value=np.log10(MEDIAN_INCOME),
    step=0.01
)
income = int(10 ** log_income)
st.write(f"Selected Income: ${income:,.0f}")

# Example: Show a simple bar chart for this income
fig = go.Figure(go.Bar(x=["Income"], y=[income], marker_color="#87ceeb"))
fig.update_layout(yaxis_title="Income ($)", xaxis_title="", height=400)
st.plotly_chart(fig, use_container_width=True)
