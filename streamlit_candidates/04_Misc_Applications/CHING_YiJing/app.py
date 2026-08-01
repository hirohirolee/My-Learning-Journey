import streamlit as st
import random
import time

# Set Streamlit page config
st.set_page_config(
    page_title="大白話視覺系易經占卜",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom Style Sheet
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Noto+Sans+TC:wght@300;400;700&display=swap');
    
    .stApp {
        background-color: #1E1E24;
        color: #E2E8F0;
        font-family: 'Outfit', 'Noto Sans TC', sans-serif;
    }
    
    /* Center the title and tagline */
    .header-container {
        text-align: center;
        padding: 30px 10px;
    }
    
    .mystic-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #D4AF37 0%, #00E5FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        text-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
    }
    
    .tagline {
        color: #A0AEC0;
        font-size: 1.1rem;
        font-weight: 300;
        margin-top: 5px;
    }
    
    /* Card layout */
    .mystic-card {
        background: rgba(30, 30, 36, 0.95);
        border: 1px solid rgba(212, 175, 55, 0.25);
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 15px rgba(212, 175, 55, 0.05);
        margin-bottom: 25px;
        backdrop-filter: blur(8px);
    }
    
    /* Hexagram display */
    .hexagram-container {
        background: rgba(18, 18, 22, 0.9);
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 25px;
        display: flex;
        flex-direction: column-reverse; /* Read bottom up (1st to 6th line) */
        align-items: center;
        gap: 12px;
        box-shadow: 0 0 25px rgba(212, 175, 55, 0.15);
        width: 100%;
        max-width: 280px;
        margin: 0 auto 20px auto;
    }
    
    .hex-line-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }
    
    .hex-line-label {
        font-size: 0.75rem;
        color: #718096;
        margin-bottom: 2px;
        font-family: monospace;
    }
    
    .hex-line {
        width: 200px;
        height: 14px;
        border-radius: 4px;
    }
    
    .hex-line.yang {
        background: linear-gradient(90deg, #D4AF37 0%, #F3E5AB 100%);
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
    }
    
    .hex-line.yin {
        display: flex;
        justify-content: space-between;
        background: transparent;
    }
    
    .hex-line.yin .half-line {
        width: 90px;
        height: 14px;
        background: linear-gradient(90deg, #00E5FF 0%, #00B0FF 100%);
        border-radius: 4px;
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    }
    
    /* Result styling */
    .result-section-title {
        color: #D4AF37 !important;
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 15px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.2);
        padding-bottom: 5px;
    }
    
    .explanation-box {
        border-left: 4px solid #00E5FF;
        padding-left: 16px;
        margin: 15px 0;
        background: rgba(0, 229, 255, 0.05);
        border-radius: 0 8px 8px 0;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    .advice-box {
        border-left: 4px solid #D4AF37;
        padding-left: 16px;
        margin: 15px 0;
        background: rgba(212, 175, 55, 0.05);
        border-radius: 0 8px 8px 0;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    /* Inputs overrides */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        border-color: rgba(212, 175, 55, 0.3) !important;
    }
    
    /* Customize blockquote */
    blockquote {
        border-left: 4px solid #D4AF37 !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
        padding: 10px 15px !important;
        color: #CBD5E0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Database definition
HEXAGRAMS_DB = {
    "火雷噬嗑": {
        "name": "火雷噬嗑",
        "nickname": "狠狠咬碎障礙卦 🦷",
        "lines": ["Yang", "Yin", "Yin", "Yang", "Yin", "Yang"],  # Bottom to Top
        "intro": "噬嗑卦代表『咬碎障礙』。卦象上下都是堅硬的陽爻，中間是軟的陰爻，但偏偏第四爻卡了個硬骨頭。這代表你現在面臨的困境不是忍忍就能過去的，而是必須使勁咬碎它！",
        "dynamic_mapping": "你輸入的『{user_input}』就是卡在你牙縫和喉嚨中間的那根死骨頭！吞不下吐不出，此時絕對不能再當溫水煮青蛙的爛好人，必須拿出魄力，狠狠咬碎它才能徹底通暢！",
        "contexts": {
            "工作/創業 💼": "別再當溫水煮青蛙的爛好人了！團隊裡那個害群之馬或制度上的大黑洞，就是那根死骨頭。現在是時候主動出擊、正面對決，把它處理掉，工作才能推展。",
            "戀愛/脫單 ❤️": "冷戰是不會有結果的！感情中的疙瘩就像卡在喉嚨的刺，越忍越痛。趕緊找個機會把話說開，該吵的架就吵，吵完了才能知道是要繼續還是放手。",
            "投資/財運 💰": "壯士斷腕！那支套牢你已久的爛股票，或是一直在損耗你資金的無底洞項目，就是那根骨頭。立刻停損、依法維權，別再抱有不切實際的幻想。"
        }
    },
    "山水蒙": {
        "name": "山水蒙",
        "nickname": "滿頭問號、新手村鬼打牆卦 👁️‍🗨️",
        "lines": ["Yin", "Yang", "Yin", "Yin", "Yin", "Yang"],  # Bottom to Top
        "intro": "蒙卦代表『啟蒙與迷茫』。上方是代表阻礙的「山」（艮），下方是代表險難與未知的「水」（坎）。你現在就像是處於迷霧之中，不知方向，容易瞎猜瞎撞。",
        "dynamic_mapping": "你的困境『{user_input}』對應底部的深水，代表你現在徹底暈船、盲目瞎猜；而對方的冷淡或是環境的阻礙就是頂部的大山，人家根本不想動，你再怎麼瞎折騰也只是在新手村鬼打牆！",
        "contexts": {
            "工作/創業 💼": "你現在就是個無頭蒼蠅！別再閉門造車、盲目摸索了。趕快放下身段，去請教有經驗的老前輩或主管，聽聽他們的意見，否則只會一直在原地打轉。",
            "戀愛/脫單 ❤️": "清醒點！不要再瘋狂傳訊息轟炸對方了，你現在的樣子看起來像個小丑。對方現在就是一座冰山，你越熱情他越躲。冷靜三天，先充實自己再說。",
            "投資/財運 💰": "你是個理財小白，妥妥的韭菜預備軍！現在市場水很深，你根本看不清迷霧。趕緊把錢包鎖死，不要聽信任何投顧老師，先去買幾本理財書看懂再說。"
        }
    }
}

# Header Section
st.markdown("""
<div class="header-container">
    <div class="mystic-title">🔮 地表最接地氣！大白話視覺系易經占卜</div>
    <div class="tagline">打破封建迷信！用現代心理學與結構學，為你的人生卡關做超直白體檢。</div>
</div>
""", unsafe_allow_html=True)

# Main Form Container
st.markdown('<div class="mystic-card">', unsafe_allow_html=True)
with st.form("divination_form"):
    st.markdown("### 🏷️ 選擇占卜類別與輸入痛點")
    
    category = st.selectbox(
        "想問哪方面的事？",
        options=["工作/創業 💼", "戀愛/脫單 ❤️", "投資/財運 💰"]
    )
    
    user_input = st.text_input(
        "你的具體痛點或煩惱是？",
        placeholder="例如：主管腦袋進水、對方已讀不回、股票一片慘綠..."
    )
    
    submit_button = st.form_submit_button("🪙 誠心求導，起卦！")
st.markdown('</div>', unsafe_allow_html=True)

# Divination Action
if submit_button:
    # Graceful handling of empty input
    resolved_input = user_input.strip()
    if not resolved_input:
        resolved_input = "我說不出口的隱憂"
        
    with st.spinner("⚡ 正在排盤、感應天地、繪製專屬卦象..."):
        time.sleep(1.5)  # Simulate cosmic connection delay
    
    # Pick a random hexagram
    hexagram_key = random.choice(list(HEXAGRAMS_DB.keys()))
    hex_data = HEXAGRAMS_DB[hexagram_key]
    
    # Layout the output
    col1, col2 = st.columns([1, 1.8], gap="large")
    
    with col1:
        st.markdown(f"### 🛡️ 占得卦象")
        st.markdown(f"<h4 style='color:#D4AF37; text-align:center;'>{hex_data['name']}</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; color:#00E5FF; font-size:1.1rem; font-weight:bold; margin-bottom:15px;'>{hex_data['nickname']}</div>", unsafe_allow_html=True)
        
        # Render hexagram lines visually
        hex_lines_html = '<div class="hexagram-container">'
        for idx, line_type in enumerate(hex_data["lines"]):
            line_num = idx + 1
            label = "初爻 (Line 1)" if line_num == 1 else ("上爻 (Line 6)" if line_num == 6 else f"第 {line_num} 爻")
            
            if line_type == "Yang":
                line_html = f'<div class="hex-line-container"><div class="hex-line-label">{label}</div><div class="hex-line yang"></div></div>'
            else:
                line_html = f'<div class="hex-line-container"><div class="hex-line-label">{label}</div><div class="hex-line yin"><div class="half-line"></div><div class="half-line"></div></div></div>'
                
            hex_lines_html += line_html
        hex_lines_html += '</div>'
        st.html(hex_lines_html)
        
    with col2:
        st.markdown("### 🎯 神明大白話開示")
        
        st.markdown('<div class="result-section-title">💡 卦象解密</div>', unsafe_allow_html=True)
        st.markdown(f"*{hex_data['intro']}*")
        
        st.markdown('<div class="result-section-title">⚡ 痛點映射</div>', unsafe_allow_html=True)
        mapped_text = hex_data["dynamic_mapping"].format(user_input=resolved_input)
        st.markdown(f'<div class="explanation-box">{mapped_text}</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="result-section-title">🧭 現代生存指南</div>', unsafe_allow_html=True)
        advice_text = hex_data["contexts"][category]
        st.markdown(f'<div class="advice-box"><strong>針對你的 {category} 提問：</strong><br/>{advice_text}</div>', unsafe_allow_html=True)
        
        st.markdown("""
        > **🔮 易經小知識**：起卦求指引，心誠則靈。一次只問一事，卦象無好壞，一切皆是當下心境的投射。
        """)
        
    # Re-divine helper
    st.info("💡 對卦象不滿意？整理好思緒與呼吸，可以調整痛點敘述重新起卦！")
