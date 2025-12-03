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

## 測試
- 確認所有頁面功能正常。
- 結帳後庫存會正確減少。
- 交易記錄可正確顯示明細。
