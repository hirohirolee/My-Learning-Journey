import { creatureSkins } from '../meta/creature-skins.js?v=3';

/**
 * 2D/3D Canvas 渲染引擎 (Island & Terrain Renderer)
 * 負責繪製海灣水源、綠意/暗黑地形、神聖領域光圈、日夜光影與島上所有實體 (物體、村莊、神獸)
 */
export class CanvasRenderer {
    constructor(canvas, camera) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.camera = camera;

        this.time = 0;
        this.islandRadius = 800; // 島嶼半徑
        this.centerWorld = { x: 1000, y: 1000 };

        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    /**
     * 主渲染流程
     */
    render(dt, worldEntities, villages, creature, particleEngine, godAlignment) {
        if (!this.ctx) return;
        this.time += dt;
        const ctx = this.ctx;

        // 1. 清空畫布與設定海浪背景
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.renderOcean(ctx, godAlignment);

        // 2. 應用攝影機縮放與平移
        this.camera.apply(ctx);

        // 3. 繪製島嶼陸地地形與沙灘
        this.renderIslandTerrain(ctx, godAlignment);

        // 4. 繪製村莊神聖領域光圈 (Boundary Rings)
        this.renderBoundaryRings(ctx, villages, godAlignment);

        // 5. 按照 Y 座標排序實體 (Y-sort / 2.5D 遮擋排序)
        const allEntities = [...worldEntities];
        if (creature) allEntities.push(creature);
        allEntities.sort((a, b) => a.y - b.y);

        // 6. 繪製所有實體 (村莊中心、樹木、石塊、動物、村民與神獸)
        for (const entity of allEntities) {
            if (entity.render) {
                entity.render(ctx, this.time);
                if (entity === creature && creatureSkins) {
                    creatureSkins.renderAccessory(ctx, creature, creature.x, creature.y, 40 * (creature.scale || 1), dt);
                }
            }
        }

        // 7. 繪製粒子與法術特效
        if (particleEngine) {
            particleEngine.render(ctx);
        }

        // 8. 恢復攝影機矩陣
        this.camera.restore(ctx);

        // 9. 繪製螢幕空間的光影渲染 (Vignette / 善惡光照濾鏡)
        this.renderScreenLighting(ctx, godAlignment);
    }

    /**
     * 繪製動態海浪海洋背景
     */
    renderOcean(ctx, alignment) {
        // 善神(蔚藍大海) vs 惡神(血紅深淵海)
        const isEvil = alignment < -30;
        const bgGrad = ctx.createRadialGradient(
            this.canvas.width / 2, this.canvas.height / 2, 100,
            this.canvas.width / 2, this.canvas.height / 2, Math.max(this.canvas.width, this.canvas.height)
        );
        if (isEvil) {
            bgGrad.addColorStop(0, '#270a14');
            bgGrad.addColorStop(1, '#090306');
        } else {
            bgGrad.addColorStop(0, '#0284c7');
            bgGrad.addColorStop(1, '#082f49');
        }
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    /**
     * 繪製島嶼地形與沙灘
     */
    renderIslandTerrain(ctx, alignment) {
        const cx = this.centerWorld.x;
        const cy = this.centerWorld.y;
        const r = this.islandRadius;
        const isEvil = alignment < -30;

        ctx.save();

        // 外圈沙灘或焦土
        ctx.beginPath();
        ctx.arc(cx, cy, r + 40, 0, Math.PI * 2);
        ctx.fillStyle = isEvil ? '#3f1f1a' : '#fde047';
        ctx.fill();

        // 淺灘浪花動畫
        ctx.strokeStyle = isEvil ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = 6 + Math.sin(this.time * 2) * 3;
        ctx.stroke();

        // 內圈陸地主地形 (圓弧與自然地形模擬)
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        
        // 漸變草地或熔岩山脈
        const landGrad = ctx.createRadialGradient(cx, cy, 100, cx, cy, r);
        if (isEvil) {
            landGrad.addColorStop(0, '#450a0a');
            landGrad.addColorStop(0.7, '#18181b');
            landGrad.addColorStop(1, '#27272a');
        } else {
            landGrad.addColorStop(0, '#22c55e');
            landGrad.addColorStop(0.7, '#15803d');
            landGrad.addColorStop(1, '#166534');
        }
        ctx.fillStyle = landGrad;
        ctx.fill();

        // 繪製島中央的山丘 / 祭壇神聖高地
        ctx.beginPath();
        ctx.arc(cx, cy - 80, 250, 0, Math.PI * 2);
        ctx.fillStyle = isEvil ? 'rgba(0, 0, 0, 0.4)' : 'rgba(255, 255, 255, 0.08)';
        ctx.fill();
        ctx.strokeStyle = isEvil ? '#ef4444' : '#86efac';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.restore();
    }

    /**
     * 繪製村莊與上帝的信仰統治領域光圈 (Boundary Rings)
     */
    renderBoundaryRings(ctx, villages, godAlignment) {
        if (!villages) return;
        const isEvil = godAlignment < -30;

        for (const v of villages) {
            ctx.save();
            ctx.beginPath();
            ctx.arc(v.x, v.y, v.boundaryRadius, 0, Math.PI * 2);
            
            // 玩家所屬村莊光圈 vs 敵對村莊光圈
            if (v.owner === 'player') {
                const color = isEvil ? 'rgba(239, 68, 68, 0.25)' : 'rgba(56, 189, 248, 0.25)';
                const borderColor = isEvil ? '#ef4444' : '#38bdf8';
                ctx.fillStyle = color;
                ctx.fill();
                ctx.lineWidth = 4;
                ctx.strokeStyle = borderColor;
                ctx.shadowColor = borderColor;
                ctx.shadowBlur = 12;
                ctx.stroke();
            } else {
                // 敵對或中立村莊 (紫色或灰色)
                ctx.fillStyle = 'rgba(168, 85, 247, 0.15)';
                ctx.fill();
                ctx.lineWidth = 3;
                ctx.strokeStyle = '#a855f7';
                ctx.setLineDash([8, 8]);
                ctx.stroke();
            }
            ctx.restore();
        }
    }

    /**
     * 螢幕空間氛圍光照與周圍暗角 (Vignette)
     */
    renderScreenLighting(ctx, alignment) {
        ctx.save();
        const w = this.canvas.width;
        const h = this.canvas.height;
        const isEvil = alignment < -30;
        const isGood = alignment > 30;

        const vigGrad = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.4, w / 2, h / 2, Math.max(w, h) * 0.75);
        vigGrad.addColorStop(0, 'transparent');
        if (isEvil) {
            vigGrad.addColorStop(1, 'rgba(153, 27, 27, 0.45)');
        } else if (isGood) {
            vigGrad.addColorStop(1, 'rgba(251, 191, 36, 0.25)');
        } else {
            vigGrad.addColorStop(1, 'rgba(0, 0, 0, 0.45)');
        }
        ctx.fillStyle = vigGrad;
        ctx.fillRect(0, 0, w, h);
        ctx.restore();
    }
}
