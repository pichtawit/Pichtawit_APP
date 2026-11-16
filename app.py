import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter

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

MONTH_NAMES_TH = {
    1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.",
    5: "พ.ค.", 6: "มิ.ย.", 7: "ก.ค.", 8: "ส.ค.",
    9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค.",
}


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_and_process_data(period: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Downloads SET100 data from Yahoo Finance, normalizes to 1.0, and computes returns."""
    yf_tickers = [f"{ticker}.BK" for ticker in SET100_TICKERS]
    raw = yf.download(yf_tickers, period=period, progress=False)["Close"]

    raw.columns = [col.replace(".BK", "") for col in raw.columns]
    missing_tickers = [col for col in raw.columns if raw[col].isna().all()]
    valid_data = raw.dropna(axis=1, how="all").ffill()

    normalized = valid_data.apply(lambda col: col / col.dropna().iloc[0])
    latest_ratios = normalized.iloc[-1].sort_values(ascending=False)
    sorted_normalized = normalized[latest_ratios.index]

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


@st.cache_data(ttl=900, show_spinner=False)
def fetch_single_stock_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Downloads OHLCV data for a single SET stock and calculates EMA 20 & EMA 50."""
    df = yf.download(f"{ticker}.BK", period=period, interval=interval, progress=False)
    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna(subset=["Close"]).copy()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_fundamentals(ticker: str) -> tuple[dict, pd.DataFrame]:
    """Fetches fundamental ratios and analyzes historical dividend frequency & payout months."""
    t_obj = yf.Ticker(f"{ticker}.BK")
    info = t_obj.info or {}

    # Valuation & Earnings metrics
    eps_ttm = info.get("trailingEps")
    eps_fwd = info.get("forwardEps")
    pe_ttm = info.get("trailingPE")
    pe_fwd = info.get("forwardPE")
    pbv = info.get("priceToBook")
    roe = info.get("returnOnEquity")
    roa = info.get("returnOnAssets")
    de_ratio = info.get("debtToEquity")
    market_cap = info.get("marketCap")
    sector = info.get("sector", "-")
    long_name = info.get("longName") or info.get("shortName") or ticker

    # Dividend Yield (Yahoo Finance returns decimal e.g. 0.052 or percentage depending on field)
    raw_div_yield = info.get("dividendYield")
    if raw_div_yield is not None:
        # Handle yfinance inconsistency: dividendYield is sometimes 5.2 (already %) or 0.052 (decimal)
        div_yield_pct = raw_div_yield if raw_div_yield > 0.5 else raw_div_yield * 100.0
    else:
        div_yield_pct = None

    div_rate = info.get("dividendRate")
    payout_ratio = info.get("payoutRatio")

    # Analyze historical dividends (last 5 years)
    divs = t_obj.dividends
    div_history_df = pd.DataFrame()
    payouts_per_year_str = "ไม่มีประวัติปันผล"
    usual_months_str = "-"
    last_xd_str = "-"

    if divs is not None and not divs.empty:
        divs = divs.sort_index()
        # Filter last 5 calendar years
        cutoff_year = pd.Timestamp.now().year - 5
        recent_divs = divs[divs.index.year >= cutoff_year]

        if not recent_divs.empty:
            # Count payouts per year (excluding current incomplete year if needed, or showing avg)
            yearly_counts = recent_divs.groupby(recent_divs.index.year).count()
            # Mode or rounded average of payouts per year
            avg_freq = round(yearly_counts.mean(), 1)
            typical_freq = int(yearly_counts.mode().iloc[0])
            payouts_per_year_str = f"{typical_freq} ครั้ง/ปี (เฉลี่ย {avg_freq} ครั้ง)"

            # Find most frequent XD months
            month_counts = Counter(recent_divs.index.month)
            top_months = sorted([m for m, _ in month_counts.most_common(max(typical_freq, 2))])
            usual_months_str = ", ".join(MONTH_NAMES_TH[m] for m in top_months)

            last_xd_date = recent_divs.index[-1]
            last_xd_amount = recent_divs.iloc[-1]
            last_xd_str = f"{last_xd_date.strftime('%d %b %Y')} (฿{last_xd_amount:.2f})"

            # Build recent dividend table (last 10 payouts)
            last_10 = recent_divs.tail(10).iloc[::-1]
            div_history_df = pd.DataFrame({
                "XD Date": last_10.index.strftime("%Y-%m-%d"),
                "Month": [MONTH_NAMES_TH[m] for m in last_10.index.month],
                "Dividend / Share (THB)": [round(float(v), 4) for v in last_10.values],
            })

    metrics = {
        "company_name": long_name,
        "sector": sector,
        "market_cap_b": f"฿{market_cap / 1e9:,.2f}B" if market_cap else "-",
        "eps_ttm": f"฿{eps_ttm:.2f}" if eps_ttm is not None else "-",
        "eps_fwd": f"฿{eps_fwd:.2f}" if eps_fwd is not None else "-",
        "pe_ttm": f"{pe_ttm:.2f}x" if pe_ttm is not None else "-",
        "pe_fwd": f"{pe_fwd:.2f}x" if pe_fwd is not None else "-",
        "pbv": f"{pbv:.2f}x" if pbv is not None else "-",
        "roe": f"{roe * 100:.2f}%" if roe is not None else "-",
        "roa": f"{roa * 100:.2f}%" if roa is not None else "-",
        "de_ratio": f"{de_ratio / 100:.2f}x" if de_ratio is not None else "-",
        "div_yield": f"{div_yield_pct:.2f}%" if div_yield_pct is not None else "-",
        "div_rate": f"฿{div_rate:.2f}" if div_rate is not None else "-",
        "payout_ratio": f"{payout_ratio * 100:.1f}%" if payout_ratio is not None else "-",
        "payouts_per_year": payouts_per_year_str,
        "usual_months": usual_months_str,
        "last_xd": last_xd_str,
    }
    return metrics, div_history_df


# --- Sidebar Controls ---
st.sidebar.header("Screener Parameters")
time_period = st.sidebar.selectbox(
    "Screener Lookback Period",
    options=["1mo", "3mo", "6mo", "1y", "2y", "ytd"],
    index=2,  # Default: 6mo
)
top_n = st.sidebar.slider("Number of Top Stocks", min_value=5, max_value=50, value=20, step=5)

if st.sidebar.button("Refresh Market Data", use_container_width=True):
    st.cache_data.clear()

# --- Main App ---
st.title("📈 Top SET100 Performers")

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

# Interactive Plotly Line Chart (Top N Normalized)
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
    height=480,
    hovermode="x unified",
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    margin=dict(l=20, r=20, t=50, b=20),
)
st.plotly_chart(fig, use_container_width=True)

# --- Interactive Ranked Table ---
st.subheader(f"Top {top_n} Ranking (คลิกเลือกแถวในตารางเพื่อดูกราฟและข้อมูลพื้นฐานรายตัว)")

table_event = st.dataframe(
    top_summary,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Return (%)": st.column_config.NumberColumn(format="%+.2f%%"),
        "Max Drawdown (%)": st.column_config.NumberColumn(format="%.2f%%"),
        "Start Price (THB)": st.column_config.NumberColumn(format="฿%.2f"),
        "Latest Price (THB)": st.column_config.NumberColumn(format="฿%.2f"),
        "Normalized Ratio": st.column_config.NumberColumn(format="%.3f"),
    },
)

selected_rows = table_event.selection.rows if table_event and table_event.selection else []
available_tickers = summary_df["Ticker"].tolist()

if selected_rows:
    default_ticker = top_summary.iloc[selected_rows[0]]["Ticker"]
else:
    default_ticker = leader["Ticker"]

st.divider()

# --- Single-Stock Deep-Dive Section ---
st.subheader("🔍 Individual Stock Chart, Fundamentals & Dividend Profile")

ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 2, 2, 2])

with ctrl_col1:
    selected_ticker = st.selectbox(
        "Select Ticker (หรือคลิกจากตารางด้านบน)",
        options=available_tickers,
        index=available_tickers.index(default_ticker),
    )

with ctrl_col2:
    stock_period = st.selectbox(
        "Chart Timeframe",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"],
        index=3,  # Default: 1y
    )

with ctrl_col3:
    stock_interval = st.selectbox(
        "Candle Interval",
        options=["1d", "1wk"],
        index=0,
    )

with ctrl_col4:
    chart_type = st.selectbox(
        "Chart Style",
        options=["Candlestick", "Line"],
        index=0,
    )

with st.spinner(f"Loading {selected_ticker}.BK chart & fundamentals..."):
    stock_df = fetch_single_stock_ohlcv(selected_ticker, stock_period, stock_interval)
    fund_metrics, div_history_df = fetch_stock_fundamentals(selected_ticker)

st.markdown(
    f"**{fund_metrics['company_name']}** (`{selected_ticker}.BK`) &nbsp;|&nbsp; "
    f"Sector: `{fund_metrics['sector']}` &nbsp;|&nbsp; Market Cap: `{fund_metrics['market_cap_b']}`"
)

# --- Fundamental & Dividend Summary Table ---
fund_col1, fund_col2 = st.columns([3, 2])

with fund_col1:
    st.markdown("##### 📊 ข้อมูลพื้นฐานและปันผลสำคัญ (Key Valuation & Dividend Metrics)")
    fundamental_table = pd.DataFrame([
        {"Metric": "EPS (TTM / Forward)", "Value": f"{fund_metrics['eps_ttm']}  /  {fund_metrics['eps_fwd']}"},
        {"Metric": "P/E Ratio (TTM / Forward)", "Value": f"{fund_metrics['pe_ttm']}  /  {fund_metrics['pe_fwd']}"},
        {"Metric": "P/BV Ratio", "Value": fund_metrics["pbv"]},
        {"Metric": "ROE / ROA", "Value": f"{fund_metrics['roe']}  /  {fund_metrics['roa']}"},
        {"Metric": "D/E Ratio", "Value": fund_metrics["de_ratio"]},
        {"Metric": "Dividend Yield (อัตราเงินปันผล)", "Value": f"{fund_metrics['div_yield']} ({fund_metrics['div_rate']}/หุ้น)"},
        {"Metric": "Payout Ratio", "Value": fund_metrics["payout_ratio"]},
        {"Metric": "ความถี่การจ่ายปันผลต่อปี (ย้อนหลัง 5 ปี)", "Value": fund_metrics["payouts_per_year"]},
        {"Metric": "เดือนที่มักขึ้นเครื่องหมาย XD", "Value": fund_metrics["usual_months"]},
        {"Metric": "วัน XD ล่าสุด", "Value": fund_metrics["last_xd"]},
    ])
    st.dataframe(fundamental_table, use_container_width=True, hide_index=True)

with fund_col2:
    st.markdown("##### 💰 ประวัติการจ่ายปันผลล่าสุด (Recent XD History)")
    if not div_history_df.empty:
        st.dataframe(
            div_history_df,
            use_container_width=True,
            hide_index=True,
            height=388,
            column_config={
                "Dividend / Share (THB)": st.column_config.NumberColumn(format="฿%.4f"),
            },
        )
    else:
        st.info(f"ไม่พบประวัติการจ่ายเงินปันผลของ {selected_ticker} ในช่วง 5 ปีที่ผ่านมา")

# --- Technical Candlestick / Line Chart ---
if not stock_df.empty:
    first_close = float(stock_df["Close"].iloc[0])
    last_close = float(stock_df["Close"].iloc[-1])
    period_high = float(stock_df["High"].max())
    period_low = float(stock_df["Low"].min())
    period_chg = ((last_close / first_close) - 1.0) * 100.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{selected_ticker} Latest Close", f"฿{last_close:.2f}", f"{period_chg:+.2f}% ({stock_period})")
    m2.metric(f"{stock_period} High", f"฿{period_high:.2f}")
    m3.metric(f"{stock_period} Low", f"฿{period_low:.2f}")
    m4.metric("Latest Volume", f"{int(stock_df['Volume'].iloc[-1]):,}")

    stock_fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25],
    )

    if chart_type == "Candlestick":
        stock_fig.add_trace(
            go.Candlestick(
                x=stock_df.index,
                open=stock_df["Open"],
                high=stock_df["High"],
                low=stock_df["Low"],
                close=stock_df["Close"],
                name=selected_ticker,
                increasing_line_color="#00C805",
                decreasing_line_color="#FF3B30",
            ),
            row=1,
            col=1,
        )
    else:
        stock_fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df["Close"],
                mode="lines",
                name="Close Price",
                line=dict(color="#2962FF", width=2),
            ),
            row=1,
            col=1,
        )

    stock_fig.add_trace(
        go.Scatter(
            x=stock_df.index,
            y=stock_df["EMA20"],
            mode="lines",
            name="EMA 20",
            line=dict(color="#FF9800", width=1.3),
        ),
        row=1,
        col=1,
    )
    stock_fig.add_trace(
        go.Scatter(
            x=stock_df.index,
            y=stock_df["EMA50"],
            mode="lines",
            name="EMA 50",
            line=dict(color="#9C27B0", width=1.3),
        ),
        row=1,
        col=1,
    )

    vol_colors = [
        "#00C805" if close >= open_ else "#FF3B30"
        for close, open_ in zip(stock_df["Close"], stock_df["Open"])
    ]
    stock_fig.add_trace(
        go.Bar(
            x=stock_df.index,
            y=stock_df["Volume"],
            name="Volume",
            marker_color=vol_colors,
            opacity=0.65,
        ),
        row=2,
        col=1,
    )

    stock_fig.update_layout(
        title=f"{selected_ticker}.BK — Price Action & Volume ({stock_period} | {stock_interval})",
        height=600,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    stock_fig.update_yaxes(title_text="Price (THB)", row=1, col=1)
    stock_fig.update_yaxes(title_text="Volume", row=2, col=1)

    st.plotly_chart(stock_fig, use_container_width=True)
else:
    st.warning(f"No historical price data returned for {selected_ticker}.BK.")

# CSV Export
csv_data = summary_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Full SET100 Ranking (CSV)",
    data=csv_data,
    file_name=f"set100_ranking_{time_period}.csv",
    mime="text/csv",
)

if missing_tickers:
    st.caption(f"Tickers unavailable on Yahoo Finance and excluded: {', '.join(missing_tickers)}")
