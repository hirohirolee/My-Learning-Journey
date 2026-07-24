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

# 複製前端程式碼
COPY app/ ./app/

# 暴露 Streamlit 預設 Port 8501
EXPOSE 8501

# 啟動 Streamlit 服務
CMD ["streamlit", "run", "app/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
