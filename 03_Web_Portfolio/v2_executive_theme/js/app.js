/**
 * v2_executive_theme - Client-Side Micro-Interactions (Behavior Only)
 * De-containerized architecture: Content is static semantic HTML5.
 * This script only manages Accordion states and Clipboard copy.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAccordion();
});

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

    const textToCopy = targetEl.innerText;
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
