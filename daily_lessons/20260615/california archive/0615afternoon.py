import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
import webbrowser
import os

from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, mutual_info_regression
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor

try:
    from xgboost import XGBRegressor
    _xgb_available = True
except Exception:
    _xgb_available = False

import plotly.express as px

# -------------------------- 1️⃣ Data Preparation --------------------------
DATA_PATH = Path(r"D:\H\0615\california archive\housing.csv")
df = pd.read_csv(DATA_PATH)

# Clean total_bedrooms missing values
if 'total_bedrooms' in df.columns:
    df['total_bedrooms'] = df['total_bedrooms'].fillna(df['total_bedrooms'].mean())

y = np.log1p(df["median_house_value"])
X = df.drop(columns=["median_house_value"])

# One-hot encode categorical features
X_encoded = pd.get_dummies(X, columns=['ocean_proximity'], dtype=float)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_encoded, y, test_size=0.20, random_state=42
)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X_encoded.columns, index=X_train.index)

# -------------------------- 2️⃣ Modeling & Feature Loop --------------------------
# Sample 2000 rows for faster CV benchmark run on local machine
sample_size = min(2000, len(X_train))
X_train_cv = X_train_scaled_df.sample(n=sample_size, random_state=42)
y_train_cv = y_train.loc[X_train_cv.index]

models = {
    "LinearRegression": LinearRegression(),
    "Ridge": Ridge(random_state=42),
    "Lasso": Lasso(alpha=0.001, random_state=42),
    "ElasticNet": ElasticNet(alpha=0.001, random_state=42),
    "DecisionTree": DecisionTreeRegressor(random_state=42),
    "RandomForest": RandomForestRegressor(n_estimators=30, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=30, random_state=42),
    "AdaBoost": AdaBoostRegressor(n_estimators=30, random_state=42),
    "SVR": SVR(C=1.0),
}
if _xgb_available:
    models["XGBoost"] = XGBRegressor(n_estimators=30, learning_rate=0.1, random_state=42, n_jobs=-1, objective='reg:squarederror')
else:
    models["KNeighbors"] = KNeighborsRegressor()

results = []

# Nested loops: feature count (1‑10) × model
for k in range(1, 11):
    selector = SelectKBest(score_func=mutual_info_regression, k=min(k, X_train_cv.shape[1]))
    Xk = selector.fit_transform(X_train_cv.values, y_train_cv.values)

    cv = KFold(n_splits=3, shuffle=True, random_state=42)

    for name, model in models.items():
        neg_mse = cross_val_score(
            model,
            Xk,
            y_train_cv.values,
            scoring="neg_mean_squared_error",
            cv=cv,
            n_jobs=-1,
        )
        mse = -neg_mse.mean()
        results.append(
            {
                "Algorithm": name,
                "Number of Features": k,
                "MSE": mse,
            }
        )

# -------------------------- 3️⃣ Consolidate Results --------------------------
res_df = pd.DataFrame(results)

# -------------------------- 4️⃣ Visualization --------------------------
fig = px.line(
    res_df,
    x="Number of Features",
    y="MSE",
    color="Algorithm",
    markers=True,
    title="California Housing Model Performance vs. Feature Count",
)
fig.update_layout(yaxis=dict(type="log", title="Mean MSE (log scale)"))

# Save figure
output_path = Path("model_performance.html")
fig.write_html(output_path)

# Open in browser
webbrowser.open('file://' + os.path.abspath(output_path))
print(f"Interactive chart saved and opened from: {output_path.resolve()}")
