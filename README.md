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

- **🎮 PlayStation**（首页，`#ps`，港服，仿 Jump 列表样式）
  - 四个大标签：**最新 PS Plus**（每月会免 / 目录新增 / 目录内打折）、**最新折扣**（精选 / 全部 / 史低 / 大折扣 / 会员价 / 即将结束 / 中文，可按热度 / 折扣 / 价格 / 剩余时间排序）、**正在流行**（畅销 / 最多下载 / 免费游玩）、**最新发布**（新游戏 / 新游戏热门 / 预购）
  - 每行：方形封面、标签（中文 / 史低 / 预购 / 目录内 / 会员价 / PS5 / PS4）、发售日 · 发行商 · 类型、红色现价 + 划线原价、剩余天数、斜角折扣角标；电脑两列、手机一列，「加载更多」每次 30 条
  - 点一行弹出详情：截图轮播、英文名、发售日 / 发行商 / 类型 / 人数 / 语言、简介、价格与截止时间、「去 PS Store 购买」
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

## 数据来源

| 来源 | 内容 | 说明 |
|---|---|---|
| Epic 商店接口（国区） | 本周限免、下周预告、人民币原价 | 折后价为 0 的才算限免 |
| [GamerPower](https://www.gamerpower.com/) | 全平台免费游戏和道具礼包 | 带截止时间、已领人数 |
| Steam 商店搜索（`cc=cn`） | 热销特惠前 300：折扣、人民币价格、好评、封面 | 每 6 小时 |
| [CheapShark](https://www.cheapshark.com/) | 热销前 120 款的美区现价和历史最低 | appid → CheapShark 编号的对应关系缓存在 data.json，之后只查新游戏 |
| [Steamworks 文档 Upcoming Events](https://partner.steamgames.com/doc/marketing/upcoming_events) | Steam 官方大促日程 | 官方提前公布给开发者 |
| [PlayStation.Blog](https://blog.playstation.com/tag/playstation-plus/) RSS | PS Plus 每月游戏、游戏目录 | 英文标题，取自美区 |
| Xbox Game Pass 目录 + Microsoft Store 接口（港区） | 最近新增游戏、中文名、封面 | |

**限制**：
- 美区史低不等于国区史低；国区史低要靠本站逐天积累（最多保留 120 天）
- 特惠可能只持续几小时，数据每 6 小时更新，以商店页为准
- Switch eShop 港服没有可用的价格接口，暂不收录
- 某个来源失败时沿用上一次的数据，并在来源状态里标红

---

### PlayStation 港服说明

- 商店数据：PlayStation Store 官方 GraphQL（`web.np.playstation.com/api/graphql/v1/op`），请求头 `x-psn-store-locale-override: zh-hans-hk` 固定为港服（否则 Actions 的美国 IP 会拿到美区）。只能用前端白名单里的 persisted query hash，失效时「PS 港服商店」来源会变红，需要从商店页面的网络请求里取新 hash 更新 `PS_HASH`
- 使用的港服常驻分类：全部优惠、全部 PS5 游戏、新游戏、免费游玩、预购（活动专题分类会轮换，不用）
- 优惠按 30 天销量取前 600 款；各榜单每个取 48 款。其中约 120 款逐个查详情（`metGetConceptById`：英文名、发售日、发行商、类型、人数、简介、截图）和价格（`metGetPricingDataByConceptId`：折扣截止、会员价、是否在游戏目录）
- 详情缓存在 data.json 的 `_ps_cache`，30 天内不重复查；首次运行约 8 分钟，之后约 1 分钟
- 请求必须带 `content-type: application/json`，否则返回 400
- 没有媒体评分（Jump 上的 88 / 93 分），商店接口不提供
- PS Plus 会员内容：`playstation.com/zh-hans-hk/ps-plus/whats-new/` 服务端渲染页面；个别配图官方 CDN 返回 403 时不拿别的游戏的图顶替，页面上按名字借商店封面或显示占位
- 第三方追踪站（PSPrices、PSDeals 等）都有 Cloudflare 验证，标准库抓不了，所以「新低」靠自己积累价格历史

## 技术架构

```
GitHub Actions（每 6 小时 + 每周四 23:20 Epic 更新后 / 手动 / 修改爬虫后 push）
  ↓ python scraper.py（只用标准库）
  ↓ Epic + GamerPower + Steam 特惠 300 + CheapShark 史低 + Steam 大促 + PS Plus + Game Pass
  ↓ 合并国区价格历史（appid → {日期: 价格}），标记美区史低 / 国区新低
  ↓ 写入 data.json 和 sales.ics，commit（updated 每次都变 = 心跳，防止定时任务因 60 天不活跃被停用）
       ↓
GitHub Pages（index.html 读取同目录 data.json，筛选排序都在前端完成）
```

### data.json 结构

```
{
  "updated": "2026-10-21T11:17:00+08:00",
  "epic": [ { "title": "Bad Cheese", "kind": "now", "start": "…", "end": "2026-10-22T23:00+08:00", "worth": 40, "img": "…", "url": "…" } ],   // kind: now / next
  "giveaways": [ { "title": "…", "type": "game", "platforms": ["Steam"], "worth": "$9.99", "end": "…", "users": 1234, "url": "…" } ], // type: game / loot
  "steam": [ { "appid": 1091500, "title": "赛博朋克 2077", "discount": 70, "price": 89.4, "orig": 298, "review": "特别好评", "rate": 80,
               "reviews": 202469, "img": "…", "rank": 1, "usd": 17.99, "usd_lowest": 17.99, "usd_low": true, "cn_low": false, "cn_days": 1 } ],
  "events": [ { "name": "Winter Sale 2026", "cn": "冬季特卖", "start": "2026-12-17", "end": "2027-01-04" } ],
  "ps_plus": [ { "kind": "monthly", "month": "October", "games": ["F1 25", "…"], "url": "…" } ],
  "game_pass": [ { "id": "9P2FF14JZLL3", "title": "戰地風雲™ 6", "img": "…", "url": "…" } ],
  "summary": { "epic_now": ["…"], "epic_now_worth": 102, "epic_end": "…", "epic_next": ["…"], "giveaway_games": 17, "steam_lows": 52,
               "next_sale": { "name": "冬季特卖", "start": "2026-12-17", "end": "2027-01-04" } },        // 给 pages-dashboard，字段只增不减
  "price_history": { "1091500": { "2026-10-21": 89.4 } },
  "sources": [ { "name": "Epic 限免", "ok": true, "count": 4, "updated": "…" } ]
}
```

---

## 本地预览

```
python3 scraper.py        # 约 1～2 分钟（CheapShark 首次要逐个查编号）
python3 -m http.server 8801
# 打开 http://localhost:8801
```
