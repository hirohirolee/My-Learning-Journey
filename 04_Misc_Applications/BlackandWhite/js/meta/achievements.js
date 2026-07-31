import { gameStorage } from '../engine/storage.js';
import { godProgression } from './progression.js';

/**
 * 每日挑戰任務與永久成就領獎系統 (Daily Quests & Achievements Manager)
 * 負責追蹤玩家局內外行為，自動更新任務進度並發放信仰水晶獎勵與紅點通知。
 */
export const DAILY_QUEST_CONFIGS = [
    { id: 'cast_5', title: '神蹟頻發', desc: '在任何關卡中累積施放神力 5 次', target: 5, reward: 35, icon: '✨', type: 'cast' },
    { id: 'sac_5', title: '祭壇狂熱', desc: '抓取並向祭壇獻祭 5 次任何物件或村民', target: 5, reward: 40, icon: '🔥', type: 'sacrifice' },
    { id: 'pet_3', title: '慈愛主人', desc: '撫摸並獎勵您的神獸 3 次', target: 3, reward: 30, icon: '✋', type: 'pet' }
];

export const ACHIEVEMENT_CONFIGS = [
    { id: 'first_win', title: '創世初成', desc: '成功統治並贏得第一次關卡勝利！', target: 1, reward: 100, icon: '🏆', type: 'win' },
    { id: 'spell_master', title: '大魔法神', desc: '生涯累積施放神力達到 30 次', target: 30, reward: 150, icon: '🧙‍♂️', type: 'cast' },
    { id: 'sac_master', title: '深淵祭司', desc: '生涯累積獻祭達到 25 次', target: 25, reward: 150, icon: '☠️', type: 'sacrifice' },
    { id: 'talent_lover', title: '天賦覺醒', desc: '升級任何上帝天賦達到 5 次', target: 5, reward: 120, icon: '🏛️', type: 'talent' }
];

export class AchievementsManager {
    constructor() {
        this.lastRefreshDate = this.getTodayString();
        this.dailyProgress = { cast_5: 0, sac_5: 0, pet_3: 0 };
        this.dailyClaimed = { cast_5: false, sac_5: false, pet_3: false };

        this.achieveProgress = { first_win: 0, spell_master: 0, sac_master: 0, talent_lover: 0 };
        this.achieveClaimed = { first_win: false, spell_master: false, sac_master: false, talent_lover: false };

        this.listeners = [];
        this.load();
        this.checkDailyRefresh();
    }

    getTodayString() {
        const d = new Date();
        return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
    }

    checkDailyRefresh() {
        const today = this.getTodayString();
        if (this.lastRefreshDate !== today) {
            this.lastRefreshDate = today;
            this.dailyProgress = { cast_5: 0, sac_5: 0, pet_3: 0 };
            this.dailyClaimed = { cast_5: false, sac_5: false, pet_3: false };
            this.save();
        }
    }

    load() {
        const saved = gameStorage.load('bw_quests_save');
        if (saved) {
            this.lastRefreshDate = saved.date || this.getTodayString();
            this.dailyProgress = { ...this.dailyProgress, ...(saved.dailyProgress || {}) };
            this.dailyClaimed = { ...this.dailyClaimed, ...(saved.dailyClaimed || {}) };
            this.achieveProgress = { ...this.achieveProgress, ...(saved.achieveProgress || {}) };
            this.achieveClaimed = { ...this.achieveClaimed, ...(saved.achieveClaimed || {}) };
        }
    }

    save() {
        gameStorage.save('bw_quests_save', {
            date: this.lastRefreshDate,
            dailyProgress: this.dailyProgress,
            dailyClaimed: this.dailyClaimed,
            achieveProgress: this.achieveProgress,
            achieveClaimed: this.achieveClaimed
        });
        this.notifyListeners();
    }

    onChange(cb) {
        this.listeners.push(cb);
    }

    notifyListeners() {
        for (const cb of this.listeners) {
            cb();
        }
    }

    /**
     * 遊戲內部事件觸發更新 (如施放魔法、獻祭、撫摸、贏得勝利)
     */
    trackEvent(eventType, count = 1, uiManager = null) {
        this.checkDailyRefresh();
        let anyUpdated = false;

        // 檢查每日任務
        for (const q of DAILY_QUEST_CONFIGS) {
            if (q.type === eventType && !this.dailyClaimed[q.id]) {
                this.dailyProgress[q.id] = Math.min(q.target, (this.dailyProgress[q.id] || 0) + count);
                anyUpdated = true;
                if (this.dailyProgress[q.id] >= q.target) {
                    this.dailyClaimed[q.id] = true;
                    godProgression.addCrystals(q.reward);
                    if (uiManager) uiManager.showNotice(`🎁 完成每日任務【${q.title}】！獲得 +${q.reward} 信仰水晶！`, 'info');
                }
            }
        }

        // 檢查永久成就
        for (const a of ACHIEVEMENT_CONFIGS) {
            if (a.type === eventType && !this.achieveClaimed[a.id]) {
                this.achieveProgress[a.id] = Math.min(a.target, (this.achieveProgress[a.id] || 0) + count);
                anyUpdated = true;
                if (this.achieveProgress[a.id] >= a.target) {
                    this.achieveClaimed[a.id] = true;
                    godProgression.addCrystals(a.reward);
                    if (uiManager) uiManager.showNotice(`🏆 解鎖成就【${a.title}】！獲得 +${a.reward} 信仰水晶！`, 'info');
                }
            }
        }

        if (anyUpdated) {
            this.save();
        }
    }

    hasUnclaimedOrActiveQuests() {
        const dCount = DAILY_QUEST_CONFIGS.filter(q => !this.dailyClaimed[q.id]).length;
        const aCount = ACHIEVEMENT_CONFIGS.filter(a => !this.achieveClaimed[a.id] && this.achieveProgress[a.id] >= a.target).length;
        return dCount > 0 || aCount > 0;
    }
}

export const godAchievements = new AchievementsManager();
