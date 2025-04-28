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
    // Create canvas element
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    
    // Define colors
    const backgroundColors = [
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 99, 132, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(199, 199, 199, 0.7)'
    ];
    
    // Create the chart
    new Chart(canvas, {
        type: 'pie',
        data: {
            labels: data.categories,
            datasets: [{
                data: data.values,
                backgroundColor: backgroundColors.slice(0, data.categories.length),
                borderWidth: 1
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
                        padding: 15
                    }
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
        fetchDataForVisualization(dataSource)
            .then(data => {
                renderTravelTimeline(timelineContainer, data);
            })
            .catch(error => {
                timelineContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load timeline data
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
    if (!data.trips || data.trips.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No travel history to display
            </div>
        `;
        return;
    }
    
    // Sort trips by start date
    data.trips.sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
    
    // Create timeline HTML
    let html = '<div class="timeline">';
    
    data.trips.forEach((trip, index) => {
        const startDate = new Date(trip.start_date);
        const endDate = new Date(trip.end_date);
        const duration = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
        
        // Alternate left/right for timeline items
        const position = index % 2 === 0 ? 'left' : 'right';
        
        html += `
            <div class="timeline-item ${position}">
                <div class="timeline-badge bg-primary">
                    <i class="fas fa-map-marker-alt"></i>
                </div>
                <div class="timeline-panel">
                    <div class="timeline-heading">
                        <h5 class="timeline-title">${trip.title}</h5>
                        <p class="text-muted">
                            <i class="fas fa-calendar me-1"></i>
                            ${formatDate(startDate)} - ${formatDate(endDate)}
                            <span class="badge bg-light text-dark ms-2">${duration} days</span>
                        </p>
                    </div>
                    <div class="timeline-body">
                        <p class="mb-1"><strong>${trip.destination}</strong></p>
                        ${trip.description ? `<p class="text-muted small">${trip.description}</p>` : ''}
                        ${trip.budget ? `<div class="mt-2"><span class="badge bg-success">Budget: $${trip.budget}</span></div>` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
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
    if (!data.destinations || data.destinations.length < 2) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                At least 2 destinations are needed for comparison
            </div>
        `;
        return;
    }
    
    // Create comparison metrics
    const metrics = [
        { key: 'cost', label: 'Average Daily Cost', unit: '$', type: 'money' },
        { key: 'duration', label: 'Duration', unit: 'days', type: 'number' },
        { key: 'distance', label: 'Distance from Home', unit: 'km', type: 'number' },
        { key: 'rating', label: 'Your Rating', unit: '', type: 'rating' }
    ];
    
    // Create canvas for radar chart
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    
    // Normalize data for radar chart (0-100 scale)
    const normalizedData = data.destinations.map(destination => {
        const normalized = {};
        
        metrics.forEach(metric => {
            // Find max value for this metric
            const maxValue = Math.max(...data.destinations.map(d => d[metric.key]));
            normalized[metric.key] = maxValue > 0 ? (destination[metric.key] / maxValue) * 100 : 0;
        });
        
        return normalized;
    });
    
    // Create the chart
    new Chart(canvas, {
        type: 'radar',
        data: {
            labels: metrics.map(m => m.label),
            datasets: data.destinations.map((destination, index) => {
                const colors = [
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(255, 206, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
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
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    ticks: {
                        display: false,
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        }
    });
    
    // Create a detailed table comparison
    let tableHtml = `
        <div class="table-responsive mt-4">
            <table class="table table-bordered table-hover">
                <thead>
                    <tr>
                        <th>Metric</th>
                        ${data.destinations.map(d => `<th>${d.name}</th>`).join('')}
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
                        value = `$${value.toFixed(2)}`;
                    } else if (metric.type === 'number') {
                        value = `${value} ${metric.unit}`;
                    } else if (metric.type === 'rating') {
                        value = '★'.repeat(Math.round(value));
                    }
                    
                    return `<td>${value}</td>`;
                }).join('')}
            </tr>
        `;
    });
    
    // Add additional metrics if available
    if (data.metrics) {
        data.metrics.forEach(metric => {
            tableHtml += `
                <tr>
                    <td>${metric.label}</td>
                    ${data.destinations.map(d => `<td>${d[metric.key] || '-'}</td>`).join('')}
                </tr>
            `;
        });
    }
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML += tableHtml;
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
