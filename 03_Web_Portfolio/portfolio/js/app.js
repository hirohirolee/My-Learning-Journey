/**
 * v2_executive_theme - Main Application Logic (Home Page)
 */

document.addEventListener('DOMContentLoaded', () => {
    fetchDataAndRender();
});

function fetchDataAndRender() {
    try {
        if (typeof contentData === 'undefined') {
            throw new Error("contentData is not defined. Make sure data/content.js is loaded.");
        }
        const data = contentData;
        
        renderProfile(data.profile);
        renderCertifications(data.certifications);
        renderServices(data.services);
        if (data.workExperience) {
            renderExperience(data.workExperience);
        }
        if (data.caseStudies) {
            renderCaseStudies(data.caseStudies);
        }
        if (data.mediaKit) {
            renderMediaKit(data.mediaKit);
        }
        
        triggerAnimations();
        
    } catch (error) {
        console.error('Failed to load content data:', error);
        const container = document.getElementById('hero-container');
        if (container) {
            container.innerHTML = `<p style="color:red">Error loading profile data: ${error.message}</p>`;
        }
    }
}

function renderMediaKit(mediaKit) {
    const container = document.getElementById('media-kit-container');
    if (!container) return;

    let downloadsHtml = '';
    mediaKit.downloads.forEach(dl => {
        downloadsHtml += `
            <a href="${dl.file}" class="btn-download" target="_blank" rel="noopener noreferrer">
                <i class="fa-solid ${dl.icon}"></i> ${dl.title}
            </a>
        `;
    });

    let equipmentHtml = '';
    mediaKit.equipment.forEach(eq => {
        equipmentHtml += `<li>${eq}</li>`;
    });

    const html = `
        <div class="media-kit-grid anim-target" data-anim="slide-up">
            <div class="media-kit-col">
                <h3><i class="fa-solid fa-address-card"></i> 公關簡介 (Speaker Bio)</h3>
                
                <div class="bio-card">
                    <h4>
                        100 字短版簡介
                        <button class="btn-copy" onclick="copyToClipboard(this, 'bio-short')">
                            <i class="fa-regular fa-copy"></i> 複製
                        </button>
                    </h4>
                    <p id="bio-short">${mediaKit.bios.short}</p>
                </div>
                
                <div class="bio-card">
                    <h4>
                        300 字完整簡介
                        <button class="btn-copy" onclick="copyToClipboard(this, 'bio-long')">
                            <i class="fa-regular fa-copy"></i> 複製
                        </button>
                    </h4>
                    <p id="bio-long">${mediaKit.bios.long}</p>
                </div>

                <h3 style="margin-top: 2rem;"><i class="fa-solid fa-microphone-lines"></i> 場地與設備需求 (Equipment)</h3>
                <ul class="equipment-list">
                    ${equipmentHtml}
                </ul>
            </div>
            
            <div class="media-kit-col">
                <div class="download-card">
                    <i class="fa-solid fa-cloud-arrow-down"></i>
                    <h4>一鍵下載講者素材包</h4>
                    <div style="width: 100%;">
                        ${downloadsHtml}
                    </div>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Global function for copy to clipboard
window.copyToClipboard = function(btn, elementId) {
    const textToCopy = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check"></i> 已複製';
        btn.classList.add('copied');
        
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
};

function renderExperience(experienceList) {
    const container = document.getElementById('experience-container');
    if (!container) return;
    
    let html = `<div class="timeline">`;
    experienceList.forEach((exp, index) => {
        const delay = (index * 0.15) + 's';
        
        let highlightsHtml = '';
        if (exp.highlights && exp.highlights.length > 0) {
            highlightsHtml = `<ul class="timeline-highlights">`;
            exp.highlights.forEach(hl => {
                // Regex to find "Text: " or "Text：" and wrap in strong tag
                const formattedHl = hl.replace(/^([^：:]+[：:])/, '<strong class="highlight-title">$1</strong>');
                highlightsHtml += `<li>${formattedHl}</li>`;
            });
            highlightsHtml += `</ul>`;
        }

        html += `
            <div class="timeline-item anim-target" data-anim="slide-up" style="animation-delay: ${delay}">
                <div class="timeline-dot"></div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <span class="timeline-period">${exp.period}</span>
                        <h3 class="timeline-title">${exp.title}</h3>
                        <h4 class="timeline-company">${exp.company}</h4>
                    </div>
                    ${highlightsHtml}
                </div>
            </div>
        `;
    });
    html += `</div>`;
    
    container.innerHTML = html;
}

function renderCaseStudies(caseStudies) {
    const container = document.getElementById('case-studies-container');
    if (!container) return;
    
    let html = `<div class="accordion anim-target" data-anim="slide-up">`;
    caseStudies.forEach((study, index) => {
        html += `
            <div class="accordion-item">
                <button class="accordion-header" aria-expanded="false">
                    <span>${study.title}</span>
                    <i class="fa-solid fa-plus accordion-icon"></i>
                </button>
                <div class="accordion-content">
                    <div class="accordion-body">
                        <div class="star-section">
                            <strong>Situation (背景)</strong>
                            <p>${study.situation}</p>
                        </div>
                        <div class="star-section">
                            <strong>Task (任務)</strong>
                            <p>${study.task}</p>
                        </div>
                        <div class="star-section">
                            <strong>Action (行動)</strong>
                            <p>${study.action}</p>
                        </div>
                        <div class="star-section star-result">
                            <strong>Result (結果與商業成效)</strong>
                            <p>${study.result}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    html += `</div>`;
    
    container.innerHTML = html;

    // Attach Accordion Event Listeners
    const accordions = container.querySelectorAll('.accordion-header');
    accordions.forEach(acc => {
        acc.addEventListener('click', function() {
            // Close all others
            const currentItem = this.parentElement;
            const isCurrentlyActive = currentItem.classList.contains('active');
            
            container.querySelectorAll('.accordion-item').forEach(item => {
                item.classList.remove('active');
                item.querySelector('.accordion-content').style.maxHeight = null;
                item.querySelector('.accordion-header').setAttribute('aria-expanded', 'false');
            });

            // Toggle current one
            if (!isCurrentlyActive) {
                currentItem.classList.add('active');
                this.setAttribute('aria-expanded', 'true');
                const content = currentItem.querySelector('.accordion-content');
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });
}

function renderProfile(profile) {
    const container = document.getElementById('hero-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="hero-content anim-target" data-anim="slide-up">
            <span class="hero-title">${profile.title}</span>
            <h1>${profile.name}</h1>
            <p style="font-size: 1.25rem; color: var(--color-text-main); margin-bottom: 2rem;">
                ${profile.slogan}
            </p>
            ${profile.yearsOfExperience ? `<p class="text-gold" style="font-weight: 500;">擁有 ${profile.yearsOfExperience} 年實戰經驗</p>` : ''}
        </div>
    `;
}

function renderCertifications(certs) {
    const container = document.getElementById('certifications-container');
    if (!container || !certs) return;
    
    let html = `<div class="certifications-list anim-target" data-anim="fade-in" style="animation-delay: 0.2s">`;
    certs.forEach(cert => {
        html += `<span class="cert-badge">${cert}</span>`;
    });
    html += `</div>`;
    
    container.innerHTML = html;
}

function renderServices(services) {
    const container = document.getElementById('services-container');
    if (!container || !services) return;
    
    let html = `<div class="services-grid">`;
    services.forEach((service, index) => {
        const delay = (index * 0.15) + 's';
        html += `
            <article class="service-card anim-target" data-anim="slide-up" style="animation-delay: ${delay}">
                <h3>${service.title}</h3>
                <p>${service.description}</p>
            </article>
        `;
    });
    html += `</div>`;
    
    container.innerHTML = html;
}

function triggerAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const animType = entry.target.getAttribute('data-anim');
                if (animType === 'slide-up') {
                    entry.target.classList.add('animate-slide-up');
                } else if (animType === 'fade-in') {
                    entry.target.classList.add('animate-fade-in');
                }
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    });

    document.querySelectorAll('.anim-target').forEach(el => {
        observer.observe(el);
    });
}
