/**
 * ============================================================================
 * 模組 C：千人同屏實體化渲染與 LOD 剔除管理器 (BattleRendererLOD)
 * 整合：攝影機視界剔除 (Frustum Culling)、3 級 LOD 動態分類、2D Canvas 批次渲染優化
 * 與 WebGL Instancing 資料緩衝區生成
 * ============================================================================
 */
export class BattleRendererLOD {
    constructor(glContext = null, maxInstances = 2048) {
        this.gl = glContext;
        this.maxInstances = maxInstances;
        
        // 實體化渲染資料緩衝 (每一筆 8 個浮點數: [posX, posY, rotation, scale, animFrame, faction, unitType, hpRatio])
        this.instanceData = new Float32Array(maxInstances * 8);
        this.instanceCount = 0;
        
        // 渲染效能統計面板，可用於 UI 遙測與 FPS 診斷
        this.stats = { lod0: 0, lod1: 0, lod2: 0, culled: 0, drawCalls: 0 };
        
        // 陣營主題配色表: 玩家(天藍), 古挪威(深紅), 日本(金黃), 阿茲特克(翠綠)
        this.factionColors = ['#38bdf8', '#ef4444', '#facc15', '#22c55e'];
        this.factionBorderColors = ['#0284c7', '#991b1b', '#ca8a04', '#15803d'];
    }

    /**
     * 動態擴容 GPU/Canvas 實體化渲染緩衝
     */
    reallocateBuffer(newMaxInstances) {
        if (newMaxInstances <= this.maxInstances) return;
        console.log(`🖼️ [BattleRendererLOD] 渲染緩衝區同步擴容至 ${newMaxInstances} 實體...`);
        const oldData = this.instanceData;
        this.maxInstances = newMaxInstances;
        this.instanceData = new Float32Array(newMaxInstances * 8);
        this.instanceData.set(oldData);
    }

    /**
     * 核心渲染準備：遍歷 ECS 引擎的所有活躍實體，進行 Frustum 剔除與 LOD 分級
     * @param {ECSBattleEngine} ecs - 模組 A 的 ECS 引擎實體
     * @param {Object} camera - 攝影機物件 (需包含 x, y, zoom, 且可取得可見範圍)
     */
    prepareInstanceBufferAndLOD(ecs, camera) {
        this.instanceCount = 0;
        this.stats = { lod0: 0, lod1: 0, lod2: 0, culled: 0, drawCalls: 0 };

        // 取得攝影機視角在世界坐標中的邊界 (外擴 100px 緩衝區避免邊境閃爍)
        const vw = window.innerWidth || 1400;
        const vh = window.innerHeight || 800;
        const zoom = camera.zoom || 1.0;
        const halfW = (vw / zoom) * 0.5 + 100;
        const halfH = (vh / zoom) * 0.5 + 100;
        const minX = camera.x - halfW;
        const maxX = camera.x + halfW;
        const minY = camera.y - halfH;
        const maxY = camera.y + halfH;

        const len = ecs.maxEntities;
        for (let i = 0; i < len; i++) {
            if (ecs.state[i] === 4) continue; // 死亡實體跳過

            const x = ecs.posX[i];
            const y = ecs.posY[i];

            // ================================================================
            // 1. 空間視界剔除 (Frustum Culling)
            // ================================================================
            if (x < minX || x > maxX || y < minY || y > maxY) {
                ecs.lodLevel[i] = 3; // 標記為視界外剔除，底層 AI 降頻至極低或休眠
                this.stats.culled++;
                continue;
            }

            // ================================================================
            // 2. 動態 LOD 級別計算 (基於與攝影機中心點的平方距離與廣角縮放)
            // ================================================================
            const distSq = (x - camera.x) ** 2 + (y - camera.y) ** 2;
            let lod = 0;
            if (distSq > 1200000 || zoom < 0.35) {       // 超遠景或極限廣角
                lod = 2; // 極簡 LOD：渲染雷達色塊/小圓點，AI 2Hz
                this.stats.lod2++;
            } else if (distSq > 300000 || zoom < 0.65) { // 中遠景
                lod = 1; // 中等 LOD：簡化外表與影格，AI 15Hz
                this.stats.lod1++;
            } else {
                lod = 0; // 高精 LOD：細緻武器、骨骼動畫與血條老兵勳章，AI 60Hz
                this.stats.lod0++;
            }
            ecs.lodLevel[i] = lod;

            // ================================================================
            // 3. 填入 GPU / 批次渲染連續記憶體緩衝
            // ================================================================
            const idx = this.instanceCount * 8;
            this.instanceData[idx]     = x;
            this.instanceData[idx + 1] = y;
            this.instanceData[idx + 2] = Math.atan2(ecs.velY[i], ecs.velX[i]); // 運動朝向
            this.instanceData[idx + 3] = lod === 2 ? 0.6 : (1.0 + ecs.veteranLvl[i] * 0.12); // 老兵體型倍增
            this.instanceData[idx + 4] = Math.floor(Date.now() / (lod === 0 ? 60 : 150)) % 8; // 動畫幀數
            this.instanceData[idx + 5] = ecs.faction[i]; // 陣營
            this.instanceData[idx + 6] = ecs.unitType[i]; // 兵種
            this.instanceData[idx + 7] = Math.max(0, ecs.hp[i] / (ecs.maxHp[i] || 1)); // 血量比例

            this.instanceCount++;
        }
    }

    /**
     * 執行 2D Canvas 批次降級渲染 (Canvas 2D Batching Fallback)
     * 將千人方陣按照陣營與 LOD 級別進行繪製指令合併，將 Draw Call 從 1000+ 次壓縮至個位數！
     */
    renderCanvas2DBatch(ctx, time) {
        if (!ctx || this.instanceCount === 0) return;

        ctx.save();
        this.stats.drawCalls = 0;

        // 按照陣營分組批次渲染 (4 個陣營各執行 1 次 Path Merge)
        for (let f = 0; f < 4; f++) {
            ctx.fillStyle = this.factionColors[f];
            ctx.strokeStyle = this.factionBorderColors[f];
            ctx.lineWidth = 1.5;

            // 第一批：繪製單位本體幾何路徑 (所有該陣營實體一次性 ctx.fill)
            ctx.beginPath();
            let hasUnits = false;
            for (let i = 0; i < this.instanceCount; i++) {
                const idx = i * 8;
                if (this.instanceData[idx + 5] !== f) continue;
                
                const x = this.instanceData[idx];
                const y = this.instanceData[idx + 1];
                const scale = this.instanceData[idx + 3];
                const radius = 5 * scale;

                ctx.moveTo(x + radius, y);
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                hasUnits = true;
            }
            if (hasUnits) {
                ctx.fill();
                ctx.stroke();
                this.stats.drawCalls += 2;
            }
        }

        // 第二批：單獨處理 LOD 0/1 的血條與老兵光環 (大幅減少狀態切換)
        ctx.lineWidth = 2;
        for (let i = 0; i < this.instanceCount; i++) {
            const idx = i * 8;
            const x = this.instanceData[idx];
            const y = this.instanceData[idx + 1];
            const scale = this.instanceData[idx + 3];
            const hpRatio = this.instanceData[idx + 7];
            const lod = Math.round(scale === 0.6 ? 2 : (scale > 1.3 ? 0 : 1)); // 概略還原 LOD

            // 僅對近中景 (LOD 0/1) 且受損單位繪製血條
            if (lod <= 1 && hpRatio < 0.98) {
                const bw = 16 * scale;
                const bh = 3;
                const bx = x - bw / 2;
                const by = y - 10 * scale;

                ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
                ctx.fillRect(bx, by, bw, bh);

                ctx.fillStyle = hpRatio > 0.5 ? '#22c55e' : (hpRatio > 0.2 ? '#facc15' : '#ef4444');
                ctx.fillRect(bx, by, bw * hpRatio, bh);
                this.stats.drawCalls += 2;
            }

            // 特效：老兵 (scale > 1.2) 足下發出黃金作戰光圈
            if (scale >= 1.2 && lod === 0) {
                ctx.strokeStyle = 'rgba(250, 204, 21, 0.6)';
                ctx.beginPath();
                ctx.arc(x, y, 9 * scale + Math.sin(time * 6) * 1.5, 0, Math.PI * 2);
                ctx.stroke();
                this.stats.drawCalls++;
            }
        }

        ctx.restore();
    }

    /**
     * WebGL Instancing 渲染接口 (保留給將來 3D / WebGL Shader 著色器對接)
     */
    renderWebGLInstanced(shaderProgram, meshGeometry, glBuffer) {
        if (!this.gl || !this.gl.drawArraysInstanced || this.instanceCount === 0) return;
        const gl = this.gl;
        gl.useProgram(shaderProgram);
        gl.bindBuffer(gl.ARRAY_BUFFER, glBuffer);
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, this.instanceData.subarray(0, this.instanceCount * 8));
        gl.drawArraysInstanced(gl.TRIANGLES, 0, meshGeometry.vertexCount, this.instanceCount);
        this.stats.drawCalls = 1;
    }

    getStats() {
        return this.stats;
    }
}
