# 🧠 NCHU AI Training: 機器學習教材開發日誌 (2026-06-08)

本篇日誌記錄了今天針對**中興大學 AI 培訓班專屬教材——「十大機器學習演算法互動式報告」**所進行的全面升級與功能擴充。我們成功實現了多個核心數學沙盒、AI 智慧雙引擎導師、視訊表情感知功能，並打通了學校與家中的 Git 協同開發流。

---

## 🚀 今日核心成果

### 1. 互動式演算法沙盒擴充 (Next.js React & Streamlit)
先前專案部分演算法僅為靜態文字，今日我們成功實作並補齊了以下 4 大演算法的**動態畫布沙盒**：
*   **決策樹 (Decision Tree)**：動態計算 **Gini 不純度** 尋找最佳切分點，並即時渲染二分切割邊界。
*   **隨機森林 (Random Forest)**：透過 Bootstrap 自助抽樣生成多棵獨立決策木，利用**多數決投票機制**凝聚出平滑的非線性決策邊界。
*   **支援向量機 (SVM)**：基於梯度下降法極大化 **Margin 邊界**，支援線性與 RBF 空間映射，並自動標註「支援向量（最前線樣本點）」。
*   **單純貝氏 (Naive Bayes)**：基於高斯機率密度函數，在畫布上渲染連續的**後驗機率漸層雲圖（機率分佈）**。

### 2. 懸浮 AI 機器學習導師 (AI Chatbot)
為了提供學生即時問答，我們在網頁右上角新增了懸浮 **AI 學習導師**：
*   **本地離線引擎**：在沒有 API 金鑰時，透過快速規則比對，即時解答 10 大演算法、過擬合、Gini 係數、邊際等核心數學知識（$0.01$ 秒極速回應，離線可用）。
*   **Gemini 官方連線**：配備 ⚙️ 設定選單，使用者貼上自己的**免費 Gemini API Key** 後，會自動啟用 Google `gemini-1.5-flash` 模型，提供專業、親切且生活化比喻的 AI 對話。

### 3. Streamlit 滿版視區最佳化 (Viewport Fix)
*   **問題**：Streamlit 預設會用 iframe 嵌入 HTML 網頁，導致懸浮按鈕掉落至網頁最下方（1450px 處），無法隨視窗滾動。
*   **解決方案**：在 `app.py` 中寫入 `position: fixed; width: 100vw; height: 100vh;` CSS 重寫樣式，使 iframe 完美覆蓋整個瀏覽器視區，讓懸浮按鈕可以順暢地在視窗右上角（Chatbot）與左下角（Emotion Assistant）漂浮。

---

## 🛠️ 開發歷程與技術細節

我們今天遵循了「本地 React 組件化開發 ➡️ 打包為單頁 HTML ➡️ 部署 Streamlit ➡️ Bug 偵錯與效能優化 ➡️ 跨電腦同步備份」的完整工程流程，具體歷程如下：

### 階段一：React 元件化與數學模型開發 (`nextjs-project`)
1. **沙盒邏輯編寫**：在本地環境下建立 `DecisionTreePlayground.tsx`、`RandomForestPlayground.tsx`、`SVMPlayground.tsx` 與 `NaiveBayesPlayground.tsx` 元件。利用 HTML5 Canvas 搭配 JavaScript 精確計算 Gini 不純度、SVM 邊界超平面、隨機森林的多數決投票，以及單純貝氏的高斯概率雲圖。
2. **解決 Build 檔案鎖定衝突 (EPERM Error)**：
   * 在進行 Next.js 靜態生產環境編譯 (`npm run build`) 時，遇到了 `.next/trace` 檔案被正在運作的 `next dev` 伺服器鎖定而導致編譯失敗的權限錯誤（EPERM: operation not permitted）。
   * **解決方法**：手動終止正在背景執行的 Next.js Dev 伺服器，釋放檔案鎖，然後順利執行 `npm run build` 通過 TypeScript 編譯與語法檢查，最後再重新啟動 Dev 服務。

### 階段二：單頁 HTML 打包與靜態移植 (`app.html`)
1. **CDN 資源整合**：將 React 專案中的邏輯與外觀結構整合成單一的 `app.html`。在 HTML 檔頭引入了 Tailwind CSS (用於精美 UI)、Lucide (用於簡潔的圖標)、canvas-confetti (用於測驗答對時的特效) 與 face-api.js (用於臉部表情偵測) 等 CDN 庫。
2. **移植核心算法**：將 React 中的數值計算與 canvas 繪圖邏輯轉為 Vanilla JavaScript（原生 JS），確保在 Streamlit 所渲染的環境中能夠在不需要伺服器後端的情況下完全流暢執行。

### 階段三：實作 AI Chatbot 與本地問答偵錯
1. **雙引擎切換邏輯**：撰寫 `submitChatMessage()`，如果偵測到瀏覽器有保存 `gemini_api_key`，則向 Google 的 Gemini 伺服器發送 POST 請求；若無 Key，則呼叫 `getLocalResponse()`。
2. **保護金鑰隱私**：為避免將個人的 API 金鑰寫死在程式碼中並上傳至 GitHub 導致洩漏，我們設計了設定面板，金鑰完全儲存在瀏覽器的 `localStorage` 中，確保開源代碼的安全性。
3. **修復「持續思考中...」的卡死錯誤 (ReferenceError)**：
   * **問題現象**：測試時發現點擊問答按鈕發送問題後，聊天視窗一直顯示「思考中...」且無任何回覆。
   * **除錯過程**：經檢查發現程式碼中調用了 `getLocalResponse()`，但 `app.html` 的 JavaScript 區塊中根本忘記寫入此函數的定義。因為 JS 拋出未定義錯誤中斷了執行，導致 `typingIndicator.remove()` 沒有被執行到，所以一直卡死在思考狀態。
   * **解決方法**：補齊並定義完整的 `getLocalResponse` 函數，比對 `決策樹`、`SVM`、`過擬合` 等關鍵字，將對應的精華解析字串回傳，成功修復卡死問題。

### 階段四：Streamlit 版面融合與版面定位調整
1. **Iframe 覆蓋重構**：為了讓 floating 元件能相對於瀏覽器視區懸浮，我們在 `app.py` 中注入了重寫樣式。將 `.block-container` 的內邊距歸零，並將載入 `app.html` 的 `iframe` 設定為 `position: fixed !important; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 999999;`，讓網頁完美呈現全螢幕 App 的外觀。
2. **AI 助理位置調整**：考慮到網頁的視覺流向，我們將 AI Chatbot 懸浮按鈕與彈出視窗從原先的右下角調整至**右上角（按鈕置於 `top-6 right-6`，視窗置於 `top-24 right-6`）**，確保它與左下角的表情感知 AI 助教保持平衡、不互相遮擋。

### 階段五：建立跨電腦協同開發備份 (`nextjs-project`)
* 為了解決回到家裡電腦無法修改 React 原始碼的問題，我們在 GitHub 倉庫的 `daily_lessons/20260608` 目錄下上傳了整個 `nextjs-project` 專案。
* 在上傳時，我們配置了 `.gitignore`，自動過濾掉無須上傳的 `node_modules` 與 `.next` 目錄，使專案檔案大小保持在極輕量級狀態，方便秒級下載。

---

## 💻 跨電腦協同開發指南 (回到家裡電腦後)

### A. 若您只想修改 Streamlit 網頁成品 (`app.html` / `app.py`)
不需要安裝 Node.js 環境，直接在專案資料夾執行：
```bash
# 取得最新代碼
git pull

# 本機運行 Streamlit
streamlit run app.py
```
使用任何文字編輯器直接編輯 `app.html`，存檔後重新整理瀏覽器即可。

### B. 若您想修改 React 原始碼 (`nextjs-project`)
1. 進入 Nextjs 目錄：`cd daily_lessons/20260608/nextjs-project`
2. 安裝套件：`npm install`
3. 啟動本機開發伺服器：`npm run dev`
4. 打開瀏覽器訪問：`http://localhost:3000`

---
*NCHU AI Training 教材專題小組 2026-06-08*
