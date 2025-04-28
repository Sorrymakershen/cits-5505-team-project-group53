/**
 * Main JavaScript functionality for the Travel Planning Platform
 * Provides DOM manipulation, AJAX requests, and UI enhancements
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips and popovers
    initTooltipsAndPopovers();
    
    // Initialize animation on scroll
    initScrollAnimation();
    
    // Initialize dynamic content loaders
    initDynamicLoaders();
    
    // Initialize notifications system
    initNotifications();
});

/**
 * Initialize Bootstrap tooltips and popovers
 */
function initTooltipsAndPopovers() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
}

/**
 * Initialize animation effects for elements when they enter the viewport
 */
function initScrollAnimation() {
    const animatedElements = document.querySelectorAll('.animate');
    
    if (animatedElements.length === 0) return;
    
    // Check if element is in viewport and add animation class
    const checkViewport = () => {
        animatedElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const isInViewport = (
                rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.bottom >= 0
            );
            
            if (isInViewport) {
                element.classList.add('animated');
            }
        });
    };
    
    // Run on scroll
    window.addEventListener('scroll', checkViewport);
    
    // Initial check
    checkViewport();
}

/**
 * Initialize lazy loading of dynamic content via AJAX
 */
function initDynamicLoaders() {
    const dynamicLoaders = document.querySelectorAll('[data-load-url]');
    
    dynamicLoaders.forEach(loader => {
        const url = loader.getAttribute('data-load-url');
        const triggerType = loader.getAttribute('data-load-trigger') || 'immediately';
        
        const loadContent = () => {
            // Show loading indicator
            loader.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading content...</p>
                </div>
            `;
            
            // Fetch the content
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    // Fade out current content
                    loader.style.opacity = 0;
                    
                    // After fade out, update content and fade in
                    setTimeout(() => {
                        loader.innerHTML = html;
                        loader.style.opacity = 1;
                        
                        // Reinitialize any components within the loaded content
                        initTooltipsAndPopovers();
                    }, 300);
                })
                .catch(error => {
                    loader.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            Failed to load content. Please try again.
                        </div>
                    `;
                    console.error('Error loading dynamic content:', error);
                });
        };
        
        // Trigger based on the specified method
        if (triggerType === 'immediately') {
            loadContent();
        } else if (triggerType === 'visible') {
            // Create an intersection observer
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        loadContent();
                        observer.unobserve(loader);
                    }
                });
            });
            
            observer.observe(loader);
        } else if (triggerType === 'click') {
            const triggerBtn = document.createElement('button');
            triggerBtn.className = 'btn btn-outline-primary';
            triggerBtn.innerHTML = `<i class="fas fa-sync-alt me-2"></i> ${loader.getAttribute('data-load-text') || 'Load Content'}`;
            
            triggerBtn.addEventListener('click', loadContent);
            
            // Clear and append the button
            loader.innerHTML = '';
            loader.appendChild(triggerBtn);
        }
    });
}

/**
 * Fetch AI recommendations for travel planning
 * @param {string} containerId - ID of the container to populate with recommendations
 * @param {string} url - URL to fetch recommendations from
 */
function fetchRecommendations(containerId, url) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Show loading state
    container.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Generating personalized recommendations...</p>
        </div>
    `;
    
    // Fetch recommendations
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderRecommendations(container, data.recommendations);
            } else {
                showRecommendationError(container);
            }
        })
        .catch(error => {
            console.error('Error fetching recommendations:', error);
            showRecommendationError(container);
        });
}

/**
 * Render recommendations into the container
 * @param {HTMLElement} container - The container element
 * @param {Array} recommendations - Array of recommendation objects
 */
function renderRecommendations(container, recommendations) {
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Add more travel plans to receive personalized recommendations.
            </div>
        `;
        return;
    }
    
    let html = '';
    recommendations.forEach(rec => {
        // Set icon based on recommendation type
        let icon = 'lightbulb';
        if (rec.type === 'destination') icon = 'map-marker-alt';
        else if (rec.type === 'interest') icon = 'heart';
        else if (rec.type === 'habit') icon = 'calendar-check';
        
        html += `
            <div class="recommendation-card p-3 mb-3">
                <h5 class="mb-2">
                    <i class="fas fa-${icon} me-2 text-primary"></i>
                    ${rec.title}
                </h5>
                <p class="mb-0">${rec.description}</p>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Show error message when recommendations fail to load
 * @param {HTMLElement} container - The container element
 */
function showRecommendationError(container) {
    container.innerHTML = `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            Unable to load recommendations. Please try again later.
        </div>
    `;
}

/**
 * Initialize notifications system
 */
function initNotifications() {
    // Check for notification elements
    const notificationElements = document.querySelectorAll('.notification-toast');
    
    notificationElements.forEach(element => {
        const toast = new bootstrap.Toast(element, {
            autohide: true,
            delay: 5000
        });
        toast.show();
    });
    
    // Check for notification data in localStorage
    const notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
    
    if (notifications.length > 0) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        
        notifications.forEach((notification, index) => {
            const toastElement = document.createElement('div');
            toastElement.className = 'toast notification-toast';
            toastElement.setAttribute('role', 'alert');
            toastElement.setAttribute('aria-live', 'assertive');
            toastElement.setAttribute('aria-atomic', 'true');
            
            toastElement.innerHTML = `
                <div class="toast-header">
                    <i class="fas fa-bell text-primary me-2"></i>
                    <strong class="me-auto">${notification.title}</strong>
                    <small>${timeSince(new Date(notification.timestamp))}</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${notification.message}
                </div>
            `;
            
            container.appendChild(toastElement);
            
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: 5000
            });
            
            // Delay showing each toast
            setTimeout(() => {
                toast.show();
            }, index * 300);
            
            // Remove from storage when dismissed
            toastElement.addEventListener('hidden.bs.toast', () => {
                let notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
                notifications = notifications.filter(n => n.id !== notification.id);
                localStorage.setItem('notifications', JSON.stringify(notifications));
            });
        });
    }
}

/**
 * Add a new notification
 * @param {string} title - Notification title
 * @param {string} message - Notification message
 * @param {string} type - Notification type (info, success, warning, danger)
 */
function addNotification(title, message, type = 'info') {
    const notification = {
        id: Date.now(), // Unique identifier
        title,
        message,
        type,
        timestamp: new Date().toISOString()
    };
    
    // Save to localStorage
    let notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
    notifications.push(notification);
    localStorage.setItem('notifications', JSON.stringify(notifications));
    
    // Show immediately if page is open
    const container = document.querySelector('.toast-container') || (() => {
        const newContainer = document.createElement('div');
        newContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(newContainer);
        return newContainer;
    })();
    
    const toastElement = document.createElement('div');
    toastElement.className = 'toast notification-toast';
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    
    toastElement.innerHTML = `
        <div class="toast-header">
            <i class="fas fa-bell text-${type} me-2"></i>
            <strong class="me-auto">${title}</strong>
            <small>Just now</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    container.appendChild(toastElement);
    
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove from storage when dismissed
    toastElement.addEventListener('hidden.bs.toast', () => {
        let notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
        notifications = notifications.filter(n => n.id !== notification.id);
        localStorage.setItem('notifications', JSON.stringify(notifications));
    });
}

/**
 * Format a past date as a time ago string
 * @param {Date} date - The date to format
 * @returns {string} - Formatted time ago string
 */
function timeSince(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) {
        return Math.floor(interval) + " years ago";
    }
    
    interval = seconds / 2592000;
    if (interval > 1) {
        return Math.floor(interval) + " months ago";
    }
    
    interval = seconds / 86400;
    if (interval > 1) {
        return Math.floor(interval) + " days ago";
    }
    
    interval = seconds / 3600;
    if (interval > 1) {
        return Math.floor(interval) + " hours ago";
    }
    
    interval = seconds / 60;
    if (interval > 1) {
        return Math.floor(interval) + " minutes ago";
    }
    
    return "Just now";
}

/**
 * Fetch data for visualization
 * @param {string} url - The URL to fetch data from
 * @returns {Promise} - Promise resolving to the fetched data
 */
function fetchDataForVisualization(url) {
    return fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            throw error;
        });
}
