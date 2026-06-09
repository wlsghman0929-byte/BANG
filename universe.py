"""universe.py — 스캔 대상 종목(티커+회사명)을 시장별로 가져온다.

- 미국: 러셀1000 / S&P500 / 나스닥100 (Wikipedia 표) 동적 수집 + 정적 폴백.
- 한국: 코스피200 / 코스피 / 코스닥 (pykrx) 동적 수집 + 정적 폴백.

get_universe(market, name, custom) -> (tickers, names, source)
"""
from __future__ import annotations

# ---------------------- 미국 폴백 (티커 -> 회사명) ----------------------
US_FALLBACK = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "AMZN": "Amazon",
    "GOOGL": "Alphabet A", "GOOG": "Alphabet C", "META": "Meta Platforms",
    "TSLA": "Tesla", "AVGO": "Broadcom", "JPM": "JPMorgan Chase", "LLY": "Eli Lilly",
    "V": "Visa", "UNH": "UnitedHealth", "XOM": "Exxon Mobil", "MA": "Mastercard",
    "COST": "Costco", "HD": "Home Depot", "PG": "Procter & Gamble",
    "JNJ": "Johnson & Johnson", "WMT": "Walmart", "NFLX": "Netflix",
    "BAC": "Bank of America", "CRM": "Salesforce", "ORCL": "Oracle", "MRK": "Merck",
    "ABBV": "AbbVie", "CVX": "Chevron", "KO": "Coca-Cola", "AMD": "AMD",
    "PEP": "PepsiCo", "ADBE": "Adobe", "WFC": "Wells Fargo", "TMO": "Thermo Fisher",
    "LIN": "Linde", "ACN": "Accenture", "MCD": "McDonald's", "CSCO": "Cisco",
    "ABT": "Abbott", "DHR": "Danaher", "INTC": "Intel", "TXN": "Texas Instruments",
    "QCOM": "Qualcomm", "DIS": "Walt Disney", "INTU": "Intuit", "VZ": "Verizon",
    "CMCSA": "Comcast", "PM": "Philip Morris", "IBM": "IBM", "CAT": "Caterpillar",
    "GE": "GE Aerospace", "NOW": "ServiceNow", "UNP": "Union Pacific",
    "AMGN": "Amgen", "SPGI": "S&P Global", "NKE": "Nike", "HON": "Honeywell",
    "COP": "ConocoPhillips", "UPS": "United Parcel", "LOW": "Lowe's", "BA": "Boeing",
    "RTX": "RTX", "ELV": "Elevance Health", "T": "AT&T", "BKNG": "Booking",
    "SBUX": "Starbucks", "DE": "Deere", "PLD": "Prologis", "MDT": "Medtronic",
    "GILD": "Gilead", "LMT": "Lockheed Martin", "BLK": "BlackRock", "ADP": "ADP",
    "MU": "Micron", "PLTR": "Palantir", "COIN": "Coinbase", "SHOP": "Shopify",
    "UBER": "Uber", "ABNB": "Airbnb", "SNOW": "Snowflake", "CRWD": "CrowdStrike",
    "NET": "Cloudflare", "PYPL": "PayPal",
}

# ---------------------- 한국 폴백 (종목코드 -> 종목명) ----------------------
KR_FALLBACK = {
    "005930": "삼성전자", "000660": "SK하이닉스", "373220": "LG에너지솔루션",
    "207940": "삼성바이오로직스", "005380": "현대차", "000270": "기아",
    "005490": "POSCO홀딩스", "035420": "NAVER", "035720": "카카오",
    "051910": "LG화학", "006400": "삼성SDI", "028260": "삼성물산",
    "105560": "KB금융", "055550": "신한지주", "012330": "현대모비스",
    "068270": "셀트리온", "003670": "포스코퓨처엠", "066570": "LG전자",
    "015760": "한국전력", "034730": "SK", "032830": "삼성생명",
    "003550": "LG", "017670": "SK텔레콤", "030200": "KT",
    "009150": "삼성전기", "086790": "하나금융지주", "011200": "HMM",
    "010130": "고려아연", "024110": "기업은행", "316140": "우리금융지주",
    "033780": "KT&G", "090430": "아모레퍼시픽", "047810": "한국항공우주",
    "010950": "S-Oil", "096770": "SK이노베이션", "018260": "삼성에스디에스",
    "011170": "롯데케미칼", "161390": "한국타이어앤테크놀로지",
    "036570": "엔씨소프트", "251270": "넷마블", "259960": "크래프톤",
    "247540": "에코프로비엠", "086520": "에코프로", "196170": "알테오젠",
    "028300": "HLB", "095340": "ISC", "058470": "리노공업",
}


# ---------------------- 미국 동적 수집 ----------------------
def _us_tables(url, sym_cands, name_cands):
    import pandas as pd
    tables = pd.read_html(url)
    for t in tables:
        cols = [str(c) for c in t.columns]
        sym_col = name_col = None
        for c in cols:
            cl = c.lower()
            if sym_col is None and any(s.lower() in cl for s in sym_cands):
                sym_col = c
            if name_col is None and any(s.lower() in cl for s in name_cands):
                name_col = c
        if sym_col is not None:
            t.columns = cols
            syms = (t[sym_col].astype(str).str.strip().str.upper()
                    .str.replace(".", "-", regex=False))
            names = (t[name_col].astype(str).str.strip()
                     if name_col is not None else syms)
            pairs = [(s, nm if nm and nm != "nan" else s)
                     for s, nm in zip(syms.tolist(), names.tolist())
                     if s and s != "NAN" and len(s) <= 6]
            if len(pairs) > 50:
                return pairs
    return []


def _get_us(name, custom):
    name = (name or "").lower()
    if name == "custom":
        tk = list(dict.fromkeys(custom or []))
        return tk, {t: US_FALLBACK.get(t, t) for t in tk}, "US/custom"
    urls = {
        "sp500": [("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                   ["Symbol", "Ticker"], ["Security", "Company"])],
        "sp500+nasdaq100": [
            ("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
             ["Symbol", "Ticker"], ["Security", "Company"]),
            ("https://en.wikipedia.org/wiki/Nasdaq-100",
             ["Ticker", "Symbol"], ["Company", "Security"])],
        "russell1000": [("https://en.wikipedia.org/wiki/Russell_1000_Index",
                         ["Symbol", "Ticker"], ["Company", "Security", "Name"])],
    }
    spec = urls.get(name, urls["russell1000"])
    try:
        pairs = []
        for url, sc, nc in spec:
            pairs += _us_tables(url, sc, nc)
        if pairs:
            seen = {}
            for s, nm in pairs:
                seen.setdefault(s, nm)
            label = name if name in urls else "russell1000"
            return list(seen.keys()), seen, f"US/{label}(live)"
    except Exception as e:
        print(f"  미국 유니버스 동적 수집 실패 -> 폴백: {repr(e)[:80]}")
    return list(US_FALLBACK.keys()), dict(US_FALLBACK), "US/fallback"


# ---------------------- 한국 동적 수집 ----------------------
def _get_kr(name, custom):
    name = (name or "").lower()
    if name == "custom":
        tk = list(dict.fromkeys(custom or []))
        # 이름은 pykrx 로 시도, 실패 시 폴백/코드
        names = {}
        try:
            from pykrx import stock
            for c in tk:
                try:
                    names[c] = stock.get_market_ticker_name(c)
                except Exception:
                    names[c] = KR_FALLBACK.get(c, c)
        except Exception:
            names = {c: KR_FALLBACK.get(c, c) for c in tk}
        return tk, names, "KR/custom"
    try:
        from pykrx import stock
        codes = []
        if name == "kospi200":
            codes = stock.get_index_portfolio_deposit_file("1028")  # KOSPI200
        elif name == "kospi":
            codes = stock.get_market_ticker_list(market="KOSPI")
        elif name == "kosdaq":
            codes = stock.get_market_ticker_list(market="KOSDAQ")
        elif name == "kospi+kosdaq":
            codes = (stock.get_market_ticker_list(market="KOSPI")
                     + stock.get_market_ticker_list(market="KOSDAQ"))
        if codes:
            names = {}
            for c in codes:
                try:
                    names[c] = stock.get_market_ticker_name(c)
                except Exception:
                    names[c] = c
            return list(codes), names, f"KR/{name}(live)"
    except Exception as e:
        print(f"  한국 유니버스 동적 수집 실패 -> 폴백: {repr(e)[:80]}")
    return list(KR_FALLBACK.keys()), dict(KR_FALLBACK), "KR/fallback"


def get_universe(market: str, name: str, custom: list[str] | None = None):
    if market.upper() == "KR":
        return _get_kr(name, custom)
    return _get_us(name, custom)
