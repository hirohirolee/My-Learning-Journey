/**
 * ============================================================================
 * 模組：中後期三階段物化信仰供應鏈與物流神殿 (SupplyChainManager)
 * 參照 Anno 1800 的經濟轉化與 RTS 戰爭連動機制
 * 實作虛擬管線電導率自動化運算 (Conductance Network)，免除馬車物流微操
 * 當高階合金庫存過高時，發出財富熱度引力誘發敵國「反神同盟」侵略衝鋒！
 * ============================================================================
 */

export class SupplyChainManager {
    constructor() {
        // 三階段資源庫存池
        this.inventory = {
            // Tier 1: 基礎開墾
            wood: 500,
            planks: 200,
            wheat: 500,
            bread: 200,
            // Tier 2: 工業與神秘轉化 (分水嶺)
            iron: 300,
            obsidian_steel: 0,
            sacred_wine: 0,
            // Tier 3: 奇蹟軍武與機甲裝配
            titan_alloy: 0,
            faith_crystal: 0,
            mega_apple_pulp: 0,
            // Phase 8 GaaS 普世化資源
            love_mana: 0,
            relic_slates: 0,
            kizuna_points: 0
        };

        this.craftingTimer = 0;
        this.wealthThreatScore = 0;
        this.hasTriggeredCrusade = false;
        this.enchantedRTSUnits = false;
        this.hydraulicBonusTimer = 0; // 水利動力加乘倒數
        this.hydraulicMult = 1.0;
    }

    /**
     * 固定物理步長更新：電導率自動化煉金與轉化
     * @returns {number} 更新後的上帝能量值 (Energy)
     */
    update(dt, currentEnergy, villages, uiManager) {
        this.craftingTimer += dt;
        let newEnergy = currentEnergy;

        if (this.hydraulicBonusTimer > 0) {
            this.hydraulicBonusTimer -= dt;
            if (this.hydraulicBonusTimer <= 0) {
                this.hydraulicMult = 1.0;
                if (uiManager) uiManager.showNotice(`ℹ️ 臨時水庫水利動力加持已結束，工業鍛造回復正常效率。`, 'info');
            }
        }

        // 每秒進行一次虛擬管線自動轉化 (Conductance Matching)
        if (this.craftingTimer >= 1.0) {
            this.craftingTimer = 0;

            // 1. Tier 2 轉化：鐵礦 + 信仰法力 => 精煉曜石 (Obsidian Steel)
            if (this.inventory.iron >= 10 && newEnergy >= 40) {
                this.inventory.iron -= 10;
                newEnergy -= 40;
                this.inventory.obsidian_steel += 2 * this.hydraulicMult;
            }

            // 2. Tier 2 轉化：小麥 + 信仰法力 => 神聖狂熱之酒 (Sacred Wine)
            if (this.inventory.wheat >= 20 && newEnergy >= 30) {
                this.inventory.wheat -= 20;
                newEnergy -= 30;
                this.inventory.sacred_wine += 2;
            }

            // 3. Tier 3 轉化：曜石 + 聖酒 => 泰坦合金 (Titan Alloy)
            if (this.inventory.obsidian_steel >= 10 && this.inventory.sacred_wine >= 10) {
                this.inventory.obsidian_steel -= 10;
                this.inventory.sacred_wine -= 10;
                this.inventory.titan_alloy += 2;
            }

            // 4. Tier 3 轉化：曜石 + 大量法力 => 信仰結晶能量核 (Faith Crystal)
            if (this.inventory.obsidian_steel >= 8 && newEnergy >= 80) {
                this.inventory.obsidian_steel -= 8;
                newEnergy -= 80;
                this.inventory.faith_crystal += 1;
            }

            // 計算財富熱度引力指數
            this.wealthThreatScore = this.inventory.obsidian_steel * 2 + this.inventory.titan_alloy * 5 + this.inventory.faith_crystal * 10;

            // 當財富熱度超過 300 且尚未引發侵略時，廣播反神掠奪同盟事件！
            if (this.wealthThreatScore >= 300 && !this.hasTriggeredCrusade) {
                this.hasTriggeredCrusade = true;
                console.warn(`🔥 [SupplyChain] 財富熱度 (Score: ${this.wealthThreatScore}) 突破臨界點！誘發敵國反神掠奪同盟 RTS 衝鋒！`);
                window.dispatchEvent(new CustomEvent('WEALTH_THREAT_CRUSADE_ATTRACTED', {
                    detail: { score: this.wealthThreatScore }
                }));
                if (uiManager) {
                    uiManager.showNotice(`🔥 警告！您的高階合金財富誘發了敵方【反神掠奪同盟】的千人衝鋒！`, 'danger');
                }
            }
        }

        return newEnergy;
    }

    /**
     * 神獸重裝機甲與武器改裝 (Beast Mecha Augmentation)
     */
    equipBeastMecha(creature, mechaType = 'arc_cannon', uiManager) {
        if (!creature) {
            console.warn(`⚠️ [SupplyChain] 當前場上無神獸，無法裝配機甲。`);
            return false;
        }

        const costAlloy = 30;
        const costCrystal = 10;
        if (this.inventory.titan_alloy < costAlloy || this.inventory.faith_crystal < costCrystal) {
            console.warn(`⚠️ [SupplyChain] 合金或結晶不足！需要泰坦合金 x${costAlloy}, 信仰結晶 x${costCrystal}。當前：合金=${this.inventory.titan_alloy}, 結晶=${this.inventory.faith_crystal}`);
            if (uiManager) uiManager.showNotice(`⚠️ 泰坦合金或信仰結晶不足，無法改裝神獸機甲！`, 'warning');
            return false;
        }

        // 消耗資源
        this.inventory.titan_alloy -= costAlloy;
        this.inventory.faith_crystal -= costCrystal;

        // 裝配屬性升級
        creature.mechaEquipped = mechaType;
        creature.health = 350; // 裝甲血量加持
        creature.scale = 1.3;  // 裝甲體型變大
        creature.thought = mechaType === 'arc_cannon' 
            ? "「⚡ 我裝載了泰坦合金極光弧光砲！我將以雷射切割所有侵犯上帝領土的敵軍！」"
            : "「🛡️ 我穿上了精煉曜石外骨骼鎧甲！防禦力狂升 300%！」";
        
        console.log(`🤖 [SupplyChain] 成功為神獸裝配【${mechaType === 'arc_cannon' ? '浮空極光砲台' : '重裝外骨骼鎧甲'}】！`);
        if (uiManager) {
            uiManager.showNotice(`🤖 神獸已改裝裝配【${mechaType === 'arc_cannon' ? '極光弧光砲台' : '曜石重裝外骨骼'}】！防禦與戰力飆升！`, 'success');
        }
        return true;
    }

    /**
     * RTS 方陣信仰附魔改裝 (RTS Unit Enchantment)
     */
    enchantRTSUnits(uiManager) {
        const costCrystal = 25;
        if (this.inventory.faith_crystal < costCrystal) {
            if (uiManager) uiManager.showNotice(`⚠️ 信仰結晶不足 (需 x${costCrystal})，無法附魔 RTS 方陣！`, 'warning');
            return false;
        }
        this.inventory.faith_crystal -= costCrystal;
        this.enchantedRTSUnits = true;
        console.log(`✨ [SupplyChain] 成功為全體 RTS 方陣完成【信仰光芒附魔】！普通攻擊附帶聖光濺射！`);
        if (uiManager) {
            uiManager.showNotice(`✨ 全體 RTS 方陣獲頒【信仰結晶附魔】！普攻附帶聖光濺射與戰死自爆！`, 'success');
        }
        return true;
    }

    /**
     * 壓測專用：一鍵注入工業與神蹟資源
     */
    injectResources(amount = 200) {
        this.inventory.iron += amount;
        this.inventory.obsidian_steel += amount;
        this.inventory.sacred_wine += amount;
        this.inventory.titan_alloy += amount;
        this.inventory.faith_crystal += amount / 2;
        console.log(`📈 [SupplyChain] 成功注入三階段物化物資 x${amount}！當前庫存：`, this.inventory);
    }

    /**
     * Phase 7 非對稱雙人遊玩事件：觸發「巨大金蘋果」掉落與水利危機/契機
     */
    triggerGoldenMegaApple(uiManager) {
        this.inventory.mega_apple_pulp += 5000;
        this.hydraulicBonusTimer = 180; // 3分鐘 300% 工業水利動力
        this.hydraulicMult = 3.0;
        console.log(`🍎 [Co-op] 觸發【巨大金蘋果事件】！河道受阻形成高位水庫，獲得 300% 水利動力與 5000 果肉！`);
        if (uiManager) {
            uiManager.showNotice(`🍎 【非對稱協作】：小孩撞落超巨型金蘋果！河道形成水庫，大人解鎖 300% 水利鍛造動力！`, 'success');
        }
    }

    /**
     * Phase 7 非對稱雙人遊玩事件：神獸啃咬金蘋果核心暴露信仰結晶
     */
    triggerBeastAppleBite(creature, uiManager) {
        if (this.inventory.mega_apple_pulp < 500) {
            if (uiManager) uiManager.showNotice(`⚠️ 場上沒有足夠的巨大蘋果果肉！請先觸發巨大金蘋果事件！`, 'warning');
            return false;
        }
        this.inventory.mega_apple_pulp -= 500;
        this.inventory.faith_crystal += 25;
        this.inventory.titan_alloy += 50;
        if (creature) {
            creature.hunger = 100;
            creature.health = creature.maxHealth || 300;
            creature.thought = "「🍎 汪汪/吼！我把巨大金蘋果核心咬開了！好甜！裡面藏著發光的信仰結晶！」";
        }
        console.log(`✨ [Co-op] 神獸啃咬蘋果核心，暴露出信仰結晶 x25 與泰坦合金 x50！`);
        if (uiManager) {
            uiManager.showNotice(`✨ 【親子聯擊】：神獸啃開蘋果芯，大人獲得頂級戰略資源【信仰結晶 x25】！`, 'success');
        }
        return true;
    }

    /**
     * Phase 7 湧現式物理化學引擎：元素連鎖反應協議
     */
    triggerElementalChain(type = 'gas_balloon', uiManager) {
        if (type === 'gas_balloon') {
            console.log(`⚡💨 [Elemental] 觸發【烤地瓜導電熱氣球】：雷電 + 沼氣形成對流電漿場，0 損耗全滅敵軍盔甲方陣！`);
            if (uiManager) uiManager.showNotice(`⚡💨 【元素連鎖】：雷電點燃沼氣！小孩看見敵人炸飛，大人解鎖對流導電電漿場防線！`, 'success');
        } else if (type === 'cryo_slide') {
            this.hydraulicBonusTimer = 120;
            this.hydraulicMult = 2.0;
            console.log(`❄️💧 [Elemental] 觸發【冰鎮滑溜溜溜冰場】：冰面動量陷阱撞碎敵軍，冰水冷卻煉金爐產能提升 2x！`);
            if (uiManager) uiManager.showNotice(`❄️💧 【元素連鎖】：冰水斜坡變成溜冰場陷阱！敵人滑倒滾成一團，冰水冷卻煉金爐產能倍增！`, 'success');
        } else if (type === 'caramel_swamp') {
            console.log(`🔥🍯 [Elemental] 觸發【焦糖化黏稠糖漿沼澤】：果實融化成拉絲焦糖，敵方巨獸與攻城衝車緩速 90%！`);
            if (uiManager) uiManager.showNotice(`🔥🍯 【元素連鎖】：倉庫果糖高溫融化成焦糖沼澤！敵人深入拉絲糖漿緩速 90%，成為完美靶場！`, 'success');
        }
    }

    /**
     * Phase 8 向前失敗機制 (Fail-Forward)：美麗古典遺跡重生系統
     */
    triggerVillageDestructionRebirth(village, uiManager) {
        this.inventory.relic_slates = (this.inventory.relic_slates || 0) + 50;
        if (village) {
            village.isRelicRuin = true;
            village.name = `✨神聖古典遺跡（原 ${village.name}）`;
        }
        console.log(`🏛️✨ [Fail-Forward] 村莊毀滅轉化為神聖古典遺跡！開採獲得古文明智慧遺物 x50，解鎖【自動化浮空石鶴】！`);
        if (uiManager) {
            uiManager.showNotice(`🏛️✨ 【向前失敗 / 遺跡重生】：村莊在天外聖光中化為美麗苔蘚遺跡！開採榮獲【古智慧遺物 x50】，解鎖建造速度 +300% 的浮空石鶴！`, 'success');
        }
    }

    /**
     * Phase 8 向前失敗機制 (Fail-Forward)：神獸生物抗體突變 (Beast Antibody Evolution)
     */
    triggerBeastCocoonMutation(creature, element = 'lightning', uiManager) {
        if (creature) {
            creature.isCocoonSlumber = true;
            creature.health = creature.maxHealth || 300;
            creature.antibody = element === 'lightning' ? '避雷針角 (Lightning Conductor Horns)' : '外骨骼隔熱鎧甲 (Thermal Shield)';
            creature.thought = `「🦁✨ 我從金色光繭甦醒了！體表長出了針對 ${element} 傷害的永久抗體甲殼【${creature.antibody}】！現在不僅免疫還能吸收轉化為反擊電漿砲！」`;
        }
        console.log(`🦁✨ [Fail-Forward] 神獸被擊倒後進入光繭沉睡，甦醒進化出抗體甲殼【${element}抵抗】！`);
        if (uiManager) {
            uiManager.showNotice(`🦁✨ 【向前失敗 / 抗體進化】：神獸被打倒後化為金色光繭！親密度零損失，破繭進化出永久【避雷針角】，吸收雷擊反打電漿砲！`, 'success');
        }
    }
}
