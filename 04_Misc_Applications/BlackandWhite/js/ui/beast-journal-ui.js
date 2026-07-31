/**
 * ============================================================================
 * 模組：神獸手帳與 AI 訓練雙態翻轉面板 (BeastJournalUI)
 * 參照任天堂 Easy to learn, hard to master 分層體驗設計
 * 表層：給小孩/休閒玩家的「幼兒園彩色貼紙作息表」(Kids Illustrated Journal)
 * 底層：給大人/玩家的「GOAP 權重與 LLM System Prompt 編輯器」(Adults Logic Gate Editor)
 * 點擊齒輪按鈕即可在雙態介面之間進行 3D 翻轉！
 * ============================================================================
 */

export class BeastJournalUI {
    constructor() {
        this.isOpen = false;
        this.isAdultView = false;
        this.weights = {
            curiosity: 50,
            protectiveness: 80,
            aggressiveness: 30
        };
        this.currentSticker = '🛡️ 堅守崗位';
        this.systemPrompt = 'Thou art a devoted guardian. Thy primary directive is to protect villagers from physical harm. Never abandon the sanctuary radius when enemies are present.';

        this.initDOM();
    }

    initDOM() {
        if (document.getElementById('beast-journal-modal')) return;

        // 建立 CSS
        const style = document.createElement('style');
        style.innerHTML = `
            #btn-open-journal {
                position: absolute;
                bottom: 15px;
                left: 15px;
                background: linear-gradient(135deg, #f59e0b, #d97706);
                color: #fff;
                border: 2px solid #fff;
                border-radius: 30px;
                padding: 10px 20px;
                font-family: 'Outfit', 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
                z-index: 50;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s ease;
            }
            #btn-open-journal:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(245, 158, 11, 0.6); }
            #beast-journal-modal {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 600px;
                height: 480px;
                perspective: 1000px;
                z-index: 100;
                display: none;
            }
            .journal-flipper {
                width: 100%;
                height: 100%;
                position: relative;
                transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1);
                transform-style: preserve-3d;
            }
            .journal-flipper.flipped {
                transform: rotateY(180deg);
            }
            .journal-face {
                position: absolute;
                width: 100%;
                height: 100%;
                backface-visibility: hidden;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 25px 50px rgba(0,0,0,0.6);
            }
            /* 正面：小孩貼紙手帳 */
            .journal-front {
                background: linear-gradient(135deg, #fffbeb, #fef3c7);
                border: 8px solid #f59e0b;
                color: #78350f;
                padding: 24px;
                font-family: 'Outfit', 'Inter', sans-serif;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }
            .journal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px dashed #d97706;
                padding-bottom: 10px;
            }
            .journal-title {
                font-size: 22px;
                font-weight: 800;
                color: #b45309;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .btn-flip-gear {
                background: #0f172a;
                color: #38bdf8;
                border: none;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 700;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s ease;
            }
            .btn-flip-gear:hover { background: #1e293b; transform: scale(1.05); }
            .sticker-slots {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            .slot-row {
                background: rgba(255,255,255,0.7);
                border: 2px solid #fcd34d;
                border-radius: 12px;
                padding: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 15px;
                font-weight: 700;
            }
            .sticker-badge {
                background: #f59e0b;
                color: #fff;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 14px;
                cursor: pointer;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            }
            .sticker-selector {
                margin-top: auto;
                background: #fde68a;
                border-radius: 14px;
                padding: 12px;
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                justify-content: center;
            }
            .sticker-option {
                background: #fff;
                border: 2px solid #f59e0b;
                border-radius: 16px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .sticker-option:hover, .sticker-option.active {
                background: #f59e0b;
                color: #fff;
                transform: scale(1.08);
            }
            /* 背面：大人進階邏輯閘與 Prompt 編輯器 */
            .journal-back {
                background: #0f172a;
                border: 2px solid #38bdf8;
                color: #f8fafc;
                padding: 24px;
                font-family: 'Courier New', monospace;
                transform: rotateY(180deg);
                display: flex;
                flex-direction: column;
                gap: 14px;
            }
            .back-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #334155;
                padding-bottom: 10px;
            }
            .tech-title {
                color: #38bdf8;
                font-size: 16px;
                font-weight: 700;
            }
            .prompt-box {
                background: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
                color: #a7f3d0;
                line-height: 1.5;
                max-height: 80px;
                overflow-y: auto;
            }
            .slider-group {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            .slider-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12px;
            }
            .slider-item input[type=range] {
                width: 60%;
            }
            .btn-apply-ai {
                margin-top: auto;
                background: linear-gradient(135deg, #0284c7, #0369a1);
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: 700;
                font-family: 'Outfit', 'Inter', sans-serif;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .btn-apply-ai:hover { background: linear-gradient(135deg, #38bdf8, #0284c7); }
            .btn-close-modal {
                position: absolute;
                top: 10px;
                right: 15px;
                background: transparent;
                border: none;
                font-size: 20px;
                cursor: pointer;
            }
        `;
        document.head.appendChild(style);

        // 建立開關按鈕
        const btnOpen = document.createElement('button');
        btnOpen.id = 'btn-open-journal';
        btnOpen.innerHTML = `📓 開啟神獸手帳 / AI 面板`;
        btnOpen.addEventListener('click', () => this.toggleModal());
        document.body.appendChild(btnOpen);

        // 建立模態窗面板
        const modal = document.createElement('div');
        modal.id = 'beast-journal-modal';
        modal.innerHTML = `
            <div id="journal-flipper-box" class="journal-flipper">
                <!-- 正面：小孩貼紙手帳 -->
                <div class="journal-face journal-front">
                    <button class="btn-close-modal" onclick="document.getElementById('beast-journal-modal').style.display='none'">✖</button>
                    <div class="journal-header">
                        <div class="journal-title">📓 神獸的彩色生活貼紙簿</div>
                        <button id="btn-flip-to-back" class="btn-flip-gear">⚙️ 總監邏輯閘面板</button>
                    </div>
                    <div class="sticker-slots">
                        <div class="slot-row"><span>🌅 早晨太陽升起：</span><span id="slot-morning" class="sticker-badge">🍎 巡視果園 + 幫忙澆水 💧</span></div>
                        <div class="slot-row"><span>⚔️ 看見壞人入侵：</span><span id="slot-danger" class="sticker-badge">🛡️ 堅守崗位 + 大吼震懾 🦁</span></div>
                        <div class="slot-row"><span>⚠️ 村裡沒食糧時：</span><span id="slot-hunger" class="sticker-badge">🚫 絕對不可吃村民，去抓海魚 🐟</span></div>
                    </div>
                    <div class="sticker-selector">
                        <span style="width:100%; text-align:center; font-size:12px; color:#b45309;">✨ 點擊選擇貼紙並貼到作息表上：</span>
                        <div class="sticker-option" data-sticker="🛡️ 堅守崗位">🛡️ 堅守崗位</div>
                        <div class="sticker-option" data-sticker="💡 聰明工程師">💡 聰明工程師</div>
                        <div class="sticker-option" data-sticker="🔥 毀滅狂王">🔥 毀滅狂王</div>
                        <div class="sticker-option" data-sticker="🍎 貪吃王">🍎 貪吃王</div>
                    </div>
                </div>
                <!-- 背面：大人進階邏輯閘與 Prompt 編輯器 -->
                <div class="journal-face journal-back">
                    <div class="back-header">
                        <div class="tech-title">⚙️ [Adults View] GOAP Weights & LLM System Prompt</div>
                        <button id="btn-flip-to-front" class="btn-flip-gear" style="background:#f59e0b; color:#fff;">📘 返回休閒貼紙簿</button>
                    </div>
                    <div style="font-size:11px; color:#94a3b8;">Generated Real-time System Prompt (Injected to AIAgentBridge):</div>
                    <div id="tech-prompt-box" class="prompt-box">${this.systemPrompt}</div>
                    <div class="slider-group">
                        <div class="slider-item"><span>🔍 Curiosity (好奇心/工程採集):</span><input type="range" id="slider-curiosity" min="0" max="100" value="50"><span id="val-curiosity">50</span></div>
                        <div class="slider-item"><span>🛡️ Protectiveness (保護欲/神殿守衛):</span><input type="range" id="slider-protect" min="0" max="100" value="80"><span id="val-protect">80</span></div>
                        <div class="slider-item"><span>🔥 Aggressiveness (侵略性/破壞攻城):</span><input type="range" id="slider-aggress" min="0" max="100" value="30"><span id="val-aggress">30</span></div>
                    </div>
                    <div style="font-size:11px; color:#cbd5e1;">GOAP Priority: Priority(DEFEND)=100 | Max_Leash_Radius=150m</div>
                    <button id="btn-apply-ai-weights" class="btn-apply-ai">⚡ 應用決策權重與 Prompt 至神獸大腦</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // 綁定翻轉事件
        document.getElementById('btn-flip-to-back')?.addEventListener('click', () => this.flipToBack());
        document.getElementById('btn-flip-to-front')?.addEventListener('click', () => this.flipToFront());

        // 綁定貼紙選擇
        const options = modal.querySelectorAll('.sticker-option');
        options.forEach(opt => {
            opt.addEventListener('click', (e) => {
                options.forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
                this.currentSticker = opt.getAttribute('data-sticker');
                this.applyStickerToSlot('slot-danger', this.currentSticker);
            });
        });

        // 綁定拉桿事件
        document.getElementById('slider-curiosity')?.addEventListener('input', (e) => {
            this.weights.curiosity = parseInt(e.target.value);
            document.getElementById('val-curiosity').innerText = this.weights.curiosity;
            this.updateSystemPromptFromWeights();
        });
        document.getElementById('slider-protect')?.addEventListener('input', (e) => {
            this.weights.protectiveness = parseInt(e.target.value);
            document.getElementById('val-protect').innerText = this.weights.protectiveness;
            this.updateSystemPromptFromWeights();
        });
        document.getElementById('slider-aggress')?.addEventListener('input', (e) => {
            this.weights.aggressiveness = parseInt(e.target.value);
            document.getElementById('val-aggress').innerText = this.weights.aggressiveness;
            this.updateSystemPromptFromWeights();
        });

        // 綁定應用按鈕
        document.getElementById('btn-apply-ai-weights')?.addEventListener('click', () => {
            console.log(`⚡ [BeastJournalUI] 成功應用進階權重與 Prompt 至神獸大腦：`, this.weights);
            alert(`✅ 神獸 AI 大腦權重已生效！\nCuriosity=${this.weights.curiosity}\nProtectiveness=${this.weights.protectiveness}\nAggressiveness=${this.weights.aggressiveness}`);
        });
    }

    toggleModal() {
        const modal = document.getElementById('beast-journal-modal');
        if (!modal) return;
        this.isOpen = !this.isOpen;
        modal.style.display = this.isOpen ? 'block' : 'none';
    }

    flipToBack() {
        const flipper = document.getElementById('journal-flipper-box');
        if (flipper) flipper.classList.add('flipped');
        this.isAdultView = true;
        console.log(`⚙️ [BeastJournalUI] 已翻轉至大人進階邏輯閘與 Prompt 編輯器面板。`);
    }

    flipToFront() {
        const flipper = document.getElementById('journal-flipper-box');
        if (flipper) flipper.classList.remove('flipped');
        this.isAdultView = false;
        console.log(`📘 [BeastJournalUI] 已返回休閒貼紙手帳面板。`);
    }

    applyStickerToSlot(slotId, stickerText) {
        const slot = document.getElementById(slotId);
        if (slot) slot.innerText = stickerText;
        console.log(`📓 [BeastJournalUI] 在時段 [${slotId}] 貼上新貼紙：${stickerText}`);
        
        // 自動同步底層權重
        if (stickerText.includes('堅守崗位')) {
            this.weights.protectiveness = 95; this.weights.aggressiveness = 20;
        } else if (stickerText.includes('工程師')) {
            this.weights.curiosity = 90;
        } else if (stickerText.includes('毀滅狂王')) {
            this.weights.aggressiveness = 95; this.weights.protectiveness = 15;
        }
        
        // 更新滑桿畫面
        if (document.getElementById('slider-protect')) document.getElementById('slider-protect').value = this.weights.protectiveness;
        if (document.getElementById('val-protect')) document.getElementById('val-protect').innerText = this.weights.protectiveness;
        if (document.getElementById('slider-curiosity')) document.getElementById('slider-curiosity').value = this.weights.curiosity;
        if (document.getElementById('val-curiosity')) document.getElementById('val-curiosity').innerText = this.weights.curiosity;
        if (document.getElementById('slider-aggress')) document.getElementById('slider-aggress').value = this.weights.aggressiveness;
        if (document.getElementById('val-aggress')) document.getElementById('val-aggress').innerText = this.weights.aggressiveness;

        this.updateSystemPromptFromWeights();
    }

    updateSystemPromptFromWeights() {
        if (this.weights.protectiveness > 70) {
            this.systemPrompt = `Thou art a devoted guardian (Protect=${this.weights.protectiveness}). Thy primary directive is to protect villagers from physical harm. Never abandon the sanctuary radius when enemies are present.`;
        } else if (this.weights.curiosity > 70) {
            this.systemPrompt = `Thou art a curious scholar and engineer (Curiosity=${this.weights.curiosity}). Observe player building patterns and actively seek out unharvested rare minerals or broken supply chains to repair.`;
        } else if (this.weights.aggressiveness > 70) {
            this.systemPrompt = `Thou art a ruthless apex predator (Aggress=${this.weights.aggressiveness}). Show no mercy to rival factions. Your goal is absolute subjugation and territorial expansion through fear and destruction.`;
        } else {
            this.systemPrompt = `Thou art a balanced Divine Beast (Curiosity=${this.weights.curiosity}, Protect=${this.weights.protectiveness}, Aggress=${this.weights.aggressiveness}). Act autonomously based on village needs.`;
        }

        const promptBox = document.getElementById('tech-prompt-box');
        if (promptBox) promptBox.innerText = this.systemPrompt;
    }
}
