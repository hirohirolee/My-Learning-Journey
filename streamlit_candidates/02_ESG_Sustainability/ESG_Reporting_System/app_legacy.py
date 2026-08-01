import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# 1. 網頁基本設定
st.set_page_config(page_title="ESG 重大性矩陣分析工具", layout="wide")

st.title("🍀 00股份有限公司 永續重大議題矩陣工具")
st.caption("透過左側控制面板調整重大性門檻，圖表與數據表將會即時動態連動更新。")

# =====================================================================
# 2. 側邊欄控制面板 (Sidebar)
# =====================================================================
st.sidebar.header("🛠️ 矩陣門檻設定")
st.sidebar.markdown("請設定「兩項分數相乘（滿分100分）」的切分門檻：")

# 讓使用者調整低度重大與高度重大的門檻
low_limit = st.sidebar.slider(
    "🟢 低度重大門檻 (中低優先分界點)",
    min_value=0,
    max_value=100,
    value=20,
    step=1,
)

high_limit = st.sidebar.slider(
    "🟣 高度重大門檻 (中高優先分界點)",
    min_value=0,
    max_value=100,
    value=60,
    step=1,
)

# 限制條件：高度門檻必須大於低度門檻
if high_limit <= low_limit:
    st.sidebar.warning("⚠️ 高度門檻必須大於低度門檻！系統已自動將高度門檻調整為低度門檻 + 1。")
    high_limit = low_limit + 1
    if high_limit > 100:
        high_limit = 100
        low_limit = 99

st.sidebar.write("---")
st.sidebar.markdown(
    f"""
**目前的分區邏輯：**
* 兩項分數相乘 `< {low_limit}` ➡️ **🟢 低度重大**
* 兩項分數相乘 `介於 {low_limit} 與 {high_limit} 之間` ➡️ **🟡 中度重大**
* 兩項分數相乘 `>= {high_limit}` ➡️ **🟣 高度重大**
"""
)

axis_min = st.sidebar.selectbox(
    "🔍 圖表縮放起點 (軸線最小值)",
    options=[0, 3, 4, 5],
    index=2,
    help="調整 X/Y 軸的起點以分散高分區的資料點，使其更容易閱讀。"
)

# =====================================================================
# 3. 原始數據統整
# =====================================================================
data = {
    "面向": [
        "1.經濟面", "1.經濟面", "1.經濟面", "1.經濟面", "1.經濟面", "1.經濟面", "1.經濟面",
        "2.環境面", "2.環境面", "2.環境面", "2.環境面", "2.環境面", "2.環境面", "2.環境面", "2.環境面",
        "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面", "3.社會面"
    ],
    "重大議題": [
        "聚焦經濟價值的產生與分配 (GRI 201)",
        "優先雇用在地管理人員 (GRI 202)",
        "加大在地社區基礎設施的投資 (GRI 203)",
        "支持在地採購 (GRI 204)",
        "實施反貪腐措施 (GRI 205)",
        "避免不公平競爭 (GRI 206)",
        "完善稅務管理 (GRI 207)",
        "使用環保原物料 (GRI 301)",
        "生物多樣性政策 (GRI 101)",
        "節約能源 (GRI 302)",
        "提升水資源的利用 (GRI 303)",
        "建構生物多樣性環境 (GRI 304)",
        "注重溫室氣體排放與管理 (GRI 305)",
        "妥善處理廢棄物 (GRI 306)",
        "以環境標準篩選供應商 (GRI 308)",
        "優化員工福利 (GRI 401)",
        "促進和諧的勞資關係 (GRI 402)",
        "落實職業安全衛生制度 (GRI 403)",
        "推動員工教育訓練與職涯發展 (GRI 404)",
        "實踐員工多元化與平等機會 (GRI 405)",
        "建構不歧視的工作場域 (GRI 406)",
        "保障員工結社自由及團體協商 (GRI 407)",
        "堅守禁用童工政策 (GRI 408)",
        "禁止強迫勞動相關措施 (GRI 409)",
        "實施保全人員的人權訓練 (GRI 410)",
        "保護原住民權利 (GRI 411)",
        "友善當地社區 (GRI 413)",
        "導入供應商社會評估 (GRI 414)",
        "堅守公共政策分際 (GRI 415)",
        "確保顧客健康與安全 (GRI 416)",
        "遵循產品資訊與標示規範 (GRI 417)",
        "維護顧客隱私 (GRI 418)"
    ],
    "營運影響度": [
        8.0, 5.0, 6.0, 7.0, 9.0, 7.5, 8.5,
        6.5, 5.5, 8.0, 7.5, 5.0, 9.0, 8.5, 7.0,
        8.8, 8.0, 9.2, 8.5, 7.5, 8.0, 6.0, 9.5, 9.5, 5.0, 4.5, 7.0, 7.5, 6.0, 9.0, 8.0, 9.5
    ],
    "關心度": [
        8.5, 5.5, 6.0, 6.5, 9.0, 7.0, 8.0,
        7.0, 5.0, 8.5, 8.0, 4.5, 9.2, 8.0, 6.8,
        9.0, 8.2, 9.5, 8.0, 7.8, 8.0, 6.5, 9.0, 9.0, 5.5, 5.0, 7.2, 7.0, 5.5, 9.2, 8.0, 9.6
    ]
}
init_df = pd.DataFrame(data)

color_map = {
    "1.經濟面": "#1f77b4",  # 藍
    "2.環境面": "#2ca02c",  # 綠
    "3.社會面": "#ff7f0e",  # 橘
}

# =====================================================================
# 4. 寬版優化佈局 (Responsive Split Layout)
# =====================================================================
col_chart, col_editor = st.columns([1.8, 1.2])

with col_chart:
    st.subheader("📊 永續重大性矩陣視覺化圖表")
    
    # 建立 Plotly 互動式圖表
    fig = go.Figure()

    # 5. 繪製背景分區 (低、中、高)
    x_grid = np.linspace(0, 10, 200)
    y_grid = np.linspace(0, 10, 200)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = X * Y

    # 平滑轉換 Z 以適配 go.Contour 的區間劃分
    l1 = max(low_limit, 0.01)
    l2 = max(high_limit, l1 + 0.01)
    
    conds = [Z < l1, (Z >= l1) & (Z < l2), Z >= l2]
    v1 = Z / l1
    v2 = 1.0 + (Z - l1) / (l2 - l1)
    v3 = 2.0 + (Z - l2) / (100.0 - l2) if l2 < 100.0 else np.full_like(Z, 3.0)
    Z_transformed = np.select(conds, [v1, v2, v3])

    # 加入雙曲線背景等高線圖
    fig.add_trace(go.Contour(
        x=x_grid,
        y=y_grid,
        z=Z_transformed,
        showscale=False,
        zmin=0.0,
        zmax=3.0,
        contours=dict(
            coloring='heatmap',
            showlines=True,
            type='levels',
            start=1.0,
            end=2.0,
            size=1.0,
        ),
        line=dict(
            width=1.5,
            color='rgba(156, 163, 175, 0.35)'
        ),
        colorscale=[
            [0.0, "rgba(243, 244, 246, 0.6)"],
            [0.333, "rgba(243, 244, 246, 0.6)"],
            [0.333, "rgba(254, 243, 199, 0.6)"],
            [0.666, "rgba(244, 243, 199, 0.6)"],
            [0.666, "rgba(235, 213, 252, 0.6)"],
            [1.0, "rgba(235, 213, 252, 0.6)"]
        ],
        hoverinfo="skip"
    ))

    # 背景區域文字標籤
    low_diag = np.sqrt(low_limit)
    high_diag = np.sqrt(high_limit)

    x_low = y_low = (axis_min + low_diag) / 2.0 if low_diag > axis_min else (axis_min + 0.2)
    x_med = y_med = (max(axis_min, low_diag) + high_diag) / 2.0
    x_high = y_high = (max(axis_min, high_diag) + 10.0) / 2.0

    fig.add_annotation(x=x_low, y=y_low, text="<b>低度重大</b>", showarrow=False, font=dict(size=14, color="#4b5563"))
    fig.add_annotation(x=x_med, y=y_med, text="<b>中度重大</b>", showarrow=False, font=dict(size=14, color="#b45309"))
    fig.add_annotation(x=x_high, y=y_high, text="<b>高度重大</b>", showarrow=False, font=dict(size=14, color="#6d28d9"))

    # 資料與圖表連動處理 (先預準備有效資料)
    # 我們讓右側編輯器資料先讀取後再回傳繪製
    valid_df = init_df.copy()

with col_editor:
    st.subheader("📝 議題數據編輯器")
    st.caption("💡 雙擊儲存格可修改數據。按下方 **`+ Add row`** 或選列按 Del 可增減議題。")
    edited_df = st.data_editor(
        init_df,
        num_rows="dynamic",
        use_container_width=True,
        height=320,
        column_config={
            "面向": st.column_config.SelectboxColumn("面向", options=["1.經濟面", "2.環境面", "3.社會面"], required=True, width="small"),
            "重大議題": st.column_config.TextColumn("重大議題", required=True, width="medium"),
            "營運影響度": st.column_config.NumberColumn("營運影響度", min_value=0.0, max_value=10.0, step=0.1, required=True, width="small"),
            "關心度": st.column_config.NumberColumn("關心度", min_value=0.0, max_value=10.0, step=0.1, required=True, width="small"),
        }
    )

    valid_df = edited_df.dropna(subset=["面向", "重大議題", "營運影響度", "關心度"]).copy()
    if not valid_df.empty:
        valid_df["編號"] = range(1, len(valid_df) + 1)
        valid_df["重大主題指標"] = valid_df["營運影響度"] * valid_df["關心度"]
        
        def get_level(row):
            score = row["重大主題指標"]
            if score < low_limit:
                return "🟢 低度重大"
            elif score < high_limit:
                return "🟡 中度重大"
            else:
                return "🟣 高度重大"
        
        valid_df["重大性等級"] = valid_df.apply(get_level, axis=1)

# 回填繪製資料點至 Plotly 圖表 (確保編輯後即時連動)
with col_chart:
    if not valid_df.empty:
        valid_df["Color"] = valid_df["面向"].map(color_map).fillna("#757575")
        
        for name, group in valid_df.groupby("面向"):
            fig.add_trace(go.Scatter(
                x=group["營運影響度"],
                y=group["關心度"],
                mode="markers+text",
                name=name,
                marker=dict(size=13, color=color_map.get(name, "#757575"), line=dict(width=1.5, color='white')),
                text=group["編號"],
                customdata=list(zip(
                    group["重大主題指標"], 
                    group["重大性等級"], 
                    group["重大議題"],
                    group["面向"]
                )),
                textposition="top right",
                textfont=dict(size=12, color="#1e293b"),
                hovertemplate=(
                    "<b>No.%{text} %{customdata[2]}</b><br>"
                    "面向: %{customdata[3]}<br>"
                    "營運影響度: %{x}<br>"
                    "關心度: %{y}<br>"
                    "指標值 (X*Y): %{customdata[0]:.1f}<br>"
                    "重大性等級: %{customdata[1]}<extra></extra>"
                )
            ))

    # 圖表外觀與軸線設定 (加大 Left Margin 防止 Y 軸標題被裁切)
    fig.update_layout(
        xaxis=dict(
            title=dict(text="營運影響程度 (衝擊程度 X軸)", font=dict(size=13)),
            range=[axis_min, 10], 
            tickmode='linear', 
            tick0=axis_min, 
            dtick=1, 
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title=dict(text="利害關係人關心程度 (Y軸)", font=dict(size=13)),
            range=[axis_min, 10], 
            tickmode='linear', 
            tick0=axis_min, 
            dtick=1, 
            gridcolor='rgba(0,0,0,0.1)'
        ),
        margin=dict(l=75, r=30, t=30, b=50),
        height=580,
        plot_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5, borderwidth=1, bordercolor="#e5e7eb")
    )

    st.plotly_chart(fig, use_container_width=True)

with col_editor:
    st.subheader("🏆 重大性議題排序總覽")
    if not valid_df.empty:
        show_df = valid_df.sort_values(by="重大主題指標", ascending=False).reset_index(drop=True)
        st.dataframe(
            show_df[["編號", "面向", "重大議題", "重大主題指標", "重大性等級"]], 
            use_container_width=True, 
            hide_index=True, 
            height=240
        )
    else:
        st.info("請在上方編輯器中新增資料。")
