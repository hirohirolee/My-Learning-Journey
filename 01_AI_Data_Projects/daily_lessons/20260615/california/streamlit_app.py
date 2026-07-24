import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import (
    f_regression, mutual_info_regression, RFE, SelectKBest
)
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet, LassoCV
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import spearmanr

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="California Housing ML Studio",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f0f1a; }
[data-testid="stSidebar"] { background: #1a1a2e; }
h1, h2, h3 { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    csv_path = Path(__file__).parent / "housing.csv"
    df = pd.read_csv(csv_path)
    if "total_bedrooms" in df.columns:
        df["total_bedrooms"] = df["total_bedrooms"].fillna(df["total_bedrooms"].median())
    return df

# ── Sidebar Controls ─────────────────────────────────────────────────────────
st.sidebar.title("🌴 California Housing")
st.sidebar.markdown("---")

ALGOS = [
    "LinearRegression", "Ridge", "Lasso", "ElasticNet",
    "DecisionTree", "RandomForest", "GradientBoosting",
    "AdaBoost", "SVR", "KNeighbors"
]

algo       = st.sidebar.selectbox("🤖 演算法", ALGOS, index=1)
k_features = st.sidebar.slider("🔢 特徵數量 K", 1, 13, 10)
test_size  = st.sidebar.slider("📊 測試集比例", 0.1, 0.4, 0.2, step=0.05)
alpha      = st.sidebar.number_input("⚙️ Alpha（正則化強度）", 0.01, 100.0, 1.0)

use_depth  = algo in ("DecisionTree", "RandomForest", "GradientBoosting")
max_depth  = st.sidebar.slider("🌲 Max Depth（樹狀模型）", 1, 20, 5) if use_depth else None

st.sidebar.markdown("---")
run_btn = st.sidebar.button("🔥 開始訓練", use_container_width=True)

# ── Main Title ────────────────────────────────────────────────────────────────
st.title("🌴 California Housing — ML Studio")
st.markdown("依 CRISP-DM 流程比較多種演算法與特徵選擇方法")

if not run_btn:
    st.info("👈 請在左側選擇參數，然後點擊「🔥 開始訓練」開始分析。")
    st.stop()

# ── Training ──────────────────────────────────────────────────────────────────
with st.spinner("⏳ 訓練中，請稍候（California 資料集較大，約 10～30 秒）..."):
    df = load_data()
    y  = df["median_house_value"] / 1000.0   # in $1000s
    X  = df.drop(columns=["median_house_value"])

    # One-hot encode ocean_proximity
    X_encoded = pd.get_dummies(X, columns=["ocean_proximity"], dtype=float)
    total_features = X_encoded.shape[1]

    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=test_size, random_state=42
    )

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)
    X_train_sc_df = pd.DataFrame(X_train_sc, columns=X_encoded.columns, index=X_train.index)
    X_test_sc_df  = pd.DataFrame(X_test_sc,  columns=X_encoded.columns, index=X_test.index)

    # SelectKBest with downsampling for speed
    k_real      = min(k_features, total_features)
    sample_size = min(3000, len(X_train))
    X_sample    = X_train_sc_df.sample(n=sample_size, random_state=42)
    y_sample    = y_train.loc[X_sample.index]

    selector = SelectKBest(score_func=mutual_info_regression, k=k_real)
    selector.fit(X_sample.values, y_sample.values)
    selected_cols = X_encoded.columns[selector.get_support()].tolist()
    mi_scores_arr = selector.scores_

    X_tr_sel = X_train_sc_df[selected_cols].values
    X_te_sel = X_test_sc_df[selected_cols].values

    MODEL_MAP = {
        "LinearRegression":  LinearRegression(),
        "Ridge":             Ridge(alpha=alpha, random_state=42),
        "Lasso":             Lasso(alpha=alpha, random_state=42),
        "ElasticNet":        ElasticNet(alpha=alpha, random_state=42),
        "DecisionTree":      DecisionTreeRegressor(max_depth=max_depth, random_state=42),
        "RandomForest":      RandomForestRegressor(n_estimators=100, max_depth=max_depth, random_state=42, n_jobs=-1),
        "GradientBoosting":  GradientBoostingRegressor(n_estimators=100, max_depth=max_depth or 3, random_state=42),
        "AdaBoost":          AdaBoostRegressor(n_estimators=100, random_state=42),
        "SVR":               SVR(C=alpha),
        "KNeighbors":        KNeighborsRegressor(),
    }
    model = MODEL_MAP.get(algo, Ridge(alpha=alpha, random_state=42))
    model.fit(X_tr_sel, y_train)

    pred_train = model.predict(X_tr_sel)
    pred_test  = model.predict(X_te_sel)

    # Convert back to USD for display
    y_train_usd = y_train * 1000.0
    y_test_usd  = y_test  * 1000.0
    pred_train_usd = pred_train * 1000.0
    pred_test_usd  = pred_test  * 1000.0

    train_rmse = float(np.sqrt(mean_squared_error(y_train_usd, pred_train_usd)))
    test_rmse  = float(np.sqrt(mean_squared_error(y_test_usd,  pred_test_usd)))
    train_r2   = float(r2_score(y_train_usd, pred_train_usd))
    test_r2    = float(r2_score(y_test_usd,  pred_test_usd))

    if hasattr(model, "feature_importances_"):
        imp = dict(zip(selected_cols, model.feature_importances_))
    elif hasattr(model, "coef_"):
        imp = dict(zip(selected_cols, np.abs(model.coef_)))
    else:
        imp = {c: 0.0 for c in selected_cols}

    # ── Benchmark with CV downsampling ────────────────────────────────────────
    cv_size   = min(1500, len(X_train))
    X_cv      = X_train_sc_df.sample(n=cv_size, random_state=42)
    y_cv      = y_train.loc[X_cv.index]

    pearson_sc  = [np.abs(np.corrcoef(X_cv.values[:, i], y_cv.values)[0, 1]) for i in range(total_features)]
    spearman_sc = [np.abs(spearmanr(X_cv.values[:, i], y_cv.values).correlation) for i in range(total_features)]
    f_sc, _     = f_regression(X_cv.values, y_cv.values)
    mi_sc       = mutual_info_regression(X_cv.values, y_cv.values, random_state=42)

    rfe = RFE(estimator=LinearRegression(), n_features_to_select=1)
    rfe.fit(X_cv.values, y_cv.values)

    lasso_cv  = LassoCV(cv=3, random_state=42).fit(X_cv.values, y_cv.values)
    rf_bench  = RandomForestRegressor(n_estimators=15, random_state=42, n_jobs=-1).fit(X_cv.values, y_cv.values)

    sfs_selected, sfs_remaining = [], list(range(total_features))
    while sfs_remaining:
        best_s, best_f = -np.inf, None
        for f in sfs_remaining:
            s = np.mean(cross_val_score(LinearRegression(), X_cv.values[:, sfs_selected + [f]], y_cv.values, cv=3, scoring="r2"))
            if s > best_s:
                best_s, best_f = s, f
        sfs_selected.append(best_f)
        sfs_remaining.remove(best_f)

    selectors = {
        "Pearson Corr":  np.argsort(pearson_sc)[::-1],
        "Spearman Corr": np.argsort(spearman_sc)[::-1],
        "F-test Reg":    np.argsort(f_sc)[::-1],
        "Mutual Info":   np.argsort(mi_sc)[::-1],
        "RFE":           np.argsort(rfe.ranking_),
        "Lasso (L1)":    np.argsort(np.abs(lasso_cv.coef_))[::-1],
        "Random Forest": np.argsort(rf_bench.feature_importances_)[::-1],
        "SFS (Forward)": sfs_selected,
    }

    bench_rows = []
    for name, rank in selectors.items():
        for kv in range(1, total_features + 1):
            idx   = list(rank[:kv])
            m_ev  = LinearRegression()
            m_ev.fit(X_train_sc[:, idx], y_train)
            preds = m_ev.predict(X_test_sc[:, idx])
            bench_rows.append({
                "Selector": name, "K": kv,
                "R2":  float(r2_score(y_test, preds)),
                "MSE": float(mean_squared_error(y_test, preds)),
            })
    bench_df = pd.DataFrame(bench_rows)

# ── Layout: 3 Tabs ───────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 模型評估", "🔍 特徵分析", "📈 比較圖"])

# ─── Tab 1 ───────────────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"模型：{algo}  ·  特徵數 K={k_real}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏋️ Train RMSE (USD)", f"${train_rmse:,.0f}")
    c2.metric("🎯 Test RMSE (USD)",  f"${test_rmse:,.0f}")
    c3.metric("📐 Train R²",         f"{train_r2:.4f}")
    c4.metric("✅ Test R²",          f"{test_r2:.4f}")

    st.markdown("#### 實際值 vs 預測值（測試集散佈圖）")
    sample_idx = np.random.RandomState(42).choice(len(y_test_usd), min(500, len(y_test_usd)), replace=False)
    fig_sc = go.Figure()
    fig_sc.add_trace(go.Scatter(
        x=y_test_usd.iloc[sample_idx].values,
        y=pred_test_usd[sample_idx],
        mode="markers",
        marker=dict(color="#6366f1", opacity=0.6, size=5),
        name="預測點"
    ))
    mn, mx = float(y_test_usd.min()), float(y_test_usd.max())
    fig_sc.add_trace(go.Scatter(
        x=[mn, mx], y=[mn, mx], mode="lines",
        line=dict(color="#10b981", dash="dash"), name="完美預測線"
    ))
    fig_sc.update_layout(
        template="plotly_dark", height=420,
        xaxis_title="實際房價 (USD)", yaxis_title="預測房價 (USD)",
        margin=dict(t=30, b=40, l=60, r=20)
    )
    st.plotly_chart(fig_sc, use_container_width=True)

# ─── Tab 2 ───────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("特徵重要性分析")
    st.markdown(f"**選中特徵（K={k_real}）：** {', '.join(selected_cols)}")

    imp_sorted = sorted(imp.items(), key=lambda x: x[1], reverse=True)
    fig_imp = go.Figure(go.Bar(
        x=[i[1] for i in imp_sorted],
        y=[i[0] for i in imp_sorted],
        orientation="h", marker=dict(color="#a78bfa"),
    ))
    fig_imp.update_layout(
        template="plotly_dark", height=max(300, 35 * len(imp_sorted)),
        xaxis_title="重要性分數", yaxis=dict(autorange="reversed"),
        margin=dict(t=20, b=40, l=160, r=20)
    )
    st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("#### 所有特徵 Mutual Info 分數")
    mi_df = pd.DataFrame({
        "Feature": X_encoded.columns,
        "MI Score": mi_scores_arr
    }).sort_values("MI Score", ascending=False).reset_index(drop=True)
    st.dataframe(mi_df, use_container_width=True)

# ─── Tab 3 ───────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("8 種特徵選擇器 × 所有 K 值的 R² / MSE 比較")

    COLORS = {
        "Pearson Corr":  "#1f77b4",
        "Spearman Corr": "#aec7e8",
        "F-test Reg":    "#ff7f0e",
        "Mutual Info":   "#ffbb78",
        "RFE":           "#2ca02c",
        "Lasso (L1)":    "#98df8a",
        "Random Forest": "#d62728",
        "SFS (Forward)": "#ff9896",
    }

    fig_bench = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Test R² by Feature Subset Size", "Test MSE by Feature Subset Size")
    )
    for name in selectors:
        sub = bench_df[bench_df["Selector"] == name]
        fig_bench.add_trace(
            go.Scatter(x=sub["K"], y=sub["R2"], mode="lines+markers",
                       name=name, line=dict(color=COLORS[name]), legendgroup=name),
            row=1, col=1
        )
        fig_bench.add_trace(
            go.Scatter(x=sub["K"], y=sub["MSE"], mode="lines+markers",
                       name=name, line=dict(color=COLORS[name]), legendgroup=name, showlegend=False),
            row=1, col=2
        )
    fig_bench.update_layout(
        template="plotly_dark", height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=40, r=20)
    )
    fig_bench.update_xaxes(title_text="Number of Features", dtick=1)
    fig_bench.update_yaxes(title_text="Test R²",  row=1, col=1)
    fig_bench.update_yaxes(title_text="Test MSE", row=1, col=2)
    st.plotly_chart(fig_bench, use_container_width=True)
