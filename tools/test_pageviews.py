#!/usr/bin/env python3
"""
test_pageviews.py — 測試 GoatCounter 頁面瀏覽計數是否正常更新

用法:
    python tools/test_pageviews.py <path> [--count N] [--site SITE_ID]

範例:
    python tools/test_pageviews.py /posts/my-post/
    python tools/test_pageviews.py /posts/my-post/ --count 5
    python tools/test_pageviews.py /posts/my-post/ --count 3 --site edwardwu
"""

import argparse
import json
import time
import urllib.request
import urllib.parse


def get_count(site_id: str, path: str) -> int | None:
    """從 GoatCounter public counter API 取得目前瀏覽數"""
    encoded = urllib.parse.quote(path, safe="")
    url = f"https://{site_id}.goatcounter.com/counter/{encoded}.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return int(data["count"].replace(",", "").replace(".", ""))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 0  # 路徑從未被記錄過，視為 0
        print(f"  [!] 無法讀取計數：{e}")
        return None
    except Exception as e:
        print(f"  [!] 無法讀取計數：{e}")
        return None


def send_pageview(site_id: str, path: str, referrer: str = "") -> bool:
    """對 GoatCounter 發送一次頁面瀏覽事件"""
    base_url = f"https://{site_id}.goatcounter.com/count"
    params = urllib.parse.urlencode({
        "p": path,
        "t": f"Test: {path}",
        "r": referrer,
        "s": "1280,800,2",   # screen size
        "b": "0",
        "q": "",
    })
    url = f"{base_url}?{params}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (test_pageviews.py)",
            "Referer": referrer or f"https://{site_id}.goatcounter.com",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"  [!] 發送失敗：{e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="測試 GoatCounter 頁面瀏覽計數")
    parser.add_argument("path", help="要測試的頁面路徑，例如 /posts/my-post/")
    parser.add_argument("--count", type=int, default=3, help="發送次數（預設 3）")
    parser.add_argument("--site", default="edwardwu", help="GoatCounter site ID（預設 edwardwu）")
    parser.add_argument("--delay", type=float, default=1.0, help="每次發送間隔秒數（預設 1.0）")
    args = parser.parse_args()

    path = args.path.rstrip("/") or "/"
    site_id = args.site

    print(f"站台：{site_id}.goatcounter.com")
    print(f"路徑：{path}")
    print(f"發送：{args.count} 次，間隔 {args.delay}s\n")

    before = get_count(site_id, path)
    if before is not None:
        print(f"發送前計數：{before}")
    else:
        print("發送前計數：無法取得（Public API 可能尚未啟用）")

    print()
    for i in range(1, args.count + 1):
        ok = send_pageview(site_id, path)
        status = "OK" if ok else "FAIL"
        print(f"  [{i}/{args.count}] {status}")
        if i < args.count:
            time.sleep(args.delay)

    print("\n等待 3 秒讓 GoatCounter 處理資料...")
    time.sleep(3)

    after = get_count(site_id, path)
    if after is not None:
        diff = after - before if before is not None else "?"
        print(f"發送後計數：{after}  （變化：+{diff}）")
        if isinstance(diff, int) and diff > 0:
            print("\n計數正常更新 ✓")
        else:
            print("\n計數未變化（正常）— GoatCounter 會對同一 IP 去重，Public API 有回應即代表設定正確")
    else:
        print("發送後計數：無法取得")


if __name__ == "__main__":
    main()
