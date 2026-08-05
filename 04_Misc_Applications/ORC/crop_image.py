import cv2
import os

def split_grid_image(image_path, output_dir, rows=6, cols=6):
    """
    將九宮格/多宮格圖片自動裁切成獨立小圖
    """
    # 建立輸出資料夾
    os.makedirs(output_dir, exist_ok=True)

    # 讀取圖片
    img = cv2.imread(image_path)
    if img is None:
        print(f"錯誤：找不到圖片 {image_path}")
        return

    # 取得圖片總長寬
    h, w, _ = img.shape
    
    # 計算每一小格的長寬
    cell_h = h // rows
    cell_w = w // cols

    count = 1
    for i in range(rows):
        for j in range(cols):
            # 計算裁切的座標範圍
            y1 = i * cell_h
            y2 = (i + 1) * cell_h
            x1 = j * cell_w
            x2 = (j + 1) * cell_w

            # 裁切圖片 (Numpy Array 切片)
            crop_img = img[y1:y2, x1:x2]
            
            # 存檔
            filename = os.path.join(output_dir, f"face_closeup_{count}.jpg")
            cv2.imwrite(filename, crop_img)
            print(f"已儲存: {filename}")
            count += 1

    print(f"\n✅ 成功！已將圖片裁切為 {count-1} 張小圖，儲存於 '{output_dir}' 資料夾。")

if __name__ == "__main__":
    # ⚠️ 請將下方的路徑換成你那張 36 宮格照片的實際檔名
    input_image = "sample_images/test7.jpg" 
    
    # 執行切圖 (預設切成 6 行 6 列 = 36 張)
    split_grid_image(input_image, "custom_dataset/images", rows=6, cols=6)