**專案名稱 & 概述**
- **名稱**: POS (簡易 Point-Of-Sale 範例應用)
- **說明**: 這是一個以 Python + FastAPI 實作的簡單 POS 後端服務，搭配靜態前端頁面（位於 `docs/`），示範商品管理、結帳與交易紀錄等功能。專案同時支援本機 sqlite 開發與以 `DATABASE_URL` 注入的 PostgreSQL（或其他支援的 DB）用於部署。

- **線上 Demo**:
  - **前端 (GitHub Pages)**: https://kaigiii.github.io/POS/
  - **後端 (Render)**: https://pos-lb9c.onrender.com

**技術棧**
- **後端框架**: `FastAPI`
- **資料庫 ORM**: `SQLAlchemy`（使用 declarative base）
- **伺服器 (開發/生產)**: `uvicorn`（開發） / `gunicorn`（可選）
- **語言 / 版本**: 建議使用 `Python 3.11.x`（`backend/runtime.txt` 指定 `python-3.11.9`）
- **相依套件**: 列於 `backend/requirements.txt`（包含 `fastapi`, `uvicorn`, `SQLAlchemy`, `python-dotenv`, `psycopg2-binary` 等）

**專案結構（重點檔案）**
- **`backend/app.py`**: FastAPI 應用主檔，包含所有 API 路由（產品 CRUD、結帳、交易查詢、初始化/重設資料等）。
- **`backend/db.py`**: 資料庫引擎與 `SessionLocal`、`Base` 設定；支援 `DATABASE_URL` 環境變數（會自動把 `postgres://` 轉為 `postgresql://`）。
- **`backend/models.py`**: ORM model 定義：`Product`, `Transaction`, `TransactionItem`。
- **`backend/init_db.py` / `backend/seed_fake_data.py`**: 初始化或重建測試資料的腳本。
- **`backend/requirements.txt`**: Python 相依套件。
- **`backend/Procfile` / `render.yaml`**: 部署到 Render 的設定範例。
- **`docs/`**: 範例前端靜態頁面（HTML + JS + CSS），與後端 API 配合使用。

**快速上手（macOS / zsh）**
1. 取得專案

```bash
git clone <repo-url>
cd POS
```

2. 建議建立虛擬環境並安裝套件

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

3. 本機環境變數（選用）
- 使用 sqlite（預設）：不需要額外設定，預設 `DATABASE_URL` 為 `sqlite:///pos.db` 並會在 `backend/` 位置建立 `pos.db`。
- 若要使用 PostgreSQL 或其他 DB，請設定 `DATABASE_URL`，例如：

```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
```

- 其他環境變數：
  - `ADMIN_KEY`：管理用金鑰（程序程式碼中存在 `X-ADMIN-KEY` 的檢查函式，但某些公開 endpoint 並未強制檢查，詳見安全注意事項）。
  - `ALLOW_DESTRUCTIVE=true`：允許破壞性操作（範例程式會以布林檢查此值）。

4. 啟動應用（開發）

```bash
cd backend
uvicorn app:app --reload --host 127.0.0.1 --port 5001
```

啟動後：
- Swagger UI: `http://127.0.0.1:5001/docs`
- 根目錄：`http://127.0.0.1:5001/` (回傳簡易狀態)

**部署（Render 範例）**
- 專案內包含 `render.yaml` 與 `backend/Procfile` 作為示範。
- Render buildCommand: `pip install -r backend/requirements.txt`，startCommand: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`。

- **線上環境 (示範)**:
  - 前端 (GitHub Pages): https://kaigiii.github.io/POS/
  - 後端 (Render): https://pos-lb9c.onrender.com

**資料庫與模型**
- 資料表由 `backend/models.py` 定義：
  - `Product`:
    - `id` (int, pk)
    - `name` (string, unique)
    - `price` (float)
    - `cost` (float)
    - `stock` (int)
  - `Transaction`:
    - `id`, `timestamp` (datetime), `total_amount` (float)
    - 與 `TransactionItem` 建立一對多關聯（`items`）
  - `TransactionItem`:
    - `transaction_id`, `product_id`, `quantity`, `price_at_sale`

- `backend/db.py`:
  - 會從 `DATABASE_URL` 讀取連線字串，若為 sqlite 會自動加 `check_same_thread=False`。
  - `init_db()` 呼叫會建立所有表格 (`Base.metadata.create_all`)。

**初始化與產生測試資料**
- 指令方式：

```bash
python backend/init_db.py       # minimal seed, 3 sample products
python backend/seed_fake_data.py  # 重建大量範例商品 + 隨機交易
```

- 也可以使用 API 呼叫（可被前端觸發）：
  - `POST /api/init_db` : 初始化並產生 sample data（回傳建立數量）
  - `POST /api/reset_seed` : 清空並重建 sample data

注意：目前 `app.py` 中 `POST /api/init_db` 與 `POST /api/reset_seed` 為公開可呼叫（無驗證），若要在公開環境使用，請務必保護這些路由（例如在實作中使用 `X-ADMIN-KEY` 或其他認證機制）。

**HTTP API 概覽**
- **GET /** : 健康檢查，回傳 `{'message': 'POS API Server', 'status': 'running', 'docs': '/docs'}`
- **GET /health** : 回傳 `{'status': 'ok'}`
- **GET /api/products** : 取得所有商品
- **POST /api/products** : 新增商品，Body 範例：

```json
{
  "name": "Bagel",
  "price": 2.5,
  "cost": 1.0,
  "stock": 50
}
```

- **GET /api/products/{product_id}** : 取得單一商品
- **PUT /api/products/{product_id}** : 更新商品（可部分更新）
- **DELETE /api/products/{product_id}** : 刪除商品
- **POST /api/checkout** : 結帳，Body 為 `[{"product_id": 1, "quantity": 2}, ...]`，成功會建立 `Transaction` 與多筆 `TransactionItem`，並自動扣庫存，回傳 `{'message': 'Checkout success', 'transaction_id': <id>}`。
- **GET /api/transactions** : 列出交易摘要（依時間降序）
- **GET /api/transactions/{transaction_id}** : 交易詳情（含 items）
- **POST /api/reset_seed** : 清空並用範例資料重建（由程式產生隨機價格與交易）
- **POST /api/init_db** : 建立資料表並產生範例資料（與 `/api/reset_seed` 類似）

更多互動式文件請啟動應用後造訪 `http://<host>:<port>/docs`。

**安全性與注意事項**
- `backend/app.py` 中提供了 `ALLOW_DESTRUCTIVE`（環境變數）與 `ADMIN_KEY`（可透過 `X-ADMIN-KEY` 標頭檢查）的參考機制；但目前某些破壞性路由（如 `init_db` / `reset_seed`）並未強制使用這些檢查，因此：
  - 建議在生產環境前確認或修改程式碼，將這些路由加上明確的驗證或限制（例如檢查 `X-ADMIN-KEY` 或在內部網路中呼叫）。
  - 若使用公開部署（Render 等），請設定 `DATABASE_URL` 與必要的密鑰（如 `ADMIN_KEY`），並限制誰能呼叫管理 API。

**開發建議與延伸功能**
- 把 `init_db` 與 `reset_seed` 的保護改成在路由內檢查 `_check_destructive(request)`，或使用 OAuth / API key 中介層。
- 加入單元測試（pytest）與 CI（GitHub Actions）以自動化測試核心邏輯（結帳、庫存變更等）。
- 將前端 `docs/` 改造成簡單 SPA，或接入更完整的管理介面。

**常見問題 (FAQ)**
- Q: 我該如何切換到 PostgreSQL？
  - A: 設定 `DATABASE_URL` 為 PostgreSQL 的連線字串（`postgresql://user:pass@host:port/dbname`），並安裝 `psycopg2-binary`（已在 `requirements.txt` 中）。
- Q: 資料會保存在哪？
  - A: 若不設定 `DATABASE_URL`，預設使用 `sqlite:///pos.db`，該檔會在啟動目錄（即 `backend/`）產生。若使用遠端 DB，則儲存在該資料庫中。

**參考檔案**
- 源碼主檔案: `backend/app.py`, `backend/models.py`, `backend/db.py`
- 初始化與種子: `backend/init_db.py`, `backend/seed_fake_data.py`
- 部署設定: `backend/Procfile`, `render.yaml`, `backend/runtime.txt`

---
如果你想我幫你：
- 把 `init_db`/`reset_seed` 加上 `X-ADMIN-KEY` 檢查並示範如何設定 `ADMIN_KEY`，或
- 撰寫一份簡單的 Postman / HTTPie 範例請求檔案，或
- 改寫前端 `docs/` 為一個更完整的管理介面，請告訴我下一步要做哪一項。

作者：自動由專案原始碼生成的 README（可由維護者編輯補充）
