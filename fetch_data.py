"""抓取加密貨幣與台股日 K，輸出到 data/crypto.json、data/tw.json。
由 GitHub Actions 定時執行；也可以在自己電腦上執行：pip install yfinance && python fetch_data.py
"""
import datetime as dt
import json
import os
import re
import time
import urllib.request

import yfinance as yf

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "data")
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
BARS = 200  # 至少要 60 根才算得出 MA60，多抓一些讓圖上有完整均線

STABLES = {"USDC", "FDUSD", "TUSD", "DAI", "USDP", "BUSD", "EUR", "USDE", "PYUSD",
           "AEUR", "EURI", "XUSD", "USD1", "BFUSD", "RLUSD", "U", "PAXG", "WBTC", "WBETH"}

# 台股清單抓不到時的備用名單
TW_FALLBACK = ["2330", "2317", "2454", "2308", "2382", "3711", "2303", "2881", "2882",
               "2891", "2412", "2357", "3231", "2345", "6669", "3008", "2603", "1301"]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ma-scanner"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def save(name, items):
    os.makedirs(OUT, exist_ok=True)
    payload = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "items": items}
    with open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{name}: {len(items)} 檔")


def r(x):
    return float(f"{x:.6g}")


# ---------------- 加密貨幣（Binance 公開行情） ----------------
def crypto():
    base = "https://data-api.binance.vision/api/v3"
    tick = get_json(base + "/ticker/24hr")
    rows = []
    for t in tick:
        s = t["symbol"]
        if not s.endswith("USDT"):
            continue
        coin = s[:-4]
        if coin in STABLES or re.search(r"(UP|DOWN|BULL|BEAR)$", coin):
            continue
        if float(t["quoteVolume"]) <= 0 or int(t.get("count", 0)) == 0:
            continue
        rows.append(t)
    rows.sort(key=lambda t: float(t["quoteVolume"]), reverse=True)
    syms = [t["symbol"] for t in rows[: CFG["crypto_top_n"]]]
    for s in CFG.get("crypto_extra", []):
        if s not in syms:
            syms.append(s)

    items = []
    for s in syms:
        try:
            k = get_json(f"{base}/klines?symbol={s}&interval=1d&limit={BARS}")
        except Exception as e:  # noqa: BLE001
            print("skip", s, e)
            continue
        candles = [[dt.datetime.fromtimestamp(x[0] / 1000, dt.timezone.utc).strftime("%Y-%m-%d"),
                    r(float(x[1])), r(float(x[2])), r(float(x[3])), r(float(x[4])), round(float(x[7]))]
                   for x in k]
        if len(candles) > 61:
            items.append({"symbol": s, "name": s[:-4] + "/USDT", "candles": candles})
        time.sleep(0.05)
    save("crypto", items)


# ---------------- 台股（上市，依成交值排序） ----------------
def tw():
    names = {}
    try:
        d = get_json("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL")
        d = [x for x in d if re.fullmatch(r"\d{4}", x.get("Code", ""))]

        def val(x):
            try:
                return float(str(x.get("TradeValue", "0")).replace(",", ""))
            except ValueError:
                return 0.0

        d.sort(key=val, reverse=True)
        codes = [x["Code"] for x in d[: CFG["tw_top_n"]]]
        names = {x["Code"]: x["Name"] for x in d}
    except Exception as e:  # noqa: BLE001
        print("TWSE 清單抓取失敗，改用備用名單：", e)
        codes = list(TW_FALLBACK)

    tickers = [c + ".TW" for c in codes]
    for t in CFG.get("tw_extra", []):  # 例如 "6488.TWO"（上櫃要加 .TWO）
        t = t if "." in t else t + ".TW"
        if t not in tickers:
            tickers.append(t)
    names.update(CFG.get("tw_names", {}))

    df = yf.download(tickers, period="1y", interval="1d", group_by="ticker",
                     auto_adjust=False, progress=False, threads=True)
    items = []
    for t in tickers:
        try:
            sub = df[t].dropna(subset=["Open", "High", "Low", "Close"])
        except KeyError:
            continue
        sub = sub.tail(BARS)
        candles = [[idx.strftime("%Y-%m-%d"), r(row.Open), r(row.High), r(row.Low), r(row.Close),
                    int(row.Volume) if row.Volume == row.Volume else 0]
                   for idx, row in sub.iterrows()]
        if len(candles) > 61:
            code = t.split(".")[0]
            items.append({"symbol": t, "name": names.get(code, code), "candles": candles})
    save("tw", items)


if __name__ == "__main__":
    for job in (crypto, tw):
        try:
            job()
        except Exception as e:  # noqa: BLE001
            print(job.__name__, "失敗：", e)
