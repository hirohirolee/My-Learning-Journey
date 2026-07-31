/**
 * 玩家遙測數據埋點與行為分析統計層 (Player Telemetry & Analytics Tracking Layer)
 * 負責收集關卡勝率、神力使用頻率、廣告轉化與流失點，標準化對接 Google Analytics (gtag) 與 GameAnalytics SDK。
 */
export class AnalyticsService {
    constructor() {
        this.sessionStartTime = Date.now();
        this.eventQueue = [];
        this.stats = {
            spellsCast: 0,
            sacrificesMade: 0,
            stagesPlayed: 0,
            stagesWon: 0
        };
    }

    /**
     * 上報標準遙測追蹤事件
     */
    trackEvent(eventName, params = {}) {
        const payload = {
            event: eventName,
            timestamp: Date.now(),
            sessionDuration: Math.round((Date.now() - this.sessionStartTime) / 1000),
            ...params
        };

        this.eventQueue.push(payload);
        console.log(`[Analytics Event] 📊 ${eventName}`, params);

        // 如果存在外部第三方 GA 或 GameAnalytics SDK，自動送出
        if (typeof window !== 'undefined') {
            if (typeof window.gtag === 'function') {
                window.gtag('event', eventName, params);
            }
            if (window.gameanalytics && typeof window.gameanalytics.GameAnalytics === 'object') {
                try {
                    window.gameanalytics.GameAnalytics.addDesignEvent(eventName, parseFloat(params.value || 0));
                } catch (e) {}
            }
        }
    }

    trackStageStart(stageId, isSandbox) {
        this.stats.stagesPlayed++;
        this.trackEvent('stage_start', { stageId, isSandbox });
    }

    trackStageEnd(stageId, win, durationSec, finalEnergy, alignment) {
        if (win) this.stats.stagesWon++;
        this.trackEvent('stage_end', {
            stageId,
            result: win ? 'win' : 'lose',
            durationSec: Math.round(durationSec),
            finalEnergy: Math.round(finalEnergy),
            alignment: Math.round(alignment)
        });
    }

    trackSpellCast(spellId, symbol) {
        this.stats.spellsCast++;
        this.trackEvent('spell_cast', { spellId, symbol });
    }

    trackSacrifice(entityType, val) {
        this.stats.sacrificesMade++;
        this.trackEvent('sacrifice', { entityType, val });
    }
}

export const analytics = new AnalyticsService();
