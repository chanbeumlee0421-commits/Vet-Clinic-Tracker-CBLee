import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="VET INTEL · 전국 동물병원 개폐업 인텔리전스",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 전역 CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #080c10 !important;
    color: #d8dce8 !important;
}
[data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid #1e2535 !important;
}
[data-testid="stSidebar"] * { color: #d8dce8 !important; }

.hero {
    padding: 48px 0 32px;
    border-bottom: 1px solid #1e2535;
    margin-bottom: 32px;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 3px;
    color: #3d8eff;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.6rem;
    letter-spacing: 2px;
    line-height: 1;
    color: #f0f4ff;
    margin-bottom: 10px;
}
.hero-title span { color: #3d8eff; }
.hero-sub {
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 0.85rem;
    color: #5a6480;
    margin-bottom: 4px;
}
.hero-author {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #3a4260;
    letter-spacing: 1px;
}

.kpi-row { display: flex; gap: 16px; margin-bottom: 32px; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 140px;
    background: #0d1117;
    border: 1px solid #1e2535;
    border-radius: 8px;
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
}
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-card.blue::after  { background: #3d8eff; }
.kpi-card.red::after   { background: #ff4560; }
.kpi-card.gold::after  { background: #f5a623; }
.kpi-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3a4260;
    margin-bottom: 8px;
}
.kpi-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    line-height: 1;
    color: #f0f4ff;
}
.kpi-card.blue  .kpi-value { color: #3d8eff; }
.kpi-card.red   .kpi-value { color: #ff4560; }
.kpi-card.gold  .kpi-value { color: #f5a623; }

.notice-bar {
    background: rgba(245,166,35,0.06);
    border: 1px solid rgba(245,166,35,0.2);
    border-left: 3px solid #f5a623;
    border-radius: 4px;
    padding: 12px 18px;
    font-size: 0.8rem;
    color: #a8854a;
    margin-bottom: 28px;
    font-family: 'Noto Sans KR', sans-serif;
}

[data-testid="stTabs"] button {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: #3a4260 !important;
    padding: 10px 20px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #3d8eff !important;
    border-bottom: 2px solid #3d8eff !important;
}

[data-testid="stButton"] button {
    background: #3d8eff !important;
    color: #080c10 !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
    padding: 10px 0 !important;
}
[data-testid="stButton"] button:hover { background: #5ea6ff !important; }

[data-testid="stDateInput"] input {
    background: #0d1117 !important;
    border: 1px solid #1e2535 !important;
    color: #d8dce8 !important;
    border-radius: 4px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
}

[data-testid="stExpander"] {
    background: #0d1117 !important;
    border: 1px solid #1e2535 !important;
    border-radius: 6px !important;
    margin-bottom: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    color: #d8dce8 !important;
}

.footer {
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid #1e2535;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #2a3050;
    letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)


# ── 담당자별 담당 지역 ──────────────────────────────────────
MANAGER_REGIONS = {
    "전체":     [],
    "대리점 A": ["인천", "고양", "김포", "부천", "광명", "시흥", "안산", "파주", "원주", "춘천"],
    "대리점 B": ["충청", "대전", "세종", "충남", "충북"],
}

URL = 'https://apis.data.go.kr/1741000/animal_hospitals/info'
KEY = '2f470b5a09e984c04d6729c7bd7f0e9451c3407c594d5767b9d7846c2cbb8faf'


# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'Bebas Neue\',sans-serif;font-size:1.4rem;letter-spacing:3px;color:#3d8eff;margin-bottom:4px;">VET INTEL</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.62rem;color:#2a3050;letter-spacing:2px;margin-bottom:20px;">NATIONAL CLINIC INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border:none;border-top:1px solid #1e2535;margin:16px 0">', unsafe_allow_html=True)

    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.65rem;letter-spacing:2px;color:#3a4260;margin-bottom:8px;">기준 날짜</div>', unsafe_allow_html=True)
    base_date   = st.date_input("", pd.to_datetime("2026-02-28"), label_visibility="collapsed")
    target_date = pd.to_datetime(base_date)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶  데이터 분석 실행", use_container_width=True)

    st.markdown('<hr style="border:none;border-top:1px solid #1e2535;margin:20px 0">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.65rem;letter-spacing:2px;color:#3a4260;margin-bottom:10px;">담당 구역 필터</div>', unsafe_allow_html=True)
    selected_manager = st.radio(
        "",
        options=list(MANAGER_REGIONS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    if selected_manager != "전체":
        st.caption(f"관할: {', '.join(MANAGER_REGIONS[selected_manager])}")

    st.markdown('<hr style="border:none;border-top:1px solid #1e2535;margin:20px 0">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;color:#2a3050;letter-spacing:1px;line-height:1.8;">ANALYST · 이찬범<br>DATA · 공공데이터포털</div>', unsafe_allow_html=True)


# ── 히어로 헤더 ──────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">National Veterinary Clinic Intelligence Dashboard</div>
  <div class="hero-title">전국 동물병원<br><span>개업 · 폐업</span> 실시간 추적기</div>
  <div class="hero-sub">공공데이터 API 연동 &nbsp;·&nbsp; 전국 시도별 자동 분류 &nbsp;·&nbsp; 담당 구역 필터</div>
  <div class="hero-author">ANALYST : 이찬범 &nbsp;·&nbsp; POWERED BY 공공데이터포털</div>
</div>
""", unsafe_allow_html=True)


# ── 데이터 수집 ──────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_all_hospital_data():
    def fetch(p):
        params = {
            'serviceKey': KEY,
            'pageNo': str(p),
            'numOfRows': '100',
            'resultType': 'json'
        }
        try:
            r = requests.get(URL, params=params, verify=False, timeout=5)
            return r.json()['response']['body']['items']['item']
        except:
            return []
    with ThreadPoolExecutor(max_workers=10) as exe:
        results = list(exe.map(fetch, range(1, 81)))
    return [item for sublist in results for item in sublist]


def filter_by_manager(df: pd.DataFrame, manager: str) -> pd.DataFrame:
    if manager == "전체":
        return df
    keywords = MANAGER_REGIONS[manager]
    mask = df['전체주소'].fillna('').apply(
        lambda addr: any(kw in addr for kw in keywords)
    )
    return df[mask]


# ── 분석 실행 ────────────────────────────────────────────────
if run_btn:
    with st.spinner("공공데이터 API 연결 중 · 전국 데이터 수집 중..."):
        all_data = get_all_hospital_data()
        df = pd.DataFrame(all_data)

        df['LCPMT_YMD']  = pd.to_datetime(df['LCPMT_YMD'],  errors='coerce')
        df['CLSBIZ_YMD'] = pd.to_datetime(df['CLSBIZ_YMD'], errors='coerce')
        df['전체주소']    = df['ROAD_NM_ADDR'].fillna(df['LOTNO_ADDR'])
        df['시도']        = df['전체주소'].str.split().str[0].fillna('미분류')

        new_open   = df[df['LCPMT_YMD']  >= target_date].copy()
        new_closed = df[df['CLSBIZ_YMD'] >= target_date].copy()

        open_filtered   = filter_by_manager(new_open,   selected_manager)
        closed_filtered = filter_by_manager(new_closed, selected_manager)

    label = f"[{selected_manager}]" if selected_manager != "전체" else "[전체]"
    total = len(open_filtered) + len(closed_filtered)

    # ── KPI 카드 ──
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card blue">
        <div class="kpi-label">신규 개업</div>
        <div class="kpi-value">{len(open_filtered)}</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-label">신규 폐업</div>
        <div class="kpi-value">{len(closed_filtered)}</div>
      </div>
      <div class="kpi-card gold">
        <div class="kpi-label">총 변동</div>
        <div class="kpi-value">{total}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if selected_manager != "전체":
        st.info(f"**{selected_manager}** 관할 구역 필터 적용 중 — {', '.join(MANAGER_REGIONS[selected_manager])}")

    st.markdown("""
    <div class="notice-bar">
    ⚠ &nbsp; 개원 신고 후 실제 운영 전인 경우가 있습니다. 방문 전 반드시 네이버지도 검색 또는 유선 확인 후 방문하시기 바랍니다.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["NEW OPEN — 신규 개업", "CLOSED — 신규 폐업"])

    with tab1:
        if not open_filtered.empty:
            for reg in sorted(open_filtered['시도'].unique()):
                reg_df = open_filtered[open_filtered['시도'] == reg]
                with st.expander(f"📍 {reg}  ·  {len(reg_df)}건", expanded=True):
                    display = reg_df[['BPLC_NM', '전체주소', 'LCPMT_YMD', 'TELNO']].copy()
                    display.columns = ['병원명', '주소', '개업일', '전화번호']
                    display['개업일'] = display['개업일'].dt.strftime('%Y-%m-%d')
                    st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.info("해당 조건의 개업 내역이 없습니다.")

    with tab2:
        if not closed_filtered.empty:
            for reg in sorted(closed_filtered['시도'].unique()):
                reg_df = closed_filtered[closed_filtered['시도'] == reg]
                with st.expander(f"📍 {reg}  ·  {len(reg_df)}건", expanded=True):
                    display = reg_df[['BPLC_NM', '전체주소', 'CLSBIZ_YMD']].copy()
                    display.columns = ['병원명', '주소', '폐업일']
                    display['폐업일'] = display['폐업일'].dt.strftime('%Y-%m-%d')
                    st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.info("해당 조건의 폐업 내역이 없습니다.")

    st.markdown(f"""
    <div class="footer">
        VET INTEL DASHBOARD &nbsp;·&nbsp; ANALYST : 이찬범 &nbsp;·&nbsp;
        DATA SOURCE : 공공데이터포털 &nbsp;·&nbsp;
        BASE DATE : {base_date.strftime('%Y-%m-%d')} &nbsp;·&nbsp; FILTER : {selected_manager}
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center; padding: 80px 0; color: #2a3050;">
        <div style="font-family:'Bebas Neue',sans-serif; font-size:1.2rem; letter-spacing:4px; margin-bottom:12px;">
            READY TO ANALYZE
        </div>
        <div style="font-family:'DM Mono',monospace; font-size:0.75rem; letter-spacing:2px; line-height:2;">
            좌측 패널에서 기준 날짜를 설정하고<br>▶ 데이터 분석 실행을 눌러주세요
        </div>
    </div>
    """, unsafe_allow_html=True)
