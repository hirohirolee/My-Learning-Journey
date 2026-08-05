import sys
import os
import cv2
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, QFrame)
from PyQt6.QtGui import QPixmap, QImage, QFont
from PyQt6.QtCore import Qt
from ultralytics import YOLO

class CatDogDetectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("貓狗 AI 辨識系統 (YOLOv11 Desktop Edition)")
        self.resize(1000, 700)
        self.model = YOLO("yolo11n.pt")
        self.current_image_path = None
        
        self.init_ui()

    def init_ui(self):
        # 主面板與佈局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左側控制區面板
        left_panel = QFrame()
        left_panel.setFixedWidth(280)
        left_panel.setStyleSheet("background-color: #2b2b2b; color: white; border-radius: 8px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 20, 15, 20)

        # 標題
        title_label = QLabel("🐱🐶 貓狗物件偵測系統")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        left_layout.addWidget(title_label)

        # 按鈕區
        self.btn_select = QPushButton("📁 選擇圖片照片")
        self.btn_select.setStyleSheet(self.get_button_style("#007acc"))
        self.btn_select.clicked.connect(self.select_image)
        left_layout.addWidget(self.btn_select)

        self.btn_detect = QPushButton("⚡ 開始 YOLO 辨識")
        self.btn_detect.setStyleSheet(self.get_button_style("#28a745"))
        self.btn_detect.setEnabled(False)
        self.btn_detect.clicked.connect(self.run_detection)
        left_layout.addWidget(self.btn_detect)

        # 統計資訊區
        left_layout.addSpacing(20)
        info_header = QLabel("📊 辨識結果統計")
        info_header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        left_layout.addWidget(info_header)

        self.lbl_cat_count = QLabel("貓 (Cats): 0 隻")
        self.lbl_cat_count.setFont(QFont("Arial", 10))
        left_layout.addWidget(self.lbl_cat_count)

        self.lbl_dog_count = QLabel("狗 (Dogs): 0 隻")
        self.lbl_dog_count.setFont(QFont("Arial", 10))
        left_layout.addWidget(self.lbl_dog_count)

        self.lbl_status = QLabel("狀態: 等待載入圖片...")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: #aaa; margin-top: 10px;")
        left_layout.addWidget(self.lbl_status)

        left_layout.addStretch()
        main_layout.addWidget(left_panel)

        # 右側圖片顯示區
        self.image_display = QLabel("請點擊左側「選擇圖片照片」載入影像")
        self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display.setStyleSheet("background-color: #1e1e1e; color: #777; font-size: 16px; border-radius: 8px;")
        main_layout.addWidget(self.image_display, stretch=1)

    def get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #555;
            }}
            QPushButton:disabled {{
                background-color: #444;
                color: #888;
            }}
        """

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇照片", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.current_image_path = file_path
            self.btn_detect.setEnabled(True)
            self.lbl_status.setText(f"已載入: {os.path.basename(file_path)}")
            
            # 顯示原圖
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(self.image_display.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_display.setPixmap(scaled_pixmap)

    def run_detection(self):
        if not self.current_image_path:
            return

        self.lbl_status.setText("正在進行 AI 推理辨識...")
        QApplication.processEvents()

        # YOLO 辨識
        results = self.model(self.current_image_path, conf=0.5)
        result = results[0]

        # 統計貓狗數量
        cat_count = 0
        dog_count = 0
        for box in result.boxes:
            cls_name = self.model.names[int(box.cls[0])]
            if cls_name == "cat":
                cat_count += 1
            elif cls_name == "dog":
                dog_count += 1

        self.lbl_cat_count.setText(f"貓 (Cats): {cat_count} 隻")
        self.lbl_dog_count.setText(f"狗 (Dogs): {dog_count} 隻")
        self.lbl_status.setText(f"辨識完成！共偵測到 {cat_count + dog_count} 隻目標。")

        # 轉換影像格式給 PyQt 顯示
        annotated_img = result.plot()
        rgb_img = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_img.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.image_display.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_display.setPixmap(scaled_pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CatDogDetectorApp()
    window.show()
    sys.exit(app.exec())