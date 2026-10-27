/**
 * v2_executive_theme - Cookie Consent & ISO 27701 Privacy Governance
 * Institutional compliance architecture (Zero Third-Party Trackers)
 */
document.addEventListener('DOMContentLoaded', () => {
    initPrivacyGovernance();
});

function initPrivacyGovernance() {
    createPrivacyDialog();
    const consentStatus = localStorage.getItem('exec_cookie_consent');
    if (!consentStatus) {
        showCookieBanner();
    }
}

function createPrivacyDialog() {
    if (document.getElementById('privacy-modal')) return;

    const dialog = document.createElement('dialog');
    dialog.id = 'privacy-modal';
    dialog.className = 'executive-dialog';
    dialog.setAttribute('aria-labelledby', 'dialog-title');
    dialog.innerHTML = `
        <div class="dialog-card">
            <header class="dialog-header">
                <div class="dialog-badge">ISO 27701 & GDPR ALIGNED</div>
                <h3 id="dialog-title">資訊隱私與數據治理準則</h3>
                <p class="dialog-subtitle">Minimalist Data Ethics · 零第三方商業追蹤宣告</p>
            </header>
            <div class="dialog-body">
                <div class="privacy-clause">
                    <span class="clause-num">01</span>
                    <div>
                        <h4>零第三方追蹤機制 (Zero Third-Party Trackers)</h4>
                        <p>本顧問網站採用純前端靜態與邊緣 CDN 架構，完全無掛載 Google Tag Manager、Facebook Pixel 或行銷指紋追蹤代碼，保障高階決策者匿名瀏覽權益。</p>
                    </div>
                </div>
                <div class="privacy-clause">
                    <span class="clause-num">02</span>
                    <div>
                        <h4>本地數據最小化 (Local Storage Only)</h4>
                        <p>我們僅使用瀏覽器端 <code>localStorage</code> 暫存您的隱私授權狀態（<code>exec_cookie_consent</code>），無任何伺服器端 Session 或使用者行為輪廓資料庫。</p>
                    </div>
                </div>
                <div class="privacy-clause">
                    <span class="clause-num">03</span>
                    <div>
                        <h4>加密通訊防護 (Enforced Cryptography)</h4>
                        <p>全站傳輸強制使用 TLS 1.3 與 HSTS 加密協定，並配置嚴格 CSP 與 Subresource Integrity (SRI)，杜絕供應鏈攻擊與中間人監聽。</p>
                    </div>
                </div>
            </div>
            <footer class="dialog-footer">
                <button type="button" class="btn-primary" id="btn-dialog-confirm">確認並儲存偏好</button>
            </footer>
        </div>
    `;

    document.body.appendChild(dialog);

    const confirmBtn = dialog.querySelector('#btn-dialog-confirm');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            localStorage.setItem('exec_cookie_consent', 'accepted');
            dialog.close();
            dismissCookieBanner();
        });
    }

    dialog.addEventListener('click', (e) => {
        const rect = dialog.getBoundingClientRect();
        const isInDialog = (rect.top <= e.clientY && e.clientY <= rect.top + rect.height
          && rect.left <= e.clientX && e.clientX <= rect.left + rect.width);
        if (!isInDialog) {
            dialog.close();
        }
    });
}

function showCookieBanner() {
    if (document.querySelector('.cookie-banner')) return;

    const banner = document.createElement('div');
    banner.className = 'cookie-banner anim-target animate-slide-up';
    banner.innerHTML = `
        <div class="cookie-content">
            <i class="fa-solid fa-shield-halved cookie-icon" aria-hidden="true"></i>
            <div>
                <h4>Privacy & Cookie Policy</h4>
                <p>本網站致力於資訊安全與隱私保護，嚴格奉行「零第三方商業追蹤」原則。<button type="button" id="btn-cookie-learn-more" style="background:none;border:none;color:var(--color-gold);text-decoration:underline;cursor:pointer;padding:0 4px;font-size:inherit;">深入了解隱私治理政策</button></p>
            </div>
        </div>
        <div class="cookie-actions">
            <button type="button" class="btn-secondary" id="btn-cookie-prefs">治理偏好</button>
            <button type="button" class="btn-primary" id="btn-cookie-accept">接受全部</button>
        </div>
    `;
    
    document.body.appendChild(banner);
    
    document.getElementById('btn-cookie-accept').addEventListener('click', () => {
        localStorage.setItem('exec_cookie_consent', 'accepted');
        dismissCookieBanner();
    });

    const openModal = () => {
        const dialog = document.getElementById('privacy-modal');
        if (dialog && typeof dialog.showModal === 'function') {
            dialog.showModal();
        }
    };

    const prefsBtn = document.getElementById('btn-cookie-prefs');
    if (prefsBtn) prefsBtn.addEventListener('click', openModal);

    const learnMoreBtn = document.getElementById('btn-cookie-learn-more');
    if (learnMoreBtn) learnMoreBtn.addEventListener('click', openModal);
}

function dismissCookieBanner() {
    const banner = document.querySelector('.cookie-banner');
    if (banner) {
        banner.style.opacity = '0';
        banner.style.transform = 'translate(-50%, 100%)';
        setTimeout(() => banner.remove(), 400);
    }
}
