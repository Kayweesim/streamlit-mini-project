import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PSA Port Analytics Dashboard",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; }
    .metric-card {
        background: #0f1923;
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
    }
    .section-header {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        color: #5a8fc4;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# Plotly configurations
plotly_config = {
    'displayModeBar': False,
    'responsive': True
}



# ── Data generation ───────────────────────────────────────────────────────────
@st.cache_data
def generate_data(seed: int = 42):
    rng = np.random.default_rng(seed)
    today = datetime.today()

    # ── Daily throughput (last 365 days) ──
    dates = pd.date_range(end=today, periods=365, freq="D")
    
    # print(dates) Checking dates, so basically from day 1 to day 365, day 365 being today.

    base = 85_000  # TEUs / day (realistic PSA scale)
    
    # Print evenly spaced intervals from 0 to 8000, total 365 values, so basically a linear growth over the year.
    trend = np.linspace(0, 8_000, 365)
    
    seasonality = 6_000 * np.sin(2 * np.pi * np.arange(365) / 365)

    # print(seasonality.shape) # Checking seasonality shape, should be (365,)
    noise = rng.normal(0, 2_500, 365)

    # print(noise) # Checking noise shape, should be (365,)
    throughput = pd.DataFrame({
        "date": dates,
        "teu": (base + trend + seasonality + noise).clip(60_000, 120_000).astype(int),
    })

    # ── Vessel arrivals (last 90 days) ──
    vessel_dates = pd.date_range(end=today, periods=90, freq="D")
    vessels = pd.DataFrame({
        "date": vessel_dates,
        "arrivals": rng.integers(18, 38, 90),
        "avg_turnaround_hrs": rng.uniform(14, 32, 90).round(1),
    })

    # ── Berth utilisation by terminal ──
    terminals = ["Tanjong Pagar", "Keppel", "Brani", "Pasir Panjang T1-2", "Pasir Panjang T3-4", "Tuas"]
    berth = pd.DataFrame({
        "terminal": terminals,
        "utilisation": rng.uniform(0.62, 0.97, len(terminals)).round(3),
        "berths": [6, 8, 4, 10, 10, 14],
    })
    berth["occupied"] = (berth["utilisation"] * berth["berths"]).round(1)

    # ── Vessel type breakdown ──
    vessel_types = pd.DataFrame({
        "type": ["Container", "Bulk Carrier", "Tanker", "RORO", "General Cargo"],
        "count": [1_240, 380, 520, 145, 95],
    })

    # ── Top trade routes ──
    routes = pd.DataFrame({
        "route": ["Singapore–China", "Singapore–Europe", "Singapore–US", "Singapore–India", "Singapore–SE Asia"],
        "teu_thousands": [4_820, 3_105, 2_780, 1_940, 3_650],
        "yoy_growth": [4.2, 1.8, 3.1, 6.7, 5.3],
    })

    return throughput, vessels, berth, vessel_types, routes


throughput_df, vessels_df, berth_df, vessel_types_df, routes_df = generate_data()

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🚢 PSA Port Analytics")
    st.caption("Singapore Container Port — Simulated Data")
    st.divider()

    date_range = st.slider(
        "Throughput lookback (days)",
        min_value=30, max_value=365, value=180, step=30,
    )
    show_ma = st.checkbox("Show 7-day moving average", value=True)
    st.divider()

    selected_terminals = st.multiselect(
        "Filter terminals",
        options=berth_df["terminal"].tolist(),
        default=berth_df["terminal"].tolist(),
    )
    st.divider()
    st.markdown("**About this dashboard**")
    st.caption(
        "Built with Streamlit, pandas & Plotly. "
        "Data is synthetically generated to mirror realistic PSA port operations."
    )

# ── KPI row ───────────────────────────────────────────────────────────────────
st.markdown("## Port Operations Dashboard")
st.caption(f"Data as of {datetime.today().strftime('%d %b %Y')} · All figures simulated")

filtered = throughput_df.tail(date_range)
total_teu = filtered["teu"].sum()
avg_daily = filtered["teu"].mean()
recent_vessels = vessels_df.tail(30)
avg_turnaround = recent_vessels["avg_turnaround_hrs"].mean()
avg_berth_util = berth_df["utilisation"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total TEUs (period)", f"{total_teu/1_000_000:.2f}M", f"+4.3% YoY")
col2.metric("Avg Daily TEUs", f"{avg_daily:,.0f}", f"+1.2% vs prev period")
col3.metric("Avg Turnaround", f"{avg_turnaround:.1f} hrs", f"-1.8 hrs vs last month")
col4.metric("Avg Berth Utilisation", f"{avg_berth_util:.0%}", f"+2pp YoY")

st.divider()

# ── Row 1: Throughput chart + vessel arrivals ─────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown('<p class="section-header">Daily Container Throughput (TEUs)</p>', unsafe_allow_html=True)
    fig_tp = go.Figure()
    fig_tp.add_trace(go.Scatter(
        x=filtered["date"], y=filtered["teu"],
        mode="lines", name="Daily TEU",
        line=dict(color="#2196f3", width=1.5),
        fill="tozeroy", fillcolor="rgba(33,150,243,0.08)",
    ))
    if show_ma:
        ma = filtered["teu"].rolling(7).mean()
        fig_tp.add_trace(go.Scatter(
            x=filtered["date"], y=ma,
            mode="lines", name="7-day MA",
            line=dict(color="#ff9800", width=2.5, dash="dot"),
        ))
    fig_tp.update_layout(
        height=280, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.12),
        xaxis=dict(showgrid=False),
        yaxis=dict(tickformat=",", gridcolor="rgba(255,255,255,0.05)"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_tp, config=plotly_config)

with col_right:
    st.markdown('<p class="section-header">Vessel Arrivals (last 90 days)</p>', unsafe_allow_html=True)
    fig_v = px.bar(
        vessels_df, x="date", y="arrivals",
        color="arrivals",
        color_continuous_scale=["#1a3a5c", "#2196f3", "#00e5ff"],
    )
    fig_v.update_layout(
        height=280, margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_v, config=plotly_config)

# ── Row 2: Berth utilisation + vessel types + trade routes ────────────────────
col_a, col_b, col_c = st.columns([2, 1.5, 2])

with col_a:
    st.markdown('<p class="section-header">Berth Utilisation by Terminal</p>', unsafe_allow_html=True)
    display_berth = berth_df[berth_df["terminal"].isin(selected_terminals)].copy()
    display_berth = display_berth.sort_values("utilisation", ascending=True)
    colors = ["#e74c3c" if u > 0.9 else "#f39c12" if u > 0.80 else "#40AEE4"
              for u in display_berth["utilisation"]]
    fig_b = go.Figure(go.Bar(
        x=display_berth["utilisation"],
        y=display_berth["terminal"],
        orientation="h",
        marker_color=colors,
        text=[f"{u:.0%}" for u in display_berth["utilisation"]],
        textposition="inside",
    ))

    # Threshold of 85% (x)

    fig_b.add_vline(x=0.85, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                    annotation_text="85% threshold", annotation_position="top right")
    fig_b.update_layout(
        height=260, margin=dict(l=0, r=60, t=10, b=0),
        xaxis=dict(tickformat=".0%", range=[0, 1.05], showgrid=True),
        yaxis=dict(showgrid=False),
        plot_bgcolor="rgba(20,20,20,20)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_b, config=plotly_config,  use_container_width=True)

with col_b:
    st.markdown('<p class="section-header">Vessel Type Mix</p>', unsafe_allow_html=True)
    fig_pie = px.pie(
        vessel_types_df, values="count", names="type",
        color_discrete_sequence=["#2196f3", "#00bcd4", "#ff9800", "#4caf50", "#9c27b0"],
        hole=0.45,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent")
    fig_pie.update_layout(
        height=260, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(font=dict(size=10), orientation="v"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_pie, config=plotly_config, use_container_width=True)

with col_c:
    st.markdown('<p class="section-header">Top Trade Routes (TEU × 1,000)</p>', unsafe_allow_html=True)
    fig_r = px.scatter(
        routes_df, x="teu_thousands", y="yoy_growth",
        size="teu_thousands", text="route",
        color="yoy_growth",
        color_continuous_scale=["#1a3a5c", "#2196f3", "#00e5ff"],
        size_max=40,
    )
    fig_r.update_traces(textposition="top center", textfont_size=10)
    fig_r.update_layout(
        height=260, margin=dict(l=0, r=0, t=10, b=20),
        coloraxis_showscale=False,
        xaxis_title="Volume (TEU ×1k)", yaxis_title="YoY Growth %",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_r, config=plotly_config, use_container_width=True)

# ── Row 3: Raw data expander ──────────────────────────────────────────────────
st.divider()
with st.expander("📋 View raw data tables"):
    tab1, tab2, tab3 = st.tabs(["Throughput", "Vessel Arrivals", "Berth Utilisation"])

    with tab1:
        st.dataframe(filtered.tail(30).sort_values("date", ascending=False), width='stretch')
    with tab2:
        st.dataframe(vessels_df.sort_values("date", ascending=False), width='stretch')
    with tab3:
        st.dataframe(berth_df, width='stretch')
