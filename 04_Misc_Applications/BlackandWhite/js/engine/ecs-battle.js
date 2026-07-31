/**
 * ============================================================================
 * 商業級 ECS 戰場引擎核心 (ECSBattleEngine & SpatialHashGrid)
 * 基於 TypedArray 連續記憶體佈局，專為千人同屏肉搏、老兵狀態計算與快取優化打造
 * ============================================================================
 */

/**
 * 輕量級空間加速網格 (Spatial Hash Grid)
 * 用於將 O(N^2) 的單位間索敵和避障查詢時間降至 O(1) ~ O(K)
 */
export class SpatialHashGrid {
    constructor(width = 4000, height = 4000, cellSize = 60) {
        this.width = width;
        this.height = height;
        this.cellSize = cellSize;
        this.cols = Math.ceil(width / cellSize);
        this.rows = Math.ceil(height / cellSize);
        this.grid = new Map(); // Key: cellIndex, Value: Array of entity IDs
    }

    clear() {
        this.grid.clear();
    }

    insert(id, x, y) {
        const cx = Math.floor(x / this.cellSize);
        const cy = Math.floor(y / this.cellSize);
        if (cx < 0 || cx >= this.cols || cy < 0 || cy >= this.rows) return;
        const idx = cy * this.cols + cx;
        let cell = this.grid.get(idx);
        if (!cell) {
            cell = [];
            this.grid.set(idx, cell);
        }
        cell.push(id);
    }

    /**
     * 尋找半徑內最近的敵對陣營實體 ID
     */
    findNearestEnemy(x, y, radius, myFaction, ecs) {
        const cx = Math.floor(x / this.cellSize);
        const cy = Math.floor(y / this.cellSize);
        const cellRadius = Math.ceil(radius / this.cellSize);
        const radiusSq = radius * radius;

        let nearestId = -1;
        let minDistSq = radiusSq;

        for (let dy = -cellRadius; dy <= cellRadius; dy++) {
            const ny = cy + dy;
            if (ny < 0 || ny >= this.rows) continue;
            for (let dx = -cellRadius; dx <= cellRadius; dx++) {
                const nx = cx + dx;
                if (nx < 0 || nx >= this.cols) continue;
                const idx = ny * this.cols + nx;
                const cell = this.grid.get(idx);
                if (!cell) continue;

                for (let i = 0; i < cell.length; i++) {
                    const targetId = cell[i];
                    if (ecs.faction[targetId] === myFaction) continue;
                    if (ecs.state[targetId] === 4) continue; // 死亡

                    const distSq = (x - ecs.posX[targetId]) ** 2 + (y - ecs.posY[targetId]) ** 2;
                    if (distSq < minDistSq) {
                        minDistSq = distSq;
                        nearestId = targetId;
                    }
                }
            }
        }
        return nearestId;
    }
}

/**
 * 實體組件引擎主體 (Struct of Arrays 架構)
 */
export class ECSBattleEngine {
    constructor(maxEntities = 2048) {
        this.maxEntities = maxEntities;
        this.activeCount = 0;
        
        // 實體 ID 回收池 (Free List)，避免 GC
        this.freeIds = [];
        for (let i = maxEntities - 1; i >= 0; i--) {
            this.freeIds.push(i);
        }

        // ====================================================================
        // SoA (Struct of Arrays) 記憶體映射表 (Float32Array / Int32Array)
        // ====================================================================
        this.posX       = new Float32Array(maxEntities); // X 座標
        this.posY       = new Float32Array(maxEntities); // Y 座標
        this.velX       = new Float32Array(maxEntities); // X 速度
        this.velY       = new Float32Array(maxEntities); // Y 速度
        this.hp         = new Float32Array(maxEntities); // 當前血量
        this.maxHp      = new Float32Array(maxEntities); // 最大血量
        this.attack     = new Float32Array(maxEntities); // 攻擊力 (受老兵加成)
        this.defense    = new Float32Array(maxEntities); // 防禦力
        this.morale     = new Float32Array(maxEntities); // 士氣值 (0~100, 低於20恐慌)
        
        this.faction    = new Int32Array(maxEntities);   // 陣營: 0(玩家), 1(古挪威), 2(日本), 3(阿茲特克)
        this.unitType   = new Int32Array(maxEntities);   // 兵種: 0(徵召兵), 1(劍士), 2(弓手), 3(騎兵)
        this.veteranLvl = new Int32Array(maxEntities);   // 老兵等級 (0~5, 提升戰鬥與生存率)
        this.state      = new Int32Array(maxEntities);   // 狀態: 0(閒置), 1(行軍), 2(攻擊), 3(恐慌逃竄), 4(死亡)
        this.targetId   = new Int32Array(maxEntities);   // 鎖定目標 ID (-1 表示無)
        this.atkCooldown= new Float32Array(maxEntities); // 攻擊冷卻時間 (秒)
        this.lodLevel   = new Int32Array(maxEntities);   // 當前 LOD 級別: 0(高頻60Hz), 1(中頻15Hz), 2(低頻2Hz), 3(剔除)

        this.spatialGrid = new SpatialHashGrid(4000, 4000, 60);
    }

    /**
     * 動態擴容 TypedArray 記憶體池 (避免實體溢位風險)
     */
    reallocateSoABuffer(newCapacity) {
        console.log(`📈 [ECSBattleEngine] 觸發動態擴容，實體容量由 ${this.maxEntities} 擴展至 ${newCapacity}...`);
        const oldMax = this.maxEntities;
        this.maxEntities = newCapacity;

        for (let i = newCapacity - 1; i >= oldMax; i--) {
            this.freeIds.push(i);
        }

        const reallocFloat = (oldArr) => {
            const newArr = new Float32Array(newCapacity);
            newArr.set(oldArr);
            return newArr;
        };
        const reallocInt = (oldArr) => {
            const newArr = new Int32Array(newCapacity);
            newArr.set(oldArr);
            return newArr;
        };

        this.posX        = reallocFloat(this.posX);
        this.posY        = reallocFloat(this.posY);
        this.velX        = reallocFloat(this.velX);
        this.velY        = reallocFloat(this.velY);
        this.hp          = reallocFloat(this.hp);
        this.maxHp       = reallocFloat(this.maxHp);
        this.attack      = reallocFloat(this.attack);
        this.defense     = reallocFloat(this.defense);
        this.morale      = reallocFloat(this.morale);
        this.atkCooldown = reallocFloat(this.atkCooldown);

        this.faction     = reallocInt(this.faction);
        this.unitType    = reallocInt(this.unitType);
        this.veteranLvl  = reallocInt(this.veteranLvl);
        this.state       = reallocInt(this.state);
        this.targetId    = reallocInt(this.targetId);
        this.lodLevel    = reallocInt(this.lodLevel);

        if (window.gameInstance && window.gameInstance.lodRenderer) {
            window.gameInstance.lodRenderer.reallocateBuffer(newCapacity);
        }
    }

    /**
     * 建立新的戰略單位
     */
    spawnUnit(x, y, faction = 0, unitType = 1, veteranLvl = 0) {
        if (this.freeIds.length === 0) {
            this.reallocateSoABuffer(this.maxEntities * 2);
        }
        const id = this.freeIds.pop();
        this.activeCount++;

        this.posX[id] = x;
        this.posY[id] = y;
        this.velX[id] = 0;
        this.velY[id] = 0;
        this.faction[id] = faction;
        this.unitType[id] = unitType;
        this.veteranLvl[id] = veteranLvl;
        this.state[id] = 0; // 閒置
        this.targetId[id] = -1;
        this.atkCooldown[id] = 0;
        this.lodLevel[id] = 0;

        // 老兵數值乘數：世代從軍者體能與武技大幅加強
        const vetBonus = 1.0 + veteranLvl * 0.35;
        const baseHp = unitType === 0 ? 40 : (unitType === 1 ? 80 : (unitType === 2 ? 60 : 120));
        const baseAtk = unitType === 0 ? 5 : (unitType === 1 ? 14 : (unitType === 2 ? 18 : 22));
        const baseDef = unitType === 0 ? 1 : (unitType === 1 ? 5 : (unitType === 2 ? 2 : 8));

        this.maxHp[id]   = baseHp * vetBonus;
        this.hp[id]      = this.maxHp[id];
        this.attack[id]  = baseAtk * vetBonus;
        this.defense[id] = baseDef * vetBonus;
        this.morale[id]  = Math.min(100, 65 + veteranLvl * 8); // 老兵心理素質強悍

        return id;
    }

    /**
     * 銷毀並回收單位 ID
     */
    destroyUnit(id) {
        if (this.state[id] === 4) return; // 已死亡
        this.state[id] = 4;
        this.freeIds.push(id);
        this.activeCount--;
    }

    /**
     * 清空所有單位
     */
    clear() {
        this.activeCount = 0;
        this.freeIds = [];
        for (let i = this.maxEntities - 1; i >= 0; i--) {
            this.freeIds.push(i);
            this.state[i] = 4;
        }
        this.spatialGrid.clear();
    }

    /**
     * 重建空間網格索引 (在每次物理演算前呼叫)
     */
    rebuildSpatialGrid() {
        this.spatialGrid.clear();
        const len = this.maxEntities;
        for (let i = 0; i < len; i++) {
            if (this.state[i] !== 4 && this.lodLevel[i] < 3) {
                this.spatialGrid.insert(i, this.posX[i], this.posY[i]);
            }
        }
    }

    /**
     * 系統 1：移動與位移更新系統 (Movement System)
     * 支援流場向量讀取、恐慌反向奔跑與 LOD 分層降頻運算
     */
    updateMovementSystem(dt, flowFieldX, flowFieldY, gridCols, cellSize, mapWidth = 3000, mapHeight = 3000) {
        const len = this.maxEntities;
        for (let i = 0; i < len; i++) {
            if (this.state[i] === 4) continue; // 跳過死亡單位

            // LOD 頻率降級控制：中遠距單位跳過部分影格運算以節省 CPU
            if (this.lodLevel[i] === 1 && Math.random() > 0.25) continue; // 15Hz
            if (this.lodLevel[i] === 2 && Math.random() > 0.033) continue; // 2Hz
            if (this.lodLevel[i] === 3) continue; // 視界外剔除

            // 狀態判定：如果處於行軍 (1) 或 恐慌逃竄 (3)，根據流場前進
            if (this.state[i] === 1 || this.state[i] === 3) {
                const cellX = Math.floor(this.posX[i] / cellSize);
                const cellY = Math.floor(this.posY[i] / cellSize);
                const gridIdx = cellY * gridCols + cellX;

                let fx = 0, fy = 0;
                if (flowFieldX && flowFieldY && gridIdx >= 0 && gridIdx < flowFieldX.length) {
                    fx = flowFieldX[gridIdx];
                    fy = flowFieldY[gridIdx];
                } else if (this.state[i] === 1 && this.targetId[i] !== -1 && this.state[this.targetId[i]] !== 4) {
                    // 朝目標追擊
                    const dx = this.posX[this.targetId[i]] - this.posX[i];
                    const dy = this.posY[this.targetId[i]] - this.posY[i];
                    const dist = Math.hypot(dx, dy);
                    if (dist > 1) {
                        fx = dx / dist;
                        fy = dy / dist;
                    }
                }

                // 恐慌逃竄時，往威脅或流場相反方向瘋狂逃離
                if (this.state[i] === 3) {
                    fx = -fx + (Math.random() - 0.5) * 0.8;
                    fy = -fy + (Math.random() - 0.5) * 0.8;
                    const lenSq = Math.hypot(fx, fy);
                    if (lenSq > 0.001) {
                        fx /= lenSq;
                        fy /= lenSq;
                    }
                }

                // 基礎移動速度與 LOD 補償 (降頻計算的影格位移需乘回倍率)
                const baseSpeed = this.state[i] === 3 ? 95 : 55;
                const lodMultiplier = this.lodLevel[i] === 0 ? 1 : (this.lodLevel[i] === 1 ? 4 : 30);
                this.velX[i] = fx * baseSpeed * lodMultiplier;
                this.velY[i] = fy * baseSpeed * lodMultiplier;
            } else if (this.state[i] === 0 || this.state[i] === 2) {
                // 閒置或近戰攻擊中停止位移
                this.velX[i] *= 0.8;
                this.velY[i] *= 0.8;
            }

            // 應用位移並限制邊界
            this.posX[i] += this.velX[i] * dt;
            this.posY[i] += this.velY[i] * dt;

            if (this.posX[i] < 20) this.posX[i] = 20;
            if (this.posX[i] > mapWidth - 20) this.posX[i] = mapWidth - 20;
            if (this.posY[i] < 20) this.posY[i] = 20;
            if (this.posY[i] > mapHeight - 20) this.posY[i] = mapHeight - 20;
        }
    }

    /**
     * 系統 2：近戰肉搏與老兵傷亡結算系統 (Combat System)
     */
    updateCombatSystem(dt) {
        this.rebuildSpatialGrid();
        const len = this.maxEntities;

        for (let i = 0; i < len; i++) {
            if (this.state[i] === 4 || this.lodLevel[i] >= 2) continue; // 死亡或遠距單位跳過肉搏

            if (this.atkCooldown[i] > 0) {
                this.atkCooldown[i] -= dt;
            }

            // 士氣崩潰檢查 (士氣極低則轉為恐慌逃亡)
            if (this.morale[i] <= 20 && this.state[i] !== 3) {
                this.state[i] = 3; // 恐慌
                this.targetId[i] = -1;
                continue;
            }

            // 尋找目標或對當前目標進攻
            let target = this.targetId[i];
            if (target === -1 || this.state[target] === 4 || this.faction[target] === this.faction[i]) {
                // 利用空間網格尋找 50 像素內的敵人
                target = this.spatialGrid.findNearestEnemy(this.posX[i], this.posY[i], 50, this.faction[i], this);
                this.targetId[i] = target;
            }

            if (target !== -1 && this.state[target] !== 4) {
                const distSq = (this.posX[i] - this.posX[target]) ** 2 + (this.posY[i] - this.posY[target]) ** 2;
                if (distSq <= 1600) { // 40^2 近戰肉搏接觸距離
                    this.state[i] = 2; // 攻擊中
                    this.velX[i] = 0;
                    this.velY[i] = 0;

                    if (this.atkCooldown[i] <= 0) {
                        this.atkCooldown[i] = 1.1 + Math.random() * 0.3; // 攻擊冷卻與隨機波動

                        // 傷害計算公式：老兵享有招架與破甲優勢
                        const rawDmg = Math.max(2, this.attack[i] - this.defense[target] * 0.4);
                        const finalDmg = rawDmg * (0.85 + Math.random() * 0.3);
                        this.hp[target] -= finalDmg;

                        // 每次受擊降低士氣，老兵世代越高士氣抵抗力越強
                        const moraleLoss = Math.max(1, 12 - this.veteranLvl[target] * 2.2);
                        this.morale[target] -= moraleLoss;

                        // 結算死亡與老兵晉升
                        if (this.hp[target] <= 0) {
                            this.destroyUnit(target);
                            this.targetId[i] = -1;
                            this.state[i] = 0; // 回歸閒置
                            this.morale[i] = Math.min(100, this.morale[i] + 25); // 殺敵鼓舞士氣

                            // 戰場演進機制：殺敵後有概率晉升下一世代老兵！
                            if (this.veteranLvl[i] < 5 && Math.random() < 0.4) {
                                this.veteranLvl[i]++;
                                this.attack[i] *= 1.12;
                                this.maxHp[i] *= 1.12;
                                this.hp[i] = Math.min(this.maxHp[i], this.hp[i] + 25);
                            }
                        }
                    }
                } else {
                    // 超出近戰範圍則追擊
                    this.state[i] = 1;
                }
            } else {
                if (this.state[i] === 2) this.state[i] = 0; // 無目標則閒置
            }
        }
    }
}
