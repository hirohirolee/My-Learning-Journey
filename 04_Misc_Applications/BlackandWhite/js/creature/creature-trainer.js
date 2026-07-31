/**
 * 神獸管教與狀態輔助管理器 (Creature Trainer & Buff System)
 * 負責處理牽繩模式切換 (Leash)、撫摸獎勵、掌摑懲罰以及 11 種輔助神力效果
 */
export class CreatureTrainer {
    constructor(creature, soundEngine) {
        this.creature = creature;
        this.soundEngine = soundEngine;
        this.activeBuffs = {}; // { 'strong': { duration: 15, ... } }
    }

    setLeashMode(mode) {
        if (!this.creature) return;
        this.creature.leashMode = mode;
        if (mode === 'village') {
            this.creature.thought = '「🔗 牽繩拴在主村！我將在這裡守護並協助大家！」';
        } else if (mode === 'roam') {
            this.creature.thought = '「🏝️ 牽繩解除了！我可以自由探索島嶼的每一個角落了！」';
        } else if (mode === 'enemy') {
            this.creature.thought = '「⚔️ 牽繩指引前往敵村！展現主人的力量與威嚇！」';
        }
    }

    pet() {
        if (!this.creature) return;
        this.creature.receivePet(this.soundEngine);
    }

    slap() {
        if (!this.creature) return;
        this.creature.receiveSlap(this.soundEngine);
    }

    /**
     * 施加輔助神力 (Buffs / Debuffs / Transformations)
     */
    applyAuxiliaryMiracle(spellId, duration = 20) {
        if (!this.creature) return;
        this.activeBuffs[spellId] = { duration: duration };

        switch (spellId) {
            case 'aux_strong':
                this.creature.thought = '「💪 強壯神力灌注！我的力量大增！」';
                this.creature.species.str *= 1.5;
                break;
            case 'aux_weak':
                this.creature.thought = '「🥀 虛弱神力...我的力氣好小...」';
                this.creature.species.str *= 0.6;
                break;
            case 'aux_freeze':
                this.creature.thought = '「❄️ 冰凍神力！好冷！身體動不了了！」';
                this.creature.state = 'frozen';
                break;
            case 'aux_speed':
                this.creature.thought = '「⚡ 加速神力！我的腳步變得無比輕盈疾速！」';
                this.creature.species.spd *= 2.0;
                break;
            case 'aux_enlarge':
                this.creature.thought = '「🦖 放大神力！我變成了頂天立地的巨獸！」';
                this.creature.scale = 2.0;
                break;
            case 'aux_shrink':
                this.creature.thought = '「🐭 縮小神力...我變得跟小老鼠一樣小了...」';
                this.creature.scale = 0.6;
                break;
            case 'aux_compassion':
                this.creature.thought = '「💖 喜愛神力！心中充滿了無限的慈悲與愛，好想幫助所有人！」';
                this.creature.alignment = Math.min(100, this.creature.alignment + 50);
                this.creature.tendencies.help_villagers = 100;
                break;
            case 'aux_anger':
                this.creature.thought = '「🔥 憤怒神力！血液在沸騰！我要摧毀眼前的一切！」';
                this.creature.alignment = Math.max(-100, this.creature.alignment - 50);
                this.creature.tendencies.destroy_houses = 100;
                break;
            case 'aux_invisible':
                this.creature.thought = '「👻 隱形神力！我融入了空氣中，沒人看得見我！」';
                break;
            case 'aux_fly':
                this.creature.thought = '「🪰 聖蒼蠅神力！控制不住自己了！瘋狂亂飛！」';
                this.creature.vx = (Math.random() - 0.5) * 400;
                this.creature.vy = (Math.random() - 0.5) * 400;
                break;
            case 'aux_shield':
                this.creature.thought = '「🛡️ 抗法術神力！任何有害的魔法都無法傷害我！」';
                break;
        }
    }

    update(dt) {
        if (!this.creature) return;
        for (const [spellId, buff] of Object.entries(this.activeBuffs)) {
            buff.duration -= dt;
            if (buff.duration <= 0) {
                // 解除 Buff 狀態回復
                if (spellId === 'aux_enlarge' || spellId === 'aux_shrink') {
                    this.creature.scale = 1.0;
                }
                delete this.activeBuffs[spellId];
            }
        }
    }
}
