import { Camera } from './engine/camera.js?v=3';
import { ParticleEngine } from './engine/particles.js?v=3';
import { SoundEngine } from './engine/audio.js?v=3';
import { GestureEngine } from './engine/gesture.js?v=3';
import { CanvasRenderer } from './engine/canvas-renderer.js?v=3';
import { FixedStepLoop } from './engine/loop.js?v=3';
import { gameStorage } from './engine/storage.js?v=3';
import { i18n } from './engine/i18n.js?v=3';
import { ECSBattleEngine } from './engine/ecs-battle.js?v=3';
import { FlowFieldManager } from './engine/flow-field.js?v=3';
import { BattleRendererLOD } from './engine/lod-renderer.js?v=3';
import { configLoader } from './engine/config-loader.js?v=3';
import { MoralitySystem } from './engine/morality-system.js?v=3';
import { VeteranEvolution } from './engine/veteran-evolution.js?v=3';
import { AudioVFXCoordinator } from './engine/audio-vfx-coordinator.js?v=3';
import { aiAgentBridge } from './engine/ai-agent-bridge.js?v=3';
import { SupplyChainManager } from './engine/supply-chain.js?v=3';
import { PrewarningRadarUI } from './ui/prewarning-radar.js?v=3';
import { BeastJournalUI } from './ui/beast-journal-ui.js?v=3';
import { GaaSEcosystemManager } from './engine/gaas-ecosystem.js?v=3';
import { GaaSHubUI } from './ui/gaas-hub-ui.js?v=3';

import { ResourceEntity } from './entities/resource.js?v=3';
import { VillagerEntity } from './entities/villager.js?v=3';
import { VillageEntity } from './entities/village.js?v=3';
import { BuildingEntity, BUILDING_DATABASE } from './entities/building.js?v=3';
import { TroopEntity } from './entities/troop.js?v=3';
import { RivalCreature } from './creature/rival-creature.js?v=3';
import { SideQuestManager } from './stages/side-quests.js?v=3';

import { CreatureAI } from './creature/creature-ai.js?v=3';
import { CreatureTrainer } from './creature/creature-trainer.js?v=3';

import { getMiraclesByGestureSymbol, MIRACLE_DATABASE } from './miracles/miracle-data.js?v=3';
import { MiracleCaster } from './miracles/miracle-caster.js?v=3';

import { getStageData } from './stages/stage-data.js?v=3';
import { UIManager } from './ui/ui-manager.js?v=3';
import { godProgression } from './meta/progression.js?v=3';
import { creatureSkins } from './meta/creature-skins.js?v=3';
import { godAchievements } from './meta/achievements.js?v=3';
import { monetization } from './sdk/monetization.js?v=3';
import { analytics } from './sdk/analytics.js?v=3';

/**
 * 商業級遊戲主控制迴圈與狀態管理器 (Commercial Game Loop & World Context)
 * 整合所有引擎模組、實體物理、固定步長迴圈、儲存防篡改、天賦加成與商務遙測。
 */
class GameMain {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.gestureCanvas = document.getElementById('gesture-canvas');

        // 1. 建立核心引擎模組
        this.camera = new Camera(this.canvas);
        this.particleEngine = new ParticleEngine(this.canvas);
        this.soundEngine = new SoundEngine();
        this.canvasRenderer = new CanvasRenderer(this.canvas, this.camera);
        this.miracleCaster = new MiracleCaster(this.particleEngine, this.soundEngine);

        // 2. 手勢辨識回調
        this.gestureEngine = new GestureEngine(this.gestureCanvas, this.camera, (symbolName, wx, wy) => {
            this.handleGestureRecognized(symbolName, wx, wy);
        });

        // 3. 遊戲世界狀態
        this.stageData = null;
        this.isSandbox = false;
        this.energy = 500;
        this.godAlignment = 0; // -100 ~ +100
        this.villages = [];
        this.resources = [];
        this.villagers = [];
        this.creature = null;
        this.creatureTrainer = null;
        this.buildings = [];
        this.troops = [];
        this.rivalCreatures = [];
        this.sideQuestManager = null;

        // 戰場 ECS 實體組件、流場導航與 LOD 實體化渲染器
        this.ecsBattle = new ECSBattleEngine(2048);
        this.flowField = new FlowFieldManager(100, 100, 40);
        this.lodRenderer = new BattleRendererLOD(null, 2048);

        // 綁定主控台全局千人戰役演習測試指令與配置管理介面
        window.startBattleTest = (count = 1000) => this.startBattleTest(count);
        this.configLoader = configLoader;
        window.gameConfig = configLoader;

        // 善惡文化同化、老兵世代演進與音效粒子聚合器 (Phase 3 & Phase 4)
        this.morality = new MoralitySystem(this.godAlignment);
        this.veteranEvolution = new VeteranEvolution(this.ecsBattle);
        this.audioVfxCoordinator = new AudioVFXCoordinator(this);

        // 商業化升級 Phase 6：三階段物化信仰供應鏈與極光預警雷達 UI
        this.supplyChain = new SupplyChainManager();
        this.prewarningRadar = new PrewarningRadarUI();

        // 全齡向體驗 Phase 7：任天堂式分層雙態手帳作息表 AI 邏輯閘面板 UI
        this.beastJournal = new BeastJournalUI();

        // 普世化服務型遊戲生態 Phase 8：跨平台通勤同步、異步互助、Cozy 裝飾與向敗而生 UI
        this.gaas = new GaaSEcosystemManager();
        this.gaasHubUI = new GaaSHubUI();

        // 綁定主控台進階驗證指令 (Phase 3 & Phase 4 壓測專用)
        window.testMoralityRoute = (route) => {
            if (route === 'good') {
                this.morality.onPlayerAction('HEAL_VILLAGERS', 80, this.uiManager);
                this.morality.prosperity = 90;
                this.godAlignment = this.morality.alignment;
                console.log("😇 [Test] 已切換至王道善良路線 (Paragon)！");
            } else if (route === 'evil') {
                this.morality.onPlayerAction('CAST_METEOR', 80, this.uiManager);
                this.morality.dread = 90;
                this.godAlignment = this.morality.alignment;
                console.log("😈 [Test] 已切換至霸道邪惡路線 (Tyrant)！");
            }
        };
        window.testVeteranPromotion = () => this.veteranEvolution.promoteAllPlayerUnits(5);
        window.testAssimilationSurrender = (type = 'peace') => {
            const enemyV = this.villages.find(v => v.owner !== 'player');
            if (enemyV) {
                if (type === 'peace') {
                    this.morality.alignment = 60; this.morality.prosperity = 100;
                    enemyV.addBelief(100, true);
                } else {
                    this.morality.alignment = -60; this.morality.dread = 100;
                    enemyV.addBelief(100, false);
                }
                console.log(`🏳️ [Test] 已觸發敵村 ${enemyV.name} 的【${type === 'peace' ? '和平同化歸順' : '恐懼威懾逼降'}】！`);
            }
        };

        // Phase 5 自主 AI 代理人與在地化 LLM 測試指令
        this.aiAgentBridge = aiAgentBridge;
        window.aiAgentBridge = aiAgentBridge;
        window.testLLMAgentDecision = (driver = 'heuristic') => {
            aiAgentBridge.setDriver(driver);
            if (this.creature) {
                this.creature.makeDecision(this.resources, this.villages, this.villages[0] || {x: 1000, y: 1050}, this.miracleCaster, this.soundEngine);
                console.log(`🤖 [Test] 已觸發神獸 AI 代理人以【${driver}】驅動進行自律推論！`);
            } else {
                console.warn(`⚠️ [Test] 當前場上無神獸，請先進入遊戲關卡。`);
            }
        };
        window.injectAgentSensoryEvent = (type, desc, impact) => {
            if (this.creature && this.creature.agentMemory) {
                this.creature.agentMemory.addSensoryEvent(type, desc, impact);
            } else {
                console.warn(`⚠️ [Test] 當前神獸記憶庫未初始化。`);
            }
        };
        window.testCreatureRebellion = () => {
            if (this.creature && this.creature.agentMemory) {
                this.creature.agentMemory.injectRebellionMemory();
                aiAgentBridge.setDriver('heuristic');
                this.creature.makeDecision(this.resources, this.villages, this.villages[0] || {x: 1000, y: 1050}, this.miracleCaster, this.soundEngine);
                console.log(`⚡ [Test] 已注入極端虐待記憶並觸發神獸自主推論反抗 (Rebellion)！`);
            } else {
                console.warn(`⚠️ [Test] 當前場上無神獸。`);
            }
        };

        // Phase 6 商業化與現代化升級進階驗證指令
        window.testCrisisWarning = (type = 'sacrifice') => {
            const crisis = type === 'sacrifice' ? 'HERETICAL_BLOOD_SACRIFICE' : (type === 'defection' ? 'UNDERGROUND_DEFECTION' : 'CRUSADE_INVASION');
            this.prewarningRadar.showCrisisCard(crisis, this.supplyChain, this.creature, this.uiManager);
        };
        window.testSupplyChainCrafting = (amount = 500) => {
            this.supplyChain.injectResources(amount);
            if (this.uiManager) this.uiManager.showNotice(`📈 [Test] 注入大量高階物化資源！財富熱度飆升！`, 'warning');
        };
        window.testEquipBeastMecha = (type = 'arc_cannon') => {
            this.supplyChain.inventory.titan_alloy += 100;
            this.supplyChain.inventory.faith_crystal += 50;
            this.supplyChain.equipBeastMecha(this.creature, type, this.uiManager);
        };
        window.testEnchantRTSUnits = () => {
            this.supplyChain.inventory.faith_crystal += 50;
            this.supplyChain.enchantRTSUnits(this.uiManager);
        };

        // Phase 7 任天堂式分層體驗進階驗證指令
        window.testGoldenAppleEvent = () => {
            this.supplyChain.triggerGoldenMegaApple(this.uiManager);
        };
        window.testBeastAppleBite = () => {
            this.supplyChain.triggerBeastAppleBite(this.creature, this.uiManager);
        };
        window.testElementalChain = (type = 'gas_balloon') => {
            this.supplyChain.triggerElementalChain(type, this.uiManager);
        };
        window.testBeastJournal = () => {
            if (this.beastJournal) this.beastJournal.toggleModal();
        };
        window.testGlacialWinter = (path = 'glasshouse') => {
            this.morality.triggerGlacialWinterEvent(path, this.villages, this.uiManager);
        };

        // Phase 8 GaaS 普世化服務型遊戲生態進階驗證指令
        window.testMobileCommuteSync = () => {
            if (this.gaas) this.gaas.simulateMobileCommuteSession(50, 100, this.supplyChain, this.uiManager);
        };
        window.testBeastAmbassador = () => {
            if (this.gaas) this.gaas.triggerBeastAmbassadorVisit("好友【虎子】", this.supplyChain, this.uiManager);
        };
        window.testFriendDivineAegis = () => {
            if (this.gaas) this.gaas.summonFriendDivineAegis("阿修羅神明", this.uiManager);
        };
        window.testStrandSupplyBox = () => {
            if (this.gaas) this.gaas.spawnStrandSupplyBox(this.supplyChain, this.uiManager);
        };
        window.testCozyAesthetics = (palette = 'sakura_pastel') => {
            if (this.gaas) this.gaas.updateAestheticResonance('angel_ribbon', palette, this.supplyChain, this.villagers, this.uiManager);
        };
        window.testRuinsRebirth = () => {
            if (this.supplyChain) this.supplyChain.triggerVillageDestructionRebirth(this.villages[0], this.uiManager);
        };
        window.testBeastAntibody = (element = 'lightning') => {
            if (this.supplyChain) this.supplyChain.triggerBeastCocoonMutation(this.creature, element, this.uiManager);
        };
        window.testGaaSHub = () => {
            if (this.gaasHubUI) this.gaasHubUI.toggleModal();
        };

        // 神之手抓取狀態
        this.grabbedEntity = null;
        this.lastMouseWorld = { x: 0, y: 0 };
        this.mouseVelocity = { x: 0, y: 0 };
        this.isGameOver = false;
        this.stageStartTime = 0;
        this.autoSaveTimer = 10; // 10秒自動存檔

        // 4. 初始化 UI 控制器
        this.uiManager = new UIManager({
            onStartGame: (stageId, speciesId) => this.startNewGame(stageId, speciesId),
            onBuildRequest: (buildId) => this.handleBuildRequest(buildId),
            onSelectSpell: (spellId) => {
                if (spellId && this.soundEngine) this.soundEngine.playMiracleCast();
            },
            onTogglePray: (isPraying) => this.toggleAllPrayers(isPraying),
            onChangeLeash: (mode) => {
                if (this.creatureTrainer) this.creatureTrainer.setLeashMode(mode);
            },
            onPet: () => {
                if (this.creatureTrainer) {
                    this.creatureTrainer.pet();
                    godAchievements.trackEvent('pet', 1, this.uiManager);
                }
            },
            onSlap: () => {
                if (this.creatureTrainer) {
                    this.creatureTrainer.slap();
                    godAchievements.trackEvent('slap', 1, this.uiManager);
                }
            },
            onToggleAudio: () => this.soundEngine.toggleMute(),
            onRestart: () => this.startNewGame(this.stageData ? this.stageData.id : 1, this.creature ? this.creature.species.id : 'ape'),
            onNextStage: () => {
                const nextId = this.stageData && this.stageData.id > 0 ? this.stageData.id + 1 : 1;
                this.startNewGame(nextId, this.creature ? this.creature.species.id : 'ape');
            }
        });

        this.initGodHandInput();

        // 5. 使用商業級固定物理步長迴圈 (FixedStepLoop) 替換原先單純 requestAnimationFrame
        this.loop = new FixedStepLoop({
            onFixedUpdate: (dt) => this.onFixedUpdate(dt),
            onRender: (alpha, dt) => this.onRender(alpha, dt),
            onPause: () => {
                console.log("⏸️ [Engine] 頁面切換後台，遊戲迴圈暫停。");
                if (this.soundEngine && this.soundEngine.ctx && this.soundEngine.ctx.state === 'running') {
                    this.soundEngine.ctx.suspend();
                }
            },
            onResume: () => {
                console.log("▶️ [Engine] 頁面回復前台，遊戲迴圈恢復。");
                if (this.soundEngine && this.soundEngine.ctx && this.soundEngine.ctx.state === 'suspended' && !this.soundEngine.isMuted) {
                    this.soundEngine.ctx.resume();
                }
            }
        });

        this.loop.start();
    }

    /**
     * 啟動新關卡與世界建立 (整合遙測與儲存載入)
     */
    startNewGame(stageId, speciesId) {
        this.stageData = getStageData(stageId);
        this.isSandbox = this.stageData.isSandbox;
        this.energy = this.stageData.initialEnergy;
        this.godAlignment = 0;
        this.isGameOver = false;
        this.stageStartTime = performance.now();
        this.updateGodTheme(0);

        // 記錄遙測
        analytics.trackStageStart(stageId, this.isSandbox);

        // 建立部落村莊
        this.villages = this.stageData.villages.map(v => new VillageEntity(v.id, v.name, v.x, v.y, v.owner));

        // 建立自然與可互動物理資源
        this.resources = this.stageData.resources.map(r => new ResourceEntity(r.id, r.type, r.x, r.y));

        // 建立村民 AI
        this.villagers = [];
        let vIdCount = 1;
        for (const v of this.villages) {
            for (let i = 0; i < v.population; i++) {
                const role = i === 0 ? 'priest' : (i % 2 === 0 ? 'lumberjack' : 'peasant');
                const vx = v.x + (Math.random() - 0.5) * 80;
                const vy = v.y + (Math.random() - 0.5) * 80;
                this.villagers.push(new VillagerEntity(`vg_${vIdCount++}`, v, vx, vy, role));
            }
        }

        // 建立 19 種神獸自律 AI 與管教系統
        const playerV = this.villages.find(v => v.owner === 'player') || this.villages[0];
        this.creature = new CreatureAI(speciesId, `神獸-${speciesId}`, playerV.x + 80, playerV.y + 80);
        this.creatureTrainer = new CreatureTrainer(this.creature, this.soundEngine);

        // 建立建築與部隊陣列
        this.buildings = [];
        this.troops = [];

        // 建立敵對文明神獸 (古挪威神狼、日本神虎、阿茲特克神龍)
        this.rivalCreatures = [];
        if (this.stageData.rivalFaction && this.stageData.rivalCreatureSpecies) {
            const rivalV = this.villages.find(v => v.owner === 'rival') || this.villages[this.villages.length - 1];
            if (rivalV) {
                const rc = new RivalCreature(this.stageData.rivalCreatureSpecies, this.stageData.rivalFaction, rivalV.x + 60, rivalV.y + 60, rivalV);
                this.rivalCreatures.push(rc);
                console.log(`🔥 [Stage] 敵對文明神獸【${rc.name}】已降臨領土守護！`);
            }
        }

        // 初始化關卡支線任務系統
        this.sideQuestManager = new SideQuestManager((msg, type) => this.uiManager.showNotice(msg, type));

        // 嘗試載入自動存檔 (如果存在且關卡匹配)
        const saved = gameStorage.load(`bw_stage_${stageId}_save`);
        if (saved && saved.stageId === stageId && !this.isSandbox) {
            console.log(`📥 [Storage] 發現關卡 ${stageId} 的歷史存檔，正在還原信仰與資源狀態...`);
            if (saved.energy !== undefined) this.energy = saved.energy;
            if (saved.godAlignment !== undefined) this.godAlignment = saved.godAlignment;
            if (saved.villages && saved.villages.length === this.villages.length) {
                this.villages.forEach((v, idx) => {
                    v.belief = saved.villages[idx].belief;
                    v.owner = saved.villages[idx].owner;
                    v.food = saved.villages[idx].food;
                    v.wood = saved.villages[idx].wood;
                });
            }
            if (saved.creature && this.creature) {
                this.creature.health = saved.creature.health || 100;
                this.creature.mana = saved.creature.mana || 100;
                this.creature.hunger = saved.creature.hunger || 80;
                this.creature.alignment = saved.creature.alignment || 0;
            }
        }

        // 攝影機聚焦於玩家村莊
        this.camera.panTo(playerV.x, playerV.y);
        this.soundEngine.init();
        this.uiManager.showNotice(`🌟 【${this.stageData.name}】已載入！請使用右鍵畫上手勢或左鍵抓取物件獻祭！`, 'info');

        // 新手自動教學引導 (如果是第一關)
        if (stageId === 1) {
            setTimeout(() => {
                const tutorialModal = document.getElementById('modal-tutorial');
                if (tutorialModal) tutorialModal.classList.add('active');
            }, 1000);
        }
    }

    /**
     * 神之手 (God Hand) 物理抓取、拋擲與點擊施法
     */
    initGodHandInput() {
        if (!this.canvas) return;

        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return; // 僅限左鍵
            this.soundEngine.init();

            const wPos = this.camera.screenToWorld(e.clientX, e.clientY);

            // 1. 如果已選取法術書中的神力，點擊畫面即施放！
            if (this.uiManager.selectedSpellId) {
                const spId = this.uiManager.selectedSpellId;
                const playerV = this.villages.find(v => v.owner === 'player') || { x: wPos.x, y: wPos.y };
                const success = this.miracleCaster.castMiracle(spId, playerV.x, playerV.y, wPos.x, wPos.y, true, null, this);
                if (success) {
                    godAchievements.trackEvent('cast', 1, this.uiManager);
                    analytics.trackSpellCast(spId, 'click');
                    if (this.sideQuestManager) this.sideQuestManager.onSpellCast(spId, this);
                }
                this.uiManager.selectedSpellId = null;
                this.uiManager.renderSpellCards(this.energy, this.isSandbox);
                return;
            }

            // 2. 檢查是否點中世界物件或村民以抓起 (God Hand Grab)
            const clickedEntity = this.findEntityAt(wPos.x, wPos.y);
            if (clickedEntity) {
                this.grabbedEntity = clickedEntity;
                this.grabbedEntity.grab();
                this.lastMouseWorld = { x: wPos.x, y: wPos.y };
                this.canvas.style.cursor = 'grabbing';
            }
        });

        window.addEventListener('mousemove', (e) => {
            if (!this.grabbedEntity) {
                this.updateHandTooltip(e.clientX, e.clientY);
                return;
            }
            
            // 抓取時隱藏 tooltip
            this.hideHandTooltip();

            const wPos = this.camera.screenToWorld(e.clientX, e.clientY);
            this.mouseVelocity = {
                x: (wPos.x - this.lastMouseWorld.x) * 15,
                y: (wPos.y - this.lastMouseWorld.y) * 15
            };
            this.grabbedEntity.x = wPos.x;
            this.grabbedEntity.y = wPos.y;
            this.lastMouseWorld = { x: wPos.x, y: wPos.y };
        });

        window.addEventListener('mouseup', (e) => {
            if (e.button === 0 && this.grabbedEntity) {
                const isOverSacrificeZone = this.checkSacrificeZone(e.clientX, e.clientY, this.grabbedEntity);
                if (isOverSacrificeZone) {
                    this.sacrificeEntity(this.grabbedEntity);
                } else {
                    this.grabbedEntity.release(this.mouseVelocity.x, this.mouseVelocity.y);
                }
                this.grabbedEntity = null;
                this.canvas.style.cursor = 'default';
            }
        });
    }

    findEntityAt(wx, wy) {
        for (const vg of this.villagers) {
            if (!vg.isDead && Math.hypot(vg.x - wx, vg.y - wy) < 25) return vg;
        }
        for (const res of this.resources) {
            if (!res.isDestroyed && Math.hypot(res.x - wx, res.y - wy) < res.size) return res;
        }
        return null;
    }

    updateHandTooltip(clientX, clientY) {
        if (!this.camera) return;
        const wPos = this.camera.screenToWorld(clientX, clientY);
        const entity = this.findEntityAt(wPos.x, wPos.y);
        const tooltip = document.getElementById('hand-tooltip');
        
        // 檢查是否在祭壇區域上方
        const isOverSacrifice = this.checkSacrificeZone(clientX, clientY, {x: wPos.x, y: wPos.y});
        
        if (tooltip) {
            if (entity) {
                let title = entity.type === 'tree' ? '樹木' : (entity.type === 'crop' ? '農作物' : (entity.type === 'rock' ? '岩石' : '動物'));
                let desc = `左鍵拖拽抓取 / 投入左側祭壇換取能量`;
                if (entity instanceof VillagerEntity) {
                    title = `村民 (${entity.role === 'priest' ? '祭司' : '平民'})`;
                    desc = `左鍵拖拽抓取 / 投入祭壇將殘忍獻祭並增加邪惡度`;
                }
                
                document.getElementById('tooltip-title').textContent = title;
                document.getElementById('tooltip-desc').textContent = desc;
                tooltip.style.left = `${clientX + 15}px`;
                tooltip.style.top = `${clientY + 15}px`;
                tooltip.classList.remove('hidden');
            } else if (isOverSacrifice) {
                document.getElementById('tooltip-title').textContent = '🔥 祭壇火焰區';
                document.getElementById('tooltip-desc').textContent = '可將抓取的物件丟入此處換取大量能量';
                tooltip.style.left = `${clientX + 15}px`;
                tooltip.style.top = `${clientY + 15}px`;
                tooltip.classList.remove('hidden');
            } else {
                tooltip.classList.add('hidden');
            }
        }
    }

    hideHandTooltip() {
        const tooltip = document.getElementById('hand-tooltip');
        if (tooltip) tooltip.classList.add('hidden');
    }

    checkSacrificeZone(screenX, screenY, entity) {
        const sz = document.getElementById('sacrifice-zone');
        if (sz) {
            const rect = sz.getBoundingClientRect();
            if (screenX >= rect.left && screenX <= rect.right && screenY >= rect.top && screenY <= rect.bottom) {
                return true;
            }
        }
        const playerV = this.villages.find(v => v.owner === 'player');
        if (playerV && Math.hypot(entity.x - playerV.x, entity.y - playerV.y) < 60) {
            return true;
        }
        return false;
    }

    /**
     * 執行祭壇獻祭 (Sacrifice System with Telemetry & Quests)
     */
    sacrificeEntity(entity) {
        this.soundEngine.playSacrifice(entity.x, this.camera?.x);
        const val = entity.sacrificeValue || 50;
        const maxE = 2000 + godProgression.getBonus('max_energy');
        this.energy = Math.min(maxE, this.energy + val);

        this.particleEngine.emitSoul(entity.x, entity.y);
        godAchievements.trackEvent('sacrifice', 1, this.uiManager);
        analytics.trackSacrifice(entity.type || 'entity', val);
        if (this.sideQuestManager) this.sideQuestManager.onSacrifice(entity.type || 'entity', this);
        
        if (entity instanceof VillagerEntity) {
            entity.isDead = true;
            this.godAlignment = Math.max(-100, this.godAlignment - 20);
            this.updateGodTheme(this.godAlignment);
            this.uiManager.showNotice(`🔥 獻祭了活人村民！獲得 +${val} 能量 (殘忍邪惡度 +20)`, 'error');
            this.camera.shake(10, 0.4);
        } else {
            entity.isDestroyed = true;
            this.uiManager.showNotice(`🔥 獻祭了${entity.symbol}！獲得 +${val} 祭壇能量！`, 'info');
        }

        this.saveStageProgress();
    }

    /**
     * 處理手勢識別施法
     */
    handleGestureRecognized(symbolName, wx, wy) {
        const symbolMap = { 'circle': '〇', 'lightning': 'Z', 'triangle': '△', 'heart': '♡', 'spiral': 'S', 'square': '□' };
        const symbolChar = symbolMap[symbolName];
        if (!symbolChar) return;

        const matchingSpells = getMiraclesByGestureSymbol(symbolChar);
        if (matchingSpells.length > 0) {
            const spell = matchingSpells[0];
            const playerV = this.villages.find(v => v.owner === 'player') || { x: wx, y: wy };
            const success = this.miracleCaster.castMiracle(spell.id, playerV.x, playerV.y, wx, wy, true, null, this);
            if (success) {
                godAchievements.trackEvent('cast', 1, this.uiManager);
                analytics.trackSpellCast(spell.id, symbolChar);
                if (this.sideQuestManager) this.sideQuestManager.onSpellCast(spell.id, this);
                this.uiManager.showNotice(`✨ 透過手勢【${symbolChar}】成功施放了【${spell.name}】！`, 'info');
            }
        }
    }

    toggleAllPrayers(isPraying) {
        const playerV = this.villages.find(v => v.owner === 'player');
        if (playerV) playerV.isPrayingMode = isPraying;
        for (const vg of this.villagers) {
            if (vg.village && vg.village.owner === 'player') {
                if (isPraying) {
                    vg.state = 'praying';
                } else if (vg.role !== 'priest') {
                    vg.state = 'idle';
                }
            }
        }
    }

    /**
     * 處理玩家建構奇觀與軍事基地請求 (SimCity vs AoE)
     */
    handleBuildRequest(buildId) {
        const def = BUILDING_DATABASE[buildId];
        if (!def) return { success: false, msg: '不明的建築選項' };
        
        const playerV = this.villages.find(v => v.owner === 'player') || this.villages[0];
        if (!playerV) return { success: false, msg: '沒有可依附的村莊領土' };
        
        if (!this.isSandbox && (playerV.wood < def.costWood || this.energy < def.costEnergy)) {
            return { success: false, msg: `資源或能量不足！需要 🪵 ${def.costWood} 木材與 ⚡ ${def.costEnergy} 能量` };
        }
        
        if (!this.isSandbox) {
            playerV.wood -= def.costWood;
            this.energy -= def.costEnergy;
        }
        
        const bx = playerV.x + (Math.random() - 0.5) * 120;
        const by = playerV.y + 50 + (Math.random() - 0.5) * 60;
        const newBuilding = new BuildingEntity(`build_${Date.now()}`, buildId, bx, by, 'player', playerV);
        this.buildings.push(newBuilding);
        
        if (this.particleEngine) this.particleEngine.emitHeal(bx, by, 100, 2);
        if (this.soundEngine) this.soundEngine.playHeal(bx);
        if (this.sideQuestManager) this.sideQuestManager.checkResourceQuest(playerV, this);
        
        return { success: true, msg: `開始在【${playerV.name}】周圍興建【${def.name}】！約3秒完工！` };
    }

    updateGodTheme(alignment) {
        document.documentElement.setAttribute('data-theme', alignment <= -30 ? 'evil' : 'good');
    }

    /**
     * 啟動千人戰場壓測與演習 (可在瀏覽器主控台呼叫 window.startBattleTest(1000))
     */
    startBattleTest(count = 1000) {
        console.log(`⚔️ [Battle Test] 啟動千人同屏戰場壓測，規模: ${count} 獨立單位...`);
        this.ecsBattle.clear();
        const half = Math.floor(count / 2);
        const center = this.villages[0] || { x: 1000, y: 1000 };
        
        // 玩家老兵方陣 (左側)
        for (let i = 0; i < half; i++) {
            const x = center.x - 350 + (Math.random() - 0.5) * 300;
            const y = center.y + (Math.random() - 0.5) * 500;
            const vetLvl = Math.random() < 0.35 ? Math.floor(Math.random() * 4) + 1 : 0;
            this.ecsBattle.spawnUnit(x, y, 0, i % 3, vetLvl);
        }
        
        // 敵國部隊 (右側)
        for (let i = 0; i < half; i++) {
            const x = center.x + 350 + (Math.random() - 0.5) * 300;
            const y = center.y + (Math.random() - 0.5) * 500;
            const vetLvl = Math.random() < 0.2 ? Math.floor(Math.random() * 3) : 0;
            this.ecsBattle.spawnUnit(x, y, 1 + (i % 3), i % 3, vetLvl);
        }
        
        if (this.uiManager) {
            this.uiManager.showNotice(`⚔️ 史詩戰役爆發！共計 ${count} 獨立單位加入戰場！`, 'warning');
        }
        
        // 啟動流場導航，雙方向中心推進
        this.flowField.requestFlowFieldUpdate(center.x, center.y);
    }

    spawnForest(x, y, count) {
        for (let i = 0; i < count; i++) {
            const rx = x + (Math.random() - 0.5) * 150;
            const ry = y + (Math.random() - 0.5) * 150;
            this.resources.push(new ResourceEntity(`tree_${Date.now()}_${i}`, 'tree', rx, ry));
        }
    }

    triggerFlash() {
        const flash = document.getElementById('screen-flash');
        if (flash) {
            flash.style.opacity = '0.6';
            setTimeout(() => flash.style.opacity = '0', 200);
        }
    }

    /**
     * 自動儲存關卡進度防篡改
     */
    saveStageProgress() {
        if (!this.stageData || this.isSandbox || this.isGameOver) return;
        const saveData = {
            stageId: this.stageData.id,
            energy: this.energy,
            godAlignment: this.godAlignment,
            morality: this.morality ? { alignment: this.morality.alignment, prosperity: this.morality.prosperity, dread: this.morality.dread } : null,
            villages: this.villages.map(v => ({ belief: v.belief, owner: v.owner, food: v.food, wood: v.wood })),
            creature: this.creature ? { health: this.creature.health, mana: this.creature.mana, hunger: this.creature.hunger, alignment: this.creature.alignment } : null
        };
        gameStorage.save(`bw_stage_${this.stageData.id}_save`, saveData);
    }

    /**
     * 固定步長物理與狀態更新 (Fixed Step Physics Update)
     */
    onFixedUpdate(dt) {
        if (this.isGameOver || !this.stageData) return;

        // 1. 更新攝影機與特效
        this.camera.update(dt);
        this.particleEngine.update(dt);

        // 2. 更新村莊與村民 (結合天賦祭壇產能加成與最大能量加成、Phase 7 文明演化與 Phase 8 通勤 Buff)
        if (this.gaas) this.gaas.update(dt);
        const commuteMult = (this.gaas && this.gaas.commuteBuffActive) ? 1.3 : 1.0;
        const effMult = godProgression.getBonus('altar_efficiency') * (this.morality ? this.morality.civEfficiencyMult : 1.0) * commuteMult;
        const maxE = 2000 + godProgression.getBonus('max_energy');

        for (const v of this.villages) {
            v.update(dt, this.villages, this.villagers, this.troops, this.particleEngine, this.soundEngine, (msg, type) => this.uiManager.showNotice(msg, type));
            const generated = v.generateEnergyFromPrayer(dt) * effMult;
            if (generated > 0 && !this.isSandbox) {
                this.energy = Math.min(maxE, this.energy + generated);
            }
        }
        for (const vg of this.villagers) {
            vg.update(dt, this.resources, this.villages[0] ? { x: this.villages[0].x, y: this.villages[0].y } : null, this.soundEngine);
        }
        for (const b of this.buildings) {
            b.update(dt, this.villages, this.particleEngine, this.soundEngine);
        }
        for (const t of this.troops) {
            t.update(dt, this.villages, this.villagers, this.rivalCreatures, this.creature, this.particleEngine, this.soundEngine);
        }
        for (const rc of this.rivalCreatures) {
            rc.update(dt, this.villages, this.villagers, this.creature, this.particleEngine, this.miracleCaster, this.soundEngine);
        }
        if (this.sideQuestManager) {
            this.sideQuestManager.update(dt, this);
        }

        // 3. 更新物理資源與動物
        for (const res of this.resources) {
            res.update(dt);
        }

        // 4. 更新神獸與管教狀態
        if (this.creature && this.creatureTrainer) {
            this.creatureTrainer.update(dt);
            this.creature.update(dt, this.resources, this.villages, this.particleEngine, this.miracleCaster, this.soundEngine, this.rivalCreatures, this.troops, this.buildings);
        }

        // 4.5 更新 ECS 戰場方陣與流場導航
        if (this.ecsBattle && this.ecsBattle.activeCount > 0) {
            this.flowField.tick(dt);
            this.ecsBattle.updateMovementSystem(dt, this.flowField.flowX, this.flowField.flowY, this.flowField.gridCols, this.flowField.cellSize);
            this.ecsBattle.updateCombatSystem(dt);
        }

        // 4.6 更新文化同化管線與老兵世代演進 (Phase 3 & Phase 4)
        if (this.morality) {
            this.morality.updateAssimilation(this.villages, dt, this.particleEngine, this.uiManager);
        }
        if (this.veteranEvolution) {
            this.veteranEvolution.update(dt);
        }

        // 4.7 更新物化信仰供應鏈與危機預警雷達 (Phase 6 商業化升級)
        if (this.supplyChain) {
            this.energy = this.supplyChain.update(dt, this.energy, this.villages, this.uiManager);
        }
        if (this.prewarningRadar) {
            this.prewarningRadar.update(dt, this.supplyChain, this.morality, this.villages, this.creature, this.uiManager);
        }

        // 5. 檢查勝負條件
        this.checkStageObjectives();

        // 6. 處理自動存檔計時器
        this.autoSaveTimer -= dt;
        if (this.autoSaveTimer <= 0) {
            this.saveStageProgress();
            this.autoSaveTimer = 10;
        }
    }

    /**
     * 視覺渲染迴圈與 UI 同步 (Visual Render)
     */
    onRender(alpha, dt) {
        if (!this.stageData) return;
        this.canvasRenderer.render(dt, [...this.villages, ...this.resources, ...this.villagers, ...this.buildings, ...this.troops, ...this.rivalCreatures], this.villages, this.creature, this.particleEngine, this.godAlignment);
        
        // 渲染 ECS 戰場方陣與 LOD 降頻優化
        if (this.ecsBattle && this.ecsBattle.activeCount > 0 && this.canvasRenderer.ctx) {
            this.canvasRenderer.camera.apply(this.canvasRenderer.ctx);
            this.lodRenderer.prepareInstanceBufferAndLOD(this.ecsBattle, this.canvasRenderer.camera);
            this.lodRenderer.renderCanvas2DBatch(this.canvasRenderer.ctx, this.canvasRenderer.time);
            this.canvasRenderer.camera.restore(this.canvasRenderer.ctx);
        }

        this.uiManager.updateHUD(this);
    }

    checkStageObjectives() {
        if (this.isSandbox || !this.villages.length || this.isGameOver) return;

        const playerControlled = this.villages.filter(v => v.owner === 'player').length;
        const total = this.villages.length;
        const duration = Math.floor((performance.now() - this.stageStartTime) / 1000);

        // 勝利：統治全島村莊
        if (playerControlled >= total && total > 0) {
            this.isGameOver = true;
            this.soundEngine.playHeal();
            const godTitle = this.godAlignment >= 20 ? '神聖慈悲救世主' : (this.godAlignment <= -20 ? '無情毀滅破壞神' : '威嚴中立之神');
            const cStatus = `${this.creature.species.symbol} ${this.creature.name} (${this.creature.alignment >= 0 ? '良善守護神獸' : '毀滅巨獸'})`;
            
            godAchievements.trackEvent('win', 1, this.uiManager);
            analytics.trackStageEnd(this.stageData.id, true, duration, this.energy, this.godAlignment);
            gameStorage.remove(`bw_stage_${this.stageData.id}_save`); // 勝利後清除關卡中繼存檔

            this.uiManager.showGameOver(true, godTitle, cStatus);
        }
        // 失敗：所有信徒與村莊失陷且毫無能量
        else if (playerControlled === 0 && this.energy < 50) {
            this.isGameOver = true;
            analytics.trackStageEnd(this.stageData.id, false, duration, this.energy, this.godAlignment);
            gameStorage.remove(`bw_stage_${this.stageData.id}_save`);

            this.uiManager.showGameOver(false, '殞落之神', '迷失的神獸');
        }
    }
}

// 當 DOM 準備完成時啟動遊戲主引擎
window.addEventListener('DOMContentLoaded', () => {
    window.gameInstance = new GameMain();
    console.log("🚀 [Black & White Engine 2026] 商業版神蹟島嶼核心引擎初始化完成。");
});
