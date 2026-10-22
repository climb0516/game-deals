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
# ── PlayStation 港服：官方商店 GraphQL（带港服 locale 头）+ PS Plus 官方中文页 ──────────
# 只接受前端白名单里的 persisted query；hash 失效时会报 PersistedQueryNotFound，让来源状态变红提醒更新
PS_GQL = "https://web.np.playstation.com/api/graphql/v1/op"
PS_HEAD = {"x-psn-store-locale-override": "zh-hans-hk", "content-type": "application/json", "Origin": "https://store.playstation.com", "Referer": "https://store.playstation.com/"}
PS_HASH = {
    "categoryGridRetrieve": ["4ce7d410a4db2c8b635a48c1dcec375906ff63b19dadd87e073f8fd0c0481d35",
                             "257713466fc3264850aa473409a29088e3a4115e6e69e9fb3e061c8dd5b9f5c6"],
    "productRetrieveForCtasWithPrice": ["8532da7eda369efdad054ca8f885394a2d0c22d03c5259a422ae2bb3b98c5c99"],
    "metGetConceptById": ["cc90404ac049d935afbd9968aef523da2b6723abfb9d586e5f77ebf7c5289006"],
    "metGetPricingDataByConceptId": ["abcb311ea830e679fe2b697a27f755764535d825b24510ab1239a4ca3092bd09"],
}
PS_CAT = {                                   # 港服常驻分类（活动分类会轮换，不用）
    "deals": "3f772501-f6f8-49b7-abac-874a88ca4897",     # 全部优惠
    "ps5": "d0446d4b-dc9a-4f1e-86ec-651f099c9b29",       # 全部 PS5 游戏
    "new": "e1699f77-77e1-43ca-a296-26d08abacb0f",       # 新游戏
    "f2p": "4dfd67ab-4ed7-40b0-a937-a549aece13d0",       # 免费游玩
    "preorder": "3bf499d7-7acf-4931-97dd-2667494ee2c9",  # 预购
}
PS_STORE = "https://store.playstation.com/zh-hans-hk"
PS_DEALS_N = 600                             # 优惠按 30 天销量取前 600
PS_ENRICH_N = 120                            # 其中前 120 个补截止时间 / 会员价 / 是否在游戏目录 / 详情
PS_LIST_N = 48                               # 畅销、下载、免费游玩、新游戏各取 48
PS_DETAIL_DAYS = 30                          # 游戏详情（发售日、发行商、截图…）缓存天数，价格每天更新


def ps_gql(op, variables):
    err = None
    for h in PS_HASH[op]:
        q = urllib.parse.urlencode({"operationName": op, "variables": json.dumps(variables, ensure_ascii=False),
                                    "extensions": json.dumps({"persistedQuery": {"version": 1, "sha256Hash": h}})})
        d = json.loads(fetch(f"{PS_GQL}?{q}", timeout=40, headers=PS_HEAD))
        if d.get("data"):
            return d["data"]
        err = (d.get("errors") or [{}])[0].get("message", "no data")
    raise RuntimeError(f"{op}: {err}")


def ps_grid(cat, size, sort="sales30", filters=None):
    v = {"id": PS_CAT[cat], "pageArgs": {"size": size, "offset": 0}, "sortBy": {"name": sort, "isAscending": False},
         "filterBy": filters or [], "facetOptions": []}
    return ps_gql("categoryGridRetrieve", v)["categoryGridRetrieve"]


def ps_cover(media, prefer=("GAMEHUB_COVER_ART", "MASTER", "FOUR_BY_THREE_BANNER", "PORTRAIT_BANNER"), w=440):
    by = {m.get("role"): m.get("url") for m in media or [] if m.get("type", "IMAGE") == "IMAGE"}
    u = next((by[r] for r in prefer if by.get(r)), "")
    return (u + f"?w={w}&thumb=false") if u else ""


def ps_poster(media):
    return ps_cover(media, ("PORTRAIT_BANNER",), 360)


def ps_name(n):
    # 去掉「(日语, 韩语, 简体中文…)」这类语言后缀
    return re.sub(r"\s*[（(][^()（）]*(?:语|文)[^()（）]*[)）]\s*$", "", n or "").strip()


def money(s):
    m = re.search(r"[\d,]+(?:\.\d+)?", s or "")
    return float(m.group().replace(",", "")) if m else None


def has_zh(name):
    return bool(re.search(r"中文|中英|中日|中韩|简体|繁体|中文版", name or ""))


def ps_shots(media, n=6):
    return [m["url"] + "?w=960&thumb=false" for m in media or [] if m.get("role") == "SCREENSHOT" and m.get("type", "IMAGE") == "IMAGE"][:n]


def ps_product(p):
    pr = p.get("price") or {}
    pct = re.search(r"-?(\d+)%", pr.get("discountText") or "")
    return {
        "id": p["id"], "name": ps_name(p.get("name")), "zh": has_zh(p.get("name")), "platforms": p.get("platforms") or [],
        "base": money(pr.get("basePrice")), "price": money(pr.get("discountedPrice")), "pct": int(pct.group(1)) if pct else 0,
        "free": bool(pr.get("isFree")), "plus_only": "PS_PLUS" in (pr.get("serviceBranding") or []),
        "preorder": any(s.get("type") == "PREORDER" for s in p.get("skus") or []),
        "cover": ps_cover(p.get("media")), "poster": ps_poster(p.get("media")), "shots": ps_shots(p.get("media"), 4), "url": f"{PS_STORE}/product/{p['id']}",
    }


def ps_concept(c):
    return {"cid": c["id"], "id": (c.get("products") or [{}])[0].get("id"), "name": ps_name(c.get("name")),
            "cover": ps_cover(c.get("media")), "poster": ps_poster(c.get("media")), "shots": ps_shots(c.get("media"), 4),
            "url": f"{PS_STORE}/concept/{c['id']}"}


def ps_enrich(item):
    """单个商品的购买按钮信息：普通折扣截止时间、PS Plus 会员价、是否在 Extra / Premium 游戏目录、能否试玩、所属 concept。"""
    d = ps_gql("productRetrieveForCtasWithPrice", {"productId": item["id"]})["productRetrieve"] or {}
    item["cid"] = (d.get("concept") or {}).get("id") or item.get("cid")
    for cta in d.get("webctas") or []:
        pr, t = cta.get("price") or {}, cta.get("type")
        if t == "ADD_TO_CART" and pr.get("endTime"):
            item["end"] = datetime.fromtimestamp(int(pr["endTime"]) / 1000, CST).isoformat(timespec="minutes")
        elif t == "UPSELL_PS_PLUS_DISCOUNT":
            item["plus_price"] = (pr.get("discountedValue") or 0) / 100
            if pr.get("endTime"):
                item.setdefault("end", datetime.fromtimestamp(int(pr["endTime"]) / 1000, CST).isoformat(timespec="minutes"))
        elif t == "UPSELL_PS_PLUS_GAME_CATALOG":
            item["catalog"] = True
        elif t == "UPSELL_PS_PLUS_TRIAL":
            item["trial"] = True


def ps_detail(cid):
    """游戏详情：英文名、发售日、发行商、类型、人数、简介、截图。"""
    c = ps_gql("metGetConceptById", {"conceptId": cid, "productId": ""})["conceptRetrieve"] or {}
    dp = c.get("defaultProduct") or {}
    notes = {n.get("type"): n.get("value") for n in dp.get("compatibilityNotices") or []}
    desc = next((x["value"] for x in dp.get("descriptions") or [] if x.get("type") == "SHORT"), "") or \
        next((x["value"] for x in dp.get("descriptions") or [] if x.get("type") == "LONG"), "")
    rel = (c.get("releaseDate") or {}).get("value") or dp.get("releaseDate")
    return {
        "en": c.get("invariantName") or "", "release": utc_iso(rel)[:10] if rel and utc_iso(rel) else "",
        "publisher": c.get("publisherName") or dp.get("publisherName") or "",
        "genres": [g["value"] for g in (c.get("combinedLocalizedGenres") or dp.get("combinedLocalizedGenres") or [])][:3],
        "players": notes.get("NO_OF_PLAYERS") or "", "online": notes.get("ONLINE_PLAY_MODE") or "",
        "desc": re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", desc)))[:220].strip(),
        "zh_d": has_zh(dp.get("name")), "shots_d": ps_shots(c.get("media") or dp.get("media"), 6),
        "_d": datetime.now(CST).date().isoformat(),
    }


def ps_price(cid):
    """concept 的默认商品价格（列表里的 concept 本身不带价格）。"""
    c = ps_gql("metGetPricingDataByConceptId", {"conceptId": cid})["conceptRetrieve"] or {}
    dp = c.get("defaultProduct") or {}
    pr = dp.get("price") or {}
    pct = re.search(r"-?(\d+)%", pr.get("discountText") or "")
    pre = any((x.get("meta") or {}).get("preOrder") for x in dp.get("mobilectas") or [])
    end = next(((x.get("price") or {}).get("endTime") for x in dp.get("mobilectas") or [] if (x.get("price") or {}).get("endTime")), None)
    return {"id": dp.get("id"), "base": (pr.get("basePriceValue") or 0) / 100 if pr.get("basePriceValue") is not None else money(pr.get("basePrice")),
            "price": (pr.get("discountedValue") or 0) / 100 if pr.get("discountedValue") is not None else money(pr.get("discountedPrice")),
            "pct": int(pct.group(1)) if pct else 0, "free": bool(pr.get("isFree")), "preorder": pre,
            "end": datetime.fromtimestamp(int(end) / 1000, CST).isoformat(timespec="minutes") if end else None,
            "_d": datetime.now(CST).date().isoformat()}


def ps_hk(prev, cache):
    """港服 PS：优惠（按 30 天销量）、畅销、最多下载、免费游玩、新游戏、预购；
    cache = {"detail": {cid: 详情}, "price": {cid: 价格}}，详情 30 天、价格 1 天内沿用，避免每次几百个请求。"""
    today = datetime.now(CST).date().isoformat()
    det, prc = cache.setdefault("detail", {}), cache.setdefault("price", {})
    stale = (datetime.now(CST).date() - timedelta(days=PS_DETAIL_DAYS)).isoformat()

    def detail(cid):
        if not cid:
            return {}
        if cid not in det or det[cid].get("_d", "") < stale:
            try:
                det[cid] = ps_detail(cid)
                time.sleep(0.2)
            except Exception as e:
                print("  ps detail fail", cid, e)
                return det.get(cid, {})
        return det[cid]

    def merge(x):
        d = detail(x.get("cid"))
        x.update({k: v for k, v in d.items() if k in ("en", "release", "publisher", "genres", "players", "online", "desc")})
        x["zh"] = x.get("zh") or d.get("zh_d", False)
        if len(d.get("shots_d") or []) > len(x.get("shots") or []):
            x["shots"] = d["shots_d"]
        return x

    deals = [ps_product(p) for p in ps_grid("deals", PS_DEALS_N, filters=["storeDisplayClassification:FULL_GAME"])["products"]]
    deals = [x for x in deals if x["base"] and x["price"] is not None]
    for x in deals[:PS_ENRICH_N]:
        old = prev.get(x["id"])
        if old and old.get("_day") == today:          # 同一天已查过购买信息，沿用
            x.update({k: v for k, v in old.items() if k in ("end", "plus_price", "catalog", "trial", "_day", "cid")})
        else:
            try:
                ps_enrich(x)
                x["_day"] = today
            except Exception as e:
                print("  ps enrich fail", x["name"][:20], e)
            time.sleep(0.2)
        merge(x)
    out = {"deals": deals}
    by_id = {x["id"]: x for x in deals}

    def concept_list(cat, sort):
        g = ps_grid(cat, PS_LIST_N, sort)
        items = [ps_concept(c) for c in g.get("concepts") or []] or [dict(ps_product(p), cid=None) for p in g.get("products") or []]
        for x in items:
            if x.get("cid"):
                if x["cid"] not in prc or prc[x["cid"]].get("_d") != today:
                    try:
                        prc[x["cid"]] = ps_price(x["cid"])
                        time.sleep(0.2)
                    except Exception as e:
                        print("  ps price fail", x["cid"], e)
                p_ = prc.get(x["cid"], {})
                x.update({k: v for k, v in p_.items() if k in ("base", "price", "pct", "free", "preorder", "end")})
                x["id"] = p_.get("id") or x["id"]
            elif x.get("id") in by_id:
                x["cid"] = by_id[x["id"]].get("cid")
            sale = by_id.get(x.get("id"))                 # 同一商品在优惠里：带上会员价 / 目录 / 截止时间
            if sale:
                x.update({k: sale[k] for k in ("plus_price", "catalog", "trial", "end", "pct", "price", "base") if sale.get(k) is not None})
            merge(x)
        time.sleep(0.3)
        return items

    for key, cat, sort in (("top_sales", "ps5", "sales30"), ("top_downloads", "ps5", "downloads30"), ("f2p", "f2p", "downloads30"),
                           ("new_release", "new", "productReleaseDate"), ("new_hot", "new", "sales30")):
        out[key] = concept_list(cat, sort)
    # 预购：分类里直接是商品（带价格），按发售日从近到远
    pre = [ps_product(p) for p in ps_grid("preorder", PS_LIST_N, "productReleaseDate")["products"]]
    for x in pre:
        if x["id"] in prev and prev[x["id"]].get("cid"):
            x["cid"] = prev[x["id"]]["cid"]
        else:
            try:
                ps_enrich(x)
                time.sleep(0.2)
            except Exception as e:
                print("  ps enrich fail", x["name"][:20], e)
        merge(x)
    out["preorder"] = sorted(pre, key=lambda x: x.get("release") or "9999")
    # 缓存只留最近 60 天用到的
    keep = {x.get("cid") for l in out.values() for x in l if x.get("cid")}
    cache["detail"] = {k: v for k, v in det.items() if k in keep or v.get("_d", "") >= stale}
    cache["price"] = {k: v for k, v in prc.items() if k in keep}
    return out


# ── 游戏详情扩展：PS 商店游戏页（星级、完整简介、分级、语言、版本价格）+ Metacritic（媒体 / 玩家评分与评测）──────
# 体积大，单独写 ps_detail.json，前端打开详情时才读；列表只带几个分数字段
DETAIL_FILE = ROOT / "ps_detail.json"
STORE_DAYS, MC_DAYS = 7, 30                      # 商店页（含版本价格）7 天、Metacritic 30 天刷新一次
EXTRA_BUDGET = 12 * 60                           # 每次运行补新游戏最多花 12 分钟，剩下的下次接着补
MC = "https://backend.metacritic.com"
PLAY_TIME = {"< 1 Hour": "不到 1 小时", ">= 80 Hours": "80 小时以上"}
DIFFICULTY = {"Simple": "很简单", "Easy": "简单", "Just Right": "适中", "Tough": "偏难", "Unforgiving": "非常难"}


def html_text(s, n):
    s = re.sub(r"<br\s*/?>", "\n", s or "", flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    # 去掉开头的购买须知（「购买该产品后可同时下载 PS4 / PS5 版」「※另有套装包」），空行并成一个
    lines = [l.strip() for l in re.sub(r"[ \t]+", " ", s).split("\n")]
    lines = [l for l in lines if not re.search(r"^※|^购买(该|本|此)(产品|商品|游戏)后|请注意避免重复购买|^本(产品|商品)(包含|为)", l)]
    return re.sub(r"\n{2,}", "\n", "\n".join(lines)).strip()[:n]


def ps_store_page(cid):
    """concept 页面服务端渲染的 JSON：星级评分、完整简介、年龄分级、语音 / 字幕语言、各版本（标准 / 豪华…）价格。"""
    t = fetch(f"{PS_STORE}/concept/{cid}", timeout=40)
    objs = {}

    def walk(o):
        if isinstance(o, dict):
            if o.get("__typename"):
                objs.setdefault(o["__typename"], []).append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for blob in re.findall(r'<script id="env:[^"]+" type="application/json">(.*?)</script>', t, re.S):
        try:
            walk(json.loads(blob))
        except ValueError:
            pass
    if not objs.get("Product"):
        raise ValueError("concept 页面没有商品数据")
    out = {}
    star = max(objs.get("StarRating", []), key=lambda r: (bool(r.get("ratingsDistribution")), r.get("totalRatingsCount") or 0), default=None)
    if star and star.get("averageRating"):
        cnt = max((r.get("totalRatingsCount") or 0) for r in objs["StarRating"])
        out["star"] = {"avg": star["averageRating"], "count": cnt,
                       "dist": {str(d["rating"]): d.get("percentageRaw", 0) for d in star.get("ratingsDistribution") or []}}
    desc = next((d["value"] for d in objs.get("Description", []) if d.get("type") == "LONG"), "")
    out["desc"] = html_text(desc, 2000)
    cr = next((r for r in objs.get("ProductContentRating", []) if r.get("description")), None)
    if cr:
        out["rating"] = {"name": cr["description"], "img": cr.get("url", ""),
                         "notes": [e["description"] for e in cr.get("interactiveElements") or [] if e.get("description")]}

    def langs(tn, key):
        by = {e.get("platform"): e.get(key) or [] for e in objs.get(tn, [])}
        return by.get("PS5") or by.get("PS4") or []
    out["voice"], out["text"] = langs("SpokenLanguagesByPlatformElement", "spokenLanguages"), langs("ScreenLanguagesByPlatformElement", "screenLanguages")
    # 版本：同一商品在缓存里出现多次，合并字段；价格来自购买按钮（GameCTA.local）
    prods = {}
    for p in objs["Product"]:
        if p.get("id"):
            prods.setdefault(p["id"], {}).update({k: v for k, v in p.items() if v not in (None, {}, [])})
    ctas = {}
    for c in objs.get("GameCTA", []):
        loc, m = c.get("local") or {}, re.search(r":([A-Z0-9]{6}-[A-Z0-9]{9}_00-[A-Z0-9]{16})", c.get("id") or "")
        if m and loc.get("ctaType") == "purchase" and loc.get("priceOrText"):
            ctas.setdefault(m.group(1), loc)
    eds = []
    for pid, p in prods.items():
        ed = p.get("edition") or {}
        if p.get("storeDisplayClassification") not in ("FULL_GAME", "GAME_BUNDLE", "PREMIUM_EDITION") or pid not in ctas:
            continue
        loc = ctas[pid]
        eds.append({"id": pid, "name": ps_name(p.get("name")), "edition": ed.get("name") or "", "features": (ed.get("features") or [])[:8],
                    "order": ed.get("ordering") or 99, "price": loc.get("priceOrText"), "orig": loc.get("originalPrice") or "",
                    "badge": loc.get("discountBadgeText") or "", "launch": (loc.get("launchPrice") or {}).get("price") or "",
                    "low30": re.sub(r"^.*?：", "", loc.get("lowestRecentPrice") or "")})
    out["editions"] = sorted(eds, key=lambda e: (e["order"], e["name"]))[:6]
    return out


def mc_norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("&", "and"))


def mc_clean(en):
    s = re.sub(r"[™®©]", "", en or "")
    s = re.sub(r"\s*[\(（]?\b(PS4|PS5)\b(\s*(&|and|/)\s*(PS4|PS5))?[\)）]?", " ", s)
    s = re.sub(r"\s*[-–:]?\s*\b(Standard|Digital Deluxe|Deluxe|Digital|Complete|Gold|Ultimate|Premium|Launch)\s+Edition\b", "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip(" -–:")


def metacritic(en, year):
    """按英文名搜 Metacritic；名字规范化后完全一致才算同一个游戏（港服发售日常是移植 / 重制日期，只在同名多作时用年份挑），对不上返回 None。"""
    q = mc_clean(en)
    if not re.search(r"[A-Za-z]{2}", q):
        return None
    items = json.loads(fetch(f"{MC}/finder/metacritic/search/{urllib.parse.quote(q)}/web?offset=0&limit=12&mcoTypeId=13",
                             headers={"Accept": "application/json"}))["data"]["items"]
    cands = [i for i in items if i.get("type") == "game-title" and mc_norm(i.get("title")) == mc_norm(q)]
    if year and len(cands) > 1:                  # 同名多作（重制 / 新作）：取年份最近的，差 3 年以上都不认
        cands = [i for i in cands if i.get("premiereYear") and abs(i["premiereYear"] - year) <= 3]
        cands.sort(key=lambda i: abs(i["premiereYear"] - year))
    if not cands:
        return None
    slug = cands[0]["slug"]
    comps = {c["meta"].get("componentName"): c.get("data") or {} for c in json.loads(fetch(
        f"{MC}/composer/metacritic/pages/games/{slug}/web?contentOnly=true", headers={"Accept": "application/json"}))["components"]}
    cs, us = (comps.get("critic-score-summary") or {}).get("item") or {}, (comps.get("user-score-summary") or {}).get("item") or {}
    prod = (comps.get("product") or {}).get("item") or {}
    stats = (comps.get("game-stats") or {}).get("item") or {}
    top = lambda l: max([r for r in l or [] if (r.get("total") or 0) >= 3], key=lambda r: r["total"], default={}).get("label", "")
    pt = top(stats.get("play_time"))
    critic = [{"src": r.get("publicationName"), "score": r.get("score"), "quote": (r.get("quote") or "")[:400], "url": r.get("url") or "",
               "date": r.get("date")} for r in ((comps.get("critic-reviews") or {}).get("item") or {}).get("default") or [] if r.get("quote")][:6]
    users = [{"author": r.get("author"), "score": r.get("score"), "quote": r["quote"][:500], "date": r.get("date")}
             for r in ((comps.get("user-reviews") or {}).get("item") or {}).get("default") or []
             if not r.get("spoiler") and 30 <= len(r.get("quote") or "") <= 1200][:4]
    if cs.get("score") is None and us.get("score") is None and not critic:
        return None
    return {"slug": slug, "title": prod.get("title") or cands[0].get("title"), "year": prod.get("premiereYear"), "must": bool(prod.get("mustPlay")),
            "score": cs.get("score"), "count": cs.get("reviewCount"), "sentiment": cs.get("sentiment"),
            "uscore": us.get("score"), "ucount": us.get("reviewCount"), "usentiment": us.get("sentiment"),
            "playtime": PLAY_TIME.get(pt) or re.sub(r"~(\d+) Hours?", r"约 \1 小时", pt), "difficulty": DIFFICULTY.get(top(stats.get("difficulty")), ""),
            "critic": critic, "users": users, "url": f"https://www.metacritic.com/game/{slug}/"}


def ps_extras(pshk, plus):
    """给首页各栏目和各列表前几屏的游戏补详情（约 250 款），按缓存日期只补过期 / 新出现的；把分数挂回列表项。"""
    old = json.loads(DETAIL_FILE.read_text("utf-8")).get("games", {}) if DETAIL_FILE.exists() else {}
    today = datetime.now(CST).date()
    stale = lambda d, n: not d or d < (today - timedelta(days=n)).isoformat()
    deals = pshk.get("deals", [])
    want = deals[:90] + [x for x in deals if x.get("catalog")] + [x for k in ("top_sales", "top_downloads", "f2p", "new_release", "new_hot", "preorder")
                                                                   for x in pshk.get(k, [])]
    names = {nk(g["name"]) for k in ("monthly", "catalog") for g in plus.get(k, [])}
    want += [x for l in pshk.values() for x in l if nk(x.get("name"))[:6] and any(nk(x["name"]).startswith(n[:6]) for n in names if n)]
    order = list(dict.fromkeys(x["cid"] for x in want if x.get("cid")))
    games, t0, done = {}, time.time(), [0, 0]
    for cid in order:
        g = dict(old.get(cid, {}))
        x = next(i for i in want if i.get("cid") == cid)
        if time.time() - t0 < EXTRA_BUDGET:
            if stale(g.get("s_d"), STORE_DAYS):
                try:
                    g["s"], g["s_d"] = ps_store_page(cid), today.isoformat()
                    done[0] += 1
                except Exception as e:
                    print("  store page fail", cid, e)
                time.sleep(0.3)
            if stale(g.get("m_d"), MC_DAYS) and x.get("en"):
                try:
                    g["m"], g["m_d"] = metacritic(x["en"], int(x["release"][:4]) if x.get("release") else None), today.isoformat()
                    done[1] += 1
                except Exception as e:
                    print("  metacritic fail", x.get("en"), e)
                time.sleep(0.4)
        if g:
            games[cid] = g
    # 分数挂回列表（首页「高分佳作」、列表角标用）
    for l in pshk.values():
        for x in l:
            g = games.get(x.get("cid")) or {}
            m, s = g.get("m") or {}, g.get("s") or {}
            x["mc"], x["mcu"], x["star"] = m.get("score"), m.get("uscore"), (s.get("star") or {}).get("avg")
    DETAIL_FILE.write_text(json.dumps({"updated": datetime.now(CST).isoformat(timespec="seconds"), "games": games},
                                      ensure_ascii=False, separators=(",", ":")), "utf-8")
    print("extras", len(order), "store new", done[0], "mc new", done[1], "mc matched", sum(1 for g in games.values() if g.get("m")))
    return games


def nk(n):
    return re.sub(r"[\s：:·™®《》()（）\-]", "", n or "").lower()


def ps_plus_hk():
    """PS Plus 官方港服中文页：本月会员免费游戏（Essential）、游戏目录本月新增（Extra / Premium），带配图。"""
    t = fetch("https://www.playstation.com/zh-hans-hk/ps-plus/whats-new/", timeout=40)
    clean_ = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
    heads = [(m.start(), clean_(m.group(1))) for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", t, re.S)]

    def section(title):
        starts = [i for i, h in heads if title in h]
        if not starts:
            return ""
        i = starts[0]
        nxt = min([j for j, h in heads if j > i and title not in h] or [len(t)])
        return t[i:nxt]

    def ok_img(u):
        try:
            req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status == 200
        except Exception:
            return False

    def img_near(seg, pos, slug=""):
        # 离标题最近、能打开、并且文件名对得上这个游戏的那张；对不上宁可不要（不拿隔壁游戏的图顶替）
        imgs = sorted({(abs(m.start() - pos), m.group(1)) for m in re.finditer(r"(https://gmedia\.playstation\.com/is/image/SIEPDC/[^\"\s?$]+)", seg)})
        key = "-".join(slug.strip("/").split("/")[-1].split("-")[:2]) if slug else ""
        for _, u in [x for x in imgs if "badge" not in x[1] and (not key or key in x[1])][:3]:
            if ok_img(u + "?$800px$"):
                return u + "?$800px$"
        return ""

    monthly = []
    seg = section("每月游戏")
    for m in re.finditer(r'<h3 class="txt-style-medium-title[^"]*"[^>]*>(.*?)</h3>', seg, re.S):
        link = re.search(r'href="(/zh-hans-hk/games/[^"]+)"', seg[m.end():m.end() + 3000])
        monthly.append({"name": clean_(m.group(1)), "img": img_near(seg, m.start(), link.group(1) if link else ""),
                        "url": "https://www.playstation.com" + link.group(1) if link else ""})
    catalog = []
    seg = section("游戏目录最新阵容")
    for m in re.finditer(r'<h5 class="txt-style-subtitle-bold txt-block-utility__title"[^>]*>(.*?)</h5>', seg, re.S):
        links = re.findall(r'href="(/zh-hans-hk/games/[^"]+)"', seg[max(0, m.start() - 4000):m.start()])
        slug = links[-1] if links else ""                     # 标题前最近的那个游戏链接
        catalog.append({"name": clean_(m.group(1)), "img": img_near(seg, m.start(), slug),
                        "url": "https://www.playstation.com" + slug if slug else ""})
    if not monthly:
        raise RuntimeError("没解析到本月会员游戏")
    return {"monthly": monthly, "catalog": catalog}


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
    prev_ps = old.get("ps_hk") or {}
    prev_enr = {x["id"]: x for l in prev_ps.values() if isinstance(l, list) for x in l if x.get("id")}
    ps_cache = old.get("_ps_cache") or {}
    pshk = run("PS 港服商店", lambda: ps_hk(prev_enr, ps_cache), "ps_hk", count=lambda v: len(v["deals"])) or {}
    psplus = run("PS Plus 港服", ps_plus_hk, "ps_plus_hk", count=lambda v: len(v["monthly"]) + len(v["catalog"])) or {}
    gpass = run("Xbox Game Pass", game_pass, "game_pass") or []
    if pshk:
        run("Metacritic 评分评测", lambda: ps_extras(pshk, psplus), "_none", count=lambda v: sum(1 for g in v.values() if g.get("m")))

    # 国区价格历史：每天保留当天最后一次价格（appid -> {date: price}），用来判断「国区近 N 天最低」
    hist = old.get("price_history", {})
    for g in st:
        h = hist.setdefault(str(g["appid"]), {})
        h[today] = g["price"]
    cutoff = (now.date() - timedelta(days=PRICE_DAYS)).isoformat()
    live = {str(g["appid"]) for g in st}
    hist = {k: {d: p for d, p in v.items() if d >= cutoff} for k, v in hist.items()}
    hist = {k: v for k, v in hist.items() if v and (k in live or max(v) >= (now.date() - timedelta(days=30)).isoformat())}

    # 港服 PS 价格历史（商品 id -> {date: 当前价}），记满 7 天后才判断「港服新低」
    ps_hist = old.get("ps_price_history", {})
    for x in pshk.get("deals", []):
        ps_hist.setdefault(x["id"], {})[today] = x["price"]
    ps_live = {x["id"] for x in pshk.get("deals", [])}
    ps_hist = {k: {d: p for d, p in v.items() if d >= cutoff} for k, v in ps_hist.items()}
    ps_hist = {k: v for k, v in ps_hist.items() if v and (k in ps_live or max(v) >= (now.date() - timedelta(days=30)).isoformat())}
    for x in pshk.get("deals", []):
        h = ps_hist.get(x["id"], {})
        x["days"] = len(h)
        x["low"] = bool(len(h) >= 7 and x["price"] <= min(h.values()))

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
        "ps_hk": pshk,
        "ps_plus_hk": psplus,
        "game_pass": gpass,
        "summary": {                    # 给 pages-dashboard 用，字段只增不减
            "epic_now": [g["title"] for g in ep if g["kind"] == "now"],
            "epic_now_worth": round(sum(g["worth"] for g in ep if g["kind"] == "now"), 2),
            "epic_end": min((g["end"] for g in ep if g["kind"] == "now" and g["end"]), default=None),
            "epic_next": [g["title"] for g in ep if g["kind"] == "next"],
            "giveaway_games": sum(1 for g in gp if g["type"] == "game"),
            "steam_lows": sum(1 for g in st if g["usd_low"] or g["cn_low"]),
            "ps_deals": len(pshk.get("deals", [])),
            "ps_plus_monthly": [g["name"] for g in psplus.get("monthly", [])],
            "next_sale": next(({"name": e["cn"] or e["name"], "start": e["start"], "end": e["end"]} for e in ev if e["end"] >= today), None),
        },
        "_lows": lows,
        "_cs_ids": cs_cache,
        "price_history": hist,
        "ps_price_history": ps_hist,
        "_ps_cache": ps_cache,
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
