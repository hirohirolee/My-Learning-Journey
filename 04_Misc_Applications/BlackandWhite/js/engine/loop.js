/**
 * 商業級固定步長主迴圈與視窗可見度管理器 (Fixed Time-Step Game Loop & Tab Visibility Manager)
 * 解決傳統 requestAnimationFrame 在分頁背景或效能抖動時物理穿透與爆發問題，保證 60Hz 固定物理演算步長。
 */
export class FixedStepLoop {
    constructor({ onFixedUpdate, onRender, onPause, onResume, onFpsUpdate, fixedStep = 1 / 60 }) {
        this.onFixedUpdate = onFixedUpdate;
        this.onRender = onRender;
        this.onPause = onPause;
        this.onResume = onResume;
        this.onFpsUpdate = onFpsUpdate;

        this.fixedStep = fixedStep;
        this.accumulator = 0;
        this.lastTime = 0;
        this.isRunning = false;
        this.isPaused = false;
        this.animFrameId = null;

        // FPS 監控計數器
        this.frameCount = 0;
        this.fpsTimer = 0;
        this.currentFps = 60;

        this.initVisibilityListener();
    }

    initVisibilityListener() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pause();
                if (this.onPause) this.onPause('tab_hidden');
            } else {
                this.resume();
                if (this.onResume) this.onResume('tab_active');
            }
        });
    }

    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.isPaused = false;
        this.lastTime = performance.now();
        this.animFrameId = requestAnimationFrame((t) => this.loop(t));
    }

    stop() {
        this.isRunning = false;
        if (this.animFrameId) {
            cancelAnimationFrame(this.animFrameId);
            this.animFrameId = null;
        }
    }

    pause() {
        this.isPaused = true;
    }

    resume() {
        if (!this.isPaused) return;
        this.isPaused = false;
        this.lastTime = performance.now(); // 重置時間差，避免切換回來瞬間計算巨大 dt
    }

    loop(currentTime) {
        if (!this.isRunning) return;

        this.animFrameId = requestAnimationFrame((t) => this.loop(t));

        if (this.isPaused) return;

        // 計算時間差 (限制最大 Frame Time 為 0.1 秒，防止死亡螺旋「Spiral of Death」)
        let dt = (currentTime - this.lastTime) / 1000;
        if (dt > 0.1) dt = 0.1;
        this.lastTime = currentTime;

        // FPS 計算
        this.frameCount++;
        this.fpsTimer += dt;
        if (this.fpsTimer >= 1.0) {
            this.currentFps = Math.round(this.frameCount / this.fpsTimer);
            this.frameCount = 0;
            this.fpsTimer = 0;
            if (this.onFpsUpdate) this.onFpsUpdate(this.currentFps);
        }

        // 累積物理步長並以固定時間步執行更新
        this.accumulator += dt;
        while (this.accumulator >= this.fixedStep) {
            if (this.onFixedUpdate) {
                this.onFixedUpdate(this.fixedStep);
            }
            this.accumulator -= this.fixedStep;
        }

        // 計算渲染插值比率 (Interpolation alpha 0.0 ~ 1.0)
        const alpha = this.accumulator / this.fixedStep;
        if (this.onRender) {
            this.onRender(alpha, dt);
        }
    }
}
