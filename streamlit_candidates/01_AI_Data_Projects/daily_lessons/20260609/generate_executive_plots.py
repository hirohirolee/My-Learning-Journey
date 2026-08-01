import streamlit as st
st.title('generate_executive_plots.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

# Set clean style for business presentation
sns.set_theme(style="whitegrid")
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Segoe UI', 'DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# Create folders
os.makedirs('images', exist_ok=True)

# 1. Load and Clean Data
df = pd.read_csv('50_Startups.csv')

# Drop index 49 outlier as identified by IQR
df_clean = df.drop(index=49).reset_index(drop=True)

# 2. Encode State (drop California to avoid trap)
df_encoded = pd.get_dummies(df_clean, columns=['State'], drop_first=True, dtype=int)

X = df_encoded.drop('Profit', axis=1)
y = df_encoded['Profit']

# 3. Train-test split (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale numerical columns
num_cols = ['R&D Spend', 'Administration', 'Marketing Spend']
scaler = StandardScaler()
X_train_scaled = X_train.copy()
X_test_scaled = X_test.copy()
X_train_scaled[num_cols] = scaler.fit_transform(X_train[num_cols])
X_test_scaled[num_cols] = scaler.transform(X_test[num_cols])

# 4. Train Best Model (Random Forest)
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train_scaled, y_train)
y_pred = rf_model.predict(X_test_scaled)

# 5. Chart 1: Feature Importance with Business Labels
rf_importances = rf_model.feature_importances_
feature_mapping = {
    'R&D Spend': '研發投入 (R&D Spend)',
    'Marketing Spend': '行銷推廣 (Marketing Spend)',
    'Administration': '行政管理 (Administration)',
    'State_New York': '落腳紐約州 (New York)',
    'State_Florida': '落腳佛羅里達州 (Florida)'
}

importance_df = pd.DataFrame({
    'Feature': [feature_mapping[col] for col in X.columns],
    'Importance': rf_importances
}).sort_values(by='Importance', ascending=False)

plt.figure(figsize=(9, 5))
colors = ['#1e3b8a', '#0d9488', '#f59e0b', '#78716c', '#a8a29e']
sns.barplot(
    data=importance_df,
    x='Importance',
    y='Feature',
    hue='Feature',
    palette=colors[:len(importance_df)],
    legend=False
)

# Add value labels to bars
for idx, row in importance_df.reset_index(drop=True).iterrows():
    plt.text(row['Importance'] + 0.01, idx, f"{row['Importance']*100:.1f}%", va='center', fontweight='bold', fontsize=10)

plt.title('新創公司利潤驅動因子影響力排行 (特徵重要性)', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('對利潤的預測貢獻比例 (%)', fontsize=11)
plt.ylabel('支出與環境項目', fontsize=11)
plt.xlim(0, 1.1)
plt.tight_layout()
plt.savefig('images/executive_importance.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. Chart 2: Actual vs Predicted Scatter with Business Labels
plt.figure(figsize=(8, 6))
sns.scatterplot(x=y_test, y=y_pred, s=100, color='#0ea5e9', edgecolor='black', alpha=0.8, label='實際預測樣本')

# 45-degree diagonal line
min_val = min(y_test.min(), y_pred.min()) - 10000
max_val = max(y_test.max(), y_pred.max()) + 10000
plt.plot([min_val, max_val], [min_val, max_val], color='#ef4444', linestyle='--', linewidth=2, label='完美預測基準線 (45度線)')

plt.title('利潤預測準確度對比圖 (實際值 vs 預測值)', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('真實公司利潤 ($)', fontsize=11)
plt.ylabel('模型預估利潤 ($)', fontsize=11)
plt.xlim(min_val, max_val)
plt.ylim(min_val, max_val)
plt.legend(loc='upper left', frameon=True)
plt.tight_layout()
plt.savefig('images/executive_actual_vs_predicted.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 3: R&D Spend vs Profit Scatter Plot with Regression Line
plt.figure(figsize=(7, 5))
sns.regplot(data=df_clean, x='R&D Spend', y='Profit', color='#0d9488', 
            scatter_kws={'alpha':0.6, 's':60}, line_kws={'color':'#ef4444', 'ls':'--'})
plt.title('R&D Spend vs Profit (with Regression Line)', fontsize=13, fontweight='bold', pad=12)
plt.xlabel('R&D Spend ($)')
plt.ylabel('Profit ($)')
plt.tight_layout()
plt.savefig('images/rd_vs_profit_regplot.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 4: Seaborn Pairplot colored by State
pairplot_fig = sns.pairplot(df_clean, hue='State', palette='viridis', 
                            vars=['R&D Spend', 'Administration', 'Marketing Spend', 'Profit'])
pairplot_fig.savefig('images/pairplot.png', dpi=300)
plt.close()

st.write("Executive plots generated successfully!")

