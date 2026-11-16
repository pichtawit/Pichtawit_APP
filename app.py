import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# Page config (16:9 widescreen layout)
st.set_page_config(
    page_title="SET100 Top Momentum Screener",
    page_icon="📈",
    layout="wide",
)

SET100_TICKERS = [
    "AAV", "ADVANC", "AEONTS", "AMATA", "AOT", "AP", "AURA", "AWC", "BA", "BAM",
    "BANPU", "BBL", "BCH", "BCP", "BCPG", "BDMS", "BEM", "BGRIM", "BH", "BJC",
    "BLA", "BTG", "BTS", "CBG", "CCET", "CENTEL", "CHG", "CK", "COM7", "CPALL",
    "CPF", "CPN", "CRC", "DELTA", "DOHOME", "EA", "EGCO", "ERW", "GFPT", "GLOBAL",
    "GPSC", "GST", "GULF", "GUNKUL", "HANA", "HMPRO", "ICHI", "IRPC", "IVL", "JMART",
    "JMT", "KBANK", "KCE", "KKP", "KTB", "KTC", "LH", "M", "MEGA", "MINT",
    "MOSHI", "MRDIYT", "MTC", "OR", "OSP", "PLANB", "PR9", "PRM", "PTG", "PTT",
    "PTTEP", "PTTGC", "QH", "RATCH", "RCL", "SAWAD", "SCB", "SCC", "SCGP", "SIRI",
    "SPALI", "SPRC", "STA", "STECON", "STGT", "TASCO", "TCAP", "TFG", "THAI", "TIDLOR",
    "TISCO", "TLI", "TOA", "TOP", "TRUE", "TTB", "TU", "VGI", "WHA", "WHAUP"
]


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_and_process_data(period: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Downloads SET100 data from Yahoo Finance, normalizes to 1.0, and computes returns."""
    yf_tickers = [f"{ticker}.BK" for ticker in SET100_TICKERS]
    raw = yf.download(yf_tickers, period=period, progress=False)["Close"]

    # Clean column names (strip .BK suffix)
    raw.columns = [col.replace(".BK", "") for col in raw.columns]

    # Identify tickers that returned no data
    missing_tickers = [col for col in raw.columns if raw[col].isna().all()]
    valid_data = raw.dropna(axis=1, how="all").ffill()

    # Normalize each stock to 1.0 at its first valid trading day in the period
    normalized = valid_data.apply(lambda col: col / col.dropna().iloc[0])

    # Sort descending by latest normalized ratio
    latest_ratios = normalized.iloc[-1].sort_values(ascending=False)
    sorted_normalized = normalized[latest_ratios.index]

    # Build summary stats table
    summary_rows = []
    for rank, (ticker, ratio) in enumerate(latest_ratios.items(), start=1):
        series = valid_data[ticker].dropna()
        start_price = series.iloc[0]
        end_price = series.iloc[-1]
        pct_return = (ratio - 1.0) * 100.0
        max_drawdown = ((series / series.cummax()) - 1.0).min() * 100.0

        summary_rows.append({
            "Rank": rank,
            "Ticker": ticker,
            "Start Price (THB)": round(float(start_price), 2),
            "Latest Price (THB)": round(float(end_price), 2),
            "Return (%)": round(float(pct_return), 2),
            "Normalized Ratio": round(float(ratio), 4),
            "Max Drawdown (%)": round(float(max_drawdown), 2),
        })

    summary_df = pd.DataFrame(summary_rows)
    return sorted_normalized, summary_df, missing_tickers


# --- Sidebar Controls ---
st.sidebar.header("Screener Parameters")
time_period = st.sidebar.selectbox(
    "Lookback Period",
    options=["1mo", "3mo", "6mo", "1y", "2y", "ytd"],
    index=2,  # Default: 6mo
)
top_n = st.sidebar.slider("Number of Top Stocks", min_value=5, max_value=50, value=20, step=5)

if st.sidebar.button("Refresh Market Data", use_container_width=True):
    st.cache_data.clear()

# --- Main App ---
st.title("📈 Top SET100 Performers (Normalized to 1.0)")

with st.spinner(f"Fetching SET100 data ({time_period}) from Yahoo Finance..."):
    sorted_normalized, summary_df, missing_tickers = fetch_and_process_data(time_period)

top_normalized = sorted_normalized.iloc[:, :top_n]
top_summary = summary_df.head(top_n)

# Top KPI Metrics Row
col1, col2, col3, col4 = st.columns(4)
leader = top_summary.iloc[0]
nth_stock = top_summary.iloc[-1]
avg_top_return = top_summary["Return (%)"].mean()
median_set100_return = summary_df["Return (%)"].median()

col1.metric("#1 Performer", f"{leader['Ticker']}", f"{leader['Return (%)']:+.2f}%")
col2.metric(f"#{top_n} Cutoff", f"{nth_stock['Ticker']}", f"{nth_stock['Return (%)']:+.2f}%")
col3.metric(f"Top {top_n} Avg Return", f"{avg_top_return:+.2f}%")
col4.metric("SET100 Median Return", f"{median_set100_return:+.2f}%")

# Interactive Plotly Line Chart
plot_df = top_normalized.reset_index().melt(
    id_vars="Date", var_name="Ticker", value_name="Normalized Ratio"
)

fig = px.line(
    plot_df,
    x="Date",
    y="Normalized Ratio",
    color="Ticker",
    title=f"Top {top_n} SET100 Stocks — Normalized Performance ({time_period})",
    labels={"Normalized Ratio": "Normalized Price Ratio (Start = 1.0)", "Date": ""},
)

fig.add_hline(y=1.0, line_dash="dash", line_color="gray", opacity=0.6)
fig.update_layout(
    height=550,
    hovermode="x unified",
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    margin=dict(l=20, r=20, t=50, b=20),
)
st.plotly_chart(fig, use_container_width=True)

# Ranked Table & CSV Export
st.subheader(f"Top {top_n} Ranking & Performance Matrix")

st.dataframe(
    top_summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Return (%)": st.column_config.NumberColumn(format="%+.2f%%"),
        "Max Drawdown (%)": st.column_config.NumberColumn(format="%.2f%%"),
        "Start Price (THB)": st.column_config.NumberColumn(format="฿%.2f"),
        "Latest Price (THB)": st.column_config.NumberColumn(format="฿%.2f"),
        "Normalized Ratio": st.column_config.NumberColumn(format="%.3f"),
    },
)

csv_data = summary_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Full SET100 Ranking (CSV)",
    data=csv_data,
    file_name=f"set100_ranking_{time_period}.csv",
    mime="text/csv",
)

if missing_tickers:
    st.caption(f"Tickers unavailable on Yahoo Finance and excluded: {', '.join(missing_tickers)}")
