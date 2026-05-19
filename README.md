# 🏥 전국 동물병원 개업/폐업 추적기

공공데이터 API를 통해 전국 동물병원의 신규 개업·폐업 현황을 자동으로 추적합니다.  
**GitHub Actions**가 매일 데이터를 갱신하고, **GitHub Pages**로 누구나 링크로 바로 확인 가능합니다.

**작성자 : 이찬범**

---

## 🚀 GitHub에서 바로 시작하는 법

### 1단계 — 저장소 만들기
1. GitHub에서 **New repository** 클릭
2. 이 파일 3개를 업로드:
   - `generate.py`
   - `.github/workflows/update.yml`
   - `README.md`

### 2단계 — 최초 HTML 생성 (Actions 수동 실행)
1. 저장소 → **Actions** 탭
2. `동물병원 데이터 자동 갱신` 클릭 → **Run workflow**
3. 완료되면 `index.html`이 자동 생성됩니다

### 3단계 — GitHub Pages 켜기
1. 저장소 → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / `/ (root)` → **Save**
4. 잠시 후 `https://[유저명].github.io/[저장소명]/` 링크 완성!

이후 매일 오전 9시(KST)에 자동 갱신됩니다.

---

## 📁 파일 구조

```
├── generate.py                    # API 호출 → index.html 생성 스크립트
├── .github/workflows/update.yml  # 매일 자동 실행 Actions
├── index.html                     # (자동 생성됨) 실제 웹페이지
└── README.md
```
