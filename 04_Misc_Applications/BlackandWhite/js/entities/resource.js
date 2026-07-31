/**
 * 可互動物件與自然資源系統 (Resource & Interactive Entities)
 * 包含：樹木 (Wood)、稻田作物 (Food)、石塊 (Rock)、野生動物 (Sheep, Cow 等)
 * 支援「神之手」抓取 (Grab)、拖拉與拋擲物理力學 (Throw Physics)
 */
export class ResourceEntity {
    constructor(id, type, x, y) {
        this.id = id;
        this.type = type; // 'tree', 'crop', 'rock', 'animal_sheep', 'animal_cow'
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.vz = 0; // 高度/空中彈跳方向
        this.z = 0;  // 離地高度 (神之手抓起時 z > 0)

        this.isGrabbed = false;
        this.amount = this.getInitialAmount();
        this.sacrificeValue = this.getSacrificeValue();
        this.symbol = this.getSymbol();
        this.size = this.getSize();
        this.isDestroyed = false;

        // 動物的隨機走動計時器
        this.wanderTimer = Math.random() * 5;
    }

    getInitialAmount() {
        switch (this.type) {
            case 'tree': return 50 + Math.floor(Math.random() * 30);
            case 'crop': return 40 + Math.floor(Math.random() * 20);
            case 'rock': return 100;
            case 'animal_sheep': return 25;
            case 'animal_cow': return 50;
            default: return 20;
        }
    }

    getSacrificeValue() {
        switch (this.type) {
            case 'tree': return 40;        // 獻祭樹木 +40能量
            case 'crop': return 25;        // 獻祭作物 +25能量
            case 'rock': return 10;
            case 'animal_sheep': return 80;  // 獻祭動物 +80能量
            case 'animal_cow': return 150;   // 獻祭牛 +150能量
            default: return 20;
        }
    }

    getSymbol() {
        switch (this.type) {
            case 'tree': return Math.random() > 0.5 ? '🌲' : '🌳';
            case 'crop': return '🌾';
            case 'rock': return '🪨';
            case 'animal_sheep': return '🐑';
            case 'animal_cow': return '🐄';
            default: return '📦';
        }
    }

    getSize() {
        switch (this.type) {
            case 'tree': return 32;
            case 'crop': return 24;
            case 'rock': return 28;
            case 'animal_sheep': return 26;
            case 'animal_cow': return 32;
            default: return 24;
        }
    }

    /**
     * 神之手抓取
     */
    grab() {
        this.isGrabbed = true;
        this.z = 40; // 提起離地
        this.vx = 0;
        this.vy = 0;
        this.vz = 0;
    }

    /**
     * 神之手拋擲 / 放置
     */
    release(throwVx, throwVy) {
        this.isGrabbed = false;
        this.vx = throwVx * 1.5;
        this.vy = throwVy * 1.5;
        this.vz = Math.hypot(throwVx, throwVy) * 0.3; // 拋物線高度初速
    }

    update(dt) {
        if (this.isDestroyed) return;

        // 如果被抓著，不動，位置由神之手控制
        if (this.isGrabbed) return;

        // 處理拋擲或空中的物理落地
        if (this.z > 0 || Math.abs(this.vx) > 5 || Math.abs(this.vy) > 5) {
            this.x += this.vx * dt;
            this.y += this.vy * dt;
            this.z += this.vz * dt;
            this.vz -= 300 * dt; // 重力加速度

            // 地板摩擦力
            this.vx *= 0.95;
            this.vy *= 0.95;

            // 落地
            if (this.z <= 0) {
                this.z = 0;
                this.vz = -this.vz * 0.4; // 彈跳
                if (Math.abs(this.vz) < 10) this.vz = 0;
            }
        } else if (this.type.startsWith('animal_')) {
            // 動物在地上閒逛 (Wander AI)
            this.wanderTimer -= dt;
            if (this.wanderTimer <= 0) {
                this.wanderTimer = 3 + Math.random() * 4;
                const angle = Math.random() * Math.PI * 2;
                const speed = 15;
                this.vx = Math.cos(angle) * speed;
                this.vy = Math.sin(angle) * speed;
            }
            this.x += this.vx * dt;
            this.y += this.vy * dt;
            this.vx *= 0.9;
            this.vy *= 0.9;
        }
    }

    /**
     * 遭受神力破壞或採集
     */
    takeDamage(dmg, particleEngine = null) {
        this.amount -= dmg;
        if (particleEngine) {
            particleEngine.addParticle({
                x: this.x, y: this.y - this.z,
                vx: (Math.random() - 0.5) * 50, vy: -50,
                size: 6, color: this.type === 'tree' ? '#86efac' : '#fde047',
                decay: 0.05
            });
        }
        if (this.amount <= 0) {
            this.isDestroyed = true;
        }
    }

    render(ctx, time) {
        if (this.isDestroyed) return;

        ctx.save();
        const renderX = this.x;
        const renderY = this.y - this.z; // Z軸往螢幕上方偏移

        // 1. 繪製地面陰影 (如果被提起，陰影會縮小變淡)
        const shadowScale = Math.max(0.3, 1 - this.z / 150);
        ctx.beginPath();
        ctx.ellipse(this.x, this.y, (this.size / 2) * shadowScale, (this.size / 4) * shadowScale, 0, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 0, 0, ${0.3 * shadowScale})`;
        ctx.fill();

        // 2. 繪製物件本體符號
        ctx.font = `${this.size}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // 抓取狀態特效光環
        if (this.isGrabbed) {
            ctx.shadowColor = '#38bdf8';
            ctx.shadowBlur = 16;
        }
        
        ctx.fillText(this.symbol, renderX, renderY);
        ctx.restore();
    }
}
