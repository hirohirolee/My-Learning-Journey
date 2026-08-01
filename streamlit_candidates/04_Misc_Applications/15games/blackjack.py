import streamlit as st
import random

st.title("🃏 21點撲克牌遊戲 (Blackjack)")
st.caption("經典卡牌 - Streamlit 互動版")

if "player_hand" not in st.session_state:
    st.session_state.player_hand = []
if "dealer_hand" not in st.session_state:
    st.session_state.dealer_hand = []
if "game_over" not in st.session_state:
    st.session_state.game_over = False

def deal_card():
    cards = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
    return random.choice(cards)

def calculate_score(hand):
    score = sum(hand)
    if score > 21 and 11 in hand:
        hand.remove(11)
        hand.append(1)
        score = sum(hand)
    return score

def start_new_game():
    st.session_state.player_hand = [deal_card(), deal_card()]
    st.session_state.dealer_hand = [deal_card(), deal_card()]
    st.session_state.game_over = False

if not st.session_state.player_hand:
    start_new_game()

player_score = calculate_score(st.session_state.player_hand)
dealer_score = calculate_score(st.session_state.dealer_hand)

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 👤 玩家的手牌")
    st.write(f"卡牌: {st.session_state.player_hand}")
    st.write(f"**總點數:** {player_score}")

with col2:
    st.markdown("### 🤖 莊家（電腦）的手牌")
    if st.session_state.game_over:
        st.write(f"卡牌: {st.session_state.dealer_hand}")
        st.write(f"**總點數:** {dealer_score}")
    else:
        st.write(f"卡牌: [{st.session_state.dealer_hand[0]}, ❓]")

st.divider()

if not st.session_state.game_over:
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("➕ 要牌 (Hit)"):
            st.session_state.player_hand.append(deal_card())
            if calculate_score(st.session_state.player_hand) > 21:
                st.session_state.game_over = True
            st.rerun()
    with b_col2:
        if st.button("✋ 停牌 (Stand)"):
            while calculate_score(st.session_state.dealer_hand) < 17:
                st.session_state.dealer_hand.append(deal_card())
            st.session_state.game_over = True
            st.rerun()
else:
    if player_score > 21:
        st.error("💥 爆牌了！玩家落敗。")
    elif dealer_score > 21 or player_score > dealer_score:
        st.balloons()
        st.success("🎉 恭喜！玩家獲勝！")
    elif player_score == dealer_score:
        st.warning("🤝 平局！")
    else:
        st.error("🤖 莊家贏了。")

if st.button("🔄 重新開局", type="primary"):
    start_new_game()
    st.rerun()
