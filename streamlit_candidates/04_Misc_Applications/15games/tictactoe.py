import streamlit as st
import random

st.title("❌⭕ 井字棋 (Tic-Tac-Toe)")
st.caption("人機對戰 - Streamlit 互動版")

if "board" not in st.session_state:
    st.session_state.board = [" "] * 9
if "winner" not in st.session_state:
    st.session_state.winner = None

def check_winner(board):
    lines = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]
    for a,b,c in lines:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    if " " not in board:
        return "平手"
    return None

def computer_move():
    empty_indices = [i for i, x in enumerate(st.session_state.board) if x == " "]
    if empty_indices and st.session_state.winner is None:
        idx = random.choice(empty_indices)
        st.session_state.board[idx] = "O"
        st.session_state.winner = check_winner(st.session_state.board)

def make_move(idx):
    if st.session_state.board[idx] == " " and st.session_state.winner is None:
        st.session_state.board[idx] = "X"
        st.session_state.winner = check_winner(st.session_state.board)
        if st.session_state.winner is None:
            computer_move()

cols = st.columns(3)
for i in range(9):
    with cols[i % 3]:
        label = st.session_state.board[i] if st.session_state.board[i] != " " else " "
        st.button(
            label if label != " " else f"位置 {i+1}",
            key=f"btn_{i}",
            on_click=make_move,
            args=(i,),
            use_container_width=True,
            disabled=(st.session_state.board[i] != " " or st.session_state.winner is not None)
        )

if st.session_state.winner:
    if st.session_state.winner == "平手":
        st.info("🤝 遊戲平手！")
    elif st.session_state.winner == "X":
        st.balloons()
        st.success("🎉 恭喜你獲勝了！")
    else:
        st.error("🤖 電腦贏了，再接再厲！")

if st.button("🔄 重置遊戲", type="primary"):
    st.session_state.board = [" "] * 9
    st.session_state.winner = None
    st.rerun()
