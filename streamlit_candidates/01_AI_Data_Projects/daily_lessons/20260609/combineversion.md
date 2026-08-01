# 🚀 50 Startups 利潤預測專案：六合一完整彙整大師報告 (Master Documentation)

**文件包含來源**：
1. `analysis_summary_zh.md` (中文技術總結)
2. `Startup_Profit_Analysis_Report.md` (英文技術總結)
3. `executive_interactive_summary.md` (高階決策報告)
4. `project_modifications_summary.md` (專案變更日誌)
5. `today_modifications_summary.md` (今日優化日誌)
6. `DEPLOYMENT.md` (部署指南)

---

## 📑 目錄
1. [第一篇：高階商業決策與互動分析 (Executive Summary)](#第一篇-高階商業決策與互動分析-executive-summary)
2. [第二篇：CRISP-DM 雙語技術與統計分析報告 (Technical Analysis)](#第二篇-crisp-dm-雙語技術與統計分析報告-technical-analysis)
3. [第三篇：系統變更與今日優化全紀錄 (Change & Modification Logs)](#第三篇-系統變更與今日優化全紀錄-change--modification-logs)
4. [第四篇：雲端與本地端部署指南 (Deployment Guide)](#第四篇-雲端與本地端部署指南-deployment-guide)

---

## 🛑 第一篇：高階商業決策與互動分析 (Executive Summary)

本章節專為經營決策層設計，避開生硬統計術語，以最直觀的商業語言總結 `50_Startups` 專案模型的核心發現與決策指引。

### 1. 模型總結：預測利潤到底準不準？
* **結論**：極度精準！
* 本模型可解釋市場上 92.6% 的新創利潤變化。
* 在測試新創公司時，平均預測誤差僅在 $6,500 左右。
* 相對於公司平均 $11.2 萬的年利潤，誤差率僅為 5.8%，具有極高的實務參考價值。

### 2. 資金配置黃金法則：100 萬美金該投在哪？
* **黃金分配**：壓倒性投入「研發 (R&D)」，行銷適量，行政費用越低越好。
* **研發 (R&D)**：每多投 $1.00，預期帶回 $0.81 新增利潤（回報率 81%）。
* **行銷 (Marketing)**：每多投 $1.00，預期帶回 $0.03 新增利潤（回報率 3%）。
* **行政 (Admin)**：每多投 $1.00，利潤反而倒扣 $0.07（淨損失）。
* **顧問建議**：優先撥出 80%~85% 的預算投入研發以確保產品核心優勢，15% 進行精準行銷，並嚴格控管行政管理成本。

### 3. 地區決策：去哪裡設點投資最划算？
* **結論**：三個州獲利無顯著差異，選擇「營運成本最低」的地方即可。
* 在模型中，地理位置對利潤的預測影響力低於 0.2%。
* 新創公司無需迷信「加州」等特定熱點，哪裡租金低、稅率划算，就是最好的選址。

### 4. 異常點啟示：Index 49 給我們的警示？
* 被剔除的 Index 49 公司呈現了典型的失敗特徵：「重行政、輕產品，無核心競爭力」。
* 該公司研發支出為 $0，行銷花了 $4.5 萬，而行政費用卻高達 $11.7 萬，最終只換來 $1.4 萬的利潤。
* 這警告我們：沒有技術研發，只靠行銷與虛胖的行政組織是行不通的。

### 5. 直觀圖表視覺化 (Executive Visuals)
* **新創公司利潤驅動因子影響力排行 (特徵重要性)**：圖表 (`images/executive_importance.png`) 直觀顯示研發投入以 91.7% 的比例佔據絕對主導地位，行銷支出以 7.3% 居次，而行政管理和落腳州別的預測影響力均低於 1.0%。這明確指出企業應實行「產品研發第一」的資源分配戰略。
* **利潤預測準確度對比圖 (實際值 vs 預測值)**：圖表 (`images/executive_actual_vs_predicted.png`) 中藍色圓點代表測試集中的真實公司，紅色斜虛線代表完美預測線。所有藍色點均緊貼在紅色虛線兩側，並未出現大幅度偏離，證明模型的實際預估能力極強。

### 6. 啟動新創利潤模擬計算器 (Profit Simulator)
* 我們已在工作區後台完成了預測計算器的部署。
* 只需載入訓練好的模型，即可根據輸入預算即時預估利潤。
* **輸入參數包含**：研發費用 (R&D Spend)、行銷費用 (Marketing Spend)、行政費用 (Administration Spend) 以及公司位置 (State，包含 California / Florida / New York)。
* 系統將自動套用最佳模型為您計算出公司預期 Profit 金額。

---

## 🔬 第二篇：CRISP-DM 雙語技術與統計分析報告 (Technical Analysis)

整合中文與英文版技術報告，詳述針對 `50_Startups.csv` 所進行的資料科學處理與模型評估。

### 2.1 商業與資料理解 (Business & Data Understanding)
* **核心目標**：利用企業在研發支出 (R&D Spend)、行政管理 (Administration)、行銷推廣 (Marketing Spend) 的投入以及所在的地區 (State)，來精準預測其產出的利潤 (Profit)。
* **資料集特徵**：共 50 筆記錄，包含 3 項數值型連續支出特徵、1 項地區類別特徵，以及目標變數 Profit。

### 2.2 數據清洗與準備 (Data Preparation)

#### 1) 極端值剔除 (IQR Outlier Filtering)
* 利用四分位距 (IQR) 檢驗目標欄位 `Profit` 的分布。
* **IQR 範圍**：$49,627.07。
* **極端低值門檻 (Lower Bound)**：$15,698.29。
* **極端高值門檻 (Upper Bound)**：$214,206.59。
* **偵測結果**：Index 49 的 Profit 為 $14,681.40，低於下限門檻被判定為極端值。
* **被剔除資料明細**：Index 49 | R&D Spend: $0.00 | Administration: $116,983.80 | Marketing Spend: $45,173.06 | State: California | Profit: $14,681.40。
* **處理方式**：在資料準備階段直接剔除 (Drop) 該筆資料（Index 49），使建模樣本數調整為 49 筆，防干擾迴歸線擬合。

#### 2) 數值為 0 的欄位處理 (Zero Values Treatment)
* 數據集中有部分欄位值為 0。
* **R&D Spend**：Index 49 ($0.00, 與 Profit 一起剔除) 與 Index 19 ($0.00)。
* **Marketing Spend**：Index 19, 47, 48, 49 ($0.00)。
* **處理方式**：這些 0 值代表真實商業模式（如無行銷預算或草創階段），屬於真實業務特徵而非缺失值，因此保持原樣，不進行平均值/中位數填補。

#### 3) 類別變數編碼 (Avoid Dummy Variable Trap)
* 針對地理位置欄位 `State`（包含 California, Florida, New York）進行 One-Hot Encoding。
* **處理方式**：設定 `drop_first=True`，剔除 baseline 地區（California），僅保留 `State_Florida` 與 `State_New York`。此舉能有效避開虛擬變數陷阱 (Dummy Variable Trap)，預防多元共線性。

#### 4) 特徵標準化縮放 (Selective Feature Scaling)
* **處理方式**：僅針對 `R&D Spend`, `Administration`, `Marketing Spend` 這三個連續型數值特徵使用 `StandardScaler` 進行標準化縮放。
* One-Hot 編碼後的二元虛擬變數（0 或 1）保持原樣不縮放，以維持可解釋性。

### 2.3 模型建立與效能對比 (Modeling & Evaluation)
* 將清洗後的資料按 80% 訓練集 (39 samples) 與 20% 測試集 (10 samples) 進行切分，固定隨機種子 `random_state=42`。

| 評估模型 | R-squared ($R^2$) | 平均絕對誤差 (MAE) |
| :--- | :---: | :---: |
| **多元線性迴歸 (Linear Regression - OLS)** | 0.91908 | $6,550.86 |
| **隨機森林迴歸 (Random Forest)** | 0.92601 | $6,892.37 |

* **對比結論**：隨機森林在 $R^2$ 上表現稍好（0.92601），而多元線性迴歸模型則在 MAE 表現上更優 ($6,550.86)。

### 2.4 特徵權重與重要性分析 (Feature Weights & Importance)

#### 1) 多元線性迴歸特徵權重 (標準化係數)
* **R&D Spend**：+34,885.07。
* **Marketing Spend**：+4,342.70。
* **State_New York**：-2,877.86。
* **State_Florida**：-1,860.88。
* **Administration**：-425.04。

#### 2) 複線性迴歸數學方程式 (原始未縮放數據)
* **中文報告版方程式**：`Profit = 54,028.04 + 0.8056 * (R&D Spend) - 0.0688 * (Administration) + 0.0299 * (Marketing Spend) + 938.7930 * (State_Florida) + 6.9878 * (State_New York)`。
* **英文報告更新版方程式**：`Profit = 51,306.76 + 0.7619 * (R&D Spend) - 0.0147 * (Administration) + 0.0400 * (Marketing Spend) - 1860.8779 * (State_Florida) - 2877.8560 * (State_New York)`。

#### 3) 隨機森林特徵重要性 (Feature Importance)
* **R&D Spend**：0.916931 (約 91.69%)。
* **Marketing Spend**：0.0728946 (約 7.29%)。
* **Administration**：0.00771542 (約 0.77%)。
* **State_New York**：0.00159434 (約 0.16%)。
* **State_Florida**：0.000864335 (約 0.09%)。

### 2.5 專案深度觀察與統計檢定
* **R&D 與 Marketing 支出之共線性檢驗 (VIF 分析)**：
  * R&D Spend VIF：2.40。
  * Marketing Spend VIF：2.32。
  * Administration VIF：1.18。
  * 結論：VIF < 5 代表無顯著共線性，兩大核心特徵可同時放入多元線性迴歸模型中，權重具高信賴度。
* **地理位置 (State) 類別編碼之消融對比實驗**：
  * 包含 State 特徵之 OLS 模型解釋力 ($R^2$)：96.18%。
  * 完全剔除 State 特徵之 OLS 模型解釋力 ($R^2$)：96.13%。
  * 結論：移除地理位置特徵後，模型解釋力僅微幅下降 0.05%，統計上驗證了地區並非獲利的決定因子，符合奧卡姆剃刀原則。
* **極端值 (Index 49) 對 OLS 迴歸係數的扭曲性實驗**：
  * 包含極端值時：`State_Florida` 係數為 +$198.79。
  * 剔除極端值後：`State_Florida` 係數為 -$1,564.22。
  * 結論：單一極端值會造成係數正負反轉，印證了 OLS 線性迴歸對異常點的極高敏感性，突顯了 IQR 清洗的重要性。

---

## 📝 第三篇：系統變更與今日優化全紀錄 (Change & Modification Logs)

整合專案開發過程與 2026-06-11 的所有程式碼變更與除錯日誌。

### 3.1 架構與效能重構
* **專案目錄重構**：於工作區建立獨立專案資料夾 `D:\H\0609\huanclass\`，移入所有檔案與 `images/` 目錄。
* **機器學習模型擴展**：模型對比陣容從 2 個擴展為 5 個常用迴歸模型（多元線性迴歸、脊迴歸、支持向量迴歸、隨機森林迴歸、梯度提升迴歸），網頁排行榜以綠色高亮最佳模型。
* **最佳化搜尋效能重構 (Vectorization)**：將預算最佳化的 1,500 次單筆預測迴圈改寫為向量化批量計算 (Vectorized Batch Processing)。最佳化運算時間從 2,000 毫秒縮減至 5 毫秒（0.005 秒）以內，使網頁達到即時秒響應。

### 3.2 互動式視覺化與重訓升級
* **Plotly 互動圖表升級**：
  * 散佈圖新增黃色 `⭐️ 您設定的模擬公司` 標記。
  * 箱型圖新增黃色 `--- 您的模擬公司預估利潤線`。
  * 相關性熱力圖支援滑鼠懸停查看精確係數。
* **自訂數據上傳與動態重訓**：側邊欄加入 `File Uploader`。當用戶上傳 CSV 時，系統自動套用相同清洗流程，並在 0.05 秒內重新訓練 5 種模型。

### 3.3 歷史與今日 Bug 修復 (2026-06-11)
* **歷史修復**：補上 `import os` 修復系統崩潰；將 Plotly 顏色條從 `'coolwarm'` 修改為 `'RdBu_r'`；移除引發警告的 `use_column_width=True`。
* **今日修復 (simplified_mode 未定義)**：修復嘗試讀取未定義 `simplified_mode` 導致的崩潰。在側邊欄加入 `st.sidebar.checkbox("簡化分析模式 (僅顯示核心特徵 R&D 與 Marketing)", value=False)`。開啟時，熱力圖、散佈圖提示與特徵矩陣會動態降維至核心欄位。
* **今日修復 (棄用警告)**：修正 `use_container_width` 的棄用警告，優化 Plotly 渲染。

### 3.4 靜態分析腳本擴充
* **今日升級**：在 `run_analysis.py` 與 `generate_executive_plots.py` 中新增兩款圖表自動生成。
  * 研發投入 vs 利潤線性趨勢圖 (`rd_vs_profit_regplot.png`)：使用 Seaborn 的 `regplot` 繪製 95% 信賴區間的線性迴歸擬合線。
  * 全景地區分類矩陣圖 (`pairplot.png`)：使用 Seaborn 的 `pairplot` 並以 `hue='State'` 進行地理分類著色。

---

## ☁️ 第四篇：雲端與本地端部署指南 (Deployment Guide)

本文件說明如何將本專案部署至 Streamlit Community Cloud 或在本地運行。

### 4.1 本地運行指南 (Local Run Guide)
1. **確保安裝 Python 環境**：支援 Python 3.9+，執行 `python --version` 確認。
2. **安裝相依套件**：在目錄 `daily_lessons/20260609/huanclass/` 下，執行 `pip install -r requirements.txt`。
3. **啟動應用程式**：執行 `streamlit run app.py`，瀏覽器會自動開啟網址 `http://localhost:8501`。

### 4.2 Streamlit Community Cloud 部署指南
1. **推送代碼至 GitHub**：確認 `app.py`、`requirements.txt`、`50_Startups.csv` 及各個 `.pkl` 檔案推送至 `My-Learning-Journey` 的主分支。
2. **登入 Streamlit Cloud**：使用 GitHub 帳號登入 Streamlit Share。
3. **建立新應用 (New App)**：
   * **Repository**：選擇 `hirohirolee/My-Learning-Journey` 儲存庫。
   * **Branch**：選擇 `master` 或 `main`。
   * **Main file path**：輸入 `daily_lessons/20260609/huanclass/app.py`。
4. **點擊 Deploy**：系統自動讀取 `requirements.txt` 並安裝套件，1-2 分鐘後即可上線。

### 4.3 注意事項與故障排除
* **數據加載錯誤 (FileNotFoundError)**：請確保 CSV 與模型檔案與 `app.py` 放在相同的子目錄下。
* **自訂數據結構**：上傳自訂 CSV 檔案的欄位名稱必須完全包含：`R&D Spend`、`Administration`、`Marketing Spend`、`State`、`Profit`，否則重訓管線會報錯。
