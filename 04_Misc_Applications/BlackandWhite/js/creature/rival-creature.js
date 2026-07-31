import { getSpeciesById } from './creature-data.js?v=3';

/**
 * 敵對文明神獸與巨獸格鬥系統 (Rival Civilization AI Creatures & Titan Combat)
 * 善與惡2專屬：古挪威芬里爾神狼、日本幕府妖虎、阿茲特克太陽神龍
 * 具備巡邏守城、主動攻伐我方村莊、以及與玩家神獸進行驚天動地的【巨獸對決】(Titan Combat)！
 */

export class RivalCreature {
    constructor(speciesId, faction, x, y, homeVillage) {
        this.species = getSpeciesById(speciesId) || getSpeciesById('wolf');
        this.faction = faction; // 'norse', 'japanese', 'aztec', 'rival'
        this.name = this.getFactionCreatureName(faction, this.species.name);
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.z = 0;
        this.homeVillage = homeVillage;

        // 巨獸數值 (高於普通神獸，極致挑戰！)
        const mult = faction === 'aztec' ? 2.5 : (faction === 'norse' ? 1.8 : 2.0);
        this.health = 100 * mult;
        this.maxHealth = 100 * mult;
        this.mana = 100;
        this.scale = mult;
        this.attackPower = 25 * mult;

        this.state = 'patrolling'; // 'patrolling', 'invading', 'titan_combat', 'casting'
        this.targetEntity = null;
        this.decisionTimer = 3;
        this.castCooldown = 5;
        this.combatCooldown = 0;
        this.isDead = false;
        this.thought = `「吼！我是護衛${this.getFactionName(faction)}的終極守護神獸！」`;
    }

    getFactionName(faction) {
        if (faction === 'norse') return '古挪威文明';
        if (faction === 'japanese') return '幕府日本文明';
        if (faction === 'aztec') return '阿茲特克帝國';
        return '敵對部落';
    }

    getFactionCreatureName(faction, baseName) {
        if (faction === 'norse') return '🐺 北歐芬里爾神狼';
        if (faction === 'japanese') return '🐯 幕府白虎神君';
        if (faction === 'aztec') return '🐉 太陽羽蛇神龍';
        return `敵對神獸·${baseName}`;
    }

    update(dt, villages, villagers, playerCreature, particleEngine, miracleCaster, soundEngine) {
        if (this.isDead) return;

        if (this.castCooldown > 0) this.castCooldown -= dt;
        if (this.combatCooldown > 0) this.combatCooldown -= dt;

        // 1. 檢測是否與玩家神獸相遇進而引發【巨獸對決】(Titan vs Titan Clash)！
        if (playerCreature && !playerCreature.isDead) {
            const distToPlayerBeast = Math.hypot(playerCreature.x - this.x, playerCreature.y - this.y);
            if (distToPlayerBeast <= 180) {
                this.state = 'titan_combat';
                this.executeTitanCombat(playerCreature, villagers, particleEngine, soundEngine, dt);
                return;
            }
        }

        // 2. AI 決策週期
        this.decisionTimer -= dt;
        if (this.decisionTimer <= 0) {
            this.decisionTimer = 3 + Math.random() * 2;
            this.makeDecision(villages, playerCreature);
        }

        // 3. 執行移動與對一般村莊/部隊的攻擊
        if (this.targetEntity) {
            const dx = this.targetEntity.x - this.x;
            const dy = this.targetEntity.y - this.y;
            const dist = Math.hypot(dx, dy);

            if (dist <= 60) {
                if (this.combatCooldown <= 0) {
                    this.combatCooldown = 1.5;
                    this.executeSmash(this.targetEntity, villagers, particleEngine, soundEngine);
                }
            } else {
                const spd = this.species.spd * (this.faction === 'norse' ? 1.3 : 1.0);
                this.vx = (dx / dist) * spd;
                this.vy = (dy / dist) * spd;
                this.x += this.vx * dt;
                this.y += this.vy * dt;
            }
        } else if (this.homeVillage) {
            // 巡邏家園周圍
            const angle = Math.random() * Math.PI * 2;
            const dist = Math.random() * 250;
            this.targetEntity = { x: this.homeVillage.x + Math.cos(angle)*dist, y: this.homeVillage.y + Math.sin(angle)*dist, isPoint: true };
        }
    }

    makeDecision(villages, playerCreature) {
        // 40% 機率主動進攻玩家村莊或挑釁玩家神獸
        if (Math.random() < 0.45) {
            if (playerCreature && !playerCreature.isDead && Math.random() < 0.5) {
                this.targetEntity = playerCreature;
                this.thought = '「嗅到了敵對神獸的氣息...前往撲殺！」';
            } else {
                const playerV = villages.find(v => v.owner === 'player');
                if (playerV) {
                    this.targetEntity = playerV;
                    this.state = 'invading';
                    this.thought = `「代表${this.getFactionName(this.faction)}摧毀敵人的祭壇！」`;
                }
            }
        } else {
            this.state = 'patrolling';
            this.targetEntity = null;
            this.thought = `「巡視領土中...保護我們的信徒！」`;
        }
    }

    /**
     * 巨獸格鬥對戰 (Titan Combat & Crowd Panic)
     */
    executeTitanCombat(playerCreature, villagers, particleEngine, soundEngine, dt) {
        this.thought = `「⚡ 與【${playerCreature.name}】進行史詩神獸殊死對決！」`;
        playerCreature.thought = `「🔥 迎戰敵方文明的巨獸【${this.name}】！絕不退縮！」`;

        // 互相貼近格鬥
        const dx = playerCreature.x - this.x;
        const dy = playerCreature.y - this.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist > 80) {
            this.x += (dx/dist) * 40 * dt;
            this.y += (dy/dist) * 40 * dt;
        }

        // 雙方互相攻擊與施放巨獸震撼彈
        if (this.combatCooldown <= 0) {
            this.combatCooldown = 1.2;
            if (soundEngine) {
                soundEngine.playCreatureRoar(this.species.pitch, this.x);
                soundEngine.playThunder(this.x);
            }

            // 扣血
            playerCreature.health = Math.max(0, playerCreature.health - this.attackPower * 0.4);
            this.health = Math.max(0, this.health - 20 * 0.4);

            // 產生震地風暴與魔法爆破粒子
            if (particleEngine) {
                particleEngine.emitExplosion((this.x + playerCreature.x)/2, (this.y + playerCreature.y)/2, 160);
                particleEngine.emitLightning((this.x + playerCreature.x)/2, (this.y + playerCreature.y)/2, 2, () => {});
            }

            // 🌟 核心特色：巨獸格鬥震撼全場！周圍 350 範圍內村民部隊四處驚恐逃竄！
            if (villagers) {
                for (const vg of villagers) {
                    if (!vg.isDead && Math.hypot(vg.x - this.x, vg.y - this.y) <= 350) {
                        vg.triggerPanic(this.x, this.y, 6);
                    }
                }
            }

            if (playerCreature.health <= 0) {
                playerCreature.isDead = true;
                this.state = 'patrolling';
                this.thought = '「吼吼吼！我擊敗了對手神獸！這座島嶼歸我們所有！」';
            }
            if (this.health <= 0) {
                this.isDead = true;
                playerCreature.thought = '「✨ 勝利！我打敗了敵方文明的巨獸！」';
                if (particleEngine) particleEngine.emitSoul(this.x, this.y);
            }
        }
    }

    executeSmash(target, villagers, particleEngine, soundEngine) {
        if (!target || target.isPoint) return;
        if (soundEngine) {
            soundEngine.playCreatureRoar(this.species.pitch * 0.8, this.x);
            soundEngine.playSlap(this.x);
        }
        if (particleEngine) {
            particleEngine.emitExplosion(target.x, target.y, 100);
        }

        if (target.takeDamage) target.takeDamage(this.attackPower, particleEngine);
        if (target.health !== undefined) target.health -= this.attackPower;

        // 巨獸肆虐導致村民逃散
        if (villagers) {
            for (const vg of villagers) {
                if (!vg.isDead && Math.hypot(vg.x - this.x, vg.y - this.y) <= 250) {
                    vg.triggerPanic(this.x, this.y, 5);
                }
            }
        }
    }

    takeDamage(dmg, particleEngine) {
        this.health -= dmg;
        if (particleEngine) {
            particleEngine.addParticle({
                x: this.x, y: this.y, vx: (Math.random() - 0.5) * 50, vy: -40, size: 8, color: '#ef4444', decay: 0.04
            });
        }
        if (this.health <= 0) {
            this.isDead = true;
            if (particleEngine) particleEngine.emitSoul(this.x, this.y);
        }
    }

    render(ctx, time) {
        if (this.isDead) return;
        ctx.save();
        ctx.translate(this.x, this.y);

        // 敵方文明專屬光環 (挪威冰藍 / 日本紫金 / 阿茲特克太陽血紅)
        const haloColor = this.faction === 'norse' ? 'rgba(56, 189, 248, 0.3)' : (this.faction === 'japanese' ? 'rgba(168, 85, 247, 0.3)' : 'rgba(239, 68, 68, 0.35)');
        const borderColor = this.faction === 'norse' ? '#38bdf8' : (this.faction === 'japanese' ? '#a855f7' : '#ef4444');

        ctx.beginPath();
        ctx.arc(0, 0, 45 * this.scale * 0.6, 0, Math.PI * 2);
        ctx.fillStyle = haloColor;
        ctx.fill();
        ctx.lineWidth = 3;
        ctx.strokeStyle = borderColor;
        ctx.setLineDash([6, 6]);
        ctx.stroke();

        // 巨獸符號與格鬥顫抖
        ctx.font = `${Math.floor(38 * (this.scale || 1.0))}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const shake = this.state === 'titan_combat' ? (Math.random() - 0.5) * 8 : Math.sin(time * 5) * 4;
        ctx.fillText(this.species.symbol, shake, shake - 5);

        // 狀態與名稱
        ctx.font = 'bold 12px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 4;
        ctx.fillText(`${this.name} [HP: ${Math.floor(this.health)}]`, 0, -50 * (this.scale * 0.6));

        // 血量條
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(-30, -38 * (this.scale * 0.6), 60, 6);
        ctx.fillStyle = '#ef4444';
        ctx.fillRect(-30, -38 * (this.scale * 0.6), (this.health / this.maxHealth) * 60, 6);

        ctx.restore();
    }
}
