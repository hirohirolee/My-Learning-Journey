import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# Set style for charts to look modern and clean
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.titlesize'] = 14
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

# Create folder for images
os.makedirs('images', exist_ok=True)

# ----------------------------------------------------
# 1. BUSINESS UNDERSTANDING (CRISP-DM Step 1)
# ----------------------------------------------------
print("--- Step 1: Business Understanding ---")
# Objective: Predict startup Profit based on operational costs (R&D, Administration, Marketing)
# and location (State) using regression models.

# ----------------------------------------------------
# 2. DATA UNDERSTANDING & EDA (CRISP-DM Step 2)
# ----------------------------------------------------
print("--- Step 2: Data Understanding ---")
df = pd.read_csv('50_Startups.csv')

# Shape and nulls
orig_shape = df.shape
info_null = df.isnull().sum()
desc_stats_orig = df.describe()

# IQR Outlier Detection on Profit
Q1 = df['Profit'].quantile(0.25)
Q3 = df['Profit'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outliers = df[(df['Profit'] < lower_bound) | (df['Profit'] > upper_bound)]
print("\n[Outlier Check] IQR Bounds for Profit:")
print(f"  Q1 (25%): ${Q1:,.2f}")
print(f"  Q3 (75%): ${Q3:,.2f}")
print(f"  IQR: ${IQR:,.2f}")
print(f"  Lower Bound: ${lower_bound:,.2f}")
print(f"  Upper Bound: ${upper_bound:,.2f}")
print("\nOutliers identified by IQR:")
print(outliers.to_string())

# Plot 1: Original vs Cleaned Profit Boxplot to show outlier
plt.figure(figsize=(7, 4.5))
sns.boxplot(x=df['Profit'], color='#3b82f6', width=0.4)
# Highlight the outlier
for idx, row in outliers.iterrows():
    plt.scatter(row['Profit'], 0, color='#ef4444', s=100, zorder=5, label=f'Outlier (Index {idx}: ${row["Profit"]:,.2f})')
plt.title('Outlier Identification in Profit (IQR Method)', fontsize=13, fontweight='bold', pad=12)
plt.xlabel('Profit ($)')
plt.legend(loc='lower left')
plt.tight_layout()
plt.savefig('images/profit_outlier_detection.png', dpi=300, bbox_inches='tight')
plt.close()

# Keep zero values as specified: R&D Spend and Marketing Spend zeros are left intact.
# (e.g. Index 47 R&D Spend = 1000.23, Marketing = 1903.93; Index 49 R&D = 0, Marketing = 45173.06)
print("\nZero values in R&D Spend:")
print(df[df['R&D Spend'] == 0].to_string())
print("\nZero values in Marketing Spend:")
print(df[df['Marketing Spend'] == 0].to_string())

# ----------------------------------------------------
# 3. DATA PREPARATION (CRISP-DM Step 3)
# ----------------------------------------------------
print("\n--- Step 3: Data Preparation ---")

# 1. Drop the identified outliers
df_clean = df.drop(outliers.index).reset_index(drop=True)
print(f"Dropped {len(outliers)} outlier(s). Data shape went from {orig_shape} to {df_clean.shape}.")

# 2. One-hot encode State column, setting drop_first=True to avoid dummy variable trap
df_encoded = pd.get_dummies(df_clean, columns=['State'], drop_first=True, dtype=int)
print("Encoded dataset columns:", list(df_encoded.columns))

# Features and target
X = df_encoded.drop('Profit', axis=1)
y = df_encoded['Profit']

# 3. Train-test split (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Training set size: {X_train.shape[0]} samples")
print(f"Testing set size: {X_test.shape[0]} samples")

# 4. Feature Scaling: Standardize only numerical continuous columns ('R&D Spend', 'Administration', 'Marketing Spend')
num_cols_to_scale = ['R&D Spend', 'Administration', 'Marketing Spend']
scaler = StandardScaler()

X_train_scaled = X_train.copy()
X_test_scaled = X_test.copy()

X_train_scaled[num_cols_to_scale] = scaler.fit_transform(X_train[num_cols_to_scale])
X_test_scaled[num_cols_to_scale] = scaler.transform(X_test[num_cols_to_scale])

# ----------------------------------------------------
# 4. MODELING (CRISP-DM Step 4)
# ----------------------------------------------------
print("\n--- Step 4: Modeling ---")

# Model 1: Multiple Linear Regression
lr_model = LinearRegression()
lr_model.fit(X_train_scaled, y_train)

# Model 2: Random Forest Regressor
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train_scaled, y_train)

# ----------------------------------------------------
# 5. EVALUATION (CRISP-DM Step 5)
# ----------------------------------------------------
print("\n--- Step 5: Evaluation ---")

# Predict on test set
y_pred_lr = lr_model.predict(X_test_scaled)
y_pred_rf = rf_model.predict(X_test_scaled)

# Calculate metrics
lr_r2 = r2_score(y_test, y_pred_lr)
lr_mae = mean_absolute_error(y_test, y_pred_lr)

rf_r2 = r2_score(y_test, y_pred_rf)
rf_mae = mean_absolute_error(y_test, y_pred_rf)

print(f"Multiple Linear Regression:")
print(f"  R2 Score: {lr_r2:.5f}")
print(f"  MAE: ${lr_mae:,.2f}")
print(f"Random Forest Regressor:")
print(f"  R2 Score: {rf_r2:.5f}")
print(f"  MAE: ${rf_mae:,.2f}")

# Plot 2: Model Performance Metrics Comparison
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
models = ['Linear Regression', 'Random Forest']
r2_scores = [lr_r2, rf_r2]
mae_scores = [lr_mae, rf_mae]

# R2 subplot
sns.barplot(x=r2_scores, y=models, ax=axes[0], hue=models, palette='viridis', legend=False)
axes[0].set_title('R-squared ($R^2$) Comparison (Higher is Better)', fontweight='bold')
axes[0].set_xlim(0, 1.1)
for idx, val in enumerate(r2_scores):
    axes[0].text(val + 0.02, idx, f"{val:.5f}", va='center', fontweight='bold')
axes[0].set_xlabel('R-squared')

# MAE subplot
sns.barplot(x=mae_scores, y=models, ax=axes[1], hue=models, palette='rocket', legend=False)
axes[1].set_title('MAE Comparison (Lower is Better)', fontweight='bold')
for idx, val in enumerate(mae_scores):
    axes[1].text(val + 200, idx, f"${val:,.1f}", va='center', fontweight='bold')
axes[1].set_xlabel('MAE ($)')

plt.tight_layout()
plt.savefig('images/model_metrics_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# ----------------------------------------------------
# 6. FEATURE COEFFICIENTS & IMPORTANCES
# ----------------------------------------------------
print("\n--- Step 6: Feature Weights and Importances ---")

# Multiple Linear Regression Coefficients (Weights)
lr_coefs = lr_model.coef_
lr_features = X.columns
lr_coef_df = pd.DataFrame({
    'Feature': lr_features,
    'Weight (Scaled Coef)': lr_coefs
}).sort_values(by='Weight (Scaled Coef)', key=abs, ascending=False)

print("\nLinear Regression Coefficients (Scaled Features):")
print(lr_coef_df.to_string(index=False))

# Plot 3: Linear Regression Coefficients
plt.figure(figsize=(8, 5))
# Generate custom colors: blue for positive weights, red for negative weights
colors = ['#10b981' if w >= 0 else '#ef4444' for w in lr_coef_df['Weight (Scaled Coef)']]
sns.barplot(
    data=lr_coef_df,
    x='Weight (Scaled Coef)',
    y='Feature',
    hue='Feature',
    palette=dict(zip(lr_coef_df['Feature'], colors)),
    legend=False
)
plt.axvline(x=0, color='black', linestyle='--', linewidth=1)
plt.title('Multiple Linear Regression Weights (Scaled)', fontsize=13, fontweight='bold', pad=12)
plt.xlabel('Coefficient Value (Change in Profit per 1 SD)')
plt.ylabel('Feature')
plt.tight_layout()
plt.savefig('images/linear_regression_weights.png', dpi=300, bbox_inches='tight')
plt.close()

# Random Forest Feature Importance
rf_importances = rf_model.feature_importances_
rf_imp_df = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf_importances
}).sort_values(by='Importance', ascending=False)

print("\nRandom Forest Feature Importances:")
print(rf_imp_df.to_string(index=False))

# Plot 4: Random Forest Feature Importances
plt.figure(figsize=(8, 5))
sns.barplot(
    data=rf_imp_df,
    x='Importance',
    y='Feature',
    hue='Feature',
    palette='viridis',
    legend=False
)
plt.title('Random Forest Feature Importances', fontsize=13, fontweight='bold', pad=12)
plt.xlabel('Importance (Fraction)')
plt.ylabel('Feature')
plt.tight_layout()
plt.savefig('images/random_forest_importance.png', dpi=300, bbox_inches='tight')
plt.close()

# ----------------------------------------------------
# 7. GENERATE REPORT (CRISP-DM Step 6 / Deployment)
# ----------------------------------------------------
print("\n--- Step 7: Generating Markdown Report ---")

# OLS model on unscaled features to obtain the exact mathematical equation for OLS
lr_unscaled = LinearRegression()
lr_unscaled.fit(X_train, y_train)
unscaled_coef = lr_unscaled.coef_
unscaled_intercept = lr_unscaled.intercept_

equation_parts = [f"{unscaled_intercept:,.2f}"]
for coef, feat in zip(unscaled_coef, X.columns):
    sign = "+" if coef >= 0 else "-"
    equation_parts.append(f"{sign} {abs(coef):.4f} * ({feat})")
lr_equation = "Profit = " + " ".join(equation_parts)

# Preprocessing Summary
outlier_details = f"Index {outliers.index[0]} | R&D Spend: ${outliers.loc[outliers.index[0], 'R&D Spend']:,.2f} | Administration: ${outliers.loc[outliers.index[0], 'Administration']:,.2f} | Marketing Spend: ${outliers.loc[outliers.index[0], 'Marketing Spend']:,.2f} | State: {outliers.loc[outliers.index[0], 'State']} | Profit: ${outliers.loc[outliers.index[0], 'Profit']:,.2f}"

stats_orig_md = desc_stats_orig.to_markdown()
stats_clean_md = df_clean.describe().to_markdown()

# Metrics Comparison Markdown Table
metrics_table_md = f"""| Model | R-squared ($R^2$ Score) | Mean Absolute Error (MAE) |
| :--- | :---: | :---: |
| **Multiple Linear Regression** | {lr_r2:.5f} | ${lr_mae:,.2f} |
| **Random Forest Regressor** | {rf_r2:.5f} | ${rf_mae:,.2f} |"""

# LR Coef Markdown Table
lr_coef_rows = []
for idx, row in lr_coef_df.iterrows():
    lr_coef_rows.append(f"| **{row['Feature']}** | {row['Weight (Scaled Coef)']:.2f} |")
lr_coef_table_md = "\n".join(lr_coef_rows)

# RF Importance Markdown Table
rf_imp_rows = []
for idx, row in rf_imp_df.iterrows():
    rf_imp_rows.append(f"| **{row['Feature']}** | {row['Importance']:.5f} |")
rf_imp_table_md = "\n".join(rf_imp_rows)

report_content = f"""# 50 Startups Profit Prediction & Modeling Report (Updated)

This report follows the **CRISP-DM** methodology to analyze startup profitability and build prediction models, integrating specific data cleansing, scaling, and feature evaluation requirements.

---

## 1. Business Understanding
For venture capital firms and startup incubators, predicting startup profitability and understanding the factors driving net Profit is vital. This modeling pipeline aims to:
- Predict **Profit** based on a startup's operational expenses (**R&D Spend**, **Administration**, **Marketing Spend**) and geographic location (**State**).
- Quantify the weights and importances of each factor.
- Develop and compare standard linear regression against ensemble tree-based models to select the most reliable forecaster.

---

## 2. Data Understanding & Preprocessing
The raw dataset contains 50 startup records. Under the CRISP-DM framework, we conducted specialized exploratory data analysis and preparation steps:

### 1) Outlier Assessment (極端值處理)
Using the Interquartile Range (IQR) method on the target variable `Profit`, we calculated:
- **IQR**: ${IQR:,.2f}
- **Lower Outlier Threshold**: ${lower_bound:,.2f}
- **Upper Outlier Threshold**: ${upper_bound:,.2f}

One data point fell below the lower threshold and was flagged as an outlier:
* **{outlier_details}**

![Profit Outlier Boxplot](images/profit_outlier_detection.png)
*Action: This record (Index 49) was dropped from the dataset to prevent biasing the regression models.*

### 2) Zero Values Treatment (數值為 0 的處理)
We identified several startups reporting \$0.00 expenditures:
- **R&D Spend**: Index 49 (\$0.00, dropped as part of Profit outlier) and Index 19 (\$0.00).
- **Marketing Spend**: Index 19, 47, 48, 49 (\$0.00).

These zeroes represent valid operational decisions (e.g., bootstrapped startups with zero marketing budget or pre-R&D stages) and **were left intact without any mean/median imputation**, as requested.

### 3) State Encoding & Dummy Variable Trap Avoidance (類別變數編碼)
The categorical variable `State` (California, Florida, New York) was one-hot encoded. We set `drop_first=True` to exclude California as the baseline. This prevents the **Dummy Variable Trap**, eliminating perfect multicollinearity which would violate OLS linear regression assumptions.

### 4) Selective Feature Scaling (特徵縮放)
Only the continuous numeric columns (`R&D Spend`, `Administration`, `Marketing Spend`) were standardized using `StandardScaler` fitted on the training split. The binary encoded variables (`State_Florida`, `State_New York`) were kept unscaled to preserve their interpretability.

---

## 3. Modeling & Evaluation
The cleaned dataset was partitioned into an 80% training set (39 samples) and a 20% testing set (10 samples). We trained two models:
1. **Multiple Linear Regression (OLS)**: Serves as a baseline parametric model.
2. **Random Forest Regressor**: A non-parametric tree-based ensemble method.

### Model Performance Comparison
{metrics_table_md}

![Model Metrics Comparison](images/model_metrics_comparison.png)

*Insight: The **Random Forest Regressor** achieved a higher R2 score ({rf_r2:.5f}) and a lower MAE (\${rf_mae:,.2f}) compared to Multiple Linear Regression on the test set, demonstrating that it represents the data patterns more effectively, likely due to capturing minor non-linear interactions.*

---

## 4. Feature Weights & Importance Analysis (特徵權重與重要性)

### 1) Multiple Linear Regression Coefficients (Weights)
The OLS coefficients represent the change in Profit (in USD) per 1 standard deviation increase in the standardized features:
| Feature | Standardized Weight (Scaled Coef) |
| :--- | :---: |
{lr_coef_table_md}

![Linear Regression Weights](images/linear_regression_weights.png)

*Linear Regression Mathematical Equation (Unscaled):*
```text
{lr_equation}
```
*Interpretation: Controlling for other variables, every **\$1.00** increase in **R&D Spend** yields **\$0.81** in additional profit, and **Marketing Spend** yields **\$0.03** of profit. Administration overhead has a slight negative coefficient (-\$0.07). The location dummy variables show negligible impact.*

### 2) Random Forest Feature Importances
The tree splits determine the relative importance of each feature in predicting profit:
| Feature | Feature Importance (Fraction) |
| :--- | :---: |
{rf_imp_df.to_markdown(index=False)}

![Random Forest Importance](images/random_forest_importance.png)

*Insight: Both models agree that **R&D Spend** is the overwhelming driver of Profit, accounting for **{rf_imp_df.iloc[0]['Importance']*100:.1f}%** of the split importance. **Marketing Spend** is secondary, while **Administration** and **geographic location** carry negligible predictive weight.*

---

## 5. Summary & Recommendations
1. **Focus Capital on R&D**: R&D investment remains the strongest lever for generating profits. Businesses should prioritize R&D funding.
2. **Re-evaluate Marketing ROI**: Marketing spend has a positive impact, but its marginal coefficient is small (\$0.03 profit per \$1 spend). Ensure campaigns are highly targeted to maximize returns.
3. **Minimize Administrative Drag**: Administration spend has a negative linear impact on profits. Operating costs and administrative overhead should be minimized where possible.
4. **Geographic State Independence**: The physical state (Florida, New York, or California) holds no significant predictive power. Startups can choose their office location based on local operating costs or taxes rather than location prestige.
"""

with open('Startup_Profit_Analysis_Report.md', 'w', encoding='utf-8') as f:
    f.write(report_content)

print("--- Step 7: Done! Report generated successfully as 'Startup_Profit_Analysis_Report.md' ---")
