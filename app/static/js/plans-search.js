/**
 * Travel Plans Search
 * Provides real-time search functionality for travel plans
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize plans search if we're on the plans page
    if (document.querySelector('.plans-container')) {
        initPlansSearch();
    }
});

/**
 * Initialize plans search functionality
 */
function initPlansSearch() {
    // Get search form elements
    const searchInput = document.querySelector('#plan-search-input');
    const searchForm = document.querySelector('#plan-search-form');
    
    if (!searchInput || !searchForm) return;
    
    // Add event listener to form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        searchPlans(searchInput.value);
    });
    
    // Add event listener to input for real-time search
    searchInput.addEventListener('keyup', debounce(function() {
        searchPlans(searchInput.value);
    }, 500)); // 500ms delay to avoid too many requests while typing
    
    // Handle destination filter dropdown
    const destinationFilters = document.querySelectorAll('.destination-filter');
    destinationFilters.forEach(filter => {
        filter.addEventListener('click', function(e) {
            e.preventDefault();
            const destination = this.getAttribute('data-destination');
            searchInput.value = destination;
            searchPlans(destination);
        });
    });
    
    // Handle date range filters
    const dateFilters = document.querySelectorAll('.date-filter');
    dateFilters.forEach(filter => {
        filter.addEventListener('click', function(e) {
            e.preventDefault();
            const dateRange = this.getAttribute('data-range');
            document.querySelector('#date-range').value = dateRange;
            searchPlans(searchInput.value);
        });
    });
    
    // Clear search button
    const clearSearchBtn = document.querySelector('#clear-search');
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            searchInput.value = '';
            document.querySelector('#date-range').value = '';
            searchPlans('');
        });
    }
}

/**
 * Search plans in real-time with entered query
 * @param {string} query - The search query
 */
function searchPlans(query) {
    // Get the plans container
    const plansContainer = document.querySelector('.plans-container');
    if (!plansContainer) return;
    
    // Show loading state
    plansContainer.classList.add('loading');
    
    // Get additional filters
    const dateRange = document.querySelector('#date-range')?.value || '';
    const sortBy = document.querySelector('#sort-by')?.value || '';
    
    // Build query params
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (dateRange) params.append('date_range', dateRange);
    if (sortBy) params.append('sort', sortBy);
    params.append('xhr', 'true');
    
    // Update URL with search parameters without reload
    const url = new URL(window.location);
    url.search = params.toString().replace('xhr=true&', '').replace('&xhr=true', '');
    window.history.pushState({}, '', url);
    
    // Send AJAX request to search plans
    fetch(`/planner/search?${params.toString()}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updatePlansDisplay(data.plans, data.total_count, query);
        })
        .catch(error => {
            console.error('Error searching plans:', error);
            plansContainer.classList.remove('loading');
            plansContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error searching plans. Please try again.
                </div>
            `;
        });
}

/**
 * Update the plans display with search results
 * @param {Array} plans - The filtered plans data
 * @param {number} totalCount - Total number of matching plans
 * @param {string} query - The search query
 */
function updatePlansDisplay(plans, totalCount, query) {
    const plansContainer = document.querySelector('.plans-container');
    if (!plansContainer) return;
    
    plansContainer.classList.remove('loading');
    
    // Update search results count
    const resultsCount = document.querySelector('#search-results-count');
    if (resultsCount) {
        if (query) {
            resultsCount.textContent = `${totalCount} result${totalCount !== 1 ? 's' : ''} for "${query}"`;
            resultsCount.style.display = 'block';
        } else {
            resultsCount.style.display = 'none';
        }
    }
    
    if (plans.length === 0) {
        plansContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="empty-state">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h4>No travel plans found</h4>
                    <p class="text-muted">Try adjusting your search or <a href="#" id="clear-search">clear the search</a>.</p>
                </div>
            </div>
        `;
        
        // Attach event listener to the new clear search link
        const clearLink = document.querySelector('#clear-search');
        if (clearLink) {
            clearLink.addEventListener('click', function(e) {
                e.preventDefault();
                const searchInput = document.querySelector('#plan-search-input');
                if (searchInput) {
                    searchInput.value = '';
                    searchPlans('');
                }
            });
        }
        
        return;
    }
    
    // Build the HTML for each plan
    let plansHTML = '';
    plans.forEach((plan, index) => {
        // Format dates
        const startDate = new Date(plan.start_date);
        const endDate = new Date(plan.end_date);
        const createdAt = new Date(plan.created_at);
        
        const startFormatted = startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const endFormatted = endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        const createdFormatted = createdAt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        
        plansHTML += `
            <div class="col-md-6 col-lg-4 animate fade-in" style="animation-delay: ${index * 0.1}s;">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="card-title mb-0">${plan.title}</h5>
                            ${plan.is_public ? '<span class="badge bg-info">Public</span>' : ''}
                        </div>
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-map-marker-alt text-danger me-2"></i>
                            <span>${plan.destination}</span>
                        </div>
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-calendar text-primary me-2"></i>
                            <span>${startFormatted} - ${endFormatted}</span>
                        </div>
                        <div class="d-flex align-items-center mb-3">
                            <i class="fas fa-money-bill-wave text-success me-2"></i>
                            <span>Budget: $${plan.budget}</span>
                        </div>
                        <p class="card-text small text-muted mb-3">
                            ${plan.interests ? plan.interests.substring(0, 100) + (plan.interests.length > 100 ? '...' : '') : 'No interests specified'}
                        </p>
                        <div class="d-flex align-items-center small text-muted mb-3">
                            <i class="fas fa-clock me-2"></i>
                            <span>Created ${createdFormatted}</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <a href="/planner/view/${plan.id}" class="btn btn-primary btn-sm">
                                <i class="fas fa-eye me-1"></i> View
                            </a>
                            <a href="/planner/edit/${plan.id}" class="btn btn-outline-secondary btn-sm">
                                <i class="fas fa-edit me-1"></i> Edit
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    plansContainer.innerHTML = `<div class="row g-4">${plansHTML}</div>`;
}

/**
 * Debounce function to limit how often a function can be called
 * @param {Function} func - The function to debounce
 * @param {number} wait - The debounce wait time in milliseconds
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
