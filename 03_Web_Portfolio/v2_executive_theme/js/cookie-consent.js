/**
 * v2_executive_theme - Cookie Consent Logic (ISO 27701 Compliance Level)
 */
document.addEventListener('DOMContentLoaded', () => {
    // Check if user has already consented
    const consentStatus = localStorage.getItem('exec_cookie_consent');
    if (!consentStatus) {
        showCookieBanner();
    }
});

function showCookieBanner() {
    const banner = document.createElement('div');
    banner.className = 'cookie-banner anim-target animate-slide-up';
    banner.innerHTML = `
        <div class="cookie-content">
            <i class="fa-solid fa-shield-halved cookie-icon"></i>
            <div>
                <h4>Privacy & Cookie Policy</h4>
                <p>本網站致力於資訊安全與隱私保護。我們使用必要的 Cookie 來提升您的瀏覽體驗與進行基本流量分析。<a href="#" style="color: var(--color-accent-cyan);">深入了解我們的隱私權政策</a>。</p>
            </div>
        </div>
        <div class="cookie-actions">
            <button class="btn-secondary" id="btn-cookie-prefs">自訂設定</button>
            <button class="btn-primary" id="btn-cookie-accept">接受全部</button>
        </div>
    `;
    
    document.body.appendChild(banner);
    
    document.getElementById('btn-cookie-accept').addEventListener('click', () => {
        localStorage.setItem('exec_cookie_consent', 'accepted');
        banner.style.opacity = '0';
        banner.style.transform = 'translateY(100%)';
        setTimeout(() => banner.remove(), 400);
    });

    document.getElementById('btn-cookie-prefs').addEventListener('click', () => {
        // Here you would typically open a modal for granular choices
        alert("自訂設定面板 (示範功能)：您可在此設定必要、分析與行銷類 Cookie 的層級。");
    });
}
