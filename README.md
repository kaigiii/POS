# POS 系統 (Frontend + Flask Backend)

簡短說明
- 這是一個以 Vanilla HTML/CSS/JS 作為前端，Flask + SQLAlchemy (SQLite) 為後端的銷售時點 POS 範例專案。
- 功能範圍：產品管理（CRUD）、收銀結帳（含交易與明細）、交易查詢與匯出、範例資料重置。

目錄結構（重要檔案）
- `backend/`
  - `app.py` - Flask 應用與 REST API
  - `seed_fake_data.py` - 範例資料建立與 `reset_data(app)` 函式
  - `init_db.py` - 初次建立資料庫的腳本
  - `pos.db` - SQLite 資料庫（若有）
  - `requirements.txt` - Python 相依套件
- `frontend/`
  - `index.html` - 銷售頁 (POS)
  - `products.html` - 產品管理頁
  - `transactions.html` - 交易紀錄頁
  - `styles.css` - 全站樣式
  - `posLogic.js`, `productManager.js`, `transactionViewer.js` - 各頁面 JS

先決條件（開發環境）
- macOS / Linux / WSL 或任支援 Python 的環境
- Python 3.10+ 建議
- 建議使用虛擬環境（venv）

快速起步（Backend）
```bash
cd /Users/xiaojunjun/Desktop/POS/backend
# 建議建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

啟動後端（開發模式）
```bash
# 在 backend 目錄下
python3 app.py
# 或在背景啟動（會把輸出導到 server.log）
nohup python3 app.py > server.log 2>&1 &
```
- 伺服器預設綁定 `127.0.0.1:5001`，前端的 `API_URL` 指向 `http://127.0.0.1:5001/api`。
- 若改用 `gunicorn`：
```bash
gunicorn --bind 127.0.0.1:5001 app:create_app()
# 背景啟動（zsh）：
nohup sh -c 'gunicorn --bind 127.0.0.1:5001 app:create_app()' > server.log 2>&1 &
```

資料庫初始化 & 範例資料
- 若 `pos.db` 不存在，`python3 app.py` 會自動建立資料表。
- 你可以執行範例資料腳本：
```bash
# 直接執行會清除並重新建立範例資料
python3 seed_fake_data.py
# 或透過後端提供的 API（開發用途）：
# POST http://127.0.0.1:5001/api/reset_seed
```

快速檢查 API
```bash
curl -i http://127.0.0.1:5001/api/products
curl -i -X POST http://127.0.0.1:5001/api/reset_seed
```

主要 API（摘要）
- `GET /api/products` - 列出所有產品
- `POST /api/products` - 新增產品
- `GET /api/products/<id>` - 取得單一產品
- `PUT /api/products/<id>` - 更新產品
- `DELETE /api/products/<id>` - 刪除產品
- `POST /api/checkout` - 建立交易（傳入購物車陣列，返回 transaction_id）
- `GET /api/transactions` - 列出交易
- `GET /api/transactions/<id>` - 取得某筆交易明細
- `POST /api/reset_seed` - 重設並建立範例資料（開發 / 本機用途，會清除資料）

前端（快速預覽）
- 直接以瀏覽器打開 `frontend/index.html`、`frontend/products.html` 或 `frontend/transactions.html` 即可（開發時以 `file://` 觀看或以簡單靜態伺服器）。
- 若前端與後端不在同一 host:port，請確認後端 CORS 設定允許來源（目前後端啟用 CORS *）。

部署提示
- 生產部署請使用 WSGI 伺服器（`gunicorn`），並放置在適當的反向代理後方（例如 nginx）。
- 注意安全性：`/api/reset_seed` 與任何破壞性 API 在生產環境應移除或受身分驗證保護。

開發與測試建議
- 在本機使用虛擬環境測試套件與執行環境整合。
- 若要自動化測試，可撰寫 pytest 測試對 `app.create_app()` 做工廠建立並使用 sqlite in-memory 測試資料庫。

若要我代勞
- 幫你跑一次 `seed_fake_data.py` 並把結果與伺服器狀態回報。
- 或將前端改為以簡單 `http-server` 或 Flask static serve 提供，方便在瀏覽器做跨-origin 測試。

---
*README 由專案腳本協助建立，如需更多客製化資訊（例如環境變數、持續整合指示、dockerfile 等），請告訴我。*
