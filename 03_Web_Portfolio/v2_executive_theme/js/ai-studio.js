/**
 * v2_executive_theme - AI Studio Specific Logic
 * Clean Executive Card Grid & Tag Filtering Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    fetchStudioDataAndRender();
});

let currentCategory = 'all';

function fetchStudioDataAndRender() {
    try {
        if (typeof contentData === 'undefined') {
            throw new Error("contentData is not defined. Make sure data/content.js is loaded.");
        }
        const data = contentData;
        
        renderAiStudio(data.aiStudioProjects);
        initFilterHandlers(data.aiStudioProjects);
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
    
    const filteredProjects = currentCategory === 'all' 
        ? projects 
        : projects.filter(p => p.category === currentCategory);
        
    if (filteredProjects.length === 0) {
        container.innerHTML = `<div style="text-align:center; color:#94a3b8; padding:3rem 0;">無此類別的專案</div>`;
        return;
    }
    
    let html = `<div class="ai-studio-grid">`;
    filteredProjects.forEach((project, index) => {
        const delay = (index * 0.08) + 's';
        
        let tagsHtml = '';
        if (project.techStack && project.techStack.length > 0) {
            tagsHtml = `<div class="studio-tags">`;
            project.techStack.forEach(tag => {
                tagsHtml += `<span class="tech-badge">${tag}</span>`;
            });
            tagsHtml += `</div>`;
        }
        
        let demoUrl = project.links && project.links.liveDemo ? project.links.liveDemo : '#';
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            if (demoUrl.includes('streamlit.app/')) {
                const path = demoUrl.split('streamlit.app/')[1] || '';
                demoUrl = `http://localhost:8501/${path}`;
            }
        }
        
        const iconClass = project.icon || 'fa-code';
        const iconBoxHtml = `<span class="card-icon-box"><i class="fa-solid ${iconClass}"></i></span>`;
        const titleTextHtml = `<span class="card-title-text">${project.title}</span>`;
        
        let linksHtml = `<div class="studio-actions">`;
        if (demoUrl !== '#') {
            linksHtml += `
                <a href="${demoUrl}" target="_blank" rel="noopener noreferrer" class="action-icon-link" title="前往開啟專案">
                    <i class="fa-solid fa-rocket"></i> 前往開啟專案
                </a>
            `;
        }
        linksHtml += `</div>`;

        let impactHtml = '';
        if (project.businessImpact) {
            impactHtml = `<div class="business-impact">${project.businessImpact}</div>`;
        }

        html += `
            <article class="studio-card anim-target" data-anim="slide-up" style="animation-delay: ${delay}">
                <h3>${iconBoxHtml}${titleTextHtml}</h3>
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

function initFilterHandlers(projects) {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = btn.getAttribute('data-filter');
            renderAiStudio(projects);
            triggerAnimations();
        });
    });
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
        threshold: 0.1
    });

    document.querySelectorAll('.anim-target').forEach(el => {
        observer.observe(el);
    });
}
