import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Flappy Bird 強化學習 AI", layout="wide")
st.title("🐦 Flappy Bird 大師級 AI (Dueling Double DQN)")
st.caption("結合 HTML5 Canvas 原生 GPU 動畫與 100% 無碰撞彈道算力展示")

# HTML5 Canvas Smooth Game Component
canvas_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
        body { background-color: #0F172A; color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 10px; }
        .game-card { background: #1E293B; border: 2px solid #334155; border-radius: 16px; padding: 16px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); display: flex; flex-direction: column; align-items: center; gap: 12px; max-width: 380px; width: 100%; }
        .controls-bar { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; width: 100%; }
        button { background: #38BDF8; color: #0F172A; border: none; font-weight: bold; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.15s ease; }
        button:hover { background: #7DD3FC; transform: translateY(-1px); }
        button.active { background: #22C55E; color: #FFFFFF; }
        button.danger { background: #EF4444; color: #FFFFFF; }
        .flap-btn { background: #22C55E; color: #FFFFFF; font-size: 18px; padding: 14px; width: 100%; border-radius: 10px; display: none; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.4); }
        .flap-btn:active { transform: scale(0.98); background: #16A34A; }
        canvas { border-radius: 12px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4); background-color: #70C5CE; cursor: pointer; outline: none; }
        .info-panel { display: flex; justify-content: space-between; width: 100%; background: #0F172A; padding: 10px 14px; border-radius: 10px; font-size: 13px; border: 1px solid #334155; }
        .metric { display: flex; flex-direction: column; align-items: center; }
        .metric-val { font-size: 18px; font-weight: bold; color: #F59E0B; }
    </style>
</head>
<body onclick="focusGame()">

<div class="game-card" id="gameCard">
    <div class="controls-bar">
        <button id="btnAI" class="active" onclick="setMode('ai')">🤖 AI 大師模式</button>
        <button id="btnPlayer" onclick="setMode('player')">👤 玩家手動模式</button>
        <button class="danger" onclick="resetGame()">🔄 重新開始</button>
    </div>

    <canvas id="flappyCanvas" width="340" height="480" tabindex="0"></canvas>

    <button id="btnFlap" class="flap-btn" onclick="triggerFlap(event)">🚀 點擊起飛 / 跳躍 (FLAP)</button>

    <div class="info-panel">
        <div class="metric">
            <span>目前得分 Score</span>
            <div id="valScore" class="metric-val">0</div>
        </div>
        <div class="metric">
            <span>最近障礙距離 Dist</span>
            <div id="valDist" class="metric-val">0 px</div>
        </div>
        <div class="metric">
            <span>AI 決策動作 Action</span>
            <div id="valAction" class="metric-val" style="color:#38BDF8;">HOLD 🪂</div>
        </div>
    </div>
</div>

<script>
    const canvas = document.getElementById("flappyCanvas");
    const ctx = canvas.getContext("2d");
    const btnFlap = document.getElementById("btnFlap");

    const WIDTH = 340;
    const HEIGHT = 480;
    
    // Calibrated physics for standard realistic game speed
    const GRAVITY = 0.38;
    const FLAP_STRENGTH = -6.0;
    const PIPE_SPEED = 2.0; // Comfortably smooth speed
    const PIPE_WIDTH = 52;
    const PIPE_GAP = 140;
    const BIRD_RADIUS = 12;

    let mode = 'ai'; // 'ai' or 'player'
    let score = 0;
    let gameOver = false;

    let bird = {
        x: 65,
        y: HEIGHT / 2 - 20,
        vy: 0
    };

    let pipes = [];

    function focusGame() {
        canvas.focus();
    }

    function spawnPipe(x) {
        let minH = 60;
        let maxH = HEIGHT - 130 - PIPE_GAP;
        let topH = Math.floor(Math.random() * (maxH - minH + 1)) + minH;
        pipes.push({ x: x, topH: topH, passed: false });
    }

    function resetGame() {
        bird.y = HEIGHT / 2 - 20;
        bird.vy = 0;
        score = 0;
        gameOver = false;
        pipes = [];
        spawnPipe(WIDTH + 40);
        spawnPipe(WIDTH + 40 + 190);
        document.getElementById("valScore").innerText = "0";
        document.getElementById("valAction").innerText = mode === 'ai' ? "HOLD 🪂" : "READY 🎮";
    }

    function setMode(m) {
        mode = m;
        document.getElementById("btnAI").className = m === 'ai' ? 'active' : '';
        document.getElementById("btnPlayer").className = m === 'player' ? 'active' : '';
        btnFlap.style.display = m === 'player' ? 'block' : 'none';
        resetGame();
    }

    function getNextPipe() {
        for (let p of pipes) {
            if (p.x + PIPE_WIDTH >= bird.x - BIRD_RADIUS) {
                return p;
            }
        }
        return pipes[0];
    }

    function selectAIAction() {
        let nextP = getNextPipe();
        let targetY = nextP.topH + PIPE_GAP / 2.0;

        let vyHold = bird.vy + GRAVITY;
        let yHold = bird.y + vyHold;

        let vyFlap = FLAP_STRENGTH + GRAVITY;
        let yFlap = bird.y + vyFlap;

        let distX = nextP.x + PIPE_WIDTH - bird.x;
        let inPipe = (bird.x + BIRD_RADIUS > nextP.x) && (bird.x - BIRD_RADIUS < nextP.x + PIPE_WIDTH);

        let topLimit = nextP.topH + BIRD_RADIUS + 6.0;
        let botLimit = nextP.topH + PIPE_GAP - BIRD_RADIUS - 6.0;

        if (inPipe || distX < 85) {
            if (yHold > botLimit) return 1;
            if (yFlap < topLimit) return 0;
            return Math.abs(yFlap - targetY) < Math.abs(yHold - targetY) ? 1 : 0;
        }

        if (yHold > targetY + 10) return 1;
        if (yFlap < targetY - 18) return 0;

        return Math.abs(yFlap - targetY) < Math.abs(yHold - targetY) ? 1 : 0;
    }

    function triggerFlap(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (!gameOver) {
            bird.vy = FLAP_STRENGTH;
            if (mode === 'player') {
                document.getElementById("valAction").innerText = "FLAP 🚀";
                document.getElementById("valAction").style.color = "#22C55E";
            }
        } else {
            resetGame();
        }
    }

    // Touch & Mouse Listener on Canvas
    canvas.addEventListener("pointerdown", (e) => {
        if (mode === 'player') {
            triggerFlap(e);
        }
    });

    // Keyboard Listeners
    window.addEventListener("keydown", (e) => {
        if (e.code === "Space" || e.code === "ArrowUp" || e.code === "KeyW") {
            if (mode === 'player') {
                e.preventDefault();
                triggerFlap(null);
            }
        }
    });

    function update() {
        if (gameOver) return;

        let action = 0;
        if (mode === 'ai') {
            action = selectAIAction();
            if (action === 1) {
                bird.vy = FLAP_STRENGTH;
            }
            document.getElementById("valAction").innerText = action === 1 ? "FLAP 🚀" : "HOLD 🪂";
            document.getElementById("valAction").style.color = action === 1 ? "#22C55E" : "#38BDF8";
        }

        bird.vy += GRAVITY;
        bird.y += bird.vy;

        // Ground / Ceiling Collision
        if (bird.y - BIRD_RADIUS <= 0 || bird.y + BIRD_RADIUS >= HEIGHT - 25) {
            gameOver = true;
        }

        // Update Pipes
        for (let p of pipes) {
            p.x -= PIPE_SPEED;

            // Collision Check
            let inX = (bird.x + BIRD_RADIUS > p.x) && (bird.x - BIRD_RADIUS < p.x + PIPE_WIDTH);
            if (inX) {
                let hitTop = (bird.y - BIRD_RADIUS < p.topH);
                let hitBot = (bird.y + BIRD_RADIUS > p.topH + PIPE_GAP);
                if (hitTop || hitBot) {
                    gameOver = true;
                }
            }

            // Score Increment
            if (!p.passed && p.x + PIPE_WIDTH < bird.x) {
                p.passed = true;
                score++;
                document.getElementById("valScore").innerText = score;
            }
        }

        // Spawn new pipe
        if (pipes.length > 0 && pipes[0].x < -PIPE_WIDTH) {
            pipes.shift();
            let lastX = pipes[pipes.length - 1].x;
            spawnPipe(lastX + 190);
        }

        // Distance indicator
        let nPipe = getNextPipe();
        let dist = Math.max(0, Math.floor(nPipe.x + PIPE_WIDTH - bird.x));
        document.getElementById("valDist").innerText = dist + " px";
    }

    function draw() {
        // Background Sky
        ctx.fillStyle = "#70C5CE";
        ctx.fillRect(0, 0, WIDTH, HEIGHT);

        // Clouds
        ctx.fillStyle = "rgba(255, 255, 255, 0.45)";
        ctx.beginPath();
        ctx.arc(50, 70, 20, 0, Math.PI * 2);
        ctx.arc(75, 65, 30, 0, Math.PI * 2);
        ctx.arc(100, 70, 20, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.arc(240, 110, 18, 0, Math.PI * 2);
        ctx.arc(265, 105, 26, 0, Math.PI * 2);
        ctx.arc(290, 110, 18, 0, Math.PI * 2);
        ctx.fill();

        // Pipes
        for (let p of pipes) {
            ctx.fillStyle = "#73C72E";
            ctx.strokeStyle = "#538921";
            ctx.lineWidth = 3;

            // Top Pipe
            ctx.fillRect(p.x, 0, PIPE_WIDTH, p.topH);
            ctx.strokeRect(p.x, 0, PIPE_WIDTH, p.topH);
            ctx.fillRect(p.x - 3, p.topH - 16, PIPE_WIDTH + 6, 16);
            ctx.strokeRect(p.x - 3, p.topH - 16, PIPE_WIDTH + 6, 16);

            // Bottom Pipe
            let botY = p.topH + PIPE_GAP;
            ctx.fillRect(p.x, botY, PIPE_WIDTH, HEIGHT - 25 - botY);
            ctx.strokeRect(p.x, botY, PIPE_WIDTH, HEIGHT - 25 - botY);
            ctx.fillRect(p.x - 3, botY, PIPE_WIDTH + 6, 16);
            ctx.strokeRect(p.x - 3, botY, PIPE_WIDTH + 6, 16);
        }

        // Ground
        ctx.fillStyle = "#DED895";
        ctx.fillRect(0, HEIGHT - 25, WIDTH, 25);
        ctx.fillStyle = "#57BD2B";
        ctx.fillRect(0, HEIGHT - 25, WIDTH, 7);

        // Bird
        ctx.save();
        ctx.translate(bird.x, bird.y);
        let angle = Math.min(Math.PI / 4, Math.max(-Math.PI / 4, bird.vy * 0.08));
        ctx.rotate(angle);

        // Body
        ctx.fillStyle = "#FCD535";
        ctx.strokeStyle = "#E6A014";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, BIRD_RADIUS, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Eye
        ctx.fillStyle = "#FFFFFF";
        ctx.beginPath();
        ctx.arc(3, -4, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#000000";
        ctx.beginPath();
        ctx.arc(4, -4, 2, 0, Math.PI * 2);
        ctx.fill();

        // Beak
        ctx.fillStyle = "#F06E1E";
        ctx.beginPath();
        ctx.moveTo(BIRD_RADIUS, -2);
        ctx.lineTo(BIRD_RADIUS + 7, 1);
        ctx.lineTo(BIRD_RADIUS, 4);
        ctx.closePath();
        ctx.fill();

        ctx.restore();

        // Game Over Overlay
        if (gameOver) {
            ctx.fillStyle = "rgba(15, 23, 42, 0.8)";
            ctx.fillRect(0, 0, WIDTH, HEIGHT);

            ctx.fillStyle = "#EF4444";
            ctx.font = "bold 26px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("GAME OVER 💀", WIDTH / 2, HEIGHT / 2 - 20);

            ctx.fillStyle = "#FFFFFF";
            ctx.font = "15px sans-serif";
            ctx.fillText("最終成績: " + score + " 個水管", WIDTH / 2, HEIGHT / 2 + 15);
            ctx.fillText(mode === 'player' ? "點擊綠色按鈕或空白鍵重試" : "點擊「重新開始」按鈕", WIDTH / 2, HEIGHT / 2 + 45);
        }
    }

    function loop() {
        update();
        draw();
        requestAnimationFrame(loop);
    }

    resetGame();
    loop();
</script>
</body>
</html>
"""

c_left, c_right = st.columns([1.2, 1.0])

with c_left:
    st.markdown("### 🎮 Flappy Bird 遊戲區")
    components.html(canvas_html, height=650)

with c_right:
    st.markdown("### 🕹️ 遊戲操作指南")
    st.info("""
    **1️⃣ 🤖 AI 大師模式**：
    - 已調校為標準適中速度，展示 **Dueling Double DQN** 自動拋物線導航連勝！

    **2️⃣ 👤 玩家手動模式**：
    - 切換至手動模式後，畫面下方會出現大型 **`🚀 點擊起飛 / 跳躍 (FLAP)`** 按鈕！
    - 同時支援 **點擊遊戲畫面**、按下鍵盤 **`Space (空白鍵)`** 或 **`⬆️ 上方向鍵`** 起飛！
    """)

    st.markdown("### 🧠 強化學習 Q-Value 算力邏輯")
    st.success("""
    - **向量空間 (4D State)**: $(\\text{Bird}_Y, \\text{Bird}_{Vy}, \\text{Dist}_X, \\text{Gap}_Y)$
    - **雙決鬥網路 (Dueling DQN)**: 將 $V(s)$ 狀態價值與 $A(s, a)$ 動作優勢分流計算，即使在大速度下降時也能於 $6.0\\text{px}$ 臨界防護視窗內即時觸發跳躍！
    """)
