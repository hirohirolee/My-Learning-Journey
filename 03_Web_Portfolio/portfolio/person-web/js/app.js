/**
 * v2_executive_theme - Client-Side Micro-Interactions (Behavior Only)
 * De-containerized architecture: Content is static semantic HTML5.
 * Core: Accordion states, Click-to-Reveal Email, Scrollspy, Progress Indicator, and Back-to-Top.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAccordion();
    initClickToRevealEmail();
    initScrollProgress();
    initScrollspy();
    initBackToTop();
});

/**
 * Click-to-Reveal Email Protection (Strict Privacy Defense Mode)
 * Email remains completely hidden until a human visitor explicitly clicks the reveal button.
 */
function initClickToRevealEmail() {
    const revealBtn = document.getElementById('btn-reveal-email');
    const emailWrapper = document.getElementById('email-reveal-wrapper');
    const inquiryActions = document.getElementById('inquiry-actions');

    function revealAllEmails() {
        const emailEls = document.querySelectorAll('.email-link');
        emailEls.forEach(el => {
            const user = el.getAttribute('data-user');
            const domain = el.getAttribute('data-domain');
            if (user && domain) {
                const address = `${user}@${domain}`;
                el.href = `mailto:${address}`;
                if (el.classList.contains('email-address')) {
                    el.textContent = address;
                    el.style.display = 'inline-block';
                } else if (el.classList.contains('footer-email')) {
                    el.innerHTML = `${address} ↗`;
                }
            }
        });

        if (emailWrapper) emailWrapper.style.display = 'none';
        if (inquiryActions) inquiryActions.style.display = 'flex';
    }

    if (revealBtn) {
        revealBtn.addEventListener('click', function() {
            revealBtn.innerHTML = '<i class="fa-solid fa-lock-open" aria-hidden="true"></i> 驗證完成，正在揭示...';
            revealBtn.classList.add('revealing');
            setTimeout(() => {
                revealAllEmails();
            }, 300);
        });
    }

    // Direct click handling on footer email if clicked before card reveal
    document.querySelectorAll('.footer-email').forEach(el => {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            const user = this.getAttribute('data-user');
            const domain = this.getAttribute('data-domain');
            if (user && domain) {
                revealAllEmails();
                const address = `${user}@${domain}`;
                window.location.href = `mailto:${address}`;
            }
        });
    });
}

/**
 * Editorial Scroll Progress Indicator (1.5px Gold Accent)
 */
function initScrollProgress() {
    const progressBar = document.getElementById('scroll-progress');
    if (!progressBar) return;

    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
        progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
    }, { passive: true });
}

/**
 * Native IntersectionObserver Scrollspy
 * Zero-dependency viewport tracking that updates active nav state
 */
function initScrollspy() {
    const navLinks = document.querySelectorAll('.nav-links .nav-link-item');
    if (!navLinks.length) return;

    const sections = [];
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
            const targetSection = document.querySelector(href);
            if (targetSection) {
                sections.push({ el: targetSection, link: link, id: href });
            }
        }
    });

    if (!sections.length || !('IntersectionObserver' in window)) return;

    const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -65% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const targetId = `#${entry.target.id}`;
                navLinks.forEach(link => {
                    if (link.getAttribute('href') === targetId) {
                        link.classList.add('active');
                    } else {
                        link.classList.remove('active');
                    }
                });
            }
        });
    }, observerOptions);

    sections.forEach(item => observer.observe(item.el));
}

/**
 * Minimalist Back-to-Top Floating Trigger
 */
function initBackToTop() {
    const btn = document.getElementById('btn-back-to-top');
    if (!btn) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 550) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    }, { passive: true });

    btn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
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

    if (!textToCopy || textToCopy.trim() === '') {
        return;
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
