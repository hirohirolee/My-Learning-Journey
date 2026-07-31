/**
 * ============================================================================
 * 模組：老兵世代演進與倖存晉升管線 (VeteranEvolution)
 * 監控戰場倖存者與殺敵貢獻，動態升級 veteranLvl (0 -> 5 世傳奇軍神)
 * 並發送 VETERAN_PROMOTED 廣播引發特效與數值倍增
 * ============================================================================
 */

export class VeteranEvolution {
    constructor(ecsEngine) {
        this.ecs = ecsEngine;
        this.scanTimer = 3.0; // 每 3 秒掃描一次戰場倖存演進
    }

    update(dt) {
        if (!this.ecs || this.ecs.activeCount === 0) return;

        this.scanTimer -= dt;
        if (this.scanTimer <= 0) {
            this.scanTimer = 4.0;
            this.performEvolutionScan();
        }
    }

    /**
     * 掃描戰場實體，對參與激烈戰鬥且存活的單位進行世代晉升
     */
    performEvolutionScan() {
        const len = this.ecs.maxEntities;
        let promotedCount = 0;

        for (let i = 0; i < len; i++) {
            if (this.ecs.state[i] === 4) continue; // 死亡跳過
            if (this.ecs.veteranLvl[i] >= 5) continue; // 已達極限傳奇等級

            // 若在近戰鎖定或處於受損倖存狀態，有概率獲得老兵榮譽晉升
            const isFighting = this.ecs.targetId[i] !== -1;
            const isWoundedSurviving = this.ecs.hp[i] < this.ecs.maxHp[i] * 0.85;

            if ((isFighting || isWoundedSurviving) && Math.random() < 0.15) {
                const oldLvl = this.ecs.veteranLvl[i];
                const newLvl = oldLvl + 1;
                this.ecs.veteranLvl[i] = newLvl;

                // 根據配置強化血量與攻擊力
                const vetMult = 1.0 + newLvl * 0.35;
                this.ecs.maxHp[i] *= 1.35;
                this.ecs.hp[i] = this.ecs.maxHp[i]; // 晉升時滿血復活
                this.ecs.attack[i] *= 1.35;
                this.ecs.defense[i] *= 1.35;
                this.ecs.morale[i] = 100; // 士氣狂熱

                promotedCount++;

                // 達標重要階梯 (L3 百戰 / L5 傳奇軍神) 發送全局榮譽特效廣播
                if (newLvl === 3 || newLvl === 5) {
                    window.dispatchEvent(new CustomEvent('VETERAN_PROMOTED', {
                        detail: {
                            x: this.ecs.posX[i],
                            y: this.ecs.posY[i],
                            faction: this.ecs.faction[i],
                            level: newLvl
                        }
                    }));
                }
            }
        }

        if (promotedCount > 0) {
            console.log(`🎖️ [VeteranEvolution] 戰場激鬥演進！本次共 ${promotedCount} 名戰士倖存晉升為更高階老兵！`);
        }
    }

    /**
     * 主控台與企劃驗證專用：立刻將所有玩家陣營單位晉升至極限傳奇老兵 (L5)！
     */
    promoteAllPlayerUnits(targetLvl = 5) {
        if (!this.ecs) return;
        const len = this.ecs.maxEntities;
        let count = 0;

        for (let i = 0; i < len; i++) {
            if (this.ecs.state[i] === 4) continue;
            if (this.ecs.faction[i] === 0) { // 玩家陣營
                this.ecs.veteranLvl[i] = targetLvl;
                this.ecs.maxHp[i] = 300;
                this.ecs.hp[i] = 300;
                this.ecs.attack[i] = 45;
                this.ecs.defense[i] = 20;
                this.ecs.morale[i] = 100;
                count++;
            }
        }

        console.log(`⚡ [VeteranEvolution] 神蹟恩賜！全場 ${count} 名玩家部隊立刻晉升為【五世傳奇軍神 (L5)】！`);
        window.dispatchEvent(new CustomEvent('VETERAN_PROMOTED', {
            detail: { x: 1000, y: 1000, faction: 0, level: targetLvl, mass: true }
        }));
    }
}
