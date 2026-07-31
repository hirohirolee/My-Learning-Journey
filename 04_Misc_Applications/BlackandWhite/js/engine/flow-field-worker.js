/**
 * ============================================================================
 * 模組 B：背景 Worker 演算法腳本 (flow-field-worker.js)
 * 在獨立 CPU 核心執行：流場尋路整合場、熱度圖擴散與威脅衰減
 * 採用零拷貝 (Transferable Objects) 回傳主執行緒，避免 UI 序列化延遲
 * ============================================================================
 */

let gridCols = 100;
let gridRows = 100;
let costField = new Uint8Array(gridCols * gridRows);  // 障礙物代價 (255 表示不可通行不可破壞)
let intField  = new Uint32Array(gridCols * gridRows); // 整合距離代價場
let flowX     = new Float32Array(gridCols * gridRows); // X 向量場
let flowY     = new Float32Array(gridCols * gridRows); // Y 向量場
let threatMap = new Float32Array(gridCols * gridRows); // 戰略威脅與恐慌熱度圖

self.onmessage = function(e) {
    const { type, data } = e.data;

    if (type === 'INIT_GRID') {
        gridCols = data.cols;
        gridRows = data.rows;
        costField = new Uint8Array(gridCols * gridRows);
        intField  = new Uint32Array(gridCols * gridRows);
        flowX     = new Float32Array(gridCols * gridRows);
        flowY     = new Float32Array(gridCols * gridRows);
        threatMap = new Float32Array(gridCols * gridRows);
        if (data.obstacles) costField.set(data.obstacles);
    } 
    else if (type === 'UPDATE_FLOW_FIELD') {
        // 計算流場 (例如玩家下達 RTS 攻擊的敵方城堡網格 X, Y)
        computeIntegrationField(data.targetX, data.targetY);
        computeVectorField();
        
        // 採用零拷貝 (Transferable) 將計算完畢的流場回傳主執行緒
        const outX = new Float32Array(flowX);
        const outY = new Float32Array(flowY);
        self.postMessage({ type: 'FLOW_FIELD_READY', flowX: outX, flowY: outY }, [outX.buffer, outY.buffer]);
    }
    else if (type === 'INJECT_THREAT_AND_DECAY') {
        // 注入威脅源 (如：神獸跺腳、毀滅神蹟砸落、敵方大軍集結點)
        if (data.injections && data.injections.length > 0) {
            for (let i = 0; i < data.injections.length; i++) {
                const inj = data.injections[i];
                const idx = inj.y * gridCols + inj.x;
                if (idx >= 0 && idx < threatMap.length) {
                    threatMap[idx] = Math.min(1000, threatMap[idx] + inj.value);
                }
            }
        }
        
        // 執行威脅熱度圖的高斯擴散 (Gaussian Diffusion) 與自然衰減 (Decay)
        diffuseAndDecayThreatMap(data.dt || 0.1);

        // 回傳熱度圖供主執行緒觸發「平民恐慌 AI」與「視覺/聽覺號角預警」
        const outThreat = new Float32Array(threatMap);
        self.postMessage({ type: 'THREAT_MAP_READY', threatMap: outThreat }, [outThreat.buffer]);
    }
};

/**
 * Dijkstra 整合代價場計算 (Integration Field)
 */
function computeIntegrationField(targetX, targetY) {
    intField.fill(4294967295); // Infinity
    const targetIdx = targetY * gridCols + targetX;
    if (targetIdx < 0 || targetIdx >= intField.length) return;
    
    intField[targetIdx] = 0;
    const queue = [targetIdx];
    let head = 0;

    const neighbors = [-1, 1, -gridCols, gridCols]; // 左、右、上、下
    while (head < queue.length) {
        const curr = queue[head++];
        const currCost = intField[curr];

        for (let i = 0; i < 4; i++) {
            const offset = neighbors[i];
            const next = curr + offset;
            if (next < 0 || next >= intField.length) continue;
            
            // 邊界跨越檢查 (防止從最右一列穿越到下一列的最左一列)
            if (offset === -1 && (curr % gridCols === 0)) continue;
            if (offset === 1 && (next % gridCols === 0)) continue;
            if (costField[next] === 255) continue; // 撞牆或地形阻擋

            const newCost = currCost + (costField[next] || 1);
            if (newCost < intField[next]) {
                intField[next] = newCost;
                queue.push(next);
            }
        }
    }
}

/**
 * 方向向量場計算 (Vector Field) - 尋找周圍一格中 intField 數值最小的方向
 */
function computeVectorField() {
    for (let y = 1; y < gridRows - 1; y++) {
        for (let x = 1; x < gridCols - 1; x++) {
            const idx = y * gridCols + x;
            if (costField[idx] === 255) {
                flowX[idx] = 0;
                flowY[idx] = 0;
                continue;
            }

            // 取得上下左右的代價場差值 (Gradient)
            const left   = intField[idx - 1];
            const right  = intField[idx + 1];
            const top    = intField[idx - gridCols];
            const bottom = intField[idx + gridCols];

            let dx = 0, dy = 0;
            if (left < 4294967295 && right < 4294967295) dx = left - right;
            else if (left < 4294967295) dx = 1;
            else if (right < 4294967295) dx = -1;

            if (top < 4294967295 && bottom < 4294967295) dy = top - bottom;
            else if (top < 4294967295) dy = 1;
            else if (bottom < 4294967295) dy = -1;

            const len = Math.hypot(dx, dy);
            if (len > 0.0001) {
                flowX[idx] = dx / len;
                flowY[idx] = dy / len;
            } else {
                flowX[idx] = 0;
                flowY[idx] = 0;
            }
        }
    }
}

/**
 * 戰略威脅熱度圖擴散與衰減 (模擬大軍壓境時的塵土與恐慌傳播)
 */
function diffuseAndDecayThreatMap(dt) {
    const nextMap = new Float32Array(threatMap.length);
    const decayFactor = Math.pow(0.85, dt * 10); // 隨時間自然衰減

    for (let y = 1; y < gridRows - 1; y++) {
        for (let x = 1; x < gridCols - 1; x++) {
            const idx = y * gridCols + x;
            // 九宮格均值擴散
            const avg = (
                threatMap[idx] * 4 +
                threatMap[idx - 1] + threatMap[idx + 1] +
                threatMap[idx - gridCols] + threatMap[idx + gridCols]
            ) / 8;
            nextMap[idx] = avg * decayFactor;
        }
    }
    threatMap.set(nextMap);
}
