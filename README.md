# 🎁 喜加一 · Game Deals

> Epic 每周限免、全平台免费领取、Steam 国区特惠与史低、Steam 大促日历、PS Plus 与 Game Pass，一页看完

**🌐 在线访问：[https://climb0516.github.io/game-deals/](https://climb0516.github.io/game-deals/)**

---

## 截图

**限免**：Epic 本周免费 + 下周预告（国区原价、截止倒计时），下面是全平台免费领取

![限免](screenshot-free.jpg)

**Steam 特惠**：国区热销特惠前 300，人民币价格、好评率、史低标记，可按价格 / 折扣 / 好评筛选

![Steam 特惠](screenshot-steam.jpg)

---

## 功能

- **🎮 PlayStation**（首页，`#ps`，港服）
  - 首页每个栏目一种卡片：**PS Plus 本月会免**（大图拼贴）、**游戏目录新增**（竖版海报横滑）、**高分佳作在打折**（海报网格 + Metacritic 分数角标）、**最新折扣**（Jump 式行 + 史低 / 5 折以下 / 会员价 / 即将结束 / 中文快捷入口）、**正在流行**（畅销 / 最多下载 / 免费游玩三栏排行）、**最新发布**（刚刚发售 / 即将发售两条时间线）
  - 「查看更多」进入单独的列表页（`#ps/deal/low` 这类地址，可直接分享），带子分类和排序（热度 / 评分 / 折扣 / 价格 / 剩余时间）。列表页是新开的一层，从右侧滑入盖在首页上，返回时滑走，首页一直在底下不动；游戏详情弹框盖在这一层之上；安卓可从左边缘右滑返回
  - 点游戏弹出详情：截图轮播；Metacritic 媒体评分、玩家评分，PS Store 玩家星级和各星占比；价格、会员价、近 30 天最低、首发价、本站价格走势；发售日 / 发行商 / 类型 / 人数 / 年龄分级 / 通关时长 / 难度 / 语音 / 字幕；完整中文介绍；媒体评测摘录（英文，带原文链接）；玩家评价；各版本及价格；「去 PS Store 购买」
  - 史低：每天记录港服价格，满 7 天后当前价不高于记录内最低价即标出
- **限免**（`#free`）
  - Epic 本周免费、下周预告：原价、领取截止倒计时、直达商店页；顶部汇总「本周送几款、原价合计多少」
  - 全平台免费领取：Steam、GOG、Ubisoft、itch.io、IndieGala、PS、Xbox、手机等，可切换「完整游戏 / 道具礼包」、按平台筛选；已和 Epic 重复的不再列出
- **Steam 特惠**（`#steam`）
  - 国区热销特惠前 300：折扣、人民币现价 / 原价、好评率和评测数
  - 筛选：价格（≤ ¥10 / 30 / 60 / 100）、折扣、好评；排序：热销 / 折扣 / 价格 / 好评；「只看史低」
  - **史低**：美区当前价已到 CheapShark 记录的历史最低（热销前 120 款）；**国区新低**：本站每天记录国区价格，满 7 天后低于等于记录最低时标出
- **大促日历**（`#sales`）：Steam 冬促 / 春促 / 夏促等官方日程，倒计时、进行中进度条；附 Epic 每周更新规律
- **主机**（`#console`）：PS Plus 本月会免游戏和游戏目录、Xbox Game Pass 港区最近新增（中文名、封面）、主机平台免费道具
- **订阅提醒**：`sales.ics`，Steam 大促开始前一天提醒、Epic 本周限免结束前 4 小时提醒
- 右侧挂件：Epic 限免倒计时、下一个 Steam 大促、当前史低数量、来源状态
- 右上角：↻ 重新读取数据，⚡ 跳转 GitHub Actions 手动触发抓取，☾ 深浅色；手机适配；`#steam` 等锚点可直达

订阅地址：`https://climb0516.github.io/game-deals/sales.ics`（iPhone 可直接打开 `webcal://` 开头的同一地址）

---

## 技术架构

```
GitHub Actions（每 6 小时 / 每周四 23:20 Epic 更新后 / 手动 / 修改 scraper.py 或工作流后 push）
  ↓ python scraper.py（Python 3.12，只用标准库，无需密钥）
  ↓ 抓取 10 个来源：Epic + GamerPower + Steam 特惠 300 + CheapShark 史低 + Steam 大促日历
  ↓                + PS Plus 博客 + PS 港服商店 + PS Plus 港服页 + Xbox Game Pass + Metacritic
  ↓ 合并价格历史（Steam 国区 / PS 港服，日期 → 价格），标记美区史低 / 国区新低 / 港服新低
  ↓ 某个来源失败 → 沿用上次数据，来源状态标红
  ↓ 写入 data.json（主数据）+ ps_detail.json（PS 详情评分评测）+ sales.ics（日历订阅）
  ↓ git commit & push（updated 每次都变 = 心跳）
       ↓
GitHub Pages（index.html）
  ↓ 读取同目录 data.json，筛选 / 排序 / 列表页都在前端完成
  ↓ 点 PS 游戏时才读 ps_detail.json 补评分、评测、版本价格
```

---

## 数据来源

| 来源 | 方式 | 每次条数 / 范围 | 备注 |
|---|---|---|---|
| Epic 商店（国区） | 接口 `freeGamesPromotions?locale=zh-CN&country=CN` | 本周限免 + 下周预告，全部 | 折后价为 0 的才算限免；原价为人民币 |
| [GamerPower](https://www.gamerpower.com/) | 接口 `/api/giveaways?sort-by=date` | 接口返回的全部（游戏 + 道具礼包） | 带截止时间、已领人数 |
| Steam 商店搜索（`cc=cn`） | 网页解析（搜索接口返回的 `results_html` 用正则拆） | 热销特惠 3 页 × 100 = 前 300（`STEAM_PAGES`） | 每页间隔 1.5 秒；带 `birthtime=0` Cookie 跳过年龄确认 |
| [CheapShark](https://www.cheapshark.com/) | 接口 | 热销前 120 款（`LOW_TOP`），每批 25 个查史低 | appid → CheapShark 编号缓存在 `_cs_ids`，之后只查新游戏 |
| [Steamworks 文档 Upcoming Events](https://partner.steamgames.com/doc/marketing/upcoming_events) | 网页解析 | 页面上列出的全部大促 | 官方提前公布给开发者 |
| [PlayStation.Blog](https://blog.playstation.com/tag/playstation-plus/) | RSS | 最近 6 条 PS Plus 每月游戏 / 游戏目录文章 | 英文标题，取自美区 |
| PlayStation Store 港服 | 接口（官方 GraphQL persisted query） | 优惠前 600（`PS_DEALS_N`）；畅销、最多下载、免费游玩、新游戏、新游戏热门、预购各 48（`PS_LIST_N`）；前 120 款补购买信息（`PS_ENRICH_N`） | 见下方「PlayStation 港服说明」 |
| PlayStation Store 港服游戏页 | 网页解析（页面内嵌的 `env:` JSON） | 首页各栏目和各列表前几屏的游戏 | 星级、完整介绍、分级、语言、各版本价格；7 天刷新 |
| PS Plus 港服中文页 `playstation.com/zh-hans-hk/ps-plus/whats-new/` | 网页解析 | 本月会员免费游戏 + 游戏目录本月新增，全部 | 带官方配图 |
| [Metacritic](https://www.metacritic.com/) | 接口（`backend.metacritic.com`，不需要 key） | 同上，按英文名逐个匹配；搜索每次取 12 个候选 | 媒体评分、玩家评分、评测摘录、通关时长、难度；30 天刷新 |
| Xbox Game Pass 目录 + Microsoft Store（港区） | 接口（`catalog.gamepass.com/sigls/v2` + `displaycatalog`） | 最近新增前 24 款 | 中文名、封面、发售日 |

**增删来源**：每个来源是 `scraper.py` 里的一个函数（`epic()`、`gamerpower()`、`steam_specials()`、`cheapshark_lows()`、`steam_events()`、`ps_plus()`、`ps_hk()`、`ps_plus_hk()`、`game_pass()`、`ps_extras()`），在 `main()` 里用 `run("来源名", 函数, "data.json 里的键")` 调用。新增来源：写函数 + 在 `main()` 加一行 `run(...)` + 写进 `data` 字典；删除来源：去掉对应 `run(...)` 和字段。PS 商店分类在 `PS_CAT`，GraphQL hash 在 `PS_HASH`，条数在文件顶部常量里。

**限制**：
- 美区史低不等于国区史低；国区史低要靠本站逐天积累（最多保留 120 天）
- 特惠可能只持续几小时，数据每 6 小时更新，以商店页为准
- Switch eShop 港服没有可用的价格接口，暂不收录
- 某个来源失败时沿用上一次的数据，并在来源状态里标红

### PlayStation 港服说明

- 商店数据：PlayStation Store 官方 GraphQL（`web.np.playstation.com/api/graphql/v1/op`），请求头 `x-psn-store-locale-override: zh-hans-hk` 固定为港服（否则 Actions 的美国 IP 会拿到美区）。只能用前端白名单里的 persisted query hash（`PS_HASH`，每个操作可放多个 hash 依次尝试），失效时「PS 港服商店」来源会变红，需要从商店页面的网络请求里取新 hash 更新 `PS_HASH`
- 使用的港服常驻分类（`PS_CAT`）：全部优惠、全部 PS5 游戏、新游戏、免费游玩、预购（活动专题分类会轮换，不用）
- 优惠按 30 天销量取前 600 款（只要 `FULL_GAME`）；各榜单每个取 48 款。前 120 款逐个查价格按钮（`productRetrieveForCtasWithPrice`：折扣截止、会员价、是否在游戏目录、能否试玩），所有条目查详情（`metGetConceptById`：英文名、发售日、发行商、类型、人数、简介、截图）；榜单里的 concept 本身不带价格，用 `metGetPricingDataByConceptId` 补
- 详情缓存在 data.json 的 `_ps_cache`（`detail` 30 天、`price` 当天有效），购买信息同一天内沿用（`_day`）
- **评分评测**写在单独的 `ps_detail.json`（打开详情时才读）：PS 商店游戏页每 7 天、Metacritic 每 30 天刷新一次；每次运行补新游戏最多花 12 分钟（`EXTRA_BUDGET`），没补完的下次接着补
- 请求必须带 `content-type: application/json`，否则返回 400
- Jump 只有 App、没有网页和公开接口，不抓；它的折扣、评分数据本身也来自 PS 商店和 Metacritic 这类公开来源
- PS Plus 会员内容取自服务端渲染的官方中文页；个别配图官方 CDN 返回 403 时不拿别的游戏的图顶替，页面上按名字借商店封面或显示占位
- 第三方追踪站（PSPrices、PSDeals 等）都有 Cloudflare 验证，标准库抓不了，所以「新低」靠自己积累价格历史

---

## 数据处理规则

**限免识别**（`epic()`）：遍历每个商品的 `promotionalOffers`（本周，`kind: now`）和 `upcomingPromotionalOffers`（下周，`kind: next`），只保留 `discountPercentage == 0`（即折后为 0）的，其余是普通打折。商店链接优先取 `catalogNs.mappings` 里 `productHome` 的 slug，否则 `productSlug` / `urlSlug`，都没有就指向免费游戏页。按「本周在前、开始时间升序」排序。

**全平台喜加一**（`gamerpower()`）：
- 平台归类：`PLATFORM_MAP` 关键词表，平台字段里包含 `PS4` / `PS5` / `PlayStation` → PlayStation，`Android` / `iOS` → 手机，`Itch` → itch.io 等，一个都对不上记「其他」
- 标题清洗：正则 `\s*\((?:[^()]*)\)\s*Giveaway$|\s*Giveaway$` 去掉「(Steam) Giveaway」这类后缀
- 类型：`type == "Game"` → `game`，其余 → `loot`（道具礼包）
- 与 Epic 去重（前端）：平台含 Epic 且标题包含某个 Epic 限免标题前 8 个字符的，不再列出

**Steam 特惠解析**（`steam_specials()`）：按 `<a href="…/app/` 切行，正则取 `data-ds-appid`、标题、`data-discount`、`data-price-final`（分 → 元）、原价、好评摘要和「N% 为好评」、评测数（「中有 N 篇 / 的 N 篇用户评测」）、发售日、封面；缺 appid / 标题 / 折扣 / 现价的行丢弃。一条都没有则视为失败。

**美区史低**（`cheapshark_lows()` + `main()`）：只看 CheapShark 里 Steam 商店（`storeID == "1"`）的现价，`usd <= cheapestPriceEver + 0.001` 即 `usd_low = true`。

**国区新低 / 港服新低**（`main()`）：
- 每次运行把当天价格写进 `price_history`（Steam appid）和 `ps_price_history`（PS 商品 id），同一天以最后一次为准
- 只保留最近 120 天（`PRICE_DAYS`）；已不在当前列表、且最后一条记录早于 30 天的游戏整条删掉
- 记录满 7 天后，当前价 `<=` 记录内最低价 → `cn_low` / `low = true`；`cn_days` / `days` 是已记录天数
- `summary.steam_lows` = 美区史低或国区新低的游戏数

**Steam 大促日历**（`steam_events()`）：页面去标签后，用名字正则 `(?:Steam )?…(?:Sale|Fest|Festival)(?: \d{4})?` 加「`|` 开始日期 – 结束日期」匹配，日期兼容「17 December, 2026」和「December 17, 2026」两种写法；中文名用 `SALE_CN` 映射（Winter Sale → 冬季特卖、Next Fest → 新品节、Lunar New Year → 农历新年特卖等）；按 (名字, 开始日) 去重、按开始日排序。匹配不到时把「Sale」附近原文写进错误信息便于排查。

**PS Plus 博客**（`ps_plus()`）：标题正则 `PlayStation Plus (Monthly Games|Game Catalog) for (\w+)\s*[:–-]\s*(.+)`，游戏名按逗号和 `and` 拆开，结尾「and more」记 `more: true`。

**PS 港服商品整理**（`ps_product()` / `ps_name()` / `has_zh()`）：
- 名字去掉语言后缀：正则 `\s*[（(][^()（）]*(?:语|文)[^()（）]*[)）]\s*$`（如「（日语, 韩语, 简体中文）」）
- 中文标记：名字含「中文 / 中英 / 中日 / 中韩 / 简体 / 繁体」即 `zh = true`（详情里的名字也会再判断一次）
- `plus_only`：`serviceBranding` 含 `PS_PLUS`；`preorder`：sku 类型为 `PREORDER`；折扣从 `discountText` 里取百分比
- 封面优先级：`GAMEHUB_COVER_ART` → `MASTER` → `FOUR_BY_THREE_BANNER` → `PORTRAIT_BANNER`；竖版海报用 `PORTRAIT_BANNER`

**PS 详情补齐范围**（`ps_extras()`）：优惠前 90 款 + 在游戏目录内的优惠 + 6 个榜单（畅销、最多下载、免费游玩、新游戏、新游戏热门、预购）+ 名字和 PS Plus 会免 / 目录新增前 6 个字符对得上的商品，按 concept 去重。补完后把 `mc`（媒体分）、`mcu`（玩家分）、`star`（PS 星级）挂回 data.json 的列表项。

**Metacritic 匹配**（`mc_clean()` / `mc_norm()` / `metacritic()`）：
- 英文名去掉 `™®©`、`PS4` / `PS5`（含「PS4 & PS5」）、`Standard / Digital Deluxe / Deluxe / Digital / Complete / Gold / Ultimate / Premium / Launch Edition` 后缀
- 规范化（小写、`&` → and、只留字母数字）后与搜索结果标题**完全一致**才算；不含连续 2 个英文字母的名字不查
- 同名多作：按港服发售年份挑最近的，差 3 年以上都不认；对不上返回空，前端不显示分数
- 媒体评测取有摘录的前 6 条（摘录截 400 字）；玩家评价排除剧透、长度 30～1200 字，取前 4 条
- 通关时长、难度：取投票数 ≥ 3 中票数最多的一项，翻译成中文（如「Tough」→ 偏难）

**商店介绍清洗**（`html_text()`，前端 `cleanDesc` 同规则）：去掉以「※」「购买该/本/此产品后」开头、含「请注意避免重复购买」、「本产品包含/为」开头的购买须知行，多个空行并成一个，最多 2000 字。

**PS Plus 港服页配图**（`ps_plus_hk()` 里的 `img_near()`）：在对应 `<h2>` 区段内找离标题最近的 `gmedia.playstation.com` 图片，排除含 `badge` 的，文件名必须包含游戏页 slug 的前两段，前 3 张里用 HEAD 请求校验返回 200 才采用；都不行就留空。没解析到本月会免视为失败。

**失败兜底**（`main()` 里的 `run()`）：任一来源抛异常 → `sources` 里记 `ok: false` 和错误信息（截 300 字），`updated` 保留上次成功时间，数据沿用 data.json 里的旧值。

**日历订阅**（`ics()`）：只写未结束的 Steam 大促（全天事件，提前 1 天提醒）和当前这期 Epic 限免（事件从结束前 1 小时开始，提醒设在开始前 3 小时，即结束前 4 小时）；`REFRESH-INTERVAL` 为 12 小时。

---

## 数据结构

### data.json

顶层字段：

| 字段 | 内容 |
|---|---|
| `updated` | 本次运行时间（北京时间），每次都变，作为心跳 |
| `epic` / `giveaways` / `steam` / `events` / `ps_plus` / `game_pass` | 各来源列表 |
| `ps_hk` | PS 港服：`deals`、`top_sales`、`top_downloads`、`f2p`、`new_release`、`new_hot`、`preorder` 七个列表 |
| `ps_plus_hk` | PS Plus 港服页：`monthly`（本月会免）、`catalog`（目录新增），每项 `name` / `img` / `url` |
| `summary` | 给 pages-dashboard 的汇总，字段只增不减 |
| `price_history` / `ps_price_history` | Steam 国区 / PS 港服价格历史 |
| `_lows` / `_cs_ids` / `_ps_cache` | 内部缓存：美区史低结果、appid → CheapShark 编号、PS 详情和价格缓存 |
| `sources` | 每个来源的状态 |

```
{
  "updated": "2026-10-21T11:17:00+08:00",
  "epic": [ { "title": "Bad Cheese", "kind": "now", "start": "…", "end": "2026-10-22T23:00+08:00", "worth": 40, "img": "…", "url": "…", "desc": "…" } ],   // kind: now / next
  "giveaways": [ { "id": 1234, "title": "…", "type": "game", "platforms": ["Steam"], "worth": "$9.99", "end": "…", "img": "…", "url": "…",
                   "users": 1234, "published": "…" } ],                                            // type: game / loot
  "steam": [ { "appid": 1091500, "title": "赛博朋克 2077", "discount": 70, "price": 89.4, "orig": 298, "review": "特别好评", "rate": 80,
               "reviews": 202469, "released": "…", "img": "…", "rank": 1, "usd": 17.99, "usd_lowest": 17.99, "usd_low": true,
               "cn_low": false, "cn_days": 1 } ],
  "events": [ { "name": "Winter Sale 2026", "cn": "冬季特卖", "start": "2026-12-17", "end": "2027-01-04" } ],
  "ps_plus": [ { "kind": "monthly", "month": "October", "games": ["F1 25", "…"], "more": false, "date": "…", "url": "…" } ],
  "ps_hk": {
    "deals": [ { "id": "商品 id", "cid": "concept id", "name": "…", "en": "英文名", "zh": true, "platforms": ["PS5"],
                 "base": 468, "price": 234, "pct": 50, "free": false, "plus_only": false, "preorder": false,
                 "plus_price": 199, "catalog": false, "end": "…", "cover": "…", "poster": "…", "shots": ["…"], "url": "…",
                 "release": "…", "publisher": "…", "genres": ["…"], "players": "…", "online": "…", "desc": "…",
                 "mc": 86, "mcu": 8.1, "star": 4.6, "days": 15, "low": true, "_day": "…" } ],
    "top_sales": [ … ], "top_downloads": [ … ], "f2p": [ … ], "new_release": [ … ], "new_hot": [ … ], "preorder": [ … ]   // 字段同上（无 days / low）
  },
  "ps_plus_hk": { "monthly": [ { "name": "…", "img": "…", "url": "…" } ], "catalog": [ … ] },
  "game_pass": [ { "id": "9P2FF14JZLL3", "title": "戰地風雲™ 6", "img": "…", "released": "…", "url": "…" } ],
  "summary": { "epic_now": ["…"], "epic_now_worth": 102, "epic_end": "…", "epic_next": ["…"], "giveaway_games": 17, "steam_lows": 52,
               "ps_deals": 598, "ps_plus_monthly": ["…"], "next_sale": { "name": "冬季特卖", "start": "2026-12-17", "end": "2027-01-04" } },
  "_lows": { "1091500": { "usd": 9.99, "usd_low": 4.99, "usd_low_date": 1591592509 } },
  "_cs_ids": { "1091500": "CheapShark gameID（查不到为空字符串）" },
  "price_history": { "1091500": { "2026-10-21": 89.4 } },
  "ps_price_history": { "商品 id": { "2026-10-21": 234 } },
  "_ps_cache": { "detail": { "concept id": { …详情, "_d": "缓存日期" } }, "price": { "concept id": { …价格, "_d": "…" } } },
  "sources": [ { "name": "Epic 限免", "ok": true, "count": 4, "updated": "…" } ]          // 失败时 ok: false + error
}
```

### ps_detail.json

PS 游戏详情扩展，前端打开详情时才读：

```
{
  "updated": "…",
  "games": {
    "concept id": {
      "s": { "star": { "avg": 4.6, "count": 12345, "dist": { "5": 80, … } }, "desc": "完整介绍", "rating": { "name": "分级", "img": "…", "notes": ["…"] },
             "voice": ["zh", "en"], "text": ["zh", "en"],
             "editions": [ { "id": "…", "name": "…", "edition": "豪华版", "features": ["…"], "order": 1, "price": "HK$468", "orig": "…",
                             "badge": "-50%", "launch": "首发价", "low30": "近 30 天最低" } ] },   // 最多 6 个版本
      "s_d": "商店页抓取日期",
      "m": { "slug": "…", "title": "…", "year": 2024, "must": false, "score": 86, "count": 90, "sentiment": "…", "uscore": 8.1, "ucount": 500,
             "usentiment": "…", "playtime": "约 40 小时", "difficulty": "适中", "critic": [ { "src": "…", "score": 90, "quote": "…", "url": "…", "date": "…" } ],
             "users": [ { "author": "…", "score": 9, "quote": "…", "date": "…" } ], "url": "…" },        // 匹配不到为 null
      "m_d": "Metacritic 抓取日期"
    }
  }
}
```

### sales.ics

iCalendar 订阅文件（`X-WR-CALNAME: Game Deals · 大促与限免`），内容见「数据处理规则 → 日历订阅」。

---

## 前端

本项目没有使用 kit 详情抽屉组件，PS 游戏详情是自带的弹窗。除「功能」一节外，前端实现要点：

- **视图与地址**：`#ps`（默认）/ `#free` / `#steam` / `#sales` / `#console`；PS 列表页地址 `#ps/<分组>/<子项>`，可直接分享：
  - `plus`：`monthly` 每月会免、`catalog` 目录新增、`incat` 目录内打折
  - `deal`：`pick` 精选（前 60）、`top` 高分佳作（Metacritic ≥ 75）、`all` 全部、`low` 史低、`big` 大折扣（≥ 50%）、`plus` 会员价、`soon` 即将结束（3 天内）、`zh` 中文
  - `hot`：`top_sales`、`top_downloads`、`f2p`
  - `new`：`new_release`、`new_hot`、`preorder`（预购按发售日由近到远）
- 列表页每次显示 30 条，「加载更多」再加 30；从首页进入列表、返回时恢复原滚动位置
- PS Plus 官方页只有名字和配图，前端按名字（去空格符号后前 5 个字符）在港服商店数据里找对应商品补价格和详情（`psFind`）
- 详情弹窗先用 data.json 里的基础信息渲染，再异步读 `ps_detail.json` 补评分、评测、版本；价格走势用 `ps_price_history` 画折线（少于 3 个点或价格没变过不画）；`Esc` 关闭
- 偏好记在 localStorage（`gd.` 前缀）：当前视图、Steam 排序 / 价格 / 折扣 / 好评筛选、只看史低、PS 列表排序、道具礼包切换、深浅色
- 右侧挂件每分钟刷新一次倒计时；订阅按钮把 `sales.ics` 地址换成 `webcal://`，另有复制链接按钮

---

## 本地运行

```
python3 scraper.py          # 只用标准库，无需 pip install，无需环境变量
python3 -m http.server 8801
# 打开 http://localhost:8801
```

- Python 版本：Actions 用 3.12，本地最低版本未确认
- 耗时：未确认（CheapShark 首次要逐个查编号；PS 详情和 Metacritic 补齐单次最多 12 分钟）
- 会改写 `data.json`、`ps_detail.json`、`sales.ics`

---

## 自动更新机制

工作流：`.github/workflows/scrape.yml`（`concurrency: scrape`，不取消进行中的运行）

| 触发方式 | 时机 |
|---|---|
| 定时任务 | 每 6 小时一次，北京时间 02:13 / 08:13 / 14:13 / 20:13（cron `13 */6 * * *`） |
| 定时任务（Epic） | 每周四 23:20 北京时间，Epic 限免刚更新后（cron `20 15 * * 4`） |
| push 到 main | 只有 `scraper.py` 或 `.github/workflows/scrape.yml` 改动时触发 |
| 手动 dispatch | Actions 页面手动运行（页面右上角 ⚡ 直达） |

- 运行后提交 `data.json`、`sales.ics`、`ps_detail.json`，提交信息 `data: update <北京时间>`，先 `git pull --rebase` 再 push
- **心跳**：`data.json` 的 `updated` 每次运行都会变，所以每次都有提交，仓库保持活跃
- GitHub 规定公开仓库 60 天没有提交会自动停用定时任务；靠上面的心跳避免。万一被停用，需要到 Actions 页面重新启用
