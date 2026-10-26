/**
 * v2_executive_theme - Client-Side Micro-Interactions (Behavior Only)
 * De-containerized architecture: Content is static semantic HTML5.
 * This script only manages Accordion states, Clipboard copy, and Contact Form API.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAccordion();
    initContactForm();
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
 * Global Copy to Clipboard Helper for Speaker Bios
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

/**
 * Asynchronous Contact Form Submission (Formspree)
 */
function initContactForm() {
    const form = document.getElementById('contact-form');
    if (!form) return;
    
    const status = document.getElementById('contact-status');
    const btn = document.getElementById('contact-submit-btn');
    
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        const data = new FormData(event.target);
        
        if (btn) {
            btn.disabled = true;
            btn.innerText = '訊息傳送中…';
        }
        if (status) {
            status.className = 'form-status status-pending';
            status.innerHTML = '正在傳送您的諮詢摘要，請稍候…';
        }
        
        try {
            const response = await fetch(event.target.action, {
                method: form.method,
                body: data,
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                if (status) {
                    status.className = 'form-status status-success';
                    status.innerHTML = '✓ 諮詢摘要已成功送達。Hiro Lee 將於 24 小時內親自審閱並回覆。';
                }
                form.reset();
            } else {
                const responseData = await response.json();
                if (Object.hasOwn(responseData, 'errors')) {
                    status.innerHTML = responseData["errors"].map(error => error["message"]).join(", ");
                } else {
                    if (status) status.innerHTML = '訊息傳送失敗，請直接寄信至 hirolee@gmail.com。';
                }
                if (status) status.className = 'form-status status-error';
            }
        } catch (error) {
            if (status) {
                status.className = 'form-status status-error';
                status.innerHTML = '網路連線異常，請直接寄信至 hirolee@gmail.com。';
            }
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerText = '發送評估需求';
            }
        }
    });
}
