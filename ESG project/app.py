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
    "營運影響度":
