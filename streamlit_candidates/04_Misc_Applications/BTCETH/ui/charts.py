import streamlit as st
st.title('charts.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

# Consistent color palette for premium design
COLOR_BTC_ORANGE = "#f7931a"
COLOR_MUTED_BG = "#0b0f19"
COLOR_CARD_BG = "rgba(17, 24, 39, 0.7)"
COLOR_GRID = "rgba(255, 255, 255, 0.08)"
COLOR_TEXT = "#e2e8f0"

def _apply_dark_layout(fig: go.Figure, title: str, x_title: str = "", y_title: str = "") -> None:
    """Applies a clean, standard dark theme layout to a Plotly figure."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=COLOR_BTC_ORANGE, family="Inter")
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLOR_TEXT, family="Inter"),
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis=dict(
            title=x_title,
            gridcolor=COLOR_GRID,
            zerolinecolor=COLOR_GRID,
            tickfont=dict(color="#94a3b8")
        ),
        yaxis=dict(
            title=y_title,
            gridcolor=COLOR_GRID,
            zerolinecolor=COLOR_GRID,
            tickfont=dict(color="#94a3b8")
        ),
        legend=dict(
            bgcolor="rgba(17, 24, 39, 0.6)",
            bordercolor=COLOR_GRID,
            borderwidth=1
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_size=12,
            font_family="Inter"
        )
    )

def create_probability_curve_chart(horizons: List[Dict[str, Any]]) -> go.Figure:
    """Creates a line chart showing how block success probability scales over time horizons."""
    df = pd.DataFrame(horizons)
    df["probability_pct"] = df["probability"] * 100.0

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["horizon"],
        y=df["probability_pct"],
        mode="lines+markers",
        line=dict(color=COLOR_BTC_ORANGE, width=3),
        marker=dict(size=8, color="#ffffff", line=dict(color=COLOR_BTC_ORANGE, width=2)),
        hovertemplate="時間跨度: <b>%{x}</b><br>出塊成功率: <b>%{y:.10f}%</b><extra></extra>"
    ))
    
    _apply_dark_layout(
        fig,
        title="不同時間跨度下的單機挖礦成功機率 (Poisson 模型)",
        x_title="時間跨度",
        y_title="找到至少 1 個區塊的機率 (%)"
    )
    return fig

def create_blocks_distribution_chart(blocks_distribution: Dict[int, float]) -> go.Figure:
    """Creates a bar chart displaying the frequency of mining exact block counts."""
    # Sort and filter keys to display standard block counts (e.g. 0 to 5)
    sorted_keys = sorted(blocks_distribution.keys())
    x = [str(k) for k in sorted_keys if k <= 5]
    y = [blocks_distribution[k] * 100.0 for k in sorted_keys if k <= 5]
    
    # Catch any leftover probability and label it as 5+
    remainder = sum(v * 100.0 for k, v in blocks_distribution.items() if k > 5)
    if remainder > 0.0:
        x.append("5+")
        y.append(remainder)
        
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x,
        y=y,
        marker_color="rgba(247, 147, 26, 0.75)",
        marker_line=dict(color=COLOR_BTC_ORANGE, width=1.5),
        hovertemplate="已挖出區塊數: <b>%{x}</b><br>可能性: <b>%{y:.4f}%</b><extra></extra>"
    ))
    
    _apply_dark_layout(
        fig,
        title="生命週期內已發現區塊數的機率分布",
        x_title="發現區塊的數量",
        y_title="機率 (%)"
    )
    return fig

def create_cash_flow_fan_chart(
    months: int,
    mean_cf_path: List[float],
    cf_percentiles: Dict[int, List[float]]
) -> go.Figure:
    """Generates a Monte Carlo fan chart showing cumulative cash flow pathways and confidence bands."""
    x = list(range(months + 1))
    
    fig = go.Figure()
    
    # Shade between 5th and 95th percentile
    fig.add_trace(go.Scatter(
        x=x + x[::-1],
        y=cf_percentiles[95] + cf_percentiles[5][::-1],
        fill="toself",
        fillcolor="rgba(239, 68, 68, 0.05)",  # Translucent red
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        showlegend=True,
        name="95% 置信區間 (5th - 95th)"
    ))

    # Shade between 25th and 75th percentile
    fig.add_trace(go.Scatter(
        x=x + x[::-1],
        y=cf_percentiles[75] + cf_percentiles[25][::-1],
        fill="toself",
        fillcolor="rgba(247, 147, 26, 0.15)",  # Translucent orange
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        showlegend=True,
        name="50% 置信區間 (25th - 75th)"
    ))

    # Median (50th) Path
    fig.add_trace(go.Scatter(
        x=x,
        y=cf_percentiles[50],
        line=dict(color="#3b82f6", width=2, dash="dash"),
        name="中位數路徑 (50th 百分位)",
        hovertemplate="第 %{x} 個月<br>中位數現金流: <b>$%{y:,.2f}</b><extra></extra>"
    ))

    # Mean Path
    fig.add_trace(go.Scatter(
        x=x,
        y=mean_cf_path,
        line=dict(color=COLOR_BTC_ORANGE, width=3),
        name="平均值路徑 (期望值)",
        hovertemplate="第 %{x} 個月<br>平均現金流: <b>$%{y:,.2f}</b><extra></extra>"
    ))

    # Zero breakeven line
    fig.add_trace(go.Scatter(
        x=x,
        y=[0] * len(x),
        line=dict(color="#ef4444", width=1, dash="dot"),
        name="盈虧平衡界線",
        hoverinfo="skip"
    ))

    _apply_dark_layout(
        fig,
        title="蒙特卡洛累計現金流置信區間扇形圖",
        x_title="時間軸 (月)",
        y_title="累計淨現金流 (USD)"
    )
    return fig

def create_waterfall_chart(
    asic_cost: float,
    opex: float,
    expected_revenue: float,
    net_profit: float
) -> go.Figure:
    """Generates a financial waterfall chart depicting cumulative profit."""
    fig = go.Figure(go.Waterfall(
        name="財務明細",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["硬體成本 (ASIC)", "營運成本 (OpEx)", "挖礦總收益", "淨利潤"],
        textposition="outside",
        text=[f"-${asic_cost:,.0f}", f"-${opex:,.0f}", f"+${expected_revenue:,.0f}", f"${net_profit:,.0f}"],
        y=[-asic_cost, -opex, expected_revenue, net_profit],
        connector=dict(line=dict(color="rgba(255,255,255,0.2)")),
        decreasing=dict(marker=dict(color="#ef4444")),
        increasing=dict(marker=dict(color="#10b981")),
        totals=dict(marker=dict(color="#f7931a"))
    ))
    
    _apply_dark_layout(
        fig,
        title="預期生命週期財務瀑布圖",
        y_title="USD 價值"
    )
    return fig

def create_expenses_pie_chart(
    asic_cost: float,
    electricity_cost: float,
    cooling_cost: float,
    maintenance_cost: float
) -> go.Figure:
    """Creates a pie chart showing expense distributions."""
    labels = ["購置 ASIC", "電費支出", "冷卻 / PUE 額外功耗", "維護 / 託管"]
    values = [asic_cost, electricity_cost, cooling_cost, maintenance_cost]
    
    # Filter out zero values to avoid empty slices
    filtered_data = [(l, v) for l, v in zip(labels, values) if v > 0]
    if not filtered_data:
        filtered_data = [("無支出", 1.0)]
    
    l_final, v_final = zip(*filtered_data)

    fig = go.Figure(go.Pie(
        labels=l_final,
        values=v_final,
        hole=0.4,
        marker=dict(colors=["#ef4444", "#3b82f6", "#eab308", "#10b981"]),
        hovertemplate="費用項目: <b>%{label}</b><br>金額: <b>$%{value:,.2f}</b> (%{percent})<extra></extra>"
    ))
    
    _apply_dark_layout(
        fig,
        title="生命週期成本分布明細"
    )
    return fig

def create_sensitivity_tornado_chart(
    base_npv: float,
    sensitivity_results: Dict[str, Tuple[float, float]]
) -> go.Figure:
    """Creates a Tornado chart displaying how parameters affect NPV."""
    parameters = list(sensitivity_results.keys())
    
    # Calculate the deviations from base NPV
    low_values = [sensitivity_results[p][0] - base_npv for p in parameters]
    high_values = [sensitivity_results[p][1] - base_npv for p in parameters]
    
    fig = go.Figure()
    
    # Low scenario (-20%)
    fig.add_trace(go.Bar(
        y=parameters,
        x=low_values,
        name="-20% 參數偏移",
        orientation="h",
        marker=dict(color="#ef4444"),
        hovertemplate="參數: <b>%{y}</b><br>NPV 偏移額: <b>$%{x:,.2f}</b><extra></extra>"
    ))
    
    # High scenario (+20%)
    fig.add_trace(go.Bar(
        y=parameters,
        x=high_values,
        name="+20% 參數偏移",
        orientation="h",
        marker=dict(color="#10b981"),
        hovertemplate="參數: <b>%{y}</b><br>NPV 偏移額: <b>$%{x:,.2f}</b><extra></extra>"
    ))
    
    _apply_dark_layout(
        fig,
        title="NPV 敏感度龍捲風圖 (相對於基準案例的偏移)",
        x_title="NPV 偏移金額 (USD)",
        y_title="挖礦參數"
    )
    fig.update_layout(barmode="overlay")
    return fig

def create_roi_heatmap(
    price_range: np.ndarray,
    diff_growth_range: np.ndarray,
    roi_matrix: np.ndarray
) -> go.Figure:
    """Generates an ROI heatmap showing yields under varied prices & difficulties."""
    # Format labels for clean display
    y_labels = [f"${p:,.0f}" for p in price_range]
    x_labels = [f"{g * 100:.1f}%" for g in diff_growth_range]

    fig = go.Figure(data=go.Heatmap(
        z=roi_matrix,
        x=x_labels,
        y=y_labels,
        colorscale=[
            [0.0, "rgb(153, 0, 0)"],       # Dark Red
            [0.4, "rgb(230, 92, 0)"],      # Orange
            [0.5, "rgb(255, 230, 204)"],   # Translucent
            [0.6, "rgb(51, 153, 102)"],    # Soft Green
            [1.0, "rgb(0, 102, 34)"]       # Dark Green
        ],
        colorbar=dict(title="ROI (%)", ticksuffix="%"),
        hovertemplate="難度年增長率: <b>%{x}</b><br>比特幣價格: <b>%{y}</b><br>預期 ROI: <b>%{z:.2f}%</b><extra></extra>"
    ))
    
    _apply_dark_layout(
        fig,
        title="預期生命週期 ROI 敏感度分析",
        x_title="全網難度年增長率",
        y_title="比特幣價格 (USD)"
    )
    return fig


# ====== 自動生成的測試執行區塊 ======
if __name__ == "__main__":
    st.write("---")
    st.subheader("函數測試區塊")
    if st.button("執行 create_probability_curve_chart"):
        try:
            res = create_probability_curve_chart() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 create_blocks_distribution_chart"):
        try:
            res = create_blocks_distribution_chart() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 create_cash_flow_fan_chart"):
        try:
            res = create_cash_flow_fan_chart() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 create_waterfall_chart"):
        try:
            res = create_waterfall_chart() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 create_expenses_pie_chart"):
        try:
            res = create_expenses_pie_chart() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 create_sensitivity_tornado_chart"):
        try:
            res = create_sensitivity_tornado_chart() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
    if st.button("執行 create_roi_heatmap"):
        try:
            res = create_roi_heatmap() # 請視需要自行補上參數
            st.write("執行結果:", res)
        except Exception as e:
            st.error(f"執行出錯，可能需要提供參數：{e}")
