/**
 * v2_executive_theme - Main Script
 */

 document.addEventListener('DOMContentLoaded', () => {
    // 1. Header Scroll Effect
    const header = document.getElementById('header');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // 2. Smooth Scrolling for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                // Offset for fixed header
                const headerHeight = header.offsetHeight;
                const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // Update active state in nav
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                if(this.classList.contains('nav-link')) {
                    this.classList.add('active');
                }
            }
        });
    });

    // 3. Simple Form Handling (Prevent default and show alert for demo)
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // In a real application, you would gather form data and send it via fetch/XHR
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            // Visual feedback
            submitBtn.textContent = '傳送中...';
            submitBtn.style.opacity = '0.8';
            submitBtn.disabled = true;
            
            // Simulate API call
            setTimeout(() => {
                submitBtn.textContent = '送出成功！';
                submitBtn.style.backgroundColor = '#10B981'; // Success green
                submitBtn.style.color = '#FFFFFF';
                
                // Reset form
                contactForm.reset();
                
                // Reset button after 3 seconds
                setTimeout(() => {
                    submitBtn.textContent = originalText;
                    submitBtn.style.backgroundColor = '';
                    submitBtn.style.color = '';
                    submitBtn.style.opacity = '1';
                    submitBtn.disabled = false;
                }, 3000);
                
            }, 1500);
        });
    }

    // 4. Numbers Animation (Intersection Observer for Stats)
    const animateValue = (obj, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start) + (obj.dataset.suffix || '');
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    };

    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const h4s = entry.target.querySelectorAll('.stat-item h4');
                h4s.forEach(h4 => {
                    // Extract number and suffix
                    const text = h4.innerText;
                    const numberMatch = text.match(/\d+/);
                    if (numberMatch) {
                        const endValue = parseInt(numberMatch[0]);
                        const suffix = text.replace(numberMatch[0], '');
                        
                        h4.dataset.suffix = suffix;
                        // Avoid re-animating
                        if (!h4.classList.contains('animated')) {
                            animateValue(h4, 0, endValue, 2000);
                            h4.classList.add('animated');
                        }
                    }
                });
            }
        });
    }, { threshold: 0.5 });

    const statsContainer = document.querySelector('.stats-container');
    if (statsContainer) {
        statsObserver.observe(statsContainer);
    }
});
