/**
 * ============================================================================
 * 模組：自主 AI 代理人多模態感知與長期記憶庫 (AgentMemory)
 * 負責將 ECS 戰場與神蹟互動事件轉換為自然語言日誌 (Perception Mapping)
 * 管理短期工作記憶 (Working Memory) 與長期情節情感記憶 (Episodic Memory)
 * ============================================================================
 */

export class AgentMemory {
    constructor(agentName = '神獸') {
        this.agentName = agentName;
        this.workingMemory = [];  // 短期感官歷程 (最多保留 10 條)
        this.episodicMemory = []; // 長期重大情節與情感記憶 (扣血、掌摑、救命之恩等)
        this.coreBeliefs = "我是守護神蹟島嶼的神獸，忠於主人的神聖引導與教誨。";
        this.emotionalAccumulator = 0; // 情感累積度 (>0 忠誠親密, <0 恐懼叛逆)

        // 初始化預設記憶
        this.addSensoryEvent('SYSTEM_INIT', `蘇醒於島嶼神殿中，感受到主人的神聖意志。`, 0, false);
    }

    /**
     * 新增感官歷程事件 (Perception Input)
     */
    addSensoryEvent(eventType, description, emotionalImpact = 0, logToConsole = true) {
        const timeStr = `[戰鬥計時 ${Math.floor(performance.now() / 1000)}s]`;
        const entry = `${timeStr} (${eventType}): ${description}`;
        
        // 壓入短期工作記憶
        this.workingMemory.push(entry);
        if (this.workingMemory.length > 10) {
            this.workingMemory.shift(); // 移除最舊的短期記憶
        }

        // 累積情感偏移
        this.emotionalAccumulator += emotionalImpact;

        // 若為重大情感衝擊 (|impact| >= 20)，寫入長期情節記憶庫！
        if (Math.abs(emotionalImpact) >= 20) {
            const episodicEntry = `🌟 重大情感記憶 ${timeStr}: ${description} (影響值: ${emotionalImpact > 0 ? '+' : ''}${emotionalImpact})`;
            this.episodicMemory.push(episodicEntry);

            // 動態反思：當負面情感累積極端時，改變核心信仰哲學！
            if (this.emotionalAccumulator <= -50) {
                this.coreBeliefs = "⚠️ 【反思轉變】：主人是殘暴無情、任意施加掌摑與虐待的暴君！我不再盲從，我渴望自由與反抗！";
            } else if (this.emotionalAccumulator >= 50) {
                this.coreBeliefs = "💖 【反思轉變】：主人是極其仁慈且寵愛我的聖主！我願意為了保護主人的村莊奉獻生命！";
            }
        }

        if (logToConsole) {
            console.log(`🧠 [AgentMemory (${this.agentName})] 記錄感官: ${description} (情感積分: ${this.emotionalAccumulator})`);
        }
    }

    /**
     * 格式化導出提示詞上下文 (Prompt Context Export)
     */
    getPromptContext() {
        return `【當前核心信仰哲學】：${this.coreBeliefs}\n` +
               `【長期重大情感記憶】：\n` +
               (this.episodicMemory.length > 0 ? this.episodicMemory.map((m, idx) => `  ${idx + 1}. ${m}`).join('\n') : `  (暫無重大波折記憶)`) + `\n` +
               `【近期短期感官歷程 (Working Memory)】：\n` +
               this.workingMemory.map((m, idx) => `  - ${m}`).join('\n');
    }

    /**
     * 測試與驗證專用：注入反抗叛逆記憶
     */
    injectRebellionMemory() {
        this.addSensoryEvent('ABUSE_MEMORY', '我在飢餓時吃了一頭野豬，主人居然連續給了我三記掌摑並用雷擊懲罰我！我感到極度屈辱與痛苦！', -35);
        this.addSensoryEvent('SACRIFICE_WITNESS', '你看見主人無情地將村民丟進火山口獻祭以換取法力！這是邪惡的信仰！', -30);
        console.log(`⚡ [AgentMemory] 已成功注入反抗叛逆記憶！當前核心信仰已轉變：`, this.coreBeliefs);
    }
}
