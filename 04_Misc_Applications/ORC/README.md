# 🐱🐶 YOLO 貓狗 AI 辨識與數量統計 Web 系統

基於 YOLOv11 與 SOTA 深度學習 Ensemble 技術的貓狗精確辨識與數量統計系統。

## 🌟 主要功能特點

1. **🤖 智慧通用自動辨識**：
   - 自動判斷單張特寫、多隻合照或 36/64 密集宮格照片。
   - 一般合照自動進行全圖二階段雙驗證標註。
   - 密集宮格拼圖自動開啟獨立宮格切分引擎。

2. **🧠 三神經網絡 Ensemble 交叉驗證**：
   - 結合 YOLOv11x + ResNet50 + EfficientNetV2-S 進行權重投票。
   - 防範後腿站立、異常姿態貓咪誤判為狗狗。

3. **🖍️ 自訂標註顯示**：
   - 支援勾選/取消勾選標註框（可選擇「不用標註」，純淨輸出原圖與統計結果）。

4. **⚡ 即時自動響應**：
   - 點擊範例圖或上傳新圖片時 0 秒延遲即時更新。

## 🚀 快速啟動

```bash
# 安裝依賴套件
pip install torch torchvision ultralytics gradio opencv-python

# 啟動 Gradio Web 系統
python web_gradio_app.py
```
