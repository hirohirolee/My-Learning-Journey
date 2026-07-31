import { gameStorage } from '../engine/storage.js';

/**
 * 上帝天賦聖殿與信仰水晶貨幣管理器 (God Talents Tree & Crystal Currency Progression)
 * 負責處理玩家帳號長線養成進度，包含創世、毀滅、御獸三大分支的升級、效果計算與序列化。
 */
export const TALENT_BRANCHES = {
    creation: {
        name: '🌟 創世系 (Creation)',
        desc: '提升神聖賜福、祭壇祈禱效率與能量上限',
        color: '#34d399',
        talents: [
            { id: 'altar_efficiency', name: '虔誠禱告', desc: '祭壇村民祈禱能量產出效率提升 +10%/級', maxLevel: 5, baseCost: 20, costMultiplier: 1.8, icon: '🙏' },
            { id: 'max_energy_boost', name: '無邊法力', desc: '祭壇最大能量上限增加 +200/級', maxLevel: 5, baseCost: 25, costMultiplier: 2.0, icon: '⚡' },
            { id: 'good_cooldown', name: '慈悲迅速', desc: '所有善性與輔助神力冷卻時間縮短 -10%/級', maxLevel: 3, baseCost: 50, costMultiplier: 2.5, icon: '✨' }
        ]
    },
    destruction: {
        name: '🔥 毀滅系 (Destruction)',
        desc: '提升天崩地裂、雷電火球傷害與威嚇威嚴',
        color: '#f87171',
        talents: [
            { id: 'fire_lightning_dmg', name: '毀滅風暴', desc: '火球、雷電與爆破神力傷害與範圍提升 +15%/級', maxLevel: 5, baseCost: 20, costMultiplier: 1.8, icon: '☄️' },
            { id: 'evil_cooldown', name: '天譴頻繁', desc: '所有惡性攻擊神力冷卻時間縮短 -10%/級', maxLevel: 3, baseCost: 50, costMultiplier: 2.5, icon: '☠️' },
            { id: 'fear_aura', name: '深淵威嚇', desc: '獻祭或破壞敵方建築時產生的信仰恐懼提升 +15%/級', maxLevel: 3, baseCost: 40, costMultiplier: 2.0, icon: '👹' }
        ]
    },
    mastery: {
        name: '🦁 御獸系 (Mastery)',
        desc: '增強神獸資質、法術領悟與飾品共鳴能力',
        color: '#fbbf24',
        talents: [
            { id: 'fast_learner', name: '聰慧靈性', desc: '神獸觀摩上帝施放法術時的學習速度提升 +20%/級', maxLevel: 5, baseCost: 30, costMultiplier: 1.8, icon: '📖' },
            { id: 'beast_vigor', name: '巨獸體格', desc: '神獸生命上限與法力上限提升 +15%/級', maxLevel: 5, baseCost: 25, costMultiplier: 2.0, icon: '💪' },
            { id: 'skin_affinity', name: '飾品共鳴', desc: '解鎖並啟用所有神獸穿戴飾品的 +25% 額外屬性共鳴效果！', maxLevel: 1, baseCost: 100, costMultiplier: 1.0, icon: '👑' }
        ]
    }
};

export class ProgressionManager {
    constructor() {
        this.crystals = 100; // 預設給予 100 信仰水晶體驗升級與購買
        this.talents = {}; // { talent_id: current_level }
        this.unlockedBeasts = ['ape', 'lion', 'wolf', 'tiger']; // 預設解鎖基礎神獸
        this.listeners = [];

        this.initDefaultTalents();
        this.loadProgress();
    }

    initDefaultTalents() {
        for (const branch of Object.values(TALENT_BRANCHES)) {
            for (const t of branch.talents) {
                if (this.talents[t.id] === undefined) {
                    this.talents[t.id] = 0;
                }
            }
        }
    }

    loadProgress() {
        const saved = gameStorage.load('bw_meta_save');
        if (saved) {
            this.crystals = saved.crystals ?? 100;
            this.talents = { ...this.talents, ...(saved.talents || {}) };
            this.unlockedBeasts = saved.unlockedBeasts || ['ape', 'lion', 'wolf', 'tiger'];
        }
    }

    saveProgress() {
        const data = {
            crystals: this.crystals,
            talents: this.talents,
            unlockedBeasts: this.unlockedBeasts
        };
        gameStorage.save('bw_meta_save', data);
        this.notifyListeners();
    }

    onChange(cb) {
        this.listeners.push(cb);
    }

    notifyListeners() {
        for (const cb of this.listeners) {
            cb(this.crystals, this.talents, this.unlockedBeasts);
        }
    }

    addCrystals(amount) {
        if (amount <= 0) return;
        this.crystals += amount;
        this.saveProgress();
    }

    spendCrystals(amount) {
        if (this.crystals < amount) return false;
        this.crystals -= amount;
        this.saveProgress();
        return true;
    }

    getTalentCost(talentId) {
        for (const branch of Object.values(TALENT_BRANCHES)) {
            const t = branch.talents.find(item => item.id === talentId);
            if (t) {
                const currentLvl = this.talents[talentId] || 0;
                if (currentLvl >= t.maxLevel) return null; // 已滿級
                return Math.round(t.baseCost * Math.pow(t.costMultiplier, currentLvl));
            }
        }
        return null;
    }

    upgradeTalent(talentId) {
        const cost = this.getTalentCost(talentId);
        if (cost === null) return { success: false, msg: '該天賦已達最大等級！' };
        if (this.crystals < cost) return { success: false, msg: '信仰水晶不足！' };

        this.crystals -= cost;
        this.talents[talentId] = (this.talents[talentId] || 0) + 1;
        this.saveProgress();
        return { success: true, msg: '天賦升級成功！' };
    }

    unlockBeast(speciesId, cost) {
        if (this.unlockedBeasts.includes(speciesId)) return { success: false, msg: '已擁有該神獸！' };
        if (this.crystals < cost) return { success: false, msg: '信仰水晶不足！' };

        this.crystals -= cost;
        this.unlockedBeasts.push(speciesId);
        this.saveProgress();
        return { success: true, msg: '成功解鎖神獸！' };
    }

    /**
     * 獲取指定加成類別的計算數值 (供引擎其他模組呼叫)
     */
    getBonus(type) {
        const lvl = (id) => this.talents[id] || 0;
        switch (type) {
            case 'altar_efficiency': return 1.0 + lvl('altar_efficiency') * 0.10; // +10% / lvl
            case 'max_energy': return lvl('max_energy_boost') * 200; // +200 / lvl
            case 'good_cooldown': return Math.max(0.3, 1.0 - lvl('good_cooldown') * 0.10); // -10% / lvl
            case 'evil_cooldown': return Math.max(0.3, 1.0 - lvl('evil_cooldown') * 0.10); // -10% / lvl
            case 'destruction_dmg': return 1.0 + lvl('fire_lightning_dmg') * 0.15; // +15% / lvl
            case 'fear_mult': return 1.0 + lvl('fear_aura') * 0.15; // +15% / lvl
            case 'learning_rate': return 1.0 + lvl('fast_learner') * 0.20; // +20% / lvl
            case 'beast_stats': return 1.0 + lvl('beast_vigor') * 0.15; // +15% / lvl
            case 'skin_affinity': return lvl('skin_affinity') > 0 ? 1.25 : 1.0; // 啟用共鳴
            default: return 1.0;
        }
    }
}

export const godProgression = new ProgressionManager();
