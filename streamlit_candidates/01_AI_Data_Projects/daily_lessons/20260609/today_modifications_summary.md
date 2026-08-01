# 50 Startups 利潤預測專案——今日變更與優化彙整報告 (2026-06-11)

本文件彙整了今日 (2026-06-11) 針對 `huanclass` 專案所進行的所有代碼修改、Bug 修復、數據分析報告擴充與視覺化升級內容。

---

## 🛠️ 1. Streamlit 互動平台修復與優化 (`app.py`)

### 🐛 解決 `simplified_mode` 未定義 Bug (NameError)
- **問題**：原先的代碼在執行到圖表繪製邏輯時，嘗試讀取 `simplified_mode` 變數以決定是否隱藏行政支出與地區，但該變數未曾定義，導致應用程式載入時崩潰。
- **修復**：在側邊欄（Sidebar）的「資料庫設定」下方新增模式切換 Checkbox，使用戶能動態開啟/關閉簡化分析模式。
  ```python
  st.sidebar.header("⚙️ 模式設定")
  simplified_mode = st.sidebar.checkbox("簡化分析模式 (僅顯示核心特徵 R&D 與 Marketing)", value=False)
  ```
- **動態更新邏輯**：
  - **熱力圖 (Heatmap)**：當開啟簡化模式時，僅計算 R&D Spend、Marketing Spend 與 Profit 的相關係數。
  - **預估 vs 真實利潤散佈圖**：隱藏行政支出的懸停提示。
  - **特徵矩陣 (Pairplot)**：切換維度至核心三維欄位。

### ⚠️ 移除 Streamlit 官方棄用警告
- 修正 `use_container_width` 的棄用警告，優化 Plotly 渲染的寬度參數。

---

## 📈 2. 統計檢定與深度觀察擴充 (`analysis_summary_zh.md`)

在專案成果報告中，新增了 **「第 6 節：專案深度觀察與統計檢定」**，為商業決策提供更嚴謹的數據科學支持：
1. **共線性檢驗 (VIF 分析)**：
   - 計算得 `R&D Spend VIF = 2.40`，`Marketing Spend VIF = 2.32`。
   - 證實兩大核心特徵在統計上無顯著多元共線性，可同時放入多元線性迴歸模型中，權重具高信賴度。
2. **地區特徵 (State) 消融對比**：
   - 包含 State 與完全剔除 State 的 OLS 模型對比實驗顯示，$R^2$ 僅相差 **0.05%**。
   - 統計上驗證了地區並非獲利的決定因子，符合奧卡姆剃刀原則（可精簡模型）。
3. **極端值扭曲性實驗 (Index 49)**：
   - 包含該異常點時，`State_Florida` 係數為 **+$198.79**（代表正向利潤）；剔除後係數反轉為 **-$1,564.22**。
   - 印證了 OLS 線性迴歸對異常點的極高敏感性，並突顯了 IQR 清洗的重要性。

---

## 📊 3. 靜態數據分析腳本升級 (`run_analysis.py` & `generate_executive_plots.py`)

為了與 Streamlit 平台的分析一致，我們在靜態分析與繪圖腳本中同步新增了以下兩款關鍵圖表的自動生成邏輯，並儲存至 `images/` 目錄：
1. **研發投入 vs 利潤線性趨勢圖 (`rd_vs_profit_regplot.png`)**：
   - 使用 Seaborn 的 `regplot` 繪製帶有 95% 信賴區間的線性迴歸擬合線，直觀呈現研發投入的壓倒性回報。
2. **全景地區分類矩陣圖 (`pairplot.png`)**：
   - 使用 Seaborn 的 `pairplot` 並以 `hue='State'` 進行地理分類著色，全局展示各支出特徵與利潤的兩兩分布關係。

---

## ☁️ 4. 雲端與本地部署指南 (`DEPLOYMENT.md`)

- 新增專屬的部署說明文件：
  - **本地端 (Local Run)**：提供環境依賴安裝 `pip install -r requirements.txt` 與 Streamlit 啟動指令。
  - **Streamlit Community Cloud**：指引如何串接 GitHub 儲存庫，正確指定嵌套目錄路徑 `daily_lessons/20260609/huanclass/app.py` 進行一鍵雲端部署。

---

### 📂 今日修改檔案清單
* 📝 **修改**：[app.py](file:///d:/My-Learning-Journey/daily_lessons/20260609/huanclass/app.py) *(新增模式設定並修復 NameError)*
* 📝 **修改**：[analysis_summary_zh.md](file:///d:/My-Learning-Journey/daily_lessons/20260609/huanclass/analysis_summary_zh.md) *(新增統計檢定與深度分析)*
* 📝 **修改**：[run_analysis.py](file:///d:/My-Learning-Journey/daily_lessons/20260609/huanclass/run_analysis.py) *(新增趨勢與矩陣圖表繪製邏輯)*
* 📝 **修改**：[generate_executive_plots.py](file:///d:/My-Learning-Journey/daily_lessons/20260609/huanclass/generate_executive_plots.py) *(同步新增高解析度圖片生成)*
* 🆕 **新增**：[DEPLOYMENT.md](file:///d:/My-Learning-Journey/daily_lessons/20260609/huanclass/DEPLOYMENT.md) *(本地/雲端部署指南)*
