# scan_config.py — 시장 스캐너 설정
# ----------------------------------------------------------------
# 한국(pykrx)·미국(yfinance) 종목을 대량 수집해
# 급등/급락/거래량급증/변동성/추천을 뽑습니다. 대시보드에서 시장 전환 가능.
# ----------------------------------------------------------------

# 스캔할 시장: ["US"], ["KR"], 또는 ["US","KR"] (둘 다)
MARKETS = ["US", "KR"]

# ---- 미국 유니버스 ----
US_UNIVERSE = "russell1000"   # "sp500" | "sp500+nasdaq100" | "russell1000" | "custom"
US_CUSTOM_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "GOOGL", "AMZN", "META"]

# ---- 한국 유니버스 ----
KR_UNIVERSE = "kospi200"      # "kospi200" | "kospi" | "kosdaq" | "kospi+kosdaq" | "custom"
KR_CUSTOM_TICKERS = ["005930", "000660", "035420", "035720", "005380", "051910"]

# 안전장치: 시장별 한 번에 스캔할 최대 종목 수 (속도 조절). None 이면 전체.
MAX_TICKERS = None

# 미국 시세 다운로드 배치 크기 (yfinance 안정성)
BATCH_SIZE = 150

# ---- 자동 갱신 ----
REFRESH_MINUTES = 10        # 몇 분마다 시세를 다시 받아올지 (실제 데이터 갱신 주기)
AUTO_RELOAD_SECONDS = 20    # 브라우저가 화면을 몇 초마다 새로고침할지 (짧을수록 자주)

# ---- 표시 개수 ----
TOP_N = 30                  # 각 랭킹 탭에 보여줄 상위 종목 수

# ---- 급변동/거래량 임계값(표시는 전체 랭킹, 임계값은 강조용) ----
VOL_SURGE_MULT = 2.0        # 평균 거래량 대비 이 배수 이상이면 '급증' 강조
BIG_MOVE_PCT = 5.0          # 당일 등락 이 % 이상이면 '급변동' 강조

# ---- 기술적 추천 파라미터 ----
FAST_MA = 20
SLOW_MA = 50
RSI_BUY_MIN = 45            # 추천 RSI 하한
RSI_BUY_MAX = 68            # 추천 RSI 상한

# 데이터 조회 실패 시 합성 데모 데이터 사용 (오프라인 테스트용)
ALLOW_DEMO_FALLBACK = True

# ---- 한국투자증권(KIS) Open API 실시간 현재가 (선택) ----
# 일봉은 pykrx, '현재가'만 KIS 실시간으로 보강합니다.
# https://apiportal.koreainvestment.com 에서 앱키/시크릿 발급 후 입력하고 스위치를 켜세요.
import os  # noqa: E402

USE_KIS_REALTIME = False     # True 로 켜면 KR 현재가를 KIS 실시간으로 대체
KIS_APP_KEY = ""             # 한국투자증권 앱키
KIS_APP_SECRET = ""          # 한국투자증권 앱시크릿
KIS_ENV = "real"             # "real"(실전) | "vps"(모의투자)

# 환경변수가 있으면 우선 적용 (클라우드 배포 시 키를 코드에 안 넣고 Secrets 로 주입)
USE_KIS_REALTIME = os.environ.get(
    "USE_KIS_REALTIME", str(USE_KIS_REALTIME)).lower() in ("1", "true", "yes")
KIS_APP_KEY = os.environ.get("KIS_APP_KEY", KIS_APP_KEY)
KIS_APP_SECRET = os.environ.get("KIS_APP_SECRET", KIS_APP_SECRET)
KIS_ENV = os.environ.get("KIS_ENV", KIS_ENV)
