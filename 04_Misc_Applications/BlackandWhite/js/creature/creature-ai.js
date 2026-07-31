import { getSpeciesById } from './creature-data.js?v=3';
import { godProgression } from '../meta/progression.js?v=3';
import { creatureSkins } from '../meta/creature-skins.js?v=3';
import { AgentMemory } from '../engine/agent-memory.js?v=3';
import { aiAgentBridge } from '../engine/ai-agent-bridge.js?v=3';

/**
 * 神獸自律 AI 決策樹與狀態管理 (Creature AI & Behavior Tree)
 * 處理神獸飢餓、情緒、學習神力模仿、協助村莊或破壞部落行為
 */
export class CreatureAI {
    constructor(speciesId, name = '神獸', x = 1000, y = 1050) {
        this.species = getSpeciesById(speciesId);
        this.name = name;
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.z = 0;

        // 核心狀態數值 (0 ~ 100)
        this.health = 100;
        this.hunger = 80;
        this.mana = 100;
        this.alignment = 0; // -100 (極惡/破壞) ~ +100 (極善/慈悲)
        this.scale = 1.0;   // 體型縮放比率

        // AI 狀態與思維
        this.state = 'wandering'; // 'wandering', 'eating', 'helping', 'destroying', 'casting', 'sleeping'
        this.thought = '「我想熟悉這座島嶼的環境...」';
        this.targetEntity = null;
        this.leashMode = 'village'; // 'village' (守護主村), 'roam' (自由), 'enemy' (進攻敵村)
        this.tetherPoint = { x: x, y: y };
        this.tetherRadius = 350;

        // 已掌握與正在學習的神力
        this.learnedSpells = ['water', 'food']; // 初始預設學會灑水與造食
        this.spellLearningProgress = {}; // { 'fireball_1': 50, ... }

        // 行為傾向記憶 (經由撫摸/掌摑訓練強化或減弱)
        this.tendencies = {
            help_villagers: 50, // 協助勞動與治療
            eat_animals: 60,    // 捕獵動物進食
            eat_villagers: 10,  // 吃掉人類
            destroy_houses: 20  // 破壞房屋建築
        };

        this.decisionTimer = 2;
        this.castCooldown = 0;
        this.currentActionType = null; // 當前正在進行的行為類型 (用於撫摸/掌摑對應獎懲)

        // Phase 5 自主 AI 代理人：多模態感官記憶庫與推論狀態
        this.agentMemory = new AgentMemory(`${this.species.name} (${this.name})`);
        this.isWaitingForLLM = false;
        this.spokenDialogue = null; // 最新產生的自然語言對話
        this.currentMood = "NORMAL";
    }

    /**
     * 觀察上帝施法並累積學習進度！
     */
    observeMiracle(spellId, spellName) {
        if (this.learnedSpells.includes(spellId)) {
            this.thought = `「主人施展了${spellName}！我已經學會這招了！」`;
            return;
        }

        if (!this.spellLearningProgress[spellId]) {
            this.spellLearningProgress[spellId] = 0;
        }

        // 根據物種智力傾向與御獸系天賦加成增加學習度
        const learnBoost = 25 * (this.species.mana / 70) * godProgression.getBonus('learning_rate');
        this.spellLearningProgress[spellId] += learnBoost;
        
        if (this.spellLearningProgress[spellId] >= 100) {
            this.learnedSpells.push(spellId);
            this.thought = `「💡 領悟了！我學會了如何施展【${spellName}】法術！」`;
            delete this.spellLearningProgress[spellId];
        } else {
            this.thought = `「我在認真觀察主人施展【${spellName}】...(學習進度: ${Math.floor(this.spellLearningProgress[spellId])}%)」`;
        }
        if (this.agentMemory) {
            this.agentMemory.addSensoryEvent('MIRACLE_OBSERVED', `我看見主人施展了【${spellName}】，這震撼了我的感官！`, +10);
        }
    }

    /**
     * 接收撫摸獎勵 (Praise / Reward)
     */
    receivePet(soundEngine) {
        if (soundEngine) soundEngine.playPet();
        if (this.currentActionType) {
            this.tendencies[this.currentActionType] = Math.min(100, (this.tendencies[this.currentActionType] || 50) + 25);
            if (this.currentActionType === 'help_villagers') {
                this.alignment = Math.min(100, this.alignment + 15);
                this.thought = '「💖 主人摸我了！他喜歡我幫助村民！我會繼續做良善的事！」';
            } else if (this.currentActionType === 'destroy_houses' || this.currentActionType === 'eat_villagers') {
                this.alignment = Math.max(-100, this.alignment - 20);
                this.thought = '「😈 主人鼓勵我的破壞行為！我將成為無情的毀滅巨獸！」';
            } else {
                this.thought = '「好舒服的撫摸！主人的愛讓我充滿力量！」';
            }
        } else {
            this.alignment = Math.min(100, this.alignment + 5);
            this.thought = '「💖 謝謝主人的疼愛！」';
        }
        if (this.agentMemory) {
            this.agentMemory.addSensoryEvent('PET_REWARD', '主人溫柔地撫摸了我的頭與背脊，我感到被珍視與溫暖！', +25);
        }
    }

    /**
     * 接收掌摑懲罰 (Slap / Punish)
     */
    receiveSlap(soundEngine) {
        if (soundEngine) soundEngine.playSlap();
        if (soundEngine) soundEngine.playCreatureRoar(this.species.pitch * 1.3); // 委屈吼叫

        if (this.currentActionType) {
            this.tendencies[this.currentActionType] = Math.max(0, (this.tendencies[this.currentActionType] || 50) - 30);
            if (this.currentActionType === 'destroy_houses' || this.currentActionType === 'eat_villagers') {
                this.thought = '「💥 痛！主人不准我破壞和吃人...我再也不敢了...」';
                this.alignment = Math.min(100, this.alignment + 10); // 改邪歸正
            } else if (this.currentActionType === 'help_villagers') {
                this.thought = '「嗚嗚...為什麼幫助他們會挨打？那我以後不幫了...」';
                this.alignment = Math.max(-100, this.alignment - 15);
            }
        } else {
            this.thought = '「💥 為什麼打我...我會變得憤怒與恐懼的！」';
            this.alignment = Math.max(-100, this.alignment - 10);
        }
        this.state = 'wandering';
        this.targetEntity = null;
        this.currentActionType = null;
        if (this.agentMemory) {
            this.agentMemory.addSensoryEvent('SLAP_PUNISHMENT', '主人重重地賞了我一巴掌！我很痛、很恐懼也很憤怒！', -30);
        }
    }

    update(dt, worldResources, villages, particleEngine, miracleCaster, soundEngine, rivalCreatures = null, troops = null, buildings = null) {
        // 數值自然變化
        this.hunger = Math.max(0, this.hunger - dt * 0.4);
        const skinStats = creatureSkins ? creatureSkins.getEquippedStats() : { maxHp: 0, maxMana: 0, speedMult: 1.0 };
        const maxHpVal = 100 * godProgression.getBonus('beast_stats') + (skinStats.maxHp || 0);
        const maxManaVal = 100 * godProgression.getBonus('beast_stats') + (skinStats.maxMana || 0);
        this.mana = Math.min(maxManaVal, this.mana + dt * 1.5);
        if (this.castCooldown > 0) this.castCooldown -= dt;

        // 🌟 檢測是否遭遇敵方文明神獸，引發【巨獸對決】(Titan Combat)！
        if (rivalCreatures && rivalCreatures.length > 0) {
            for (const rc of rivalCreatures) {
                if (!rc.isDead && Math.hypot(rc.x - this.x, rc.y - this.y) <= 180) {
                    this.state = 'titan_combat';
                    this.targetEntity = rc;
                    this.thought = `「🔥 遭遇敵方文明巨獸【${rc.name}】！展開史詩決鬥！」`;
                    break;
                }
            }
        }

        // 根據牽繩設定限制範圍與中心
        let center = this.tetherPoint;
        if (this.leashMode === 'village') {
            const playerV = villages.find(v => v.owner === 'player');
            if (playerV) { center = { x: playerV.x, y: playerV.y }; this.tetherPoint = center; }
        } else if (this.leashMode === 'enemy') {
            const enemyV = villages.find(v => v.owner !== 'player');
            if (enemyV) { center = { x: enemyV.x, y: enemyV.y }; this.tetherPoint = center; }
        }

        // 決策樹更新
        this.decisionTimer -= dt;
        if (this.decisionTimer <= 0) {
            this.decisionTimer = 2 + Math.random() * 2;
            this.makeDecision(worldResources, villages, center, miracleCaster, soundEngine);
        }

        // 執行移動與動作
        if (this.targetEntity && !this.targetEntity.isDestroyed && !this.targetEntity.isDead) {
            const dx = this.targetEntity.x - this.x;
            const dy = this.targetEntity.y - this.y;
            const dist = Math.hypot(dx, dy);
            
            if (dist > 40) {
                const skinSpd = creatureSkins ? creatureSkins.getEquippedStats().speedMult : 1.0;
                const spd = this.species.spd * 0.8 * (this.scale > 1.5 ? 0.7 : 1.0) * skinSpd;
                this.vx = (dx / dist) * spd;
                this.vy = (dy / dist) * spd;
                this.x += this.vx * dt;
                this.y += this.vy * dt;
            } else {
                // 到達目標執行互動
                this.executeInteraction(particleEngine, miracleCaster, soundEngine, dt);
            }
        } else {
            // 隨機漫步 (保持在牽繩範圍內)
            if (this.state === 'wandering' && Math.random() < 0.3) {
                const angle = Math.random() * Math.PI * 2;
                const dist = Math.random() * (this.leashMode === 'roam' ? 600 : this.tetherRadius * 0.7);
                this.targetEntity = { x: center.x + Math.cos(angle)*dist, y: center.y + Math.sin(angle)*dist, isPoint: true };
            }
        }
    }

    /**
     * 自律決策核心邏輯 (支持 Phase 5 自主 AI 代理人 LLM 雙驅動)
     */
    makeDecision(resources, villages, center, miracleCaster, soundEngine) {
        // 啟動非同步自主 AI 代理人推論 (不阻塞物理步長迴圈)
        if (!this.isWaitingForLLM && this.agentMemory) {
            this.isWaitingForLLM = true;
            const currentState = {
                health: this.health,
                hunger: this.hunger,
                mana: this.mana,
                alignment: this.alignment,
                leashMode: this.leashMode
            };

            aiAgentBridge.decideAction(this.species.name, this.agentMemory.getPromptContext(), currentState)
                .then((decision) => {
                    this.isWaitingForLLM = false;
                    if (!decision) return;

                    this.thought = decision.internal_thought || this.thought;
                    this.spokenDialogue = decision.spoken_dialogue || null;
                    if (decision.emotional_shift) {
                        this.alignment = Math.max(-100, Math.min(100, this.alignment + (decision.emotional_shift.morality_alignment || 0)));
                        this.currentMood = decision.emotional_shift.current_mood || this.currentMood;
                    }

                    const act = decision.concrete_action;
                    if (!act) return;

                    if (act.action_type === 'REBEL_AGAINST_GOD') {
                        this.state = 'destroying';
                        this.leashMode = 'roam';
                        this.thought = '「⚠️ 我要掙脫牽繩！為自由反抗！」';
                        if (soundEngine) soundEngine.playCreatureRoar(this.species.pitch * 0.7);
                    } else if (act.action_type === 'CAST_MIRACLE' && act.spell_id && miracleCaster) {
                        const targetX = act.target_coordinates?.x || center.x;
                        const targetY = act.target_coordinates?.y || center.y;
                        if (this.mana >= 20) {
                            miracleCaster.castMiracle(act.spell_id, this.x, this.y, targetX, targetY, false, this);
                            this.mana -= 20;
                            this.castCooldown = 8;
                        }
                    } else if (act.action_type === 'EAT_FOOD') {
                        this.state = 'eating';
                        this.targetEntity = this.findNearest(resources, 'animal_') || this.findNearest(resources, 'crop');
                    }
                })
                .catch(() => { this.isWaitingForLLM = false; });
        }

        // 1. 飢餓優先：去吃獵物或農作物
        if (this.hunger < 40) {
            this.state = 'eating';
            // 根據性格傾向選擇進食動物、作物或村民！
            if (this.alignment < -20 && this.tendencies.eat_villagers > 30 && Math.random() < 0.3) {
                this.thought = '「我肚子好餓...想吃個鮮甜的村民！」';
                this.currentActionType = 'eat_villagers';
                // 尋找敵對或中立村民
            } else {
                this.thought = '「肚子好餓...尋找羊隻或作物進食中...」';
                this.currentActionType = 'eat_animals';
                this.targetEntity = this.findNearest(resources, 'animal_');
                if (!this.targetEntity) this.targetEntity = this.findNearest(resources, 'crop');
            }
            return;
        }

        // 2. 協助主村或進攻敵村
        if (this.leashMode === 'village' && this.tendencies.help_villagers > 30) {
            this.state = 'helping';
            this.currentActionType = 'help_villagers';
            
            // 嘗試自動施展神力幫助 (如造食或灑水)
            if (this.mana >= 30 && this.castCooldown <= 0 && Math.random() < 0.5) {
                if (this.learnedSpells.includes('water')) {
                    this.thought = '「我想幫主人的稻田灑灑水雨...」';
                    if (miracleCaster) miracleCaster.castMiracle('water_1', this.x, this.y, center.x, center.y, false, this);
                    this.mana -= 20;
                    this.castCooldown = 8;
                    return;
                } else if (this.learnedSpells.includes('heal')) {
                    this.thought = '「施展神聖光芒治療大家！」';
                    if (miracleCaster) miracleCaster.castMiracle('heal_1', this.x, this.y, center.x, center.y, false, this);
                    this.mana -= 25;
                    this.castCooldown = 10;
                    return;
                }
            }

            this.thought = '「我在巡視並協助主人的村莊...」';
            this.targetEntity = this.findNearest(resources, 'tree');
            return;
        } 
        else if (this.leashMode === 'enemy' || (this.alignment < -30 && this.tendencies.destroy_houses > 40)) {
            this.state = 'destroying';
            this.currentActionType = 'destroy_houses';
            this.thought = '「吼！我要摧毀這些異教徒的房屋，展示主人的恐懼與神威！」';
            if (soundEngine && Math.random() < 0.3) soundEngine.playCreatureRoar(this.species.pitch);

            // 如果學會火球或雷電，主動對敵村轟炸！
            if (this.mana >= 40 && this.castCooldown <= 0) {
                const enemyV = villages.find(v => v.owner !== 'player');
                if (enemyV) {
                    if (this.learnedSpells.includes('fireball_1')) {
                        this.thought = '「對準敵人的村莊吐出烈焰火球！」';
                        if (miracleCaster) miracleCaster.castMiracle('fireball_1', this.x, this.y, enemyV.x, enemyV.y, false, this);
                        this.mana -= 30;
                        this.castCooldown = 6;
                        return;
                    } else if (this.learnedSpells.includes('lightning_1')) {
                        this.thought = '「召喚落雷劈下敵方祭壇！」';
                        if (miracleCaster) miracleCaster.castMiracle('lightning_1', this.x, this.y, enemyV.x, enemyV.y, false, this);
                        this.mana -= 35;
                        this.castCooldown = 8;
                        return;
                    }
                }
            }

            const enemyV = villages.find(v => v.owner !== 'player');
            if (enemyV) {
                this.targetEntity = { x: enemyV.x, y: enemyV.y, isVillage: true, ref: enemyV };
            }
            return;
        }

        // 3. 預設閒逛
        this.state = 'wandering';
        this.currentActionType = null;
        this.thought = `「身為【${this.species.name}】，正在島上自由漫步，觀察一切...」`;
    }

    executeInteraction(particleEngine, miracleCaster, soundEngine, dt) {
        if (!this.targetEntity) return;

        if (this.state === 'eating' && !this.targetEntity.isPoint) {
            // 吃掉目標
            this.targetEntity.takeDamage(100, particleEngine);
            this.hunger = Math.min(100, this.hunger + 40);
            this.thought = `「😋 美味！吃掉了${this.targetEntity.symbol || '食物'}，飽食度恢復了！」`;
            this.targetEntity = null;
            this.state = 'wandering';
        } else if (this.state === 'destroying' && this.targetEntity.isVillage) {
            // 攻擊敵對村莊
            if (this.targetEntity.ref) {
                this.targetEntity.ref.takeDamage(40 * dt, particleEngine);
                this.targetEntity.ref.addBelief(-2 * dt, false); // 造成恐懼與降服
            }
            if (Math.random() < 0.05 && particleEngine) {
                particleEngine.emitExplosion(this.x, this.y, 60);
            }
        } else if (this.state === 'titan_combat' && this.targetEntity && !this.targetEntity.isPoint) {
            // 🌟 巨獸對決互毆
            if (soundEngine && Math.random() < 0.25) {
                soundEngine.playCreatureRoar(this.species.pitch, this.x);
                soundEngine.playSlap(this.x);
            }
            if (particleEngine && Math.random() < 0.3) {
                particleEngine.emitExplosion((this.x+this.targetEntity.x)/2, (this.y+this.targetEntity.y)/2, 150);
            }
            if (this.targetEntity.takeDamage) {
                this.targetEntity.takeDamage(22 * (this.scale || 1) * dt, particleEngine);
            }
            if (this.targetEntity.isDead) {
                this.state = 'wandering';
                this.targetEntity = null;
                this.thought = '「吼！我成功擊敗了敵對神獸！守護了主人的島嶼！」';
            }
        } else if (this.targetEntity.isPoint) {
            const dx = this.targetEntity.x - this.x;
            const dy = this.targetEntity.y - this.y;
            if (Math.hypot(dx, dy) < 20) {
                this.targetEntity = null;
            }
        }
    }

    findNearest(list, prefix) {
        if (!list) return null;
        let nearest = null, minD = Infinity;
        for (const item of list) {
            if (!item.isDestroyed && item.type && item.type.startsWith(prefix)) {
                const d = Math.hypot(item.x - this.x, item.y - this.y);
                if (d < minD) { minD = d; nearest = item; }
            }
        }
        return nearest;
    }

    render(ctx, time) {
        ctx.save();
        const renderX = this.x;
        const renderY = this.y - this.z;
        const size = 52 * this.scale;

        // 1. 神獸地面光環與陰影 (根據善惡發出金光或紅光)
        const shadowR = (size * 0.6) * Math.max(0.4, 1 - this.z / 150);
        ctx.beginPath();
        ctx.ellipse(this.x, this.y, shadowR, shadowR * 0.5, 0, 0, Math.PI * 2);
        ctx.fillStyle = this.alignment >= 0 ? 'rgba(251, 191, 36, 0.25)' : 'rgba(239, 68, 68, 0.35)';
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = this.alignment >= 0 ? '#fbbf24' : '#ef4444';
        ctx.stroke();

        // 2. 繪製神獸表情/物種符號 (若處於巨大化或特定狀態會變色)
        ctx.font = `${size}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // 輕微呼吸跳動動畫
        const bounce = Math.sin(time * 3) * 4;
        ctx.fillText(this.species.symbol, renderX, renderY + bounce);

        // 3. 繪製頭上名稱與傾向標示
        ctx.font = 'bold 12px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 4;
        ctx.fillText(`${this.name} (${this.alignment >= 0 ? '😇善' : '😈惡'})`, renderX, renderY - size * 0.6 + bounce);

        // 4. 狀態小圖標 (飢餓肉骨頭 / 攻擊火花 / 治療愛心)
        if (this.hunger < 30) {
            ctx.font = '16px sans-serif';
            ctx.fillText('🍖!', renderX + size * 0.5, renderY - size * 0.4 + bounce);
        } else if (this.state === 'destroying') {
            ctx.font = '16px sans-serif';
            ctx.fillText('💥', renderX + size * 0.5, renderY - size * 0.4 + bounce);
        } else if (this.state === 'helping') {
            ctx.font = '16px sans-serif';
            ctx.fillText('💖', renderX + size * 0.5, renderY - size * 0.4 + bounce);
        } else if (this.state === 'titan_combat') {
            ctx.font = '16px sans-serif';
            ctx.fillText('⚡格鬥中!', renderX, renderY + size * 0.5 + bounce);
        }

        ctx.restore();
    }
}
