import os
import sys
from pathlib import Path

_quant_root = str(Path(__file__).resolve().parent.parent)
if _quant_root in sys.path:
    sys.path.remove(_quant_root)
sys.path.insert(0, _quant_root)

for k in list(sys.modules.keys()):
    if k == 'config' or k == 'utils' or k.startswith('utils.'):
        sys.modules.pop(k, None)

import streamlit as st

from config import UI_PAGE_TITLE, UI_PAGE_ICON, UI_LAYOUT

# 1. 設定 Streamlit 頁面全局配置 (必須是第一個 st 指令)
st.set_page_config(
    page_title=UI_PAGE_TITLE,
    page_icon=UI_PAGE_ICON,
    layout=UI_LAYOUT,
    initial_sidebar_state="expanded"
)

def main():
    """
    Streamlit 應用程式主入口
    """
    # 2. 建立側邊欄 (Sidebar) UI
    with st.sidebar:
        st.title(f"{UI_PAGE_ICON} 👵 阿嬤的買菜神器")
        st.markdown("---")
        st.info(
            "💡 **這頁能幫你做什麼：**\n\n"
            "歡迎來到阿嬤的超級大黑板！這裡幫你把所有好康都整理好了。\n"
            "直接點擊左邊的選單來看看：\n"
            "- 🔥 **阿嬤的每日挑蘋果秘笈**\n"
            "- 📊 **阿嬤的時光機**\n"
            "- 📰 **市場阿姨們的八卦風向**\n"
            "- ⚙️ **阿嬤的總開關**\n"
            "- 🎯 **老頭家誠實豆沙包** (新)\n"
            "- ⚡ **機器人賺便當錢** (新)"
        )
        st.markdown("---")
        st.caption("Version 2.0 | 👵 由阿嬤與 AI 秘書共同打造")

    # 3. 預設首頁內容 (當停留在首頁時的說明與儀表板)
    st.info("💡 **這頁能幫你做什麼：** 這是我們的大門口，一眼看懂現在市場天氣好不好、AI 秘書有沒有在認真顧店！")
    st.title("👵 歡迎來到阿嬤的買菜神器 (AI 秘書保鑣版)")
    
    from datetime import datetime
    st.info(f"🕒 **目前系統資料更新時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (剛從菜市場最新鮮帶回來的！)")
    
    st.markdown(
        """
        這是一套結合了 **AI 老頭家眼光**、**菜市場阿姨八卦（新聞風向）** 與 **時光機驗證** 的超強防護罩。買股票就像去菜市場挑蘋果，我們幫你挑最甜的！🍎
        
        ### 🎯 阿嬤的錦囊妙計
        1. **眼觀四面耳聽八方**：看天氣預報帶傘 ☔️，結合技術線型、外資買賣與市場八卦，全方位幫你評估。
        2. **請機器人當保鑣**：AI 老頭家親自上陣，自動學習市場的眉眉角角，比傳統死板的規則聰明多了！🤖
        3. **資金保護傘（建議買多少）**：遇到好天氣就多買點，快下雨就趕快收手，保護阿嬤的退休金 💰。
        
        👉 **快從左邊的列表點進去，看看今天 AI 秘書有什麼好康報給你！**
        """
    )
    st.divider()
    
    # 4. 呈現系統高階狀態卡片 (快速檢視系統健康度與大盤狀態)
    st.markdown("### 📊 阿嬤的店面招牌 (即時監控)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="🤖 AI 老頭家狀態", value="正在顧店 (精神飽滿)", delta="準確度: 讚")
    with col2:
        st.metric(label="📰 市場阿姨們的八卦風向", value="大家很嗨", delta="心情 +0.45", delta_color="normal")
    with col3:
        st.metric(label="🍎 大盤買菜指數", value="22,150", delta="-1.5%", delta_color="inverse")

main()
