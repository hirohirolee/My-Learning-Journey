/**
 * ============================================================================
 * 模組：GaaS 普世化服務型生態引擎 (GaaSEcosystemManager)
 * 參照 Bartle 玩家心理學與服務型遊戲長青架構
 * 1. 跨平台節奏切換：手機端通勤 Tamagotchi 互動同步 (+30% 產能 Buff)
 * 2. 溫和異步社交：《死亡擱淺》與《動森》式零 PVP 毒性互助連接
 * 3. Cozy 信仰裝飾與心情共振：美學即戰力，釋放愛心結晶法力 (Love Mana)
 * ============================================================================
 */

export class GaaSEcosystemManager {
    constructor() {
        this.commuteBuffActive = false;
        this.commuteBuffTimer = 0;
        this.aestheticScore = 50;
        this.currentSkin = 'default';
        this.currentPalette = 'neutral';
        this.friendAegisActive = false;
        this.friendAegisTimer = 0;

        // 異步社交狀態池
        this.ambassadorBeast = null;
        this.strandBoxAvailable = false;
    }

    /**
     * 1. 跨平台同步：模擬手機端通勤 Tamagotchi 遊玩包裹下載
     */
    simulateMobileCommuteSession(clicks = 50, fishingRewards = 100, supplyChain, uiManager) {
        if (!supplyChain) return false;
        
        supplyChain.inventory.love_mana = (supplyChain.inventory.love_mana || 0) + clicks * 2;
        supplyChain.inventory.faith_crystal += fishingRewards;
        supplyChain.inventory.kizuna_points = (supplyChain.inventory.kizuna_points || 0) + 30;

        this.commuteBuffActive = true;
        this.commuteBuffTimer = 600; // 10 分鐘 (實時) 30% 全島產能 Buff

        console.log(`📱 [GaaS-CrossPlatform] 成功下載手機通勤遊玩數據包！愛心法力 +${clicks*2}，信仰結晶 +${fishingRewards}！全島產能 +30%！`);
        if (uiManager) {
            uiManager.showNotice(`📱 【跨平台同步】：神獸從手機端帶回滿滿礦石！因通勤被摸 ${clicks} 次極度亢奮，今日全島煉金與產能 +30%！`, 'success');
        }
        return true;
    }

    /**
     * 2.1 溫和異步社交：好友神獸觀光大使打工 (Beast Ambassador)
     */
    triggerBeastAmbassadorVisit(friendName = "好友【虎子】", supplyChain, uiManager) {
        this.ambassadorBeast = { name: friendName, workHours: 5, status: 'visiting' };
        if (supplyChain) {
            supplyChain.inventory.wheat += 500;
            supplyChain.inventory.bread += 300;
            supplyChain.inventory.kizuna_points = (supplyChain.inventory.kizuna_points || 0) + 50;
        }
        console.log(`🤝 [GaaS-Social] 異步好友神獸大使抵達！請喝美酒施展【豐收奇蹟】，小麥與麵包豐收！`);
        if (uiManager) {
            uiManager.showNotice(`🤝 【異步社交】：${friendName}背著小背包來您的島嶼打工！為您的麥田施展【豐收奇蹟】，作物產量翻倍並送上 50 羈絆點！`, 'success');
        }
    }

    /**
     * 2.2 溫和異步社交：天災呼叫好友神明護盾 (Friend Divine Aegis)
     */
    summonFriendDivineAegis(friendName = "阿修羅神明", uiManager) {
        this.friendAegisActive = true;
        this.friendAegisTimer = 60; // 60秒無敵恆溫護盾
        console.log(`🆘✨ [GaaS-Social] 成功調用好友【${friendName}】的黃金神話幻影，展開 60 秒天災防禦罩！`);
        if (uiManager) {
            uiManager.showNotice(`🆘✨ 【天災共同防線】：成功呼叫好友【${friendName}】的神明幻影！在上空撐起 60 秒恆溫無敵護盾，為您擋過致命天災！`, 'success');
        }
    }

    /**
     * 2.3 溫和異步社交：死亡擱淺式漂流補給箱 (Strand Supply Box)
     */
    spawnStrandSupplyBox(supplyChain, uiManager) {
        this.strandBoxAvailable = true;
        if (supplyChain) {
            supplyChain.inventory.obsidian_steel += 150;
            supplyChain.inventory.titan_alloy += 80;
        }
        console.log(`👍📦 [GaaS-Social] 發現死亡擱淺式漂流補給箱！獲得精煉曜石 x150，泰坦合金 x80！`);
        if (uiManager) {
            uiManager.showNotice(`👍📦 【善良連接】：海灘漂來陌生好友的【物流補給箱】！點讚感恩後解鎖曜石 x150 與合金 x80，榮獲黃金天使光環！`, 'success');
        }
    }

    /**
     * 3. Cozy 信仰裝飾與心情共振系統：美學即戰力 (Beauty is Power)
     */
    updateAestheticResonance(skinId = 'angel_ribbon', palette = 'sakura_pastel', supplyChain, villagers, uiManager) {
        this.currentSkin = skinId;
        this.currentPalette = palette;
        this.aestheticScore = 100; // 美學共振滿分

        if (supplyChain) {
            supplyChain.inventory.love_mana = (supplyChain.inventory.love_mana || 0) + 150;
        }

        if (villagers && villagers.length > 0) {
            for (const vg of villagers) {
                vg.happinessCap = 150; // 幸福上限突破至 150%
                vg.fatigueMult = 0.5;  // 疲勞累積減半
            }
        }

        console.log(`🎨✨ [GaaS-Cozy] 啟用 Cozy 美學共振！裝扮【${skinId}】與色彩【${palette}】，村民幸福上限突破至 150%，釋放愛心法力 x150！`);
        if (uiManager) {
            uiManager.showNotice(`🎨✨ 【美學即戰力】：您裝扮了【${skinId}】並鋪設【櫻花步道】！村民群聚拍手圍觀，幸福上限突破至 150%，釋放愛心結晶法力！`, 'success');
        }
    }

    /**
     * 60Hz 物理步長更新
     */
    update(dt) {
        if (this.commuteBuffActive && this.commuteBuffTimer > 0) {
            this.commuteBuffTimer -= dt;
            if (this.commuteBuffTimer <= 0) {
                this.commuteBuffActive = false;
                console.log(`ℹ️ [GaaS-CrossPlatform] 手機通勤 30% 產能 Buff 已結束。`);
            }
        }
        if (this.friendAegisActive && this.friendAegisTimer > 0) {
            this.friendAegisTimer -= dt;
            if (this.friendAegisTimer <= 0) {
                this.friendAegisActive = false;
                console.log(`ℹ️ [GaaS-Social] 好友神明黃金護盾已結束。`);
            }
        }
    }
}
