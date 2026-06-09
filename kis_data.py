"""kis_data.py — 한국투자증권(KIS) Open API 실시간 현재가 조회

용도: 일봉(pykrx)은 그대로 두고, KR 종목의 '현재가'만 KIS 실시간 시세로 보강.

사용 준비:
  1) KIS 계좌 개설 후 https://apiportal.koreainvestment.com 에서 개발자 등록
  2) 앱키(APP KEY) / 앱시크릿(APP SECRET) 발급
  3) scan_config.py 에 키 입력하고 USE_KIS_REALTIME = True 로 설정

키가 없거나 오류가 나면 모든 함수가 None 을 반환해 자동으로 pykrx 만 사용합니다.
표준 라이브러리(urllib)만 사용하므로 추가 설치가 필요 없습니다.
"""
from __future__ import annotations
import json
import time
import os
import urllib.request

import scan_config as C

_REAL = "https://openapi.koreainvestment.com:9443"
_VPS = "https://openapivts.koreainvestment.com:29443"
_TOKEN_FILE = os.path.join(os.path.dirname(__file__), ".kis_token.json")


def _base() -> str:
    return _VPS if getattr(C, "KIS_ENV", "real") == "vps" else _REAL


def enabled() -> bool:
    return bool(getattr(C, "USE_KIS_REALTIME", False)
               and getattr(C, "KIS_APP_KEY", "") and getattr(C, "KIS_APP_SECRET", ""))


def _post_json(url, headers, body, timeout=10):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _get_json(url, headers, timeout=10):
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _get_token() -> str | None:
    """액세스 토큰 발급(약 24시간 유효). 파일에 캐시해 재사용."""
    try:
        if os.path.exists(_TOKEN_FILE):
            cached = json.load(open(_TOKEN_FILE, encoding="utf-8"))
            if cached.get("expire", 0) > time.time() + 300 and cached.get("token"):
                return cached["token"]
    except Exception:
        pass
    try:
        res = _post_json(
            _base() + "/oauth2/tokenP",
            {"content-type": "application/json"},
            {"grant_type": "client_credentials",
             "appkey": C.KIS_APP_KEY, "appsecret": C.KIS_APP_SECRET},
        )
        token = res.get("access_token")
        if not token:
            return None
        expires = int(res.get("expires_in", 86400))
        try:
            json.dump({"token": token, "expire": time.time() + expires},
                      open(_TOKEN_FILE, "w", encoding="utf-8"))
        except Exception:
            pass
        return token
    except Exception as e:
        print(f"  [KIS] 토큰 발급 실패: {repr(e)[:90]}")
        return None


def get_price(code: str) -> float | None:
    """종목코드의 현재가(원) 반환. 실패 시 None."""
    if not enabled():
        return None
    token = _get_token()
    if not token:
        return None
    try:
        url = (_base() + "/uapi/domestic-stock/v1/quotations/inquire-price"
               "?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD=" + code)
        headers = {
            "content-type": "application/json",
            "authorization": "Bearer " + token,
            "appkey": C.KIS_APP_KEY,
            "appsecret": C.KIS_APP_SECRET,
            "tr_id": "FHKST01010100",
            "custtype": "P",
        }
        res = _get_json(url, headers)
        out = res.get("output") or {}
        px = out.get("stck_prpr")  # 주식 현재가
        return float(px) if px not in (None, "", "0") else None
    except Exception as e:
        print(f"  [KIS] {code} 현재가 조회 실패: {repr(e)[:90]}")
        return None
