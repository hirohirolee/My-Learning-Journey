/**
 * v2_executive_theme - AI Studio Specific Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    fetchStudioDataAndRender();
});

function fetchStudioDataAndRender() {
    try {
        if (typeof contentData === 'undefined') {
            throw new Error("contentData is not defined. Make sure data/content.js is loaded.");
        }
        const data = contentData;
        
        renderAiStudio(data.aiStudioProjects);
        triggerAnimations();
        
    } catch (error) {
        console.error('Failed to load content data:', error);
        const container = document.getElementById('ai-studio-container');
        if (container) {
            container.innerHTML = `<p style="color:red">Error loading AI Studio data: ${error.message}</p>`;
        }
    }
}

function renderAiStudio(projects) {
    const container = document.getElementById('ai-studio-container');
    if (!container || !projects) return;
    
    let html = `<div class="ai-studio-grid">`;
    projects.forEach((project, index) => {
        const delay = (index * 0.15) + 's';
        
        let tagsHtml = '';
        if (project.techStack && project.techStack.length > 0) {
            tagsHtml = `<div class="studio-tags">`;
            project.techStack.forEach(tag => {
                tagsHtml += `<span class="tech-badge">${tag}</span>`;
            });
            tagsHtml += `</div>`;
        }
        
        let linksHtml = '';
        if (project.links) {
            linksHtml = `<div class="studio-actions">`;
            if (project.links.liveDemo && project.links.liveDemo !== '#') {
                linksHtml += `<a href="${project.links.liveDemo}" target="_blank" rel="noopener noreferrer" class="action-icon" title="Launch Streamlit App">
                                <i class="fa-solid fa-arrow-up-right-from-square"></i>
                              </a>`;
            }
            if (project.links.sourceCode && project.links.sourceCode !== '#') {
                linksHtml += `<a href="${project.links.sourceCode}" target="_blank" rel="noopener noreferrer" class="action-icon" title="Source Code">
                                <i class="fa-brands fa-github"></i>
                              </a>`;
            }
            if (project.links.docs && project.links.docs !== '#') {
                linksHtml += `<a href="${project.links.docs}" target="_blank" class="action-icon" title="Documentation">
                                <i class="fa-solid fa-file-lines"></i>
                              </a>`;
            }
            linksHtml += `</div>`;
        }

        let impactHtml = '';
        if (project.businessImpact) {
            impactHtml = `<div class="business-impact">${project.businessImpact}</div>`;
        }

        html += `
            <article class="studio-card anim-target" data-anim="slide-up" style="animation-delay: ${delay}">
                <h3>${project.title}</h3>
                <p class="card-desc">${project.description}</p>
                ${impactHtml}
                ${tagsHtml}
                ${linksHtml}
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
