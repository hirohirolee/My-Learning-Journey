/**
 * 2.5D 俯瞰/等距 攝影機系統 (Camera System)
 * 負責處理視窗縮放 (Zoom)、平移 (Pan)、座標轉換 (Screen <-> World) 與 震動特效 (Screen Shake)
 */
export class Camera {
    constructor(canvas) {
        this.canvas = canvas;
        this.x = 1000; // 預設世界座標中心 (島嶼中心)
        this.y = 1000;
        this.zoom = 1.0;
        this.targetZoom = 1.0;
        this.minZoom = 0.4;
        this.maxZoom = 2.5;

        // 震動特效數值
        this.shakeIntensity = 0;
        this.shakeDuration = 0;
        this.shakeOffsetX = 0;
        this.shakeOffsetY = 0;

        // 拖拽控制狀態
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.cameraStartX = 0;
        this.cameraStartY = 0;

        this.initEventListeners();
    }

    initEventListeners() {
        // 滾輪縮放
        window.addEventListener('wheel', (e) => {
            if (e.target !== this.canvas && e.target !== document.getElementById('gesture-canvas')) return;
            e.preventDefault();
            const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
            this.targetZoom = Math.max(this.minZoom, Math.min(this.maxZoom, this.targetZoom * zoomFactor));
        }, { passive: false });

        // 中鍵或空白鍵+左鍵平移地圖
        window.addEventListener('mousedown', (e) => {
            if (e.target !== this.canvas && e.target !== document.getElementById('gesture-canvas')) return;
            // 按下滑鼠中鍵 (button === 1) 或按住空白鍵搭配左鍵
            if (e.button === 1 || (e.button === 0 && e.spaceKey)) {
                this.isDragging = true;
                this.dragStartX = e.clientX;
                this.dragStartY = e.clientY;
                this.cameraStartX = this.x;
                this.cameraStartY = this.y;
                this.canvas.style.cursor = 'grabbing';
            }
        });

        window.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;
            const dx = (e.clientX - this.dragStartX) / this.zoom;
            const dy = (e.clientY - this.dragStartY) / this.zoom;
            this.x = this.cameraStartX - dx;
            this.y = this.cameraStartY - dy;
        });

        window.addEventListener('mouseup', (e) => {
            if (this.isDragging) {
                this.isDragging = false;
                this.canvas.style.cursor = 'default';
            }
        });
    }

    /**
     * 觸發螢幕震動特效 (例如雷電劈下、火球爆炸、神獸咆哮)
     * @param {number} intensity - 震動強度 (0~50)
     * @param {number} duration - 震動持續時間 (秒)
     */
    shake(intensity = 15, duration = 0.5) {
        this.shakeIntensity = intensity;
        this.shakeDuration = duration;
    }

    update(dt) {
        // 平滑縮放過渡
        this.zoom += (this.targetZoom - this.zoom) * 10 * dt;

        // 處理螢幕震動衰退
        if (this.shakeDuration > 0) {
            this.shakeDuration -= dt;
            const currentIntensity = this.shakeIntensity * (this.shakeDuration / 0.5);
            this.shakeOffsetX = (Math.random() - 0.5) * 2 * currentIntensity;
            this.shakeOffsetY = (Math.random() - 0.5) * 2 * currentIntensity;
        } else {
            this.shakeOffsetX = 0;
            this.shakeOffsetY = 0;
        }
    }

    /**
     * 應用攝影機變更到 Canvas 2D Context
     */
    apply(ctx) {
        ctx.save();
        const centerX = ctx.canvas.width / 2;
        const centerY = ctx.canvas.height / 2;

        ctx.translate(centerX + this.shakeOffsetX, centerY + this.shakeOffsetY);
        ctx.scale(this.zoom, this.zoom);
        ctx.translate(-this.x, -this.y);
    }

    restore(ctx) {
        ctx.restore();
    }

    /**
     * 平移攝影機視角聚焦於指定世界座標
     */
    panTo(worldX, worldY, zoomLevel = 1.0) {
        this.x = worldX;
        this.y = worldY;
        if (zoomLevel) {
            this.targetZoom = zoomLevel;
            this.zoom = zoomLevel;
        }
    }

    /**
     * 將螢幕像素座標轉換為遊戲世界座標 (考慮 Zoom 與 Pan)
     */
    screenToWorld(screenX, screenY) {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const worldX = (screenX - centerX) / this.zoom + this.x;
        const worldY = (screenY - centerY) / this.zoom + this.y;
        return { x: worldX, y: worldY };
    }

    /**
     * 將遊戲世界座標轉換為螢幕像素座標
     */
    worldToScreen(worldX, worldY) {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const screenX = (worldX - this.x) * this.zoom + centerX;
        const screenY = (worldY - this.y) * this.zoom + centerY;
        return { x: screenX, y: screenY };
    }
}
