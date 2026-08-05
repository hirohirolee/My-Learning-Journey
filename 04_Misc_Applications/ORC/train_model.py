from ultralytics import YOLO

def main():
    # 1. 載入輕量級的官方預訓練模型作為「地基」
    # 使用 small 版本即可，訓練快且準確度夠用
    model = YOLO('yolo11s.pt')

    # 2. 開始訓練 (Transfer Learning)
    print("🚀 開始訓練專屬模型...")
    results = model.train(
        data='my_roboflow_data/data.yaml',  # ⚠️ 指向你從 Roboflow 下載解壓縮後的 data.yaml
        epochs=50,       # 讓 AI 反覆學習這批資料 50 遍
        imgsz=640,       # 訓練時的影像尺寸
        batch=8,         # 每次處理 8 張圖片 (依電腦記憶體調整)
        device='cpu',    # 指定使用 CPU 訓練
        plots=True       # 訓練後產生圖表讓你檢視學習成效
    )
    print("✅ 訓練完成！")

if __name__ == '__main__':
    # 在 Windows 系統下，YOLO 訓練建議包在 if __name__ == '__main__': 區塊內
    main()