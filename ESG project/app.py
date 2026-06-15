import numpy as np
import pandas as pd
import streamlit as __st  # 規避特定命名限制
import plotly.graph_objects as go

# 1. 網頁基本設定
__st.set_page_config(page_title="ESG 重大性矩陣分析工具", layout="wide")

__st.title("🍀 00股份有限公司 永續重大議題矩陣工具")
__st.markdown("透過左側控制面板調整重大性門檻，右側圖表將會即時動態更新。")

# =====================================================================
# 2. 側邊欄控制面板 (Sidebar)
# =====================================================================
__st.sidebar.header("🛠️ 矩陣門檻設定")
__st.sidebar.markdown("請設定「兩項分數相加（滿分20分）」的切分門檻：")

# 讓使用者調整低度重大與高度重大的門檻
low_sum_limit = __st.sidebar.slider(
    "🟢 低度重大門檻 (總分低於此數值)",
    min_value=2.0,
    max_value=12.0,
    value=9.0,
    step=0.5,
)

high_sum_limit = __st.sidebar.slider(
    "🟣 高度重大門檻 (總分高於此數值)",
    min_value=12.5,
    max_value=18.0,
    value=15.0,
    step=0.5,
)

__st.sidebar.write("---")
__st.sidebar.markdown(
    f"""
**目前的分區邏輯：**
* 總分 `< {low_sum_limit}` ➡️ **低度重大**
* 總分 `介於兩者之間` ➡️ **中度重大**
* 總分 `> {high_sum_limit}` ➡️ **高度重大**
"""
)

# =====================================================================
# 3. 原始數據統整
# =====================================================================
data = {
    "面向": ["經濟面", "經濟面", "環境面", "環境面", "社會面", "社會面", "社會面", "治理面", "治理面"],
    "重大議題": ["經濟績效與獲利", "反貪腐與反競爭", "溫室氣體管理", "水資源管理", "安心職場", "人才招募與留任", "顧客隱私", "誠信經營與法規遵循", "吹哨者制度"],
    "營運影響度": [9.0, 3.5, 7.5, 4.0, 8.5, 8.8, 9.5, 9.2, 4.2],  # X軸
    "關心度": [8.8, 4.2, 7.8, 4.5, 8.2, 8.0, 9.6, 9.0, 4.8],  # Y軸
}
init_df = pd.DataFrame(data)

color_map = {
    "環境面": "#2ca02c",  # 綠
    "社會面": "#ff7f0e",  # 橘
    "經濟面": "#1f77b4",  # 藍
    "治理面": "#17becf",  # 青
}

# =====================================================================
# 4. 資料與圖表渲染
# =====================================================================
col1, col2 = __st.columns([1.6, 1.4])

with col2:
    __st.subheader("📝 議題數據編輯器")
    __st.markdown("💡 雙擊格可修改。按下方 **`+ Add row`** 或選列按 Del 可增減。")
    edited_df = __st.data_editor(
        init_df,
        num_rows="dynamic",
        use_container_width=True,
        height=300,
        column_config={
            "面向": __st.column_config.SelectboxColumn("面向", options=["經濟面", "環境面", "社會面", "治理面"], required=True, width="small"),
            "重大議題": __st.column_config.TextColumn("重大議題", required=True, width="medium"),
            "營運影響度": __st.column_config.NumberColumn("營運影響度", min_value=0.0, max_value=10.0, step=0.1, required=True, width="small"),
            "關心度": __st.column_config.NumberColumn("關心度", min_value=0.0, max_value=10.0, step=0.1, required=True, width="small"),
        }
    )

    __st.subheader("🏆 重大性排序一覽")
    valid_df = edited_df.dropna(subset=["面向", "重大議題", "營運影響度", "關心度"]).copy()
    
    if not valid_df.empty:
        valid_df["總分"] = valid_df["營運影響度"] + valid_df["關心度"]
        
        def get_level(row):
            total = row["總分"]
            if total < low_sum_limit: return "🟢 低度重大"
            elif total > high_sum_limit: return "🟣 高度重大"
            else: return "🟡 中度重大"
        
        valid_df["重大性等級"] = valid_df.apply(get_level, axis=1)
        show_df = valid_df.sort_values(by="總分", ascending=False).reset_index(drop=True)
        __st.dataframe(show_df[["面向", "重大議題", "總分", "重大性等級"]], use_container_width=True, hide_index=True, height=250)
    else:
        __st.info("請在上方編輯器中新增資料。")

with col1:
    # 建立 Plotly 互動式圖表
    fig = go.Figure()

    # 5. 繪製背景分區 (低、中、高)
    # 利用形狀 (Shapes) 來畫出背後的切分區域
    fig.add_shape(type="path", path=f"M 0,0 L {low_sum_limit},0 L 0,{low_sum_limit} Z", fillcolor="#f3f4f6", opacity=0.6, line_width=0, layer="below")
    fig.add_shape(type="path", path=f"M {low_sum_limit},0 L {high_sum_limit},0 L 0,{high_sum_limit} L 0,{low_sum_limit} Z", fillcolor="#fef3c7", opacity=0.6, line_width=0, layer="below")
    fig.add_shape(type="path", path=f"M {high_sum_limit},0 L 10,0 L 10,10 L 0,10 L 0,{high_sum_limit} Z", fillcolor="#ebd5fc", opacity=0.6, line_width=0, layer="below")

    # 6. 新增背景區域文字標籤 (天生支援中文)
    fig.add_annotation(x=low_sum_limit/4, y=low_sum_limit/4, text="低度重大", showarrow=False, font=dict(size=14, color="#4b5563", bold=True))
    fig.add_annotation(x=(low_sum_limit+high_sum_limit)/4, y=(low_sum_limit+high_sum_limit)/4, text="中度重大", showarrow=False, font=dict(size=14, color="#b45309", bold=True))
    fig.add_annotation(x=(high_sum_limit+20)/4, y=(high_sum_limit+20)/4, text="高度重大", showarrow=False, font=dict(size=14, color="#6d28d9", bold=True))

    # 7. 繪製資料點與標籤
    if not valid_df.empty:
        valid_df["Color"] = valid_df["面向"].map(color_map).fillna("#757575")
        
        # 依面向分組繪製，以便自動生成漂亮的圖例
        for name, group in valid_df.groupby("面向"):
            fig.add_trace(go.Scatter(
                x=group["營運影響度"],
                y=group["關心度"],
                mode="markers+text",
                name=name,
                marker=dict(size=12, color=color_map.get(name, "#757575"), line=dict(width=1.5, color='white')),
                text=group["重大議題"],
                textposition="top right",
                font=dict(size=11),
                hovertemplate="<b>%{text}</b><br>營運影響度: %{x}<br>關心度: %{y}<extra></extra>"
            ))

    # 8. 圖表外觀與軸線設定
    fig.update_layout(
        xaxis=dict(title="營運影響程度（衝擊程度）", range=[0, 10], tickmode='linear', tick0=0, dtick=1, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(title="對經濟、環境和人（人權）的衝擊影響（利害關係人關心度）", range=[0, 10], tickmode='linear', tick0=0, dtick=1, gridcolor='rgba(0,0,0,0.1)'),
        margin=dict(l=40, r=40, t=20, b=40),
        height=600,
        plot_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, borderwidth=1, bordercolor="#e5e7eb")
    )

    # 顯示 Plotly 圖表
    __st.plotly_chart(fig, use_container_width=True)
