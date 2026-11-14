# 圖圖生酮蛋糕店官方網站 (`tutu888.com.tw`)

台南仁德手作無麩質、無小麥麵粉、無添加精製砂糖甜點預約制官網。

## 架構亮點（v2.0 全方位 `*EO` + UCP 升級版）
- **零外部阻塞依賴（Pure CSS3 + Vanilla JS）**：移除執行期 Tailwind Play CDN，預編譯精簡原生樣式並將 5 座 3D 微縮島嶼轉為獨立高畫質 WebP（`/assets/*.webp`），大幅提升手機 LCP 與互動流暢度。
- **41 款商品靜態預渲染（SSR Static HTML）+ 結構化資料**：初始 HTML 直接內建完整 18 大系列 41 款商品卡片與 `Bakery` / `Menu` / `FAQPage` JSON-LD。
- **AI 檢索與商務探索（GEO + UCP）**：同步維護 `/llms.txt` 與 `/.well-known/ucp`（及 `ucp.json`），支援生成式搜尋與 AI 代理精準報價。
- **高轉換湊單體驗（CRO + SMO）**：內建台灣時區動態檔期防呆、同義詞智慧搜尋、手機底部即時免運差額懸浮列，以及 `#cart=...` 親友湊滿 NT$2,000 免運專屬分享連結。
