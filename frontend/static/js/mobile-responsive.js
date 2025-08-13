// ===== MOBILE RESPONSIVE JAVASCRIPT =====
// Mobile-friendly interactions and navigation for KasiKash

document.addEventListener('DOMContentLoaded', function() {
    
    // Mobile menu functionality
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mobileOverlay = document.querySelector('.mobile-overlay');
    const body = document.body;
    
    // Create mobile menu toggle if it doesn't exist
    if (!mobileMenuToggle && sidebar) {
        const toggle = document.createElement('button');
        toggle.className = 'mobile-menu-toggle';
        toggle.innerHTML = '<i class="fas fa-bars"></i>';
        toggle.setAttribute('aria-label', 'Toggle mobile menu');
        document.body.appendChild(toggle);
        
        // Create mobile overlay if it doesn't exist
        if (!mobileOverlay) {
            const overlay = document.createElement('div');
            overlay.className = 'mobile-overlay';
            document.body.appendChild(overlay);
        }
    }
    
    // Mobile menu toggle functionality
    function toggleMobileMenu() {
        if (sidebar) {
            sidebar.classList.toggle('mobile-open');
            if (mobileOverlay) {
                mobileOverlay.classList.toggle('active');
            }
            body.classList.toggle('menu-open');
        }
    }
    
    // Event listeners for mobile menu
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
    }
    
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', toggleMobileMenu);
    }
    
    // Close mobile menu when clicking on nav links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 767) {
                toggleMobileMenu();
            }
        });
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 767) {
            if (sidebar) {
                sidebar.classList.remove('mobile-open');
            }
            if (mobileOverlay) {
                mobileOverlay.classList.remove('active');
            }
            body.classList.remove('menu-open');
        }
    });
    
    // Touch-friendly interactions
    function addTouchSupport() {
        // Add touch feedback to buttons and cards
        const touchElements = document.querySelectorAll('.btn, .card, .nav-link, .quick-action-btn');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
                this.style.transition = 'transform 0.1s ease';
            });
            
            element.addEventListener('touchend', function() {
                this.style.transform = 'scale(1)';
            });
            
            element.addEventListener('touchcancel', function() {
                this.style.transform = 'scale(1)';
            });
        });
    }
    
    // Form improvements for mobile
    function improveMobileForms() {
        const inputs = document.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Prevent zoom on iOS
            if (input.type !== 'file') {
                input.style.fontSize = '16px';
            }
            
            // Add better focus states
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
        });
    }
    
    // Table improvements for mobile
    function improveMobileTables() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            if (!table.parentElement.classList.contains('table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });
    }
    
    // Chart responsiveness
    function makeChartsResponsive() {
        const charts = document.querySelectorAll('.chart-container');
        
        charts.forEach(chart => {
            const resizeObserver = new ResizeObserver(entries => {
                entries.forEach(entry => {
                    const canvas = entry.target.querySelector('canvas');
                    if (canvas && canvas.chart) {
                        canvas.chart.resize();
                    }
                });
            });
            
            resizeObserver.observe(chart);
        });
    }
    
    // Modal improvements for mobile
    function improveMobileModals() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            // Prevent body scroll when modal is open
            modal.addEventListener('show.bs.modal', function() {
                body.style.overflow = 'hidden';
            });
            
            modal.addEventListener('hidden.bs.modal', function() {
                body.style.overflow = '';
            });
        });
    }
    
    // Swipe gestures for mobile
    function addSwipeSupport() {
        let startX, startY, endX, endY;
        
        document.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', function(e) {
            endX = e.changedTouches[0].clientX;
            endY = e.changedTouches[0].clientY;
            
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            // Swipe left to close mobile menu
            if (diffX > 50 && Math.abs(diffY) < 50 && sidebar && sidebar.classList.contains('mobile-open')) {
                toggleMobileMenu();
            }
            
            // Swipe right to open mobile menu
            if (diffX < -50 && Math.abs(diffY) < 50 && window.innerWidth <= 767 && sidebar && !sidebar.classList.contains('mobile-open')) {
                toggleMobileMenu();
            }
        });
    }
    
    // Lazy loading for images
    function addLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // Performance optimizations
    function optimizePerformance() {
        // Debounce resize events
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                // Handle resize logic here
            }, 250);
        });
        
        // Preload critical resources
        const criticalLinks = document.querySelectorAll('link[rel="preload"]');
        criticalLinks.forEach(link => {
            link.rel = 'stylesheet';
        });
    }
    
    // Accessibility improvements
    function improveAccessibility() {
        // Add skip links
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'sr-only sr-only-focusable';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            z-index: 1000;
            padding: 8px 16px;
            background: var(--primary-blue);
            color: white;
            text-decoration: none;
            border-radius: 4px;
        `;
        
        skipLink.addEventListener('focus', function() {
            this.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', function() {
            this.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Add main content landmark
        const mainContent = document.querySelector('.main-content, .admin-main, .dashboard-main');
        if (mainContent && !mainContent.id) {
            mainContent.id = 'main-content';
        }
        
        // Improve keyboard navigation
        const focusableElements = document.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');

        focusableElements.forEach(element => {
            element.addEventListener('keydown', function(e) {
                const tag = this.tagName.toLowerCase();
                const isTextInput = tag === 'input' || tag === 'textarea' || this.isContentEditable;
                if (isTextInput) return; // Do not hijack typing in inputs/textareas
                const isClickable = this.tagName === 'BUTTON' || this.getAttribute('role') === 'button' || this.dataset.keyclick === 'true' || this.hasAttribute('href');
                if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault();
                    this.click();
                }
            });
        });
    }
    
    // Initialize all mobile improvements
    function initMobileImprovements() {
        addTouchSupport();
        improveMobileForms();
        improveMobileTables();
        makeChartsResponsive();
        improveMobileModals();
        addSwipeSupport();
        addLazyLoading();
        optimizePerformance();
        improveAccessibility();
    }
    
    // Initialize when DOM is ready
    initMobileImprovements();
    
    // Handle orientation change
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            // Recalculate layouts after orientation change
            if (window.innerWidth > 767) {
                if (sidebar) {
                    sidebar.classList.remove('mobile-open');
                }
                if (mobileOverlay) {
                    mobileOverlay.classList.remove('active');
                }
            }
        }, 100);
    });
    
    // Service Worker registration for PWA capabilities
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/static/sw.js')
                .then(function(registration) {
                    console.log('SW registered: ', registration);
                })
                .catch(function(registrationError) {
                    console.log('SW registration failed: ', registrationError);
                });
        });
    }
    
    // Add loading states
    function addLoadingStates() {
        const buttons = document.querySelectorAll('.btn');
        
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                // Skip chat form send button to avoid blocking real-time send
                if (this.closest('#chat-form')) return;
                if (!this.classList.contains('loading')) {
                    this.classList.add('loading');
                    this.disabled = true;
                    
                    // Remove loading state after a delay (adjust as needed)
                    setTimeout(() => {
                        this.classList.remove('loading');
                        this.disabled = false;
                    }, 2000);
                }
            });
        });
    }
    
    // Add loading states
    addLoadingStates();
    
    // Handle offline/online status
    window.addEventListener('online', function() {
        document.body.classList.remove('offline');
        showNotification('You are back online!', 'success');
    });
    
    window.addEventListener('offline', function() {
        document.body.classList.add('offline');
        showNotification('You are currently offline', 'warning');
    });
    
    // Notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" aria-label="Close notification">×</button>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--primary-blue);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 300px;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
        
        // Close button functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });
    }
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .btn.loading {
            position: relative;
            color: transparent;
        }
        
        .btn.loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid transparent;
            border-top: 2px solid currentColor;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .offline .btn {
            opacity: 0.6;
            pointer-events: none;
        }
        
        .notification-close {
            background: none;
            border: none;
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            margin-left: 1rem;
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
    `;
    document.head.appendChild(style);
    
});

// Export functions for use in other scripts
window.MobileResponsive = {
    toggleMobileMenu: function() {
        const sidebar = document.querySelector('.sidebar');
        const mobileOverlay = document.querySelector('.mobile-overlay');
        const body = document.body;
        
        if (sidebar) {
            sidebar.classList.toggle('mobile-open');
            if (mobileOverlay) {
                mobileOverlay.classList.toggle('active');
            }
            body.classList.toggle('menu-open');
        }
    },
    
    showNotification: function(message, type = 'info') {
        // Implementation of showNotification function
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}; 