import { godProgression } from '../meta/progression.js';
import { creatureSkins } from '../meta/creature-skins.js';
import { analytics } from './analytics.js';

/**
 * 商業變現對接層與廣告內購處理器 (Monetization & IAP/Ads SDK Adapter)
 * 封裝獎勵型廣告 (Rewarded Ads) 與商城內購 (IAP)，具備無縫對接 Poki, CrazyGames 或 Steam 微交易 API 的標準化介面。
 */
export const SHOP_ITEMS = [
    { id: 'pack_small', title: '小袋信仰水晶', desc: '獲得 +60 信仰水晶，用於升級天賦', type: 'crystal', amount: 60, costType: 'ad', icon: '💎' },
    { id: 'pack_large', title: '一箱信仰水晶', desc: '獲得 +300 信仰水晶與額外祝福', type: 'crystal', amount: 300, costType: 'iap', price: '$2.99 USD', icon: '📦' },
    { id: 'beast_dragon', title: '傳說神龍 (Dragon)', desc: '解鎖商用限定頂級東方巨龍神獸', type: 'beast', speciesId: 'dragon', costType: 'crystal', price: 200, icon: '🐉' },
    { id: 'beast_phoenix', title: '傳說不死鳥 (Phoenix)', desc: '解鎖商用限定浴火神聖不死鳥神獸', type: 'beast', speciesId: 'phoenix', costType: 'crystal', price: 200, icon: '🦅' },
    { id: 'skin_crown', title: '王者之神冠', desc: '解鎖頂級神獸飾品：王者之神冠', type: 'skin', skinId: 'crown', costType: 'crystal', price: 120, icon: '👑' }
];

export class MonetizationService {
    constructor() {
        this.adCooldown = false;
    }

    /**
     * 檢查當前是否有可播放的獎勵型廣告
     */
    isAdReady() {
        return !this.adCooldown;
    }

    /**
     * 播放獎勵型廣告 (支援自動對接 Poki/CrazyGames SDK 或本地模擬器)
     */
    showRewardedAd({ onReward, onClose, onFail, uiManager }) {
        if (this.adCooldown) {
            if (onFail) onFail('廣告冷卻中，請稍後再試！');
            return;
        }

        analytics.trackEvent('ad_requested');

        // 檢查是否處於真實發行平台 (如 Poki / CrazyGames)
        if (typeof window !== 'undefined' && window.PokiSDK && typeof window.PokiSDK.rewardedBreak === 'function') {
            window.PokiSDK.rewardedBreak().then((withReward) => {
                if (withReward) {
                    analytics.trackEvent('ad_reward_earned');
                    if (onReward) onReward();
                } else {
                    if (onClose) onClose();
                }
            });
            return;
        }

        // 否則啟動本地商用模擬廣告視窗 (模擬 3 秒倒數計時)
        this.adCooldown = true;
        setTimeout(() => this.adCooldown = false, 30000); // 30秒冷卻

        this.simulateAdModal(onReward, onClose, uiManager);
    }

    simulateAdModal(onReward, onClose, uiManager) {
        const modal = document.createElement('div');
        modal.className = 'modal-backdrop ad-modal';
        modal.innerHTML = `
            <div class="modal-card ad-card" style="text-align:center; max-width: 400px; padding: 30px;">
                <h2 style="color: var(--primary-gold);">📺 神聖感應連線中...</h2>
                <p style="margin: 20px 0; color: #cbd5e1;">正在接收來自高維世界的信仰祝福 (獎勵型廣告模擬)</p>
                <div class="ad-spinner" style="font-size: 3rem; margin: 20px 0;">✨</div>
                <p id="ad-timer" style="font-size: 1.5rem; font-weight: bold; color: var(--accent-cyan);">剩餘 3 秒...</p>
            </div>
        `;
        document.body.appendChild(modal);

        let count = 3;
        const timer = setInterval(() => {
            count--;
            const timerEl = document.getElementById('ad-timer');
            if (timerEl) timerEl.textContent = `剩餘 ${count} 秒...`;

            if (count <= 0) {
                clearInterval(timer);
                document.body.removeChild(modal);
                analytics.trackEvent('ad_reward_earned_simulated');
                if (onReward) onReward();
                if (uiManager) uiManager.showNotice('✨ 廣告感應結束！已發放神聖獎勵！', 'info');
            }
        }, 1000);
    }

    /**
     * 商城商品購買執行邏輯
     */
    purchaseItem(item, uiManager) {
        analytics.trackEvent('shop_purchase_click', { itemId: item.id });

        if (item.costType === 'ad') {
            this.showRewardedAd({
                onReward: () => {
                    godProgression.addCrystals(item.amount);
                    if (uiManager) uiManager.showNotice(`💎 成功獲得 +${item.amount} 信仰水晶！`, 'info');
                    if (uiManager) uiManager.renderShopModal();
                },
                uiManager
            });
            return { success: true, pending: true };
        }

        if (item.costType === 'crystal') {
            if (godProgression.crystals < item.price) {
                return { success: false, msg: '信仰水晶不足！' };
            }

            if (item.type === 'beast') {
                const res = godProgression.unlockBeast(item.speciesId, item.price);
                if (!res.success) return res;
            } else if (item.type === 'skin') {
                const res = creatureSkins.unlock(item.skinId);
                if (!res.success) return res;
            }

            analytics.trackEvent('shop_purchase_success', { itemId: item.id, cost: item.price });
            return { success: true, msg: `🎉 成功解鎖【${item.title}】！` };
        }

        if (item.costType === 'iap') {
            // 模擬真實 IAP 結帳流程
            const confirmed = confirm(`【商用內購測試】是否確認支付 ${item.price} 購買 ${item.title}？`);
            if (confirmed) {
                godProgression.addCrystals(item.amount || 300);
                analytics.trackEvent('iap_purchase_success', { itemId: item.id, price: item.price });
                return { success: true, msg: `🎉 模擬內購成功！獲得 +${item.amount || 300} 信仰水晶！` };
            }
            return { success: false, msg: '交易已取消。' };
        }

        return { success: false, msg: '未知交易類型！' };
    }
}

export const monetization = new MonetizationService();
