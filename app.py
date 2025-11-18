import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os
import base64
from datetime import datetime

# --------------------------
# Page config
# --------------------------
st.set_page_config(page_title="🌿 ECO STEP - 최종 보고서", layout="wide", page_icon="🌱")
DATA_DIR = "output"

# --------------------------
# Load helpers
# --------------------------
def load_kpi(path=os.path.join(DATA_DIR, "kpi.json")):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_csv(name):
    return pd.read_csv(os.path.join(DATA_DIR, name))

def fmt(n):
    if n is None:
        return "N/A"
    if isinstance(n, float):
        return f"{n:,.2f}"
    if isinstance(n, int):
        return f"{n:,d}"
    return str(n)

# --------------------------
# CSS: Deep green theme + buttons + KPI glass + filter text fix
# --------------------------
st.markdown("""
<style>

html, body, .appview-container, .main {
    background-color: #154a39 !important;
    color: #ffffff !important;
    font-family: 'Segoe UI', 'Nanum Gothic', sans-serif;
}

/* headings */
h1,h2,h3,h4 { color: #ffffff !important; }

/* ---- KPI GLASS CARD ---- */
.kpi-card {
    background: rgba(255,255,255,0.10) !important;
    backdrop-filter: blur(14px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(14px) saturate(140%) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.32) !important;
    transition: transform .18s ease, box-shadow .18s ease !important;
}
.kpi-card:hover {
    transform: translateY(-4px) scale(1.03);
    box-shadow: 0 14px 38px rgba(0,0,0,0.45) !important;
}
.kpi-title { font-size:13px; opacity: 0.95; }
.kpi-value { font-size:24px; font-weight:700; }

/* Plotly card */
.plotly-card {
    background: #ffffff !important;
    color: #154a39 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 10px 26px rgba(0,0,0,0.25) !important;
}

/* DataFrame white card */
.stDataFrame > div {
    background: rgba(255,255,255,0.98) !important;
    color: #154a39 !important;
    border-radius: 10px !important;
}

/* Summary box */
.summary-box {
    background: rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 18px;
    color: #ffffff;
    line-height: 1.6;
}

/* Fix expander header text */
.streamlit-expanderHeader { color: #ffffff !important; }

/* ------- FILTER LABELS TO WHITE ------- */
.stSelectbox label,
.stMultiSelect label,
.stDateInput label,
.stSlider label {
    color: #ffffff !important;
}

/* Inside select dropdown */
div[data-baseweb="select"] * {
    color: #154a39 !important;
}

/* ------- DOWNLOAD BUTTON ------- */
.custom-download {
    display:inline-block;
    padding: 10px 22px;
    margin-bottom: 16px;
    background: #ffffff;
    color: #154a39;
    font-weight: 700;
    border-radius: 12px;
    text-decoration: none;
    border: 2px solid rgba(255,255,255,0.35);
    box-shadow: 0 10px 26px rgba(0,0,0,0.25);
    transition: all .18s ease;
}
.custom-download:hover {
    background: #f4f4f4;
    transform: translateY(-3px);
}

/* Disabled small placeholder */
.small-disabled {
    display:inline-block;
    padding: 10px 18px;
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.6);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
}

</style>
""", unsafe_allow_html=True)

# --------------------------
# Load data
# --------------------------
missing = []
try:
    kpi = load_kpi()
except Exception:
    kpi = {}
    missing.append("kpi.json")

for fn in ("daily_events.csv", "screen_counts.csv", "merged_events.csv"):
    if not os.path.exists(os.path.join(DATA_DIR, fn)):
        missing.append(fn)

if missing:
    st.error(f"필요한 파일이 누락되어 있습니다: {', '.join(missing)}. (output/ 폴더 확인)")    

try: df_daily = load_csv("daily_events.csv")
except: df_daily = pd.DataFrame(columns=["date","count"])

try: df_screen = load_csv("screen_counts.csv")
except: df_screen = pd.DataFrame(columns=["screen","count"])

try: df_merged = load_csv("merged_events.csv")
except: df_merged = pd.DataFrame(columns=["event_time","screen","duration","device_id","session_id","date"])

# --------------------------
# HEADER
# --------------------------
st.markdown("<h1 style='text-align:center; margin-bottom:6px;'>🌿 ECO STEP — 사용자 활동 분석 (최종보고서)</h1>", unsafe_allow_html=True)
st.markdown("---")

# --------------------------
# KPI Section
# --------------------------
st.subheader("핵심 지표 (KPI)")
kpi_cols = st.columns(6)

items = [
    ("전체 이벤트 수", fmt(kpi.get("total_events"))),
    ("평균 체류 시간(초)", fmt(kpi.get("average_stay"))),
    ("중앙값 체류 시간(초)", fmt(kpi.get("median_stay"))),
    ("고유 화면 수", fmt(kpi.get("unique_screens"))),
    ("고유 세션 수", fmt(kpi.get("unique_sessions"))),
    ("고유 디바이스 수", fmt(kpi.get("unique_devices"))),
]

for col, (title, value) in zip(kpi_cols, items):
    col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --------------------------
# CHARTS Section
# --------------------------
left, right = st.columns((2,1))

with left:
    st.subheader("일자별 이벤트 발생 수")
    if "date" in df_daily.columns:
        df_daily["date"] = pd.to_datetime(df_daily["date"]).dt.date
        df_daily = df_daily.sort_values("date")

    fig_daily = px.bar(df_daily, x="date", y="count")
    fig_daily.update_traces(marker_color="#27ae60")
    fig_daily.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="#154a39")

    st.markdown("<div class='plotly-card'>", unsafe_allow_html=True)
    st.plotly_chart(fig_daily, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("상위 방문 화면 (TOP)")
    top_n = st.slider("표시 개수", 3, min(10, max(6, len(df_screen))), 6)
    df_top = df_screen.head(top_n)

    fig_top = px.bar(df_top, x="count", y="screen", orientation="h", text="count")
    fig_top.update_traces(marker_color="#27ae60")
    fig_top.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color="#154a39",
        yaxis={'categoryorder':'total ascending'}
    )

    st.markdown("<div class='plotly-card'>", unsafe_allow_html=True)
    st.plotly_chart(fig_top, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.subheader("단과대 비율")

    colleges = {
        "미래산업융합대학": 35.9,
        "사회과학대학": 26.6,
        "과학기술융합대학": 23.4,
        "인문대학": 10.9,
        "아트앤디자인스쿨": 3.1
    }

    col_df = pd.DataFrame({"college": colleges.keys(), "rate": colleges.values()})

    pastel_blue = ["#A7C7E7", "#B5D9FF", "#89CFF0", "#6EC6FF", "#C2E7FF"]

    fig_donut = px.pie(
        col_df,
        names="college",
        values="rate",
        hole=0.45,
        color_discrete_sequence=pastel_blue
    )
    fig_donut.update_layout(paper_bgcolor="white", font_color="#154a39")

    st.markdown("<div class='plotly-card'>", unsafe_allow_html=True)
    st.plotly_chart(fig_donut, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# --------------------------
# Summary
# --------------------------
st.subheader("요약 해석")

if not df_screen.empty:
    top_screen_name = df_screen.iloc[0]["screen"]
    top_screen_cnt = int(df_screen.iloc[0]["count"])
else:
    top_screen_name = "자료 없음"
    top_screen_cnt = 0

long_summary = f"""
이번 분석 기간 동안 총 {kpi.get('total_events',0):,}건의 이벤트가 발생했습니다.<br><br>
사용자는 평균 {kpi.get('average_stay','N/A')}초,  
중앙값 {kpi.get('median_stay','N/A')}초 동안 앱에 체류했습니다.<br><br>
가장 많이 방문된 화면은 '{top_screen_name}' (총 {top_screen_cnt:,}회) 입니다.<br><br>
11월 초(11/3~11/5)에 이벤트 발생량이 크게 증가하여  
사용자 활동이 가장 활발했던 시기로 나타났습니다.<br><br>
향후 스크린 이동 경로 분석, 사용자군별 행동 패턴 분석 등을 추가하면  
더 깊은 인사이트 확보가 가능합니다.
"""

with st.expander("통계 지표 해석 보기"):
    st.markdown(f"<div class='summary-box'>{long_summary}</div>", unsafe_allow_html=True)

st.markdown("---")

# --------------------------
# RAW DATA + FILTERS
# --------------------------
st.subheader("원시 이벤트 탐색")
col1, col2, col3 = st.columns([1.6, 1, 1])

if "date" in df_merged.columns:
    date_min = pd.to_datetime(df_merged["date"]).min().date()
    date_max = pd.to_datetime(df_merged["date"]).max().date()
else:
    date_min = datetime.today().date()
    date_max = datetime.today().date()

sel_start, sel_end = col1.date_input("기간 선택", [date_min, date_max])
sel_screen = col2.multiselect("화면 필터", df_merged["screen"].dropna().unique())
sel_device = col3.multiselect("디바이스 필터", df_merged["device_id"].dropna().unique())

df_view = df_merged.copy()
df_view["date"] = pd.to_datetime(df_view["date"]).dt.date
df_view = df_view[(df_view["date"] >= sel_start) & (df_view["date"] <= sel_end)]

if sel_screen:
    df_view = df_view[df_view["screen"].isin(sel_screen)]
if sel_device:
    df_view = df_view[df_view["device_id"].isin(sel_device)]

st.dataframe(df_view, use_container_width=True, height=320)

# --------------------------
# CSV DOWNLOAD BUTTON
# --------------------------
csv_bytes = df_view.to_csv(index=False).encode("utf-8")
csv_b64 = base64.b64encode(csv_bytes).decode()

st.markdown(
    f'<a class="custom-download" href="data:text/csv;base64,{csv_b64}" download="filtered_events.csv">CSV 다운로드 (필터 결과)</a>',
    unsafe_allow_html=True
)

# --------------------------
# PDF DOWNLOAD BUTTON
# --------------------------
pdf_static_path = os.path.join(DATA_DIR, "eco_step_report.pdf")
if os.path.exists(pdf_static_path):
    with open(pdf_static_path, "rb") as f:
        pdf_bytes = f.read()
    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    st.markdown(
        f'<a class="custom-download" href="data:application/pdf;base64,{pdf_b64}" download="eco_step_report.pdf">PDF 보고서 다운로드</a>',
        unsafe_allow_html=True
    )
else:
    st.markdown('<span class="small-disabled">PDF 파일 없음 (output/eco_step_report.pdf)</span>', unsafe_allow_html=True)

st.markdown("---")
st.caption("© EarthSWU 2025")
