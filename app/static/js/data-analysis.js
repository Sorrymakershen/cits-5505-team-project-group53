/**
 * Data Analysis and Visualization Functions
 * Provides advanced data analysis and interactive visualizations for travel statistics
 */

/**
 * Initialize all data visualizations on the statistics page
 */
function initDataVisualizations() {
    // Initialize expense breakdown chart
    initExpenseChart();
    
    // NEW: Initialize monthly expenses chart
    initMonthlyExpensesChart();
    
    // NEW: Initialize trip duration distribution chart
    initDurationDistributionChart();
    
    // NEW: Initialize destination frequency chart
    initDestinationFrequencyChart();
    
    // Initialize travel timeline
    initTravelTimeline();
    
    // Initialize destination comparison
    initDestinationComparison();
    
    // Initialize travel heatmap if we have the data
    if (typeof travelData !== 'undefined' && travelData.destinations) {
        initTravelHeatmap(travelData.destinations);
    }
    
    // Initialize trend analysis
    initTrendAnalysis();
}

/**
 * Initialize expense breakdown chart using Chart.js
 */
function initExpenseChart() {
    const chartContainer = document.getElementById('expenseChart');
    if (!chartContainer) return;
    
    // Get data from the container's data attributes or fetch from API
    const dataSource = chartContainer.getAttribute('data-source');
    
    if (dataSource) {
        fetchDataForVisualization(dataSource)
            .then(data => {
                renderExpenseChart(chartContainer, data);
            })
            .catch(error => {
                chartContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load expense data
                    </div>
                `;
            });
    } else {
        // Use inline data if available
        const categories = JSON.parse(chartContainer.getAttribute('data-categories') || '[]');
        const values = JSON.parse(chartContainer.getAttribute('data-values') || '[]');
        
        if (categories.length > 0 && values.length > 0) {
            renderExpenseChart(chartContainer, { categories, values });
        }
    }
}

/**
 * Render expense breakdown chart
 * @param {HTMLElement} container - The container element
 * @param {Object} data - The chart data
 */
function renderExpenseChart(container, data) {
    console.log("Rendering expense chart");
    
    // Ensure we have categories and values
    if (!data.categories || !data.values || 
        !Array.isArray(data.categories) || !Array.isArray(data.values) || 
        data.categories.length === 0 || data.values.length === 0) {
        
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No expense data available yet. Add travel expenses to see category breakdown.
            </div>
        `;
        return;
    }
    
    // Performance optimization: Limit categories if there are too many
    if (data.categories.length > 7) {
        // Find the smallest categories and combine them into "Other"
        const sortedIndices = [...data.values.keys()].sort((a, b) => data.values[a] - data.values[b]);
        const otherIndices = sortedIndices.slice(0, data.categories.length - 6);
        const otherValue = otherIndices.reduce((sum, i) => sum + data.values[i], 0);
        
        // Create new arrays without the smallest categories
        const newCategories = data.categories.filter((_, i) => !otherIndices.includes(i));
        const newValues = data.values.filter((_, i) => !otherIndices.includes(i));
        
        // Add the "Other" category
        newCategories.push("Other");
        newValues.push(otherValue);
        
        data.categories = newCategories;
        data.values = newValues;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Create fixed-height expense chart container
    const chartContainer = document.createElement('div');
    chartContainer.className = 'expense-chart-container';
    container.appendChild(chartContainer);
    
    // Create canvas element inside the container
    const canvas = document.createElement('canvas');
    chartContainer.appendChild(canvas);
    
    // Define pie chart colors
    const backgroundColors = [
        'rgba(54, 162, 235, 0.7)',  // Blue
        'rgba(255, 99, 132, 0.7)',   // Red
        'rgba(255, 206, 86, 0.7)',   // Yellow
        'rgba(75, 192, 192, 0.7)',   // Green
        'rgba(153, 102, 255, 0.7)',  // Purple
        'rgba(255, 159, 64, 0.7)',   // Orange
        'rgba(199, 199, 199, 0.7)'   // Gray
    ];
    
    try {
        // Create pie chart
        new Chart(canvas, {
            type: 'pie',
            data: {
                labels: data.categories,
                datasets: [{
                    data: data.values,
                    backgroundColor: backgroundColors.slice(0, data.categories.length),
                    borderWidth: 1,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: {
                                size: 11 // Smaller font size
                            },
                            padding: 10 // Reduced padding
                        },
                        // Limit the number of legend items shown
                        maxItems: 6
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `$${value.toFixed(2)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Add compact total and max expense category
        const totalExpense = data.values.reduce((sum, value) => sum + value, 0);
        const maxExpenseIndex = data.values.indexOf(Math.max(...data.values));
        const maxExpenseCategory = data.categories[maxExpenseIndex];
        const maxExpense = data.values[maxExpenseIndex];
        const maxExpensePercentage = Math.round((maxExpense / totalExpense) * 100);
        
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'insight-box alert alert-light py-1 px-2 small';
        summaryDiv.innerHTML = `
            <div class="fw-bold mb-1">Total: $${totalExpense.toFixed(2)}</div>
            <div>Largest: ${maxExpenseCategory} ($${maxExpense.toFixed(2)}, ${maxExpensePercentage}%)</div>
        `;
        container.appendChild(summaryDiv);
    } catch (error) {
        console.error("Error creating expense chart:", error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error rendering expense chart: ${error.message}
            </div>
        `;
    }
}

/**
 * NEW: Initialize monthly expenses chart
 */
function initMonthlyExpensesChart() {
    const chartContainer = document.getElementById('monthlyExpensesChart');
    if (!chartContainer) return;
    
    // Get data from the container's data source attribute
    const dataSource = chartContainer.getAttribute('data-source');
    
    if (dataSource) {
        // Show loading state
        chartContainer.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading monthly expense data...</p>
            </div>
        `;
        
        // Fetch data from the API endpoint
        fetch(dataSource)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderMonthlyExpensesChart(chartContainer, data);
                } else {
                    throw new Error(data.message || 'Failed to load monthly expense data');
                }
            })
            .catch(error => {
                console.error('Error loading monthly expenses:', error);
                chartContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load monthly expense data: ${error.message}
                    </div>
                `;
            });
    }
}

/**
 * NEW: Render monthly expenses chart
 * @param {HTMLElement} container - The container element
 * @param {Object} data - The chart data with labels and values
 */
function renderMonthlyExpensesChart(container, data) {
    // Check if we have data to display
    if (!data.labels || data.labels.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No monthly expense data available yet. Add expenses to your travel plans to see this chart.
            </div>
        `;
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Create canvas for chart
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    
    // Create the bar chart
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Monthly Expenses ($)',
                data: data.data,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `$${context.raw.toFixed(2)}`;
                        }
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
    
    // Add summary text below the chart if there are enough data points
    if (data.data.length > 0) {
        const total = data.data.reduce((sum, value) => sum + value, 0);
        const average = total / data.data.length;
        const max = Math.max(...data.data);
        const maxIndex = data.data.indexOf(max);
        
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'mt-3 text-center text-muted small';
        summaryDiv.innerHTML = `
            <div class="row">
                <div class="col-4">
                    <div class="fw-bold">$${average.toFixed(2)}</div>
                    <div>Monthly Avg</div>
                </div>
                <div class="col-4">
                    <div class="fw-bold">$${total.toFixed(2)}</div>
                    <div>Total</div>
                </div>
                <div class="col-4">
                    <div class="fw-bold">$${max.toFixed(2)}</div>
                    <div>Highest (${data.labels[maxIndex]})</div>
                </div>
            </div>
        `;
        container.appendChild(summaryDiv);
    }
}

/**
 * NEW: Initialize trip duration distribution chart
 */
function initDurationDistributionChart() {
    const chartContainer = document.getElementById('durationDistributionChart');
    if (!chartContainer) return;
    
    // Get data from the container's data source attribute
    const dataSource = chartContainer.getAttribute('data-source');
    
    if (dataSource) {
        // Fetch data from the API endpoint
        fetch(dataSource)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderDurationDistributionChart(chartContainer, data);
                } else {
                    throw new Error(data.message || 'Failed to load duration data');
                }
            })
            .catch(error => {
                console.error('Error loading trip durations:', error);
                chartContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load trip duration data: ${error.message}
                    </div>
                `;
            });
    }
}

/**
 * NEW: Render trip duration distribution chart
 * @param {HTMLElement} container - The container element
 * @param {Object} data - The chart data with labels and values
 */
function renderDurationDistributionChart(container, data) {
    // Check if we have data to display
    if (!data.labels || data.labels.length === 0 || data.data.every(value => value === 0)) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No trip duration data available yet. Create travel plans to see this chart.
            </div>
        `;
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Create canvas for chart
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    
    // Define colors for pie chart segments
    const backgroundColors = [
        'rgba(54, 162, 235, 0.7)',   // Blue
        'rgba(255, 99, 132, 0.7)',    // Red
        'rgba(255, 206, 86, 0.7)',    // Yellow
        'rgba(75, 192, 192, 0.7)',    // Green
        'rgba(153, 102, 255, 0.7)',   // Purple
    ];
    
    // Create the pie chart
    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: backgroundColors.slice(0, data.labels.length),
                borderWidth: 1,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        font: {
                            size: 12
                        },
                        padding: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${context.label}: ${value} trips (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Add summary below the chart
    const total = data.data.reduce((sum, value) => sum + value, 0);
    if (total > 0) {
        // Find most common duration category
        let maxCount = 0;
        let mostCommonIndex = 0;
        
        data.data.forEach((count, index) => {
            if (count > maxCount) {
                maxCount = count;
                mostCommonIndex = index;
            }
        });
        
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'mt-3 text-center text-muted small';
        summaryDiv.innerHTML = `
            <p>You prefer trips of <strong>${data.labels[mostCommonIndex]}</strong> (${Math.round((maxCount / total) * 100)}% of your travels)</p>
        `;
        container.appendChild(summaryDiv);
    }
}

/**
 * NEW: Initialize destination frequency chart
 */
function initDestinationFrequencyChart() {
    const chartContainer = document.getElementById('destinationFrequencyChart');
    if (!chartContainer) return;
    
    // Get data from the container's data source attribute
    const dataSource = chartContainer.getAttribute('data-source');
    
    if (dataSource) {
        // Fetch data from the API endpoint
        fetch(dataSource)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderDestinationFrequencyChart(chartContainer, data);
                } else {
                    throw new Error(data.message || 'Failed to load destination data');
                }
            })
            .catch(error => {
                console.error('Error loading destination frequency:', error);
                chartContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load destination frequency data: ${error.message}
                    </div>
                `;
            });
    }
}

/**
 * NEW: Render destination frequency chart
 * @param {HTMLElement} container - The container element
 * @param {Object} data - The chart data with labels, values and colors
 */
function renderDestinationFrequencyChart(container, data) {
    // Check if we have data to display
    if (!data.labels || data.labels.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No destination data available yet. Create travel plans to see your most visited places.
            </div>
        `;
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Create canvas for chart
    const canvas = document.createElement('canvas');
    canvas.style.height = '300px';
    container.appendChild(canvas);
    
    // Create the horizontal bar chart
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Number of Visits',
                data: data.data,
                backgroundColor: data.colors || 'rgba(54, 162, 235, 0.7)',
                borderColor: data.colors ? data.colors.map(color => color.replace('0.7', '1')) : 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',  // Horizontal bar chart
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Visits'
                    },
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
    
    // If we have enough destinations, add a "favorite destinations" insight
    if (data.labels.length >= 3) {
        const top3 = data.labels.slice(0, 3);
        const insightDiv = document.createElement('div');
        insightDiv.className = 'mt-3 alert alert-success';
        insightDiv.innerHTML = `
            <i class="fas fa-star me-2"></i>
            <strong>Your Top Destinations:</strong> ${top3.join(', ')} are your most frequented places. You may have favorite spots or connections in these locations!
        `;
        container.appendChild(insightDiv);
    }
}

/**
 * Initialize travel timeline visualization
 */
function initTravelTimeline() {
    const timelineContainer = document.getElementById('travelTimeline');
    if (!timelineContainer) return;
    
    // Get data from the container's data attributes or fetch from API
    const dataSource = timelineContainer.getAttribute('data-source');
    
    if (dataSource) {
        // Show loading state first
        timelineContainer.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading your travel timeline...</p>
            </div>
        `;
        
        // Fetch data using improved function with better error handling
        fetchDataForVisualization(dataSource)
            .then(data => {
                renderTravelTimeline(timelineContainer, data);
            })
            .catch(error => {
                console.error('Error loading timeline data:', error);
                timelineContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load timeline data: ${error.message || 'Unknown error'}
                    </div>
                `;
            });
    }
}

/**
 * Render travel timeline
 * @param {HTMLElement} container - The container element
 * @param {Object} data - The timeline data
 */
function renderTravelTimeline(container, data) {
    console.log("Rendering travel timeline");
    
    if (!data.trips || !Array.isArray(data.trips) || data.trips.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No travel history to display yet. Create travel plans to see your timeline.
            </div>
        `;
        return;
    }
    
    // Performance optimization: Limit number of trips if there are too many
    let trips = [...data.trips]; // Create a copy
    
    // Sort trips by start date (newest first)
    trips.sort((a, b) => new Date(b.start_date) - new Date(a.start_date));
    
    // Limit to 10 most recent trips to prevent browser freezing
    if (trips.length > 10) {
        const moreTripsCount = trips.length - 10;
        trips = trips.slice(0, 10);
        
        // Add note about more trips
        container.innerHTML = `
            <div class="alert alert-info mb-4">
                <i class="fas fa-info-circle me-2"></i>
                Showing your 10 most recent trips. ${moreTripsCount} more ${moreTripsCount === 1 ? 'trip is' : 'trips are'} not displayed for performance reasons.
            </div>
        `;
    } else {
        container.innerHTML = ''; // Clear container
    }
    
    // Create timeline HTML
    let html = '<div class="timeline">';
    
    trips.forEach((trip, index) => {
        // Validate date fields
        let startDate, endDate, duration;
        
        try {
            startDate = new Date(trip.start_date);
            endDate = new Date(trip.end_date);
            duration = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
            
            if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
                throw new Error("Invalid date format");
            }
        } catch (e) {
            console.error("Date parsing error for trip:", trip, e);
            startDate = new Date();
            endDate = new Date();
            duration = 0;
        }
        
        // Alternate left/right for timeline items
        const position = index % 2 === 0 ? 'left' : 'right';
        
        html += `
            <div class="timeline-item ${position}">
                <div class="timeline-badge bg-primary">
                    <i class="fas fa-map-marker-alt"></i>
                </div>
                <div class="timeline-panel">
                    <div class="timeline-heading">
                        <h5 class="timeline-title">${trip.title || 'Untitled Trip'}</h5>
                        <p class="text-muted">
                            <i class="fas fa-calendar me-1"></i>
                            ${formatDate(startDate)} - ${formatDate(endDate)}
                            <span class="badge bg-light text-dark ms-2">${duration} days</span>
                        </p>
                    </div>
                    <div class="timeline-body">
                        <p class="mb-1"><strong>${trip.destination || 'Unknown Destination'}</strong></p>
                        ${trip.description ? `<p class="text-muted small">${trip.description.substring(0, 150)}${trip.description.length > 150 ? '...' : ''}</p>` : ''}
                        ${trip.budget ? `<div class="mt-2"><span class="badge bg-success">Budget: $${trip.budget}</span></div>` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML += html;
    
    // Add "View All" button if trips were limited
    if (data.trips.length > 10) {
        const viewAllButton = document.createElement('div');
        viewAllButton.className = 'text-center mt-4';
        viewAllButton.innerHTML = `
            <button id="viewAllTripsBtn" class="btn btn-outline-primary">
                <i class="fas fa-list me-2"></i>View All ${data.trips.length} Trips
            </button>
        `;
        container.appendChild(viewAllButton);
        
        // Add click event for the button
        setTimeout(() => {
            const button = document.getElementById('viewAllTripsBtn');
            if (button) {
                button.addEventListener('click', function() {
                    window.location.href = '/planner'; // Redirect to planner page to see all trips
                });
            }
        }, 0);
    }
}

/**
 * Initialize destination comparison
 */
function initDestinationComparison() {
    const comparisonContainer = document.getElementById('destinationComparison');
    if (!comparisonContainer) return;
    
    // Get data from the container's data attributes or fetch from API
    const dataSource = comparisonContainer.getAttribute('data-source');
    
    if (dataSource) {
        fetchDataForVisualization(dataSource)
            .then(data => {
                renderDestinationComparison(comparisonContainer, data);
            })
            .catch(error => {
                comparisonContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load destination comparison data
                    </div>
                `;
            });
    }
}

/**
 * Render destination comparison
 * @param {HTMLElement} container - The container element
 * @param {Object} data - The comparison data
 */
function renderDestinationComparison(container, data) {
    console.log("Rendering destination comparison");
    
    // Ensure data structure is correct with enough destinations to compare
    if (!data.destinations || !Array.isArray(data.destinations) || data.destinations.length < 2) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                At least 2 destinations are needed for comparison. Please add more travel plans.
            </div>
        `;
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Create metrics for radar chart (simplified for compactness)
    const metrics = [
        { key: 'cost', label: 'Cost', unit: '$', type: 'money' },
        { key: 'duration', label: 'Days', unit: '', type: 'number' },
        { key: 'distance', label: 'Distance', unit: 'km', type: 'number' },
        { key: 'visits', label: 'Visits', unit: '', type: 'number' }
    ];
    
    // Check if all destinations have necessary data
    data.destinations.forEach(dest => {
        metrics.forEach(metric => {
            if (dest[metric.key] === undefined || dest[metric.key] === null) {
                // Set default values for missing metrics
                if (metric.type === 'money' || metric.type === 'number') {
                    dest[metric.key] = 0;
                } else if (metric.type === 'rating') {
                    dest[metric.key] = 3; // Default 3-star rating
                }
            }
        });
    });
    
    // Performance optimization: Limit to 3 destinations to save space
    if (data.destinations.length > 3) {
        data.destinations = data.destinations.slice(0, 3);
    }
    
    // Create compact layout with two columns
    const row = document.createElement('div');
    row.className = 'row';
    container.appendChild(row);
    
    // Left column for radar chart (6 cols)
    const chartCol = document.createElement('div');
    chartCol.className = 'col-lg-6 mb-2';
    row.appendChild(chartCol);
    
    // Create radar chart canvas
    const canvasContainer = document.createElement('div');
    canvasContainer.className = 'radar-chart-container';
    const canvas = document.createElement('canvas');
    canvasContainer.appendChild(canvas);
    chartCol.appendChild(canvasContainer);
    
    // Right column for table and insights (6 cols)
    const infoCol = document.createElement('div');
    infoCol.className = 'col-lg-6';
    row.appendChild(infoCol);
    
    // Normalize data for radar chart (0-100 scale)
    const normalizedData = data.destinations.map(destination => {
        const normalized = {};
        
        metrics.forEach(metric => {
            // Find max value for this metric
            const maxValue = Math.max(...data.destinations.map(d => d[metric.key] || 0));
            normalized[metric.key] = maxValue > 0 ? (destination[metric.key] / maxValue) * 100 : 0;
        });
        
        return normalized;
    });
    
    try {
        // Create radar chart with optimized options for compact display
        new Chart(canvas, {
            type: 'radar',
            data: {
                labels: metrics.map(m => m.label),
                datasets: data.destinations.map((destination, index) => {
                    const colors = [
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                    ];
                    
                    return {
                        label: destination.name,
                        data: metrics.map(m => normalizedData[index][m.key]),
                        backgroundColor: colors[index % colors.length],
                        borderColor: colors[index % colors.length].replace('0.5', '1'),
                        borderWidth: 2,
                        pointBackgroundColor: colors[index % colors.length].replace('0.5', '1')
                    };
                })
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: {
                            display: true
                        },
                        ticks: {
                            display: false,
                            beginAtZero: true,
                            max: 100
                        },
                        pointLabels: {
                            font: {
                                size: 11 // Smaller font
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 15,
                            padding: 10,
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
        
        // Create compact table with key metrics only
        let tableHtml = `
            <table class="table table-sm table-bordered comparison-table">
                <thead>
                    <tr>
                        <th></th>
                        ${data.destinations.map(d => `<th>${d.name.substring(0, 10)}${d.name.length > 10 ? '...' : ''}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
        `;
        
        metrics.forEach(metric => {
            tableHtml += `
                <tr>
                    <td>${metric.label}</td>
                    ${data.destinations.map(d => {
                        let value = d[metric.key];
                        
                        if (metric.type === 'money') {
                            value = `$${(value || 0).toFixed(0)}`;
                        } else if (metric.type === 'number') {
                            value = `${value || 0}${metric.unit}`;
                        } else if (metric.type === 'rating') {
                            value = '★'.repeat(Math.round(value || 0));
                        }
                        
                        return `<td>${value}</td>`;
                    }).join('')}
                </tr>
            `;
        });
        
        tableHtml += `
                </tbody>
            </table>
        `;
        
        infoCol.innerHTML = tableHtml;
        
        // Add brief insights below the table
        const insightDiv = document.createElement('div');
        insightDiv.className = 'insight-box alert alert-light py-1 px-2';
        
        // Find best destination for each metric
        const bestDestinations = {};
        metrics.forEach(metric => {
            // For cost, lower is better
            if (metric.key === 'cost') {
                const minIndex = data.destinations
                    .map(d => d[metric.key] || Infinity)
                    .indexOf(Math.min(...data.destinations.map(d => d[metric.key] || Infinity)));
                bestDestinations[metric.key] = data.destinations[minIndex].name;
            } else {
                // For other metrics, higher is better
                const maxIndex = data.destinations
                    .map(d => d[metric.key] || 0)
                    .indexOf(Math.max(...data.destinations.map(d => d[metric.key] || 0)));
                bestDestinations[metric.key] = data.destinations[maxIndex].name;
            }
        });
        
        // Create compact insights
        const insights = [
            `<strong>${bestDestinations.cost}</strong>: Lowest cost`,
            `<strong>${bestDestinations.duration}</strong>: Longest stay`,
            `<strong>${bestDestinations.visits || bestDestinations.cost}</strong>: Most visited`
        ];
        
        insightDiv.innerHTML = insights.join(' • ');
        infoCol.appendChild(insightDiv);
        
    } catch (error) {
        console.error("Error creating destination comparison chart:", error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error rendering destination comparison: ${error.message}
            </div>
        `;
    }
}

/**
 * Initialize travel heatmap
 * @param {Array} destinations - Array of destination objects with coordinates
 */
function initTravelHeatmap(destinations) {
    const heatmapContainer = document.getElementById('travelHeatmap');
    if (!heatmapContainer) return;
    
    // Validate that we have valid coordinates
    const validDestinations = destinations.filter(d => d.lat && d.lng);
    
    if (validDestinations.length === 0) {
        heatmapContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No location data available for heatmap
            </div>
        `;
        return;
    }
    
    // Create the map
    const map = L.map(heatmapContainer).setView([20, 0], 2);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Prepare heat data
    const heatData = validDestinations.map(d => {
        // Intensity based on visit count or duration
        const intensity = d.visit_count || d.duration || 1;
        return [d.lat, d.lng, intensity];
    });
    
    // Add heat layer
    L.heatLayer(heatData, {
        radius: 25,
        blur: 15,
        maxZoom: 10,
        max: Math.max(...heatData.map(d => d[2])),
        gradient: {
            0.4: 'blue',
            0.6: 'cyan',
            0.7: 'lime',
            0.8: 'yellow',
            1.0: 'red'
        }
    }).addTo(map);
}

/**
 * Initialize trend analysis
 */
function initTrendAnalysis() {
    const trendContainer = document.getElementById('trendAnalysis');
    if (!trendContainer) return;
    
    // Get data from the container's data attributes or fetch from API
    const dataSource = trendContainer.getAttribute('data-source');
    
    if (dataSource) {
        fetchDataForVisualization(dataSource)
            .then(data => {
                renderTrendAnalysis(trendContainer, data);
            })
            .catch(error => {
                trendContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load trend data
                    </div>
                `;
            });
    }
}

/**
 * Render trend analysis
 * @param {HTMLElement} container - The container element
 * @param {Object} data - The trend data
 */
function renderTrendAnalysis(container, data) {
    if (!data.timeSeries || Object.keys(data.timeSeries).length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Not enough data for trend analysis
            </div>
        `;
        return;
    }
    
    // Create canvas for line chart
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    
    // Create the chart
    new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: Object.entries(data.timeSeries).map(([key, values], index) => {
                const colors = [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)'
                ];
                
                return {
                    label: key,
                    data: values,
                    borderColor: colors[index % colors.length],
                    backgroundColor: colors[index % colors.length].replace('1)', '0.1)'),
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                };
            })
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });
    
    // Add insights if available
    if (data.insights && data.insights.length > 0) {
        let insightsHtml = `
            <div class="mt-4">
                <h5><i class="fas fa-chart-line me-2"></i>Trend Insights</h5>
                <ul class="list-group">
        `;
        
        data.insights.forEach(insight => {
            insightsHtml += `
                <li class="list-group-item">
                    <i class="fas fa-lightbulb text-warning me-2"></i>
                    ${insight}
                </li>
            `;
        });
        
        insightsHtml += `
                </ul>
            </div>
        `;
        
        container.innerHTML += insightsHtml;
    }
}

/**
 * Format a date as a readable string
 * @param {Date} date - The date to format
 * @returns {string} - Formatted date string
 */
function formatDate(date) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString(undefined, options);
}

/**
 * NEW: Helper function to fetch data for visualizations
 * @param {string} url - The API endpoint URL
 * @returns {Promise} - Promise resolving to the fetched data
 */
function fetchDataForVisualization(url) {
    console.log(`Fetching data from: ${url}`);
    return fetch(url, {
        headers: {
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache'
        }
    })
    .then(response => {
        if (!response.ok) {
            console.error(`HTTP error! Status: ${response.status}`);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log(`Data received from ${url}:`, data);
        // Check if the API returned success:false
        if (data && data.success === false) {
            throw new Error(data.message || 'API returned success:false');
        }
        return data;
    })
    .catch(error => {
        console.error(`Error fetching data from ${url}:`, error);
        throw error;
    });
}
