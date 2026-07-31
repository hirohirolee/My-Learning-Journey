/**
 * 神兵軍團與武士部隊系統 (Age of Empires Conquest Troops)
 * 善與惡2武力征服流核心：玩家或敵方文明可派遣部隊前進敵村、交戰、並強力征服領土
 */

export class TroopEntity {
    constructor(id, type, x, y, owner = 'player', targetVillage = null) {
        this.id = id;
        this.type = type; // 'militia', 'samurai', 'archer'
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.z = 0;
        this.owner = owner; // 'player', 'rival'
        this.targetVillage = targetVillage;

        const statsMap = {
            'militia': { name: '義勇民團', icon: '⚔️', hp: 150, atk: 18, spd: 55, range: 40 },
            'samurai': { name: '精銳武士', icon: '🗡️', hp: 300, atk: 35, spd: 65, range: 45 },
            'archer':  { name: '神射弓手', icon: '🏹', hp: 120, atk: 25, spd: 50, range: 160 }
        };

        const stats = statsMap[type] || statsMap['militia'];
        this.name = stats.name;
        this.icon = stats.icon;
        this.health = stats.hp;
        this.maxHealth = stats.hp;
        this.attackPower = stats.atk;
        this.speed = stats.spd;
        this.attackRange = stats.range;

        this.state = 'marching'; // 'marching', 'attacking', 'celebrating'
        this.targetEntity = null;
        this.attackCooldown = 0;
        this.isDead = false;
        this.size = 20;
    }

    update(dt, villages, villagers, rivalCreatures, playerCreature, particleEngine, soundEngine) {
        if (this.isDead) return;

        if (this.attackCooldown > 0) this.attackCooldown -= dt;

        // 1. 尋找交戰範圍內的敵方目標 (敵軍部隊、敵方神獸或敵方村民)
        if (!this.targetEntity || this.targetEntity.isDead || this.targetEntity.isDestroyed) {
            this.targetEntity = this.findEnemyTarget(villagers, rivalCreatures, playerCreature);
        }

        // 2. 如果有攻擊目標就在射程內攻擊，否則向目標前進
        if (this.targetEntity) {
            const dx = this.targetEntity.x - this.x;
            const dy = this.targetEntity.y - this.y;
            const dist = Math.hypot(dx, dy);

            if (dist <= this.attackRange) {
                this.state = 'attacking';
                if (this.attackCooldown <= 0) {
                    this.attackCooldown = 1.2; // 攻擊頻率
                    this.executeAttack(this.targetEntity, particleEngine, soundEngine);
                }
            } else {
                this.state = 'marching';
                this.vx = (dx / dist) * this.speed;
                this.vy = (dy / dist) * this.speed;
                this.x += this.vx * dt;
                this.y += this.vy * dt;
            }
            return;
        }

        // 3. 否則向敵方目標村莊進軍征服
        if (this.targetVillage && this.targetVillage.owner !== this.owner) {
            const dx = this.targetVillage.x - this.x;
            const dy = this.targetVillage.y - this.y;
            const dist = Math.hypot(dx, dy);

            if (dist <= 60) {
                // 到達敵方村莊中心！如果無抵抗則強力武力征服！
                this.state = 'attacking';
                if (this.attackCooldown <= 0) {
                    this.attackCooldown = 2.0;
                    this.targetVillage.takeDamage(this.attackPower * 2, particleEngine);
                    if (soundEngine) soundEngine.playSlap(this.x);
                    
                    // 造成村民恐慌逃逸
                    for (const vg of villagers) {
                        if (vg.village === this.targetVillage && !vg.isDead) {
                            vg.triggerPanic(this.x, this.y, 6);
                        }
                    }

                    // 強制削減信仰並奪取政權
                    this.targetVillage.addBelief(-15, false);
                    if (this.targetVillage.belief <= 0) {
                        this.targetVillage.owner = this.owner;
                        this.targetVillage.belief = 100;
                        this.state = 'celebrating';
                        if (particleEngine) particleEngine.emitHeal(this.x, this.y, 150, 3);
                    }
                }
            } else {
                this.state = 'marching';
                this.vx = (dx / dist) * this.speed;
                this.vy = (dy / dist) * this.speed;
                this.x += this.vx * dt;
                this.y += this.vy * dt;
            }
        } else {
            // 守備駐紮或尋找下一個非我方村莊
            const enemyV = villages.find(v => v.owner !== this.owner);
            if (enemyV) {
                this.targetVillage = enemyV;
            } else {
                this.state = 'celebrating';
            }
        }
    }

    findEnemyTarget(villagers, rivalCreatures, playerCreature) {
        let nearest = null;
        let minDist = 300; // 索敵半徑

        // 尋找敵方神獸
        if (this.owner === 'player' && rivalCreatures) {
            for (const rc of rivalCreatures) {
                if (!rc.isDead && Math.hypot(rc.x - this.x, rc.y - this.y) < minDist) {
                    nearest = rc;
                    minDist = Math.hypot(rc.x - this.x, rc.y - this.y);
                }
            }
        } else if (this.owner === 'rival' && playerCreature && !playerCreature.isDead) {
            if (Math.hypot(playerCreature.x - this.x, playerCreature.y - this.y) < minDist) {
                nearest = playerCreature;
                minDist = Math.hypot(playerCreature.x - this.x, playerCreature.y - this.y);
            }
        }

        // 尋找敵方村民與守衛
        if (!nearest && villagers) {
            for (const vg of villagers) {
                if (!vg.isDead && vg.village && vg.village.owner !== this.owner) {
                    const d = Math.hypot(vg.x - this.x, vg.y - this.y);
                    if (d < minDist) {
                        nearest = vg;
                        minDist = d;
                    }
                }
            }
        }
        return nearest;
    }

    executeAttack(target, particleEngine, soundEngine) {
        if (!target) return;
        if (soundEngine) soundEngine.playSlap(this.x);
        if (particleEngine) {
            particleEngine.addParticle({
                x: target.x, y: target.y,
                vx: (Math.random() - 0.5) * 60, vy: -40,
                size: 8, color: '#ef4444', text: '💥', decay: 0.05
            });
        }

        if (target.takeDamage) {
            target.takeDamage(this.attackPower, particleEngine);
        } else if (target.health !== undefined) {
            target.health -= this.attackPower;
            if (target.health <= 0) target.isDead = true;
        }

        // 遠程弓箭特效
        if (this.type === 'archer' && particleEngine) {
            particleEngine.addParticle({
                x: (this.x + target.x)/2, y: (this.y + target.y)/2 - 20,
                vx: (target.x - this.x)*0.1, vy: (target.y - this.y)*0.1,
                size: 10, color: '#facc15', text: '🏹', decay: 0.08
            });
        }
    }

    takeDamage(dmg, particleEngine) {
        this.health -= dmg;
        if (particleEngine) {
            particleEngine.addParticle({
                x: this.x, y: this.y, vx: 0, vy: -30, size: 6, color: '#ef4444', decay: 0.05
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

        // 我方 vs 敵軍部隊底框
        ctx.beginPath();
        ctx.arc(0, 0, 16, 0, Math.PI * 2);
        ctx.fillStyle = this.owner === 'player' ? 'rgba(56, 189, 248, 0.4)' : 'rgba(239, 68, 68, 0.4)';
        ctx.fill();
        ctx.strokeStyle = this.owner === 'player' ? '#38bdf8' : '#ef4444';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 兵種圖示與武器
        ctx.font = '24px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const bounce = this.state === 'marching' ? Math.sin(time * 10) * 3 : 0;
        ctx.fillText(this.icon, 0, bounce);

        // 血量條
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(-15, -22, 30, 4);
        ctx.fillStyle = '#22c55e';
        ctx.fillRect(-15, -22, (this.health / this.maxHealth) * 30, 4);

        ctx.restore();
    }
}
