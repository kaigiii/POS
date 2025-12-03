# 部署說明

## 前端 (GitHub Pages)
1. 將 frontend 資料夾內容推送至 GitHub repository。
2. 於 GitHub 設定 Pages，選擇 frontend 為靜態網站根目錄。
3. 確認 fetch API 呼叫的 URL 指向 Render 部署後的後端網址。

## 後端 (Render)
1. 建立 Render Web Service，選擇 Python。
2. 部署 backend 資料夾。
3. 設定環境變數：
   - PYTHONUNBUFFERED=1
   - FLASK_APP=app
4. 確認 requirements.txt 已包含 gunicorn。
5. Procfile 啟動命令：
   - web: gunicorn --bind 0.0.0.0:$PORT app:create_app()
6. 部署完成後，取得後端 API URL，更新前端 fetch 呼叫。

## Render

Environment variables (recommended)
- `DATABASE_URL` — PostgreSQL connection string from Render Managed Postgres (optional; if unset app falls back to sqlite)
- `SECRET_KEY` — random secret for Flask sessions / security
- `ALLOW_DESTRUCTIVE` — set to `1` or `true` to allow destructive endpoints (`/api/reset_seed` and `/api/init_db`) when `ADMIN_KEY` is not used. Use only temporarily; prefer `ADMIN_KEY` for safety.
- `ADMIN_KEY` — (recommended) a long random string. If present, destructive endpoints require the request header `X-ADMIN-KEY: <ADMIN_KEY>`; this is more secure than enabling `ALLOW_DESTRUCTIVE`.

How to deploy backend to Render (recommended flow)

1) Prepare repository & service
- Confirm your repository has the `backend/` folder at repo root and `requirements.txt` lists all dependencies including `gunicorn` and `flask_sqlalchemy`.
- Optional: add a `runtime.txt` with the Python version (e.g. `python-3.11.4`).

2) Create Render Managed Postgres (optional but recommended)
- In Render Dashboard, create a new "Database" → Postgres. Note the `DATABASE_URL` connection string.

3) Create a Render Web Service
- From Render Dashboard: New → Web Service → Connect to GitHub → choose `kaigiii/POS` → branch `main`.
- Build Command: leave blank or set to `pip install -r backend/requirements.txt` (Render auto-detects Python but explicit command can help).
- Start Command / Procfile: the repo contains a `Procfile` with `web: gunicorn --bind 0.0.0.0:$PORT app:create_app()` — Render will use it automatically.

4) Set Environment Variables (Render service settings)
- `PYTHONUNBUFFERED=1`
- `FLASK_APP=app`
- `DATABASE_URL` — paste connection string from Render Postgres (if using Postgres)
- `SECRET_KEY` — set a random value
- `ALLOW_DESTRUCTIVE` — leave unset in production. If you need to seed via HTTP temporarily set to `1` (not recommended for long periods).
- `ADMIN_KEY` — prefer this to allow secure destructive calls. If set, calls to `/api/reset_seed` and `/api/init_db` must include `X-ADMIN-KEY` header.

5) Initialization & seeding (safe options)
- Preferred (manual, safe): Use Render Dashboard → Service → Shell. Then run these inside the repo path (Render places code in `/opt/render/project/src`):
```bash
cd /opt/render/project/src/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py --create-tables-only  # (see note)
# or run init script if provided
python init_db.py         # create tables and minimal seed (if present)
python seed_fake_data.py  # optional: create sample products + transactions
```
Note: This repo's `app.py` already creates `db.create_all()` when run as script. If you prefer one-shot, run `python backend/app.py` from project root in the shell.

- Alternative (HTTP, less safe): Temporarily set `ALLOW_DESTRUCTIVE=1` or use `ADMIN_KEY`, then call endpoints:
```bash
# initialize (creates tables and seeds)
curl -X POST https://<your-service>.onrender.com/api/init_db -H "X-ADMIN-KEY: <ADMIN_KEY>"
# reset sample data (destructive)
curl -X POST https://<your-service>.onrender.com/api/reset_seed -H "X-ADMIN-KEY: <ADMIN_KEY>"
```

6) Verify deployment
- Visit your service URL `https://<your-service>.onrender.com/health` — should return `{"status":"ok"}`.
- Confirm endpoints: `/api/products`, `/api/transactions` behave as expected.

環境變數（建議）
- `SECRET_KEY` — 用於 Flask session/安全，請設定一個隨機字串。
- `PYTHONUNBUFFERED` — 設為 `1` 以便日誌即時輸出。
- `FLASK_APP` — 設為 `app`（Render 需要或 Procfile 使用）。
- `ALLOW_DESTRUCTIVE` / `ADMIN_KEY` — 若你之後需要用 HTTP 初始化或重設資料，建議使用 `ADMIN_KEY`（較安全），暫時才啟用 `ALLOW_DESTRUCTIVE`。

把後端在 Render 上「能正常運作」的最簡要步驟（不包含資料庫細節）

1) 確認 repo 結構
- 專案根目錄下有 `backend/` 資料夾與 `requirements.txt`（或在 `backend/requirements.txt`）。請確認 `requirements.txt` 列出 `gunicorn`、`flask`、`flask_sqlalchemy` 等必要套件。

2) 在本機測試後端能啟動
- 建議先在本機測試，確保沒有缺少依賴：
```bash
cd /Users/xiaojunjun/Desktop/POS
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python app.py
```
- 預設會在 `127.0.0.1:5001` 啟動，測試健康檢查：
```bash
curl http://127.0.0.1:5001/health
# 應回傳 {"status":"ok"}
```

3) 準備 Render 部署（快速指南）
- 在 Render 建立一個新的 Web Service 並連結到 `kaigiii/POS` 的 `main` 分支。
- Render 會讀取 `Procfile`（若有），本專案 `Procfile` 應包含：
```
web: gunicorn --bind 0.0.0.0:$PORT app:create_app()
```
- 若 Render 要你填 Build Command，可填：`pip install -r backend/requirements.txt`；或讓 Render 自動偵測。

4) 在 Render 的 Service 設定環境變數
- `PYTHONUNBUFFERED=1`
- `FLASK_APP=app`
- `SECRET_KEY=<一個隨機字串>`
- 如需呼叫破壞性 endpoint（初始化/重設），建立 `ADMIN_KEY=<長隨機字串>`，之後呼叫 API 時在 header 加 `X-ADMIN-KEY: <ADMIN_KEY>`。

5) 部署並驗證
- 推送到 `main` 後，Render 會自動部署（或按 Render UI 手動部署）。
- 驗證健康：
```bash
curl https://<your-service>.onrender.com/health
# 應回傳 {"status":"ok"}
```
- 測試主要 API：
```bash
curl https://<your-service>.onrender.com/api/products
```

6) 更新前端 API URL
- 部署成功後，將前端中的 `window.__API_URL__` 或對應 fetch 路徑改為 `https://<your-service>.onrender.com/api`。

本機測試小記
- 若要在本機以 sqlite 測試（簡單、無外部 DB）：`backend/app.py` 已在直接執行時呼叫 `db.create_all()`，因此直接執行 `python backend/app.py` 可建立 `pos.db` 並啟動服務。

補充建議
- 在正式環境避免長期開啟 `ALLOW_DESTRUCTIVE`，使用 `ADMIN_KEY` 加強保護破壞性 API。

## 測試
- 確認健康檢查 `/health` 正常回應。
- 確認 `/api/products`、`/api/transactions` 等主要 API 能正常操作。
