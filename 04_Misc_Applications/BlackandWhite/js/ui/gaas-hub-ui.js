/**
 * ============================================================================
 * 模組：GaaS 普世化服務型互動控制中心 UI (GaaSHubUI)
 * 提供 4 大普世化分類分頁與互動測試：
 * 1. 跨平台通勤同步 (Mobile Sync)
 * 2. 異步互助社交 (Asynchronous Social)
 * 3. Cozy 信仰裝飾與心情共振 (Cozy Aesthetics)
 * 4. 向前失敗遺跡與抗體 (Fail-Forward Hub)
 * ============================================================================
 */

export class GaaSHubUI {
    constructor() {
        this.isOpen = false;
        this.activeTab = 'mobile';
        this.initDOM();
    }

    initDOM() {
        if (document.getElementById('gaas-hub-btn')) return;

        // 1. 建立左下角懸浮觸發按鈕
        const btn = document.createElement('button');
        btn.id = 'gaas-hub-btn';
        btn.innerHTML = '🌐 <b>GaaS 普世生態中心</b>';
        Object.assign(btn.style, {
            position: 'fixed',
            bottom: '20px',
            right: '250px',
            zIndex: '9998',
            padding: '10px 18px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899)',
            color: '#fff',
            border: '2px solid rgba(255,255,255,0.4)',
            borderRadius: '25px',
            cursor: 'pointer',
            fontFamily: "'Segoe UI', Roboto, sans-serif",
            fontSize: '14px',
            fontWeight: 'bold',
            boxShadow: '0 4px 15px rgba(139, 92, 246, 0.5)',
            transition: 'all 0.2s ease',
            textShadow: '0 1px 2px rgba(0,0,0,0.5)'
        });
        btn.onmouseover = () => btn.style.transform = 'scale(1.06) translateY(-2px)';
        btn.onmouseout = () => btn.style.transform = 'scale(1.0) translateY(0)';
        btn.onclick = () => this.toggleModal();
        document.body.appendChild(btn);

        // 2. 建立主彈窗容器 ( Glassmorphism 現代科技風格 )
        const modal = document.createElement('div');
        modal.id = 'gaas-hub-modal';
        Object.assign(modal.style, {
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%) scale(0.95)',
            width: '640px',
            maxHeight: '85vh',
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '20px',
            zIndex: '10000',
            padding: '24px',
            color: '#f8fafc',
            fontFamily: "'Segoe UI', Roboto, sans-serif",
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
            display: 'none',
            flexDirection: 'column',
            gap: '16px',
            overflowY: 'auto'
        });
        document.body.appendChild(modal);

        // 3. 建立關閉遮罩
        const overlay = document.createElement('div');
        overlay.id = 'gaas-hub-overlay';
        Object.assign(overlay.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100vw',
            height: '100vh',
            background: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(4px)',
            zIndex: '9999',
            display: 'none'
        });
        overlay.onclick = () => this.toggleModal();
        document.body.appendChild(overlay);
    }

    toggleModal() {
        this.isOpen = !this.isOpen;
        const modal = document.getElementById('gaas-hub-modal');
        const overlay = document.getElementById('gaas-hub-overlay');
        if (this.isOpen) {
            this.renderContent();
            modal.style.display = 'flex';
            modal.style.transform = 'translate(-50%, -50%) scale(1)';
            overlay.style.display = 'block';
        } else {
            modal.style.display = 'none';
            modal.style.transform = 'translate(-50%, -50%) scale(0.95)';
            overlay.style.display = 'none';
        }
    }

    renderContent() {
        const modal = document.getElementById('gaas-hub-modal');
        if (!modal) return;

        modal.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:12px;">
                <h2 style="margin:0; font-size:20px; background:linear-gradient(90deg, #60a5fa, #c084fc, #f472b6); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    🌐 GaaS 普世化服務型遊戲控制台 (All-Audiences Hub)
                </h2>
                <button id="close-gaas-btn" style="background:none; border:none; color:#94a3b8; font-size:20px; cursor:pointer;">✖</button>
            </div>

            <!-- 分類頁籤 -->
            <div style="display:flex; gap:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">
                <button class="gaas-tab-btn" data-tab="mobile" style="flex:1; padding:8px; border-radius:8px; border:none; background:${this.activeTab==='mobile'?'#3b82f6':'rgba(255,255,255,0.05)'}; color:#fff; cursor:pointer; font-weight:bold;">📱 跨平台通勤同步</button>
                <button class="gaas-tab-btn" data-tab="social" style="flex:1; padding:8px; border-radius:8px; border:none; background:${this.activeTab==='social'?'#8b5cf6':'rgba(255,255,255,0.05)'}; color:#fff; cursor:pointer; font-weight:bold;">🤝 異步社交互助</button>
                <button class="gaas-tab-btn" data-tab="cozy" style="flex:1; padding:8px; border-radius:8px; border:none; background:${this.activeTab==='cozy'?'#ec4899':'rgba(255,255,255,0.05)'}; color:#fff; cursor:pointer; font-weight:bold;">🎨 Cozy裝飾共振</button>
                <button class="gaas-tab-btn" data-tab="fail" style="flex:1; padding:8px; border-radius:8px; border:none; background:${this.activeTab==='fail'?'#10b981':'rgba(255,255,255,0.05)'}; color:#fff; cursor:pointer; font-weight:bold;">🦾 向前失敗遺跡</button>
            </div>

            <!-- 內容區 -->
            <div id="gaas-tab-content" style="padding:10px 0;">
                ${this.getTabHTML(this.activeTab)}
            </div>
        `;

        document.getElementById('close-gaas-btn').onclick = () => this.toggleModal();
        modal.querySelectorAll('.gaas-tab-btn').forEach(b => {
            b.onclick = (e) => {
                this.activeTab = e.target.getAttribute('data-tab');
                this.renderContent();
            };
        });

        // 綁定內嵌驗證按鈕事件
        const bindBtn = (id, fn) => {
            const el = document.getElementById(id);
            if (el) el.onclick = () => { fn(); this.renderContent(); };
        };

        if (this.activeTab === 'mobile') {
            bindBtn('btn-sync-commute', () => window.testMobileCommuteSync && window.testMobileCommuteSync());
        } else if (this.activeTab === 'social') {
            bindBtn('btn-social-ambassador', () => window.testBeastAmbassador && window.testBeastAmbassador());
            bindBtn('btn-social-aegis', () => window.testFriendDivineAegis && window.testFriendDivineAegis());
            bindBtn('btn-social-box', () => window.testStrandSupplyBox && window.testStrandSupplyBox());
        } else if (this.activeTab === 'cozy') {
            bindBtn('btn-cozy-sakura', () => window.testCozyAesthetics && window.testCozyAesthetics('sakura_pastel'));
            bindBtn('btn-cozy-crystal', () => window.testCozyAesthetics && window.testCozyAesthetics('crystal_fountain'));
        } else if (this.activeTab === 'fail') {
            bindBtn('btn-fail-ruins', () => window.testRuinsRebirth && window.testRuinsRebirth());
            bindBtn('btn-fail-lightning', () => window.testBeastAntibody && window.testBeastAntibody('lightning'));
            bindBtn('btn-fail-thermal', () => window.testBeastAntibody && window.testBeastAntibody('thermal'));
        }
    }

    getTabHTML(tab) {
        if (tab === 'mobile') {
            return `
                <div style="background:rgba(59,130,246,0.1); border:1px solid #3b82f6; border-radius:12px; padding:16px;">
                    <h3 style="margin-top:0; color:#60a5fa;">📱 跨平台 Tamagotchi 增量數據互通</h3>
                    <p style="font-size:13px; line-height:1.6; color:#cbd5e1;">
                        在手機端，通勤玩家不載入 4,000 單位物理流場，僅進行<b>電子雞陪伴、摸摸神獸與海釣放置</b>小互動。<br>
                        產生的包裹同步至雲端後，回家登入 PC 端將自動解包注入產能與美酒，並獲得全島加速！
                    </p>
                    <div style="margin-top:16px; display:flex; justify-content:center;">
                        <button id="btn-sync-commute" style="padding:10px 20px; background:linear-gradient(135deg, #2563eb, #3b82f6); border:none; border-radius:10px; color:#fff; font-weight:bold; cursor:pointer; box-shadow:0 4px 12px rgba(37,99,235,0.4);">
                            📲 模擬下載通勤遊玩包：觸發 50 次撫摸回饋與 +30% 全島產能 Buff！
                        </button>
                    </div>
                </div>
            `;
        } else if (tab === 'social') {
            return `
                <div style="display:flex; flex-direction:column; gap:12px;">
                    <div style="background:rgba(139,92,246,0.1); border:1px solid #8b5cf6; border-radius:12px; padding:14px;">
                        <h4 style="margin:0 0 6px 0; color:#c084fc;">🤝 好友神獸觀光大使與打工大使</h4>
                        <p style="font-size:12px; color:#cbd5e1; margin:0 0 10px 0;">好友登出後神獸背背包來訪，招待美酒可為您的麥田施展【豐收奇蹟】（產量 200%）！</p>
                        <button id="btn-social-ambassador" style="width:100%; padding:8px; background:#7c3aed; border:none; border-radius:8px; color:#fff; font-weight:bold; cursor:pointer;">招待好友【虎子】施展豐收奇蹟 (+500 小麥)</button>
                    </div>
                    <div style="background:rgba(236,72,153,0.1); border:1px solid #ec4899; border-radius:12px; padding:14px;">
                        <h4 style="margin:0 0 6px 0; color:#f472b6;">🆘 天災共同防線：呼叫好友神明幻影護盾</h4>
                        <p style="font-size:12px; color:#cbd5e1; margin:0 0 10px 0;">遭遇百年寒冬或反神衝鋒時，調用朋友的神明幻影撐起 60 秒恆溫無敵防禦罩！</p>
                        <button id="btn-social-aegis" style="width:100%; padding:8px; background:#db2777; border:none; border-radius:8px; color:#fff; font-weight:bold; cursor:pointer;">呼叫好友【阿修羅神明】展開 60 秒恆溫護盾</button>
                    </div>
                    <div style="background:rgba(16,185,129,0.1); border:1px solid #10b981; border-radius:12px; padding:14px;">
                        <h4 style="margin:0 0 6px 0; color:#34d399;">👍📦 死亡擱淺式漂流補給箱共享</h4>
                        <p style="font-size:12px; color:#cbd5e1; margin:0 0 10px 0;">海灘漂來陌生好友多餘的工研補給箱，點讚感恩解鎖精煉曜石與黃金天使光環！</p>
                        <button id="btn-social-box" style="width:100%; padding:8px; background:#059669; border:none; border-radius:8px; color:#fff; font-weight:bold; cursor:pointer;">點讚拾取漂流補給箱 (+150 曜石 / +80 泰坦合金)</button>
                    </div>
                </div>
            `;
        } else if (tab === 'cozy') {
            return `
                <div style="background:rgba(236,72,153,0.1); border:1px solid #ec4899; border-radius:12px; padding:16px;">
                    <h3 style="margin-top:0; color:#f472b6;">🎨✨ 美學即戰力：信仰裝飾與心情共振</h3>
                    <p style="font-size:13px; line-height:1.6; color:#cbd5e1;">
                        裝扮不只是好看！當神獸穿上櫻花蝴蝶結或村莊鋪設發光水晶步道，系統計算<b>美學共振半徑</b>：<br>
                        • 村民<b>幸福感上限突破至 150%</b>，工作疲勞累積速度減半！<br>
                        • 村民圍觀拍手釋放珍稀<b>【愛心結晶法力 (Love Mana)】</b>，是鍛造頂級奇蹟軍武的唯一媒介！
                    </p>
                    <div style="margin-top:16px; display:flex; gap:12px;">
                        <button id="btn-cozy-sakura" style="flex:1; padding:10px; background:linear-gradient(135deg, #ec4899, #f43f5e); border:none; border-radius:8px; color:#fff; font-weight:bold; cursor:pointer;">
                            🌸 裝配【櫻花粉彩蝴蝶結】(+150 愛心法力)
                        </button>
                        <button id="btn-cozy-crystal" style="flex:1; padding:10px; background:linear-gradient(135deg, #8b5cf6, #a855f7); border:none; border-radius:8px; color:#fff; font-weight:bold; cursor:pointer;">
                            ⛲ 鋪設【發光水晶噴泉步道】(150% 幸福突破)
                        </button>
                    </div>
                </div>
            `;
        } else if (tab === 'fail') {
            return `
                <div style="display:flex; flex-direction:column; gap:12px;">
                    <div style="background:rgba(16,185,129,0.1); border:1px solid #10b981; border-radius:12px; padding:14px;">
                        <h4 style="margin:0 0 6px 0; color:#34d399;">🏛️✨ 美麗古典遺跡重生系統 (Failure as a Feature)</h4>
                        <p style="font-size:12px; color:#cbd5e1; margin:0 0 10px 0;">村莊毀滅不顯 Game Over，轉為綠苔發光的古典遺跡！開採遺物解鎖隱藏奇觀【自動浮空石鶴】！</p>
                        <button id="btn-fail-ruins" style="width:100%; padding:8px; background:#059669; border:none; border-radius:8px; color:#fff; font-weight:bold; cursor:pointer;">觸發村莊毀滅重生 (+50 古智慧遺物 / 解鎖石鶴)</button>
                    </div>
                    <div style="background:rgba(245,158,11;0.1); border:1px solid #f59e0b; border-radius:12px; padding:14px;">
                        <h4 style="margin:0 0 6px 0; color:#fbbf24;">🦁✨ 神獸生物抗體定向突變 (Beast Antibody Evolution)</h4>
                        <p style="font-size:12px; color:#cbd5e1; margin:0 0 10px 0;">神獸被打倒化為金色光繭，甦醒突變出定向抗體甲殼！吸收相剋傷害轉化為反打電漿砲！</p>
                        <div style="display:flex; gap:8px;">
                            <button id="btn-fail-lightning" style="flex:1; padding:8px; background:#d97706; border:none; border-radius:8px; color:#fff; font-weight:bold; cursor:pointer;">⚡ 突變【避雷針角】(雷電免疫反打)</button>
                            <button id="btn-fail-thermal" style="flex:1; padding:8px; background:#ea580c; border:none; border-radius:8px; color:#fff; font-weight:bold; cursor:pointer;">🔥 突變【隔熱外骨骼】(熔岩免疫)</button>
                        </div>
                    </div>
                </div>
            `;
        }
    }
}
