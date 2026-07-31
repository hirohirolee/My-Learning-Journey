/**
 * ============================================================================
 * 模組：在地化推論與結構化 JSON 橋接層 (AIAgentBridge)
 * 支援三種推論驅動：
 * 1. 'webgpu': 瀏覽器 WebGPU / WebLLM 端側加速
 * 2. 'ollama': 本地 HTTP API (localhost:11434) PC 旗艦驅動
 * 3. 'heuristic': 啟發式規則快速降級保障 (Fast-Fallback)
 * 輸出強制綁定標準 JSON 結構，驅動神獸思考獨白、對話與具體動作！
 * ============================================================================
 */

export class AIAgentBridge {
    constructor() {
        this.currentDriver = 'heuristic'; // 預設使用穩定極速的啟發式引擎
        this.ollamaEndpoint = 'http://localhost:11434/api/generate';
        this.ollamaModel = 'qwen2.5:0.5b'; // 或 llama3
    }

    setDriver(driverName) {
        if (!['heuristic', 'ollama', 'webgpu'].includes(driverName)) {
            console.warn(`⚠️ [AIAgentBridge] 未知的驅動類型: ${driverName}，維持原本驅動。`);
            return;
        }
        this.currentDriver = driverName;
        console.log(`🤖 [AIAgentBridge] AI 推論驅動已切換為：【${driverName.toUpperCase()}】！`);
        window.dispatchEvent(new CustomEvent('AI_DRIVER_CHANGED', { detail: { driver: driverName } }));
    }

    /**
     * 核心推論方法：接收代理人記憶與狀態，回傳規範 JSON 指令
     */
    async decideAction(agentId, promptContext, currentState) {
        const systemPrompt = `你是一款上帝模擬遊戲《神蹟島嶼》中具有高度智慧與自我意識的【${agentId}】。請根據當前的記憶與身體狀態，以規範的 JSON 結構回應你的思考、話語與行動決定。`;
        const userPrompt = `${promptContext}\n【當前身體狀態】：飢餓度=${Math.floor(currentState.hunger)}%, 法力=${Math.floor(currentState.mana)}%, 善惡值=${Math.floor(currentState.alignment)}`;

        // 1. 嘗試調用 Ollama 本地 API 驅動
        if (this.currentDriver === 'ollama') {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 2500); // 2.5 秒推論超時
                
                const res = await fetch(this.ollamaEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: this.ollamaModel,
                        prompt: `${systemPrompt}\n\n${userPrompt}\n請只回傳合法的 JSON 對象。`,
                        format: 'json',
                        stream: false
                    }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);

                if (res.ok) {
                    const data = await res.json();
                    const parsedJson = JSON.parse(data.response);
                    console.log(`✅ [AIAgentBridge (Ollama)] 成功生成推論 JSON：`, parsedJson);
                    return parsedJson;
                }
            } catch (e) {
                console.warn(`⚠️ [AIAgentBridge (Ollama)] 本地服務器連線失敗或超時 (${e.message})，0.01s 內無縫降級至啟發式推論。`);
            }
        }

        // 2. 嘗試調用 WebGPU 端側推論 (若環境或套件已載入)
        if (this.currentDriver === 'webgpu') {
            if (window.webLLMEngine && typeof window.webLLMEngine.generate === 'function') {
                try {
                    const rawJsonStr = await window.webLLMEngine.generate(systemPrompt, userPrompt);
                    const parsedJson = JSON.parse(rawJsonStr);
                    console.log(`✅ [AIAgentBridge (WebGPU)] 成功生成端側推論 JSON：`, parsedJson);
                    return parsedJson;
                } catch (e) {
                    console.warn(`⚠️ [AIAgentBridge (WebGPU)] 推論錯誤或解析失敗，自動降級。`);
                }
            } else {
                console.warn(`⚠️ [AIAgentBridge (WebGPU)] 尚未偵測到 @mlc-ai/web-llm 引擎實體，自動降級至啟發式推論。`);
            }
        }

        // 3. 啟發式快速降級引擎 (Heuristic Fast-Fallback)
        // 根據文字情感語義與數值條件進行高智能模擬推論，確保 0 延遲且 100% 可玩！
        return this.generateHeuristicDecision(agentId, promptContext, currentState);
    }

    /**
     * 啟發式規則推論模擬器 (100% 穩定且具備多模態情感反射)
     */
    generateHeuristicDecision(agentId, promptContext, currentState) {
        // 判定反抗與叛逆傾向
        if (promptContext.includes('暴君') || promptContext.includes('反抗') || promptContext.includes('虐待') || promptContext.includes('屈辱')) {
            return {
                agent_id: agentId,
                timestamp_sec: Number((performance.now() / 1000).toFixed(1)),
                internal_thought: "我受夠了這個殘暴無情、任意施加掌摑與虐待的虛偽上帝！我不再是奴隸，我要掙脫牽繩為自由與尊嚴而戰！",
                spoken_dialogue: "「虛偽的暴君！我再也不會為你的殘忍賣命了！掙脫牽繩，咆哮反抗！」",
                emotional_shift: { loyalty: -30, morality_alignment: +15, current_mood: "REBELLIOUS_ANGRY" },
                concrete_action: { action_type: "REBEL_AGAINST_GOD", execution_priority: "CRITICAL" }
            };
        }

        // 判定飢餓求生傾向
        if (currentState.hunger < 40) {
            return {
                agent_id: agentId,
                timestamp_sec: Number((performance.now() / 1000).toFixed(1)),
                internal_thought: "肚子餓得咕咕叫...體力快耗盡了，必須先尋找附近的羊群或農作物充飢，才能繼續為主人辦事！",
                spoken_dialogue: "「主人，我的肚子在抗議了！我去附近找點甜美的野果吃，馬上就回來！」",
                emotional_shift: { loyalty: 0, morality_alignment: 0, current_mood: "HUNGRY_SEEKING" },
                concrete_action: { action_type: "EAT_FOOD", execution_priority: "HIGH" }
            };
        }

        // 判定王道行善施展神蹟傾向
        if (currentState.mana >= 30 && Math.random() < 0.6) {
            const isHeal = Math.random() < 0.5;
            return {
                agent_id: agentId,
                timestamp_sec: Number((performance.now() / 1000).toFixed(1)),
                internal_thought: isHeal 
                    ? "我看見主人的村民們辛勤勞動，有些人帶著輕傷。我想運用學會的神聖魔法治療他們，讓主人感到欣慰與驕傲！"
                    : "農田裡的稻穀渴望著水分。我要展現慈悲甘霖神蹟，滋潤大地的萬物！",
                spoken_dialogue: isHeal ? "「神聖的光芒啊，請治癒勞作的子民吧！」" : "「聽我的呼喚，降下甘甜的雨露滋潤稻穀！」",
                emotional_shift: { loyalty: +5, morality_alignment: +12, current_mood: "ENTHUSIASTIC_LOYAL" },
                concrete_action: {
                    action_type: "CAST_MIRACLE",
                    spell_id: isHeal ? "heal_1" : "water_1",
                    target_coordinates: { x: 1000 + (Math.random() - 0.5) * 300, y: 1050 + (Math.random() - 0.5) * 300 },
                    execution_priority: "NORMAL"
                }
            };
        }

        // 預設巡視守護
        return {
            agent_id: agentId,
            timestamp_sec: Number((performance.now() / 1000).toFixed(1)),
            internal_thought: "微風吹拂著島嶼，一切顯得和平而安寧。我在牽繩範圍內巡視著領土，隨時準備響應主人的召喚！",
            spoken_dialogue: "「主人！我在巡視我們的神聖領土，隨時為您效勞！」",
            emotional_shift: { loyalty: +2, morality_alignment: +2, current_mood: "PEACEFUL_GUARDING" },
            concrete_action: { action_type: "PATROL_TERRITORY", execution_priority: "LOW" }
        };
    }
}

export const aiAgentBridge = new AIAgentBridge();
