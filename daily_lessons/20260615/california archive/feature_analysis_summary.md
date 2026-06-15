# California Housing Feature Analysis & Selection Summary

This document summarizes the feature selection recommendations for the California Housing regression project based on evaluations across 10 different machine learning models.

---

## 1. Feature Ranking & Importance Matrix

Based on Mutual Information (MI) regression scores and feature importance outputs from linear and tree-based models:

| Feature Name | Type | Importance Rank | Action | Selection Reason |
| :--- | :--- | :---: | :---: | :--- |
| **`median_income`** | Numeric | **#1** | **Keep** | Primary driver of purchasing power. Highly correlated with house prices. |
| **`ocean_proximity`** | Categorical | **#2** | **Keep** | Encoded categories (`INLAND`, `NEAR OCEAN`, etc.) define local pricing tiers. |
| **`longitude` / `latitude`** | Numeric | **#3** | **Conditional** | Essential for **non-linear models** (XGBoost, Random Forest, SVR) to segment geographic zones. Exclude or replace for **linear models**. |
| **`housing_median_age`** | Numeric | **#4** | **Keep** | Captures historical premium/newer development cycles. Low collinearity. |
| **`total_rooms`** | Numeric | **#5** | **Select One** | Highly collinear with bedrooms/households. Only keep one raw count or convert to ratio. |
| **`households` / `population`** | Numeric | **#6** | **Select One** | Redundant when other density indicators are present. |

---

## 2. Algorithm-Specific Recommendations

### 🌲 Non-Linear & Tree-Based Models
*   **Algorithms**: Random Forest, XGBoost, SVR, Gradient Boosting, AdaBoost
*   **Optimal K (Features)**: **5 to 8**
*   **Recommended Set**: `['median_income', 'longitude', 'latitude', 'ocean_proximity_INLAND', 'housing_median_age']`
*   **Rationale**: Decision trees easily perform axis-aligned splits on longitude and latitude (e.g. bounding coordinates for high-value coastal regions like the SF Bay Area). This allows them to exploit coordinate parameters effectively.

### 📈 Linear & Regularized Models
*   **Algorithms**: Ridge, Lasso, ElasticNet, Linear Regression
*   **Optimal K (Features)**: **3 to 5**
*   **Recommended Set**: `['median_income', 'ocean_proximity_INLAND', 'housing_median_age', 'total_rooms']`
*   **Rationale**: Linear models attempt to fit monotonic relations. They struggle with geographic coordinates because prices peak on the coasts and drop inland (non-linear). Instead, they benefit from the categorical indicator `ocean_proximity_INLAND`, which applies a direct negative weight penalty.

---

## 3. Multicorrelation & Feature Engineering Advice

> [!WARNING]
> Including raw density counts (`total_rooms`, `total_bedrooms`, `population`, `households`) simultaneously creates severe **multicollinearity**!
> * **Linear models** will experience unstable coefficients.
> * **Tree-based models** will generate redundant splits, leading to overfitting.

### 💡 Recommendation
Replace raw counts with ratios:
$$\text{rooms\_per\_household} = \frac{\text{total\_rooms}}{\text{households}}$$
$$\text{bedrooms\_per\_room} = \frac{\text{total\_bedrooms}}{\text{total\_rooms}}$$
$$\text{population\_per\_household} = \frac{\text{population}}{\text{households}}$$
Using these engineered features dramatically improves regression stability and $R^2$ scores.
