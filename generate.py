import requests
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

URL = 'https://apis.data.go.kr/1741000/animal_hospitals/info'
KEY = '2f470b5a09e984c04d6729c7bd7f0e9451c3407c594d5767b9d7846c2cbb8faf'

TARGET_DATE = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

def fetch(p):
    params = {
        'serviceKey': KEY,
        'pageNo': str(p),
        'numOfRows': '100',
        'resultType': 'json'
    }
    try:
        r = requests.get(URL, params=params, verify=False, timeout=10)
        return r.json()['response']['body']['items']['item']
    except:
        return []

print("📡 데이터 수집 중...")
with ThreadPoolExecutor(max_workers=10) as exe:
    results = list(exe.map(fetch, range(1, 81)))
all_data = [item for sublist in results for item in sublist]
print(f"총 {len(all_data)}건 수집 완료")

def parse_date(val):
    try:
        return datetime.strptime(str(val)[:10], '%Y-%m-%d')
    except:
        return None

target_dt = datetime.strptime(TARGET_DATE, '%Y-%m-%d')

open_list = []
close_list = []

for item in all_data:
    addr = item.get('ROAD_NM_ADDR') or item.get('LOTNO_ADDR') or ''
    sido = addr.split()[0] if addr.strip() else '미분류'
    base = {
        'name': item.get('BPLC_NM', ''),
        'addr': addr,
        'tel': item.get('TELNO', ''),
        'sido': sido,
    }
    open_dt = parse_date(item.get('LCPMT_YMD'))
    close_dt = parse_date(item.get('CLSBIZ_YMD'))

    if open_dt and open_dt >= target_dt:
        open_list.append({**base, 'date': open_dt.strftime('%Y-%m-%d')})
    if close_dt and close_dt >= target_dt:
        close_list.append({**base, 'date': close_dt.strftime('%Y-%m-%d')})

# 시도별 그룹
def group_by_sido(lst):
    groups = {}
    for item in lst:
        groups.setdefault(item['sido'], []).append(item)
    return dict(sorted(groups.items()))

open_groups = group_by_sido(open_list)
close_groups = group_by_sido(close_list)

updated_at = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')

# HTML 생성
def render_table(items, date_label):
    rows = ''
    for it in items:
        rows += f"""
        <tr>
          <td>{it['name']}</td>
          <td class="addr">{it['addr']}</td>
          <td>{it['date']}</td>
          <td>{it['tel']}</td>
        </tr>"""
    return f"""
    <table>
      <thead><tr><th>병원명</th><th>주소</th><th>{date_label}</th><th>전화번호</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""

def render_sections(groups, date_label, tab_id):
    html = ''
    for sido, items in groups.items():
        rows_html = render_table(items, date_label)
        html += f"""
        <div class="section">
          <div class="section-header" onclick="toggleSection(this)">
            <span class="pin">📍</span>
            <span>{sido} {'개업' if tab_id=='open' else '폐업'} <span class="badge">{len(items)}건</span></span>
            <span class="chevron">▾</span>
          </div>
          <div class="section-body">
            {rows_html}
          </div>
        </div>"""
    return html

open_html = render_sections(open_groups, '개업일', 'open')
close_html = render_sections(close_groups, '폐업일', 'close')

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>전국 동물병원 개업/폐업 추적기</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<style>
  :root {{
    --bg: #0d0f14;
    --surface: #161921;
    --surface2: #1e2230;
    --border: #2a2f3d;
    --accent-open: #00e5a0;
    --accent-close: #ff4d6d;
    --accent-yellow: #ffd166;
    --text: #e8eaf0;
    --text-muted: #7a8099;
    --font: 'Noto Sans KR', sans-serif;
    --mono: 'DM Mono', monospace;
  }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
  }}

  /* ── HEADER ── */
  header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 28px 40px 24px;
    display: flex;
    align-items: flex-end;
    gap: 20px;
    flex-wrap: wrap;
  }}
  .header-left h1 {{
    font-size: 1.7rem;
    font-weight: 900;
    letter-spacing: -0.5px;
    line-height: 1.2;
  }}
  .header-left p {{
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-top: 5px;
  }}
  .header-left .author {{
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 2px;
    font-family: var(--mono);
  }}
  .header-right {{
    margin-left: auto;
    text-align: right;
  }}
  .updated {{
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--text-muted);
  }}
  .updated span {{
    color: var(--accent-open);
  }}

  /* ── STAT CARDS ── */
  .stats {{
    display: flex;
    gap: 16px;
    padding: 24px 40px;
    flex-wrap: wrap;
  }}
  .stat-card {{
    flex: 1;
    min-width: 160px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
  }}
  .stat-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
  }}
  .stat-card.open::before {{ background: var(--accent-open); }}
  .stat-card.close::before {{ background: var(--accent-close); }}
  .stat-card .label {{
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: var(--mono);
  }}
  .stat-card .num {{
    font-size: 2.8rem;
    font-weight: 900;
    line-height: 1.1;
    margin-top: 6px;
  }}
  .stat-card.open .num {{ color: var(--accent-open); }}
  .stat-card.close .num {{ color: var(--accent-close); }}
  .stat-card .sub {{
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 4px;
  }}

  /* ── NOTICE ── */
  .notice {{
    margin: 0 40px 20px;
    background: rgba(255, 209, 102, 0.08);
    border: 1px solid rgba(255, 209, 102, 0.25);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 0.82rem;
    color: var(--accent-yellow);
    line-height: 1.6;
  }}

  /* ── TABS ── */
  .tabs {{
    display: flex;
    gap: 4px;
    padding: 0 40px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }}
  .tab-btn {{
    padding: 10px 20px;
    background: none;
    border: none;
    cursor: pointer;
    font-family: var(--font);
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-muted);
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: all 0.2s;
  }}
  .tab-btn:hover {{ color: var(--text); }}
  .tab-btn.active-open {{ color: var(--accent-open); border-bottom-color: var(--accent-open); }}
  .tab-btn.active-close {{ color: var(--accent-close); border-bottom-color: var(--accent-close); }}

  /* ── CONTENT ── */
  .tab-content {{ display: none; padding: 0 40px 60px; }}
  .tab-content.active {{ display: block; }}

  /* ── FILTER ── */
  .filter-bar {{
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    align-items: center;
  }}
  .filter-bar span {{
    font-size: 0.78rem;
    color: var(--text-muted);
    font-family: var(--mono);
    margin-right: 4px;
  }}
  .filter-btn {{
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: var(--surface2);
    color: var(--text-muted);
    font-size: 0.8rem;
    font-family: var(--font);
    cursor: pointer;
    transition: all 0.15s;
  }}
  .filter-btn:hover, .filter-btn.active {{
    border-color: var(--accent-open);
    color: var(--accent-open);
    background: rgba(0,229,160,0.08);
  }}

  /* ── SECTION ── */
  .section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 12px;
    overflow: hidden;
  }}
  .section-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 20px;
    cursor: pointer;
    user-select: none;
    transition: background 0.15s;
    font-weight: 700;
    font-size: 0.9rem;
  }}
  .section-header:hover {{ background: var(--surface2); }}
  .badge {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-family: var(--mono);
    color: var(--text-muted);
    font-weight: 400;
  }}
  .chevron {{
    margin-left: auto;
    font-size: 1rem;
    color: var(--text-muted);
    transition: transform 0.2s;
  }}
  .section.collapsed .chevron {{ transform: rotate(-90deg); }}
  .section-body {{
    border-top: 1px solid var(--border);
    overflow-x: auto;
  }}
  .section.collapsed .section-body {{ display: none; }}

  /* ── TABLE ── */
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }}
  thead tr {{
    background: var(--surface2);
  }}
  th {{
    padding: 10px 16px;
    text-align: left;
    font-size: 0.72rem;
    font-family: var(--mono);
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
    white-space: nowrap;
  }}
  td {{
    padding: 11px 16px;
    border-top: 1px solid var(--border);
    vertical-align: middle;
    line-height: 1.4;
  }}
  td.addr {{
    color: var(--text-muted);
    font-size: 0.78rem;
    max-width: 340px;
  }}
  tr:hover td {{ background: rgba(255,255,255,0.02); }}

  /* ── RESPONSIVE ── */
  @media (max-width: 700px) {{
    header, .stats, .tabs, .tab-content, .notice {{ padding-left: 16px; padding-right: 16px; }}
    .header-left h1 {{ font-size: 1.2rem; }}
    .stat-card .num {{ font-size: 2rem; }}
  }}
</style>
</head>
<body>

<header>
  <div class="header-left">
    <h1>🏥 전국 동물병원 개업/폐업 추적기</h1>
    <p>공공데이터 API를 통해 전국 데이터를 자동 분석합니다.</p>
    <p class="author">작성자 : 이찬범</p>
  </div>
  <div class="header-right">
    <div class="updated">최종 업데이트 <span>{updated_at}</span></div>
    <div class="updated" style="margin-top:4px">기준: {TARGET_DATE} 이후</div>
  </div>
</header>

<div class="stats">
  <div class="stat-card open">
    <div class="label">신규 개업</div>
    <div class="num">{len(open_list)}</div>
    <div class="sub">건 집계됨</div>
  </div>
  <div class="stat-card close">
    <div class="label">신규 폐업</div>
    <div class="num">{len(close_list)}</div>
    <div class="sub">건 집계됨</div>
  </div>
</div>

<div class="notice">
  ※ 개원 신고만 하고 실제로는 아직 오픈 전인 경우가 있으니 반드시 사전에 네이버지도 검색 혹은 전화를 통해 확인 후 방문 부탁 드립니다.
</div>

<div class="tabs">
  <button class="tab-btn active-open" onclick="switchTab('open', this)">🆕 신규 개업 상세</button>
  <button class="tab-btn" onclick="switchTab('close', this)">❌ 신규 폐업 상세</button>
</div>

<div id="tab-open" class="tab-content active">
  <div class="filter-bar" id="filter-open">
    <span>지역 필터:</span>
    <button class="filter-btn active" onclick="filterSido('open', '', this)">전체</button>
    {"".join(f'<button class="filter-btn" onclick="filterSido(\'open\', \'{s}\', this)">{s}</button>' for s in sorted(open_groups.keys()))}
  </div>
  {open_html}
</div>

<div id="tab-close" class="tab-content">
  <div class="filter-bar" id="filter-close">
    <span>지역 필터:</span>
    <button class="filter-btn active" onclick="filterSido('close', '', this)">전체</button>
    {"".join(f'<button class="filter-btn" onclick="filterSido(\'close\', \'{s}\', this)">{s}</button>' for s in sorted(close_groups.keys()))}
  </div>
  {close_html}
</div>

<script>
function switchTab(tab, btn) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.className = 'tab-btn');
  document.getElementById('tab-' + tab).classList.add('active');
  btn.className = 'tab-btn active-' + tab;
}}

function toggleSection(header) {{
  header.parentElement.classList.toggle('collapsed');
}}

function filterSido(tab, sido, btn) {{
  const container = document.getElementById('tab-' + tab);
  container.querySelectorAll('.section').forEach(sec => {{
    if (!sido) {{
      sec.style.display = '';
    }} else {{
      const title = sec.querySelector('.section-header span:nth-child(2)').textContent;
      sec.style.display = title.startsWith(sido) ? '' : 'none';
    }}
  }});
  const filterBar = document.getElementById('filter-' + tab);
  filterBar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}}
</script>
</body>
</html>"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ index.html 생성 완료! 개업 {len(open_list)}건 / 폐업 {len(close_list)}건")
