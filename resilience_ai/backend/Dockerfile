# [FEATURE] Docker 容器化
# 使用輕量級 Python 3.11 Slim 基礎映像檔
FROM python:3.11-slim

# 設定容器內工作目錄
WORKDIR /app

# 設定環境變數，避免 Python 產生 pyc 暫存檔與緩衝輸出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 複製依賴清單並安裝，以利 Docker 快取層優化
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製後端程式碼與預設資料庫目錄
COPY backend/ ./backend/
COPY audit_db/ ./audit_db/
COPY vector_db/ ./vector_db/

# 暴露 FastAPI 預設 Port 8000
EXPOSE 8000

# 啟動 FastAPI 服務
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
