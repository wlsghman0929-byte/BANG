# ☁️ 내 컴퓨터 없이 자동 갱신하기 (GitHub Actions + GitHub Pages)

내 PC를 켜두지 않아도 **GitHub의 클라우드 서버가 30분마다 시세를 받아** 대시보드를
다시 만들어 웹에 올려줍니다. 무료이고, 만든 주소(`https://아이디.github.io/저장소/`)만
열면 됩니다. 브라우저는 그 주소를 자동 새로고침하므로 최신 결과가 보입니다.

> 왜 이게 필요한가: HTML 파일은 스스로 시세를 못 받아옵니다. 누군가(=내 PC의 파이썬,
> 또는 클라우드 서버)가 주기적으로 다시 만들어줘야 합니다. 이 방법은 그 "누군가"를
> GitHub 클라우드가 대신 해줍니다.

---

## 준비물
- GitHub 계정 (무료) — https://github.com 가입

## 단계

### 1. 저장소(repository) 만들고 코드 올리기
1. GitHub에서 **New repository** → 이름 입력(예: `my-quant`) → **Public** 선택 → Create
2. 이 `quant_dashboard` 폴더 전체를 그 저장소에 올립니다.
   - 쉬운 방법: 저장소 페이지 → **Add file → Upload files** → 폴더 안 파일들을 드래그해서 업로드 → Commit
   - (`.github/workflows/scan.yml` 파일도 반드시 함께 올라가야 합니다 — 이게 자동 실행 설정입니다)

### 2. GitHub Pages 켜기
- 저장소 → **Settings → Pages → Build and deployment → Source** 를 **GitHub Actions** 로 설정

### 3. 자동 실행 시작
- 저장소 → **Actions** 탭 → "Update Market Scanner" 워크플로 선택 → **Run workflow** 로 한 번 수동 실행
- 이후에는 30분마다 자동으로 돕니다. (cron 은 `scan.yml` 에서 조절)

### 4. 대시보드 주소 확인
- **Settings → Pages** 상단에 표시되는 주소(`https://아이디.github.io/저장소/`)가 대시보드입니다.
- 휴대폰·다른 PC 어디서든 그 주소만 열면 됩니다.

---

## (선택) 한국투자증권 실시간 현재가 켜기
키를 코드에 적지 말고 **GitHub Secrets** 에 넣습니다:
- 저장소 → **Settings → Secrets and variables → Actions → New repository secret** 로 아래 3개 등록
  - `USE_KIS_REALTIME` = `true`
  - `KIS_APP_KEY` = 발급받은 앱키
  - `KIS_APP_SECRET` = 발급받은 앱시크릿

`scan_config.py` 가 환경변수를 우선 읽으므로, Secrets 만 넣으면 클라우드에서 자동 적용됩니다.

---

## 참고 / 한계
- GitHub 예약 실행(cron)은 보통 **5~30분 단위**가 현실적이며, 트래픽 상황에 따라 몇 분 늦거나
  건너뛸 수 있습니다. 초 단위 실시간은 클라우드 무료로는 어렵습니다.
- 종목 수가 많으면(러셀1000+코스피200) 한 번 도는 데 몇 분 걸립니다. 빠르게 하려면
  `scan_config.py` 에서 `US_UNIVERSE="sp500"` 또는 `MAX_TICKERS=300` 으로 줄이세요.
- 한국 시세(pykrx)는 해외 서버에서 간헐적으로 막힐 수 있습니다. 안정성이 중요하면
  국내에 있는 항상 켜진 장비(예: 라즈베리파이)나 국내 클라우드에서 `python run_scanner.py`
  (반복 모드)로 돌리는 것도 방법입니다.

## 다른 무료/저비용 대안
- **PythonAnywhere**: 무료 플랜에 "Scheduled task"(하루 1회) 제공. 더 자주 돌리려면 유료.
- **Render / Railway 등의 Cron Job**: 주기 실행 가능(소액 과금 또는 무료 한도).
- **항상 켜진 미니 PC / 라즈베리파이**: `python run_scanner.py` 를 그냥 띄워두면 됨(내 PC는 꺼도 됨).
