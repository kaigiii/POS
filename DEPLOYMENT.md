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
- `ALLOW_DESTRUCTIVE` — set to `1` or `true` to allow destructive endpoints (`/api/reset_seed` and `/api/init_db`) when `ADMIN_KEY` is not used. Use only temporarily.
- `ADMIN_KEY` — (recommended) a long random string. If present, destructive endpoints require the request header `X-ADMIN-KEY: <ADMIN_KEY>`; this is more secure than enabling `ALLOW_DESTRUCTIVE`.

How to initialize / seed data on Render
- Option 1 (manual, safest): Use Render Dashboard → Service → Shell, then run:
```bash
cd /opt/render/project/src/backend
python3 init_db.py         # create tables and minimal seed
python3 seed_fake_data.py  # (optional) create sample products + transactions
```
- Option 2 (via HTTP): Temporarily set `ALLOW_DESTRUCTIVE=1` in Environment, then POST to the endpoints:
```bash
# initialize
curl -X POST https://<your-service>.onrender.com/api/init_db
# reset sample data (destructive)
curl -X POST https://<your-service>.onrender.com/api/reset_seed
```
   If you use `ADMIN_KEY` instead, include header `-H "X-ADMIN-KEY: <ADMIN_KEY>"` in the curl calls and do NOT set `ALLOW_DESTRUCTIVE`.
## 測試
- 確認所有頁面功能正常。
- 結帳後庫存會正確減少。
- 交易記錄可正確顯示明細。
