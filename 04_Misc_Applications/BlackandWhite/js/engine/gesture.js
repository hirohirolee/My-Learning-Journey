/**
 * 手勢認證與辨識系統 (Gesture Recognition Engine)
 * 負責監控滑鼠/手指在螢幕上畫出的軌跡，並匹配形狀 (〇, Z, △, ♡, S, □) 以觸發對應神力
 */
export class GestureEngine {
    constructor(gestureCanvas, camera, onGestureSuccess) {
        this.canvas = gestureCanvas;
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        this.camera = camera;
        this.onGestureSuccess = onGestureSuccess;

        this.points = [];
        this.isDrawing = false;
        this.strokeColor = '#38bdf8';
        this.glowColor = 'rgba(56, 189, 248, 0.6)';

        this.initEventListeners();
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    initEventListeners() {
        if (!this.canvas) return;

        // 由於 gesture-canvas 預設 pointer-events: none，我們在 window 或 game-container 上監聽右鍵滑動
        window.addEventListener('contextmenu', (e) => {
            // 阻止預設右鍵選單
            if (e.target.tagName === 'CANVAS' || e.target.id === 'game-container') {
                e.preventDefault();
            }
        });

        window.addEventListener('mousedown', (e) => {
            // 按下右鍵 (button === 2) 開始畫手勢
            if (e.button === 2 && (e.target.tagName === 'CANVAS' || e.target.id === 'game-container')) {
                this.isDrawing = true;
                this.points = [{ x: e.clientX, y: e.clientY }];
                this.clearCanvas();
                this.canvas.style.pointerEvents = 'auto'; // 暫時接收事件以畫出流動軌跡
            }
        });

        window.addEventListener('mousemove', (e) => {
            if (!this.isDrawing) return;
            const pt = { x: e.clientX, y: e.clientY };
            const lastPt = this.points[this.points.length - 1];
            if (Math.hypot(pt.x - lastPt.x, pt.y - lastPt.y) > 5) {
                this.points.push(pt);
                this.drawTrail();
            }
        });

        const stopDrawing = (e) => {
            if (!this.isDrawing) return;
            this.isDrawing = false;
            this.canvas.style.pointerEvents = 'none';

            if (this.points.length > 10) {
                const recognized = this.recognizeShape(this.points);
                if (recognized) {
                    // 獲取手勢終點或中心的世界座標
                    const center = this.getBoundingBoxCenter(this.points);
                    const worldPos = this.camera.screenToWorld(center.x, center.y);
                    this.showSuccessFeedback(recognized);
                    if (this.onGestureSuccess) {
                        this.onGestureSuccess(recognized, worldPos.x, worldPos.y);
                    }
                } else {
                    this.showFailedFeedback();
                }
            } else {
                this.clearCanvas();
            }
        };

        window.addEventListener('mouseup', (e) => {
            if (e.button === 2) stopDrawing(e);
        });
        window.addEventListener('mouseleave', stopDrawing);
    }

    clearCanvas() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    drawTrail() {
        if (!this.ctx || this.points.length < 2) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.save();
        this.ctx.strokeStyle = this.strokeColor;
        this.ctx.lineWidth = 6;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.shadowColor = this.glowColor;
        this.ctx.shadowBlur = 16;

        this.ctx.beginPath();
        this.ctx.moveTo(this.points[0].x, this.points[0].y);
        for (let i = 1; i < this.points.length; i++) {
            this.ctx.lineTo(this.points[i].x, this.points[i].y);
        }
        this.ctx.stroke();
        this.ctx.restore();
    }

    showSuccessFeedback(shapeName) {
        if (!this.ctx) return;
        this.strokeColor = '#34d399'; // 成功綠光/金光
        this.glowColor = 'rgba(52, 211, 153, 0.8)';
        this.drawTrail();

        // 在中心顯示識別成功符號
        const center = this.getBoundingBoxCenter(this.points);
        this.ctx.save();
        this.ctx.font = 'bold 28px Outfit, sans-serif';
        this.ctx.fillStyle = '#facc15';
        this.ctx.textAlign = 'center';
        this.ctx.shadowColor = '#000';
        this.ctx.shadowBlur = 8;
        this.ctx.fillText(`✨ 施法手勢成功: ${shapeName}`, center.x, center.y - 20);
        this.ctx.restore();

        setTimeout(() => {
            this.clearCanvas();
            this.strokeColor = '#38bdf8';
            this.glowColor = 'rgba(56, 189, 248, 0.6)';
        }, 800);
    }

    showFailedFeedback() {
        if (!this.ctx) return;
        this.strokeColor = '#ef4444'; // 失敗紅光
        this.glowColor = 'rgba(239, 68, 68, 0.8)';
        this.drawTrail();
        setTimeout(() => {
            this.clearCanvas();
            this.strokeColor = '#38bdf8';
            this.glowColor = 'rgba(56, 189, 248, 0.6)';
        }, 400);
    }

    getBoundingBoxCenter(pts) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const p of pts) {
            if (p.x < minX) minX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.x > maxX) maxX = p.x;
            if (p.y > maxY) maxY = p.y;
        }
        return { x: (minX + maxX) / 2, y: (minY + maxY) / 2 };
    }

    /**
     * 幾何軌跡匹配演算法 (識別：circle, lightning, triangle, heart, spiral, square)
     */
    recognizeShape(pts) {
        const n = pts.length;
        if (n < 12) return null;

        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        let totalDist = 0;
        for (let i = 0; i < n; i++) {
            const p = pts[i];
            if (p.x < minX) minX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.x > maxX) maxX = p.x;
            if (p.y > maxY) maxY = p.y;
            if (i > 0) totalDist += Math.hypot(p.x - pts[i-1].x, p.y - pts[i-1].y);
        }

        const width = maxX - minX;
        const height = maxY - minY;
        const aspect = width / Math.max(1, height);
        const startEndDist = Math.hypot(pts[0].x - pts[n-1].x, pts[0].y - pts[n-1].y);
        const isClosed = startEndDist < (width + height) * 0.25;

        // 1. 識別閃電 (Z-Shape)：非閉合，具有明顯左右折轉
        if (!isClosed && aspect > 0.4 && aspect < 2.5) {
            let leftToRightCount = 0;
            let rightToLeftCount = 0;
            for (let i = 1; i < n; i++) {
                const dx = pts[i].x - pts[i-1].x;
                if (dx > 3) leftToRightCount++;
                else if (dx < -3) rightToLeftCount++;
            }
            // Z 字形有顯著往右、往左再往右的特徵
            if (leftToRightCount > n * 0.35 && rightToLeftCount > n * 0.15) {
                return 'lightning'; // 雷電神力 (Z)
            }
        }

        // 2. 識別圓形 (Circle) 或 螺旋 (Spiral/S)
        if (isClosed && aspect > 0.6 && aspect < 1.6) {
            // 計算點到中心的距離方差
            const center = { x: minX + width / 2, y: minY + height / 2 };
            const avgRadius = (width + height) / 4;
            let variance = 0;
            for (const p of pts) {
                const r = Math.hypot(p.x - center.x, p.y - center.y);
                variance += Math.pow(r - avgRadius, 2);
            }
            variance /= n;
            const stdDev = Math.sqrt(variance);

            if (stdDev / avgRadius < 0.3) {
                return 'circle'; // 造水神力 (〇)
            }
        }

        // 3. 識別三角形 (Triangle)
        if (isClosed && n >= 15) {
            // 三角形上方應有一個尖頭，下方較寬
            let topPoints = 0, bottomPoints = 0;
            const midY = minY + height * 0.5;
            for (const p of pts) {
                if (p.y < midY) topPoints++;
                else bottomPoints++;
            }
            if (bottomPoints > topPoints * 1.2) {
                return 'triangle'; // 火球神力 (△)
            }
        }

        // 4. 識別方形或護盾 (Square)
        if (isClosed && aspect > 0.7 && aspect < 1.4) {
            return 'square'; // 防禦穹頂 (□)
        }

        // 5. 識別愛心或十字 (Heart / Heal)
        if (!isClosed && height > width * 0.8) {
            return 'heart'; // 治療神力 (♡)
        }

        // 預設 fallback 猜測：若畫了很大的軌跡但未準確對齊，根據是否閉合給予預設
        return isClosed ? 'circle' : 'lightning';
    }
}
