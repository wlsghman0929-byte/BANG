"""run_scanner.py — 시장 스캐너 자동 갱신 실행기

  python run_scanner.py

동작:
  1) 유니버스(러셀1000 등) 종목 목록 수집
  2) yfinance 로 시세 대량 다운로드 → 등락/거래량/변동성/추천 계산
  3) scan_dashboard.html 생성
  4) REFRESH_MINUTES 분 대기 후 1~3 반복 (Ctrl+C 로 종료)

브라우저에서 scan_dashboard.html 을 열어두면 AUTO_RELOAD_SECONDS 마다
자동 새로고침되어 최신 결과가 반영됩니다.
"""
from __future__ import annotations
import sys
import time
import json
import datetime as dt

import scan_config as C
import universe
import scanner
import scan_dashboard


OUT = "scan_dashboard.html"
UNI_NAME = {"US": C.US_UNIVERSE, "KR": C.KR_UNIVERSE}
UNI_CUSTOM = {"US": C.US_CUSTOM_TICKERS, "KR": C.KR_CUSTOM_TICKERS}


def one_cycle():
    markets = {}
    for mk in C.MARKETS:
        name = UNI_NAME[mk]
        tickers, names, usrc = universe.get_universe(mk, name, UNI_CUSTOM[mk])
        if C.MAX_TICKERS:
            tickers = tickers[:C.MAX_TICKERS]
        print(f"[{mk}] 유니버스: {usrc} / {len(tickers)}종목")
        rows, dsrc = scanner.scan(mk, tickers, names)
        ranked = scanner.rank(rows)
        if mk == "US":
            try:
                scanner.finnhub_overlay(ranked)
            except Exception as e:
                print(f"  [Finnhub] overlay 오류: {repr(e)[:80]}")
        markets[mk] = {
            "market": mk,
            "universe": usrc,
            "universe_size": len(tickers),
            "n_analyzed": len(rows),
            "data_mode": "데모(합성)" if dsrc == "demo" else "실데이터",
            "ranked": ranked,
        }

    meta = {
        "generated": dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S KST"),
        "fast": C.FAST_MA, "slow": C.SLOW_MA,
        "big_move": C.BIG_MOVE_PCT,
        "vol_surge": C.VOL_SURGE_MULT,
        "market_order": list(markets.keys()),
    }
    html = scan_dashboard.build_html(meta, markets, C.AUTO_RELOAD_SECONDS)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "markets": markets}, f, ensure_ascii=False, indent=2)
    summary = ", ".join(f"{m}:{markets[m]['n_analyzed']}개({markets[m]['data_mode']})"
                        for m in markets)
    print(f"→ {OUT} 생성 완료 [{summary}]")


def main():
    print("=" * 60)
    print(" Market Scanner 시작 — Ctrl+C 로 종료")
    print(f" 갱신 주기: {C.REFRESH_MINUTES}분 / 브라우저 새로고침: {C.AUTO_RELOAD_SECONDS}초")
    print("=" * 60)
    cycle = 0
    while True:
        cycle += 1
        print(f"\n[사이클 {cycle}] {dt.datetime.now():%H:%M:%S}")
        try:
            one_cycle()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"  사이클 오류(다음 주기에 재시도): {repr(e)[:120]}")
        try:
            time.sleep(C.REFRESH_MINUTES * 60)
        except KeyboardInterrupt:
            print("\n종료합니다.")
            break


if __name__ == "__main__":
    # 클라우드(예: GitHub Actions)에서는 1회만 실행: python run_scanner.py --once
    if "--once" in sys.argv:
        one_cycle()
    else:
        try:
            main()
        except KeyboardInterrupt:
            print("\n종료합니다.")
