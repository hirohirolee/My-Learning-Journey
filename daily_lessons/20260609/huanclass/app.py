import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Set page config
st.set_page_config(
    page_title="新創公司利潤預測與經營決策 AI 平台",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium business analytics style
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .stAppHeader {
        background-color: transparent;
    }
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .metric-title {
        color: #64748b;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #0f172a;
        font-size: 28px;
        font-weight: 700;
    }
    .metric-value-rf {
        color: #10b981; /* Green */
        font-size: 28px;
        font-weight: 700;
    }
    .metric-value-lr {
        color: #3b82f6; /* Blue */
        font-size: 28px;
        font-weight: 700;
    }
    .section-title {
        color: #1e293b;
        font-size: 22px;
        font-weight: 700;
        border-left: 6px solid #1e3a8a;
        padding-left: 12px;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    .advice-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #f59e0b;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        margin-bottom: 15px;
    }
    .opt-card-current {
        background-color: #fef2f2;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #fee2e2;
        text-align: center;
    }
    .opt-card-best {
        background-color: #f0fdf4;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #dcfce7;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.title("🤖 新創公司利潤預測與決策最佳化 AI 平台")
st.markdown("本系統基於 **CRISP-DM** 流程，提供資料上傳、動態模型訓練、互動式視覺化分析以及**經營預算最佳化配置**的整合性決策工具。")

# ----------------------------------------------------
# DATA LOADING & DYNAMIC ML PIPELINE
# ----------------------------------------------------
@st.cache_data
def train_and_evaluate_pipeline(df):
    # 1. IQR Outlier detection on Profit
    Q1 = df['Profit'].quantile(0.25)
    Q3 = df['Profit'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df['Profit'] < lower_bound) | (df['Profit'] > upper_bound)]
    df_clean = df.drop(outliers.index).reset_index(drop=True)
    
    # 2. One-hot encode State column
    df_encoded = pd.get_dummies(df_clean, columns=['State'], drop_first=True, dtype=int)
    
    # Ensure standard dummy columns are present even if custom data has fewer states
    if 'State_Florida' not in df_encoded.columns:
        df_encoded['State_Florida'] = 0
    if 'State_New York' not in df_encoded.columns:
        df_encoded['State_New York'] = 0
        
    X = df_encoded.drop('Profit', axis=1)
    y = df_encoded['Profit']
    
    # Keep columns aligned to baseline
    features_list = ['R&D Spend', 'Administration', 'Marketing Spend', 'State_Florida', 'State_New York']
    X = X[features_list]
    
    # 3. Train-test split (80% / 20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Standard scale numerical spend features
    num_cols = ['R&D Spend', 'Administration', 'Marketing Spend']
    scaler = StandardScaler()
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    
    X_train_scaled[num_cols] = scaler.fit_transform(X_train[num_cols])
    X_test_scaled[num_cols] = scaler.transform(X_test[num_cols])
    
    # 5. Train 5 models for comparison
    models = {
        "多元線性迴歸 (Linear Regression)": LinearRegression(),
        "脊迴歸 (Ridge Regression)": Ridge(alpha=1.0),
        "支持向量迴歸 (SVR)": SVR(C=100000, epsilon=10.0),
        "隨機森林迴歸 (Random Forest)": RandomForestRegressor(n_estimators=100, random_state=42),
        "梯度提升迴歸 (Gradient Boosting)": GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    
    trained_models = {}
    metrics = {}
    test_predictions = {}
    
    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        trained_models[name] = model
        metrics[name] = {"R2": r2, "MAE": mae, "RMSE": rmse}
        test_predictions[name] = y_pred
        
    return scaler, trained_models, metrics, X_train, X_test, y_train, y_test, test_predictions, outliers, df_clean

# Sidebar: CSV File Uploader
st.sidebar.header("📁 資料庫設定")
uploaded_file = st.sidebar.file_uploader("上傳您的自訂新創 CSV 資料集", type="csv")

if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
        # Check required columns
        req_cols = {'R&D Spend', 'Administration', 'Marketing Spend', 'State', 'Profit'}
        if not req_cols.issubset(raw_df.columns):
            st.sidebar.error("❌ CSV 欄位不符！必須包含：R&D Spend, Administration, Marketing Spend, State, Profit")
            df_source = pd.read_csv('50_Startups.csv')
            dataset_name = "預設 50_Startups.csv 資料集"
        else:
            df_source = raw_df
            dataset_name = f"已上傳資料集 ({uploaded_file.name})"
    except Exception as e:
        st.sidebar.error(f"❌ 載入失敗: {e}")
        df_source = pd.read_csv('50_Startups.csv')
        dataset_name = "預設 50_Startups.csv 資料集"
else:
    df_source = pd.read_csv('50_Startups.csv')
    dataset_name = "預設 50_Startups.csv 資料集"

st.sidebar.success(f"📊 使用中資料集：{dataset_name}")

# Run ML Pipeline dynamically
scaler, trained_models, metrics, X_train, X_test, y_train, y_test, test_predictions, outliers, df_clean = train_and_evaluate_pipeline(df_source)

# ----------------------------------------------------
# DYNAMIC STEPWISE FEATURE SELECTION METRICS
# ----------------------------------------------------
@st.cache_data
def get_stepwise_metrics(X_train, X_test, y_train, y_test, num_cols, _scaler):
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    X_train_scaled[num_cols] = _scaler.transform(X_train[num_cols])
    X_test_scaled[num_cols] = _scaler.transform(X_test[num_cols])
    
    features = list(X_train.columns)
    selected = []
    steps = []
    remaining = list(features)
    
    for step in range(1, len(features) + 1):
        best_r2 = -np.inf
        best_feature = None
        best_rmse = None
        
        for f in remaining:
            candidate_features = selected + [f]
            lr = LinearRegression()
            lr.fit(X_train_scaled[candidate_features], y_train)
            preds = lr.predict(X_test_scaled[candidate_features])
            
            r2 = r2_score(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            
            if r2 > best_r2:
                best_r2 = r2
                best_feature = f
                best_rmse = rmse
                
        selected.append(best_feature)
        remaining.remove(best_feature)
        
        label_mapping = {
            'R&D Spend': '研發投入 (R&D Spend)',
            'Marketing Spend': '行銷推廣 (Marketing Spend)',
            'Administration': '行政管理 (Administration)',
            'State_Florida': '落腳佛州 (State_Florida)',
            'State_New York': '落腳紐約州 (State_New York)'
        }
        selected_labels = [label_mapping.get(x, x) for x in selected]
        
        steps.append({
            '特徵數量': step,
            '選入特徵組合': " + ".join(selected_labels),
            'RMSE (均方根誤差)': best_rmse,
            'R-squared (解釋力)': best_r2
        })
        
    return pd.DataFrame(steps)

num_cols_to_scale = ['R&D Spend', 'Administration', 'Marketing Spend']
step_df = get_stepwise_metrics(X_train, X_test, y_train, y_test, num_cols_to_scale, scaler)

# Sidebar: Interactive Simulator Inputs
st.sidebar.header("⚙️ 營運預算模擬配置")
rd_input = st.sidebar.number_input("1. 研發費用 (R&D Spend) - 美元", min_value=0.0, max_value=500000.0, value=100000.0, step=5000.0)
mkt_input = st.sidebar.number_input("2. 行銷推廣 (Marketing Spend) - 美元", min_value=0.0, max_value=500000.0, value=150000.0, step=5000.0)
admin_input = st.sidebar.number_input("3. 行政管理 (Administration) - 美元", min_value=0.0, max_value=300000.0, value=80000.0, step=5000.0)
state_input = st.sidebar.selectbox("4. 公司落腳州別 (State)", ["加州 (California)", "佛羅里達州 (Florida)", "紐約州 (New York)"])

state_mapping = {
    "加州 (California)": "california",
    "佛羅里達州 (Florida)": "florida",
    "紐約州 (New York)": "new york"
}
selected_state = state_mapping[state_input]

# ----------------------------------------------------
# MAIN DASHBOARD TABS
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 利潤預測模擬", 
    "🎯 預算分配最佳化推薦", 
    "📊 互動式視覺化分析", 
    "🏆 模型競技場 & 商業洞察"
])

# Identify Best Model based on R2 Score
best_model_name = max(metrics, key=lambda k: metrics[k]["R2"])
best_model = trained_models[best_model_name]

# Prepare prediction inputs
state_florida = 1 if selected_state == "florida" else 0
state_newyork = 1 if selected_state == "new york" else 0
input_df = pd.DataFrame([{
    'R&D Spend': rd_input,
    'Administration': admin_input,
    'Marketing Spend': mkt_input,
    'State_Florida': state_florida,
    'State_New York': state_newyork
}])
num_cols = ['R&D Spend', 'Administration', 'Marketing Spend']
input_scaled = input_df.copy()
input_scaled[num_cols] = scaler.transform(input_df[num_cols])

# Predict
pred_best = best_model.predict(input_scaled)[0]
pred_lr = trained_models["多元線性迴歸 (Linear Regression)"].predict(input_scaled)[0]

# --- TAB 1: PREDICTION SIMULATOR ---
with tab1:
    st.markdown('<div class="section-title">🔮 即時利潤預測</div>', unsafe_allow_html=True)
    st.write(f"模型已為 **{dataset_name}** 動態訓練完成。以下為您配置的預算在兩款模型下的預估年利潤：")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🌲 最佳模型：{best_model_name}</div>
            <div class="metric-value-rf">${pred_best:,.2f}</div>
            <p style="color: #64748b; font-size: 12px; margin-top: 8px;">模型測試集解釋能力 (R²): {metrics[best_model_name]['R2']*100:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 基準模型：多元線性迴歸 (Linear Regression)</div>
            <div class="metric-value-lr">${pred_lr:,.2f}</div>
            <p style="color: #64748b; font-size: 12px; margin-top: 8px;">模型測試集平均誤差 (MAE): ${metrics['多元線性迴歸 (Linear Regression)']['MAE']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('<div class="section-title">💡 預算配置動態健康診斷</div>', unsafe_allow_html=True)
    total_budget = rd_input + mkt_input + admin_input
    if total_budget > 0:
        rd_ratio = (rd_input / total_budget) * 100
        admin_ratio = (admin_input / total_budget) * 100
        
        st.write(f"您設定的總營運預算為：**\${total_budget:,.2f}**")
        
        # Progress bar
        col_pb1, col_pb2 = st.columns([1, 4])
        with col_pb1:
            st.write(f"研發費用佔比: **{rd_ratio:.1f}%**")
        with col_pb2:
            st.progress(min(rd_input / total_budget, 1.0))
            
        if rd_ratio >= 50:
            st.success("🎯 **健康配置（研發領軍）**：您的研發預算佔比超過一半！研發是推動獲利的第一核心引擎，此配置利於建立技術壁壘。")
        elif rd_ratio >= 20:
            st.warning("⚠️ **配置偏保守**：研發佔比較低。因為研發的回報率最高，若能將部分行銷或行政開銷挪至研發，將能顯著拉抬預期利潤。")
        else:
            st.error("🚨 **極高風險配置**：研發投入過低！這極易導致產品在市場上失去競爭力，落入「無技術、重負擔」的困境。")
            
        if admin_ratio > 30:
            st.error(f"📉 **行政負載警告**：行政成本佔比達 **{admin_ratio:.1f}%**！數據顯示行政管理是負向效應（純成本），應盡量精簡組織開支。")
    else:
        st.info("請在左側配置非零的預算金額以啟動健康診斷。")

# --- TAB 2: BUDGET OPTIMIZATION ---
with tab2:
    st.markdown('<div class="section-title">🎯 預算黃金配置最佳化推薦</div>', unsafe_allow_html=True)
    st.write("輸入您的總預算，AI 將自動基於模型算法，在滿足基本業務營運的約束條件下，尋找能**創造最大利潤**的預算分配比例。")
    
    col_opt1, col_opt2 = st.columns([2, 3])
    
    with col_opt1:
        st.subheader("⚙️ 最佳化約束條件設定")
        opt_budget = st.number_input("規劃總預算 (美元)", min_value=10000.0, max_value=1000000.0, value=300000.0, step=10000.0)
        
        # User sets bounds
        min_admin_pct = st.slider("最低行政佔比保障 (%)", min_value=5, max_value=30, value=10, help="考量基本行政辦公、財務與法規成本，公司必須保留的最低行政佔比。")
        min_mkt_pct = st.slider("最低行銷投入保障 (%)", min_value=5, max_value=40, value=10, help="考量基本市場曝光，公司必須保留的最低行銷佔比。")
        
        st.markdown("---")
        st.markdown("💡 **AI 最佳化原理**：系統利用網格搜尋法，在您的約束條件內（行政 $\ge$ 設定值，行銷 $\ge$ 設定值，且研發 $\ge 10\%$），使用表現最好的隨機森林模型評估數千種配置，找出預測利潤最高的黃金解。")
        
    with col_opt2:
        # Optimization Grid Search (Vectorized for high performance)
        best_opt_val = -np.inf
        best_allocation = None
        
        min_ad_r = min_admin_pct / 100.0
        min_mk_r = min_mkt_pct / 100.0
        
        # Pre-generate ratio combinations
        ad_ratios = np.arange(min_ad_r, 0.401, 0.01)
        mk_ratios = np.arange(min_mk_r, 0.601, 0.01)
        
        ratio_combinations = []
        for r_ad in ad_ratios:
            for r_mk in mk_ratios:
                r_rd = 1.0 - r_ad - r_mk
                if r_rd >= 0.1:
                    ratio_combinations.append((r_rd, r_mk, r_ad))
                    
        if len(ratio_combinations) > 0:
            ratio_combinations = np.array(ratio_combinations)
            opt_rds = ratio_combinations[:, 0] * opt_budget
            opt_mks = ratio_combinations[:, 1] * opt_budget
            opt_ads = ratio_combinations[:, 2] * opt_budget
            
            # Construct a single large dataframe for batch processing
            opt_df_all = pd.DataFrame({
                'R&D Spend': opt_rds,
                'Administration': opt_ads,
                'Marketing Spend': opt_mks,
                'State_Florida': state_florida,
                'State_New York': state_newyork
            })
            
            # Reorder columns to match features
            features_list = ['R&D Spend', 'Administration', 'Marketing Spend', 'State_Florida', 'State_New York']
            opt_df_all = opt_df_all[features_list]
            
            # Scale all combinations at once
            opt_scaled_all = opt_df_all.copy()
            opt_scaled_all[num_cols] = scaler.transform(opt_df_all[num_cols])
            
            # Batch predict
            all_preds = best_model.predict(opt_scaled_all)
            
            # Find the best
            best_idx = np.argmax(all_preds)
            best_opt_val = all_preds[best_idx]
            best_allocation = (opt_rds[best_idx], opt_mks[best_idx], opt_ads[best_idx], 
                               ratio_combinations[best_idx, 0], ratio_combinations[best_idx, 1], ratio_combinations[best_idx, 2])
                    
        if best_allocation is not None:
            opt_rd, opt_mk, opt_ad, r_rd, r_mk, r_ad = best_allocation
            
            st.subheader("🏆 AI 推薦黃金分配結果")
            
            # Predict current selection with opt_budget to show improvement
            # Let's assume current user ratio in sidebar is used
            current_total = rd_input + mkt_input + admin_input
            if current_total > 0:
                curr_rd_r = rd_input / current_total
                curr_mk_r = mkt_input / current_total
                curr_ad_r = admin_input / current_total
            else:
                curr_rd_r, curr_mk_r, curr_ad_r = 0.33, 0.33, 0.33
                
            # Current predicted profit scaled to opt_budget
            curr_rd = curr_rd_r * opt_budget
            curr_mk = curr_mk_r * opt_budget
            curr_ad = curr_ad_r * opt_budget
            
            curr_test_df = pd.DataFrame([{
                'R&D Spend': curr_rd,
                'Administration': curr_ad,
                'Marketing Spend': curr_mk,
                'State_Florida': state_florida,
                'State_New York': state_newyork
            }])
            curr_test_scaled = curr_test_df.copy()
            curr_test_scaled[num_cols] = scaler.transform(curr_test_df[num_cols])
            curr_pred_profit = best_model.predict(curr_test_scaled)[0]
            
            # Show comparison cards
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown(f"""
                <div class="opt-card-current">
                    <div style="color: #ef4444; font-size: 13px; font-weight: 600;">❌ 照目前比例分配 (預算 ${opt_budget:,.0f})</div>
                    <div style="font-size: 22px; font-weight: 700; color: #7f1d1d; margin-top: 5px;">${curr_pred_profit:,.2f}</div>
                    <p style="font-size: 11px; color: #991b1b; margin-top: 5px;">研發 {curr_rd_r*100:.1f}% | 行銷 {curr_mk_r*100:.1f}% | 行政 {curr_ad_r*100:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            with col_c2:
                profit_diff = best_opt_val - curr_pred_profit
                pct_inc = (profit_diff / max(curr_pred_profit, 1)) * 100
                st.markdown(f"""
                <div class="opt-card-best">
                    <div style="color: #22c55e; font-size: 13px; font-weight: 600;">✨ AI 黃金分配預測利潤 (最佳配置)</div>
                    <div style="font-size: 22px; font-weight: 700; color: #14532d; margin-top: 5px;">${best_opt_val:,.2f}</div>
                    <p style="font-size: 11px; color: #166534; font-weight: 600; margin-top: 5px;">預期利潤提升: +${profit_diff:,.2f} ({pct_inc:+.1f}%)</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Plotly Pie Chart
            pie_df = pd.DataFrame({
                '配置項目': ['研發預算 (R&D)', '行銷預算 (Marketing)', '行政預算 (Administration)'],
                '分配金額': [opt_rd, opt_mk, opt_ad]
            })
            fig_pie = px.pie(
                pie_df, 
                values='分配金額', 
                names='配置項目', 
                color_discrete_sequence=['#1e3b8a', '#0d9488', '#f59e0b'],
                hole=0.4
            )
            fig_pie.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 3: INTERACTIVE VISUALIZATIONS ---
with tab3:
    st.markdown('<div class="section-title">📊 互動式數據視覺化分析 (Plotly)</div>', unsafe_allow_html=True)
    st.write("所有圖表均為動態生成，支援滑鼠懸停看數據、拉近放大及雙擊重設。")
    
    col_vis1, col_vis2 = st.columns(2)
    
    with col_vis1:
        # Plot 1: Heatmap
        corr = df_clean[['R&D Spend', 'Administration', 'Marketing Spend', 'Profit']].corr()
        fig_heat = px.imshow(
            corr,
            text_auto=".3f",
            color_continuous_scale='RdBu_r',
            zmin=-1, zmax=1,
            title="① 數值型欄位相關性互動熱力圖"
        )
        fig_heat.update_layout(height=400)
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption("解讀：相關度越接近 1.000 代表正相關越強。可見研發支出 (0.973) 與行銷支出 (0.748) 是利潤的強相關特徵。")
        
    with col_vis2:
        # Plot 2: Actual vs Predicted
        pred_df = pd.DataFrame({
            '真實利潤': y_test.values,
            '預估利潤': test_predictions[best_model_name],
            '研發投入': X_test['R&D Spend'].values,
            '行銷推廣': X_test['Marketing Spend'].values,
            '行政管理': X_test['Administration'].values
        })
        
        fig_scatter = px.scatter(
            pred_df,
            x='真實利潤',
            y='預估利潤',
            hover_data=['研發投入', '行銷推廣', '行政管理'],
            title=f"② 預估利潤 vs 真實利潤散佈圖 ({best_model_name})"
        )
        # Add 45 degree line
        min_v = min(y_test.min(), test_predictions[best_model_name].min()) * 0.95
        max_v = max(y_test.max(), test_predictions[best_model_name].max()) * 1.05
        fig_scatter.add_shape(
            type="line", x0=min_v, y0=min_v, x1=max_v, y1=max_v,
            line=dict(color="Red", dash="dash", width=2)
        )
        # Add the current simulated startup point to the plot dynamically
        fig_scatter.add_trace(go.Scatter(
            x=[pred_best], # Lies on the diagonal line (Actual = Predicted)
            y=[pred_best],
            mode='markers+text',
            marker=dict(symbol='star', size=17, color='#f59e0b', line=dict(color='black', width=1.5)),
            name='👈 您當前設定的模擬公司',
            text=['您當前的模擬預估點'],
            textposition='top center',
            hovertemplate=(
                f"<b>您的模擬公司預估點</b><br>"
                f"預估利潤: ${pred_best:,.2f}<br>"
                f"研發投入: ${rd_input:,.2f}<br>"
                f"行銷費用: ${mkt_input:,.2f}<br>"
                f"行政管理: ${admin_input:,.2f}<extra></extra>"
            )
        ))
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("解讀：虛線代表完美預測基準線。藍點越靠近紅虛線，代表模型的預估精準度越高。")
        
    st.markdown("---")
    
    col_vis3, col_vis4 = st.columns(2)
    
    with col_vis3:
        # Plot 3: Feature Importances
        if hasattr(best_model, 'feature_importances_'):
            importances = best_model.feature_importances_
            labels = {
                'R&D Spend': '研發投入 (R&D)',
                'Marketing Spend': '行銷推廣 (Marketing)',
                'Administration': '行政管理 (Admin)',
                'State_Florida': '落腳佛州 (Florida)',
                'State_New York': '落腳紐約州 (New York)'
            }
            imp_df = pd.DataFrame({
                '項目': [labels[c] for c in X_train.columns],
                '決定權重': importances
            }).sort_values(by='決定權重', ascending=True)
            
            fig_imp = px.bar(
                imp_df,
                x='決定權重',
                y='項目',
                orientation='h',
                color='決定權重',
                color_continuous_scale='Viridis',
                text_auto='.1%',
                title="③ 利潤決定因子權重排行 (隨機森林)"
            )
            fig_imp.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_imp, use_container_width=True)
            st.caption("解讀：長條占比越大，代表該項支出在分割決策樹時對預測利潤的影響力越大。")
        else:
            st.info("當前最佳模型不支援特徵重要性評估（例如 SVR）。")
            
    with col_vis4:
        # Plot 4: Boxplot of clean data
        fig_box = px.box(
            df_clean,
            x='State',
            y='Profit',
            color='State',
            points="all",
            title="④ 各地區利潤分布箱型圖 (已清洗極端值)"
        )
        # Add horizontal dashed line for user's predicted profit
        fig_box.add_hline(
            y=pred_best, 
            line_dash="dash", 
            line_color="#f59e0b", 
            line_width=2.5,
            annotation_text=f"👈 您的模擬公司預估利潤: ${pred_best:,.2f}", 
            annotation_position="top right"
        )
        fig_box.update_layout(height=350)
        st.plotly_chart(fig_box, use_container_width=True)
        st.caption("解讀：中線代表各地區獲利中位數，圓點代表各公司真實位置。可看出各地區獲利分布區間高度重疊。")
        
    # --- NEW SECTION: STEPWISE FEATURE SELECTION ---
    st.markdown('<div class="section-title">🔍 特徵逐步篩選與模型效能分析 (Stepwise Feature Selection)</div>', unsafe_allow_html=True)
    st.write("以下呈現逐步將特徵（研發、行銷、行政支出、地區）加入線性模型後，模型在測試集上的效能變化。您可以藉此判斷哪些特徵組合能帶來最佳預測效果。")
    
    col_step1, col_step2 = st.columns(2)
    
    with col_step1:
        # Plot 5: RMSE by Number of Features
        fig_step_rmse = px.line(
            step_df,
            x='特徵數量',
            y='RMSE (均方根誤差)',
            markers=True,
            title="⑤ 隨特徵數量增加的 RMSE 變化 (越低越好)"
        )
        # Highlight best point (lowest RMSE)
        opt_rmse_idx = step_df['RMSE (均方根誤差)'].idxmin()
        fig_step_rmse.add_trace(go.Scatter(
            x=[step_df.loc[opt_rmse_idx, '特徵數量']],
            y=[step_df.loc[opt_rmse_idx, 'RMSE (均方根誤差)']],
            mode='markers',
            marker=dict(color='#ef4444', size=12, symbol='star', line=dict(color='black', width=1)),
            name='最佳特徵數量點'
        ))
        fig_step_rmse.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_step_rmse, use_container_width=True)
        st.caption("解讀：均方根誤差 (RMSE) 代表預測值偏離實際值的標準差。轉折最低點代表在當前特徵數量下，模型預測偏誤最小。")
        
    with col_step2:
        # Plot 6: R-squared by Number of Features
        fig_step_r2 = px.line(
            step_df,
            x='特徵數量',
            y='R-squared (解釋力)',
            markers=True,
            title="⑥ 隨特徵數量增加的 R-squared 變化 (越高越好)"
        )
        # Highlight best point (highest R2)
        opt_r2_idx = step_df['R-squared (解釋力)'].idxmax()
        fig_step_r2.add_trace(go.Scatter(
            x=[step_df.loc[opt_r2_idx, '特徵數量']],
            y=[step_df.loc[opt_r2_idx, 'R-squared (解釋力)']],
            mode='markers',
            marker=dict(color='#22c55e', size=12, symbol='star', line=dict(color='black', width=1)),
            name='最佳特徵數量點'
        ))
        fig_step_r2.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_step_r2, use_container_width=True)
        st.caption("解讀：決定係數 (R-squared) 代表模型可解釋的資料變異比例。最高點代表該特徵組合對利潤的預測解釋能力最強。")
        
    st.write("**逐步特徵篩選評估詳表：**")
    st.dataframe(
        step_df.style.format({
            'RMSE (均方根誤差)': '${:,.2f}',
            'R-squared (解釋力)': '{:.4%}'
        }).highlight_min(axis=0, subset=['RMSE (均方根誤差)'], color='#dcfce7')
          .highlight_max(axis=0, subset=['R-squared (解釋力)'], color='#dcfce7'),
        use_container_width=True
    )
    st.info("💡 **決策啟示**：從表中可以觀察到，當特徵數量為 **2 個**（選入『研發支出』與『行銷支出』）時，RMSE 達到最低點，而 R-squared 達到最高點，為模型最優解。隨後加入『地區』與『行政管理』時，模型表現反而下降，這印證了多餘的噪音特徵會干擾預測效能的規律。")

# --- TAB 4: LEADERBOARD & INSIGHTS ---
with tab4:
    st.markdown('<div class="section-title">🏆 機器學習模型競技場 (Leaderboard)</div>', unsafe_allow_html=True)
    st.write("我們在後台同步訓練了 5 個常用迴調模型，並使用獨立的測試集進行客觀評量：")
    
    # Render leaderboard dataframe
    lead_df = pd.DataFrame.from_dict(metrics, orient='index')
    lead_df.columns = ['R-squared (解釋能力)', 'MAE (平均絕對誤差)', 'RMSE (均方根誤差)']
    lead_df = lead_df.sort_values(by='R-squared (解釋能力)', ascending=False)
    
    # Styled table
    st.dataframe(
        lead_df.style.format({
            'R-squared (解釋能力)': '{:.2%}',
            'MAE (平均絕對誤差)': '${:,.2f}',
            'RMSE (均方根誤差)': '${:,.2f}'
        }).highlight_max(axis=0, subset=['R-squared (解釋能力)'], color='#dcfce7')
          .highlight_min(axis=0, subset=['MAE (平均絕對誤差)', 'RMSE (均方根誤差)'], color='#dcfce7'),
        use_container_width=True
    )
    
    # Outlier log
    st.markdown('<div class="section-title">⚠️ 數據清洗日誌</div>', unsafe_allow_html=True)
    if len(outliers) > 0:
        st.error(f"🚨 **IQR 檢驗已剔除 {len(outliers)} 筆利潤極端值數據**：")
        st.write(outliers)
        st.info("商業警示：這些極端值多為「高行政開銷、零研發投資且極低獲利」的企業，剔除能防範多元線性迴歸線偏斜。")
    else:
        st.success("✅ 數據集非常乾淨，經 IQR 檢驗無顯著的 Profit 極端值偏離點。")
        
    st.markdown('<div class="section-title">💼 決策顧問黃金指引卡</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="advice-card">
        <h4>💡 研發為本 (R&D First)</h4>
        <p>資料集在大數據分析下揭示：研發支出與利潤的相關度高達 <b>97.3%</b>。在線性模型中，每投入 $1.00 研發費用可帶回近 <b>$0.81</b> 的利潤回報。產品力是新創存活的核心根基。</p>
    </div>
    <div class="advice-card" style="border-left-color: #3b82f6;">
        <h4>📍 地址去中心化選址</h4>
        <p>地區變數在所有機器學習拆分樹中，影響力權重均低於 <b>0.2%</b>。加州、紐約州和佛羅里達州本身的區位優勢並不能直接提升獲利。選址應以<b>免稅政策、補貼或租金廉價度</b>為第一考量。</p>
    </div>
    <div class="advice-card" style="border-left-color: #ef4444;">
        <h4>🚨 嚴防行政黑洞 (Overhead)</h4>
        <p>行政支出在多元線性迴歸中係數為負（每多 $1 倒扣 $0.07），且重要性極低（低於 1.0%）。這提醒經營者：避免過早建立臃腫的後勤團隊，草創期應實行精實管理。</p>
    </div>
    """, unsafe_allow_html=True)
