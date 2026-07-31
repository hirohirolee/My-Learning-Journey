/**
 * 城市建築與奇觀紀念碑系統 (SimCity vs Age of Empires Buildings)
 * 善與惡2專屬：包含模擬城市繁榮吸引力奇觀 (Fountains, Wonders, Gardens)
 * 與 世紀帝國武力征服軍事設施 (War Camps, Archery Ranges, Defense Towers)
 */

export const BUILDING_DATABASE = {
    // ----- 模擬城市經營流 (繁榮與文化吸引力) -----
    'fountain': {
        id: 'fountain',
        name: '神聖許願噴泉',
        category: 'simcity',
        icon: '⛲',
        costWood: 150,
        costFood: 0,
        costEnergy: 100,
        prosperityBonus: 25,
        maxHp: 400,
        desc: '大幅提升城鎮文化吸引力與居民幸福度，誘使敵對村民自願移民投誠！'
    },
    'garden': {
        id: 'garden',
        name: '巴比倫空中花園',
        category: 'simcity',
        icon: '🌷',
        costWood: 250,
        costFood: 100,
        costEnergy: 200,
        prosperityBonus: 50,
        maxHp: 600,
        desc: '極致的藝術花園奇觀！持續散發和樂光環，每秒自動轉化周圍敵對部落的信仰度。'
    },
    'grand_temple': {
        id: 'grand_temple',
        name: '創世大教堂奇觀',
        category: 'simcity',
        icon: '⛪',
        costWood: 500,
        costFood: 200,
        costEnergy: 500,
        prosperityBonus: 120,
        maxHp: 1200,
        desc: '史詩級文化奇觀！建立後城市繁榮度暴增，周圍敵對文明將無法抵擋您神聖和平的呼喚！'
    },

    // ----- 世紀帝國武力征服流 (軍事訓練與武力進攻) -----
    'barracks': {
        id: 'barracks',
        name: '部隊練武軍營',
        category: 'aoe',
        icon: '⛺',
        costWood: 200,
        costFood: 150,
        costEnergy: 150,
        militaryBonus: 30,
        maxHp: 700,
        desc: '世紀帝國式軍事要塞！允許將普通村民訓練成神兵武士部隊，主動出擊攻佔敵方領土！'
    },
    'archery': {
        id: 'archery',
        name: '精銳弓箭手塔樓',
        category: 'aoe',
        icon: '🏹',
        costWood: 300,
        costFood: 100,
        costEnergy: 250,
        militaryBonus: 50,
        maxHp: 800,
        desc: '遠程部隊防禦與訓練陣地！能自動射擊靠近的敵軍部隊與野獸，並訓練弓箭軍團！'
    },
    'war_altar': {
        id: 'war_altar',
        name: '毀滅戰神巨碑',
        category: 'aoe',
        icon: '🗿',
        costWood: 450,
        costFood: 300,
        costEnergy: 600,
        militaryBonus: 100,
        maxHp: 1500,
        desc: '散發血腥與狂暴戰意的黑石巨碑！大幅增強全體武裝部隊的攻擊力與神獸破壞慾望！'
    }
};

export class BuildingEntity {
    constructor(id, type, x, y, owner = 'player', village = null) {
        this.id = id;
        this.type = type;
        this.x = x;
        this.y = y;
        this.owner = owner; // 'player', 'rival', 'neutral'
        this.village = village;

        const def = BUILDING_DATABASE[type] || BUILDING_DATABASE['fountain'];
        this.name = def.name;
        this.category = def.category; // 'simcity' or 'aoe'
        this.icon = def.icon;
        this.prosperityBonus = def.prosperityBonus || 0;
        this.militaryBonus = def.militaryBonus || 0;
        
        this.health = def.maxHp;
        this.maxHealth = def.maxHp;
        this.isDestroyed = false;

        // 建造特效與動畫
        this.buildProgress = 0; // 0 ~ 100%
        this.isConstructed = false;
        this.size = 45;
    }

    update(dt, villages, particleEngine, soundEngine) {
        if (this.isDestroyed) return;

        // 建築施工動畫
        if (!this.isConstructed) {
            this.buildProgress += dt * 30; // 約3.3秒建成
            if (this.buildProgress >= 100) {
                this.buildProgress = 100;
                this.isConstructed = true;
                if (particleEngine) particleEngine.emitHeal(this.x, this.y, 80, 2);
                if (soundEngine) soundEngine.playHeal(this.x);
                // 建成後將加成注入村莊
                if (this.village) {
                    this.village.prosperity += this.prosperityBonus;
                    this.village.militaryPower += this.militaryBonus;
                }
            }
            return;
        }

        // 奇觀的持續和樂光環或武力威壓
        if (this.isConstructed && Math.random() < 0.1 && particleEngine) {
            if (this.category === 'simcity') {
                particleEngine.addParticle({
                    x: this.x + (Math.random() - 0.5) * 30, y: this.y - 20,
                    vx: 0, vy: -15, size: 10, color: '#fef08a', text: '✨', decay: 0.02
                });
            } else {
                particleEngine.addParticle({
                    x: this.x + (Math.random() - 0.5) * 30, y: this.y - 20,
                    vx: 0, vy: -15, size: 10, color: '#ef4444', text: '⚔️', decay: 0.02
                });
            }
        }
    }

    takeDamage(dmg, particleEngine) {
        if (this.isDestroyed) return;
        this.health -= dmg;
        if (particleEngine) {
            particleEngine.addParticle({
                x: this.x + (Math.random() - 0.5) * 30, y: this.y,
                vx: (Math.random() - 0.5) * 40, vy: -30, size: 6, color: '#f97316', decay: 0.05
            });
        }
        if (this.health <= 0) {
            this.isDestroyed = true;
            if (this.village) {
                this.village.prosperity = Math.max(0, this.village.prosperity - this.prosperityBonus);
                this.village.militaryPower = Math.max(0, this.village.militaryPower - this.militaryBonus);
            }
            if (particleEngine) particleEngine.emitExplosion(this.x, this.y, 80);
        }
    }

    render(ctx, time) {
        if (this.isDestroyed) return;
        ctx.save();
        ctx.translate(this.x, this.y);

        // 施工中的工地鷹架效果
        if (!this.isConstructed) {
            ctx.fillStyle = 'rgba(180, 83, 9, 0.4)';
            ctx.fillRect(-25, -25, 50, 50);
            ctx.strokeStyle = '#f59e0b';
            ctx.lineWidth = 2;
            ctx.strokeRect(-25, -25, 50, 50);

            ctx.font = '20px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('🏗️', 0, 0);

            // 建築進度條
            ctx.fillStyle = 'rgba(0,0,0,0.6)';
            ctx.fillRect(-20, -35, 40, 6);
            ctx.fillStyle = '#22c55e';
            ctx.fillRect(-20, -35, (this.buildProgress / 100) * 40, 6);
            ctx.restore();
            return;
        }

        // 完工奇觀/軍事基地外圈光環
        ctx.beginPath();
        ctx.arc(0, 0, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.category === 'simcity' ? 'rgba(250, 204, 21, 0.15)' : 'rgba(239, 68, 68, 0.15)';
        ctx.fill();
        ctx.strokeStyle = this.category === 'simcity' ? '#facc15' : '#ef4444';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.stroke();

        // 建築圖示
        ctx.font = '34px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.icon, 0, -5);

        // 名稱與血量
        ctx.font = '11px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 3;
        ctx.fillText(this.name, 0, 25);

        ctx.restore();
    }
}
