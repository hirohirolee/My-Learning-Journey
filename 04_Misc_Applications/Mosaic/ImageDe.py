import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import numpy as np
import cv2

# ========================
# 1. 模型定義
# ========================

class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.prelu = nn.PReLU()
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = self.conv1(x)
        residual = self.bn1(residual)
        residual = self.prelu(residual)
        residual = self.conv2(residual)
        residual = self.bn2(residual)
        return x + residual

class Generator(nn.Module):
    """
    生成器：從低解析度圖像重建高解析度圖像 (SRResNet 結構)
    """
    def __init__(self):
        super(Generator, self).__init__()
        
        # 初步特徵提取
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=9, padding=4),
            nn.PReLU()
        )
        
        # 殘差塊
        self.res_blocks = nn.Sequential(
            *[ResidualBlock(64) for _ in range(16)]
        )
        
        self.conv2 = nn.Sequential(
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64)
        )
        
        # 最終輸出
        self.final_conv = nn.Sequential(
            nn.Conv2d(64, 3, kernel_size=9, padding=4),
            nn.Tanh()  # 輸出範圍 [-1, 1]
        )

    def forward(self, x):
        conv1_out = self.conv1(x)
        res_out = self.res_blocks(conv1_out)
        conv2_out = self.conv2(res_out)
        out = conv1_out + conv2_out # Skip connection
        out = self.final_conv(out)
        return out

class Discriminator(nn.Module):
    """
    判别器：PatchGAN 結構
    """
    def __init__(self):
        super(Discriminator, self).__init__()
        
        def discriminator_block(in_filters, out_filters, stride=1, normalize=True):
            layers = [nn.Conv2d(in_filters, out_filters, kernel_size=3, stride=stride, padding=1)]
            if normalize:
                layers.append(nn.BatchNorm2d(out_filters))
            layers.append(nn.LeakyReLU(0.2, inplace=True))
            return layers

        self.model = nn.Sequential(
            *discriminator_block(3, 64, normalize=False),
            *discriminator_block(64, 64, stride=2),
            *discriminator_block(64, 128),
            *discriminator_block(128, 128, stride=2),
            *discriminator_block(128, 256),
            *discriminator_block(256, 256, stride=2),
            *discriminator_block(256, 512),
            *discriminator_block(512, 512, stride=2),
            nn.Conv2d(512, 1, kernel_size=3, stride=1, padding=1)
        )

    def forward(self, img):
        return self.model(img)

class FeatureExtractor(nn.Module):
    """
    用於計算感知損失的 VGG19 特徵提取器
    """
    def __init__(self):
        super(FeatureExtractor, self).__init__()
        vgg19 = torchvision.models.vgg19(weights=torchvision.models.VGG19_Weights.IMAGENET1K_V1)
        # 使用 VGG19 的 feature extractor 直到 activation of conv5_4
        self.feature_extractor = nn.Sequential(*list(vgg19.features.children())[:36])
        for param in self.feature_extractor.parameters():
            param.requires_grad = False

    def forward(self, x):
        # 轉換輸入從 [-1, 1] 到 [0, 1] 然後標準化 (ImageNet)
        x = (x + 1.0) / 2.0
        mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).to(x.device)
        std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).to(x.device)
        x = (x - mean) / std
        return self.feature_extractor(x)

# ========================
# 2. 輔助函數與訓練流程
# ========================

def create_dummy_image(image_path, size=(256, 256)):
    """如果圖片不存在，則建立一張測試用圖片"""
    if not os.path.exists(image_path):
        img = np.zeros((*size, 3), dtype=np.uint8)
        cv2.circle(img, (128, 128), 64, (0, 255, 0), -1)
        cv2.rectangle(img, (64, 64), (192, 192), (255, 0, 0), 2)
        cv2.putText(img, "Test", (60, 135), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        cv2.imwrite(image_path, img)
        print(f"建立測試用圖片: {image_path}")

def load_and_preprocess_image(image_path, size=(256, 256)):
    """載入圖像並下採樣以模擬馬賽克效果"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"無法讀取圖片: {image_path}")
    
    # 轉換成 RGB，方便神經網絡處理
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 縮小圖像以模擬馬賽克 (下採樣)
    downscale_size = (size[0] // 4, size[1] // 4)
    small_img = cv2.resize(img, downscale_size, interpolation=cv2.INTER_AREA)
    
    # 擴展回原始大小
    hr_img = cv2.resize(img, size, interpolation=cv2.INTER_CUBIC)
    lr_img_resized = cv2.resize(small_img, size, interpolation=cv2.INTER_CUBIC)
    
    # 轉換為 PyTorch Tensor，範圍從 [0, 255] 轉換為 [-1, 1]
    tensor_hr = torch.from_numpy(hr_img.astype(np.float32) / 127.5 - 1).permute(2, 0, 1)
    tensor_lr = torch.from_numpy(lr_img_resized.astype(np.float32) / 127.5 - 1).permute(2, 0, 1)
    
    return tensor_lr, tensor_hr, img

def adversarial_loss(output, is_real):
    """二分類交叉熵損失 (使用 BCEWithLogitsLoss 因為判別器結尾沒有 sigmoid)"""
    target = torch.full_like(output, 1.0 if is_real else 0.0)
    loss = nn.BCEWithLogitsLoss()(output, target)
    return loss

def train_step(generator, discriminator, feature_extractor, optimizer_g, optimizer_d, lr_imgs, hr_imgs):
    """單步訓練"""
    # ========================
    # 訓練 Discriminator
    # ========================
    optimizer_d.zero_grad()
    
    # 判別器對真實高解析度圖像的判斷
    real_pred = discriminator(hr_imgs)
    d_loss_real = adversarial_loss(real_pred, is_real=True)
    
    # 判別器對生成圖像的判斷
    fake_hr_imgs = generator(lr_imgs)
    fake_pred = discriminator(fake_hr_imgs.detach())
    d_loss_fake = adversarial_loss(fake_pred, is_real=False)
    
    d_loss = d_loss_real + d_loss_fake
    d_loss.backward()
    optimizer_d.step()
    
    # ========================
    # 訓練 Generator
    # ========================
    optimizer_g.zero_grad()
    
    # 騙過 Discriminator
    fake_pred_g = discriminator(fake_hr_imgs)
    g_loss_adv = adversarial_loss(fake_pred_g, is_real=True)
    
    # 感知損失 (Content Loss)
    real_features = feature_extractor(hr_imgs).detach()
    fake_features = feature_extractor(fake_hr_imgs)
    g_loss_content = nn.MSELoss()(fake_features, real_features)
    
    # 總 Generator Loss
    g_loss = g_loss_content + 1e-3 * g_loss_adv
    
    g_loss.backward()
    optimizer_g.step()
    
    return d_loss.item(), g_loss.item()

# ========================
# 3. 主執行流程
# ========================
def main():
    parser = argparse.ArgumentParser(description="Image Super Resolution / De-Mosaic")
    parser.add_argument("--image", type=str, default="sample_image.jpg", help="你要處理的圖片路徑 (預設為 sample_image.jpg)")
    parser.add_argument("--epochs", type=int, default=100, help="訓練次數 (預設 100)")
    args = parser.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用裝置: {device}")

    # 初始化模型
    generator = Generator().to(device)
    discriminator = Discriminator().to(device)
    feature_extractor = FeatureExtractor().to(device).eval()

    # 初始化優化器
    optimizer_g = optim.Adam(generator.parameters(), lr=0.0001, betas=(0.9, 0.999))
    optimizer_d = optim.Adam(discriminator.parameters(), lr=0.0001, betas=(0.9, 0.999))

    # 確保圖片存在，若無則生成測試圖片 (僅限預設的 sample_image.jpg)
    image_path = args.image
    if image_path == "sample_image.jpg":
        create_dummy_image(image_path)
    elif not os.path.exists(image_path):
        print(f"錯誤：找不到圖片 '{image_path}'！請確認路徑是否正確。")
        return

    # 載入圖像並處理
    lr_tensor, hr_tensor, original_img = load_and_preprocess_image(image_path)
    lr_tensor = lr_tensor.unsqueeze(0).to(device)
    hr_tensor = hr_tensor.unsqueeze(0).to(device)

    # 訓練
    epochs = args.epochs
    print(f"開始針對圖片 '{image_path}' 進行訓練 (共 {epochs} Epochs)...")
    for epoch in range(epochs):
        generator.train()
        discriminator.train()
        
        d_loss, g_loss = train_step(generator, discriminator, feature_extractor, 
                                    optimizer_g, optimizer_d, lr_tensor, hr_tensor)
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], D Loss: {d_loss:.4f}, G Loss: {g_loss:.4f}")

    # 測試結果
    generator.eval()
    with torch.no_grad():
        sr_tensor = generator(lr_tensor)
        
        # 轉換回 numpy 圖像 [0, 255] BGR 供 opencv 儲存
        def tensor_to_img(tensor):
            img = tensor.cpu().numpy().squeeze().transpose(1, 2, 0)
            img = (img * 127.5 + 127.5).clip(0, 255).astype(np.uint8)
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        sr_image = tensor_to_img(sr_tensor)
        lr_image = tensor_to_img(lr_tensor)
        hr_image = tensor_to_img(hr_tensor)
        
        # 保存結果
        cv2.imwrite("result_sr.jpg", sr_image)
        cv2.imwrite("result_lr.jpg", lr_image)
        cv2.imwrite("result_hr.jpg", hr_image)
        
        print("\n訓練完成！結果已保存:")
        print("- result_lr.jpg (馬賽克/低畫質圖片)")
        print("- result_sr.jpg (AI 修復後圖片)")
        print("- result_hr.jpg (原始目標圖片)")

if __name__ == '__main__':
    main()
