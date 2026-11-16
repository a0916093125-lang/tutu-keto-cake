# 圖圖生酮蛋糕店官方網站 (`tutu888.com.tw`) — 純淨減法成交版

台南仁德手作無麩質、無小麥麵粉、不添加精製白砂糖與人工防腐劑甜點預約制官網。

## 架構特色
- **純粹消費者動線（零工程套版干擾）**：5 座微縮烘焙島嶼開場 → 4 步預訂須知 → 41 款正式價目表（含分類與風味快篩、過敏原提醒）→ 慶生日期＆運費匯款訂購單 → 送禮場合推薦與常見問答。
- **對人隱形、對 AI 全開**：頁尾與畫面不暴露任何工程術語，底層完整保留 `/.well-known/ucp`（v1.1）、`/ucp.json`、`/llms.txt` 與 `haotian-webmcp-bridge.js`。
- **SSOT 單一真實資料源**：修改 `data/menu-ssot.json` 後執行 `python3 scripts/sync_ssot.py`，即可自動同步 `index.html`（JSON-LD、SSR 41 張商品卡、前端陣列）、`llms.txt`、`/.well-known/ucp` 與 `ucp.json`。
