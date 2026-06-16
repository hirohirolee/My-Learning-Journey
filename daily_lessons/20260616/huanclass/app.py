import streamlit as st
import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd

st.set_page_config(page_title="Iris 3D Classifier", layout="wide")
st.title("🌸 Iris — Logistic Regression 3D Explorer")

iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df["target"] = iris.target
df["species"] = [iris.target_names[t] for t in iris.target]

feat_names = iris.feature_names
col1, col2, col3 = st.columns(3)
x_feat = col1.selectbox("X axis", feat_names, index=0)
y_feat = col2.selectbox("Y axis", feat_names, index=1)
z_feat = col3.selectbox("Z axis", feat_names, index=2)

X = df[[x_feat, y_feat, z_feat]].values
y = df["target"].values
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)

clf = LogisticRegression(max_iter=500)
clf.fit(X_tr, y_tr)
y_pred_all = clf.predict(X)
y_pred_te  = clf.predict(X_te)

colors = ["#636EFA", "#EF553B", "#00CC96"]
symbols = ["circle", "square", "diamond"]
PALETTE = {name: colors[i] for i, name in enumerate(iris.target_names)}

# Decision-region mesh
n = 18
xs = np.linspace(X[:, 0].min(), X[:, 0].max(), n)
ys = np.linspace(X[:, 1].min(), X[:, 1].max(), n)
zs = np.linspace(X[:, 2].min(), X[:, 2].max(), n)
gx, gy, gz = np.meshgrid(xs, ys, zs)
grid = np.c_[gx.ravel(), gy.ravel(), gz.ravel()]
gp = clf.predict(grid)

fig = go.Figure()
for i, name in enumerate(iris.target_names):
    mask = gp == i
    fig.add_trace(go.Scatter3d(
        x=grid[mask, 0], y=grid[mask, 1], z=grid[mask, 2],
        mode="markers",
        marker=dict(size=2.5, color=colors[i], opacity=0.07),
        name=f"{name} region", showlegend=False,
    ))

for i, name in enumerate(iris.target_names):
    mask = iris.target == i
    correct = y_pred_all[mask] == i
    for ok, label, sym, op in [(correct, name, symbols[i], 1.0),
                                (~correct, f"{name} ✗", symbols[i], 0.9)]:
        if ok.any():
            fig.add_trace(go.Scatter3d(
                x=X[mask][ok, 0], y=X[mask][ok, 1], z=X[mask][ok, 2],
                mode="markers",
                marker=dict(size=5, color=colors[i], symbol=sym,
                            opacity=op, line=dict(width=1 if ok.all() else 2,
                            color="white" if ok.all() else "black")),
                name=label,
            ))

fig.update_layout(
    scene=dict(xaxis_title=x_feat, yaxis_title=y_feat, zaxis_title=z_feat),
    height=600, margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(itemsizing="constant"),
    template="plotly_dark",
)
st.plotly_chart(fig, use_container_width=True)

acc = accuracy_score(y_te, y_pred_te)
report = classification_report(y_te, y_pred_te, target_names=iris.target_names, output_dict=True)
st.subheader("📊 Test Metrics (25 % hold-out)")
m1, m2, m3 = st.columns(3)
m1.metric("Accuracy", f"{acc:.2%}")
m2.metric("Macro F1", f"{report['macro avg']['f1-score']:.3f}")
m3.metric("Weighted F1", f"{report['weighted avg']['f1-score']:.3f}")
st.dataframe(pd.DataFrame(report).T.style.format("{:.3f}"), use_container_width=True)
