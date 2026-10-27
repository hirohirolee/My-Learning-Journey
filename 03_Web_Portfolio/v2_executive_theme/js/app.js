/**
 * v2_executive_theme - Client-Side Micro-Interactions (Behavior Only)
 * De-containerized architecture: Content is static semantic HTML5.
 * This script only manages Accordion states and Clipboard copy.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAccordion();
    initEmailProtection();
});

/**
 * Anti-Scraping Dynamic Email Protection (ISO 27001 / Privacy Defense)
 * Prevents automated harvester bots from scraping plain text mailto addresses.
 */
function initEmailProtection() {
    const emailEls = document.querySelectorAll('.email-link');
    emailEls.forEach(el => {
        const user = el.getAttribute('data-user');
        const domain = el.getAttribute('data-domain');
        if (user && domain) {
            const address = `${user}@${domain}`;
            if (el.tagName.toLowerCase() === 'a') {
                el.href = `mailto:${address}`;
            }
            if (el.classList.contains('email-address')) {
                el.textContent = address;
            }
        }
    });
}

/**
 * Accordion Interactivity for STAR Case Studies
 */
function initAccordion() {
    const accordions = document.querySelectorAll('.accordion-header');
    if (!accordions.length) return;

    accordions.forEach(header => {
        header.addEventListener('click', function() {
            const currentItem = this.closest('.accordion-item');
            if (!currentItem) return;

            const isCurrentlyActive = currentItem.classList.contains('active');
            const parentAccordion = currentItem.closest('.accordion');

            // Close all items in this accordion group
            if (parentAccordion) {
                parentAccordion.querySelectorAll('.accordion-item').forEach(item => {
                    item.classList.remove('active');
                    const content = item.querySelector('.accordion-content');
                    if (content) content.style.maxHeight = null;
                    const btn = item.querySelector('.accordion-header');
                    if (btn) btn.setAttribute('aria-expanded', 'false');
                });
            }

            // Toggle current
            if (!isCurrentlyActive) {
                currentItem.classList.add('active');
                this.setAttribute('aria-expanded', 'true');
                const content = currentItem.querySelector('.accordion-content');
                if (content) {
                    content.style.maxHeight = content.scrollHeight + 'px';
                }
            }
        });
    });
}

/**
 * Global Copy to Clipboard Helper for Speaker Bios & Official Email
 */
window.copyToClipboard = function(btn, elementId) {
    const targetEl = document.getElementById(elementId);
    if (!targetEl) return;

    let textToCopy = targetEl.innerText || targetEl.textContent;
    if (targetEl.hasAttribute('data-user') && targetEl.hasAttribute('data-domain')) {
        textToCopy = `${targetEl.getAttribute('data-user')}@${targetEl.getAttribute('data-domain')}`;
    }

    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check" aria-hidden="true"></i> 已複製';
        btn.classList.add('copied');
        
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.remove('copied');
        }, 2200);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
};
