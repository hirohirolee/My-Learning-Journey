import streamlit as st
import random

st.title("👑 皇家對決 (Royal Clash Strategy Tool)")
st.caption("1v1 卡牌對戰與英雄輔助工具 - Streamlit 互動版")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="⚔️ 英雄指揮官", value="聖騎士國王", delta="等級 10")
with col2:
    st.metric(label="💧 聖水恢復速度", value="1.5x", delta="極速戰術")
with col3:
    st.metric(label="🏆 目前勝率", value="68.5%", delta="高階競技場")

st.markdown("### 🃏 推薦卡組與組合分析")

cards = [
    ("🛡️ 皇家巨人", "坦克", "6 聖水", "高血量近戰，針對防禦塔"),
    ("🔥 烈焰法師", "遠程/AOE", "5 聖水", "範圍火球傷害，清群怪首選"),
    ("⚡ 閃電電導塔", "建築", "4 聖水", "對空/對地高頻率電擊防禦塔"),
    ("🏹 哥布林飛桶", "法術", "3 聖水", "直接偷襲敵方主塔"),
    ("🐉 飛龍寶寶", "飛行", "4 聖水", "空中範圍傷害與護甲"),
]

for name, ctype, cost, desc in cards:
    with st.expander(f"{name} ({cost}) - {ctype}"):
        st.write(f"**功能描述:** {desc}")
        st.progress(random.randint(60, 95))

if st.button("🎲 模擬一局卡牌對戰", type="primary"):
    with st.spinner("⚔️ 戰鬥模擬運算中..."):
        win = random.choice([True, False])
        if win:
            st.balloons()
            st.success("🎉 戰術生效！你成功推倒敵方皇家三塔，奪得勝利！")
        else:
            st.error("💀 敵方使用閃電反制，戰術失效，請調整卡組再試！")
