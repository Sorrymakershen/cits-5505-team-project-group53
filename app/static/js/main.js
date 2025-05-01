/**
 * Main JavaScript functionality for the Travel Planning Platform
 * Provides DOM manipulation, AJAX requests, and UI enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all Bootstrap tooltips
    initTooltips();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize animations
    initAnimations();
    
    // Initialize enhanced UI features
    initEnhancedUI();
    
    // Initialize interactive features
    initInteractiveFeatures();
    
    // Initialize theme preferences
    initThemePreferences();
    
    // Initialize lazy loading
    initLazyLoading();
    
    // Initialize CSRF token for AJAX requests
    initCsrfProtection();
    
    // Initialize optimized interactive animations
    optimizeInteractiveAnimations();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    // Add form validation logic here
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // NEW: Enhanced real-time validation feedback
    document.querySelectorAll('input, textarea, select').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.checkValidity()) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            } else if (this.value !== '') {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            }
        });
        
        input.addEventListener('input', function() {
            if (this.checkValidity()) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            }
        });
    });
}

/**
 * Initialize animations for page elements with optimized performance
 */
function initAnimations() {
    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
        // Respect user preference and disable animations
        document.documentElement.classList.add('reduced-motion');
        return;
    }
    
    // Animate elements when they come into view
    const animatedElements = document.querySelectorAll('.animate');
    
    if (animatedElements.length > 0) {
        // Check if Intersection Observer is supported
        if ('IntersectionObserver' in window) {
            // Use optimized options for Intersection Observer
            const observerOptions = {
                root: null,
                rootMargin: '0px 0px 50px 0px', // Pre-load animations before they're visible
                threshold: 0.1
            };
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // Use requestAnimationFrame for smoother animation triggering
                        requestAnimationFrame(() => {
                            entry.target.classList.add('fade-in');
                            
                            // Set timeout to clean up animations after they're complete
                            const animationDuration = getComputedStyle(entry.target).animationDuration;
                            const durationMs = parseFloat(animationDuration) * 1000;
                            
                            setTimeout(() => {
                                entry.target.classList.add('animation-complete');
                                entry.target.style.willChange = 'auto'; // Release GPU resources
                            }, durationMs);
                        });
                        
                        observer.unobserve(entry.target);
                    }
                });
            }, observerOptions);
            
            // Batch DOM reads/writes for better performance
            const elementsToObserve = [];
            
            animatedElements.forEach(element => {
                // Prepare elements before observation
                element.style.willChange = 'opacity, transform';
                elementsToObserve.push(element);
            });
            
            // Use requestIdleCallback if available for non-critical animations
            if ('requestIdleCallback' in window) {
                requestIdleCallback(() => {
                    elementsToObserve.forEach(element => observer.observe(element));
                }, { timeout: 1000 });
            } else {
                // Fallback to setTimeout with a minimal delay
                setTimeout(() => {
                    elementsToObserve.forEach(element => observer.observe(element));
                }, 10);
            }
        } else {
            // Fallback for browsers that don't support Intersection Observer
            // Apply animations with a staggered delay to prevent jank
            animatedElements.forEach((element, index) => {
                setTimeout(() => {
                    element.classList.add('fade-in');
                }, index * 50); // Stagger by 50ms per element
            });
        }
    }
    
    // Optimize staggered animation for lists and grids
    document.querySelectorAll('.staggered-animation').forEach(container => {
        const items = Array.from(container.children);
        const batchSize = 5; // Process animations in batches
        
        // Apply optimizations only if there are enough items
        if (items.length > 10) {
            // Use animation batching for large collections
            for (let i = 0; i < items.length; i += batchSize) {
                const batch = items.slice(i, i + batchSize);
                
                // Stagger batch animations
                setTimeout(() => {
                    requestAnimationFrame(() => {
                        batch.forEach((item, index) => {
                            item.style.animationDelay = `${(i + index) * 0.05}s`;
                            item.classList.add('animate', 'fade-in');
                        });
                    });
                }, i * 10); // Small delay between batches
            }
        } else {
            // For smaller collections, use standard approach with optimized delays
            items.forEach((item, index) => {
                item.style.animationDelay = `${index * 0.075}s`; // Slightly faster animation sequence
                item.classList.add('animate', 'fade-in');
            });
        }
    });
    
    // Add device performance awareness
    detectLowPowerMode();
}

/**
 * Detect if device is in low power mode or has low performance
 * and adapt animations accordingly
 */
function detectLowPowerMode() {
    // Check if device is in low power mode (iOS)
    const isLowPower = window.navigator.getBattery ? 
        window.navigator.getBattery().then(battery => battery.dischargingTime < 3600) : 
        false;
    
    // Check for low memory conditions
    const isLowMemory = navigator.deviceMemory && navigator.deviceMemory < 4;
    
    // Check for low CPU cores
    const isLowCPU = navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4;
    
    // Create performance score
    Promise.resolve(isLowPower).then(lowPower => {
        if (lowPower || isLowMemory || isLowCPU) {
            // Apply simpler animations for low-power devices
            document.documentElement.classList.add('low-performance-device');
            
            // Reduce number of animated elements
            const animatedElements = document.querySelectorAll('.animate:not(.important)');
            animatedElements.forEach(el => {
                el.classList.remove('animate');
                el.style.opacity = 1;
            });
            
            // Simplify existing animations
            document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right').forEach(el => {
                el.style.animationDuration = '0.3s';
            });
        }
    });
}

/**
 * Initialize enhanced UI features
 */
function initEnhancedUI() {
    // Add hover effects to cards
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('card-hover');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('card-hover');
        });
    });
    
    // NEW: Add scroll to top button
    addScrollToTopButton();
    
    // NEW: Add custom context menu for images
    addCustomImageContextMenu();
    
    // NEW: Add smooth scrolling for anchor links
    enableSmoothScrolling();
    
    // 删除了加载指示器 - enableLoadingIndicator();
}

/**
 * Add scroll to top button
 */
function addScrollToTopButton() {
    // Create button if it doesn't exist
    if (!document.getElementById('scroll-top-btn')) {
        const scrollTopBtn = document.createElement('button');
        scrollTopBtn.id = 'scroll-top-btn';
        scrollTopBtn.className = 'btn btn-primary rounded-circle position-fixed bottom-0 end-0 mb-4 me-4';
        scrollTopBtn.style.width = '45px';
        scrollTopBtn.style.height = '45px';
        scrollTopBtn.style.zIndex = '1000';
        scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
        
        document.body.appendChild(scrollTopBtn);
        
        // Add click event
        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
        
        // Show/hide button based on scroll position
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                scrollTopBtn.classList.add('show');
            } else {
                scrollTopBtn.classList.remove('show');
            }
        });
    }
}

/**
 * Add custom context menu for images
 */
function addCustomImageContextMenu() {
    const images = document.querySelectorAll('.gallery-item img, .memory-img');
    
    images.forEach(img => {
        img.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            
            // Remove any existing context menus
            const existingMenu = document.querySelector('.custom-context-menu');
            if (existingMenu) {
                existingMenu.remove();
            }
            
            // Create custom context menu
            const menu = document.createElement('div');
            menu.className = 'custom-context-menu card shadow';
            menu.style.position = 'fixed';
            menu.style.zIndex = '9999';
            menu.style.top = e.pageY + 'px';
            menu.style.left = e.pageX + 'px';
            menu.style.padding = '0.5rem 0';
            menu.style.minWidth = '150px';
            
            // Add menu items
            const actions = [
                { text: 'View Image', icon: 'fa-eye', action: () => window.open(this.src, '_blank') },
                { text: 'Download', icon: 'fa-download', action: () => downloadImage(this.src) },
                { text: 'Share', icon: 'fa-share-alt', action: () => shareImage(this.src) }
            ];
            
            actions.forEach(action => {
                const item = document.createElement('div');
                item.className = 'px-3 py-2 d-flex align-items-center';
                item.style.cursor = 'pointer';
                item.innerHTML = `<i class="fas ${action.icon} me-2 text-primary"></i> ${action.text}`;
                item.addEventListener('click', action.action);
                item.addEventListener('mouseenter', () => item.style.backgroundColor = '#f8f9fa');
                item.addEventListener('mouseleave', () => item.style.backgroundColor = '');
                
                menu.appendChild(item);
            });
            
            document.body.appendChild(menu);
            
            // Close menu when clicking outside
            document.addEventListener('click', function closeMenu() {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            });
        });
    });
}

/**
 * Download an image
 * @param {string} src - Image source URL
 */
function downloadImage(src) {
    const a = document.createElement('a');
    a.href = src;
    a.download = src.split('/').pop();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

/**
 * Share an image
 * @param {string} src - Image source URL
 */
function shareImage(src) {
    if (navigator.share) {
        navigator.share({
            title: 'Shared Image',
            text: 'Check out this image from my travel memories!',
            url: src
        }).catch(err => {
            console.error('Share failed:', err);
        });
    } else {
        // Fallback for browsers that don't support Web Share API
        // You could show a modal with share options
        alert('Sharing is not supported in your browser');
    }
}

/**
 * Enable smooth scrolling for anchor links
 */
function enableSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update URL hash without jumping
                history.pushState(null, null, targetId);
            }
        });
    });
}

/**
 * Initialize interactive features
 */
function initInteractiveFeatures() {
    // Image galleries
    initImageGalleries();
    
    // NEW: Interactive rating stars
    initRatingStars();
    
    // NEW: Interactive tags
    initInteractiveTags();
    
    // NEW: Text truncation
    initTextTruncation();
}

/**
 * Initialize image galleries
 */
function initImageGalleries() {
    // Check for lightbox gallery
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    if (galleryItems.length > 0) {
        galleryItems.forEach(item => {
            item.addEventListener('click', function() {
                const img = this.querySelector('img');
                if (img) {
                    openImageModal(img.src, img.alt);
                }
            });
        });
    }
}

/**
 * Open an image in a modal lightbox
 * @param {string} src - Image source URL
 * @param {string} alt - Image alt text
 */
function openImageModal(src, alt) {
    // Create modal if it doesn't exist
    if (!document.getElementById('image-modal')) {
        const modalHtml = `
            <div class="modal fade" id="image-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header border-0 pb-0">
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body text-center p-0">
                            <img id="modal-image" class="img-fluid" alt="" style="max-height: 80vh;">
                        </div>
                        <div class="modal-footer border-0 pt-0">
                            <p id="modal-caption" class="text-center w-100 mb-0"></p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
    
    // Update modal content
    const modalImage = document.getElementById('modal-image');
    const modalCaption = document.getElementById('modal-caption');
    
    modalImage.src = src;
    modalCaption.textContent = alt || '';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('image-modal'));
    modal.show();
}

/**
 * Initialize rating stars
 */
function initRatingStars() {
    const ratingContainers = document.querySelectorAll('.rating-input');
    
    ratingContainers.forEach(container => {
        const stars = container.querySelectorAll('i');
        const input = container.querySelector('input[type="hidden"]');
        
        stars.forEach((star, index) => {
            // Set initial state
            if (input.value >= index + 1) {
                star.classList.remove('far');
                star.classList.add('fas');
            }
            
            // Add click event
            star.addEventListener('click', function() {
                const rating = index + 1;
                input.value = rating;
                
                // Update stars
                stars.forEach((s, i) => {
                    if (i < rating) {
                        s.classList.remove('far');
                        s.classList.add('fas');
                    } else {
                        s.classList.remove('fas');
                        s.classList.add('far');
                    }
                });
                
                // Trigger change event
                input.dispatchEvent(new Event('change'));
            });
            
            // Add hover effect
            star.addEventListener('mouseenter', function() {
                stars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.remove('far');
                        s.classList.add('fas');
                    }
                });
            });
            
            star.addEventListener('mouseleave', function() {
                const rating = parseInt(input.value, 10) || 0;
                
                stars.forEach((s, i) => {
                    if (i < rating) {
                        s.classList.remove('far');
                        s.classList.add('fas');
                    } else {
                        s.classList.remove('fas');
                        s.classList.add('far');
                    }
                });
            });
        });
    });
}

/**
 * Initialize interactive tags
 */
function initInteractiveTags() {
    const tags = document.querySelectorAll('.tag');
    
    tags.forEach(tag => {
        // Add click animation
        tag.addEventListener('click', function() {
            this.classList.add('tag-click');
            setTimeout(() => {
                this.classList.remove('tag-click');
            }, 300);
        });
    });
    
    // NEW: Filter by tag functionality (if on appropriate page)
    const tagFilter = document.getElementById('tag-filter');
    if (tagFilter) {
        tags.forEach(tag => {
            tag.addEventListener('click', function() {
                const tagValue = this.textContent.trim();
                tagFilter.value = tagValue;
                const form = tagFilter.closest('form');
                if (form) form.submit();
            });
        });
    }
}

/**
 * Initialize automatic text truncation
 */
function initTextTruncation() {
    document.querySelectorAll('.truncate-text').forEach(element => {
        const originalText = element.textContent;
        const maxLength = parseInt(element.getAttribute('data-max-length')) || 100;
        
        if (originalText.length > maxLength) {
            const truncatedText = originalText.substring(0, maxLength) + '...';
            element.textContent = truncatedText;
            
            // Add expand/collapse functionality
            const toggle = document.createElement('span');
            toggle.className = 'text-primary ms-1 cursor-pointer';
            toggle.textContent = 'Read more';
            toggle.style.cursor = 'pointer';
            
            toggle.addEventListener('click', function() {
                if (element.textContent.includes('...')) {
                    element.textContent = originalText;
                    toggle.textContent = 'Show less';
                } else {
                    element.textContent = truncatedText;
                    toggle.textContent = 'Read more';
                }
                element.appendChild(toggle);
            });
            
            element.appendChild(toggle);
        }
    });
}

/**
 * Initialize theme preferences - Dark mode functionality removed
 */
function initThemePreferences() {
    // All dark mode toggle functionality has been removed
    // Setting default theme to light
    document.body.setAttribute('data-bs-theme', 'light');
}

/**
 * Initialize lazy loading for images
 */
function initLazyLoading() {
    // Check if native lazy loading is supported
    if ('loading' in HTMLImageElement.prototype) {
        // Use native lazy loading
        document.querySelectorAll('img.lazy').forEach(img => {
            img.loading = 'lazy';
            if (img.dataset.src) {
                img.src = img.dataset.src;
                delete img.dataset.src;
            }
        });
    } else {
        // Fallback to Intersection Observer
        if ('IntersectionObserver' in window) {
            const lazyImageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const lazyImage = entry.target;
                        if (lazyImage.dataset.src) {
                            lazyImage.src = lazyImage.dataset.src;
                            lazyImage.classList.remove('lazy');
                            lazyImageObserver.unobserve(lazyImage);
                        }
                    }
                });
            });
            
            document.querySelectorAll('img.lazy').forEach(lazyImage => {
                lazyImageObserver.observe(lazyImage);
            });
        } else {
            // Fallback for older browsers
            document.querySelectorAll('img.lazy').forEach(img => {
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    delete img.dataset.src;
                }
            });
        }
    }
}

/**
 * Initialize CSRF protection for AJAX requests
 * This adds the CSRF token to all fetch() and XMLHttpRequest calls
 */
function initCsrfProtection() {
    // Get CSRF token from the meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    if (!csrfToken) {
        console.warn('CSRF token not found. AJAX requests requiring CSRF protection may fail.');
        return;
    }
    
    // Store CSRF token for later use
    window.csrfToken = csrfToken;
    
    // Add CSRF token to all fetch() requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Only modify POST, PUT, DELETE requests (not GET or HEAD)
        if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
            if (!options.headers) {
                options.headers = {};
            }
            
            // Convert headers object to Headers instance if it's not already
            if (!(options.headers instanceof Headers)) {
                options.headers = new Headers(options.headers);
            }
            
            // Add CSRF token header if not already present
            if (!options.headers.has('X-CSRFToken')) {
                options.headers.set('X-CSRFToken', csrfToken);
            }
        }
        
        return originalFetch(url, options);
    };
    
    // Also add CSRF token to any XMLHttpRequest (for backward compatibility)
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        originalOpen.apply(this, arguments);
        
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
            this.setRequestHeader('X-CSRFToken', csrfToken);
        }
    };
}

/**
 * Create and show a toast notification
 * @param {string} title - Notification title
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning, info)
 * @param {number} duration - Duration in ms before toast auto-hides
 */
function showToast(title, message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1090';
        document.body.appendChild(toastContainer);
    }
    
    // Get icon based on type
    let icon;
    switch (type) {
        case 'success':
            icon = 'fa-check-circle text-success';
            break;
        case 'error':
            icon = 'fa-exclamation-circle text-danger';
            break;
        case 'warning':
            icon = 'fa-exclamation-triangle text-warning';
            break;
        default:
            icon = 'fa-info-circle text-info';
    }
    
    // Create toast
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="fas ${icon} me-2"></i>
                <strong class="me-auto">${title}</strong>
                <small>Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: duration });
    toast.show();
    
    // Remove toast from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Optimize interactive animations for memory cards and itinerary items
 * This enhances the responsiveness and smoothness of frequently interacted elements
 */
function optimizeInteractiveAnimations() {
    // Add more fluid card animations with hardware acceleration
    document.querySelectorAll('.memory-card, .plan-card, .itinerary-item').forEach(card => {
        // Add hardware acceleration hints
        card.style.willChange = 'transform, opacity';
        card.style.transform = 'translateZ(0)';
        
        // Use passive event listeners for better scroll performance
        card.addEventListener('mouseenter', () => {
            requestAnimationFrame(() => {
                card.classList.add('interaction-hover');
            });
        }, { passive: true });
        
        card.addEventListener('mouseleave', () => {
            requestAnimationFrame(() => {
                card.classList.remove('interaction-hover');
            });
        }, { passive: true });
        
        // Add touch interaction support for mobile
        card.addEventListener('touchstart', () => {
            requestAnimationFrame(() => {
                card.classList.add('interaction-active');
            });
        }, { passive: true });
        
        card.addEventListener('touchend', () => {
            requestAnimationFrame(() => {
                card.classList.remove('interaction-active');
                // Add a small "out" animation
                card.classList.add('interaction-touch-end');
                setTimeout(() => {
                    card.classList.remove('interaction-touch-end');
                }, 300);
            });
        }, { passive: true });
    });
    
    // Optimize image hover effects
    document.querySelectorAll('.gallery-item img, .card-img-top').forEach(img => {
        img.style.willChange = 'transform';
        img.style.transition = 'transform 0.3s cubic-bezier(0.23, 1, 0.32, 1)';
        
        // Use a more efficient transform for hover
        const parent = img.closest('.gallery-item') || img.closest('.memory-card');
        if (parent) {
            parent.addEventListener('mouseenter', () => {
                requestAnimationFrame(() => {
                    img.style.transform = 'scale3d(1.05, 1.05, 1)';
                });
            }, { passive: true });
            
            parent.addEventListener('mouseleave', () => {
                requestAnimationFrame(() => {
                    img.style.transform = 'scale3d(1, 1, 1)';
                });
            }, { passive: true });
        }
    });
    
    // Optimize button click animations
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('mousedown', () => {
            requestAnimationFrame(() => {
                button.style.transform = 'scale3d(0.98, 0.98, 1)';
            });
        }, { passive: true });
        
        button.addEventListener('mouseup', () => {
            requestAnimationFrame(() => {
                button.style.transform = 'scale3d(1, 1, 1)';
            });
        }, { passive: true });
        
        button.addEventListener('mouseleave', () => {
            if (button.style.transform !== 'scale3d(1, 1, 1)') {
                requestAnimationFrame(() => {
                    button.style.transform = 'scale3d(1, 1, 1)';
                });
            }
        }, { passive: true });
    });
    
    // Optimize rating stars interaction
    optimizeRatingInteraction();
    
    // Debounce scroll handlers for better performance
    optimizeScrollHandlers();
}

/**
 * Optimize rating stars interaction for smoother animation
 */
function optimizeRatingInteraction() {
    document.querySelectorAll('.rating-stars').forEach(container => {
        const stars = container.querySelectorAll('i');
        
        stars.forEach((star, index) => {
            star.style.willChange = 'transform';
            
            // Use efficient transform animation
            star.addEventListener('mouseenter', () => {
                requestAnimationFrame(() => {
                    // Apply transform to current and previous stars
                    for (let i = 0; i <= index; i++) {
                        stars[i].style.transform = 'scale3d(1.3, 1.3, 1)';
                        stars[i].style.color = '#ffc107'; // Make yellow
                    }
                });
            }, { passive: true });
            
            container.addEventListener('mouseleave', () => {
                requestAnimationFrame(() => {
                    // Reset all stars
                    stars.forEach(s => {
                        s.style.transform = 'scale3d(1, 1, 1)';
                        // Color will be managed by the existing class system
                    });
                });
            }, { passive: true });
        });
    });
}

/**
 * Optimize scroll event handlers using requestAnimationFrame
 */
function optimizeScrollHandlers() {
    // Replace any direct scroll handlers with debounced versions
    const scrollHandlers = {};
    
    // Store original handler
    const originalScrollHandler = window.onscroll;
    
    // Optimized scroll handler using requestAnimationFrame
    window.onscroll = function() {
        // Call original handler if it exists
        if (originalScrollHandler && typeof originalScrollHandler === 'function') {
            if (!scrollHandlers.original) {
                scrollHandlers.original = debounce(originalScrollHandler, 10);
            }
            scrollHandlers.original();
        }
        
        // Handle scroll-to-top button visibility
        const scrollTopBtn = document.getElementById('scroll-top-btn');
        if (scrollTopBtn) {
            if (!scrollHandlers.scrollTopBtn) {
                scrollHandlers.scrollTopBtn = debounce(() => {
                    if (window.pageYOffset > 300) {
                        scrollTopBtn.classList.add('show');
                    } else {
                        scrollTopBtn.classList.remove('show');
                    }
                }, 50);
            }
            scrollHandlers.scrollTopBtn();
        }
    };
}

/**
 * Create a debounced function that delays invoking func until after wait milliseconds
 * @param {Function} func - The function to debounce
 * @param {number} wait - Milliseconds to wait before invoking
 * @returns {Function} - Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

/**
 * Create a throttled function that only invokes func at most once per animation frame
 * @param {Function} func - The function to throttle
 * @returns {Function} - Throttled function
 */
function throttleAnimationFrame(func) {
    let scheduled = false;
    return function() {
        const context = this;
        const args = arguments;
        
        if (!scheduled) {
            scheduled = true;
            requestAnimationFrame(() => {
                func.apply(context, args);
                scheduled = false;
            });
        }
    };
}

// Export functions for use in other modules
window.travelApp = {
    showToast: showToast,
    openImageModal: openImageModal
};