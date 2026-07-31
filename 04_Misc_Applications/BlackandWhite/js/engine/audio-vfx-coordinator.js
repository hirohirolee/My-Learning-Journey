/**
 * ============================================================================
 * 模組：全局音效與粒子特效聚合橋樑 (AudioVFXCoordinator)
 * 監聽千人戰場熱度預警、老兵晉升、善惡變更與村莊歸順事件
 * 聚合調度 SoundEngine 與 ParticleEngine 產生震憾感官體驗
 * ============================================================================
 */

export class AudioVFXCoordinator {
    constructor(gameInstance) {
        this.game = gameInstance;
        this.lastWarningTime = 0;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // 1. 監聽千人戰場極高威脅與恐慌熱度預警
        window.addEventListener('BATTLEFIELD_HIGH_THREAT_WARNING', (e) => {
            const now = performance.now();
            if (now - this.lastWarningTime < 3000) return; // 3 秒防刷屏冷卻
            this.lastWarningTime = now;

            const { x, y, threatLevel } = e.detail;
            console.log(`📯 [AudioVFXCoordinator] 偵測到戰場高威脅熱度 (${Math.floor(threatLevel)})，吹響戰鬥號角與揚沙！`);

            // 觸發音效與視覺震盪
            if (this.game.soundEngine) {
                this.game.soundEngine.playMiracleCast(); // 借用神威音效模擬號角
            }
            if (this.game.triggerFlash) {
                this.game.triggerFlash();
            }

            // 在高熱度座標爆發戰場塵土與刀光劍影粒子
            if (this.game.particleEngine) {
                for (let i = 0; i < 20; i++) {
                    this.game.particleEngine.addParticle({
                        x: x + (Math.random() - 0.5) * 200,
                        y: y + (Math.random() - 0.5) * 200,
                        vx: (Math.random() - 0.5) * 80,
                        vy: -20 - Math.random() * 50,
                        color: threatLevel > 700 ? '#ef4444' : '#ca8a04',
                        size: 4 + Math.random() * 4,
                        life: 1.0 + Math.random() * 1.0,
                        symbol: Math.random() < 0.5 ? '💨' : '⚔️'
                    });
                }
            }
        });

        // 2. 監聽善惡路線轉變
        window.addEventListener('MORALITY_ROUTE_CHANGED', (e) => {
            const { theme, alignment } = e.detail;
            if (this.game.soundEngine) {
                if (theme === 'good') this.game.soundEngine.playHeal();
                else if (theme === 'evil') this.game.soundEngine.playCreatureRoar(0.5);
            }
            if (this.game.particleEngine) {
                const center = this.game.villages[0] || { x: 1000, y: 1000 };
                for (let i = 0; i < 35; i++) {
                    this.game.particleEngine.addParticle({
                        x: center.x + (Math.random() - 0.5) * 500,
                        y: center.y + (Math.random() - 0.5) * 500,
                        vx: (Math.random() - 0.5) * 100,
                        vy: -50 - Math.random() * 100,
                        color: theme === 'good' ? '#38bdf8' : '#ef4444',
                        size: 5 + Math.random() * 5,
                        life: 2.0,
                        symbol: theme === 'good' ? '✨' : '🔥'
                    });
                }
            }
        });

        // 3. 監聽老兵榮譽晉升
        window.addEventListener('VETERAN_PROMOTED', (e) => {
            const { x, y, level, mass } = e.detail;
            if (this.game.soundEngine && mass) {
                this.game.soundEngine.playHeal();
            }
            if (this.game.particleEngine) {
                const count = mass ? 30 : 12;
                for (let i = 0; i < count; i++) {
                    this.game.particleEngine.addParticle({
                        x: x + (Math.random() - 0.5) * 100,
                        y: y - 10,
                        vx: (Math.random() - 0.5) * 60,
                        vy: -40 - Math.random() * 60,
                        color: level >= 5 ? '#a855f7' : '#facc15',
                        size: 4 + Math.random() * 3,
                        life: 1.5,
                        symbol: level >= 5 ? '👑' : '⭐'
                    });
                }
            }
        });

        // 4. 監聽敵城歸順投降
        window.addEventListener('ENEMY_VILLAGE_SURRENDERED', (e) => {
            const { village, type } = e.detail;
            if (this.game.soundEngine) {
                this.game.soundEngine.playHeal();
            }
            if (this.game.particleEngine) {
                for (let i = 0; i < 30; i++) {
                    this.game.particleEngine.addParticle({
                        x: village.x + (Math.random() - 0.5) * 200,
                        y: village.y - 30,
                        vx: (Math.random() - 0.5) * 100,
                        vy: -60 - Math.random() * 80,
                        color: type === 'peace' ? '#22c55e' : '#9333ea',
                        size: 6,
                        life: 2.0,
                        symbol: type === 'peace' ? '🕊️' : '🏳️'
                    });
                }
            }
        });
    }
}
