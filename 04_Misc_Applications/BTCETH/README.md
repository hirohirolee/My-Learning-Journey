# 比特幣單機挖礦分析平台 (Bitcoin Solo Mining Analytics Platform)

這是一個先進的分析平台儀表板，旨在評估比特幣單機挖礦（彩票挖礦 / Solo Mining）的經濟合理性、統計概率學特徵及潛在投資風險。

本平台將即時的比特幣鏈上數據與概率論、折現現金流 (DCF) 估值模型、市場情境分析以及向量化的蒙特卡洛模擬相結合，來回答一個關鍵的財務問題：**在當前的網路難度與市場價格下，單機挖礦在經濟上是否合理？**

---

## 🏛️ 系統架構

平台嚴格遵循乾淨程式碼（SOLID, DRY, KISS）的軟體工程原則開發，將核心業務邏輯、網路層與 UI 展示層進行了嚴格的解耦：

```
bitcoin-solo-mining/
├── app.py                   # 應用程式入口及 Streamlit 前端調度中心
├── config.py                # 基於 Pydantic Settings 的配置管理器及內置 ASIC 數據庫
├── requirements.txt         # 核心第三方依賴庫
├── README.md                # 項目說明文檔
├── LICENSE                  # MIT 開源授權協議
├── .gitignore
├── .env.example             # 環境變數配置範本
│
├── core/
│   ├── bitcoin_api.py       # 鏈上指標抓取器，具備多重端點故障自動回退
│   ├── difficulty.py        # 算力轉換與難度年增長複利預測
│   ├── probability.py       # Poisson 與二項分布概率計算引擎
│   ├── finance.py           # 電費/維護成本 (OpEx)、挖礦收益及 DCF 資本預算模型 (NPV, IRR)
│   └── simulation.py        # 基於 NumPy 的高性能向量化蒙特卡洛模擬器
│
├── ui/
│   ├── sidebar.py           # 側邊欄參數與情境輸入面板
│   ├── dashboard.py         # 儀表板版面配置、月度財務明細報表展示與匯出
│   ├── charts.py            # 基於 Plotly 的互動式圖表模板
│   └── metrics.py           # Glassmorphism 毛玻璃卡片與綜合風險評估面板
│
├── utils/
│   ├── formatter.py         # 貨幣、算力、概率與等待時間的格式化工具
│   └── logger.py            # 基於 Loguru 的異步滾動日誌配置
│
└── tests/                   # 完整單元測試套件（整體覆蓋率 > 90%）
    ├── test_api.py
    ├── test_finance.py
    ├── test_probability.py
    └── test_simulation.py
```

---

## 🛠️ 平台特色

*   **即時區塊鏈同步：** 動態向 `mempool.space`、`Blockchain.com` 及 `CoinGecko` 發送請求以獲取即時比特幣价格、全網難度、區塊高度、補貼獎勵與交易手續費，並具備多重回退層。
*   **預載主流礦機庫：** 內置行業標準 ASIC 礦機參數（如 Antminer S21 Hyd, S21, S19 XP, WhatsMiner M60, Avalon A1566 等），並支持自定義數值覆蓋。
*   **精準概率學模型：** 基於 **Poisson (泊松) 分布** 與 **Binomial (二項) 分布**，計算 1 天到 1825 天（5 年）各時間跨度下成功出塊的精確概率（支援科學計數法與高精度顯示）。
*   **出塊等待時間估算：** 計算預期（平均）等待出塊時間與中位數等待時間，並求解指數分布下 95% 置信區間的上下限。
*   **折現現金流 (DCF) 估值：** 計算淨現值 (NPV)、內部收益率 (IRR)、盈虧平衡難度與盈虧平衡幣價（關機幣價），以及項目動態回本週期。
*   **向量化蒙特卡洛模擬：** 支持在給定的模擬次數下，快速模擬上萬條隨機出塊路徑，計算在難度與幣價按年增長時，項目的累計現金流置信百分位區間及最終獲利概率。
*   **市場情境分析：** 對比分析牛市（幣價 +50%，難度增長 +25%）、震蕩市（基準價格，難度增長 +10%）與熊市（幣價 -45%，難度增長 0%）情境下的收益與 ROI。
*   **多格式數據下載：** 支持將每月的財務預測明細一鍵匯出為 CSV、Excel、或 JSON 格式。

---

## 📐 數學公式說明

### 1. 單機挖礦出塊成功概率
已知礦機算力 $H$ (hashes/sec) 及當前全網難度 $D$，在任意 1 秒內挖到區塊的概率 $p$ 為：
$$p = \frac{H}{D \times 2^{32}}$$

對於一個長度為 $T$ 秒的時間區段，預期出塊數（Poisson $\lambda$ 參數）為：
$$\lambda = p \times T = \frac{H \times T}{D \times 2^{32}}$$

依據 **Poisson 分布**，挖出剛好 $k$ 個區塊的概率為：
$$P(X = k) = \frac{\lambda^k e^{-\lambda}}{k!}$$

挖到至少一個區塊（單機挖礦成功概率）為：
$$P(X \ge 1) = 1 - e^{-\lambda}$$

### 2. 等待出塊時間指標 (指數分布)
*   **預期 (平均) 等待時間:**
    $$E[t] = \frac{1}{p} = \frac{D \times 2^{32}}{H} \text{ 秒}$$
*   **中位數等待時間:**
    $$t_{median} = E[t] \times \ln(2) \text{ 秒}$$
*   **95% 概率的出塊等待時間區間:**
    $$\text{CI}_{95\%} = \left[ -\ln(0.975) \times E[t], \ -\ln(0.025) \times E[t] \right]$$

---

## 🚀 本地安裝與運行

### 先決條件
*   Python 3.12+
*   Pip 套件管理器

### 安裝步驟
1.  **進入項目根目錄**：
    ```bash
    cd bitcoin-solo-mining
    ```
2.  **建立並啟用 Python 虛擬環境**：
    ```bash
    python -m venv .venv
    # Windows 系統:
    .venv\Scripts\activate
    # macOS/Linux 系統:
    source .venv/bin/activate
    ```
3.  **安裝依賴庫**：
    ```bash
    pip install -r requirements.txt
    ```
4.  **建立本地環境變數配置**：
    ```bash
    cp .env.example .env
    ```
5.  **啟動 Streamlit 伺服器**：
    ```bash
    streamlit run app.py
    ```

---

## 🧪 自動化測試

本平台的測試套件全面驗證了出塊概率分布、DCF 內部收益率求解、快取過期控制與 HTTP 請求模擬。

執行測試套件並檢視覆蓋率報告：
```bash
python -m pytest --cov=core --cov=utils --cov-report=term-missing
```

---

## 🐳 部署指南

### Docker 容器化部署
1.  **建構 Docker 映像檔**：
    ```bash
    docker build -t bitcoin-solo-mining .
    ```
2.  **運行 Docker 容器**：
    ```bash
    docker run -p 8501:8501 bitcoin-solo-mining
    ```

### 生產環境 SaaS 部署
*   **Streamlit Community Cloud:** 關聯您的 GitHub 倉庫並指向 `app.py` 即可。
*   **Render / Railway / GCP Cloud Run:** 可使用內置 Docker 設定檔進行一鍵容器化部署。

---

## 📝 開源授權協議

本项目採用 MIT 授權協議開源 - 詳情請參閱 [LICENSE](LICENSE) 檔案。
