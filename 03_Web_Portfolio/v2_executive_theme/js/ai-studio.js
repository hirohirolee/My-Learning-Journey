/**
 * v2_executive_theme - AI Studio Specific Logic
 * Glassmorphism Streamlit Modal Viewer & Tag Filtering Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    fetchStudioDataAndRender();
    initModalHandlers();
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
        
        const demoUrl = project.links && project.links.liveDemo ? project.links.liveDemo : '#';
        const projectIcon = project.icon ? `<i class="fa-solid ${project.icon}"></i>` : `<i class="fa-solid fa-code"></i>`;
        
        let linksHtml = `<div class="studio-actions">`;
        if (demoUrl !== '#') {
            linksHtml += `
                <button class="action-btn-main open-modal-btn" data-url="${demoUrl}" data-title="${project.title}" data-icon="${project.icon || 'fa-rocket'}" data-desc="${project.description}">
                    <i class="fa-solid fa-play"></i> 即時體驗 (Live App)
                </button>
                <a href="${demoUrl}" target="_blank" rel="noopener noreferrer" class="action-icon" title="新分頁開啟">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i>
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
                <h3>${projectIcon} ${project.title}</h3>
                <p class="card-desc">${project.description}</p>
                ${impactHtml}
                ${tagsHtml}
                ${linksHtml}
            </article>
        `;
    });
    html += `</div>`;
    
    container.innerHTML = html;
    
    // Bind modal click events
    container.querySelectorAll('.open-modal-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const target = e.currentTarget;
            const url = target.getAttribute('data-url');
            const title = target.getAttribute('data-title');
            const icon = target.getAttribute('data-icon');
            const desc = target.getAttribute('data-desc');
            openStreamlitModal(url, title, icon, desc);
        });
    });
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

function initModalHandlers() {
    const modal = document.getElementById('streamlit-modal');
    const closeBtn = document.getElementById('modal-close-btn');
    const iframe = document.getElementById('streamlit-iframe');
    const loader = document.getElementById('modal-loader');
    const deviceBtns = document.querySelectorAll('.device-btn');
    const modalContainer = document.querySelector('.modal-container');
    
    if (!modal) return;
    
    // Close modal handlers
    closeBtn.addEventListener('click', closeStreamlitModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeStreamlitModal();
        }
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeStreamlitModal();
        }
    });
    
    // Device toggle
    deviceBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            deviceBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const device = btn.getAttribute('data-device');
            modalContainer.className = 'modal-container device-' + device;
        });
    });
    
    // Hide loader on iframe load
    if (iframe) {
        iframe.addEventListener('load', () => {
            if (loader) loader.style.display = 'none';
        });
    }
}

function openStreamlitModal(url, title, iconClass, desc) {
    const modal = document.getElementById('streamlit-modal');
    const iframe = document.getElementById('streamlit-iframe');
    const loader = document.getElementById('modal-loader');
    const titleEl = document.getElementById('modal-project-title');
    const descEl = document.getElementById('modal-project-desc');
    const iconEl = document.getElementById('modal-project-icon');
    const extLink = document.getElementById('modal-external-link');
    
    if (!modal || !iframe) return;
    
    if (titleEl) titleEl.textContent = title || 'Streamlit App';
    if (descEl) descEl.textContent = desc || 'Live Cloud Sandbox';
    if (iconEl) iconEl.innerHTML = `<i class="fa-solid ${iconClass || 'fa-rocket'}"></i>`;
    if (extLink) extLink.href = url;
    
    if (loader) loader.style.display = 'flex';
    iframe.src = url;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeStreamlitModal() {
    const modal = document.getElementById('streamlit-modal');
    const iframe = document.getElementById('streamlit-iframe');
    if (!modal) return;
    
    modal.style.display = 'none';
    if (iframe) iframe.src = '';
    document.body.style.overflow = '';
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
