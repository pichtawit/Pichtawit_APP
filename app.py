import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import time

# Page config (16:9 widescreen layout)
st.set_page_config(
    page_title="SET100 & DR Momentum Screener",
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

DR_TICKERS = [
    "AAOI03", "AAOI23", "AAPL01", "AAPL03", "AAPL19", "AAPL80", "ABBV19", "ABBV80", "ABNB06", "ACHR03",
    "ADBE03", "ADBE06", "ADVANT19", "ADVANT23", "ADVANT80", "AEHR03", "AFRM03", "AIA06", "AIA19", "AIA23",
    "AIRBUS80", "AJINO23", "AJINO80", "ALAB01", "ALAB03", "ALAB23", "AMAT01", "AMAT19", "AMAT23", "AMAT80",
    "AMBA03", "AMD03", "AMD23", "AMD80", "AMEC80", "AMGN06", "AMKR03", "AMKR23", "AMPX03", "AMSC03",
    "AMZN01", "AMZN03", "AMZN06", "AMZN19", "AMZN23", "AMZN80", "ANET23", "ANET80", "ANTA13", "ANTA23",
    "APLD03", "APPL03", "ASEMI23", "ASEMI24", "ASICS23", "ASML01", "ASTS01", "ASTS03", "ASTS23", "AVGO23",
    "AVGO80", "AXP06", "BABA01", "BABA06", "BABA11", "BABA13", "BABA19", "BABA23", "BABA80", "BAC03",
    "BDX06", "BE03", "BE80", "BIDU01", "BIDU06", "BIDU23", "BIDU80", "BILIBILI01", "BIREN23", "BKNG03",
    "BKNG80", "BKSY03", "BLK06", "BOEING80", "BONDAS19", "BONDUS01", "BRKB23", "BRKB80", "BYDCOM01", "BYDCOM80",
    "CAMBRI80", "CAT19", "CAT80", "CATL01", "CATL11", "CATL23", "CATL80", "CBRS03", "CBRS80", "CCJ23",
    "CDNS23", "CEG23", "CH30080", "CHAI80", "CHHONGQ19", "CHMOBILE19", "CHMOBILE23", "CHNEXT80", "CHNXT5023", "CHSTAR5080",
    "CIEN03", "CLS03", "CMBANK23", "CME03", "CN01", "CN23", "CNBIO24", "CNEV24", "CNLIFE11", "CNRE80",
    "CNROBOAI23", "CNSEMI23", "CNSTAR5023", "CNTECH01", "COHR23", "COHR80", "COIN01", "COIN23", "COIN80", "COPX03",
    "COSTCO19", "COSTCO80", "CRDO23", "CRDO80", "CRM01", "CRM06", "CRM80", "CRSP03", "CRWD06", "CRWD80",
    "CRWV03", "CRWV23", "CSCO06", "CYPC80", "DASH03", "DBO80", "DBS19", "DDOG19", "DEAM19", "DELL03",
    "DELL19", "DELL23", "DELL80", "DEYE80", "DISCO24", "DISCO80", "DISNEY19", "DOLLARG80", "DUOL06", "E1VFVN3001",
    "ECHO03", "ELMT03", "EOSE03", "EOSE23", "ESTEE80", "ETN03", "ETN23", "EXPE06", "FABRINET03", "FABRINET23",
    "FABRINET80", "FANUC23", "FCX23", "FERRARI80", "FPTVN11", "FPTVN19", "FSLR03", "FTNT03", "FUEVFVND01", "FWONK06",
    "GAC03", "GANFENG23", "GANFENG80", "GASVN11", "GDS23", "GE03", "GEELY06", "GEELY80", "GEV23", "GEV80",
    "GFS03", "GIGA23", "GIGA80", "GLW80", "GOLD03", "GOLD19", "GOLDM01", "GOLDM23", "GOLDUS03", "GOLDUS19",
    "GOLDUS80", "GOOG06", "GOOG23", "GOOG80", "GOOGL01", "GOOGL03", "GOOGL19", "GRAB80", "GSEMI24", "GSUS06",
    "HAIERS19", "HANSOH19", "HERMES80", "HIMS03", "HITACHI24", "HK01", "HK13", "HKCE01", "HKEX23", "HKTECH13",
    "HONDA19", "HOOD03", "HOOD06", "HOOD80", "HORIZON23", "HPE03", "HPE80", "HPG19", "HSBC11", "HSHD23",
    "HUAHONG23", "HUAHONG80", "HXL03", "HYGON80", "IBIDEN23", "IBIDEN80", "IBM03", "IBM06", "IBM23", "ICBC06",
    "ICBC19", "IFLYTEK80", "INDIA01", "INDIAESG19", "INFQ03", "INTEL01", "INTEL03", "INTEL19", "INTEL23", "INTEL80",
    "IONQ03", "IONQ23", "IQQ23", "ISRG01", "ISRG06", "ISRG19", "ISRG80", "ITOCHU19", "IVV23", "JAP03",
    "JAPAN10001", "JAPAN13", "JCI03", "JD80", "JDHEAL19", "JEPI19", "JGRO19", "JLMAG80", "JNJ03", "JOBY03",
    "JPANIME24", "JPMUS06", "JPMUS19", "JPROBOAI24", "JPSEMI24", "JTEK19", "KEYENCE23", "KINGSOFT23", "KIOXIA23", "KIOXIA80",
    "KLAC01", "KLAC03", "KLAC19", "KLAC23", "KO80", "KONAMI24", "KOREA01", "KUAISH01", "KUAISH06", "KUAISH11",
    "KUAISH23", "KUAISH80", "LENOVO13", "LEU03", "LITE01", "LITE03", "LITE23", "LITE80", "LLY23", "LLY80",
    "LOREAL80", "LPGOLD13", "LRCX01", "LRCX19", "LRCX23", "LRCX80", "LULU06", "LUXSHARE80", "LVMH01", "MA80",
    "MAOGEP80", "MEITUAN19", "MEITUAN23", "MEITUAN80", "MELI06", "MELI23", "META01", "META06", "META23", "META80",
    "MICRON01", "MICRON03", "MICRON19", "MICRON23", "MICRON80", "MIDEA80", "MITSU19", "MIXUE80", "MKSI03", "MNSO80",
    "MNST06", "MONTAGE80", "MOUTAI80", "MP23", "MP80", "MPWR23", "MRAM03", "MRK03", "MRVL03", "MRVL06",
    "MRVL23", "MRVL80", "MS06", "MSFT01", "MSFT03", "MSFT06", "MSFT19", "MSFT23", "MSFT80", "MSN11",
    "MSN19", "MTRN03", "MUFG19", "MUFG23", "MURATA23", "MWG11", "MWG19", "NAURA23", "NAURA80", "NBIS01",
    "NBIS03", "NBIS23", "NBIS80", "NDAQ06", "NDX01", "NEE80", "NEM06", "NEM23", "NET03", "NETEASE11",
    "NETEASE80", "NFLX06", "NFLX80", "NIKE80", "NIKKEI80", "NINTENDO19", "NINTENDO23", "NONGFU80", "NOVOB80", "NOW03",
    "NOW19", "NOW23", "NVDA01", "NVDA03", "NVDA06", "NVDA19", "NVDA23", "NVDA80", "NVTS03", "NVTS23",
    "OIL03", "OIL24", "OILUS03", "OKLO03", "OKLO23", "ON23", "ONDS03", "ONON03", "ORCL01", "ORCL06",
    "ORCL19", "ORCL23", "ORCL80", "OUST03", "OXY03", "PANW19", "PANW80", "PEP80", "PETROCN80", "PFIZER19",
    "PINGAN01", "PINGAN11", "PINGAN80", "PLAB03", "PLTR01", "PLTR03", "PLTR06", "PLTR23", "PLTR80", "PNG80",
    "POPMART11", "POPMART23", "POPMART80", "PWR03", "PWR80", "PYPL06", "QBTS03", "QCOM03", "QCOM06", "QCOM23",
    "QCOM80", "QNT03", "QQQM19", "RBLX06", "REMX03", "RGTI03", "RGTI23", "RKLB01", "RKLB03", "RKLB23",
    "RKLB80", "SANOFI80", "SANRIO23", "SANRIO80", "SBUX80", "SCHDER80", "SCREEN23", "SEAGATE23", "SEAGATE80", "SEMB19",
    "SENSE23", "SGX19", "SHINCHEM19", "SHINCHEM80", "SHOP03", "SHOP06", "SIA19", "SIL03", "SINGTEL80", "SINOBIO19",
    "SMCI03", "SMFG19", "SMIC01", "SMIC03", "SMIC13", "SMIC23", "SMR03", "SMR23", "SNDK03", "SNDK23",
    "SNDK80", "SNOW06", "SNOW23", "SOFI23", "SOFTBANK23", "SOFTBANK80", "SONY80", "SOXX23", "SP50001", "SP500US19",
    "SP500US80", "SPACEX01", "SPACEX03", "SPACEX06", "SPACEX23", "SPACEX80", "SPBOND80", "SPCOM80", "SPENGY80", "SPFIN80",
    "SPHLTH80", "SPOT06", "SPTECH80", "STAR5001", "STEG19", "STM03", "SUNGROW80", "SUNNY19", "SUNNY80", "SUSHI23",
    "SYM03", "SYM23", "SYNP03", "SYNP23", "TAIWAN19", "TAIWANAI13", "TAIWANHD13", "TEL23", "TEL80", "TENCENT01",
    "TENCENT06", "TENCENT11", "TENCENT13", "TENCENT19", "TENCENT23", "TENCENT80", "TER01", "TER23", "TER80", "THAIBEV19",
    "TME23", "TONGFU23", "TOYOTA80", "TRIPCOM23", "TRIPCOM80", "TRVUS06", "TSEMI03", "TSEMI23", "TSEMI80", "TSLA01",
    "TSLA03", "TSLA23", "TSLA80", "TTMI80", "TXN03", "UBER06", "UBTECH11", "UBTECH23", "UNH19", "UNIQLO80",
    "UOB19", "URA03", "USAR03", "USTR24", "V3011", "VCB11", "VCB19", "VDIAMOND11", "VENTURE19", "VGT80",
    "VHM19", "VICR80", "VISA06", "VISA80", "VISHAY03", "VNFIN24", "VNM19", "VRT01", "VRT03", "VRT23",
    "VRT80", "VST03", "VT03", "WDC03", "WMT06", "WMT80", "WORLD03", "WORLDA01", "WUXI06", "WUXI11",
    "WUXI13", "WUXIAT80", "XIAOMI01", "XIAOMI11", "XIAOMI13", "XIAOMI19", "XIAOMI23", "XIAOMI80", "XPENG03", "YOFC23",
    "ZAI23", "ZIJIN13", "ZIJIN23", "ZIJIN80", "ZJINNO80", "ZS03"
]

MONTH_NAMES_TH = {
    1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.",
    5: "พ.ค.", 6: "มิ.ย.", 7: "ก.ค.", 8: "ส.ค.",
    9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค.",
}

ISSUER_MAP = {
    "01": "บัวหลวง (BLS)",
    "03": "พาย (Pi)",
    "06": "เกียรตินาคินภัทร (KKPS)",
    "11": "กสิกรไทย (KS)",
    "13": "เคจีไอ (KGI)",
    "19": "หยวนต้า (Yuanta)",
    "23": "อินโนเวสท์ เอกซ์ (INVX)",
    "24": "ยูโอบี เคย์เฮียน (UOBKH)",
    "80": "กรุงไทย (KTB)",
}


def get_dr_issuer(ticker: str) -> str:
    """Extracts the 2-digit issuer code suffix from a Thai DR ticker."""
    if len(ticker) >= 2 and ticker[-2:] in ISSUER_MAP:
        return ISSUER_MAP[ticker[-2:]]
    return "-"


def _extract_close_df(raw_df: pd.DataFrame, requested_tickers: list[str]) -> pd.DataFrame:
    """Safely extracts Close prices regardless of yfinance single/multi-index column format."""
    if raw_df is None or raw_df.empty:
        return pd.DataFrame()

    if isinstance(raw_df.columns, pd.MultiIndex):
        if "Close" in raw_df.columns.get_level_values(0):
            close_df = raw_df["Close"].copy()
        elif "Close" in raw_df.columns.get_level_values(1):
            close_df = raw_df.xs("Close", axis=1, level=1).copy()
        else:
            return pd.DataFrame()
    else:
        if "Close" in raw_df.columns:
            ticker_name = requested_tickers[0].replace(".BK", "")
            close_df = raw_df[["Close"]].rename(columns={"Close": ticker_name})
        else:
            close_df = raw_df.copy()

    close_df.columns = [str(col).replace(".BK", "") for col in close_df.columns]
    return close_df


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_and_process_universe(
    tickers: tuple[str, ...], period: str, is_dr: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Downloads closing prices in safe batches of 80 tickers to prevent Yahoo Finance timeouts."""
    chunk_size = 80
    close_frames = []

    for i in range(0, len(tickers), chunk_size):
        batch = tickers[i : i + chunk_size]
        yf_batch = [f"{t}.BK" for t in batch]
        try:
            raw_chunk = yf.download(
                yf_batch,
                period=period,
                progress=False,
                threads=True,
                auto_adjust=True,
            )
            chunk_close = _extract_close_df(raw_chunk, yf_batch)
            if not chunk_close.empty:
                close_frames.append(chunk_close)
        except Exception:
            pass
        if len(tickers) > chunk_size:
            time.sleep(0.3)

    if not close_frames:
        return pd.DataFrame(), pd.DataFrame(), list(tickers)

    raw = pd.concat(close_frames, axis=1)
    # Remove duplicate columns if any
    raw = raw.loc[:, ~raw.columns.duplicated()]

    downloaded_cols = set(raw.columns)
    missing_tickers = [t for t in tickers if t not in downloaded_cols or raw[t].dropna().shape[0] < 2]

    # Keep only tickers with at least 2 valid trading days
    valid_cols = [col for col in raw.columns if raw[col].dropna().shape[0] >= 2]
    if not valid_cols:
        return pd.DataFrame(), pd.DataFrame(), missing_tickers

    valid_data = raw[valid_cols].ffill()

    # Normalize each security to 1.0 at its first valid trading day in the period
    normalized_dict = {}
    for col in valid_data.columns:
        non_na = valid_data[col].dropna()
        first_val = float(non_na.iloc[0])
        if first_val > 0:
            normalized_dict[col] = valid_data[col] / first_val

    normalized = pd.DataFrame(normalized_dict, index=valid_data.index)

    # Sort descending by latest normalized ratio
    latest_ratios = normalized.iloc[-1].dropna().sort_values(ascending=False)
    sorted_normalized = normalized[latest_ratios.index]

    summary_rows = []
    for rank, (ticker, ratio) in enumerate(latest_ratios.items(), start=1):
        series = valid_data[ticker].dropna()
        start_price = float(series.iloc[0])
        end_price = float(series.iloc[-1])
        pct_return = (float(ratio) - 1.0) * 100.0
        max_drawdown = float(((series / series.cummax()) - 1.0).min() * 100.0)

        row = {
            "Rank": rank,
            "Ticker": ticker,
        }
        if is_dr:
            row["Issuer (ผู้ออก)"] = get_dr_issuer(ticker)

        row.update({
            "Start Price (THB)": round(start_price, 2),
            "Latest Price (THB)": round(end_price, 2),
            "Return (%)": round(pct_return, 2),
            "Normalized Ratio": round(float(ratio), 4),
            "Max Drawdown (%)": round(max_drawdown, 2),
        })
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    return sorted_normalized, summary_df, missing_tickers


@st.cache_data(ttl=900, show_spinner=False)
def fetch_single_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Downloads OHLCV data for a single ticker and calculates EMA 20 & EMA 50."""
    try:
        df = yf.download(f"{ticker}.BK", period=period, interval=interval, progress=False)
    except Exception:
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if "Close" not in df.columns:
        return pd.DataFrame()

    df = df.dropna(subset=["Close"]).copy()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_security_fundamentals(ticker: str, is_dr: bool = False) -> tuple[dict, pd.DataFrame]:
    """Fetches fundamental ratios and analyzes historical dividend frequency & payout months."""
    try:
        t_obj = yf.Ticker(f"{ticker}.BK")
        info = t_obj.info or {}
    except Exception:
        t_obj = None
        info = {}

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

    wk52_high = info.get("fiftyTwoWeekHigh")
    wk52_low = info.get("fiftyTwoWeekLow")
    avg_vol_10d = info.get("averageDailyVolume10Day") or info.get("averageVolume")

    raw_div_yield = info.get("dividendYield")
    if raw_div_yield is not None:
        div_yield_pct = raw_div_yield if raw_div_yield > 0.5 else raw_div_yield * 100.0
    else:
        div_yield_pct = None

    div_rate = info.get("dividendRate")
    payout_ratio = info.get("payoutRatio")

    div_history_df = pd.DataFrame()
    payouts_per_year_str = "ไม่มีประวัติจ่ายปันผล"
    usual_months_str = "-"
    last_xd_str = "-"

    try:
        divs = t_obj.dividends if t_obj is not None else None
        if divs is not None and not divs.empty:
            divs = divs.sort_index()
            cutoff_year = pd.Timestamp.now().year - 5
            recent_divs = divs[divs.index.year >= cutoff_year]

            if not recent_divs.empty:
                yearly_counts = recent_divs.groupby(recent_divs.index.year).count()
                avg_freq = round(float(yearly_counts.mean()), 1)
                typical_freq = int(yearly_counts.mode().iloc[0])
                payouts_per_year_str = f"{typical_freq} ครั้ง/ปี (เฉลี่ย {avg_freq} ครั้ง)"

                month_counts = Counter(recent_divs.index.month)
                top_months = sorted([m for m, _ in month_counts.most_common(max(typical_freq, 2))])
                usual_months_str = ", ".join(MONTH_NAMES_TH[m] for m in top_months)

                last_xd_date = recent_divs.index[-1]
                last_xd_amount = float(recent_divs.iloc[-1])
                last_xd_str = f"{last_xd_date.strftime('%d %b %Y')} (฿{last_xd_amount:.4f})"

                last_10 = recent_divs.tail(10).iloc[::-1]
                div_history_df = pd.DataFrame({
                    "XD Date": last_10.index.strftime("%Y-%m-%d"),
                    "Month": [MONTH_NAMES_TH[m] for m in last_10.index.month],
                    "Dividend / Unit (THB)": [round(float(v), 4) for v in last_10.values],
                })
    except Exception:
        pass

    metrics = {
        "company_name": long_name,
        "issuer": get_dr_issuer(ticker) if is_dr else "-",
        "sector": sector,
        "market_cap_b": f"฿{market_cap / 1e9:,.2f}B" if market_cap else "-",
        "wk52_range": f"฿{wk52_low:.2f} - ฿{wk52_high:.2f}" if (wk52_low and wk52_high) else "-",
        "avg_vol": f"{int(avg_vol_10d):,} หน่วย" if avg_vol_10d else "-",
        "eps_ttm": f"฿{eps_ttm:.2f}" if eps_ttm is not None else "-",
        "eps_fwd": f"฿{eps_fwd:.2f}" if eps_fwd is not None else "-",
        "pe_ttm": f"{pe_ttm:.2f}x" if pe_ttm is not None else "-",
        "pe_fwd": f"{pe_fwd:.2f}x" if pe_fwd is not None else "-",
        "pbv": f"{pbv:.2f}x" if pbv is not None else "-",
        "roe": f"{roe * 100:.2f}%" if roe is not None else "-",
        "roa": f"{roa * 100:.2f}%" if roa is not None else "-",
        "de_ratio": f"{de_ratio / 100:.2f}x" if de_ratio is not None else "-",
        "div_yield": f"{div_yield_pct:.2f}%" if div_yield_pct is not None else "-",
        "div_rate": f"฿{div_rate:.4f}" if div_rate is not None else "-",
        "payout_ratio": f"{payout_ratio * 100:.1f}%" if payout_ratio is not None else "-",
        "payouts_per_year": payouts_per_year_str,
        "usual_months": usual_months_str,
        "last_xd": last_xd_str,
    }
    return metrics, div_history_df


def render_screener_dashboard(
    title: str,
    tickers: list[str],
    is_dr: bool = False,
    key_prefix: str = "set100",
):
    """Shared dashboard renderer for both SET100 and DR tabs."""
    ctrl_top1, ctrl_top2, ctrl_top3, ctrl_top4 = st.columns([2, 2, 3, 1.5])

    with ctrl_top1:
        time_period = st.selectbox(
            "Screener Lookback Period",
            options=["1mo", "3mo", "6mo", "1y", "2y", "ytd"],
            index=2,  # Default: 6mo
            key=f"{key_prefix}_period",
        )
    with ctrl_top2:
        top_n = st.slider(
            "Number of Top Performers",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            key=f"{key_prefix}_top_n",
        )
    with ctrl_top3:
        if is_dr:
            search_filter = st.text_input(
                "Filter DR Symbol (เช่น NVDA, AAPL, BABA)",
                value="",
                key=f"{key_prefix}_filter",
            ).strip().upper()
        else:
            search_filter = st.text_input(
                "Filter SET100 Symbol (เช่น DELTA, KBANK)",
                value="",
                key=f"{key_prefix}_filter",
            ).strip().upper()
    with ctrl_top4:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Data", use_container_width=True, key=f"{key_prefix}_refresh"):
            st.cache_data.clear()
            st.rerun()

    st.subheader(title)

    with st.spinner(f"กำลังโหลดข้อมูล {len(tickers)} หลักทรัพย์ ({time_period}) จาก Yahoo Finance..."):
        sorted_normalized, summary_df, missing_tickers = fetch_and_process_universe(
            tuple(tickers), time_period, is_dr=is_dr
        )

    if summary_df.empty:
        st.error("ไม่สามารถดึงข้อมูลจาก Yahoo Finance ได้ในขณะนี้ กรุณารอสักครู่แล้วกด Refresh Data")
        return

    if search_filter:
        filtered_summary = summary_df[summary_df["Ticker"].str.contains(search_filter, na=False)].copy()
        if filtered_summary.empty:
            st.warning(f"ไม่พบชื่อย่อที่มีคำว่า '{search_filter}'")
            return
        display_summary = filtered_summary.head(top_n)
        display_tickers = display_summary["Ticker"].tolist()
        display_normalized = sorted_normalized[display_tickers]
    else:
        display_summary = summary_df.head(top_n)
        display_normalized = sorted_normalized.iloc[:, :top_n]

    # Top KPI Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    leader = display_summary.iloc[0]
    nth_stock = display_summary.iloc[-1]
    avg_top_return = display_summary["Return (%)"].mean()
    median_universe_return = summary_df["Return (%)"].median()

    col1.metric("#1 Performer", f"{leader['Ticker']}", f"{leader['Return (%)']:+.2f}%")
    col2.metric(f"#{len(display_summary)} Cutoff", f"{nth_stock['Ticker']}", f"{nth_stock['Return (%)']:+.2f}%")
    col3.metric("Displayed Avg Return", f"{avg_top_return:+.2f}%")
    col4.metric(
        f"All {'DR' if is_dr else 'SET100'} Median ({len(summary_df)} active)",
        f"{median_universe_return:+.2f}%",
    )

    # Interactive Plotly Line Chart (Normalized)
    plot_df = display_normalized.reset_index()
    date_col_name = plot_df.columns[0]
    plot_melted = plot_df.melt(
        id_vars=date_col_name, var_name="Ticker", value_name="Normalized Ratio"
    )

    fig = px.line(
        plot_melted,
        x=date_col_name,
        y="Normalized Ratio",
        color="Ticker",
        title=f"Top {len(display_summary)} {'DR' if is_dr else 'SET100'} — Normalized Performance ({time_period})",
        labels={"Normalized Ratio": "Normalized Price Ratio (Start = 1.0)", date_col_name: ""},
    )

    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", opacity=0.6)
    fig.update_layout(
        height=480,
        hovermode="x unified",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Interactive Ranked Table
    st.markdown(f"#### Top {len(display_summary)} Ranking (คลิกเลือกแถวในตารางเพื่อดูกราฟและข้อมูลรายตัว)")

    table_event = st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"{key_prefix}_table",
        column_config={
            "Return (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            "Max Drawdown (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Start Price (THB)": st.column_config.NumberColumn(format="฿%.2f"),
            "Latest Price (THB)": st.column_config.NumberColumn(format="฿%.2f"),
            "Normalized Ratio": st.column_config.NumberColumn(format="%.3f"),
        },
    )

    selected_rows = []
    try:
        if table_event and hasattr(table_event, "selection") and table_event.selection:
            selected_rows = table_event.selection.rows
    except Exception:
        selected_rows = []

    available_tickers = summary_df["Ticker"].tolist()

    if selected_rows and selected_rows[0] < len(display_summary):
        default_ticker = display_summary.iloc[selected_rows[0]]["Ticker"]
    else:
        default_ticker = leader["Ticker"]

    st.divider()

    # --- Single-Security Deep-Dive Section ---
    st.markdown(f"#### 🔍 Individual {'DR' if is_dr else 'Stock'} Chart, Fundamentals & Dividend Profile")

    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 2, 2, 2])

    with ctrl_col1:
        selected_ticker = st.selectbox(
            "Select Ticker (หรือคลิกจากตารางด้านบน)",
            options=available_tickers,
            index=available_tickers.index(default_ticker),
            key=f"{key_prefix}_single_ticker",
        )

    with ctrl_col2:
        stock_period = st.selectbox(
            "Chart Timeframe",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"],
            index=3,  # Default: 1y
            key=f"{key_prefix}_single_period",
        )

    with ctrl_col3:
        stock_interval = st.selectbox(
            "Candle Interval",
            options=["1d", "1wk"],
            index=0,
            key=f"{key_prefix}_single_interval",
        )

    with ctrl_col4:
        chart_type = st.selectbox(
            "Chart Style",
            options=["Candlestick", "Line"],
            index=0,
            key=f"{key_prefix}_single_style",
        )

    with st.spinner(f"Loading {selected_ticker}.BK chart & fundamentals..."):
        stock_df = fetch_single_ohlcv(selected_ticker, stock_period, stock_interval)
        fund_metrics, div_history_df = fetch_security_fundamentals(selected_ticker, is_dr=is_dr)

    if is_dr:
        st.markdown(
            f"**{fund_metrics['company_name']}** (`{selected_ticker}.BK`) &nbsp;|&nbsp; "
            f"ผู้ออก DR: **{fund_metrics['issuer']}** &nbsp;|&nbsp; 52W Range: `{fund_metrics['wk52_range']}`"
        )
    else:
        st.markdown(
            f"**{fund_metrics['company_name']}** (`{selected_ticker}.BK`) &nbsp;|&nbsp; "
            f"Sector: `{fund_metrics['sector']}` &nbsp;|&nbsp; Market Cap: `{fund_metrics['market_cap_b']}`"
        )

    # Fundamental & Dividend Tables
    fund_col1, fund_col2 = st.columns([3, 2])

    with fund_col1:
        st.markdown("##### 📊 ข้อมูลพื้นฐานและปันผลสำคัญ (Key Metrics & Distribution)")
        if is_dr:
            rows = [
                {"Metric": "ผู้ออกตราสาร (DR Issuer)", "Value": fund_metrics["issuer"]},
                {"Metric": "ช่วงราคา 52 สัปดาห์ (52W High/Low)", "Value": fund_metrics["wk52_range"]},
                {"Metric": "ปริมาณซื้อขายเฉลี่ย 10 วัน", "Value": fund_metrics["avg_vol"]},
                {"Metric": "EPS / P/E (หากมีข้อมูลบนกระดาน)", "Value": f"{fund_metrics['eps_ttm']}  /  {fund_metrics['pe_ttm']}"},
                {"Metric": "Dividend / Distribution Yield", "Value": f"{fund_metrics['div_yield']} ({fund_metrics['div_rate']}/หน่วย)"},
                {"Metric": "ความถี่การจ่ายปันผลต่อปี (ย้อนหลัง 5 ปี)", "Value": fund_metrics["payouts_per_year"]},
                {"Metric": "เดือนที่มักขึ้นเครื่องหมาย XD", "Value": fund_metrics["usual_months"]},
                {"Metric": "วัน XD ล่าสุด", "Value": fund_metrics["last_xd"]},
            ]
        else:
            rows = [
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
            ]

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with fund_col2:
        st.markdown("##### 💰 ประวัติการจ่ายปันผลล่าสุด (Recent XD History)")
        if not div_history_df.empty:
            st.dataframe(
                div_history_df,
                use_container_width=True,
                hide_index=True,
                height=340 if is_dr else 388,
                column_config={
                    "Dividend / Unit (THB)": st.column_config.NumberColumn(format="฿%.4f"),
                },
            )
        else:
            st.info(f"ไม่พบประวัติการจ่ายเงินปันผลของ {selected_ticker} ในช่วง 5 ปีที่ผ่านมา")

    # Candlestick / Line Chart
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
        label=f"Download Full {'DR' if is_dr else 'SET100'} Ranking (CSV)",
        data=csv_data,
        file_name=f"{key_prefix}_ranking_{time_period}.csv",
        mime="text/csv",
        key=f"{key_prefix}_download",
    )

    if missing_tickers:
        with st.expander(f"Tickers unavailable on Yahoo Finance ({len(missing_tickers)} tickers)"):
            st.caption(", ".join(missing_tickers))


# --- Main Header & Top Tabs ---
st.title("📈 Thai Market Momentum Screener (SET100 & DR)")

tab_set100, tab_dr = st.tabs(["🇹🇭 SET100 Screener", "🌐 DR Screener (386 Tickers)"])

with tab_set100:
    render_screener_dashboard(
        title="Top SET100 Performers (Normalized to 1.0)",
        tickers=SET100_TICKERS,
        is_dr=False,
        key_prefix="set100",
    )

with tab_dr:
    render_screener_dashboard(
        title="Top Thai DR Performers (Normalized to 1.0)",
        tickers=DR_TICKERS,
        is_dr=True,
        key_prefix="dr",
    )
