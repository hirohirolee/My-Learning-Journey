import streamlit as st
import time

st.set_page_config(page_title="阿嬤的總開關", layout="wide")

st.info("💡 **這頁能幫你做什麼：** 這裡是阿嬤的總開關！可以手動叫機器人去菜市場補貨（更新資料），也可以看看他們有沒有乖乖按時幫阿嬤做事。")
st.title("⚙️ 阿嬤的總開關 (系統指揮中心)")
st.markdown("不用懂那些複雜的電腦程式，按鈕按下去，機器人就會乖乖去跑腿囉！")

st.header("🪫 今天補貨了沒？")
col1, col2, col3 = st.columns(3)
col1.metric("市場價格紀錄 (歷史價量)", "今日 14:00", "已補貨")
col2.metric("外資大戶動向 (籌碼資料)", "今日 15:30", "已補貨")
col3.metric("菜市場八卦 (新聞風向)", "昨日 23:00", "-阿姨還沒講", delta_color="inverse")

st.markdown("---")

st.header("🚀 手動叫機器人跑腿")

with st.expander("叫機器人去菜市場補貨 (下載最新資料)", expanded=True):
    st.warning("⚠️ 乖孫提醒阿嬤：不要一直狂按喔！按太快會被菜市場的警衛（API 限制）趕出來。")
    if st.button("📥 點我！馬上叫機器人去補貨"):
        with st.spinner("機器人正在騎腳踏車去菜市場..."):
            prog = st.progress(0)
            
            st.text("正在看今天有哪些蘋果上市...")
            time.sleep(0.5)
            prog.progress(30)
            
            st.text("正在抄下今天的蘋果價格跟大戶名單...")
            time.sleep(1)
            prog.progress(70)
            
            st.text("正在聽菜市場阿姨聊八卦...")
            time.sleep(1.5)
            prog.progress(100)
            
            st.success("✅ 補貨完成！阿嬤，明天的挑蘋果秘笈準備好囉！🍎")

with st.expander("叫 AI 老頭家去補習 (重新訓練模型)"):
    st.info("💡 叫老頭家去補習要花很久的時間，他會拿過去的歷史考卷（時光機）重新練習一遍。")
    if st.button("🧠 點我！送 AI 老頭家去補習班"):
        st.error("❌ 哎呀！阿嬤，現在補習班沒開（系統資源不足），請叫乖孫工程師幫你處理。")

st.markdown("---")
st.header("⏱️ 機器人乖乖上班時間表")
st.code("""
# 機器人的打卡表

# 每天下午 15:30，自動去抄菜市場收盤價
30 15 * * 1-5 python /tw_ai_quant_system/main_scheduler.py --task download_data

# 每天晚上 20:00，AI 老頭家開始挑蘋果、寫報告給阿嬤看
00 20 * * 1-5 python /tw_ai_quant_system/main_scheduler.py --task run_ai_scanner
""", language='bash')
