import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import streamlit as __st  # 規避特定命名限制
import urllib.request
import os
from matplotlib.lines import Line2D

# 1. 網頁基本設定
__st.set_page_config(page_title="ESG 重大性矩陣分析工具", layout="wide")

# =====================================================================
# ⚙️ 解決 Streamlit Cloud Linux 環境中文亂碼問題
# =====================================================================
@__st.cache_resource  # 快取字型下載機制，避免每次網頁重新整理都重複下載
def init_chinese_font():
    # 使用 Adobe 開源的思源黑體 (Source Han Sans TC) 繁體中文版
    font_url = "https://github.com/adobe-fonts/source-hans-sans/raw/release/OTF/TraditionalChinese/SourceHanSansTC-Regular.otf"
    font_path = "SourceHanSansTC-Regular.otf"
    
    # 如果本地沒有字型檔，就從 GitHub 下載
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve(font_url, font_path)
        except Exception as e:
            # 若下載失敗，則降級使用系統預設字型
            return ["sans-serif"]
            
    # 將下載的字型註冊到 matplotlib 中
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    return [font_prop.get_name(), "sans-serif"]

# 執行字型初始化，並設定給 matplotlib
font_list = init_chinese_font()
plt.rcParams["font.sans-serif"] = font_list
plt.rcParams["axes.unicode_minus"] = False

# =====================================================================

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
# 3. 原始數據統整 (未來可改成 st.file_uploader 讓使用者上傳 Excel)
# =====================================================================
data = {
    "面向": [
        "經濟面",
        "經濟面",
        "環境面",
        "環境面",
        "社會面",
        "社會面",
        "社會面",
        "治理面",
        "治理面",
    ],
    "重大議題": [
        "經濟績效與獲利",
        "反貪腐與反競爭",
        "溫室氣體管理",
        "水資源管理",
        "安心職場",
        "人才招募與留任",
        "顧客隱私",
        "誠信經營與法規遵循",
        "吹哨者制度",
    ],
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

# 先在右側 col2 進行數據編輯，以便將編輯後的數據 (edited_df) 即時傳給左側 col1 的圖表
with col2:
    __st.subheader("📝 議題數據編輯器")
    __st.markdown("💡 雙擊格可修改。按下方 **`+ Add row`** 或選列按 Del 可增減。")
    edited_df = __st.data_editor(
        init_df,
        num_rows="dynamic",
        use_container_width=True,
        height=300,  # 固定高度，超出的話可在內部滾動
        column_config={
            "面向": __st.column_config.SelectboxColumn(
                "面向",
                options=["經濟面", "環境面", "社會面", "治理面"],
                required=True,
                width="small",
            ),
            "重大議題": __st.column_config.TextColumn(
                "重大議題",
                required=True,
                width="medium",
            ),
            "營運影響度": __st.column_config.NumberColumn(
                "營運影響度",
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                required=True,
                width="small",
            ),
            "關心度": __st.column_config.NumberColumn(
                "關心度",
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                required=True,
                width="small",
            ),
        }
    )

    # 顯示依總分排序的重大性等級表
    __st.subheader("🏆 重大性排序一覽")
    
    # 清理可能包含的 NaN 列（例如使用者新增了空白列）
    valid_df = edited_df.dropna(subset=["面向", "重大議題", "營運影響度", "關心度"]).copy()
    
    if not valid_df.empty:
        valid_df["總分"] = valid_df["營運影響度"] + valid_df["關心度"]
        
        # 定義重大性區分等級
        def get_level(row):
            total = row["總分"]
            if total < low_sum_limit:
                return "🟢 低度重大"
            elif total > high_sum_limit:
                return "🟣 高度重大"
            else:
                return "🟡 中度重大"
        
        valid_df["重大性等級"] = valid_df.apply(get_level, axis=1)
        show_df = valid_df.sort_values(by="總分", ascending=False).reset_index(drop=True)
        __st.dataframe(
            show_df[["面向", "重大議題", "總分", "重大性等級"]], 
            use_container_width=True,
            hide_index=True,
            height=250  # 固定高度，超出的話可在內部滾動
        )
    else:
        __st.info("請在上方編輯器中新增資料。")

with col1:
    # 建立 Matplotlib 圖表
    fig, ax = plt.subplots(figsize=(10, 6.5))

    # 背景漸層網格
    X, Y = np.meshgrid(np.linspace(0, 10, 300), np.linspace(0, 10, 300))
    Z = X + Y
    levels = [0, low_sum_limit, high_sum_limit, 20]

    # 繪製三個區塊的背景顏色
    ax.contourf(
        X,
        Y,
        Z,
        levels=levels,
        colors=["#f3f4f6", "#fef3c7", "#ebd5fc"],
        alpha=0.5,
    )

    # 動態調整背景區域的文字位置 (置於對角線上，以符合 X+Y 區間)
    ax.text(
        low_sum_limit / 4,
        low_sum_limit / 4,
        "低度重大",
        fontsize=12,
        fontweight="bold",
        color="#4b5563",  # 深灰
        alpha=0.8,
        ha="center",
        va="center",
    )
    ax.text(
        (low_sum_limit + high_sum_limit) / 4,
        (low_sum_limit + high_sum_limit) / 4,
        "中度重大",
        fontsize=12,
        fontweight="bold",
        color="#b45309",  # 深橘黃
        alpha=0.8,
        ha="center",
        va="center",
    )
    ax.text(
        (high_sum_limit + 20) / 4,
        (high_sum_limit + 20) / 4,
        "高度重大",
        fontsize=12,
        fontweight="bold",
        color="#6d28d9",  # 深紫
        alpha=0.9,
        ha="center",
        va="center",
    )

    # 繪製議題散佈點
    if not valid_df.empty:
        valid_df["Color"] = valid_df["面向"].map(color_map).fillna("#757575")
        for _, row in valid_df.iterrows():
            ax.scatter(
                row["營運影響度"],
                row["關心度"],
                color=row["Color"],
                s=130,
                edgecolors="w",
                linewidth=1.5,
                zorder=3,
            )
            ax.text(
                row["營運影響度"] + 0.15,
                row["關心度"],
                row["重大議題"],
                fontsize=10,
                va="center",
                zorder=4,
            )

    # 軸線設定
    ax.set_xlabel("營運影響程度（衝擊程度）", fontsize=11, labelpad=10)
    ax.set_ylabel(
        "對經濟、環境和人（人權）的的衝擊影響（利害關係人關心度）",
        fontsize=11,
        labelpad=10,
    )
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xticks(range(0, 11))
    ax.set_yticks(range(0, 11))
    ax.grid(True, linestyle="--", alpha=0.3, zorder=1)

    # 自訂圖例
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label=k,
            markerfacecolor=v,
            markersize=9,
        )
        for k, v in color_map.items()
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.2),
        ncol=4,
        frameon=True,
        fontsize=10,
    )

    plt.tight_layout()

    # 將圖表傳遞給 Streamlit 顯示
    __st.pyplot(fig)
