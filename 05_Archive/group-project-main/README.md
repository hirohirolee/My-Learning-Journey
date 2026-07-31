# Group Project VM Deployment Package

這份資料夾是從 `D:\DATA\group-project-V1-main` 精簡複製出來的 VM 部署版本，只保留 GCP VM / Docker 部署需要的檔案。未包含 `.env`、`.git`、`.venv`、archive、Streamlit 支線、工具腳本、快取與產出 CSV。

## 專案用途

本專案是一套 AI 輿情監測與回覆儀表板：

- `FastAPI` 提供後端 API。
- `frontend/` 提供營運總覽、危機處理、趨勢分析與 AI 一鍵回覆介面。
- `Supabase` 作為主要資料來源與寫回位置。
- `models/` 的 ML 模型用於風險/危機機率判斷。
- `Gemini`、`Hugging Face` 等雲端模型可透過後端 proxy 產生回覆。
- 首次載入採 lazy loading，先載入最新一批資料，再於背景補齊完整資料。
- 前端已加入 PWA manifest 與 service worker，可支援安裝到手機主畫面與基本離線殼層快取。
- Dockerfile 已準備好，可直接在 GCP VM 上用 Docker 執行。

## 快速連結

| 項目 | 連結 / 路徑 |
|---|---|
| 正式 HTTPS 網址 | `https://group-project.35-221-246-156.sslip.io/` |
| 健康檢查 | `https://group-project.35-221-246-156.sslip.io/api/health` |
| GitHub repo | `https://github.com/jimm1218/group-project` |
| GCP VM | `group-project-vm` (`asia-east1-c`) |
| VM 專案路徑 | `/home/g791218cobras/group-project` |
| 完整部署操作手冊 | [`docs/GCP_VM_DEPLOYMENT_GUIDE.md`](docs/GCP_VM_DEPLOYMENT_GUIDE.md) |

如果要從零重建 GCP VM、Nginx HTTPS、GitHub Actions 或每日同步排程，請優先參考完整部署操作手冊。README 只保留專案總覽與常用部署摘要。

## 資料夾架構

```txt
group-project/
├─ .github/
│  └─ workflows/
│     └─ deploy-vm.yml
├─ backend/
│  ├─ api_server.py
│  ├─ ml_analyzer.py
│  └─ supabase_db.py
├─ data/
│  ├─ laws.txt
│  └─ menu.txt
├─ docs/
│  └─ GCP_VM_DEPLOYMENT_GUIDE.md
├─ frontend/
│  ├─ app.js
│  ├─ icon.svg
│  ├─ index.html
│  ├─ manifest.webmanifest
│  ├─ styles.css
│  ├─ sw.js
│  └─ tailwind.config.js
├─ models/
│  ├─ classifier.pkl
│  └─ vectorizer.pkl
├─ ops/
│  ├─ cloud-run-scheduler-create.ps1
│  ├─ vm-bootstrap.sh
│  ├─ vm-deploy.sh
│  └─ vm-cron-sync-new.sh
├─ prompts/
│  ├─ dashboard_reply_ollama_negative.txt
│  ├─ dashboard_reply_ollama_positive.txt
│  ├─ ml_prompts.py
│  ├─ pr_generator_ollama_negative.txt
│  ├─ pr_generator_ollama_positive.txt
│  ├─ pr_generator_openai_negative.txt
│  ├─ pr_generator_openai_positive.txt
│  ├─ pr_reviewer.txt
│  └─ sentiment_analyzer.txt
├─ .dockerignore
├─ .env.example
├─ .gitignore
├─ .python-version
├─ Dockerfile
├─ README.md
└─ requirements.txt
```

## 根目錄檔案說明

| 路徑 | 說明 |
|---|---|
| `Dockerfile` | VM / Docker 部署入口。使用 `python:3.12-slim`，安裝 `requirements.txt`，並以 `uvicorn api_server:app --host 0.0.0.0 --port $PORT` 啟動。 |
| `.dockerignore` | Docker build 時排除不必要或敏感檔案，例如 `.env`、`.venv`、`.git`、archive 與產出資料。 |
| `.env.example` | 環境變數範本。部署到 VM 時請自行建立 `.env`，不要把正式 key commit 到 Git。 |
| `.gitignore` | Git 忽略規則，避免密鑰、虛擬環境、快取與本機產物進入版本控制。 |
| `.python-version` | Python 版本提示，目前為 `3.12`。 |
| `requirements.txt` | Python 套件依賴清單，Docker build 與本機安裝都會使用。 |
| `README.md` | 本文件，說明部署包內容與資料夾架構。 |

## `docs/` 文件

| 路徑 | 說明 |
|---|---|
| `docs/GCP_VM_DEPLOYMENT_GUIDE.md` | GCP VM 部署操作手冊。逐步說明要在哪個介面操作、要輸入什麼指令、如何設定 Docker、Nginx HTTPS、GitHub Actions、Static IP 與每日同步排程。 |

## `.github/` GitHub Actions

| 路徑 | 說明 |
|---|---|
| `.github/workflows/deploy-vm.yml` | 當 `main` 分支有新 commit 時，自動 SSH 到 GCP VM，拉 GitHub 最新版本，重建 Docker image 並重啟 container。也支援手動按 `Run workflow` 部署。 |

## `backend/` 後端服務

| 路徑 | 說明 |
|---|---|
| `backend/api_server.py` | FastAPI 主程式。提供 Dashboard API、Supabase 查詢/同步、AI 回覆 proxy、健康檢查與前端靜態檔掛載。 |
| `backend/supabase_db.py` | Supabase 連線與資料表讀寫邏輯，包含查詢原始評論、讀取分析結果、upsert 分析欄位與寫回回覆。 |
| `backend/ml_analyzer.py` | ML 分析相關輔助邏輯，保留給後端分析流程使用。 |

主要 API：

| API | 說明 |
|---|---|
| `GET /` | 回傳前端首頁。 |
| `GET /dashboard` | 回傳前端首頁。 |
| `GET /api/health` | 健康檢查。 |
| `GET /api/supabase-query` | Dashboard 前端讀取 Supabase 分析結果。 |
| `POST /api/ml-dashboard/sync` | 手動或排程同步資料，將原始評論分析後寫入 `master_reviews_result`。 |
| `POST /api/ai-reply` | Gemini / Hugging Face 等雲端模型的後端 proxy。 |
| `POST /api/reviews/resolve` | 將回覆內容寫回資料庫並結案。 |

## `frontend/` 前端介面

| 路徑 | 說明 |
|---|---|
| `frontend/index.html` | 主要 Dashboard HTML。包含營運總覽、危機處理、深度趨勢、AI 一鍵回覆等介面。 |
| `frontend/app.js` | 前端互動邏輯。包含 lazy loading 資料載入、同步按鈕、圖表渲染、篩選器、PWA service worker 註冊、AI provider 選擇與回覆產生流程。 |
| `frontend/styles.css` | 自訂樣式與 RWD 設定，包含手機版底部導覽、事件列表與多選篩選器；`<768px` 時事件篩選下拉選單靠右對齊。 |
| `frontend/tailwind.config.js` | Tailwind CSS 設定，定義色票、陰影與其他設計 token。 |
| `frontend/manifest.webmanifest` | PWA manifest，定義 app 名稱、顏色、啟動 URL、display 模式與 icon。 |
| `frontend/sw.js` | PWA service worker，快取前端殼層檔案，API 請求維持走網路。 |
| `frontend/icon.svg` | PWA / favicon 使用的 SVG 圖示。 |

## Lazy Loading 資料載入

前端預設首批只載入最新 `200` 筆資料：

```txt
GET /api/supabase-query?...&limit=200
```

畫面先完成初始渲染後，會在背景再呼叫完整查詢補齊資料。背景資料載入完成後，圖表、篩選器與事件清單會自動刷新。

相關設定位於：

```js
const INITIAL_DATA_LIMIT = 200;
```

如需調整首批筆數，可修改 `frontend/app.js` 的 `INITIAL_DATA_LIMIT`。

## PWA 支援

本專案已包含基本 PWA 架構：

- `frontend/manifest.webmanifest`
- `frontend/sw.js`
- `frontend/icon.svg`
- `frontend/index.html` 內的 manifest、theme color 與 icon 設定
- `frontend/app.js` 內的 `registerServiceWorker()`

注意：service worker 只快取前端殼層與靜態檔，`/api/` 請求不快取，避免 Dashboard 顯示過期資料。

## `data/` 參考資料

| 路徑 | 說明 |
|---|---|
| `data/laws.txt` | 負面/高風險回覆時可參考的法務或消保相關文字。 |
| `data/menu.txt` | 正面或一般體驗回覆時可參考的品牌/菜單資訊。 |

未包含 `data/ml_dashboard_export.csv`，因為它是同步流程產生的本機輸出，不是部署必要檔案。

## `models/` ML 模型

| 路徑 | 說明 |
|---|---|
| `models/classifier.pkl` | 已訓練的分類模型，用於判斷評論風險/危機機率。 |
| `models/vectorizer.pkl` | 文字向量化模型，與 `classifier.pkl` 搭配使用。 |

這兩個檔案是後端啟動時會嘗試載入的模型檔，因此有保留在部署包內。

## `ops/` 部署與排程輔助腳本

| 路徑 | 說明 |
|---|---|
| `ops/cloud-run-scheduler-create.ps1` | 在 Windows PowerShell 建立 Cloud Scheduler job，每天呼叫 Cloud Run 同步 API，只同步新增資料。 |
| `ops/vm-bootstrap.sh` | 第一次設定 GCP VM 用。安裝 Git / Docker、clone GitHub repo 到 `APP_DIR`，並準備 `.env`。若未指定 `APP_DIR`，預設為 `/opt/group-project`。目前線上 VM 使用 `/home/g791218cobras/group-project`。 |
| `ops/vm-deploy.sh` | VM 部署腳本。會在 VM 上 build Docker image、移除舊 container、用 `.env` 啟動最新版服務。 |
| `ops/vm-cron-sync-new.sh` | 在 GCP VM Linux 主機上給 cron 使用的同步腳本，會呼叫本機服務的同步 API，只同步新增資料。 |

## `prompts/` 提示詞模板

| 路徑 | 說明 |
|---|---|
| `prompts/dashboard_reply_ollama_negative.txt` | Dashboard 負面評論回覆模板。 |
| `prompts/dashboard_reply_ollama_positive.txt` | Dashboard 正面評論回覆模板。 |
| `prompts/ml_prompts.py` | ML / LLM 分析用提示詞輔助內容。 |
| `prompts/pr_generator_ollama_negative.txt` | Ollama 負面公關回覆生成模板。 |
| `prompts/pr_generator_ollama_positive.txt` | Ollama 正面公關回覆生成模板。 |
| `prompts/pr_generator_openai_negative.txt` | OpenAI 負面公關回覆生成模板，保留供舊流程或未來擴充使用。 |
| `prompts/pr_generator_openai_positive.txt` | OpenAI 正面公關回覆生成模板，保留供舊流程或未來擴充使用。 |
| `prompts/pr_reviewer.txt` | 回覆審查/修正流程的提示詞。 |
| `prompts/sentiment_analyzer.txt` | 情緒分析流程的提示詞。 |

## 未複製的內容

| 原始內容 | 不複製原因 |
|---|---|
| `.env` | 包含正式 Supabase / AI API key，不應放進部署包或 Git。請在 VM 上自行建立。 |
| `.git/` | 版本控制資料，不是 VM 執行必要內容。若要版本控管，建議在新資料夾重新 `git init` 或推到 GitHub。 |
| `.venv/` | 本機 Python 虛擬環境，Docker 會重新安裝依賴。 |
| `archive/` | 歷史原型與舊部署資料，不是目前 VM 部署主線。 |
| `frontend/archive_v1/` | 前端舊版備份，不是目前正式介面。 |
| `streamlit/` | Streamlit 支線，不是目前 FastAPI + Docker 主線部署。 |
| `tools/` | 本機輔助工具，不是 VM 執行必要內容。 |
| `data/ml_dashboard_export.csv` | 同步流程輸出的產物，可由程式重新產生。 |
| `__pycache__/` | Python 快取，可由執行環境自行產生。 |

## VM 部署準備

完整逐步版請看：

```txt
docs/GCP_VM_DEPLOYMENT_GUIDE.md
```

在 GCP VM 上建議使用 Ubuntu 22.04 / 24.04，並安裝 Docker：

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

登出 SSH 再重新登入，讓 docker group 生效。

## 環境變數

請在 VM 上建立 `.env`，可從 `.env.example` 複製後填入正式值：

```bash
cp .env.example .env
nano .env
```

常用必要欄位：

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_KEY=
SUPABASE_TABLE_NAME=master_reviews
SUPABASE_RESULT_TABLE_NAME=master_reviews_result
ENGINE=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
GEMINI_API_KEY=
HUGGINGFACE_API_KEY=
ML_GATEKEEPER_THRESHOLD=0.7
```

若 VM 不跑 Ollama，正式線上使用建議以前端選擇 Gemini 或 Hugging Face。

## Docker 執行方式

本機或 VM 都可使用：

```bash
docker build -t group-project .
docker run -d \
  --name group-project \
  --env-file .env \
  -p 80:8080 \
  --restart unless-stopped \
  group-project
```

啟動後可測試：

```txt
http://VM_EXTERNAL_IP/
http://VM_EXTERNAL_IP/api/health
```

若使用 Artifact Registry 的 image，可改成：

```bash
docker run -d \
  --name group-project \
  --env-file .env \
  -p 80:8080 \
  --restart unless-stopped \
  asia-east1-docker.pkg.dev/group-project-503201/group-project-repo/group-project-v1:latest
```

## 每天自動只同步新增

同步 API 已支援只同步新增資料：

```txt
POST /api/ml-dashboard/sync?dry_run=false&force=false
```

其中 `force=false` 代表不重跑已存在於 `master_reviews_result` 的資料，只處理新增的原始評論。前端手動同步按鈕也會保留，兩者可並存。

### Cloud Run：使用 Cloud Scheduler

如果服務部署在 Cloud Run，可用 Cloud Scheduler 每天固定時間呼叫同步 API。

PowerShell 範例已放在：

```txt
ops/cloud-run-scheduler-create.ps1
```

預設設定：

| 設定 | 值 |
|---|---|
| Job name | `daily-dashboard-sync-new` |
| Region | `asia-east1` |
| Schedule | `0 3 * * *` |
| Time zone | `Asia/Taipei` |
| URL | `https://group-project-v1-320496839513.asia-east1.run.app/api/ml-dashboard/sync?dry_run=false&force=false` |
| Method | `POST` |

執行方式：

```powershell
cd D:\DATA\group-project
.\ops\cloud-run-scheduler-create.ps1
```

若 Cloud Scheduler job 已存在，可到 GCP Console 的 `Cloud Scheduler` 頁面修改或刪除後重建。

### GCP VM：使用 cron

如果服務部署在 GCP VM，並用 Docker 對外映射：

```bash
docker run -d \
  --name group-project \
  --env-file .env \
  -p 80:8080 \
  --restart unless-stopped \
  group-project
```

則 VM 主機本機可呼叫：

```txt
http://127.0.0.1:8080/api/ml-dashboard/sync?dry_run=false&force=false
```

先讓腳本可執行：

```bash
chmod +x /path/to/group-project/ops/vm-cron-sync-new.sh
```

編輯 cron：

```bash
crontab -e
```

每天台灣時間早上 7 點同步一次：

```cron
CRON_TZ=Asia/Taipei
0 7 * * * APP_URL=http://127.0.0.1:8080 /path/to/group-project/ops/vm-cron-sync-new.sh >> /path/to/group-project/logs/daily-sync.log 2>&1
```

也可以改整台 VM 的時區：

```bash
sudo timedatectl set-timezone Asia/Taipei
```

手動測試：

```bash
APP_URL=http://127.0.0.1:8080 /path/to/group-project/ops/vm-cron-sync-new.sh
```

## 更新部署

### GitHub push 自動部署到 GCP VM

建議正式使用這條流程：

```txt
本機修改程式碼 -> push 到 GitHub main -> GitHub Actions SSH 到 GCP VM -> VM git pull/reset -> Docker rebuild/restart
```

這樣 GCP VM 會永遠跑 GitHub `main` 分支的最新版，不需要手動把檔案複製到 VM。

#### 1. 先把專案推到 GitHub

在本機專案根目錄：

```bash
git init
git add .
git commit -m "Initial VM deploy package"
git branch -M main
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin main
```

請把 `OWNER/REPO` 換成你的 GitHub repo。

#### 2. 第一次設定 GCP VM

SSH 進 VM 後執行：

```bash
curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/ops/vm-bootstrap.sh -o vm-bootstrap.sh
chmod +x vm-bootstrap.sh
./vm-bootstrap.sh https://github.com/OWNER/REPO.git
```

如果 GitHub repo 是 private，VM 需要有讀取 repo 的權限。建議使用 GitHub deploy key，或把 clone URL 換成 SSH 格式：

```bash
./vm-bootstrap.sh git@github.com:OWNER/REPO.git
```

腳本會把專案 clone 到：

```txt
/opt/group-project
```

第一次執行後請編輯 VM 上的 `.env`：

```bash
cd /opt/group-project
nano .env
```

填好正式環境變數後，手動部署一次：

```bash
./ops/vm-deploy.sh
```

測試：

```txt
http://VM_EXTERNAL_IP:8080/
http://VM_EXTERNAL_IP:8080/api/health
```

目前線上 HTTPS 網址：

```txt
https://group-project.35-221-246-156.sslip.io/
https://group-project.35-221-246-156.sslip.io/api/health
```

如果你要用 80 port，可以改用：

```bash
HOST_PORT=80 ./ops/vm-deploy.sh
```

#### 3. 建立 GitHub Actions SSH key

在本機產生一組專門給 GitHub Actions 用的 SSH key：

```bash
ssh-keygen -t ed25519 -C "github-actions-gcp-vm" -f ./github-actions-gcp-vm
```

把 public key 加到 VM：

```bash
ssh-copy-id -i ./github-actions-gcp-vm.pub VM_USER@VM_EXTERNAL_IP
```

如果 Windows 沒有 `ssh-copy-id`，可以手動把 `github-actions-gcp-vm.pub` 內容貼到 VM 的：

```txt
~/.ssh/authorized_keys
```

#### 4. 設定 GitHub Secrets

到 GitHub repo：

```txt
Settings -> Secrets and variables -> Actions -> New repository secret
```

新增：

| Secret 名稱 | 說明 |
|---|---|
| `GCP_VM_HOST` | VM 外部 IP，例如 `34.xxx.xxx.xxx`。 |
| `GCP_VM_USER` | SSH 使用者，例如 `your-linux-user`。 |
| `GCP_VM_SSH_KEY` | 剛剛產生的 private key，也就是 `github-actions-gcp-vm` 檔案完整內容。 |
| `GCP_VM_PORT` | SSH port，通常是 `22`。可省略。 |
| `GCP_VM_APP_DIR` | VM 專案路徑，預設 `/opt/group-project`。可省略。 |

目前線上 VM 對應值：

| Secret 名稱 | 目前值 |
|---|---|
| `GCP_VM_HOST` | `35.221.246.156` |
| `GCP_VM_USER` | `g791218cobras` |
| `GCP_VM_PORT` | `22` |
| `GCP_VM_APP_DIR` | `/home/g791218cobras/group-project` |

不要把 `.env` 放進 GitHub Secrets 給 Actions 寫入 VM。正式 `.env` 建議只留在 VM 上，GitHub Actions 只負責更新程式碼與重啟服務。

#### 5. 之後如何更新

以後只要：

```bash
git add .
git commit -m "Update dashboard"
git push
```

GitHub Actions 就會自動 SSH 到 VM，執行 `git reset --hard origin/main`，再用 `bash ops/vm-deploy.sh` 重建並重啟 Docker。你也可以到：

```txt
GitHub repo -> Actions -> Deploy to GCP VM
```

手動按 `Run workflow` 重新部署。

### 手動更新 VM 部署

如果暫時不使用 GitHub Actions，也可以手動 SSH 到 VM：

```bash
cd /opt/group-project
git fetch origin main
git reset --hard origin/main
./ops/vm-deploy.sh
```

### Artifact Registry 手動更新

如果程式碼更新且你仍想走 Artifact Registry：

1. 在本機或 CI 重新 build image。
2. 推送到 Artifact Registry 或複製到 VM。
3. 在 VM 上重新拉取並重啟 container：

```bash
docker pull asia-east1-docker.pkg.dev/group-project-503201/group-project-repo/group-project-v1:latest
docker stop group-project
docker rm group-project
docker run -d \
  --name group-project \
  --env-file .env \
  -p 80:8080 \
  --restart unless-stopped \
  asia-east1-docker.pkg.dev/group-project-503201/group-project-repo/group-project-v1:latest
```

## 安全提醒

- 不要把 `.env` commit 到 GitHub。
- VM 防火牆只開需要的 port，例如 80 / 443。
- 若要正式對外服務，建議加上 HTTPS、網域與反向代理，例如 Nginx + Let's Encrypt。
- 若保留同步 API 公開呼叫，建議未來加上管理驗證或排程專用 token，避免外部任意觸發同步。
