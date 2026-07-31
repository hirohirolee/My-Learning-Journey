import { TroopEntity } from './troop.js?v=3';

/**
 * 村莊中心與祭壇統治系統 (Village Center & Altar Dominance - SimCity vs Age of Empires)
 * 統計人口、食物/木材庫存、信仰度 (0~100%)、祭壇能量與領域邊界擴張
 * 善與惡2專屬：包含城市繁榮度(Prosperity/SimCity)與軍事力量(MilitaryPower/Age of Empires)
 */
export class VillageEntity {
    constructor(id, name, x, y, owner = 'neutral') {
        this.id = id;
        this.name = name;
        this.x = x;
        this.y = y;
        this.owner = owner; // 'player', 'rival', 'neutral'

        this.population = 15 + Math.floor(Math.random() * 10);
        this.maxPopulation = 35;
        this.food = 350;
        this.wood = 250;

        // 信仰統治度 (0% ~ 100%)
        this.belief = owner === 'player' ? 100 : (owner === 'rival' ? 0 : 20);
        this.boundaryRadius = owner === 'player' ? 380 : 280;

        // 🌟 善與惡2核心雙軌指標
        this.prosperity = owner === 'player' ? 60 : (owner === 'rival' ? 30 : 20); // 模擬城市繁榮吸引力
        this.militaryPower = owner === 'rival' ? 60 : 20; // 世紀帝國武備力量

        // 祈禱模式控制
        this.isPrayingMode = false;
        this.energyAccumulator = 0;
        
        // 建築損壞程度
        this.health = 600;
        this.maxHealth = 600;
        this.isDestroyed = false;

        this.consumeTimer = 5; // 食物消耗週期
        this.emigrateTimer = 12; // 自願移民檢查週期 (SimCity 勝利路徑)
        this.troopRecruitTimer = 22; // 部隊訓練出征週期 (AoE 勝利路徑)
    }

    /**
     * 增加/扣減玩家信仰度 (達到 100% 時征服該村莊！)
     */
    addBelief(amount, isGoodAct = true) {
        if (this.owner === 'player') {
            this.belief = 100;
            if (amount > 0 && this.boundaryRadius < 650) {
                this.boundaryRadius += amount * 1.5;
            }
            if (isGoodAct) this.prosperity = Math.min(300, this.prosperity + amount * 0.5);
            return;
        }

        this.belief += amount;
        if (this.belief >= 100) {
            this.belief = 100;
            this.owner = 'player';
            this.boundaryRadius = 450;
            this.prosperity += 50;
        } else if (this.belief <= 0) {
            this.belief = 0;
            this.owner = 'rival';
        }
    }

    generateEnergyFromPrayer(dt) {
        if (this.owner !== 'player') return 0;
        const generated = 14 * dt;
        this.energyAccumulator += generated;
        return generated;
    }

    update(dt, allVillages = null, allVillagers = null, allTroops = null, particleEngine = null, soundEngine = null, uiCallback = null) {
        if (this.isDestroyed) return;

        // 1. 糧食消耗與人口繁衍
        this.consumeTimer -= dt;
        if (this.consumeTimer <= 0) {
            this.consumeTimer = 6;
            const foodConsumed = Math.ceil(this.population * 0.4);
            this.food -= foodConsumed;

            if (this.food < 0) {
                this.food = 0;
                if (this.population > 5) this.population--;
                if (this.owner === 'player') this.addBelief(-5, false);
                this.prosperity = Math.max(0, this.prosperity - 10);
            } else if (this.food > 200 && this.population < this.maxPopulation && Math.random() < 0.4) {
                this.population++;
                this.prosperity += 5;
            }
        }

        // 2. 🌟 模擬城市 (SimCity) 和平繁榮吸引力移民流！
        if (allVillages && allVillagers && this.owner !== 'player') {
            this.emigrateTimer -= dt;
            if (this.emigrateTimer <= 0) {
                this.emigrateTimer = 14;
                const playerV = allVillages.find(v => v.owner === 'player');
                if (playerV && playerV.prosperity - this.prosperity >= 40) {
                    // 玩家城市太過繁榮美妙！敵方/中立居民心生嚮往，自願移民投誠！
                    const candidate = allVillagers.find(vg => vg.village === this && !vg.isDead && !vg.isGrabbed);
                    if (candidate) {
                        candidate.village = playerV;
                        candidate.beliefInPlayer = 100;
                        candidate.showEmotion('💖', 4);
                        this.population = Math.max(1, this.population - 1);
                        playerV.population = Math.min(playerV.maxPopulation, playerV.population + 1);
                        this.addBelief(12, true); // 移民帶動整村信仰傾倒！
                        
                        if (particleEngine) particleEngine.emitHeal(candidate.x, candidate.y, 100, 2);
                        if (uiCallback && Math.random() < 0.5) {
                            uiCallback(`⛲ 模擬城市效應：【${this.name}】的居民因羨慕您的文化奇觀與繁榮，自願歸順移民至您的王都！`, 'info');
                        }
                    }
                }
            }
        }

        // 3. 🌟 世紀帝國 (Age of Empires) 武力征服練兵出征流！
        if (allTroops && (this.owner === 'player' || this.owner === 'rival') && this.militaryPower >= 40) {
            this.troopRecruitTimer -= dt;
            if (this.troopRecruitTimer <= 0 && allTroops.filter(t => t.owner === this.owner && !t.isDead).length < 5) {
                this.troopRecruitTimer = 25;
                // 根據武備力量選擇訓練義勇民團或精銳武士/弓箭手！
                const type = this.militaryPower > 100 ? (Math.random() < 0.5 ? 'samurai' : 'archer') : 'militia';
                const targetV = allVillages ? allVillages.find(v => v.owner !== this.owner) : null;
                
                if (targetV) {
                    const newTroop = new TroopEntity(`troop_${Date.now()}`, type, this.x + (Math.random()-0.5)*60, this.y + (Math.random()-0.5)*60, this.owner, targetV);
                    allTroops.push(newTroop);
                    if (particleEngine) particleEngine.emitHeal(this.x, this.y, 80, 1);
                    if (uiCallback && this.owner === 'player') {
                        uiCallback(`⚔️ 世紀帝國效應：【${this.name}】成功訓練出【${newTroop.name}】並前進敵方村莊進攻！`, 'info');
                    } else if (uiCallback && this.owner === 'rival' && Math.random() < 0.4) {
                        uiCallback(`⚠️ 敵情警報：敵對文明訓練出了【${newTroop.name}】，正朝您的領土進軍！`, 'error');
                    }
                }
            }
        }
    }

    takeDamage(dmg, particleEngine = null) {
        this.health -= dmg;
        if (particleEngine && Math.random() < 0.3) {
            particleEngine.addParticle({
                x: this.x + (Math.random() - 0.5) * 60, y: this.y + (Math.random() - 0.5) * 60,
                vx: (Math.random() - 0.5) * 80, vy: -60, size: 8, color: '#f97316', decay: 0.04
            });
        }
        if (this.health <= 0 && !this.isDestroyed) {
            this.isDestroyed = true;
            if (particleEngine) particleEngine.emitExplosion(this.x, this.y, 140);
        }
    }

    render(ctx, time) {
        if (this.isDestroyed) return;
        ctx.save();

        // 1. 底板廣場
        ctx.beginPath();
        ctx.arc(this.x, this.y, 55, 0, Math.PI * 2);
        ctx.fillStyle = this.owner === 'player' ? 'rgba(56, 189, 248, 0.25)' : (this.owner === 'rival' ? 'rgba(239, 68, 68, 0.25)' : 'rgba(168, 85, 247, 0.18)');
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = this.owner === 'player' ? '#38bdf8' : (this.owner === 'rival' ? '#ef4444' : '#a855f7');
        ctx.stroke();

        // 2. 建築中心圖示
        ctx.font = '38px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const buildingIcon = this.owner === 'player' ? '🏛️' : (this.owner === 'rival' ? '🏰' : '⛺');
        ctx.fillText(buildingIcon, this.x, this.y - 12);

        // 3. 周圍景觀與繁榮度呈現
        ctx.font = '20px sans-serif';
        ctx.fillText(this.prosperity > 80 ? '⛲' : '🏠', this.x - 38, this.y + 15);
        ctx.fillText(this.militaryPower > 60 ? '🏹' : '🏡', this.x + 38, this.y + 15);
        ctx.fillText('🔥', this.x, this.y + 25);

        // 4. 名稱與統治條
        ctx.font = 'bold 13px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 4;
        ctx.fillText(`${this.name} (${Math.floor(this.belief)}%)`, this.x, this.y - 50);

        // 繁榮與兵力微型狀態列
        ctx.font = '11px Outfit, sans-serif';
        ctx.fillStyle = '#fef08a';
        ctx.fillText(`✨文化:${Math.floor(this.prosperity)} | ⚔️兵力:${Math.floor(this.militaryPower)}`, this.x, this.y + 50);

        // 統治條底框與進度
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(this.x - 32, -38 + this.y, 64, 6);
        ctx.fillStyle = this.owner === 'player' ? '#38bdf8' : (this.owner === 'rival' ? '#ef4444' : '#a855f7');
        ctx.fillRect(this.x - 32, -38 + this.y, (this.belief / 100) * 64, 6);
        ctx.strokeStyle = 'rgba(255,255,255,0.4)';
        ctx.strokeRect(this.x - 32, -38 + this.y, 64, 6);

        ctx.restore();
    }
}
