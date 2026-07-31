/**
 * ============================================================================
 * 模組 B：主執行緒 Worker 通信橋樑與熱度廣播處理 (FlowFieldManager)
 * 負責在主執行緒與後台 Web Worker 之間傳遞零拷貝陣列與處理威脅預警事件
 * ============================================================================
 */

export class FlowFieldManager {
    constructor(gridCols = 100, gridRows = 100, cellSize = 40) {
        this.gridCols = gridCols;
        this.gridRows = gridRows;
        this.cellSize = cellSize;
        
        this.flowX = new Float32Array(gridCols * gridRows);
        this.flowY = new Float32Array(gridCols * gridRows);
        this.threatMap = new Float32Array(gridCols * gridRows);
        
        this.pendingInjections = [];
        this.initWorker();
    }

    /**
     * 初始化 Web Worker，並內建 CORS/本地 File 協議的 Inline Blob 降級方案
     */
    initWorker() {
        try {
            this.worker = new Worker('./js/engine/flow-field-worker.js');
        } catch (e) {
            console.warn("⚠️ [FlowFieldManager] 外部 Worker 檔案載入失敗，切換至 Inline Blob Worker 模式:", e);
            const blobCode = `
                let gridCols = 100, gridRows = 100;
                let costField = new Uint8Array(10000), intField = new Uint32Array(10000);
                let flowX = new Float32Array(10000), flowY = new Float32Array(10000), threatMap = new Float32Array(10000);

                self.onmessage = function(e) {
                    const { type, data } = e.data;
                    if (type === 'INIT_GRID') {
                        gridCols = data.cols; gridRows = data.rows;
                        costField = new Uint8Array(gridCols * gridRows); intField = new Uint32Array(gridCols * gridRows);
                        flowX = new Float32Array(gridCols * gridRows); flowY = new Float32Array(gridCols * gridRows);
                        threatMap = new Float32Array(gridCols * gridRows);
                        if (data.obstacles) costField.set(data.obstacles);
                    } else if (type === 'UPDATE_FLOW_FIELD') {
                        intField.fill(4294967295);
                        const tIdx = data.targetY * gridCols + data.targetX;
                        if (tIdx >= 0 && tIdx < intField.length) {
                            intField[tIdx] = 0;
                            const q = [tIdx]; let head = 0;
                            const nb = [-1, 1, -gridCols, gridCols];
                            while (head < q.length) {
                                const c = q[head++]; const cc = intField[c];
                                for (let offset of nb) {
                                    const n = c + offset;
                                    if (n < 0 || n >= intField.length || costField[n] === 255) continue;
                                    if (offset === -1 && (c % gridCols === 0)) continue;
                                    if (offset === 1 && (n % gridCols === 0)) continue;
                                    const nc = cc + (costField[n] || 1);
                                    if (nc < intField[n]) { intField[n] = nc; q.push(n); }
                                }
                            }
                        }
                        for (let y = 1; y < gridRows - 1; y++) {
                            for (let x = 1; x < gridCols - 1; x++) {
                                const idx = y * gridCols + x;
                                if (costField[idx] === 255) { flowX[idx] = 0; flowY[idx] = 0; continue; }
                                const l = intField[idx - 1], r = intField[idx + 1], top = intField[idx - gridCols], b = intField[idx + gridCols];
                                let dx = (l < 4294967295 && r < 4294967295) ? l - r : (l < 4294967295 ? 1 : (r < 4294967295 ? -1 : 0));
                                let dy = (top < 4294967295 && b < 4294967295) ? top - b : (top < 4294967295 ? 1 : (b < 4294967295 ? -1 : 0));
                                const len = Math.hypot(dx, dy);
                                if (len > 0.0001) { flowX[idx] = dx / len; flowY[idx] = dy / len; } else { flowX[idx] = 0; flowY[idx] = 0; }
                            }
                        }
                        const ox = new Float32Array(flowX), oy = new Float32Array(flowY);
                        self.postMessage({ type: 'FLOW_FIELD_READY', flowX: ox, flowY: oy }, [ox.buffer, oy.buffer]);
                    } else if (type === 'INJECT_THREAT_AND_DECAY') {
                        if (data.injections) {
                            for (let inj of data.injections) {
                                const idx = inj.y * gridCols + inj.x;
                                if (idx >= 0 && idx < threatMap.length) threatMap[idx] = Math.min(1000, threatMap[idx] + inj.value);
                            }
                        }
                        const nm = new Float32Array(threatMap.length);
                        const df = Math.pow(0.85, (data.dt || 0.1) * 10);
                        for (let y = 1; y < gridRows - 1; y++) {
                            for (let x = 1; x < gridCols - 1; x++) {
                                const idx = y * gridCols + x;
                                const avg = (threatMap[idx] * 4 + threatMap[idx - 1] + threatMap[idx + 1] + threatMap[idx - gridCols] + threatMap[idx + gridCols]) / 8;
                                nm[idx] = avg * df;
                            }
                        }
                        threatMap.set(nm);
                        const ot = new Float32Array(threatMap);
                        self.postMessage({ type: 'THREAT_MAP_READY', threatMap: ot }, [ot.buffer]);
                    }
                };
            `;
            const blob = new Blob([blobCode], { type: 'application/javascript' });
            this.worker = new Worker(URL.createObjectURL(blob));
        }

        this.worker.postMessage({ type: 'INIT_GRID', data: { cols: this.gridCols, rows: this.gridRows } });
        this.setupWorkerListeners();
    }

    setupWorkerListeners() {
        this.worker.onmessage = (e) => {
            const { type, flowX, flowY, threatMap } = e.data;
            if (type === 'FLOW_FIELD_READY') {
                this.flowX = flowX;
                this.flowY = flowY;
            } else if (type === 'THREAT_MAP_READY') {
                this.threatMap = threatMap;
                this.evaluateGlobalPanicAndWarnings();
            }
        };
    }

    /**
     * 下達 RTS 推進指令時調用，在背景非同步更新最優流場
     */
    requestFlowFieldUpdate(targetWorldX, targetWorldY) {
        const targetCellX = Math.floor(targetWorldX / this.cellSize);
        const targetCellY = Math.floor(targetWorldY / this.cellSize);
        if (targetCellX < 0 || targetCellX >= this.gridCols || targetCellY < 0 || targetCellY >= this.gridRows) return;
        this.worker.postMessage({ type: 'UPDATE_FLOW_FIELD', data: { targetX: targetCellX, targetY: targetCellY } });
    }

    /**
     * 當神獸重擊地面、大軍急行軍、毀滅神蹟爆發時呼叫，注入威脅度
     */
    injectThreat(worldX, worldY, value) {
        const x = Math.floor(worldX / this.cellSize);
        const y = Math.floor(worldY / this.cellSize);
        if (x < 0 || x >= this.gridCols || y < 0 || y >= this.gridRows) return;
        this.pendingInjections.push({ x, y, value });
    }

    /**
     * 引擎每幀或定時呼叫：推動 Worker 進行熱度擴散
     */
    tick(dt) {
        this.worker.postMessage({
            type: 'INJECT_THREAT_AND_DECAY',
            data: { dt, injections: this.pendingInjections }
        });
        this.pendingInjections = [];
    }

    /**
     * 查詢指定世界坐標的流場向量與熱度值 (O(1) 時間複雜度)
     */
    queryField(worldX, worldY) {
        const x = Math.floor(worldX / this.cellSize);
        const y = Math.floor(worldY / this.cellSize);
        if (x < 0 || x >= this.gridCols || y < 0 || y >= this.gridRows) {
            return { fx: 0, fy: 0, threat: 0 };
        }
        const idx = y * this.gridCols + x;
        return {
            fx: this.flowX[idx] || 0,
            fy: this.flowY[idx] || 0,
            threat: this.threatMap[idx] || 0
        };
    }

    /**
     * 檢閱全局熱度圖：當某區域威脅度大於閥值，自動觸發 視覺揚沙特效 與 聽覺預警號角！
     */
    evaluateGlobalPanicAndWarnings() {
        if (!this.threatMap) return;
        const len = this.threatMap.length;
        for (let i = 0; i < len; i++) {
            const threat = this.threatMap[i];
            if (threat > 500) { // 極高威脅閥值
                const cellY = Math.floor(i / this.gridCols);
                const cellX = i % this.gridCols;
                const worldX = cellX * this.cellSize;
                const worldY = cellY * this.cellSize;
                
                // 廣播事件給 VFX / SFX 引擎 (觸發戰鬥號角聲與地表塵土)
                window.dispatchEvent(new CustomEvent('BATTLEFIELD_HIGH_THREAT_WARNING', {
                    detail: { x: worldX, y: worldY, threatLevel: threat }
                }));
            }
        }
    }
}
