/**
 * ============================================================================
 * 模組：數據預警雷達與極光趨勢環 UI (PrewarningRadarUI)
 * 參照 RimWorld 與 Frostpunk 的高壓預警與法典干預
 * 實作頂部極光趨勢環與右側磨砂玻璃危機卡片 (Glassmorphism Crisis Card)
 * 提供一鍵智能稽核與授權決策按鈕，徹底免除微操地獄！
 * ============================================================================
 */

export class PrewarningRadarUI {
    constructor() {
        this.container = null;
        this.auroraContainer = null;
        this.crisisCard = null;
        this.activeCrisis = null; // 當前活動的危機類型
        this.countdownSec = 200;  // 倒數秒數

        this.initDOM();
    }

    initDOM() {
        if (document.getElementById('prewarning-radar-ui')) return;

        // 建立 CSS 樣式
        const style = document.createElement('style');
        style.innerHTML = `
            #aurora-trend-rings {
                position: absolute;
                top: 15px;
                right: 300px;
                display: flex;
                gap: 15px;
                z-index: 50;
                pointer-events: none;
            }
            .aurora-ring {
                background: rgba(15, 23, 42, 0.75);
                border: 2px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(8px);
                border-radius: 30px;
                padding: 6px 14px;
                color: #fff;
                font-family: 'Outfit', 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 6px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                transition: all 0.3s ease;
            }
            .aurora-ring.healthy {
                border-color: #38bdf8;
                box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
            }
            .aurora-ring.warning {
                border-color: #f97316;
                background: rgba(124, 45, 18, 0.85);
                box-shadow: 0 0 15px rgba(249, 115, 22, 0.7);
                animation: ring-pulse 1s infinite alternate;
            }
            @keyframes ring-pulse {
                0% { transform: scale(1); }
                100% { transform: scale(1.06); }
            }
            #crisis-glass-card {
                position: absolute;
                top: 100px;
                right: 25px;
                width: 320px;
                background: rgba(15, 23, 42, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(16px);
                border-radius: 16px;
                padding: 18px;
                color: #f8fafc;
                font-family: 'Outfit', 'Inter', sans-serif;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.2);
                z-index: 60;
                display: none;
                flex-direction: column;
                gap: 12px;
                animation: slide-in-right 0.4s ease-out;
            }
            @keyframes slide-in-right {
                from { opacity: 0; transform: translateX(50px); }
                to { opacity: 1; transform: translateX(0); }
            }
            .crisis-title {
                font-size: 16px;
                font-weight: 700;
                color: #fb7185;
                display: flex;
                align-items: center;
                gap: 8px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                padding-bottom: 8px;
            }
            .crisis-timer {
                font-size: 13px;
                color: #facc15;
                font-weight: 600;
            }
            .root-causes {
                background: rgba(0,0,0,0.3);
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                color: #cbd5e1;
                line-height: 1.6;
            }
            .delegate-buttons {
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-top: 6px;
            }
            .btn-delegate {
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            }
            .btn-paragon {
                background: linear-gradient(135deg, #0284c7, #0369a1);
                color: #fff;
                box-shadow: 0 4px 10px rgba(2, 132, 199, 0.4);
            }
            .btn-paragon:hover { background: linear-gradient(135deg, #38bdf8, #0284c7); transform: translateY(-2px); }
            .btn-tyrant {
                background: linear-gradient(135deg, #9f1239, #881337);
                color: #fff;
                box-shadow: 0 4px 10px rgba(159, 18, 57, 0.4);
            }
            .btn-tyrant:hover { background: linear-gradient(135deg, #f43f5e, #9f1239); transform: translateY(-2px); }
        `;
        document.head.appendChild(style);

        // 建立極光趨勢環容器
        this.auroraContainer = document.createElement('div');
        this.auroraContainer.id = 'aurora-trend-rings';
        this.auroraContainer.innerHTML = `
            <div id="ring-faith" class="aurora-ring healthy">✨ 信仰狂熱: 90%</div>
            <div id="ring-material" class="aurora-ring healthy">🍞 物質飽食: 85%</div>
            <div id="ring-order" class="aurora-ring healthy">🕊️ 社會秩序: 95%</div>
        `;
        document.body.appendChild(this.auroraContainer);

        // 建立危機卡片容器
        this.crisisCard = document.createElement('div');
        this.crisisCard.id = 'crisis-glass-card';
        document.body.appendChild(this.crisisCard);
    }

    /**
     * 更新儀表板數據與倒數邏輯
     */
    update(dt, supplyChain, morality, villages, creature, uiManager) {
        if (!this.auroraContainer) return;

        // 計算綜合數據
        const totalFood = villages.reduce((acc, v) => acc + v.food, 0) + (supplyChain ? supplyChain.inventory.wheat : 0);
        const avgBelief = villages.length > 0 ? villages.reduce((acc, v) => acc + v.belief, 0) / villages.length : 80;
        const dread = morality ? morality.dread : 0;
        const prosperity = morality ? morality.prosperity : 50;

        // 更新極光環文字與樣式
        const elFaith = document.getElementById('ring-faith');
        const elMaterial = document.getElementById('ring-material');
        const elOrder = document.getElementById('ring-order');

        if (elFaith) {
            const faithScore = Math.min(100, Math.floor(avgBelief));
            elFaith.innerText = `✨ 信仰狂熱: ${faithScore}%`;
            elFaith.className = `aurora-ring ${faithScore < 40 ? 'warning' : 'healthy'}`;
        }
        if (elMaterial) {
            const matScore = Math.min(100, Math.floor((totalFood / 1500) * 100));
            elMaterial.innerText = `🍞 物質飽食: ${matScore}%`;
            elMaterial.className = `aurora-ring ${matScore < 35 ? 'warning' : 'healthy'}`;
        }
        if (elOrder) {
            const orderScore = Math.max(0, Math.floor(100 - dread * 0.8));
            elOrder.innerText = `🕊️ 社會秩序: ${orderScore}%`;
            elOrder.className = `aurora-ring ${orderScore < 40 || dread > 70 ? 'warning' : 'healthy'}`;
        }

        // 倒數計時更新
        if (this.activeCrisis) {
            this.countdownSec = Math.max(0, this.countdownSec - dt);
            const elTimer = document.getElementById('crisis-timer-text');
            if (elTimer) {
                const mins = Math.floor(this.countdownSec / 60);
                const secs = Math.floor(this.countdownSec % 60);
                elTimer.innerText = `⏱️ 倒數計時：${mins} 分 ${secs} 秒後爆發！`;
            }
            if (this.countdownSec <= 0) {
                this.triggerCrisisExplosion(uiManager);
            }
        }
    }

    /**
     * 觸發顯示特定危機預警卡片
     */
    showCrisisCard(crisisType, supplyChain, creature, uiManager) {
        if (!this.crisisCard) return;
        this.activeCrisis = crisisType;
        this.countdownSec = 180; // 3分鐘倒數
        this.crisisCard.style.display = 'flex';

        let title = '⚠️ 危機預警：未知騷動';
        let causes = '• 社會不滿情緒累積<br>• 資源供需失衡';
        let btn1Text = '🕊️ 授權祭司開倉賑濟';
        let btn2Text = '💀 派遣神獸咆哮鎮壓';

        if (crisisType === 'HERETICAL_BLOOD_SACRIFICE') {
            title = '⚠️ 危機預警：異端狂熱血祭要求';
            causes = '• 極端飢餓與食物短缺 -35%<br>• 絕望指數突破 70%<br>• 神蹟長時間未顯現 -15%';
            btn1Text = '🕊️ [王道] 授權祭司開倉賑濟 (食 -200)';
            btn2Text = '💀 [霸道] 神之手將俘虜投入火山血祭';
        } else if (crisisType === 'UNDERGROUND_DEFECTION') {
            title = '⚠️ 危機預警：地下鐵逃亡潮醞釀中';
            causes = '• 霸道重稅威懾 -40%<br>• 工匠恐懼不滿 -25%<br>• 敵對文化滲透誘惑 -20%';
            btn1Text = '🕊️ [王道] 授權大祭司頒布減稅特赦法典';
            btn2Text = '💀 [霸道] 命令神獸夜間武裝巡夜戒嚴';
        } else if (crisisType === 'CRUSADE_INVASION') {
            title = '🔥 史詩危機：反神同盟千人衝鋒';
            causes = '• 曜石/合金財富熱度突破 300<br>• 海盜與阿茲特克結盟<br>• 目標：物流神殿與煉金爐';
            btn1Text = '🤖 [王道] 命令神獸裝配機甲奔赴前線';
            btn2Text = '⚡ [霸道] 授權流場神殿引爆防禦雷雨';
        }

        this.crisisCard.innerHTML = `
            <div class="crisis-title">${title}</div>
            <div id="crisis-timer-text" class="crisis-timer">⏱️ 倒數計時：3 分 00 秒後爆發！</div>
            <div class="root-causes">
                <strong>🔍 根源歸因分析 (Root Causes):</strong><br>
                ${causes}
            </div>
            <div class="delegate-buttons">
                <button id="btn-delegate-1" class="btn-delegate btn-paragon">${btn1Text}</button>
                <button id="btn-delegate-2" class="btn-delegate btn-tyrant">${btn2Text}</button>
            </div>
        `;

        // 綁定一鍵智能授權按鈕事件
        document.getElementById('btn-delegate-1')?.addEventListener('click', () => {
            this.resolveCrisis('paragon', supplyChain, creature, uiManager);
        });
        document.getElementById('btn-delegate-2')?.addEventListener('click', () => {
            this.resolveCrisis('tyrant', supplyChain, creature, uiManager);
        });

        console.log(`⚠️ [PrewarningRadarUI] 已彈出危機雷達卡片：【${crisisType}】！`);
        if (uiManager) uiManager.showNotice(`⚠️ 危機倒數預警：【${title.replace('⚠️ ', '')}】已啟動！`, 'danger');
    }

    /**
     * 一鍵智能授權決策解決危機 (Zero-Micromanagement)
     */
    resolveCrisis(route, supplyChain, creature, uiManager) {
        if (!this.activeCrisis) return;

        console.log(`✅ [PrewarningRadarUI] 玩家一鍵授權執行【${route === 'paragon' ? '王道安撫' : '霸道鎮壓'}】決策！危機解除！`);
        
        if (route === 'paragon') {
            if (supplyChain) supplyChain.inventory.wheat = Math.max(0, supplyChain.inventory.wheat - 100);
            if (creature) {
                creature.thought = "「🕊️ 遵從主人的王道仁慈！大祭司與我一同開倉發糧，平息了騷動！」";
                creature.alignment = Math.min(100, creature.alignment + 20);
            }
            if (uiManager) uiManager.showNotice(`🕊️ 【危機解除】：大祭司開倉賑濟並宣講神聖法典，村民歡呼鼓舞！`, 'success');
        } else {
            if (creature) {
                creature.thought = "「💀 遵從主人的霸道威武！我發出震撼全島的咆哮，無人敢再反抗！」";
                creature.alignment = Math.max(-100, creature.alignment - 20);
            }
            if (uiManager) uiManager.showNotice(`💀 【危機解除】：神之手與神獸以極致恐懼威懾了反抗者！秩序重歸肅穆！`, 'warning');
        }

        this.hideCrisisCard();
    }

    hideCrisisCard() {
        this.activeCrisis = null;
        if (this.crisisCard) this.crisisCard.style.display = 'none';
    }

    triggerCrisisExplosion(uiManager) {
        console.warn(`💥 [PrewarningRadarUI] 危機倒數結束，爆發失控！`);
        if (uiManager) uiManager.showNotice(`💥 倒數結束！危機全面爆發！村莊陷入暴動與戰火！`, 'danger');
        this.hideCrisisCard();
    }
}
