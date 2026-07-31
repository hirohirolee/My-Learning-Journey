/**
 * 高效能粒子與神蹟特效引擎 (Particle & Miracle VFX Engine)
 * 負責渲染所有奇蹟法術、自然現象、獻祭靈魂與善惡鳥群特效
 */
export class ParticleEngine {
    constructor() {
        this.particles = [];
        this.projectiles = []; // 移動中的投射物 (火球、飛翔的鳥群/蝙蝠、狼群、獻祭靈魂)
        this.persistentEffects = []; // 持續性特效 (龍捲風、魔法防禦穹頂、暴風雨雲層)
    }

    /**
     * 生成通用粒子
     */
    addParticle(config) {
        this.particles.push({
            x: config.x || 0,
            y: config.y || 0,
            vx: config.vx || 0,
            vy: config.vy || 0,
            size: config.size || 5,
            color: config.color || '#ffffff',
            alpha: config.alpha !== undefined ? config.alpha : 1.0,
            decay: config.decay || 0.02,
            gravity: config.gravity || 0,
            type: config.type || 'normal',
            rotation: config.rotation || 0,
            vRot: config.vRot || 0,
            text: config.text || null // 若是文字符號(如💖或🕊️)
        });
    }

    /**
     * 釋放火球神力特效 (單顆或多顆連環轟炸)
     */
    emitFireball(startX, startY, targetX, targetY, count = 1, onImpact = null) {
        for (let i = 0; i < count; i++) {
            const delay = i * 250; // 連環轟炸時間差
            setTimeout(() => {
                const angle = Math.atan2(targetY - startY, targetX - startX) + (Math.random() - 0.5) * (count > 1 ? 0.3 : 0);
                const speed = 400 + Math.random() * 100;
                this.projectiles.push({
                    type: 'fireball',
                    x: startX + (Math.random() - 0.5) * 40,
                    y: startY - 200, // 從天降下或從上帝視角射出
                    vx: Math.cos(angle) * speed,
                    vy: Math.sin(angle) * speed,
                    targetX: targetX + (Math.random() - 0.5) * (count > 1 ? 120 : 0),
                    targetY: targetY + (Math.random() - 0.5) * (count > 1 ? 120 : 0),
                    size: count === 8 ? 24 : (count === 3 ? 30 : 36),
                    color: '#ef4444',
                    onImpact: onImpact
                });
            }, delay);
        }
    }

    /**
     * 釋放雷電神力特效 (落雷劈擊)
     */
    emitLightning(targetX, targetY, intensity = 1, onImpact = null) {
        // 從天際 (targetY - 600) 劈擊到地面
        const startX = targetX + (Math.random() - 0.5) * 100;
        const startY = targetY - 600;
        
        // 產生鋸齒狀閃電線條粒子
        let currentX = startX;
        let currentY = startY;
        const segments = [];
        
        while (currentY < targetY) {
            const nextX = currentX + (Math.random() - 0.5) * 60 * intensity;
            const nextY = Math.min(targetY, currentY + 30 + Math.random() * 40);
            segments.push({ x1: currentX, y1: currentY, x2: nextX, y2: nextY });
            currentX = nextX;
            currentY = nextY;
        }

        this.persistentEffects.push({
            type: 'lightning_strike',
            segments: segments,
            alpha: 1.0,
            duration: 0.35,
            color: intensity > 1 ? '#a855f7' : '#38bdf8',
            width: 3 * intensity
        });

        // 觸發雷擊地面爆炸火花
        this.emitExplosion(targetX, targetY, 60 * intensity, intensity > 1 ? '#c084fc' : '#7dd3fc');
        if (onImpact) onImpact(targetX, targetY);
    }

    /**
     * 釋放治療神力 (金光愛心與神聖十字光柱)
     */
    emitHeal(x, y, radius = 80, level = 1) {
        const count = level * 15;
        // 產生上升的綠光與金光愛心
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI * 2;
            const dist = Math.random() * radius;
            this.addParticle({
                x: x + Math.cos(angle) * dist,
                y: y + Math.sin(angle) * dist,
                vx: (Math.random() - 0.5) * 20,
                vy: -40 - Math.random() * 50,
                size: 16 + Math.random() * 10,
                color: level === 3 ? '#fbbf24' : '#34d399',
                alpha: 1.0,
                decay: 0.015,
                text: Math.random() > 0.4 ? '✨' : (level === 3 ? '🌟' : '💚')
            });
        }

        // 地面神聖光環
        this.persistentEffects.push({
            type: 'holy_circle',
            x: x, y: y, radius: radius,
            alpha: 0.8, duration: 1.5,
            color: level === 3 ? 'rgba(251, 191, 36, 0.4)' : 'rgba(52, 211, 153, 0.4)'
        });
    }

    /**
     * 釋放暴風雨/降雨/龍捲風 (Storm & Tornado)
     */
    emitStorm(x, y, radius = 150, hasLightning = false, hasTornado = false, duration = 8) {
        this.persistentEffects.push({
            type: 'storm_cloud',
            x: x, y: y, radius: radius,
            duration: duration,
            hasLightning: hasLightning,
            hasTornado: hasTornado,
            timer: 0
        });
    }

    /**
     * 釋放爆破神力與爆炸火花
     */
    emitExplosion(x, y, radius = 80, color = '#f97316') {
        // 爆炸波光環
        this.persistentEffects.push({
            type: 'shockwave',
            x: x, y: y, radius: 5, maxRadius: radius,
            alpha: 1.0, duration: 0.4, color: color
        });

        // 噴濺碎屑與火焰
        const count = Math.floor(radius / 2);
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = 50 + Math.random() * 250;
            this.addParticle({
                x: x, y: y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                size: 4 + Math.random() * 8,
                color: Math.random() > 0.5 ? color : '#facc15',
                alpha: 1.0,
                decay: 0.02 + Math.random() * 0.02,
                gravity: 100
            });
        }
    }

    /**
     * 釋放獻祭靈魂升天特效 (Soul Ascending to Altar)
     */
    emitSoul(fromX, fromY, altarX, altarY, value = 50) {
        this.projectiles.push({
            type: 'soul',
            x: fromX, y: fromY,
            vx: 0, vy: -100,
            targetX: altarX, targetY: altarY,
            speed: 300,
            size: 20,
            text: '👻',
            color: '#60a5fa',
            value: value
        });
    }

    /**
     * 釋放怪物飛翔神力 (白鴿 vs 蝙蝠)
     */
    emitMonsterFlight(x, y, isGood = true, count = 12) {
        const symbol = isGood ? '🕊️' : '🦇';
        for (let i = 0; i < count; i++) {
            const angle = (i / count) * Math.PI * 2;
            const speed = 80 + Math.random() * 60;
            this.projectiles.push({
                type: 'flying_creature',
                x: x + (Math.random() - 0.5) * 40,
                y: y + (Math.random() - 0.5) * 40,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                size: 24,
                text: symbol,
                life: 6 + Math.random() * 4,
                rotAngle: angle
            });
        }
    }

    /**
     * 召喚狼群神力 (Wolf Pack)
     */
    emitWolfPack(x, y, count = 6, targetVillage = null) {
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI * 2;
            this.projectiles.push({
                type: 'wolf',
                x: x + Math.cos(angle) * 30,
                y: y + Math.sin(angle) * 30,
                vx: (Math.random() - 0.5) * 100,
                vy: (Math.random() - 0.5) * 100,
                size: 28,
                text: '🐺',
                life: 15, // 存活 15 秒
                targetVillage: targetVillage,
                attackTimer: 0
            });
        }
    }

    /**
     * 更新所有特效狀態
     */
    update(dt, worldEntities = null) {
        // 1. 更新普通粒子
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            p.vy += p.gravity * dt;
            p.rotation += p.vRot * dt;
            p.alpha -= p.decay * (dt * 60);

            if (p.alpha <= 0 || p.size <= 0.5) {
                this.particles.splice(i, 1);
            }
        }

        // 2. 更新移動投射物 (火球、靈魂、狼群、鳥群)
        for (let i = this.projectiles.length - 1; i >= 0; i--) {
            const proj = this.projectiles[i];
            
            if (proj.type === 'fireball') {
                const dx = proj.targetX - proj.x;
                const dy = proj.targetY - proj.y;
                const dist = Math.hypot(dx, dy);
                if (dist < 20) {
                    // 到達目標點，爆炸！
                    this.emitExplosion(proj.targetX, proj.targetY, proj.size * 3.5);
                    if (proj.onImpact) proj.onImpact(proj.targetX, proj.targetY);
                    this.projectiles.splice(i, 1);
                    continue;
                }
                const speed = Math.hypot(proj.vx, proj.vy);
                proj.vx = (dx / dist) * speed;
                proj.vy = (dy / dist) * speed;
                proj.x += proj.vx * dt;
                proj.y += proj.vy * dt;

                // 產生火球尾跡
                this.addParticle({
                    x: proj.x + (Math.random() - 0.5) * 10,
                    y: proj.y + (Math.random() - 0.5) * 10,
                    vx: -proj.vx * 0.2 + (Math.random() - 0.5) * 30,
                    vy: -proj.vy * 0.2 - 20,
                    size: proj.size * 0.6,
                    color: Math.random() > 0.4 ? '#ef4444' : '#f97316',
                    alpha: 0.8, decay: 0.05
                });
            } 
            else if (proj.type === 'soul') {
                const dx = proj.targetX - proj.x;
                const dy = proj.targetY - proj.y;
                const dist = Math.hypot(dx, dy);
                if (dist < 30) {
                    // 抵達祭壇，觸發能量增加提示
                    this.addParticle({
                        x: proj.targetX, y: proj.targetY - 20,
                        vx: 0, vy: -50,
                        size: 20, color: '#facc15', text: `+${proj.value}⚡`,
                        alpha: 1.0, decay: 0.02
                    });
                    this.projectiles.splice(i, 1);
                    continue;
                }
                proj.x += (dx / dist) * proj.speed * dt;
                proj.y += (dy / dist) * proj.speed * dt;
            }
            else if (proj.type === 'flying_creature') {
                proj.life -= dt;
                proj.x += proj.vx * dt;
                proj.y += proj.vy * dt;
                // 盤旋移動
                proj.vx += Math.cos(proj.life * 3) * 50 * dt;
                proj.vy += Math.sin(proj.life * 3) * 50 * dt;
                if (proj.life <= 0) this.projectiles.splice(i, 1);
            }
            else if (proj.type === 'wolf') {
                proj.life -= dt;
                proj.x += proj.vx * dt;
                proj.y += proj.vy * dt;
                // 狼群尋找附近目標或隨機跑動
                if (proj.targetVillage && Math.random() < 0.05) {
                    const dx = proj.targetVillage.x - proj.x;
                    const dy = proj.targetVillage.y - proj.y;
                    const dist = Math.hypot(dx, dy);
                    if (dist > 50) {
                        proj.vx = (dx / dist) * 120;
                        proj.vy = (dy / dist) * 120;
                    } else {
                        // 攻擊村莊或村民
                        this.addParticle({ x: proj.x, y: proj.y, text: '💥', size: 16, decay: 0.05 });
                    }
                } else if (Math.random() < 0.02) {
                    proj.vx = (Math.random() - 0.5) * 150;
                    proj.vy = (Math.random() - 0.5) * 150;
                }
                if (proj.life <= 0) this.projectiles.splice(i, 1);
            }
        }

        // 3. 更新持續性特效 (暴風雨雲、雷電、穹頂護盾)
        for (let i = this.persistentEffects.length - 1; i >= 0; i--) {
            const eff = this.persistentEffects[i];
            if (eff.duration !== undefined) {
                eff.duration -= dt;
                if (eff.duration <= 0) {
                    this.persistentEffects.splice(i, 1);
                    continue;
                }
            }

            if (eff.type === 'storm_cloud') {
                eff.timer += dt;
                // 持續產生雨滴
                for (let r = 0; r < 3; r++) {
                    const angle = Math.random() * Math.PI * 2;
                    const dist = Math.random() * eff.radius;
                    this.addParticle({
                        x: eff.x + Math.cos(angle) * dist,
                        y: eff.y + Math.sin(angle) * dist - 150,
                        vx: -30, vy: 300,
                        size: 3, color: '#60a5fa', alpha: 0.6, decay: 0.03
                    });
                }
                // 隨機閃電
                if (eff.hasLightning && Math.random() < 0.05 * (dt * 60)) {
                    const lx = eff.x + (Math.random() - 0.5) * eff.radius * 1.5;
                    const ly = eff.y + (Math.random() - 0.5) * eff.radius * 1.5;
                    this.emitLightning(lx, ly, 1);
                }
                // 龍捲風特效
                if (eff.hasTornado) {
                    const tx = eff.x + Math.cos(eff.timer * 2) * (eff.radius * 0.5);
                    const ty = eff.y + Math.sin(eff.timer * 2) * (eff.radius * 0.5);
                    this.addParticle({
                        x: tx, y: ty, vx: (Math.random()-0.5)*100, vy: -150,
                        size: 24, text: '🌪️', alpha: 0.9, decay: 0.03
                    });
                }
            }
            else if (eff.type === 'shockwave') {
                eff.radius += (eff.maxRadius - eff.radius) * 15 * dt;
                eff.alpha = eff.duration / 0.4;
            }
        }
    }

    /**
     * 渲染所有粒子與法術特效
     */
    render(ctx) {
        ctx.save();

        // 1. 渲染持續性特效底層 (如神聖光環、護盾)
        for (const eff of this.persistentEffects) {
            if (eff.type === 'holy_circle') {
                ctx.beginPath();
                ctx.arc(eff.x, eff.y, eff.radius, 0, Math.PI * 2);
                ctx.fillStyle = eff.color;
                ctx.fill();
                ctx.lineWidth = 3;
                ctx.strokeStyle = '#facc15';
                ctx.stroke();
            } else if (eff.type === 'shockwave') {
                ctx.beginPath();
                ctx.arc(eff.x, eff.y, eff.radius, 0, Math.PI * 2);
                ctx.strokeStyle = eff.color;
                ctx.lineWidth = 4 * eff.alpha;
                ctx.globalAlpha = eff.alpha;
                ctx.stroke();
                ctx.globalAlpha = 1.0;
            }
        }

        // 2. 渲染投射物與生物符號 (火球、狼群、白鴿/蝙蝠、靈魂)
        for (const proj of this.projectiles) {
            if (proj.text) {
                ctx.font = `${proj.size}px sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(proj.text, proj.x, proj.y);
            } else if (proj.type === 'fireball') {
                // 火球本體發光
                const grad = ctx.createRadialGradient(proj.x, proj.y, 0, proj.x, proj.y, proj.size);
                grad.addColorStop(0, '#fef08a');
                grad.addColorStop(0.4, '#f97316');
                grad.addColorStop(1, 'transparent');
                ctx.fillStyle = grad;
                ctx.beginPath();
                ctx.arc(proj.x, proj.y, proj.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        // 3. 渲染普通粒子與閃電
        for (const p of this.particles) {
            ctx.globalAlpha = Math.max(0, p.alpha);
            if (p.text) {
                ctx.font = `${p.size}px sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(p.text, p.x, p.y);
            } else {
                ctx.fillStyle = p.color;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        ctx.globalAlpha = 1.0;

        // 4. 渲染雷電鋸齒線條 (頂層)
        for (const eff of this.persistentEffects) {
            if (eff.type === 'lightning_strike' && eff.segments) {
                ctx.save();
                ctx.strokeStyle = eff.color;
                ctx.lineWidth = eff.width;
                ctx.shadowColor = eff.color;
                ctx.shadowBlur = 16;
                ctx.beginPath();
                for (const seg of eff.segments) {
                    ctx.moveTo(seg.x1, seg.y1);
                    ctx.lineTo(seg.x2, seg.y2);
                }
                ctx.stroke();
                // 核心白線
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = eff.width * 0.5;
                ctx.stroke();
                ctx.restore();
            } else if (eff.type === 'storm_cloud') {
                // 烏雲頂蓋
                ctx.fillStyle = 'rgba(15, 23, 42, 0.4)';
                ctx.beginPath();
                ctx.arc(eff.x, eff.y - 120, eff.radius * 0.8, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        ctx.restore();
    }
}
