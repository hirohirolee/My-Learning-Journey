/**
 * ============================================================================
 * 模組：善惡雙極數值矩陣與文化同化管線 (MoralitySystem)
 * 處理王道 (Paragon / 經營) vs 霸道 (Tyrant / 征服) 的數值演變
 * 與文化同化吸引/恐懼震懾開城自動投降
 * ============================================================================
 */

export class MoralitySystem {
    constructor(initialAlignment = 0) {
        this.alignment = initialAlignment; // -100 (極惡) ~ +100 (極善)
        this.prosperity = 50;              // 文化繁榮度 (0 ~ 100)
        this.dread = 20;                   // 威懾恐懼度 (0 ~ 100)
        this.currentTheme = 'neutral';     // 'good', 'evil', 'neutral'
        
        // Phase 7 哲學兩難事件：溫室巨嬰 vs 鋼鐵意志文明演化狀態
        this.glacialWinterActive = false;
        this.civilizationEvolution = 'normal'; // 'normal', 'learned_helplessness', 'iron_will', 'coop_balanced'
        this.civEfficiencyMult = 1.0;
    }

    /**
     * 玩家行為紀錄與善惡數值偏移
     */
    onPlayerAction(actionType, value = 10, uiManager = null) {
        const oldTheme = this.currentTheme;

        switch (actionType) {
            case 'HEAL_VILLAGERS':
            case 'WATER_CROPS':
            case 'BLESS_BUILDING':
            case 'PET_CREATURE':
                this.alignment = Math.min(100, this.alignment + value);
                this.prosperity = Math.min(100, this.prosperity + value * 0.5);
                this.dread = Math.max(0, this.dread - value * 0.3);
                break;

            case 'CAST_METEOR':
            case 'CAST_FIREBALL':
            case 'SLAP_CREATURE':
            case 'SACRIFICE_VILLAGER':
            case 'PLUNDER_VILLAGE':
                this.alignment = Math.max(-100, this.alignment - value);
                this.dread = Math.min(100, this.dread + value * 0.7);
                this.prosperity = Math.max(0, this.prosperity - value * 0.4);
                break;
        }

        // 判定外觀主題切換
        if (this.alignment >= 30) this.currentTheme = 'good';
        else if (this.alignment <= -30) this.currentTheme = 'evil';
        else this.currentTheme = 'neutral';

        // 若主題改變，發送廣播通知渲染器與 UI
        if (oldTheme !== this.currentTheme) {
            console.log(`☯️ [MoralitySystem] 神聖主題轉變為: ${this.currentTheme.toUpperCase()} (Alignment: ${Math.floor(this.alignment)})`);
            document.documentElement.setAttribute('data-theme', this.currentTheme);
            window.dispatchEvent(new CustomEvent('MORALITY_ROUTE_CHANGED', {
                detail: { theme: this.currentTheme, alignment: this.alignment }
            }));
            if (uiManager) {
                const title = this.currentTheme === 'good' ? '✨ 神聖救世主之路' : (this.currentTheme === 'evil' ? '😈 毀滅霸道主宰' : '⚖️ 威嚴中立之神');
                uiManager.showNotice(`☯️ 您的神格已邁向：【${title}】！`, 'info');
            }
        }
    }

    /**
     * 取得魔法法力消耗折扣倍率
     */
    getSpellCostMultiplier(spellCategory) {
        // 從結構化設定檔載入修飾參數
        let rules = null;
        if (window.gameConfig && window.gameConfig.getMoralityModifiers) {
            rules = window.gameConfig.getMoralityModifiers(this.alignment);
        }

        if (!rules) return 1.0;

        if (spellCategory === 'mercy' || spellCategory === 'heal' || spellCategory === 'water') {
            return rules.outflow_modifiers?.mercy_spell_mana || (this.alignment > 20 ? 0.7 : 1.0);
        } else if (spellCategory === 'wrath' || spellCategory === 'fireball' || spellCategory === 'meteor') {
            return rules.outflow_modifiers?.wrath_spell_mana || (this.alignment < -20 ? 0.65 : 1.0);
        }
        return 1.0;
    }

    /**
     * 文化同化與恐懼震懾管線 (Assimilation & Dread Pipeline)
     */
    updateAssimilation(villages, dt, particleEngine = null, uiManager = null) {
        if (!villages || villages.length < 2) return;

        const playerVillages = villages.filter(v => v.owner === 'player');
        const enemyVillages  = villages.filter(v => v.owner !== 'player');
        if (playerVillages.length === 0 || enemyVillages.length === 0) return;

        for (const pv of playerVillages) {
            for (const ev of enemyVillages) {
                const dist = Math.hypot(pv.x - ev.x, pv.y - ev.y);
                if (dist > 650) continue; // 超過文化輻射範圍則跳過

                // ============================================================
                // 1. 王道善良路線：高文化繁榮度和平同化 (Peaceful Assimilation)
                // ============================================================
                if (this.alignment >= 20 && this.prosperity > 40) {
                    const attractRate = (this.prosperity / 50) * 1.5 * dt;
                    ev.addBelief(attractRate, true);

                    // 視覺表現：金黃色和睦信仰光流由敵村飄向玩家主村
                    if (particleEngine && Math.random() < 0.1) {
                        particleEngine.addParticle({
                            x: ev.x + (Math.random() - 0.5) * 60,
                            y: ev.y - 20,
                            vx: (pv.x - ev.x) * 0.3,
                            vy: (pv.y - ev.y) * 0.3,
                            color: '#facc15',
                            size: 3,
                            life: 1.5,
                            symbol: '✨'
                        });
                    }

                    if (ev.owner === 'player' && uiManager) {
                        uiManager.showNotice(`🕊️ 和平同化！【${ev.name}】感服於您的仁慈與文化繁榮，自願歸順！`, 'info');
                        window.dispatchEvent(new CustomEvent('ENEMY_VILLAGE_SURRENDERED', { detail: { village: ev, type: 'peace' } }));
                    }
                }

                // ============================================================
                // 2. 霸道邪惡路線：高恐懼度威懾逼降 (Dread Surrender)
                // ============================================================
                else if (this.alignment <= -20 && this.dread > 40) {
                    const terrorRate = (this.dread / 50) * 2.0 * dt;
                    ev.addBelief(terrorRate, false);
                    ev.health = Math.max(50, ev.health - dt * 2); // 建築結構因戰慄與騷亂受損

                    // 視覺表現：紫色恐懼怨念圍繞敵村
                    if (particleEngine && Math.random() < 0.15) {
                        particleEngine.addParticle({
                            x: ev.x + (Math.random() - 0.5) * 80,
                            y: ev.y,
                            vx: 0,
                            vy: -30,
                            color: '#9333ea',
                            size: 4,
                            life: 1.0,
                            symbol: '💀'
                        });
                    }

                    if (ev.owner === 'player' && uiManager) {
                        uiManager.showNotice(`💀 威懾降服！【${ev.name}】在極度恐懼與絕望下開城投降！`, 'warning');
                        window.dispatchEvent(new CustomEvent('ENEMY_VILLAGE_SURRENDERED', { detail: { village: ev, type: 'dread' } }));
                    }
                }
            }
        }
    }

    /**
     * Phase 7 灰色地帶的哲學抉擇：觸發「百年寒冬冰河期」與文明演化試煉
     * @param {string} path - 'glasshouse' (溫室過度保護) / 'iron_will' (殘酷放手獨立) / 'balanced' (親子灰度妥協)
     */
    triggerGlacialWinterEvent(path = 'glasshouse', villages, uiManager) {
        this.glacialWinterActive = true;
        
        if (path === 'glasshouse') {
            this.civilizationEvolution = 'learned_helplessness';
            this.civEfficiencyMult = 0.2; // 工業與研發產能萎縮 80%
            this.prosperity = 100;
            console.warn(`❄️🏠 [Moral Dilemma] 玩家選擇【途徑 A：極致溺愛與溫室保護】！維持恆溫護盾與神獸餵飯。`);
            console.warn(`⚠️ 社會演化後果：村民失去防寒與鍛造自理記憶，淪為「溫室巨嬰 (Learned Helplessness)」！產能 -80%！`);
            if (uiManager) {
                uiManager.showNotice(`❄️🏠 【哲學兩難】：您日夜維持金色溫室護盾，村民幸福滿分，但演化為失去生存能力的【溫室巨嬰】(產能 -80%)！`, 'warning');
            }
        } else if (path === 'iron_will') {
            this.civilizationEvolution = 'iron_will';
            this.civEfficiencyMult = 2.5; // 工業產能翻倍 250%
            this.dread = Math.min(100, this.dread + 40);
            console.warn(`❄️🦾 [Moral Dilemma] 玩家選擇【途徑 B：殘酷放手與獨立成長】！拒絕施放溫室護盾。`);
            console.warn(`✨ 社會演化後果：村民在冰雪絕境中激發鋼鐵意志，自主發明【地下暖氣】與【蒸氣裝甲】！產能翻倍 2.5x！`);
            if (uiManager) {
                uiManager.showNotice(`❄️🦾 【哲學兩難】：您殘酷放手！村民在冰雪絕境中覺醒【鋼鐵意志】，發明蒸汽裝甲，產能飆升 2.5 倍！`, 'success');
            }
        } else {
            this.civilizationEvolution = 'coop_balanced';
            this.civEfficiencyMult = 1.5;
            console.log(`❄️🌱 [Moral Dilemma] 玩家選擇【途徑 C：親子的灰度妥協】！小孩放溫溫暖氣，大人逼迫跑操訓練。`);
            if (uiManager) {
                uiManager.showNotice(`❄️🌱 【哲學兩難】：親密雙人協作達成！村民懂得知恩圖報，同時具備自衛韌性！效率 1.5x！`, 'success');
            }
        }
    }
}
