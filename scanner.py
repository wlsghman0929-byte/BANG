"""scanner.py — 대량 종목 스캔 엔진

yfinance 로 유니버스 전체 시세를 배치 다운로드하고, 종목별로
등락률 / 거래량급증 / 변동성 / 기술적 추천점수를 계산한다.
네트워크 실패 시 합성 데모 데이터로 폴백.
"""
from __future__ import annotations
import datetime as dt
import numpy as np
import pandas as pd

import scan_config as C
import indicators


# ---------------------------------------------------------------- 데모
def _demo_df(ticker: str, n: int = 90,
             base_lo: float = 20, base_hi: float = 600) -> pd.DataFrame:
    seed = abs(hash(ticker)) % (2**32)
    rng = np.random.default_rng(seed)
    mu = rng.uniform(-0.001, 0.0015)
    sigma = rng.uniform(0.012, 0.05)
    rets = rng.normal(mu, sigma, n)
    # 가끔 큰 점프(급변동 종목 흉내)
    if rng.random() < 0.15:
        rets[-1] += rng.choice([-1, 1]) * rng.uniform(0.06, 0.15)
    start = rng.uniform(base_lo, base_hi)
    close = start * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(rng.normal(0, 0.01, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.01, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    base_vol = rng.integers(1_000_000, 20_000_000)
    vol = rng.integers(int(base_vol*0.5), int(base_vol*1.5), n).astype(float)
    if rng.random() < 0.15:  # 거래량 급증 흉내
        vol[-1] *= rng.uniform(2.5, 6)
    idx = pd.bdate_range(end=dt.date.today(), periods=n)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low,
                         "Close": close, "Volume": vol}, index=idx)


# ---------------------------------------------------------------- 다운로드
def _download_batch(tickers: list[str]) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    try:
        import yfinance as yf
        data = yf.download(tickers, period="4mo", interval="1d",
                           group_by="ticker", threads=True,
                           progress=False, auto_adjust=True)
        if data is None or len(data) == 0:
            return out
        if len(tickers) == 1:
            t = tickers[0]
            df = data
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            out[t] = df
            return out
        for t in tickers:
            try:
                df = data[t].dropna(how="all")
                if len(df) > 0:
                    out[t] = df
            except Exception:
                pass
    except Exception as e:
        print(f"  배치 다운로드 실패: {repr(e)[:80]}")
    return out


# ---------------------------------------------------------------- 한국 시세
def _fetch_kr_one(code: str) -> pd.DataFrame | None:
    try:
        from pykrx import stock
        end = dt.date.today()
        start = end - dt.timedelta(days=130)
        df = stock.get_market_ohlcv(start.strftime("%Y%m%d"),
                                    end.strftime("%Y%m%d"), code)
        if df is None or len(df) == 0:
            return None
        df = df.rename(columns={"시가": "Open", "고가": "High", "저가": "Low",
                                "종가": "Close", "거래량": "Volume"})
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        df = df[df["Close"] > 0]
        return df if len(df) else None
    except Exception:
        return None


# ---------------------------------------------------------------- 지표 계산
def _atr(df: pd.DataFrame, n: int = 14) -> float:
    h, l, c = df["High"], df["Low"], df["Close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1])


# ---------------------------------------------------------------- 마감가 예측기
def _ewma_last(x, span: int) -> float:
    a = 2.0 / (span + 1)
    m = x[0]
    for v in x[1:]:
        m = a * v + (1 - a) * m
    return m


def _rsi_arr(arr, n: int = 14) -> float:
    if len(arr) < 2:
        return 50.0
    d = np.diff(arr)
    g = np.clip(d, 0, None)[-n:]
    l = np.clip(-d, 0, None)[-n:]
    ag = g.mean() if len(g) else 0.0
    al = l.mean() if len(l) else 0.0
    al = al if al > 0 else 1e-9
    return float(100 - 100 / (1 + ag / al))


def predict_r(closes) -> tuple[float, float]:
    """다음 1봉 수익률 예측 r_hat 과 변동성 sigma 반환.
    추세(모멘텀 EWMA) + 회귀(선형추세) + 평균회귀(RSI) 앙상블, 변동성으로 클립."""
    arr = np.asarray(closes, dtype=float)
    if len(arr) < 6:
        return 0.0, 0.0
    rr = np.diff(arr) / arr[:-1]
    sigma = float(rr[-20:].std()) if len(rr) >= 2 else 0.0
    mom = _ewma_last(rr.tolist(), 5)
    n = min(10, len(arr))
    x = np.arange(n)
    slope = float(np.polyfit(x, arr[-n:], 1)[0])
    reg = slope / arr[-1]
    rsi = _rsi_arr(arr)
    rsi_pull = ((50.0 - rsi) / 50.0) * (sigma if sigma > 0 else 0.0)
    r = 0.4 * mom + 0.2 * reg + 0.4 * rsi_pull
    lim = 2.0 * sigma if sigma > 0 else 0.04
    return max(-lim, min(lim, r)), sigma


def backtest_pred(closes, lookback: int = 30):
    """예측기를 과거에 워크포워드로 적용해 방향 적중률(%)·평균오차(%)·잔차표준편차."""
    arr = list(map(float, closes))
    start = max(55, len(arr) - lookback)
    hits = cnt = 0
    errs, resids = [], []
    for t in range(start, len(arr)):
        r, _ = predict_r(arr[:t])
        prev = arr[t - 1]
        pred = prev * (1 + r)
        actual = arr[t]
        errs.append(abs(pred - actual) / actual)
        resids.append((actual - pred) / prev)
        if (pred >= prev) == (actual >= prev):
            hits += 1
        cnt += 1
    hit = 100.0 * hits / cnt if cnt else 0.0
    mae = 100.0 * float(np.mean(errs)) if errs else 0.0
    rstd = float(np.std(resids)) if resids else 0.0
    return hit, mae, rstd


def compute_metrics(ticker: str, df: pd.DataFrame, name: str = "",
                    market: str = "US") -> dict | None:
    df = df.dropna(subset=["Close"]).copy()
    if len(df) < C.SLOW_MA + 2:
        return None
    df = indicators.add_all(df, C.FAST_MA, C.SLOW_MA)
    last, prev = df.iloc[-1], df.iloc[-2]
    close = float(last["Close"])
    if close <= 0:
        return None

    day_change = (close / float(prev["Close"]) - 1) * 100
    avg_vol = float(df["Volume"].tail(20).mean())
    vol = float(last["Volume"])
    vol_ratio = (vol / avg_vol) if avg_vol > 0 else 0.0

    atr = _atr(df, 14)
    atr_pct = (atr / close) * 100 if close else 0.0
    ret_std = float(df["Close"].pct_change().tail(20).std() * np.sqrt(252) * 100)

    rsi = float(last["RSI"])
    trend_up = last["MA_fast"] > last["MA_slow"]
    above_fast = close > last["MA_fast"]
    macd_up = last["MACD"] > last["MACD_signal"]
    cross_up = (prev["MA_fast"] <= prev["MA_slow"]) and (last["MA_fast"] > last["MA_slow"])
    macd_turn_up = (prev["MACD"] <= prev["MACD_signal"]) and macd_up

    # 기술적 추천 점수 (0~5)
    score = 0
    reasons = []
    if trend_up: score += 1; reasons.append("상승추세(MA20>MA50)")
    if above_fast: score += 1; reasons.append("MA20 위")
    if macd_up: score += 1; reasons.append("MACD 매수권")
    if C.RSI_BUY_MIN <= rsi <= C.RSI_BUY_MAX: score += 1; reasons.append(f"RSI {rsi:.0f} 적정")
    if cross_up or macd_turn_up: score += 1; reasons.append("신규 매수전환")

    if cross_up:
        signal = "BUY"
    elif (prev["MA_fast"] >= prev["MA_slow"]) and (last["MA_fast"] < last["MA_slow"]):
        signal = "SELL"
    elif score >= 4:
        signal = "BUY"
    else:
        signal = "HOLD"

    # ---- 다음 마감가 예측 + 과거 적중률 백테스트 ----
    closes_list = df["Close"].tolist()
    r_hat, sigma = predict_r(closes_list)
    pred_close = close * (1 + r_hat)
    pred_chg = r_hat * 100
    pred_hit, pred_mae, resid_std = backtest_pred(closes_list, lookback=30)
    band = resid_std if resid_std > 0 else sigma
    pred_low = close * (1 + r_hat - band)
    pred_high = close * (1 + r_hat + band)

    # ---- 상세(모달 차트)용 최근 60봉 데이터 ----
    tail = df.tail(60)
    d_dates = [t.strftime("%m-%d") for t in tail.index]
    d_close = [round(float(x), 2) for x in tail["Close"].tolist()]
    d_open = [round(float(x), 2) for x in tail["Open"].tolist()]
    d_vol = [int(x) for x in tail["Volume"].tolist()]
    # 매수세/매도세: 당일 종가>=시가 면 매수우위(거래량을 +), 아니면 매도우위(-)
    up_flags = [1 if c >= o else -1 for c, o in zip(d_close, d_open)]
    # 최근 20봉 매수세 비중(%)
    recent = list(zip(up_flags[-20:], d_vol[-20:]))
    buy_v = sum(v for f, v in recent if f > 0)
    tot_v = sum(v for _, v in recent) or 1
    buy_ratio = round(buy_v / tot_v * 100, 1)

    return {
        "ticker": ticker,
        "name": name or ticker,
        "market": market,
        "close": round(close, 2),
        "day_change": round(day_change, 2),
        "vol_ratio": round(vol_ratio, 2),
        "volume": int(vol),
        "atr_pct": round(atr_pct, 2),
        "ret_vol": round(ret_std, 1),
        "rsi": round(rsi, 1),
        "score": score,
        "signal": signal,
        "reasons": reasons,
        "buy_ratio": buy_ratio,
        "pred_close": round(pred_close, 2),
        "pred_chg": round(pred_chg, 2),
        "pred_low": round(pred_low, 2),
        "pred_high": round(pred_high, 2),
        "pred_hit": round(pred_hit, 0),
        "pred_mae": round(pred_mae, 2),
        "spark": d_close[-30:],
        "detail": {"dates": d_dates, "close": d_close,
                   "vol": d_vol, "updown": up_flags},
    }


# ---------------------------------------------------------------- 메인 스캔
def scan(market: str, tickers: list[str],
         names: dict[str, str] | None = None) -> tuple[list[dict], str]:
    names = names or {}
    market = market.upper()
    rows: list[dict] = []
    got_any = False
    total = len(tickers)

    if market == "KR":
        # KIS 실시간 현재가 보강 여부 (키 설정 시에만 활성)
        kis = None
        try:
            import kis_data
            if kis_data.enabled():
                kis = kis_data
                print("  [KR] 현재가는 한국투자증권(KIS) 실시간으로 보강합니다.")
        except Exception:
            kis = None
        # 한국: pykrx 는 배치가 없어 종목별 조회
        for j, t in enumerate(tickers):
            df = _fetch_kr_one(t)
            if df is not None:
                got_any = True
            elif C.ALLOW_DEMO_FALLBACK:
                df = _demo_df(t, base_lo=5000, base_hi=400000)
            if df is None:
                continue
            # 일봉은 pykrx, 현재가만 KIS 실시간으로 덮어쓰기
            if kis is not None:
                rt = kis.get_price(t)
                if rt:
                    df = df.copy()
                    df.iloc[-1, df.columns.get_loc("Close")] = rt
            m = compute_metrics(t, df, names.get(t, t), "KR")
            if m:
                rows.append(m)
            if (j + 1) % 50 == 0 or j + 1 == total:
                print(f"  [KR] 진행: {j+1}/{total} 종목")
    else:
        # 미국: yfinance 배치 다운로드
        for i in range(0, total, C.BATCH_SIZE):
            chunk = tickers[i:i + C.BATCH_SIZE]
            batch = _download_batch(chunk)
            if batch:
                got_any = True
            for t in chunk:
                df = batch.get(t)
                if df is None and C.ALLOW_DEMO_FALLBACK:
                    df = _demo_df(t, base_lo=20, base_hi=600)
                if df is None:
                    continue
                m = compute_metrics(t, df, names.get(t, t), "US")
                if m:
                    rows.append(m)
            print(f"  [US] 진행: {min(i+C.BATCH_SIZE, total)}/{total} 종목")

    return rows, ("demo" if not got_any else "live")


def rank(rows: list[dict]) -> dict:
    """랭킹별 상위 종목 묶음 반환."""
    n = C.TOP_N
    gainers = sorted(rows, key=lambda r: r["day_change"], reverse=True)[:n]
    losers = sorted(rows, key=lambda r: r["day_change"])[:n]
    vol_surge = sorted(rows, key=lambda r: r["vol_ratio"], reverse=True)[:n]
    volatile = sorted(rows, key=lambda r: r["atr_pct"], reverse=True)[:n]
    recommend = sorted(
        [r for r in rows if r["signal"] == "BUY"],
        key=lambda r: (r["score"], r["day_change"]), reverse=True)[:n]
    return {"gainers": gainers, "losers": losers, "vol_surge": vol_surge,
            "volatile": volatile, "recommend": recommend}
