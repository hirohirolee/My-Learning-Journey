import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
import webbrowser
import os

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import f_regression, mutual_info_regression, RFE
from sklearn.linear_model import LinearRegression, LassoCV
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import spearmanr
from sklearn.metrics import mean_squared_error, r2_score
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# -------------------------- 1️⃣ Data Preparation --------------------------
DATA_PATH = Path(r"D:\H\0615\archive\HousingData.csv")
df = pd.read_csv(DATA_PATH)

# Clean missing values
for col in df.columns:
    if df[col].isnull().any():
        df[col] = df[col].fillna(df[col].mean())

y = df["MEDV"]  # Target is already in $1000s
X = df.drop(columns=["MEDV"])

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

total_features = X.shape[1]

# -------------------------- 2️⃣ Feature Selector Rankings --------------------------
print("Running feature selection algorithms...")

# 1. Pearson Correlation
pearson_scores = [np.abs(np.corrcoef(X_train_scaled[:, i], y_train)[0, 1]) for i in range(total_features)]
pearson_rank = np.argsort(pearson_scores)[::-1]

# 2. Spearman Correlation
spearman_scores = [np.abs(spearmanr(X_train_scaled[:, i], y_train).correlation) for i in range(total_features)]
spearman_rank = np.argsort(spearman_scores)[::-1]

# 3. F-test Regression
f_scores, _ = f_regression(X_train_scaled, y_train)
f_rank = np.argsort(f_scores)[::-1]

# 4. Mutual Information
mi_scores = mutual_info_regression(X_train_scaled, y_train, random_state=42)
mi_rank = np.argsort(mi_scores)[::-1]

# 5. RFE (Recursive Feature Elimination)
rfe = RFE(estimator=LinearRegression(), n_features_to_select=1)
rfe.fit(X_train_scaled, y_train)
rfe_rank = np.argsort(rfe.ranking_)

# 6. Lasso L1 Coefficient Magnitudes
lasso = LassoCV(cv=5, random_state=42).fit(X_train_scaled, y_train)
lasso_coefs = np.abs(lasso.coef_)
# Avoid all zero coefficients by ranking all features, even if lasso set them to 0
lasso_rank = np.argsort(lasso_coefs)[::-1]

# 7. Random Forest Feature Importances
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1).fit(X_train_scaled, y_train)
rf_rank = np.argsort(rf.feature_importances_)[::-1]

# 8. Sequential Forward Selection (SFS)
def forward_selection(X, y):
    selected = []
    remaining = list(range(X.shape[1]))
    while remaining:
        best_score = -np.inf
        best_feat = None
        for f in remaining:
            candidate = selected + [f]
            # Evaluate using cross_val_score on 3 folds for speed
            score = np.mean(cross_val_score(LinearRegression(), X[:, candidate], y, cv=3, scoring='r2'))
            if score > best_score:
                best_score = score
                best_feat = f
        selected.append(best_feat)
        remaining.remove(best_feat)
    return selected

sfs_rank = forward_selection(X_train_scaled, y_train)

selectors = {
    "Pearson Corr": pearson_rank,
    "Spearman Corr": spearman_rank,
    "F-test Reg": f_rank,
    "Mutual Info": mi_rank,
    "RFE": rfe_rank,
    "Lasso (L1)": lasso_rank,
    "Random Forest": rf_rank,
    "SFS (Forward)": sfs_rank
}

# -------------------------- 3️⃣ Stepwise Evaluation Loop --------------------------
print("Evaluating feature subsets...")
results = []

for name, rank in selectors.items():
    for k in range(1, total_features + 1):
        selected_indices = rank[:k]
        
        # Train base LinearRegression estimator
        model = LinearRegression()
        model.fit(X_train_scaled[:, selected_indices], y_train)
        
        # Test predictions
        preds = model.predict(X_test_scaled[:, selected_indices])
        
        # Metrics
        r2 = r2_score(y_test, preds)
        mse = mean_squared_error(y_test, preds)
        
        results.append({
            "Selector": name,
            "Number of Features": k,
            "R2": r2,
            "MSE": mse
        })

res_df = pd.DataFrame(results)

# -------------------------- 4️⃣ Visualizations (Dual Subplots) --------------------------
fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("Test R-squared Score by Feature Subset Size", "Test MSE by Feature Subset Size")
)

# Colors matching teacher's screenshot vibes (harmonious slate/pastels)
colors = {
    "Pearson Corr": "#1f77b4",
    "Spearman Corr": "#aec7e8",
    "F-test Reg": "#ff7f0e",
    "Mutual Info": "#ffbb78",
    "RFE": "#2ca02c",
    "Lasso (L1)": "#98df8a",
    "Random Forest": "#d62728",
    "SFS (Forward)": "#ff9896"
}

for name in selectors.keys():
    sub_df = res_df[res_df["Selector"] == name]
    
    # R2 plot (Left)
    fig.add_trace(
        go.Scatter(
            x=sub_df["Number of Features"],
            y=sub_df["R2"],
            mode="lines+markers",
            name=name,
            line=dict(color=colors[name]),
            legendgroup=name
        ),
        row=1, col=1
    )
    
    # MSE plot (Right)
    fig.add_trace(
        go.Scatter(
            x=sub_df["Number of Features"],
            y=sub_df["MSE"],
            mode="lines+markers",
            name=name,
            line=dict(color=colors[name]),
            legendgroup=name,
            showlegend=False
        ),
        row=1, col=2
    )

# Customize Layout
fig.update_layout(
    title_text="Boston Housing CRISP-DM Feature Selection Stepwise Evaluation Plot",
    template="plotly_dark",
    font=dict(family="Inter, sans-serif"),
    margin=dict(t=80, b=40, l=40, r=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

fig.update_xaxes(title_text="Number of Features in Model", dtick=1, row=1, col=1)
fig.update_xaxes(title_text="Number of Features in Model", dtick=1, row=1, col=2)
fig.update_yaxes(title_text="Test R-squared", row=1, col=1)
fig.update_yaxes(title_text="Test Mean Squared Error (MSE)", row=1, col=2)

# Save figure
output_path = Path("model_performance.html")
fig.write_html(output_path)

# Open in browser
webbrowser.open('file://' + os.path.abspath(output_path))
print(f"Boston Interactive chart saved and opened from: {output_path.resolve()}")