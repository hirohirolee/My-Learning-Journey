# 50 Startups 利潤預測專案——變更與優化紀錄報告 (Change Log)

本報告彙整了本專案在開發與迭代過程中，所進行的所有架構優化、數據預處理、演算法升級、網格搜尋效能重構以及 Streamlit 互動功能的變更紀錄。

---

## 📁 1. 專案目錄重構 (Directory Reorganization)
為了使專案結構更加整潔且易於上傳至 GitHub，我們在工作區建立了獨立的專案資料夾：
* **新資料夾路徑**：`D:\H\0609\huanclass\`
* **移入檔案**：包含原始資料集 `50_Startups.csv`、所有 Python 腳本、訓練好的 `.pkl` 模型、影像目錄 `images/` 以及所有書面 Markdown 成果報告。

---

## 🧹 2. 數據理解與準備變更 (Data Cleansing & Prep)
根據資料特徵與迴歸建模要求，進行了以下特定的預處理調整：
* **極端值剔除 (Outlier Drop)**：利用 IQR (四分位距) 檢驗 `Profit` 欄位，精準定位並剔除了極端低值點 **Index 49** (加州，利潤 \$14,681.40)，防範迴歸線產生偏斜。
* **零值保留 (Zeros Preserved)**：確認 R&D Spend 與 Marketing Spend 的 0 值代表真實業務情況而非缺失值，保持原樣，不進行填補。
* **避免虛擬變數陷阱 (Dummy Variable Trap)**：在對 `State` 進行 One-Hot 編碼時設定 `drop_first=True`，剔除加州作為基準地區，防止共線性。
* **選擇性特徵縮放 (Selective Scaling)**：僅對連續型特徵（研發、行政、行銷支出）進行 `StandardScaler` 標準化縮放，二元虛擬變數保持原樣。

---

## 🤖 3. 機器學習模型擴展 (Model Expansion)
模型對比陣容從原先的 2 個模型擴展為 **5 個常用迴歸模型**，以提供更客觀的評估：
1. 多元線性迴歸 (Multiple Linear Regression)
2. 脊迴歸 (Ridge Regression - L2 正則化)
3. 支持向量迴歸 (Support Vector Regression - SVR)
4. 隨機森林迴歸 (Random Forest - 整合樹模型)
5. 梯度提升迴歸 (Gradient Boosting - 提升樹模型)
* 系統在背景以 80% 訓練集與 20% 測試集進行評估，計算 $R^2$、MAE 與 RMSE，並在網頁排行榜中以**綠色高亮最佳模型**。

---

## ⚡ 4. 最佳化搜尋效能重構 (Performance Optimization)
* **問題**：原先的「預算最佳化推薦」功能在 1,500 次迴圈中採取單筆循環預測，導致每次網頁數值變動時都會產生 2 秒以上的系統阻塞與介面卡頓。
* **重構方案**：將搜尋完全改寫為**向量化批量計算 (Vectorized Batch Processing)**。將 1,500 種分配組合一次性生成為單一 DataFrame 進行批量縮放與批量預測。
* **成果**：最佳化運算時間從 2,000 毫秒縮減至 **5 毫秒（0.005 秒）以內**，徹底消除了 Streamlit UI 的卡頓感，使網頁操作達到即時秒響應。

---

## 📊 5. 互動式視覺化升級 (Plotly Interactivity)
將原本 Matplotlib/Seaborn 的靜態圖表全面替換為 **Plotly 互動式圖表**，並新增了與左側滑桿配置的**實時聯動指標**：
* **散佈圖 (Scatter Plot)**：新增黃色 **`⭐️ 您設定的模擬公司`** 標記。當調整左側滑桿時，星星會在完美預測斜線上左右滑動，並顯示當前預算的懸停資料。
* **箱型圖 (Box Plot)**：新增黃色 **`--- 您的模擬公司預估利潤線`**。虛線會隨著預算變動在各州箱型圖中即時上下浮動，呈現公司利潤在行業分布中的水平。
* **特徵相關性熱力圖 (Correlation Heatmap)**：支援滑鼠懸停查看交叉項目的精確相關係數。

---

## 📁 6. 自訂數據上傳與動態重訓 (Dynamic Retraining)
* **新增功能**：在側邊欄加入 **`File Uploader`** 支援 CSV 資料上傳。
* **邏輯**：當用戶上傳符合結構的新創 CSV 檔案時，系統會自動在背景套用相同的 IQR 清洗、編碼、縮放流程，並在 **0.05 秒內重新訓練 5 種模型**。全站的預測數值、最佳化推薦以及 Plotly 圖表將即時更新為新資料的結果。

---

## 🐛 7. Bug 與警告修復 (Bug & Warning Fixes)
* **os 庫 NameError**：在 `app.py` 頂部補上 `import os` 以修復檔案存在性檢查時產生的系統崩潰。
* **Plotly 顏色條語法錯誤**：將相關性熱力圖的 colorscale 參數由不支援的 `'coolwarm'` 修改為 Plotly 官方標準的 **`'RdBu_r'`**。
* **棄用警告修復**：將 `app.py` 中引發黃色警告方塊的舊參數 `use_column_width=True` 移除，替換為符合標準的 Plotly 渲染設定。

---

## 📋 8. 部署準備 (Deployment)
* **`requirements.txt`**：已成功建立並將 `plotly` 新增至相依套件清單中，以利專案直接於 **Streamlit Community Cloud** 雲端進行一鍵免費部署。
