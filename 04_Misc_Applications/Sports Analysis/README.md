# 市場套利分析與資訊效率稽核系統

> **免責聲明**：本系統僅供學術研究與資訊效率稽核用途。數據來源：[The Odds API](https://the-odds-api.com/)。
> 嚴格遵守 API 服務條款，不包含自動下單或任何交易執行功能。

---

## 目錄結構

```
Sports Analysis/
├── config.py              # 集中設定管理（從 .env 讀取）
├── data_provider.py       # OddsApiClient（API 串接、速率限制、重試）
├── data_warehouse.py      # OddsDatabase（SQLite 儲存、完整性檢查）
├── analysis_engine.py     # ArbitrageAnalyzer（ROI 計算、異常標記、匯出）
├── main.py                # 主入口（asyncio 排程、CLI 模式）
│
├── tests/
│   ├── __init__.py
│   ├── test_data_warehouse.py     # 完整性檢查 + 寫入/查詢測試
│   ├── test_analysis_engine.py    # ROI 計算 + 異常值 + 穩定性測試
│   └── test_data_provider.py     # 速率限制 + 重試 + 正規化測試
│
├── data/                  # SQLite 資料庫（自動建立，不提交）
├── output/                # CSV 與 Markdown 報告輸出（不提交）
├── logs/                  # 系統日誌（不提交）
│
├── .env.example           # 環境變數範本（提交）
├── .env                   # 真實設定（不提交，加入 .gitignore）
├── .gitignore
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
# 複製範本並填入真實值
copy .env.example .env
# 編輯 .env，填入 ODDS_API_KEY
```

### 3. 執行系統

```bash
# 單輪抓取 + 分析 + 匯出
python main.py --mode single

# 持續輪詢（每 5 分鐘執行一次）
python main.py --mode poll --interval 300

# 指定運動項目
python main.py --mode single --sports basketball_nba soccer_epl

# 僅分析現有資料庫內容（不消耗 API 額度）
python main.py --mode analyze

# 查看 API 額度與資料庫狀態
python main.py --mode status
```

### 4. 執行測試

```bash
# 執行所有單元測試（不需要真實 API 金鑰）
pytest

# 排除整合測試
pytest -m "not integration"

# 顯示詳細輸出
pytest -v
```

---

## 速率限制策略

詳見 [POWERBI_DATAMODEL.md](./POWERBI_DATAMODEL.md) 的完整說明，以及 `config.py` 的參數設定。

**核心機制**：
- `RateLimitState` 持久化計數器追蹤本月已用次數（重啟不歸零）
- 動態每日預算：`剩餘額度 / 本月剩餘天數`
- 安全緩衝：超過 90% 用量時記錄警告
- 額度耗盡時阻止請求，拋出 `RuntimeError`

---

## Power BI 連接

1. **直接連接 SQLite**：在 Power BI Desktop 使用 ODBC 或 SQLite connector 連接 `data/odds_warehouse.db`
2. **CSV 匯入**：執行 `python main.py --mode analyze` 後，從 `output/` 目錄匯入 CSV

詳細 Star Schema 設計請參閱 [POWERBI_DATAMODEL.md](./POWERBI_DATAMODEL.md)。
