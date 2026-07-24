import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# ==============================================================================
# Page Configuration & Styling
# ==============================================================================
st.set_page_config(
    page_title="Linear Regression & Outlier Detector",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern premium looks
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    .title-text {
        font-family: 'Outfit', 'Inter', sans-serif;
        color: #1e293b;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .subtitle-text {
        font-family: 'Inter', sans-serif;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("<h1 class='title-text'>📈 Linear Regression & Outlier Detector</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle-text'>Interactively generate synthetic linear data, fit a regression model, and detect statistical outliers (residuals) in real-time.</p>", unsafe_allow_html=True)

# ==============================================================================
# Sidebar controls (a, b, N)
# ==============================================================================
st.sidebar.markdown("### 🛠️ Model Parameters")

# Random Seed for reproducibility
seed_option = st.sidebar.checkbox("Fix Random Seed (Reproducible)", value=True)
if seed_option:
    seed_value = st.sidebar.number_input("Seed Value", min_value=0, max_value=99999, value=42)
    np.random.seed(seed_value)
else:
    # Use random state that varies
    np.random.seed(None)

# N (Number of points)
N = st.sidebar.slider(
    "Number of Data Points (N)",
    min_value=10,
    max_value=1000,
    value=200,
    step=10,
    help="Total number of random samples generated."
)

# a (Slope)
a = st.sidebar.slider(
    "True Slope (a)",
    min_value=-100.0,
    max_value=100.0,
    value=30.0,
    step=1.0,
    help="The slope parameter of the underlying linear relation."
)

# b (Intercept)
b = st.sidebar.slider(
    "True Intercept (b)",
    min_value=-200.0,
    max_value=500.0,
    value=100.0,
    step=5.0,
    help="The intercept parameter of the underlying linear relation."
)

# Noise Amplitude
noise_std = st.sidebar.slider(
    "Noise Scale (Standard Deviation)",
    min_value=0.0,
    max_value=100.0,
    value=10.0,
    step=1.0,
    help="The standard deviation of Gaussian noise added to the data points."
)

# Number of Outliers to show
max_outliers_possible = min(50, N)
num_outliers = st.sidebar.slider(
    "Number of Outliers to Highlight",
    min_value=0,
    max_value=max_outliers_possible,
    value=min(20, max_outliers_possible),
    step=1,
    help="Finds and highlights the points with the absolute largest residuals."
)

# ==============================================================================
# CRISP-DM 階段 3 & 4：資料產生與建模 (Data Generation & Modeling)
# ==============================================================================
# Generate linear data
x = np.random.uniform(0, 100, N)
noise = np.random.normal(0, 1, N)
y = a * x + b + noise_std * noise

# Fit Linear Regression Model
X_matrix = x.reshape(-1, 1)
model = LinearRegression()
model.fit(X_matrix, y)

# Predictions & Metrics
y_pred = model.predict(X_matrix)
fitted_a = model.coef_[0]
fitted_b = model.intercept_
r2 = r2_score(y, y_pred)
mse = mean_squared_error(y, y_pred)

# Detect outliers
residuals = np.abs(y - y_pred)
top_outliers_idx = np.argsort(residuals)[-num_outliers:][::-1] if num_outliers > 0 else []

# ==============================================================================
# Metric Cards
# ==============================================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label="Estimated Slope (â)",
        value=f"{fitted_a:.4f}",
        delta=f"Diff: {fitted_a - a:.4f}",
        delta_color="off"
    )
with col2:
    st.metric(
        label="Estimated Intercept (b̂)",
        value=f"{fitted_b:.4f}",
        delta=f"Diff: {fitted_b - b:.4f}",
        delta_color="off"
    )
with col3:
    st.metric(
        label="R² Score (Goodness of Fit)",
        value=f"{r2:.4f}"
    )
with col4:
    st.metric(
        label="Mean Squared Error (MSE)",
        value=f"{mse:.2f}"
    )

st.markdown("---")

# ==============================================================================
# Main Section: Visualization & Data Details
# ==============================================================================
tab1, tab2 = st.tabs(["📊 Visualization", "📋 Outliers & Source Data"])

with tab1:
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    
    # 1. Normal points in slate blue
    ax.scatter(x, y, color="#4f46e5", alpha=0.5, edgecolors='none', label="Normal Data")
    
    # 2. Regression line
    sort_idx = np.argsort(x)
    ax.plot(
        x[sort_idx],
        y_pred[sort_idx],
        color="#ef4444",
        linewidth=2.5,
        label="Fitted Regression Line"
    )
    
    # 3. Highlight outliers
    if len(top_outliers_idx) > 0:
        ax.scatter(
            x[top_outliers_idx],
            y[top_outliers_idx],
            color="#f97316",
            edgecolors="black",
            s=90,
            zorder=5,
            label=f"Top {num_outliers} Outliers"
        )
        
        # Label outliers on the plot
        for rank, idx in enumerate(top_outliers_idx):
            label_text = str(rank + 1)
            # Offset label positioning slightly depending on point location
            ax.text(
                x[idx] + 0.8,
                y[idx] + (noise_std * 0.15 if noise_std > 0 else 0.5),
                label_text,
                color="#c2410c",
                fontsize=9,
                weight="bold"
            )
            
    # Chart styling
    ax.set_title("Linear Regression & Residual Outliers Analysis", fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel("X (Independent Variable)", fontsize=10)
    ax.set_ylabel("Y (Dependent Variable)", fontsize=10)
    ax.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
    ax.grid(True, linestyle="--", alpha=0.5, color='#cbd5e1')
    
    # Border styling
    for spine in ax.spines.values():
        spine.set_color('#cbd5e1')
        
    st.pyplot(fig)

with tab2:
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("⚠️ Detected Outliers")
        if len(top_outliers_idx) > 0:
            outlier_data = pd.DataFrame({
                "Rank": range(1, len(top_outliers_idx) + 1),
                "Index": top_outliers_idx,
                "X": x[top_outliers_idx],
                "Actual Y": y[top_outliers_idx],
                "Predicted Y": y_pred[top_outliers_idx],
                "Absolute Residual": residuals[top_outliers_idx]
            }).set_index("Rank")
            
            st.dataframe(outlier_data.style.format({
                "X": "{:.2f}",
                "Actual Y": "{:.2f}",
                "Predicted Y": "{:.2f}",
                "Absolute Residual": "{:.2f}"
            }), use_container_width=True)
            
            # Download button for outliers
            csv_outliers = outlier_data.to_csv(index=True)
            st.download_button(
                label="📥 Download Outliers CSV",
                data=csv_outliers,
                file_name="detected_outliers.csv",
                mime="text/csv"
            )
        else:
            st.info("No outliers are currently highlighted.")
            
    with col_right:
        st.subheader("📁 Complete Generated Dataset")
        full_dataset = pd.DataFrame({
            "X": x,
            "Actual Y": y,
            "Predicted Y": y_pred,
            "Residual": residuals,
            "Is Outlier": [idx in top_outliers_idx for idx in range(N)]
        })
        
        st.dataframe(full_dataset.style.format({
            "X": "{:.2f}",
            "Actual Y": "{:.2f}",
            "Predicted Y": "{:.2f}",
            "Residual": "{:.2f}"
        }), use_container_width=True)
        
        # Download button for complete dataset
        csv_full = full_dataset.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Dataset CSV",
            data=csv_full,
            file_name="linear_regression_dataset.csv",
            mime="text/csv"
        )
