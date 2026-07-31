import { CREATURE_SPECIES } from '../creature/creature-data.js?v=3';
import { getMiraclesByCategory, MIRACLE_DATABASE } from '../miracles/miracle-data.js?v=3';
import { godProgression, TALENT_BRANCHES } from '../meta/progression.js?v=3';
import { creatureSkins, ACCESSORY_DATABASE } from '../meta/creature-skins.js?v=3';
import { godAchievements, DAILY_QUEST_CONFIGS, ACHIEVEMENT_CONFIGS } from '../meta/achievements.js?v=3';
import { monetization, SHOP_ITEMS } from '../sdk/monetization.js?v=3';
import { i18n } from '../engine/i18n.js?v=3';
import { BUILDING_DATABASE } from '../entities/building.js?v=3';

/**
 * 商業級 UI 介面與 HUD 控制器 (Commercial UI Manager & HUD Controller)
 * 負責渲染法術卡片、神獸 19 種物種選擇卡、關卡切換、獻祭區互動與商務模組 (天賦、商城、裝扮、任務) 視窗交互。
 */
export class UIManager {
    constructor(callbacks) {
        this.callbacks = callbacks;
        this.selectedStageId = 1;
        this.selectedSpeciesId = 'ape';
        this.activeSpellCategory = 'good';
        this.selectedSpellId = null;

        this.initModals();
        this.initSpellbookTabs();
        this.initSacrificeZone();
        this.initButtons();
        this.initCommercialListeners();

        this.updateCrystalsDisplay();
        this.updateRedDots();
    }

    initCommercialListeners() {
        godProgression.onChange(() => {
            this.updateCrystalsDisplay();
            this.updateRedDots();
            this.initModals(); // 重新整理神獸選單是否解鎖鎖頭
        });
        creatureSkins.onChange(() => {
            this.updateCrystalsDisplay();
        });
        godAchievements.onChange(() => {
            this.updateCrystalsDisplay();
            this.updateRedDots();
        });
    }

    updateCrystalsDisplay() {
        const valEl = document.getElementById('crystal-value');
        if (valEl) valEl.textContent = godProgression.crystals;

        const tCrystal = document.getElementById('modal-talents-crystal');
        if (tCrystal) tCrystal.textContent = godProgression.crystals;

        const sCrystal = document.getElementById('modal-skins-crystal');
        if (sCrystal) sCrystal.textContent = godProgression.crystals;

        const shCrystal = document.getElementById('modal-shop-crystal');
        if (shCrystal) shCrystal.textContent = godProgression.crystals;
    }

    updateRedDots() {
        const qBtn = document.getElementById('btn-quests');
        if (qBtn) {
            const hasRed = godAchievements.hasUnclaimedOrActiveQuests();
            let dot = qBtn.querySelector('.badge-dot');
            if (hasRed && !dot) {
                dot = document.createElement('span');
                dot.className = 'badge-dot';
                qBtn.appendChild(dot);
            } else if (!hasRed && dot) {
                qBtn.removeChild(dot);
            }
        }
    }

    initModals() {
        // 1. 生成 19 種神獸卡片到 Modal 中 (支援鎖頭與傳說標籤)
        const grid = document.getElementById('creature-select-grid');
        if (grid) {
            grid.innerHTML = CREATURE_SPECIES.map(s => {
                const isLocked = s.premium && !godProgression.unlockedBeasts.includes(s.id);
                return `
                <div class="creature-card ${s.id === this.selectedSpeciesId ? 'selected' : ''} ${isLocked ? 'locked' : ''}" 
                     data-species="${s.id}" title="${s.desc}">
                    <span class="creature-card-emoji">${s.symbol}</span>
                    <strong class="creature-card-name">${s.name.split(' ')[1] || s.name}</strong>
                    <span class="creature-card-en">${s.name.split(' ')[0]}</span>
                    ${isLocked ? `<span class="creature-lock-badge" style="color:#ef4444; font-size:0.8rem; font-weight:bold;">🔒 需購買 (${s.cost}💎)</span>` : ''}
                </div>
            `;
            }).join('');

            grid.querySelectorAll('.creature-card').forEach(card => {
                card.addEventListener('click', () => {
                    const spId = card.dataset.species;
                    const sp = CREATURE_SPECIES.find(s => s.id === spId);
                    const isLocked = sp && sp.premium && !godProgression.unlockedBeasts.includes(spId);

                    if (isLocked) {
                        this.showNotice(`🔒 【${sp.name}】是商用傳說神獸！正在為您導航至商城解鎖...`, 'info');
                        document.getElementById('modal-shop')?.classList.add('active');
                        this.renderShopModal();
                        return;
                    }

                    grid.querySelectorAll('.creature-card').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    this.selectedSpeciesId = spId;
                });
            });
        }

        // 2. 關卡選擇卡片點擊
        const stageGrid = document.getElementById('stage-select-grid');
        if (stageGrid) {
            stageGrid.querySelectorAll('.stage-card').forEach(card => {
                card.addEventListener('click', () => {
                    stageGrid.querySelectorAll('.stage-card').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    this.selectedStageId = Number(card.dataset.stage);
                });
            });
        }

        // 3. 開始遊戲按鈕
        const btnStart = document.getElementById('btn-start-game');
        if (btnStart) {
            // 避免重複綁定監聽器
            btnStart.replaceWith(btnStart.cloneNode(true));
            document.getElementById('btn-start-game').addEventListener('click', () => {
                document.getElementById('modal-start').classList.remove('active');
                if (this.callbacks.onStartGame) {
                    this.callbacks.onStartGame(this.selectedStageId, this.selectedSpeciesId);
                }
            });
        }

        // 4. 通用 Modal 關閉按鈕
        document.querySelectorAll('.close-modal-btn').forEach(btn => {
            btn.replaceWith(btn.cloneNode(true));
        });
        document.querySelectorAll('.close-modal-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.target;
                if (target) document.getElementById(target)?.classList.remove('active');
            });
        });
    }

    initSpellbookTabs() {
        const tabs = document.querySelectorAll('.tab-btn');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.activeSpellCategory = tab.dataset.category;
                this.renderSpellCards();
            });
        });
        this.renderSpellCards();
    }

    renderSpellCards(currentEnergy = 500, isSandbox = false) {
        const container = document.getElementById('spell-cards-container');
        if (!container) return;

        const spells = getMiraclesByCategory(this.activeSpellCategory);
        container.innerHTML = spells.map(sp => {
            const canCast = isSandbox || currentEnergy >= sp.cost;
            const isSelected = this.selectedSpellId === sp.id;
            return `
                <div class="spell-card ${canCast ? '' : 'disabled'} ${isSelected ? 'selected-spell' : ''}" 
                     data-spell="${sp.id}" title="${sp.desc}">
                    <div class="spell-card-top">
                        <span class="spell-icon">${sp.icon}</span>
                        <span class="spell-cost">⚡${sp.cost}</span>
                    </div>
                    <strong class="spell-name">${sp.name}</strong>
                    <div class="spell-gesture">
                        <span>手勢:</span>
                        <span class="spell-gesture-symbol">${sp.symbol}</span>
                    </div>
                </div>
            `;
        }).join('');

        container.querySelectorAll('.spell-card').forEach(card => {
            card.addEventListener('click', () => {
                const spId = card.dataset.spell;
                const sp = MIRACLE_DATABASE[spId];
                if (!sp) return;

                if (!isSandbox && currentEnergy < sp.cost) {
                    this.showNotice('⚡ 能量不足！請抓取樹木/動物丟入左側【祭壇】獻祭，或點擊【召喚祈禱】按鈕！', 'error');
                    return;
                }

                this.selectedSpellId = this.selectedSpellId === spId ? null : spId;
                container.querySelectorAll('.spell-card').forEach(c => c.style.borderColor = 'rgba(255,255,255,0.12)');
                if (this.selectedSpellId) {
                    card.style.borderColor = '#38bdf8';
                    card.style.boxShadow = '0 0 16px rgba(56, 189, 248, 0.6)';
                    this.showNotice(`🪄 已選取【${sp.name}】，請在畫面上**點擊目標位置**施放！`, 'info');
                } else {
                    this.showNotice('已取消選取法術', 'info');
                }
                if (this.callbacks.onSelectSpell) {
                    this.callbacks.onSelectSpell(this.selectedSpellId);
                }
            });
        });
    }

    initSacrificeZone() {
        const zone = document.getElementById('sacrifice-zone');
        if (!zone) return;

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('drag-over');
        });
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');
        });
    }

    showSacrificeFeedback(text) {
        const fb = document.getElementById('sacrifice-feedback');
        if (fb) {
            fb.textContent = text;
            setTimeout(() => { if (fb.textContent === text) fb.textContent = ''; }, 2000);
        }
    }

    initButtons() {
        document.getElementById('btn-audio')?.addEventListener('click', (e) => {
            if (this.callbacks.onToggleAudio) {
                const muted = this.callbacks.onToggleAudio();
                e.target.textContent = muted ? '🔇' : '🔊';
            }
        });

        document.getElementById('btn-toggle-pray')?.addEventListener('click', (e) => {
            const btn = e.currentTarget;
            btn.classList.toggle('active');
            const isActive = btn.classList.contains('active');
            btn.querySelector('.btn-text').textContent = isActive ? '🙏 村民正在祭壇熱切祈禱中 (點擊取消)' : '召喚村民前往祭壇祈禱 (+持續產能)';
            if (this.callbacks.onTogglePray) this.callbacks.onTogglePray(isActive);
        });

        document.getElementById('btn-change-creature')?.addEventListener('click', () => {
            document.getElementById('modal-start').classList.add('active');
        });

        document.getElementById('btn-build')?.addEventListener('click', () => {
            this.renderBuildModal();
            document.getElementById('modal-build')?.classList.add('active');
        });

        // 神獸牽繩與管教按鈕
        const leashBtns = document.querySelectorAll('.leash-btn');
        leashBtns.forEach((btn, idx) => {
            btn.addEventListener('click', () => {
                leashBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const modes = ['village', 'roam', 'enemy'];
                if (this.callbacks.onChangeLeash) this.callbacks.onChangeLeash(modes[idx]);
            });
        });

        document.getElementById('btn-pet')?.addEventListener('click', () => {
            if (this.callbacks.onPet) this.callbacks.onPet();
        });

        document.getElementById('btn-slap')?.addEventListener('click', () => {
            if (this.callbacks.onSlap) this.callbacks.onSlap();
        });

        // 商業化 HUD 按鈕綁定
        document.getElementById('btn-talents')?.addEventListener('click', () => {
            this.renderTalentsModal();
            document.getElementById('modal-talents')?.classList.add('active');
        });

        document.getElementById('btn-skins')?.addEventListener('click', () => {
            this.renderSkinsModal();
            document.getElementById('modal-skins')?.classList.add('active');
        });

        document.getElementById('btn-shop')?.addEventListener('click', () => {
            this.renderShopModal();
            document.getElementById('modal-shop')?.classList.add('active');
        });
        document.querySelector('.crystal-display')?.addEventListener('click', () => {
            this.renderShopModal();
            document.getElementById('modal-shop')?.classList.add('active');
        });

        document.getElementById('btn-quests')?.addEventListener('click', () => {
            this.renderQuestsModal();
            document.getElementById('modal-quests')?.classList.add('active');
        });

        document.getElementById('btn-lang')?.addEventListener('click', () => {
            const langs = ['zh-TW', 'en-US', 'ja-JP', 'zh-CN'];
            const currentIdx = langs.indexOf(i18n.currentLang);
            const nextLang = langs[(currentIdx + 1) % langs.length];
            i18n.setLanguage(nextLang);
            this.showNotice(`🌐 語言已切換為：${nextLang}`, 'info');
        });

        document.getElementById('btn-tutorial')?.addEventListener('click', () => {
            document.getElementById('modal-tutorial')?.classList.add('active');
        });
    }

    /**
     * 渲染天賦聖殿內容
     */
    renderTalentsModal() {
        const grid = document.getElementById('talents-grid');
        if (!grid) return;
        this.updateCrystalsDisplay();

        grid.innerHTML = Object.values(TALENT_BRANCHES).map(branch => `
            <div class="talent-branch-col" style="border-top: 4px solid ${branch.color};">
                <div class="branch-title" style="color: ${branch.color};">${branch.name}</div>
                <p style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 8px;">${branch.desc}</p>
                ${branch.talents.map(t => {
                    const currentLvl = godProgression.talents[t.id] || 0;
                    const isMax = currentLvl >= t.maxLevel;
                    const cost = godProgression.getTalentCost(t.id);
                    const canAfford = !isMax && godProgression.crystals >= cost;
                    return `
                        <div class="talent-card">
                            <div class="talent-top">
                                <span class="talent-name">${t.icon} ${t.name}</span>
                                <span class="talent-lvl">Lv.${currentLvl}/${t.maxLevel}</span>
                            </div>
                            <div class="talent-desc">${t.desc}</div>
                            <button class="talent-btn" data-talent="${t.id}" ${canAfford ? '' : 'disabled'}>
                                ${isMax ? '✅ 已達滿級' : `💎 升級 (${cost} 水晶)`}
                            </button>
                        </div>
                    `;
                }).join('')}
            </div>
        `).join('');

        grid.querySelectorAll('.talent-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const talentId = btn.dataset.talent;
                const res = godProgression.upgradeTalent(talentId);
                if (res.success) {
                    this.showNotice('🏛️ ' + res.msg, 'info');
                    this.renderTalentsModal();
                } else {
                    this.showNotice('❌ ' + res.msg, 'error');
                }
            });
        });
    }

    /**
     * 渲染獸舍裝扮內容
     */
    renderSkinsModal() {
        const grid = document.getElementById('skins-grid');
        if (!grid) return;
        this.updateCrystalsDisplay();

        grid.innerHTML = Object.values(ACCESSORY_DATABASE).map(acc => {
            const isUnlocked = creatureSkins.unlockedAccessories.includes(acc.id);
            const isEquipped = creatureSkins.equippedAccessory === acc.id;
            return `
                <div class="comm-card" style="${isEquipped ? 'border-color:#22c55e; box-shadow:0 0 15px rgba(34,197,94,0.3);' : ''}">
                    <div class="comm-icon">${acc.symbol}</div>
                    <div class="comm-title">${acc.name}</div>
                    <div class="comm-desc">${acc.desc}</div>
                    <button class="comm-action-btn ${isEquipped ? 'btn-equip-active' : (isUnlocked ? 'btn-equip-idle' : 'btn-buy-crystal')}"
                            data-acc="${acc.id}" data-unlocked="${isUnlocked}">
                        ${isEquipped ? '✅ 使用中' : (isUnlocked ? '👑 裝備' : `💎 購買解鎖 (${acc.cost} 水晶)`)}
                    </button>
                </div>
            `;
        }).join('');

        grid.querySelectorAll('.comm-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const accId = btn.dataset.acc;
                const isUnlocked = btn.dataset.unlocked === 'true';
                if (isUnlocked) {
                    const res = creatureSkins.equip(accId);
                    this.showNotice('👑 ' + res.msg, 'info');
                } else {
                    const res = creatureSkins.unlock(accId);
                    if (res.success) {
                        creatureSkins.equip(accId);
                        this.showNotice('🎉 ' + res.msg, 'info');
                    } else {
                        this.showNotice('❌ ' + res.msg, 'error');
                    }
                }
                this.renderSkinsModal();
            });
        });
    }

    /**
     * 渲染商城內容
     */
    renderShopModal() {
        const grid = document.getElementById('shop-grid');
        if (!grid) return;
        this.updateCrystalsDisplay();

        grid.innerHTML = SHOP_ITEMS.map(item => {
            let isOwned = false;
            if (item.type === 'beast' && godProgression.unlockedBeasts.includes(item.speciesId)) isOwned = true;
            if (item.type === 'skin' && creatureSkins.unlockedAccessories.includes(item.skinId)) isOwned = true;

            let btnClass = 'btn-buy-crystal';
            let btnText = `💎 ${item.price} 水晶購買`;
            if (item.costType === 'ad') { btnClass = 'btn-buy-ad'; btnText = '📺 觀看 30秒 廣告免費領'; }
            if (item.costType === 'iap') { btnClass = 'btn-buy-iap'; btnText = `💳 支付 ${item.price}`; }
            if (isOwned) { btnClass = 'btn-equip-idle'; btnText = '✅ 已擁有 / 已解鎖'; }

            return `
                <div class="comm-card">
                    <div class="comm-icon">${item.icon}</div>
                    <div class="comm-title">${item.title}</div>
                    <div class="comm-desc">${item.desc}</div>
                    <button class="comm-action-btn ${btnClass}" data-item="${item.id}" ${isOwned ? 'disabled' : ''}>
                        ${btnText}
                    </button>
                </div>
            `;
        }).join('');

        grid.querySelectorAll('.comm-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const itemId = btn.dataset.item;
                const item = SHOP_ITEMS.find(i => i.id === itemId);
                if (!item) return;

                const res = monetization.purchaseItem(item, this);
                if (res && res.msg) {
                    this.showNotice(res.success ? res.msg : '❌ ' + res.msg, res.success ? 'info' : 'error');
                }
                if (res && res.success) {
                    this.renderShopModal();
                }
            });
        });
    }

    /**
     * 渲染每日任務與成就內容
     */
    renderQuestsModal() {
        const dList = document.getElementById('daily-quests-list');
        const aList = document.getElementById('achievements-list');
        if (!dList || !aList) return;
        this.updateCrystalsDisplay();

        dList.innerHTML = DAILY_QUEST_CONFIGS.map(q => {
            const prog = godAchievements.dailyProgress[q.id] || 0;
            const isClaimed = godAchievements.dailyClaimed[q.id];
            const isReady = prog >= q.target && !isClaimed;
            return `
                <div class="quest-item" style="${isReady ? 'border-color:#38bdf8; background:rgba(56,189,248,0.1);' : ''}">
                    <div class="quest-left">
                        <span class="quest-icon">${q.icon}</span>
                        <div class="quest-info">
                            <h4>${q.title}</h4>
                            <p>${q.desc}</p>
                        </div>
                    </div>
                    <div class="quest-right">
                        <span class="quest-prog">${prog} / ${q.target}</span>
                        <button class="quest-claim-btn" data-type="daily" data-id="${q.id}" ${!isReady ? 'disabled' : ''}>
                            ${isClaimed ? '✅ 已領獎' : (isReady ? `🎁 領取 +${q.reward}💎` : '進行中')}
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        aList.innerHTML = ACHIEVEMENT_CONFIGS.map(a => {
            const prog = godAchievements.achieveProgress[a.id] || 0;
            const isClaimed = godAchievements.achieveClaimed[a.id];
            const isReady = prog >= a.target && !isClaimed;
            return `
                <div class="quest-item" style="${isReady ? 'border-color:#fbbf24; background:rgba(251,191,36,0.1);' : ''}">
                    <div class="quest-left">
                        <span class="quest-icon">${a.icon}</span>
                        <div class="quest-info">
                            <h4>${a.title}</h4>
                            <p>${a.desc}</p>
                        </div>
                    </div>
                    <div class="quest-right">
                        <span class="quest-prog">${prog} / ${a.target}</span>
                        <button class="quest-claim-btn" data-type="achieve" data-id="${a.id}" ${!isReady ? 'disabled' : ''}>
                            ${isClaimed ? '✅ 已領獎' : (isReady ? `🏆 領取 +${a.reward}💎` : '進行中')}
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        document.querySelectorAll('.quest-claim-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                const type = btn.dataset.type;
                if (type === 'daily') {
                    godAchievements.dailyClaimed[id] = true;
                    const q = DAILY_QUEST_CONFIGS.find(item => item.id === id);
                    if (q) godProgression.addCrystals(q.reward);
                } else if (type === 'achieve') {
                    godAchievements.achieveClaimed[id] = true;
                    const a = ACHIEVEMENT_CONFIGS.find(item => item.id === id);
                    if (a) godProgression.addCrystals(a.reward);
                }
                godAchievements.save();
                this.showNotice('🎉 成功領取水晶獎勵！', 'info');
                this.renderQuestsModal();
            });
        });
    }

    /**
     * 渲染城市奇觀與軍事基地建設 Modal (SimCity vs AoE)
     */
    renderBuildModal() {
        const grid = document.getElementById('build-grid');
        if (!grid) return;
        this.updateCrystalsDisplay();

        grid.innerHTML = Object.values(BUILDING_DATABASE).map(b => `
            <div class="comm-card" style="border-top: 4px solid ${b.category === 'simcity' ? '#facc15' : '#ef4444'};">
                <div class="comm-icon">${b.icon}</div>
                <div class="comm-title" style="color:${b.category === 'simcity' ? '#facc15' : '#ef4444'};">${b.name}</div>
                <div class="comm-desc">${b.desc}</div>
                <div style="font-size:0.8rem; margin:8px 0; color:#cbd5e1;">
                    造價: 🪵 ${b.costWood} 木材 | ⚡ ${b.costEnergy} 能量
                </div>
                <button class="comm-action-btn btn-equip-idle" data-build="${b.id}">
                    ${b.category === 'simcity' ? '⛲ 建造 (提升繁榮度)' : '⚔️ 建造 (訓練出兵)'}
                </button>
            </div>
        `).join('');

        grid.querySelectorAll('.comm-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const buildId = btn.dataset.build;
                if (this.callbacks.onBuildRequest) {
                    const res = this.callbacks.onBuildRequest(buildId);
                    if (res.success) {
                        this.showNotice('🏗️ ' + res.msg, 'info');
                        document.getElementById('modal-build')?.classList.remove('active');
                    } else {
                        this.showNotice('❌ ' + res.msg, 'error');
                    }
                }
            });
        });
    }

    updateHUD(world) {
        if (!world) return;

        this.updateCrystalsDisplay();
        this.updateRedDots();

        // 1. 頂部上帝狀態
        const alignVal = Math.floor(world.godAlignment);
        document.getElementById('alignment-value').textContent = alignVal;
        
        const markerPos = ((alignVal + 100) / 200) * 100;
        const marker = document.getElementById('alignment-marker');
        if (marker) marker.style.left = `${markerPos}%`;

        const titleEl = document.getElementById('god-title');
        const iconEl = document.getElementById('god-icon');
        if (titleEl && iconEl) {
            if (alignVal >= 50) { titleEl.textContent = '神聖救世主'; iconEl.textContent = '😇'; }
            else if (alignVal >= 20) { titleEl.textContent = '慈悲之神'; iconEl.textContent = '🕊️'; }
            else if (alignVal <= -50) { titleEl.textContent = '毀滅破壞神'; iconEl.textContent = '😈'; }
            else if (alignVal <= -20) { titleEl.textContent = '無情之神'; iconEl.textContent = '🦇'; }
            else { titleEl.textContent = '中立之神'; iconEl.textContent = '⚖️'; }
        }

        // 2. 能量顯示
        document.getElementById('energy-value').textContent = Math.floor(world.energy);
        document.getElementById('energy-max').textContent = world.isSandbox ? ' / 無限' : ' / ' + Math.floor(2000 + godProgression.getBonus('max_energy'));
        this.renderSpellCards(world.energy, world.isSandbox);

        // 3. 關卡與部落統治進度
        if (world.stageData && world.villages) {
            document.getElementById('stage-name').textContent = world.stageData.name;
            const controlledCount = world.villages.filter(v => v.owner === 'player').length;
            const totalCount = world.villages.length;
            document.getElementById('stage-objective').textContent = `統治島上所有村莊 (${controlledCount} / ${totalCount})`;
            
            const progPercent = (controlledCount / Math.max(1, totalCount)) * 100;
            const progFill = document.getElementById('obj-progress-fill');
            if (progFill) progFill.style.width = `${progPercent}%`;

            const playerV = world.villages.find(v => v.owner === 'player');
            if (playerV) {
                document.getElementById('stat-pop').textContent = `${playerV.population} / ${playerV.maxPopulation}`;
                document.getElementById('stat-food').textContent = Math.floor(playerV.food);
                document.getElementById('stat-wood').textContent = Math.floor(playerV.wood);
                const prayersCount = world.villagers ? world.villagers.filter(vg => vg.state === 'praying').length : 0;
                document.getElementById('stat-prayers').textContent = `${prayersCount} 人`;
                const prospEl = document.getElementById('stat-prosperity');
                if (prospEl) prospEl.textContent = `${Math.floor(playerV.prosperity)}`;
                const milEl = document.getElementById('stat-military');
                if (milEl) milEl.textContent = `${Math.floor(playerV.militaryPower)}`;
            }

            const vListEl = document.getElementById('village-list');
            if (vListEl) {
                vListEl.innerHTML = world.villages.map(v => `
                    <li class="village-item">
                        <div class="village-item-header">
                            <span>${v.name}</span>
                            <strong style="color: ${v.owner === 'player' ? '#38bdf8' : (v.owner === 'rival' ? '#ef4444' : '#a855f7')}">
                                ${v.owner === 'player' ? '👑 歸順' : (v.owner === 'rival' ? '⚔️ 敵對' : '🤝 中立')} (${Math.floor(v.belief)}%)
                            </strong>
                        </div>
                        <div class="village-bar">
                            <div class="village-fill" style="width: ${v.belief}%; background: ${v.owner === 'player' ? '#38bdf8' : (v.owner === 'rival' ? '#ef4444' : '#a855f7')};"></div>
                        </div>
                    </li>
                `).join('');
            }
        }

        // 4. 神獸心智與數值條
        const c = world.creature;
        if (c && c.species) {
            document.getElementById('creature-emoji').textContent = c.species.symbol;
            document.getElementById('creature-name').textContent = `${c.name} (${c.species.name.split(' ')[0]})`;
            document.getElementById('creature-size-tag').textContent = `體格: ${c.scale > 1.5 ? '巨獸 (2.0x)' : (c.scale < 0.8 ? '幼獸 (0.6x)' : '成長期 (1.0x)')}`;
            
            const alignTag = document.getElementById('creature-align-tag');
            if (alignTag) {
                alignTag.textContent = `傾向: ${c.alignment >= 20 ? '😇 善良' : (c.alignment <= -20 ? '😈 邪惡' : '⚖️ 中立')}`;
                alignTag.className = `tag ${c.alignment >= 20 ? 'good-tag' : (c.alignment <= -20 ? 'evil-tag' : 'neutral-tag')}`;
            }

            document.getElementById('creature-thought').textContent = c.thought;

            document.getElementById('c-stat-health').style.width = `${Math.floor(c.health)}%`;
            document.getElementById('c-stat-hunger').style.width = `${Math.floor(c.hunger)}%`;
            document.getElementById('c-stat-mana').style.width = `${Math.floor(c.mana)}%`;

            const spellListEl = document.getElementById('creature-spell-list');
            if (spellListEl) {
                spellListEl.innerHTML = c.learnedSpells.map(sId => {
                    const sp = MIRACLE_DATABASE[sId];
                    return sp ? `<span class="c-spell-badge" title="${sp.desc}">${sp.icon} ${sp.name.split(' ')[0]}</span>` : '';
                }).join('');
            }
        }
    }

    showNotice(msg, type = 'info') {
        const fb = document.getElementById('sacrifice-feedback');
        if (fb) fb.textContent = msg;
    }

    showGameOver(isWin, godTitle, creatureStatus, onNext, onRestart) {
        const modal = document.getElementById('modal-gameover');
        if (!modal) return;

        document.getElementById('gameover-title').textContent = isWin ? '🏆 信仰統一！神島被您征服' : '💀 信仰潰散，島嶼失去了神蹟';
        document.getElementById('gameover-icon').textContent = isWin ? '🌟' : '⛈️';
        document.getElementById('gameover-desc').textContent = isWin 
            ? '您憑藉著無比神聖的神蹟與強悍的神獸，成功降服並贏得了島上所有部落的虔誠信仰！'
            : '敵對上帝或飢荒毀滅了您的所有信徒，失去了信仰支持的您被迫離開了這座島嶼...';
        
        document.getElementById('final-god-title').textContent = godTitle || '慈悲的救世主';
        document.getElementById('final-creature-status').textContent = creatureStatus || '神聖巨猿';

        const nextBtn = document.getElementById('btn-next-stage');
        if (nextBtn) nextBtn.style.display = isWin ? 'inline-block' : 'none';

        modal.classList.add('active');
    }
}
