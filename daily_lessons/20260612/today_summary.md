# 📝 新創公司利潤預測與決策 AI 平台 - 今日修改紀錄 (2026-06-12)

今天我們針對 **新創公司利潤預測與決策最佳化 AI 平台**（位於 `daily_lessons/20260609/huanclass/app.py`）進行了多項核心優化、圖表重構、互動性強化、代碼防錯以及 GitHub 同步與雲端部署設定。

---

## 🛠️ 今日工作詳細彙總

### 1. ⚙️ 環境設定與依賴安裝
* **操作**：使用 `pip` 自動解析並安裝了 `requirements.txt` 中所列的所有機器學習與資料科學必要套件（包括 `streamlit`, `plotly`, `scikit-learn`, `seaborn` 等）。
* **驗證**：成功在本地啟動 Streamlit 伺服器並運行於 `http://localhost:8501`。

### 2. 🔄 圖表佈局重排 (Reordering Layout)
* **操作**：依據您的初次指示，將「互動式視覺化分析」分頁中的圖表進行了位置互換：
  * 將原本位於第 7、8 位置的特徵數量變化折線圖（RMSE & R-squared 變化圖）移至第 1、2 最上方核心位置。
  * 將原本位於第 1、2 位置的相關性熱力圖與研發投入散佈圖移至第 7、8 位置。
  * 修正了「利潤決定因子權重排行（圖表 ⑥）」說明中「解慢」為「解讀」的字型錯誤。

### 3. 📊 簡報投影級大圖表重構 (Projector-Style Chart)
* **操作**：應簡報設計需求，將頂部圖表重構為一個寬度佔 **80%（兩側留空居中）** 的大型主折線圖：
  * **主題**：**"Top 10 ML Algorithms: MSE vs. Feature Count"**，動態評估 10 種模型（包括 Linear, Ridge, Lasso, ElasticNet, Decision Tree, Random Forest, Gradient Boosting, AdaBoost, Extra Trees, SVR）。
  * **超大字級**：標題調整至 `26px`，坐標軸與標籤調整至 `20px` / `16px`，便於簡報投影展示。
  * **圖例配置**：將 10 種色彩標記的圖例框放置於圖表內部右上角。
  * **互動微調**：將所有模型的超參數調整（Lasso/Ridge Alpha、Random Forest/Extra Trees Estimators、SVR C值）移至左側邊欄面板。

### 4. 🎛️ 線條擠壓優化與互動強化 (Interactive Optimization)
* **問題**：因 SVR 的 MSE 數值遠大於其他 9 種算法，導致其他算法折線全部擠壓在底部，難以看清。
* **解決方案**：
  * **對數尺度 (Log Scale)**：在左側控制台引入了 **「Y 軸對數尺度 (Log Scale)」** 核取方框（**預設開啟**），使底部微小 MSE 線條動態展寬。
  * **演算法多選篩選器 (Multi-Select)**：在左側新增演算法篩選下拉選單，使用者可手動關閉/開啟特定模型（例如手動移除 SVR），讓圖表只對比感興趣的算法。
  * **線條粗細強化**：將折線寬度加粗至 `3.5`，提高視覺辨識度。
  * **一體化對比 (Unified Hover)**：配置 Plotly Hover Mode 為 `x unified`，滑鼠移動時會彈出單一提示框同時呈現 10 種模型的 MSE。

### 5. 📂 雲端路徑相容性修復 (Deployment Path Fix)
* **操作**：將 `app.py` 中原本相對路徑加載資料的 `pd.read_csv('50_Startups.csv')` 替換為以檔案目錄為基準的絕對路徑：
  ```python
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  csv_path = os.path.join(BASE_DIR, '50_Startups.csv')
  ```
* **效果**：100% 避免了在 Streamlit Cloud 部署時因 Working Directory 不同所導致的 `FileNotFoundError` 錯誤。

### 6. 🐙 GitHub 同步 (Git Sync)
* **操作**：
  1. 通過 `git stash` 備份未提交的非相關檔案變更。
  2. 進行 `git pull --rebase` 安全合併遠端修改。
  3. 成功執行 `git push` 將代碼提交至您的 GitHub 倉庫 `hirohirolee/My-Learning-Journey` 的 `master` 分支。
  4. 執行 `git stash pop` 還原暫存工作。

---

## 🔗 相關資源與操作路徑

* **本地執行檔**：[app.py](file:///d:/My-Learning-Journey/daily_lessons/20260609/huanclass/app.py)
* **本地資料集**：[50_Startups.csv](file:///d:/My-Learning-Journey/daily_lessons/20260609/huanclass/50_Startups.csv)
* **詳細的視覺變更及截圖**：[walkthrough.md](file:///C:/Users/admin/.gemini/antigravity-ide/brain/9b20897f-84ba-46e0-a5dd-16db9c0eb0f3/walkthrough.md)
* **Streamlit Community Cloud 部署設定資訊**：
  * **Repository**: `hirohirolee/My-Learning-Journey`
  * **Branch**: `master`
  * **Main file path**: `daily_lessons/20260609/huanclass/app.py`
