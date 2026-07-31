# GCP VM 部署流程操作手冊

這份文件是 `jimm1218/group-project` 的 GCP VM 部署操作手冊。它會明確標示每一步要在哪個介面操作，以及要輸入什麼指令或填什麼欄位。

## 0. 目前線上資訊

| 項目 | 目前值 |
|---|---|
| GCP project | `group-project-503201` |
| VM instance | `group-project-vm` |
| Zone | `asia-east1-c` |
| VM 外部 IP | `35.221.246.156` |
| SSH user | `g791218cobras` |
| GitHub repo | `https://github.com/jimm1218/group-project` |
| VM 專案路徑 | `/home/g791218cobras/group-project` |
| Docker image | `group-project-vm:latest` |
| Docker container | `group-project-vm` |
| Container port | `8080` |
| HTTP 測試網址 | `http://35.221.246.156:8080/` |
| HTTPS 正式網址 | `https://group-project.35-221-246-156.sslip.io/` |
| Nginx 設定檔 | `/etc/nginx/sites-available/group-project` |
| 每日同步 log | `/home/g791218cobras/group-project/logs/daily-sync.log` |

整體架構：

```text
使用者瀏覽器
  -> https://group-project.35-221-246-156.sslip.io/
  -> GCP VM 443 port
  -> Nginx
  -> http://127.0.0.1:8080
  -> Docker container group-project-vm
  -> FastAPI + frontend static files
  -> Supabase / AI provider
```

自動部署流程：

```text
本機修改程式碼
  -> git push origin main
  -> GitHub Actions
  -> SSH 連進 GCP VM
  -> git fetch/reset
  -> bash ops/vm-deploy.sh
  -> Docker build + restart
```

## 1. 建立 GCP VM

### 操作介面

```text
GCP Console 網頁
```

### 操作路徑

```text
Google Cloud Console
-> Compute Engine
-> VM instances
-> Create instance
```

### 建議填寫

| 欄位 | 建議值 |
|---|---|
| Name | `group-project-vm` |
| Region | `asia-east1` |
| Zone | `asia-east1-c` |
| Machine type | 可先用預設或 e2 系列 |
| Boot disk | Ubuntu 22.04 LTS 或 Ubuntu 24.04 LTS |
| Firewall | 勾選 `Allow HTTP traffic` 和 `Allow HTTPS traffic` |

建立完成後，在 VM instances 頁面記下：

```text
External IP
```

目前你的外部 IP 是：

```text
35.221.246.156
```

## 2. 將 VM IP 改成 Static external IP

這一步建議做，否則 VM 重開或重建後 IP 可能改變，HTTPS 網域和 DNS 會失效。

### 操作介面

```text
GCP Console 網頁
```

### 操作路徑

```text
Google Cloud Console
-> VPC network
-> IP addresses
-> External IP addresses
```

### 操作步驟

找到目前 VM 的 IP：

```text
35.221.246.156
```

點右側三點選單：

```text
Promote to static IP address
```

名稱可以填：

```text
group-project-vm-ip
```

按：

```text
Reserve
```

## 3. SSH 進 VM

### 操作介面

```text
GCP Console 網頁
```

### 操作路徑

```text
Compute Engine
-> VM instances
-> group-project-vm
-> SSH
```

點下去後會開啟 VM 的瀏覽器終端機。

之後文件中標示：

```text
輸入位置：VM SSH 終端機
```

代表要在這個 SSH 視窗裡輸入。

## 4. 在 VM 安裝 Git 和 Docker

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
sudo apt-get update
sudo apt-get install -y git docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

執行完後，請關掉 SSH 視窗，再重新從 GCP Console 點一次 SSH。

重新登入後檢查：

```bash
git --version
docker --version
docker ps
```

如果 `docker ps` 不需要 `sudo` 就能跑，代表 Docker 權限正常。

## 5. 把 GitHub 專案 clone 到 VM

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
cd /home/g791218cobras
git clone https://github.com/jimm1218/group-project.git
cd group-project
```

確認目前路徑：

```bash
pwd
```

應該看到：

```text
/home/g791218cobras/group-project
```

確認檔案：

```bash
ls -la
```

應該看到：

```text
Dockerfile
backend
frontend
ops
requirements.txt
```

## 6. 建立 VM 的正式 `.env`

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
cd /home/g791218cobras/group-project
cp .env.example .env
nano .env
```

把正式環境變數填進去，例如：

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

儲存 nano：

```text
Ctrl + O
Enter
Ctrl + X
```

注意：

- `.env` 不要 commit 到 GitHub。
- 正式 API key 不要貼到 README、issue、PR 或聊天紀錄。
- 如果 key 曾外洩，請到對應平台重新產生。

## 7. 第一次手動部署 Docker

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
cd /home/g791218cobras/group-project
chmod +x ops/vm-deploy.sh ops/vm-cron-sync-new.sh
bash ops/vm-deploy.sh
```

這支腳本會做：

```text
1. 讀取目前 git commit
2. docker build image
3. 移除舊 container
4. 啟動新 container
5. 對外開 8080 port
```

確認 container：

```bash
docker ps --filter name=group-project-vm
```

確認目前 container 跑的是哪個 commit：

```bash
docker inspect group-project-vm --format '{{range .Config.Env}}{{println .}}{{end}}' | grep APP_REVISION
```

確認後端健康狀態：

```bash
curl -fsS http://127.0.0.1:8080/api/health
```

成功會看到類似：

```json
{"status":"ok","api_key_configured":false,"ml_model_loaded":true}
```

### 操作介面

```text
瀏覽器
```

打開：

```text
http://35.221.246.156:8080/
```

如果能看到網頁，代表 Docker 服務已經成功。

## 8. 設定 Nginx 反向代理

Docker 目前跑在 VM 的 `8080` port。Nginx 的工作是把正式網站的 `80/443` 導到 `127.0.0.1:8080`。

### 輸入位置

```text
VM SSH 終端機
```

### 安裝 Nginx

```bash
sudo apt-get update
sudo apt-get install -y nginx
sudo systemctl enable --now nginx
```

確認 Nginx：

```bash
sudo systemctl status nginx
```

### 建立站台設定

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
sudo nano /etc/nginx/sites-available/group-project
```

貼上：

```nginx
server {
    listen 80;
    server_name group-project.35-221-246-156.sslip.io;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

儲存 nano：

```text
Ctrl + O
Enter
Ctrl + X
```

啟用站台：

```bash
sudo ln -s /etc/nginx/sites-available/group-project /etc/nginx/sites-enabled/group-project
sudo nginx -t
sudo systemctl reload nginx
```

### 操作介面

```text
瀏覽器
```

打開：

```text
http://group-project.35-221-246-156.sslip.io/
```

如果可以看到網站，代表 Nginx HTTP 反向代理成功。

## 9. 設定 HTTPS

這一步會用 Certbot 幫 Nginx 申請 Let’s Encrypt SSL 憑證。

### 輸入位置

```text
VM SSH 終端機
```

### 安裝 Certbot

```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

### 申請 HTTPS 憑證

```bash
sudo certbot --nginx -d group-project.35-221-246-156.sslip.io
```

過程中如果問 email，就輸入你的 email。

如果問是否同意條款，選：

```text
Y
```

如果問是否 redirect HTTP to HTTPS，建議選：

```text
2
```

完成後測試：

```bash
sudo nginx -t
curl -fsS https://group-project.35-221-246-156.sslip.io/api/health
```

### 操作介面

```text
瀏覽器
```

打開正式 HTTPS 網址：

```text
https://group-project.35-221-246-156.sslip.io/
```

## 10. 之後換成正式網域

假設你買的網域是：

```text
example.com
```

### 10.1 設定 DNS

### 操作介面

```text
網域商後台，例如 Namecheap、GoDaddy、Cloudflare、Google Domains 類似介面
```

新增 DNS record：

```text
Type: A
Name: @
Value: 35.221.246.156
```

再新增：

```text
Type: A
Name: www
Value: 35.221.246.156
```

等待 DNS 生效，可能是數分鐘到數小時。

### 10.2 修改 Nginx server_name

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
sudo nano /etc/nginx/sites-available/group-project
```

把：

```nginx
server_name group-project.35-221-246-156.sslip.io;
```

改成：

```nginx
server_name example.com www.example.com;
```

檢查 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 10.3 重新申請正式網域 HTTPS

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
sudo certbot --nginx -d example.com -d www.example.com
sudo nginx -t
sudo systemctl reload nginx
```

### 操作介面

```text
瀏覽器
```

打開：

```text
https://example.com/
```

## 11. 設定 GitHub Actions 自動部署

### 11.1 確認 workflow 檔案

### 操作介面

```text
本機 PowerShell
```

### 指令

```powershell
cd D:\DATA\group-project
Get-Content .\.github\workflows\deploy-vm.yml
```

這個檔案會在 push 到 `main` 時部署。

### 11.2 建立 GitHub Actions SSH key

### 操作介面

```text
本機 PowerShell
```

### 指令

```powershell
cd D:\DATA\group-project
ssh-keygen -t ed25519 -C "github-actions-gcp-vm" -f .\github-actions-gcp-vm
```

會產生：

```text
github-actions-gcp-vm
github-actions-gcp-vm.pub
```

### 11.3 把 public key 加到 VM

### 操作介面

```text
本機 PowerShell
```

### 指令

```powershell
Get-Content .\github-actions-gcp-vm.pub
```

複製輸出的整行 public key。

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
```

把剛剛複製的 public key 貼到檔案最後一行。

儲存後執行：

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 11.4 測試 SSH key

### 操作介面

```text
本機 PowerShell
```

### 指令

```powershell
ssh -i .\github-actions-gcp-vm -p 22 g791218cobras@35.221.246.156 hostname
```

成功會看到類似：

```text
group-project-vm.asia-east1-c.c.group-project-503201.internal
```

### 11.5 設定 GitHub Secrets

### 操作介面

```text
GitHub 網頁
```

### 操作路徑

```text
GitHub repo jimm1218/group-project
-> Settings
-> Secrets and variables
-> Actions
-> New repository secret
```

新增以下 secrets：

| Secret 名稱 | 要填的值 |
|---|---|
| `GCP_VM_HOST` | `35.221.246.156` |
| `GCP_VM_USER` | `g791218cobras` |
| `GCP_VM_PORT` | `22` |
| `GCP_VM_APP_DIR` | `/home/g791218cobras/group-project` |
| `GCP_VM_SSH_KEY` | `github-actions-gcp-vm` private key 完整內容 |

取得 private key：

### 操作介面

```text
本機 PowerShell
```

### 指令

```powershell
Get-Content .\github-actions-gcp-vm -Raw
```

把完整內容貼到 GitHub Secret `GCP_VM_SSH_KEY`。

注意：

- private key 不要 commit。
- private key 不要貼到公開地方。
- repo 中的 `.gitignore` 應該要排除 private key。

### 11.6 測試 GitHub Actions

### 操作介面

```text
GitHub 網頁
```

### 操作路徑

```text
GitHub repo
-> Actions
-> Deploy to GCP VM
-> Run workflow
```

或在本機 push 一個 commit：

### 操作介面

```text
本機 PowerShell
```

### 指令

```powershell
cd D:\DATA\group-project
git status
git add .
git commit -m "Update dashboard"
git push origin main
```

### 檢查部署結果

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
cd /home/g791218cobras/group-project
git rev-parse --short HEAD
docker inspect group-project-vm --format '{{range .Config.Env}}{{println .}}{{end}}' | grep APP_REVISION
curl -fsS http://127.0.0.1:8080/api/health
```

`git rev-parse` 和 `APP_REVISION` 最後應該一致。

## 12. 設定每天早上 7 點自動同步新增資料

這個排程保留頁面上的手動同步按鈕，同時讓 VM 每天自動呼叫同步 API。

同步 API：

```text
POST /api/ml-dashboard/sync?dry_run=false&force=false
```

`force=false` 代表只同步新增資料。

API 會立即回傳背景任務 ID，不會等待整批分析完成。若要確認進度，可呼叫：

```text
GET /api/ml-dashboard/sync/status?job_id=<POST 回傳的任務 ID>
```

### 12.1 建立 log 資料夾並確認腳本權限

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
mkdir -p /home/g791218cobras/group-project/logs
chmod +x /home/g791218cobras/group-project/ops/vm-cron-sync-new.sh
```

### 12.2 編輯 crontab

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
crontab -e
```

貼上：

```cron
CRON_TZ=Asia/Taipei
0 7 * * * APP_URL=http://127.0.0.1:8080 /bin/bash /home/g791218cobras/group-project/ops/vm-cron-sync-new.sh >> /home/g791218cobras/group-project/logs/daily-sync.log 2>&1
```

儲存後確認：

```bash
crontab -l
```

應該看到：

```cron
CRON_TZ=Asia/Taipei
0 7 * * * APP_URL=http://127.0.0.1:8080 /bin/bash /home/g791218cobras/group-project/ops/vm-cron-sync-new.sh >> /home/g791218cobras/group-project/logs/daily-sync.log 2>&1
```

### 12.3 手動測試同步

### 輸入位置

```text
VM SSH 終端機
```

### 指令

```bash
APP_URL=http://127.0.0.1:8080 /bin/bash /home/g791218cobras/group-project/ops/vm-cron-sync-new.sh
```

### 12.4 查看同步是否成功

### 輸入位置

```text
VM SSH 終端機
```

看最近 50 行 log：

```bash
tail -n 50 /home/g791218cobras/group-project/logs/daily-sync.log
```

即時追蹤：

```bash
tail -f /home/g791218cobras/group-project/logs/daily-sync.log
```

看 cron 是否有觸發：

```bash
grep CRON /var/log/syslog | tail -n 30
```

## 13. 平常更新網站

### 操作介面

```text
本機 PowerShell
```

### 指令

```powershell
cd D:\DATA\group-project
git status
git add .
git commit -m "描述這次修改"
git push origin main
```

推上 GitHub 後，自動部署會開始跑。

### 操作介面

```text
GitHub 網頁
```

### 操作路徑

```text
GitHub repo
-> Actions
-> Deploy to GCP VM
```

點最新一次 workflow，看是否成功。

### 輸入位置

```text
VM SSH 終端機
```

確認線上 container：

```bash
cd /home/g791218cobras/group-project
git rev-parse --short HEAD
docker inspect group-project-vm --format '{{range .Config.Env}}{{println .}}{{end}}' | grep APP_REVISION
docker ps --filter name=group-project-vm
```

## 14. 常用檢查指令

### 看網站健康狀態

### 輸入位置

```text
VM SSH 終端機
```

```bash
curl -fsS http://127.0.0.1:8080/api/health
```

### 操作介面

```text
瀏覽器
```

```text
https://group-project.35-221-246-156.sslip.io/api/health
```

### 看 Docker container

### 輸入位置

```text
VM SSH 終端機
```

```bash
docker ps --filter name=group-project-vm
docker logs --tail 100 group-project-vm
```

### 看 Nginx

### 輸入位置

```text
VM SSH 終端機
```

```bash
sudo nginx -t
sudo systemctl status nginx
sudo cat /etc/nginx/sites-available/group-project
```

### 看 80 / 443 / 8080 port

### 輸入位置

```text
VM SSH 終端機
```

```bash
ss -ltnp | grep -E ':80 |:443 |:8080 '
```

### 看是否正在部署

### 輸入位置

```text
VM SSH 終端機
```

```bash
ps -eo pid,ppid,stat,cmd | grep -E 'docker build|vm-deploy|git fetch' | grep -v grep
```

## 15. 常見問題

### 問題：瀏覽器打不開網站

### 輸入位置

```text
VM SSH 終端機
```

先檢查 Docker：

```bash
docker ps --filter name=group-project-vm
curl -fsS http://127.0.0.1:8080/api/health
```

再檢查 Nginx：

```bash
sudo nginx -t
sudo systemctl status nginx
```

### 問題：GitHub push 後線上還是舊版

### 操作介面

```text
GitHub 網頁
```

先看：

```text
GitHub repo -> Actions -> Deploy to GCP VM
```

### 輸入位置

```text
VM SSH 終端機
```

再查：

```bash
cd /home/g791218cobras/group-project
git rev-parse --short HEAD
docker inspect group-project-vm --format '{{range .Config.Env}}{{println .}}{{end}}' | grep APP_REVISION
```

如果 git commit 已經新了，但 `APP_REVISION` 還是舊的，通常代表 Docker build 還在跑或部署失敗。

### 問題：HTTPS 憑證壞掉

### 輸入位置

```text
VM SSH 終端機
```

```bash
sudo certbot certificates
sudo nginx -t
sudo systemctl reload nginx
```

### 問題：cron 不確定有沒有跑

### 輸入位置

```text
VM SSH 終端機
```

```bash
crontab -l
tail -n 50 /home/g791218cobras/group-project/logs/daily-sync.log
grep CRON /var/log/syslog | tail -n 30
```

## 16. 重要提醒

- VM 的 `.env` 是正式密鑰，不要 commit。
- GitHub Actions SSH private key 只放 GitHub Secret，不要公開。
- Static IP 很重要，否則正式網域可能因 VM IP 改變而失效。
- 每次 push 到 `main` 都會觸發部署。
- 如果同時手動部署又 GitHub Actions 部署，可能會有兩個 Docker build 同時跑，建議等一個跑完再做下一個。
