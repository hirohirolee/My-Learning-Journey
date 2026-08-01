import streamlit as st
import random

st.set_page_config(page_title="小精靈迷宮 (Pacman)", layout="wide")
st.title("👾 小精靈迷宮大冒險 (Pacman Interactive)")
st.caption("經典迷宮遊戲 - Streamlit 可玩互動版")

# Initial maze layout configuration
INITIAL_MAZE = [
    ["🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱"],
    ["🧱", "😃", "🟡", "🟡", "🧱", "🟡", "🟡", "🟡", "🍇", "🟡", "🧱"],
    ["🧱", "🟡", "🧱", "🟡", "🧱", "🟡", "🧱", "🧱", "🧱", "🟡", "🧱"],
    ["🧱", "🟡", "🧱", "🟡", "🟡", "🟡", "🟡", "🟡", "🧱", "🟡", "🧱"],
    ["🧱", "🟡", "🧱", "🧱", "🧱", "🧱", "🧱", "🟡", "🧱", "🟡", "🧱"],
    ["🧱", "🟡", "🟡", "🟡", "👻", "🟡", "🟡", "🟡", "👻", "🟡", "🧱"],
    ["🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱", "🧱"],
]

def init_game():
    st.session_state.pacman_pos = [1, 1]
    st.session_state.ghosts = [[5, 4], [5, 8]]
    st.session_state.score = 0
    st.session_state.game_over = False
    st.session_state.won = False
    
    # Copy maze items
    food_set = set()
    fruits_set = set()
    walls_set = set()
    
    for r in range(len(INITIAL_MAZE)):
        for c in range(len(INITIAL_MAZE[0])):
            item = INITIAL_MAZE[r][c]
            if item == "🧱":
                walls_set.add((r, c))
            elif item == "🟡":
                food_set.add((r, c))
            elif item == "🍇":
                fruits_set.add((r, c))
                
    st.session_state.walls = walls_set
    st.session_state.foods = food_set
    st.session_state.fruits = fruits_set

if "pacman_pos" not in st.session_state:
    init_game()

def move_pacman(dr, dc):
    if st.session_state.game_over or st.session_state.won:
        return
        
    pr, pc = st.session_state.pacman_pos
    nr, nc = pr + dr, pc + dc
    
    # Check wall collision
    if (nr, nc) in st.session_state.walls:
        return
        
    st.session_state.pacman_pos = [nr, nc]
    
    # Check food consumption
    if (nr, nc) in st.session_state.foods:
        st.session_state.foods.remove((nr, nc))
        st.session_state.score += 10
    elif (nr, nc) in st.session_state.fruits:
        st.session_state.fruits.remove((nr, nc))
        st.session_state.score += 50
        
    # Check win condition
    if len(st.session_state.foods) == 0 and len(st.session_state.fruits) == 0:
        st.session_state.won = True
        return

    # Move Ghosts
    new_ghosts = []
    for gr, gc in st.session_state.ghosts:
        possible_moves = []
        for gdr, gdc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            gnr, gnc = gr + gdr, gc + gdc
            if (gnr, gnc) not in st.session_state.walls:
                possible_moves.append([gnr, gnc])
        if possible_moves:
            # Move towards Pacman with some randomness
            possible_moves.sort(key=lambda pos: abs(pos[0] - nr) + abs(pos[1] - nc))
            chosen = possible_moves[0] if random.random() < 0.7 else random.choice(possible_moves)
            new_ghosts.append(chosen)
        else:
            new_ghosts.append([gr, gc])
            
    st.session_state.ghosts = new_ghosts
    
    # Check ghost collision
    for gr, gc in st.session_state.ghosts:
        if [gr, gc] == st.session_state.pacman_pos:
            st.session_state.game_over = True
            break

# UI Header Metrics
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("目前得分 Score", st.session_state.score)
with col_m2:
    st.metric("剩餘豆豆 Food Left", len(st.session_state.foods) + len(st.session_state.fruits))
with col_m3:
    if st.button("🔄 重新開始遊戲 (Reset)", use_container_width=True):
        init_game()
        st.rerun()

st.divider()

# Game Status Banners
if st.session_state.game_over:
    st.error("💀 小精靈被幽靈抓到了！ Game Over！按「重新開始」再挑戰一次！")
elif st.session_state.won:
    st.balloons()
    st.success("🎉 恭喜通關！成功吃完所有迷宮豆豆與水果！🏆")

# Render Maze Grid
rows = len(INITIAL_MAZE)
cols = len(INITIAL_MAZE[0])

grid_display = []
for r in range(rows):
    row_chars = []
    for c in range(cols):
        pos = (r, c)
        if [r, c] == st.session_state.pacman_pos:
            row_chars.append("😃" if not st.session_state.game_over else "💥")
        elif [r, c] in st.session_state.ghosts:
            row_chars.append("👻")
        elif pos in st.session_state.walls:
            row_chars.append("🧱")
        elif pos in st.session_state.fruits:
            row_chars.append("🍇")
        elif pos in st.session_state.foods:
            row_chars.append("🟡")
        else:
            row_chars.append("⬛")
    grid_display.append(" ".join(row_chars))

maze_html = "<div style='font-family: monospace; font-size: 26px; line-height: 1.3; background-color: #0E1117; padding: 16px; border-radius: 12px; display: inline-block; text-align: center; font-weight: bold; border: 2px solid #334155;'>" + "<br/>".join(grid_display) + "</div>"

c_left, c_right = st.columns([1.2, 1.0])

with c_left:
    st.markdown("### 🗺️ 迷宮地圖 (Interactive Map)")
    st.markdown(maze_html, unsafe_allow_html=True)

with c_right:
    st.markdown("### 🎮 方向控制器 (D-Pad)")
    st.caption("點擊箭頭按鈕操控小精靈移動並避開幽靈 👻：")
    
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u2:
        if st.button("⬆️ 向上", use_container_width=True, disabled=st.session_state.game_over or st.session_state.won):
            move_pacman(-1, 0)
            st.rerun()
            
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        if st.button("⬅️ 向左", use_container_width=True, disabled=st.session_state.game_over or st.session_state.won):
            move_pacman(0, -1)
            st.rerun()
    with col_l3:
        if st.button("➡️ 向右", use_container_width=True, disabled=st.session_state.game_over or st.session_state.won):
            move_pacman(0, 1)
            st.rerun()
            
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d2:
        if st.button("⬇️ 向下", use_container_width=True, disabled=st.session_state.game_over or st.session_state.won):
            move_pacman(1, 0)
            st.rerun()
            
    st.markdown("---")
    st.info("💡 **遊戲玩法說明：**\n- 😃 小精靈：由你操作移動\n- 🟡 金黃小豆：+10 分\n- 🍇 能量水果：+50 分\n- 👻 巡邏幽靈：碰觸到會 Game Over")
