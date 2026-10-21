# Created by 青云 on 2026/10/21.
"""Game Deals 数据抓取：Epic 限免、全平台喜加一、Steam 国区特惠 + 史低、Steam 大促日历、PS Plus / Game Pass。只用标准库。

输出 data.json 和 sales.ics（Steam 大促 + Epic 每周限免更新提醒）。
"""
import gzip, html, json, re, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data.json"
CST = timezone(timedelta(hours=8))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
API_UA = "GameDeals/1.0 (https://github.com/climb0516/game-deals)"     # CheapShark 要求能识别的 UA
STEAM_PAGES = 3                     # Steam 热销特惠取前 300 条
PRICE_DAYS = 120                    # 国区价格历史保留天数


def fetch(url, timeout=25, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "ignore")


def utc_iso(s):
    """各接口的时间统一成带时区的 ISO（北京时间）。"""
    if not s or s == "N/A":
        return None
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CST).isoformat(timespec="minutes")


# ── Epic：本周限免 + 下周预告（国区价格）──────────────────
def epic():
    d = json.loads(fetch("https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=zh-CN&country=CN&allowCountries=CN"))
    out = []
    for x in d["data"]["Catalog"]["searchStore"]["elements"]:
        p = x.get("promotions") or {}
        for kind, key in (("now", "promotionalOffers"), ("next", "upcomingPromotionalOffers")):
            for g in p.get(key) or []:
                for o in g["promotionalOffers"]:
                    if o["discountSetting"]["discountPercentage"] != 0:     # 0 = 折后价为 0，即限免；其余是普通打折
                        continue
                    slug = next((m["pageSlug"] for m in (x.get("catalogNs") or {}).get("mappings") or [] if m.get("pageType") == "productHome"), None) \
                        or x.get("productSlug") or x.get("urlSlug")
                    img = next((i["url"] for t in ("OfferImageWide", "DieselStoreFrontWide", "Thumbnail") for i in x["keyImages"] if i["type"] == t), "")
                    out.append({"title": x["title"], "kind": kind, "start": utc_iso(o["startDate"]), "end": utc_iso(o["endDate"]),
                                "worth": x["price"]["totalPrice"]["originalPrice"] / 100, "img": img,
                                "url": f"https://store.epicgames.com/zh-CN/p/{slug}" if slug else "https://store.epicgames.com/zh-CN/free-games",
                                "desc": (x.get("description") or "")[:160]})
    return sorted(out, key=lambda r: (r["kind"] != "now", r["start"] or ""))


# ── GamerPower：全平台喜加一（游戏 + 道具礼包）────────────
PLATFORM_MAP = [("Steam", "Steam"), ("Epic", "Epic"), ("GOG", "GOG"), ("Ubisoft", "Ubisoft"), ("Itch", "itch.io"),
                ("Indiegala", "IndieGala"), ("PlayStation", "PlayStation"), ("PS4", "PlayStation"), ("PS5", "PlayStation"),
                ("Xbox", "Xbox"), ("Switch", "Switch"), ("Android", "手机"), ("iOS", "手机"), ("Prime", "Prime Gaming")]


def gamerpower():
    d = json.loads(fetch("https://www.gamerpower.com/api/giveaways?sort-by=date"))
    out = []
    for x in d:
        plats = sorted({v for k, v in PLATFORM_MAP if k.lower() in x["platforms"].lower()}) or ["其他"]
        out.append({"id": x["id"], "title": re.sub(r"\s*\((?:[^()]*)\)\s*Giveaway$|\s*Giveaway$", "", x["title"]),
                    "type": "game" if x["type"] == "Game" else "loot", "platforms": plats,
                    "worth": x["worth"] if x["worth"] != "N/A" else "", "end": utc_iso(x["end_date"]),
                    "img": x["thumbnail"], "url": x["open_giveaway_url"], "users": x["users"],
                    "published": utc_iso(x["published_date"])})
    return out


# ── Steam：热销特惠前 300（国区人民币）────────────────────
def steam_specials():
    out = []
    for page in range(STEAM_PAGES):
        q = urllib.parse.urlencode({"query": "", "start": page * 100, "count": 100, "specials": 1, "filter": "topsellers",
                                    "infinite": 1, "cc": "cn", "l": "schinese", "category1": 998})
        d = json.loads(fetch("https://store.steampowered.com/search/results/?" + q,
                             headers={"Cookie": "birthtime=0; wants_mature_content=1"}))
        for row in re.split(r'<a href="https://store\.steampowered\.com/app/', d["results_html"])[1:]:
            appid = re.search(r'data-ds-appid="(\d+)"', row)
            title = re.search(r'<span class="title">([^<]+)', row)
            disc = re.search(r'data-discount="(\d+)"', row)
            final = re.search(r'data-price-final="(\d+)"', row)
            orig = re.search(r'discount_original_price">¥\s*([\d,.]+)', row)
            if not (appid and title and disc and final):
                continue
            review = re.search(r'search_review_summary (\w+)" data-tooltip-html="([^&"]+)&lt;br&gt;[^"]*?(\d+)% 为好评', row)
            nrev = re.search(r'中有\s*([\d,]+)\s*篇|的\s*([\d,]+)\s*篇用户评测', html.unescape(row))
            rel = re.search(r'search_released[^>]*>\s*([^<]+?)\s*<', row)
            img = re.search(r'<img src="([^"]+)"', row)
            out.append({"appid": int(appid.group(1)), "title": html.unescape(title.group(1)).strip(), "discount": int(disc.group(1)),
                        "price": int(final.group(1)) / 100, "orig": float(orig.group(1).replace(",", "")) if orig else None,
                        "review": html.unescape(review.group(2)) if review else "", "rate": int(review.group(3)) if review else None,
                        "reviews": int((nrev.group(1) or nrev.group(2)).replace(",", "")) if nrev else None,
                        "released": rel.group(1) if rel else "", "img": img.group(1) if img else "", "rank": len(out) + 1})
        time.sleep(1.5)
    if not out:
        raise ValueError("empty")
    return out


# ── CheapShark：美区史低（按 Steam appid 逐个查编号，再批量取史低）──
LOW_TOP = 120                       # 只查热销前 120（每个 appid 一次请求，限速）


def cheapshark_lows(steam, cache):
    """cache: appid -> CheapShark gameID（找不到记 ""），跨次运行复用，减少请求。"""
    hdr = {"User-Agent": API_UA}
    for g in steam[:LOW_TOP]:
        k = str(g["appid"])
        if k in cache:
            continue
        r = json.loads(fetch(f"https://www.cheapshark.com/api/1.0/games?steamAppID={k}&limit=1", headers=hdr))
        cache[k] = r[0]["gameID"] if r else ""
        time.sleep(0.6)
    want = {cache[str(g["appid"])]: str(g["appid"]) for g in steam[:LOW_TOP] if cache.get(str(g["appid"]))}
    ids, out = list(want), {}
    for i in range(0, len(ids), 25):
        info = json.loads(fetch("https://www.cheapshark.com/api/1.0/games?ids=" + ",".join(ids[i:i + 25]), headers=hdr))
        for gid, v in info.items():
            cur = next((float(d["price"]) for d in v.get("deals", []) if d["storeID"] == "1"), None)
            if cur is None:
                continue
            out[want[gid]] = {"usd": cur, "usd_low": float(v["cheapestPriceEver"]["price"]), "usd_low_date": v["cheapestPriceEver"]["date"]}
        time.sleep(1)
    if not out:
        raise ValueError("empty")
    return out


# ── Steam 官方大促日历（Steamworks 文档）─────────────────
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                      "September", "October", "November", "December"], 1)}
SALE_CN = {"Winter Sale": "冬季特卖", "Spring Sale": "春季特卖", "Summer Sale": "夏季特卖", "Autumn Sale": "秋季特卖",
           "Next Fest": "新品节", "Lunar New Year": "农历新年特卖"}


def steam_events():
    raw = fetch("https://partner.steamgames.com/doc/marketing/upcoming_events?l=english",
                headers={"Accept-Language": "en-US,en;q=0.9"})
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))
    name_pat = r"((?:Steam )?[A-Z][A-Za-z' :&-]{2,60}?(?:Sale|Fest|Festival)(?: \d{4})?(?:: [A-Za-z]+ \d{4})?)"
    # 两种日期写法：「17 December, 2026」或「December 17, 2026」
    date_dm = r"(\d{1,2}) ([A-Z][a-z]+),? (\d{4})"
    date_md = r"([A-Z][a-z]+) (\d{1,2}),? (\d{4})"
    out = []
    for dp, order in ((date_dm, "dm"), (date_md, "md")):
        for m in re.finditer(name_pat + r" \| " + dp + r" ?[-–] ?" + dp, t):
            name, a1, b1, y1, a2, b2, y2 = m.groups()
            (d1, m1), (d2, m2) = ((a1, b1), (a2, b2)) if order == "dm" else ((b1, a1), (b2, a2))
            if m1 not in MONTHS or m2 not in MONTHS:
                continue
            cn = next((v for k, v in SALE_CN.items() if k in name), "")
            out.append({"name": name.strip(), "cn": cn, "start": f"{y1}-{MONTHS[m1]:02d}-{int(d1):02d}",
                        "end": f"{y2}-{MONTHS[m2]:02d}-{int(d2):02d}"})
    uniq = {(e["name"], e["start"]): e for e in out}
    if not uniq:
        # 诊断：把「Sale」附近的原文带进错误信息，便于看 Actions 上拿到的页面
        i = t.find("Sale")
        raise ValueError(f"empty, len={len(raw)}, near Sale: {t[max(0, i - 60):i + 80] if i >= 0 else t[:140]}")
    return sorted(uniq.values(), key=lambda e: e["start"])


# ── PS Plus：官方博客 RSS 里的每月游戏 / 游戏目录 ─────────
def ps_plus():
    t = fetch("https://blog.playstation.com/tag/playstation-plus/feed/")
    out = []
    for it in re.findall(r"<item>(.*?)</item>", t, re.S):
        title = html.unescape(re.search(r"<title>(.*?)</title>", it, re.S).group(1)).strip()
        m = re.match(r"PlayStation Plus (Monthly Games|Game Catalog) for (\w+)\s*[:–-]\s*(.+)", title)
        if not m:
            continue
        games = [g.strip() for g in re.split(r",\s*|\s+and\s+", re.sub(r"\s+and more$", "", m.group(3))) if g.strip()]
        pub = datetime.strptime(re.search(r"<pubDate>(.*?)</pubDate>", it).group(1)[:25].strip(), "%a, %d %b %Y %H:%M:%S")
        out.append({"kind": "monthly" if m.group(1) == "Monthly Games" else "catalog", "month": m.group(2), "games": games,
                    "more": title.endswith("and more"), "date": pub.date().isoformat(),
                    "url": re.search(r"<link>(.*?)</link>", it).group(1).strip()})
    if not out:
        raise ValueError("empty")
    return out[:6]


# ── Xbox Game Pass：最近新增（港区，中文名）───────────────
def game_pass():
    ids = [x["id"] for x in json.loads(fetch("https://catalog.gamepass.com/sigls/v2?id=f13cf6b4-57e6-4459-89df-6aec18cf0538&language=zh-cn&market=HK")) if "id" in x][:24]
    d = json.loads(fetch(f"https://displaycatalog.mp.microsoft.com/v7.0/products?bigIds={','.join(ids)}&market=HK&languages=zh-hk"))
    order = {pid: i for i, pid in enumerate(ids)}
    out = []
    for p in d["Products"]:
        L = p["LocalizedProperties"][0]
        img = next((i["Uri"] for t in ("BoxArt", "Poster", "SuperHeroArt") for i in L["Images"] if i["ImagePurpose"] == t), "")
        out.append({"id": p["ProductId"], "title": L["ProductTitle"], "img": ("https:" + img) if img.startswith("//") else img,
                    "released": (p.get("MarketProperties") or [{}])[0].get("OriginalReleaseDate", "")[:10],
                    "url": f'https://www.xbox.com/zh-HK/games/store/_/{p["ProductId"]}'})
    if not out:
        raise ValueError("empty")
    return sorted(out, key=lambda r: order.get(r["id"], 99))


# ── ICS：Steam 大促 + Epic 每周四限免更新 ─────────────────
def ics(events, epic_now, today):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    esc = lambda s: s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//game-deals//CN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:Game Deals · 大促与限免", "X-WR-TIMEZONE:Asia/Shanghai", "REFRESH-INTERVAL;VALUE=DURATION:PT12H"]
    for e in events:
        end = (datetime.fromisoformat(e["end"]) + timedelta(days=1)).strftime("%Y%m%d")
        L += ["BEGIN:VEVENT", f'UID:steam-{e["start"]}-{re.sub(r"[^A-Za-z0-9]", "", e["name"])}@game-deals', f"DTSTAMP:{stamp}",
              f'DTSTART;VALUE=DATE:{e["start"].replace("-", "")}', f"DTEND;VALUE=DATE:{end}",
              f'SUMMARY:{esc("🎮 Steam " + (e["cn"] or e["name"]))}', f'DESCRIPTION:{esc(e["name"])}',
              "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-P1D", f'DESCRIPTION:{esc("明天开始 Steam " + (e["cn"] or e["name"]))}', "END:VALARM",
              "END:VEVENT"]
    # Epic 限免每周四 23:00（北京时间）更新；只放当前这一期的结束时间，避免写死规律
    for g in epic_now:
        if g["end"]:
            t = datetime.fromisoformat(g["end"]).astimezone(timezone.utc)
            L += ["BEGIN:VEVENT", f'UID:epic-{t.strftime("%Y%m%d")}@game-deals', f"DTSTAMP:{stamp}",
                  f'DTSTART:{(t - timedelta(hours=1)).strftime("%Y%m%dT%H%M%SZ")}', f'DTEND:{t.strftime("%Y%m%dT%H%M%SZ")}',
                  f'SUMMARY:{esc("🎁 Epic 本周限免即将结束，记得领取")}',
                  f'DESCRIPTION:{esc("、".join(x["title"] for x in epic_now))}',
                  "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-PT3H", "DESCRIPTION:Epic 限免还剩 4 小时", "END:VALARM", "END:VEVENT"]
            break
    L.append("END:VCALENDAR")
    return "\r\n".join(L) + "\r\n"


def main():
    now = datetime.now(CST)
    stamp = now.isoformat(timespec="seconds")
    today = now.date().isoformat()
    old = json.loads(DATA_FILE.read_text("utf-8")) if DATA_FILE.exists() else {}
    sources = []

    def run(name, fn, key, count=len):
        try:
            v = fn()
            sources.append({"name": name, "ok": True, "count": count(v), "updated": stamp})
            return v
        except Exception as e:
            prev = next((s for s in old.get("sources", []) if s["name"] == name), {})
            sources.append({"name": name, "ok": False, "error": str(e)[:300], "updated": prev.get("updated")})
            print("FAIL", name, e)
            return old.get(key)

    ep = run("Epic 限免", epic, "epic") or []
    gp = run("GamerPower 喜加一", gamerpower, "giveaways") or []
    st = run("Steam 国区特惠", steam_specials, "steam") or []
    cs_cache = old.get("_cs_ids", {})
    lows = run("CheapShark 美区史低", lambda: cheapshark_lows(st, cs_cache), "_lows") or {}
    ev = run("Steam 大促日历", steam_events, "events") or []
    ps = run("PS Plus 博客", ps_plus, "ps_plus") or []
    gpass = run("Xbox Game Pass", game_pass, "game_pass") or []

    # 国区价格历史：每天保留当天最后一次价格（appid -> {date: price}），用来判断「国区近 N 天最低」
    hist = old.get("price_history", {})
    for g in st:
        h = hist.setdefault(str(g["appid"]), {})
        h[today] = g["price"]
    cutoff = (now.date() - timedelta(days=PRICE_DAYS)).isoformat()
    live = {str(g["appid"]) for g in st}
    hist = {k: {d: p for d, p in v.items() if d >= cutoff} for k, v in hist.items()}
    hist = {k: v for k, v in hist.items() if v and (k in live or max(v) >= (now.date() - timedelta(days=30)).isoformat())}

    for g in st:
        lo = lows.get(str(g["appid"]))
        g["usd_low"] = bool(lo and lo["usd"] <= lo["usd_low"] + 0.001)      # 美区当前价已到史低
        g["usd"], g["usd_lowest"] = (lo["usd"], lo["usd_low"]) if lo else (None, None)
        h = hist.get(str(g["appid"]), {})
        g["cn_days"] = len(h)
        g["cn_low"] = bool(len(h) >= 7 and g["price"] <= min(h.values()))      # 至少记录 7 天后才判断国区新低

    data = {
        "updated": stamp,               # 每次都变 = 心跳，保证每次运行都有提交
        "epic": ep,
        "giveaways": gp,
        "steam": st,
        "events": ev,
        "ps_plus": ps,
        "game_pass": gpass,
        "summary": {                    # 给 pages-dashboard 用，字段只增不减
            "epic_now": [g["title"] for g in ep if g["kind"] == "now"],
            "epic_now_worth": round(sum(g["worth"] for g in ep if g["kind"] == "now"), 2),
            "epic_end": min((g["end"] for g in ep if g["kind"] == "now" and g["end"]), default=None),
            "epic_next": [g["title"] for g in ep if g["kind"] == "next"],
            "giveaway_games": sum(1 for g in gp if g["type"] == "game"),
            "steam_lows": sum(1 for g in st if g["usd_low"] or g["cn_low"]),
            "next_sale": next(({"name": e["cn"] or e["name"], "start": e["start"], "end": e["end"]} for e in ev if e["end"] >= today), None),
        },
        "_lows": lows,
        "_cs_ids": cs_cache,
        "price_history": hist,
        "sources": sources,
    }
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), "utf-8")
    (ROOT / "sales.ics").write_text(ics([e for e in ev if e["end"] >= today], [g for g in ep if g["kind"] == "now"], today), "utf-8")
    print("epic", [(g["title"], g["kind"]) for g in ep])
    print("giveaways", len(gp), "steam", len(st), "usd_low", sum(g["usd_low"] for g in st), "lows matched", sum(1 for g in st if str(g["appid"]) in lows))
    print("events", [(e["cn"] or e["name"], e["start"], e["end"]) for e in ev])
    print("ps", [(p["kind"], p["month"], p["games"][:3]) for p in ps[:2]], "gamepass", [g["title"] for g in gpass[:5]])
    print("failed", [s["name"] for s in sources if not s["ok"]])


if __name__ == "__main__":
    main()
