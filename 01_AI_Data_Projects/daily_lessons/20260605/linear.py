import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

# ==============================================================================
# CRISP-DM 階段 1 & 2：商業與數據理解 (Business & Data Understanding)
# 目標：建立線性回歸模型，並找出預測誤差（殘差）最大的前 20 個異常點（Outliers）。
# ==============================================================================

# 固定隨機種子，確保每次執行的結果都一樣，方便觀察
np.random.seed(42)

# 1. 產生兩百個隨機點 (x, y)
# x 的範圍是 0 ~ 100
x = np.random.uniform(0, 100, 200)

# 標準常態分佈 N(0,1) 的隨機雜訊
noise = np.random.normal(0, 1, 200)

# y 的形式是 30x + 100 + 10 * N(0,1)
y = 30 * x + 100 + 10 * noise

# ==============================================================================
# CRISP-DM 階段 3：數據準備 (Data Preparation)
# Scikit-learn 的線性回歸模型要求輸入的 X 必須是二維矩陣 (n_samples, n_features)
# ==============================================================================
X_matrix = x.reshape(-1, 1)

# ==============================================================================
# CRISP-DM 階段 4：建模 (Modeling)
# ==============================================================================
model = LinearRegression()
model.fit(X_matrix, y)  # 讓模型學習這 200 個點的規律
y_pred = model.predict(X_matrix)  # 計算出模型對每個 x 的「預測值」

# ==============================================================================
# CRISP-DM 階段 5：評估與異常值偵測 (Evaluation & Outlier Detection)
# 計算「真實 y 值」與「預測 y 值」之間的絕對誤差（即殘差）
# ==============================================================================
residuals = np.abs(y - y_pred)

# 找出誤差最大的 20 個點的索引
# np.argsort 會將誤差從小到大排序，傳回索引。
# [-20:] 代表取出最後 20 個（也就是誤差最大的 20 個），[::-1] 代表將其反轉，讓最大的排在最前面
top_20_outliers_idx = np.argsort(residuals)[-20:][::-1]

# ==============================================================================
# CRISP-DM 階段 6：部署與視覺化呈現 (Deployment / Visualization)
# ==============================================================================
plt.figure(figsize=(10, 7))

# 2. 畫出散佈圖，一般的點是藍色的 (這裡先將所有點畫成藍色)
plt.scatter(x, y, color="blue", alpha=0.6, label="Normal Data")

# 3. 畫出紅色回歸線
# 為了讓劃線順暢，我們將 x 軸資料排序後再進行連線
sort_idx = np.argsort(x)
plt.plot(
    x[sort_idx],
    y_pred[sort_idx],
    color="red",
    linewidth=2,
    label="Regression Line",
)

# 4. 把 20 個誤差最大的 outlier 用紅色標記出來，並在圖上標記順序
# 我們在原本的藍點上方，重疊疊加一個紅色的點，並加大面積 (s=100) 突顯它
plt.scatter(
    x[top_20_outliers_idx],
    y[top_20_outliers_idx],
    color="red",
    edgecolors="black",
    s=90,
    zorder=5,
    label="Top 20 Outliers",
)

# 使用迴圈，在每個異常點旁邊加上文字標記順序（1 代表誤差最大）
for rank, idx in enumerate(top_20_outliers_idx):
    # rank 從 0 開始，所以標記文字要 +1
    label_text = str(rank + 1)
    # plt.text(X座標, Y座標, 要顯示的文字)
    # x[idx]+1 和 y[idx]+2 是為了讓文字偏移一點點，不會剛好擋住紅色的點
    plt.text(
        x[idx] + 1,
        y[idx] + 2,
        label_text,
        color="darkred",
        fontsize=10,
        weight="bold",
    )

# 加上圖表的基本資訊
plt.title("Linear Regression & Outlier Detection (CRISP-DM)", fontsize=14)
plt.xlabel("X")
plt.ylabel("Y")
plt.legend()  # 顯示圖例
plt.grid(True, linestyle="--", alpha=0.5)  # 加上背景網格

# 顯示成果圖表
plt.show()