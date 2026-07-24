# Streamlit Cloud 部署指南

本專案建議用 `streamlit_dashboard.py` 作為 Streamlit Community Cloud 入口。這個入口會讀取 Supabase 資料、套用本機 ML 模型或 fallback 規則，並把資料注入 `index.html` 內嵌顯示。

## 1. 必要檔案

部署到 GitHub 前，確認以下檔案都有被提交：

```text
streamlit_dashboard.py
index.html
requirements.txt
.streamlit/config.toml
models/classifier.pkl
models/vectorizer.pkl
data/laws.txt
data/menu.txt
prompts/
```

`data/ml_dashboard_export.csv` 是執行時產生的暫存輸出，不需要提交。

## 2. Streamlit Cloud 建立 App

在 Streamlit Cloud 建立 app 時填入：

```text
Repository: 你的 GitHub repository
Branch: main
Main file path: group-project/streamlit_dashboard.py
```

如果 GitHub repo 的根目錄就是 `group-project`，Main file path 改填：

```text
streamlit_dashboard.py
```

## 3. Secrets 設定

到 Streamlit Cloud：

```text
App settings -> Secrets
```

貼上 `.streamlit/secrets.toml.example` 的內容，並把範例值換成正式值。

最少需要：

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-supabase-key-for-server-side-read"
SUPABASE_PUBLIC_KEY = "your-supabase-anon-public-key-for-browser-submit"
SUPABASE_TABLE_NAME = "master_reviews_result"
DASHBOARD_LIMIT = "0"
```

`DASHBOARD_LIMIT = "0"` 代表讀取全部資料。只有在想限制筆數時，才改成例如 `"500"`。

`SUPABASE_PUBLIC_KEY` 必須使用 Supabase 的 anon/public key，不能使用 `service_role` 或 `sb_secret_` secret key。這個 key 會提供給瀏覽器，用於提交 AI 回覆寫回 `master_reviews_result.reviews_response`。

如果提交 AI 回覆時顯示成功但資料沒有寫回，或顯示 `未更新任何資料列`，請確認 `master_reviews_result` 有允許 anon/public key 更新的 RLS policy。可以在 Supabase SQL Editor 依你的安全需求調整，例如：

```sql
alter table public.master_reviews_result enable row level security;

create policy "Allow dashboard read result rows"
on public.master_reviews_result
for select
to anon
using (true);

create policy "Allow dashboard update reply fields"
on public.master_reviews_result
for update
to anon
using (true)
with check (true);
```

上面範例會讓 anon key 可讀與可更新整張 `master_reviews_result`，正式環境建議再加上品牌、登入身分或其他條件限制。

如果要啟用 OpenAI 相關功能，再加入：

```toml
OPENAI_API_KEY = "sk-..."
```

不要提交 `.streamlit/secrets.toml` 或 `.env` 到 GitHub。

## 4. 本機測試

先在本機確認 Streamlit 版能跑：

```powershell
cd D:\data\group-project
python -m pip install -r requirements.txt
streamlit run streamlit_dashboard.py
```

本機可以用 `.env`，雲端則使用 Streamlit Secrets。

## 5. 部署後檢查

部署完成後確認：

- 頁面可以成功載入。
- Dashboard 有讀到 Supabase 資料。
- 深度趨勢圖表可點選並顯示下方事件清單。
- 若模型檔沒有載入，頁面仍會用 fallback 規則顯示資料。
- 側邊或頁面上沒有顯示任何密鑰。

## 6. 常見問題

### ModuleNotFoundError

代表 `requirements.txt` 少了套件。把錯誤訊息中的套件加入 `requirements.txt` 後重新部署。

### Supabase 沒資料

檢查 Secrets：

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_TABLE_NAME`

也要確認 Supabase key 有讀取 `master_reviews` 的權限。

### App build 太久或失敗

Streamlit Cloud 會安裝 `requirements.txt`。如果部署變慢，優先移除 Streamlit 入口沒有用到的重型套件，或另外拆一份更精簡的部署分支。

### 檔案寫入沒有永久保存

Streamlit Cloud 的檔案系統是暫存環境。`data/ml_dashboard_export.csv` 可以作為當次下載用，不適合當永久資料庫。永久保存請寫回 Supabase 或雲端儲存。

## 7. 參考官方文件

- Streamlit Community Cloud 部署：https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- App dependencies：https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- Secrets management：https://docs.streamlit.io/develop/concepts/connections/secrets-management
