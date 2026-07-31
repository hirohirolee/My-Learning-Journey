import { godProgression } from '../meta/progression.js?v=3';

/**
 * 關卡動態支線任務系統 (Dynamic Stage Side Quests)
 * 善與惡2特色：在主線征服八島的漫長經營過程中，隨機穿插豐富的突發支線事件！
 * 包含求雨抗旱、迷途農夫、狼群侵襲、商團貿易與巨石陣祭祀，提供水晶、能量與信仰度獎勵。
 */

export const SIDE_QUEST_POOL = [
    {
        id: 'drought_relief',
        title: '🌧️ 求雨抗旱事件',
        desc: '乾旱肆虐了中立部落的稻田！請在 60 秒內在該區域上方施展【灑水神力】拯救莊稼！',
        timeLimit: 60,
        targetSpell: 'water_1',
        rewardEnergy: 250,
        rewardCrystal: 30,
        rewardBelief: 25,
        isCompleted: false
    },
    {
        id: 'lost_farmer',
        title: '🌾 迷途與染病的農夫',
        desc: '一位農夫在森林深處迷路染病！請使用【治療神力】救治他或派神獸護送他返回部落！',
        timeLimit: 90,
        targetSpell: 'heal_1',
        rewardEnergy: 200,
        rewardCrystal: 25,
        rewardBelief: 20,
        isCompleted: false
    },
    {
        id: 'wolf_invasion',
        title: '🐺 餓狼群的突襲',
        desc: '山林裡的餓狼正準備襲擊您的村莊！請派遣部隊、神獸或施展【火球/閃電】擊退牠們！',
        timeLimit: 75,
        targetSpell: 'fireball_1',
        rewardEnergy: 300,
        rewardCrystal: 40,
        rewardBelief: 30,
        isCompleted: false
    },
    {
        id: 'merchant_trade',
        title: '💎 異域商團的委託',
        desc: '來自遠方文明的貿易商隊需要木材補給！請在祭壇獻祭或累積超過 400 木材以完成交易！',
        timeLimit: 120,
        targetResource: 'wood',
        targetAmount: 400,
        rewardEnergy: 150,
        rewardCrystal: 60,
        rewardBelief: 15,
        isCompleted: false
    },
    {
        id: 'ancient_ritual',
        title: '⛩️ 巨石陣的古老祭祀',
        desc: '部落長老希望在古老的神壇舉行盛大獻祭！請用神之手抓取 1 隻牛或羊丟入祭壇獻祭！',
        timeLimit: 90,
        targetAction: 'sacrifice_animal',
        rewardEnergy: 400,
        rewardCrystal: 50,
        rewardBelief: 35,
        isCompleted: false
    }
];

export class SideQuestManager {
    constructor(uiCallback) {
        this.activeQuest = null;
        this.spawnTimer = 25; // 每隔 25~45 秒嘗試觸發一個支線任務
        this.uiCallback = uiCallback;
        this.completedCount = 0;
    }

    update(dt, worldContext) {
        if (worldContext.isSandbox || worldContext.isGameOver) return;

        // 檢查當前任務倒數
        if (this.activeQuest) {
            this.activeQuest.timeLimit -= dt;
            if (this.activeQuest.timeLimit <= 0) {
                if (this.uiCallback) this.uiCallback(`⏳ 支線任務【${this.activeQuest.title}】超時失敗！`, 'error');
                this.activeQuest = null;
                this.spawnTimer = 35;
            }
            return;
        }

        // 生成新支線任務
        this.spawnTimer -= dt;
        if (this.spawnTimer <= 0) {
            this.spawnTimer = 40 + Math.random() * 30;
            this.triggerRandomQuest(worldContext);
        }
    }

    triggerRandomQuest(worldContext) {
        const available = SIDE_QUEST_POOL.filter(q => !q.isCompleted);
        if (available.length === 0) {
            // 所有任務皆解過一次後，重置池子繼續挑戰
            SIDE_QUEST_POOL.forEach(q => q.isCompleted = false);
            return;
        }
        const template = available[Math.floor(Math.random() * available.length)];
        this.activeQuest = { ...template, timeLimit: template.timeLimit };

        if (this.uiCallback) {
            this.uiCallback(`📜 觸發支線任務：【${this.activeQuest.title}】\n${this.activeQuest.desc}\n🎁 獎勵：+${this.activeQuest.rewardCrystal} 信仰水晶, +${this.activeQuest.rewardEnergy} 祭壇能量`, 'info');
        }
    }

    /**
     * 檢測法術施放是否滿足任務條件
     */
    onSpellCast(spellId, worldContext) {
        if (!this.activeQuest) return;
        if (this.activeQuest.targetSpell && spellId.includes(this.activeQuest.targetSpell.split('_')[0])) {
            this.completeQuest(worldContext);
        }
    }

    /**
     * 檢測獻祭是否滿足任務條件
     */
    onSacrifice(entityType, worldContext) {
        if (!this.activeQuest) return;
        if (this.activeQuest.targetAction === 'sacrifice_animal' && entityType.startsWith('animal_')) {
            this.completeQuest(worldContext);
        }
    }

    /**
     * 檢測資源數量是否滿足任務條件
     */
    checkResourceQuest(playerVillage, worldContext) {
        if (!this.activeQuest) return;
        if (this.activeQuest.targetResource === 'wood' && playerVillage && playerVillage.wood >= this.activeQuest.targetAmount) {
            playerVillage.wood -= this.activeQuest.targetAmount;
            this.completeQuest(worldContext);
        }
    }

    completeQuest(worldContext) {
        const q = this.activeQuest;
        if (!q) return;

        q.isCompleted = true;
        this.completedCount++;

        // 發放獎勵
        if (worldContext && worldContext.energy !== undefined) {
            worldContext.energy += q.rewardEnergy;
        }
        godProgression.addCrystals(q.rewardCrystal);

        // 增加玩家村莊統治度
        if (worldContext && worldContext.villages) {
            const playerV = worldContext.villages.find(v => v.owner === 'player');
            if (playerV) playerV.addBelief(q.rewardBelief, true);
        }

        if (this.uiCallback) {
            this.uiCallback(`🎉 完美達成支線任務【${q.title}】！\n獲得 💎 +${q.rewardCrystal} 水晶, ⚡ +${q.rewardEnergy} 能量, 💖 信仰度大躍進！`, 'info');
        }
        if (worldContext.soundEngine) worldContext.soundEngine.playHeal();
        if (worldContext.particleEngine && worldContext.camera) {
            worldContext.particleEngine.emitHeal(worldContext.camera.x, worldContext.camera.y, 200, 3);
        }

        this.activeQuest = null;
        this.spawnTimer = 30;
    }
}
