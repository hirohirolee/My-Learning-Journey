import { gameStorage } from '../engine/storage.js';
import { godProgression } from './progression.js';

/**
 * 神獸飾品裝扮與外觀共鳴系統 (Creature Customizer & Accessories Stats)
 * 允許玩家購買與穿戴專屬神獸飾品，在 Canvas 上繪製視覺外觀，並給予強大的被動能力加成。
 */
export const ACCESSORY_DATABASE = {
    halo: {
        id: 'halo',
        name: '聖光天使環',
        symbol: '😇',
        desc: '閃耀神聖純潔之光的頭環。神獸法力上限 +50，善性傾向明顯提高！',
        cost: 50,
        slot: 'head',
        stats: { maxMana: 50, alignmentBoost: 30, speedMult: 1.05 }
    },
    horns: {
        id: 'horns',
        name: '熔岩惡魔角',
        symbol: '😈',
        desc: '散發地獄熱氣的巨角。神獸破壞攻擊力 +35%，惡性傾向明顯提高！',
        cost: 50,
        slot: 'head',
        stats: { attackBoost: 1.35, alignmentBoost: -30, speedMult: 1.05 }
    },
    crown: {
        id: 'crown',
        name: '王者之神冠',
        symbol: '👑',
        desc: '萬獸之王的純金皇冠。神獸生命上限 +100，全屬性提高 20%！',
        cost: 120,
        slot: 'head',
        stats: { maxHp: 100, maxMana: 50, attackBoost: 1.20, speedMult: 1.15 }
    },
    boots: {
        id: 'boots',
        name: '疾風之靈靴',
        symbol: '🥾',
        desc: '注入風暴神力的輕盈短靴。神獸移動與巡邏速度大幅提升 +40%！',
        cost: 70,
        slot: 'feet',
        stats: { speedMult: 1.40, maxHp: 30 }
    }
};

export class CreatureSkinManager {
    constructor() {
        this.unlockedAccessories = ['halo']; // 預設送一個聖光天使環
        this.equippedAccessory = 'halo'; // 預設穿戴
        this.listeners = [];

        this.loadSkins();
    }

    loadSkins() {
        const saved = gameStorage.load('bw_skins_save');
        if (saved) {
            this.unlockedAccessories = saved.unlocked || ['halo'];
            this.equippedAccessory = saved.equipped ?? 'halo';
        }
    }

    saveSkins() {
        gameStorage.save('bw_skins_save', {
            unlocked: this.unlockedAccessories,
            equipped: this.equippedAccessory
        });
        this.notifyListeners();
    }

    onChange(cb) {
        this.listeners.push(cb);
    }

    notifyListeners() {
        for (const cb of this.listeners) {
            cb(this.unlockedAccessories, this.equippedAccessory);
        }
    }

    unlock(accId) {
        const acc = ACCESSORY_DATABASE[accId];
        if (!acc) return { success: false, msg: '無效的飾品ID！' };
        if (this.unlockedAccessories.includes(accId)) return { success: false, msg: '您已經擁有該飾品！' };

        const spent = godProgression.spendCrystals(acc.cost);
        if (!spent) return { success: false, msg: '信仰水晶不足！' };

        this.unlockedAccessories.push(accId);
        this.saveSkins();
        return { success: true, msg: `恭喜解鎖【${acc.name}】！` };
    }

    equip(accId) {
        if (!accId || accId === 'none') {
            this.equippedAccessory = null;
            this.saveSkins();
            return { success: true, msg: '已卸下飾品。' };
        }
        if (!this.unlockedAccessories.includes(accId)) return { success: false, msg: '尚未解鎖該飾品！' };

        this.equippedAccessory = accId;
        this.saveSkins();
        return { success: true, msg: `已裝備【${ACCESSORY_DATABASE[accId].name}】！` };
    }

    /**
     * 獲取當前配戴飾品的加成屬性 (結合御獸系天賦共鳴比率)
     */
    getEquippedStats() {
        if (!this.equippedAccessory || !ACCESSORY_DATABASE[this.equippedAccessory]) {
            return { maxHp: 0, maxMana: 0, attackBoost: 1.0, speedMult: 1.0, alignmentBoost: 0 };
        }
        const base = ACCESSORY_DATABASE[this.equippedAccessory].stats;
        const affinity = godProgression.getBonus('skin_affinity'); // 1.0 或 1.25

        return {
            maxHp: (base.maxHp || 0) * affinity,
            maxMana: (base.maxMana || 0) * affinity,
            attackBoost: 1.0 + ((base.attackBoost || 1.0) - 1.0) * affinity,
            speedMult: 1.0 + ((base.speedMult || 1.0) - 1.0) * affinity,
            alignmentBoost: (base.alignmentBoost || 0) * affinity
        };
    }

    /**
     * 於 Canvas 渲染畫面上即時畫出神獸穿戴的飾品特效
     */
    renderAccessory(ctx, creature, screenX, screenY, size, dt) {
        if (!this.equippedAccessory || !ACCESSORY_DATABASE[this.equippedAccessory]) return;
        const acc = ACCESSORY_DATABASE[this.equippedAccessory];
        ctx.save();

        if (acc.id === 'halo') {
            // 繪製懸浮在神獸頭上發光的聖光天使環
            const floatOffset = Math.sin(performance.now() / 250) * 3;
            ctx.beginPath();
            ctx.ellipse(screenX, screenY - size * 0.9 + floatOffset, size * 0.5, size * 0.15, 0, 0, Math.PI * 2);
            ctx.strokeStyle = '#fef08a';
            ctx.lineWidth = 4;
            ctx.shadowColor = '#fde047';
            ctx.shadowBlur = 15;
            ctx.stroke();
            ctx.fillStyle = 'rgba(254, 240, 138, 0.3)';
            ctx.fill();
        } else if (acc.id === 'horns') {
            // 繪製頭頂兩側熾熱的熔岩角
            ctx.shadowColor = '#dc2626';
            ctx.shadowBlur = 12;
            ctx.font = `${size * 0.6}px Outfit`;
            ctx.textAlign = 'center';
            ctx.fillText('😈', screenX, screenY - size * 0.7);
        } else if (acc.id === 'crown') {
            // 繪製王者金冠
            const floatOffset = Math.sin(performance.now() / 400) * 2;
            ctx.shadowColor = '#fbbf24';
            ctx.shadowBlur = 15;
            ctx.font = `${size * 0.6}px Outfit`;
            ctx.textAlign = 'center';
            ctx.fillText('👑', screenX, screenY - size * 0.8 + floatOffset);
        } else if (acc.id === 'boots') {
            // 繪製腳底下疾風旋風粒子特效
            ctx.beginPath();
            ctx.arc(screenX, screenY + size * 0.5, size * 0.6, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(56, 189, 248, 0.6)';
            ctx.lineWidth = 3;
            ctx.setLineDash([8, 6]);
            ctx.lineDashOffset = -performance.now() / 30;
            ctx.stroke();
        }

        ctx.restore();
    }
}

export const creatureSkins = new CreatureSkinManager();
