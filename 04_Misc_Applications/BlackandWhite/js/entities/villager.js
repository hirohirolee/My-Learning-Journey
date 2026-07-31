/**
 * 村民 AI 邏輯與信仰度系統 (Villager AI & Belief System - Crowd Panic & Emigration)
 * 狀態：閒置(idle)、伐木(gathering_wood)、耕作(gathering_food)、返回交納(returning)、
 *       祭壇祈禱(praying)、驚慌逃命(fleeing)、被神之手抓取(grabbed)
 * 善與惡2專屬：包含巨獸對打與武裝部隊入侵時的恐慌逃竄 AI (Crowd Panic dynamics)
 */
export class VillagerEntity {
    constructor(id, village, x, y, role = 'peasant') {
        this.id = id;
        this.village = village; // 所屬村莊
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.z = 0;
        this.vz = 0;

        this.role = role; // 'peasant', 'lumberjack', 'farmer', 'priest'
        this.state = 'idle';
        this.targetEntity = null;
        this.carryingAmount = 0;
        this.carryingType = null;
        
        this.speed = 45 + Math.random() * 15;
        this.isGrabbed = false;
        this.isDead = false;
        this.sacrificeValue = 200; // 獻祭活人村民 +200 能量！

        // 信仰歸屬度與態度數值
        this.beliefInPlayer = 0; // 0 ~ 100
        this.emotion = null; // '💖', '😱', '🙏', '😤'
        this.emotionTimer = 0;

        this.stateTimer = Math.random() * 2;
    }

    /**
     * 神之手抓取
     */
    grab() {
        this.isGrabbed = true;
        this.state = 'grabbed';
        this.z = 50;
        this.vx = 0;
        this.vy = 0;
        this.showEmotion('😲', 3);
    }

    /**
     * 拋擲/放下
     */
    release(throwVx, throwVy) {
        this.isGrabbed = false;
        this.state = 'idle';
        this.vx = throwVx * 1.5;
        this.vy = throwVy * 1.5;
        this.vz = Math.hypot(throwVx, throwVy) * 0.35;
        if (Math.hypot(throwVx, throwVy) > 200) {
            this.showEmotion('😱', 3);
        }
    }

    showEmotion(symbol, duration = 2.5) {
        this.emotion = symbol;
        this.emotionTimer = duration;
    }

    /**
     * 🌟 善與惡2專屬：群體戰爭與巨獸對打恐慌逃逸 (Crowd Panic Dynamics)
     * 當兩隻巨獸在附近交戰或武士侵入村莊時，村民感到無比恐懼尖叫四散！
     */
    triggerPanic(sourceX, sourceY, duration = 5) {
        if (this.isDead || this.isGrabbed || this.state === 'fleeing') return;
        this.showEmotion('😱', duration);
        this.state = 'fleeing';
        this.stateTimer = duration;

        const dx = this.x - sourceX;
        const dy = this.y - sourceY;
        const dist = Math.hypot(dx, dy) || 1;
        // 向危險源的反方向極速逃亡
        this.vx = (dx / dist) * (this.speed * 2.8) + (Math.random()-0.5) * 60;
        this.vy = (dy / dist) * (this.speed * 2.8) + (Math.random()-0.5) * 60;
    }

    /**
     * 受到奇蹟或神威影響
     */
    receiveMiracleImpact(isGood, impactAmount, godAlignRef) {
        if (isGood) {
            this.showEmotion('💖', 4);
            this.beliefInPlayer = Math.min(100, this.beliefInPlayer + impactAmount);
            if (this.village) this.village.addBelief(impactAmount, true);
        } else {
            this.showEmotion('😱', 4);
            this.state = 'fleeing';
            this.stateTimer = 4;
            this.vx = (Math.random() - 0.5) * 160;
            this.vy = (Math.random() - 0.5) * 160;
            this.beliefInPlayer = Math.min(100, this.beliefInPlayer + impactAmount * 1.2);
            if (this.village) this.village.addBelief(impactAmount * 1.2, false);
        }
    }

    update(dt, worldResources, altarPos, soundEngine = null) {
        if (this.isDead || this.isGrabbed) return;

        // 表情計時
        if (this.emotionTimer > 0) {
            this.emotionTimer -= dt;
            if (this.emotionTimer <= 0) this.emotion = null;
        }

        // 處理空中掉落或滑行
        if (this.z > 0 || Math.abs(this.vx) > 10 || Math.abs(this.vy) > 10) {
            this.x += this.vx * dt;
            this.y += this.vy * dt;
            this.z += this.vz * dt;
            this.vz -= 350 * dt; // 重力
            this.vx *= 0.95;
            this.vy *= 0.95;

            if (this.z <= 0) {
                this.z = 0;
                this.vz = 0;
                if (Math.hypot(this.vx, this.vy) > 250) {
                    this.isDead = true; // 摔死
                    if (soundEngine) soundEngine.playSlap(this.x);
                }
            }
            return;
        }

        // 狀態計時器與 AI 決策
        this.stateTimer -= dt;
        if (this.stateTimer <= 0) {
            this.makeDecision(worldResources, altarPos);
        }

        // 執行當前狀態動作
        this.executeState(dt, altarPos);
    }

    makeDecision(worldResources, altarPos) {
        if (!this.village || this.village.isDestroyed) {
            this.state = 'idle';
            this.stateTimer = 2;
            return;
        }

        // 如果村莊處於全體祈禱模式
        if (this.village.isPrayingMode && this.village.owner === 'player') {
            this.state = 'praying';
            this.stateTimer = 5;
            this.targetEntity = altarPos ? { x: altarPos.x, y: altarPos.y, isPoint: true } : null;
            return;
        }

        if (this.role === 'priest') {
            this.state = 'praying';
            this.stateTimer = 6;
            this.targetEntity = altarPos ? { x: altarPos.x, y: altarPos.y, isPoint: true } : null;
            return;
        }

        if (this.role === 'lumberjack') {
            if (this.carryingAmount >= 20) {
                this.state = 'returning';
                this.targetEntity = this.village;
            } else {
                this.state = 'gathering_wood';
                this.targetEntity = this.findNearestResource(worldResources, 'tree');
            }
            this.stateTimer = 4;
            return;
        }

        // 'peasant' / 'farmer'
        if (this.carryingAmount >= 20) {
            this.state = 'returning';
            this.targetEntity = this.village;
        } else {
            this.state = 'gathering_food';
            this.targetEntity = this.findNearestResource(worldResources, 'crop');
            if (!this.targetEntity) {
                this.targetEntity = this.findNearestResource(worldResources, 'tree');
                if (this.targetEntity) this.state = 'gathering_wood';
            }
        }
        this.stateTimer = 4;
    }

    findNearestResource(resources, typePrefix) {
        if (!resources) return null;
        let nearest = null;
        let minDist = Infinity;
        for (const res of resources) {
            if (!res.isDestroyed && res.type.startsWith(typePrefix)) {
                const dist = Math.hypot(res.x - this.x, res.y - this.y);
                if (dist < minDist && dist < 450) {
                    minDist = dist;
                    nearest = res;
                }
            }
        }
        return nearest;
    }

    executeState(dt, altarPos) {
        switch (this.state) {
            case 'fleeing':
                this.x += this.vx * dt;
                this.y += this.vy * dt;
                break;

            case 'praying':
                if (this.targetEntity && Math.hypot(this.x - this.targetEntity.x, this.y - this.targetEntity.y) > 60) {
                    this.moveTowards(this.targetEntity.x, this.targetEntity.y, dt, 0.7);
                } else {
                    if (Math.random() < 0.05) this.showEmotion('🙏', 2);
                }
                break;

            case 'gathering_wood':
            case 'gathering_food':
                if (!this.targetEntity || this.targetEntity.isDestroyed) {
                    this.stateTimer = 0;
                    return;
                }
                if (Math.hypot(this.x - this.targetEntity.x, this.y - this.targetEntity.y) <= 20) {
                    // 採集
                    const gathered = this.targetEntity.harvest(dt * 10);
                    this.carryingAmount += gathered;
                    this.carryingType = this.state === 'gathering_wood' ? 'wood' : 'food';
                    if (this.carryingAmount >= 20 || this.targetEntity.isDestroyed) {
                        this.state = 'returning';
                        this.targetEntity = this.village;
                    }
                } else {
                    this.moveTowards(this.targetEntity.x, this.targetEntity.y, dt);
                }
                break;

            case 'returning':
                if (!this.targetEntity || this.targetEntity.isDestroyed) {
                    this.stateTimer = 0;
                    return;
                }
                if (Math.hypot(this.x - this.targetEntity.x, this.y - this.targetEntity.y) <= 30) {
                    // 上繳物資與增加村莊繁榮度
                    if (this.carryingType === 'wood') {
                        this.village.wood += this.carryingAmount;
                        this.village.prosperity += 1;
                    } else if (this.carryingType === 'food') {
                        this.village.food += this.carryingAmount;
                        this.village.prosperity += 1;
                    }
                    this.carryingAmount = 0;
                    this.carryingType = null;
                    this.stateTimer = 0; // 重新決策
                } else {
                    this.moveTowards(this.targetEntity.x, this.targetEntity.y, dt);
                }
                break;

            case 'idle':
            default:
                if (Math.random() < 0.1) {
                    this.vx = (Math.random() - 0.5) * 20;
                    this.vy = (Math.random() - 0.5) * 20;
                }
                this.x += this.vx * dt;
                this.y += this.vy * dt;
                break;
        }
    }

    moveTowards(tx, ty, dt, speedMult = 1.0) {
        const dx = tx - this.x;
        const dy = ty - this.y;
        const dist = Math.hypot(dx, dy);
        if (dist > 5) {
            const spd = this.speed * speedMult;
            this.vx = (dx / dist) * spd;
            this.vy = (dy / dist) * spd;
            this.x += this.vx * dt;
            this.y += this.vy * dt;
        }
    }

    render(ctx, time) {
        if (this.isDead) return;
        ctx.save();
        ctx.translate(this.x, this.y - this.z);

        // 影子
        if (this.z > 0) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
            ctx.beginPath();
            ctx.arc(0, this.z, 8, 0, Math.PI * 2);
            ctx.fill();
        }

        // 村民圖示
        ctx.font = '22px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        let icon = '🧑‍🌾';
        if (this.role === 'priest') icon = '🧙‍♂️';
        if (this.role === 'lumberjack') icon = '🪓';
        if (this.carryingType === 'wood') icon = '🪵';
        if (this.carryingType === 'food') icon = '🌾';

        // 奔跑上下晃動
        const bounce = (this.state === 'fleeing' || this.state === 'gathering_wood' || this.state === 'returning') ? Math.sin(time * 12 + this.id) * 3 : 0;
        ctx.fillText(icon, 0, bounce);

        // 心情氣泡
        if (this.emotion) {
            ctx.font = '16px sans-serif';
            ctx.fillText(this.emotion, 0, -22 + bounce);
        }

        ctx.restore();
    }
}
