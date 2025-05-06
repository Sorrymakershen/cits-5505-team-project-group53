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
    
    // Initialize monthly expenses chart
    initMonthlyExpensesChart();
    
    // Initialize trip duration distribution chart
    initDurationDistributionChart();
    
    // Initialize destination frequency chart
    initDestinationFrequencyChart();
    
    // Initialize travel timeline
    initTravelTimeline();
    
    // Initialize destination comparison
    initDestinationComparison();
}

/**
 * Initialize expense breakdown chart using Chart.js
 */
function initExpenseChart() {
    const chartContainer = document.getElementById('expenseChart');
    if (!chartContainer) return;
    
    // Get data from the container's data attributes or fetch from API
    const dataSource = chartContainer.getAttribute('data-source') || '/statistics/api/expenses/by-trip';
    
    // Always fetch from API to get expenses by trip
    fetchDataForVisualization(dataSource)
        .then(data => {
            renderExpenseChart(chartContainer, data);
        })
        .catch(error => {
            chartContainer.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load expense data: ${error.message || 'Unknown error'}
                </div>
            `;
        });
}

/**
 * Render expense breakdown chart
 * @param {HTMLElement} container - The container element
 * @param {Object} data - The chart data
 */
function renderExpenseChart(container, data) {
    console.log("Rendering expense chart");
    
    // Check if we have trip data
    if (!data.trips || !Array.isArray(data.trips) || data.trips.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No expense data available yet. Add travel expenses to see category breakdown by trip.
            </div>
        `;
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Create trip selector
    const selectorDiv = document.createElement('div');
    selectorDiv.className = 'mb-3';
    
    let selectorHtml = `
        <label for="tripSelector" class="form-label">Select Trip:</label>
        <select class="form-select form-select-sm" id="tripSelector">
            <option value="all" selected>All Trips</option>
    `;
    
    data.trips.forEach(trip => {
        selectorHtml += `<option value="${trip.id}">${trip.title || 'Untitled Trip'}</option>`;
    });
    
    selectorHtml += `</select>`;
    selectorDiv.innerHTML = selectorHtml;
    container.appendChild(selectorDiv);
    
    // Create fixed-height expense chart container
    const chartContainer = document.createElement('div');
    chartContainer.className = 'expense-chart-container';
    container.appendChild(chartContainer);
    
    // Create canvas element inside the container
    const canvas = document.createElement('canvas');
    chartContainer.appendChild(canvas);
    
    // Initialize chart with "All Trips" data
    const chart = createExpenseChart(canvas, data.aggregated);
    
    // Add event listener for trip selection
    document.getElementById('tripSelector').addEventListener('change', function() {
        const tripId = this.value;
        let chartData;
        
        if (tripId === 'all') {
            chartData = data.aggregated;
        } else {
            const selectedTrip = data.trips.find(t => t.id.toString() === tripId);
            chartData = selectedTrip ? selectedTrip.expenses : { categories: [], values: [] };
        }
        
        // Update chart with selected trip data
        updateExpenseChart(chart, chartData);
        
        // Update summary
        updateExpenseSummary(container, chartData);
    });
    
    // Add initial summary
    updateExpenseSummary(container, data.aggregated);
    
    function createExpenseChart(canvas, chartData) {
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
            // Check if we have data
            if (!chartData.categories || !chartData.values || chartData.categories.length === 0) {
                return null;
            }
            
            // Create pie chart
            return new Chart(canvas, {
                type: 'pie',
                data: {
                    labels: chartData.categories,
                    datasets: [{
                        data: chartData.values,
                        backgroundColor: backgroundColors.slice(0, chartData.categories.length),
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
        } catch (error) {
            console.error("Error creating expense chart:", error);
            canvas.parentNode.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error rendering expense chart: ${error.message}
                </div>
            `;
            return null;
        }
    }
    
    function updateExpenseChart(chart, chartData) {
        if (!chart || !chartData.categories || !chartData.values) return;
        
        chart.data.labels = chartData.categories;
        chart.data.datasets[0].data = chartData.values;
        chart.update();
    }
    
    function updateExpenseSummary(container, chartData) {
        // Remove existing summary
        const existingSummary = container.querySelector('.expense-summary');
        if (existingSummary) {
            existingSummary.remove();
        }
        
        if (!chartData.categories || !chartData.values || chartData.values.length === 0) {
            const noDataDiv = document.createElement('div');
            noDataDiv.className = 'expense-summary alert alert-info';
            noDataDiv.innerHTML = `
                <i class="fas fa-info-circle me-2"></i>
                No expense data for the selected trip.
            `;
            container.appendChild(noDataDiv);
            return;
        }
        
        // Add compact total and max expense category
        const totalExpense = chartData.values.reduce((sum, value) => sum + value, 0);
        const maxExpenseIndex = chartData.values.indexOf(Math.max(...chartData.values));
        const maxExpenseCategory = chartData.categories[maxExpenseIndex];
        const maxExpense = chartData.values[maxExpenseIndex];
        const maxExpensePercentage = Math.round((maxExpense / totalExpense) * 100);
        
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'expense-summary insight-box alert alert-light py-1 px-2 small mt-3';
        summaryDiv.innerHTML = `
            <div class="fw-bold mb-1">Total: $${totalExpense.toFixed(2)}</div>
            <div>Largest: ${maxExpenseCategory} ($${maxExpense.toFixed(2)}, ${maxExpensePercentage}%)</div>
        `;
        container.appendChild(summaryDiv);
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
    console.log("Rendering travel timeline", data);
    
    if (!data.trips || !Array.isArray(data.trips) || data.trips.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No travel history to display yet. Create travel plans to see your timeline.
            </div>
        `;
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Create actual timeline container with the timeline class
    const timelineElement = document.createElement('div');
    timelineElement.className = 'timeline';
    container.appendChild(timelineElement);
    
    // Sort trips by start date
    const trips = [...data.trips]; // Create a copy
    trips.sort((a, b) => new Date(a.start_date) - new Date(b.start_date)); // 按时间顺序
    
    // Add timeline items
    trips.forEach((trip, index) => {
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
            return; // Skip this trip if dates are invalid
        }
        
        // Create timeline item (alternating left and right)
        const timelineItem = document.createElement('div');
        timelineItem.className = `timeline-item ${index % 2 === 0 ? 'left' : 'right'}`;
        
        // Create timeline badge with plane icon
        const timelineBadge = document.createElement('div');
        timelineBadge.className = 'timeline-badge bg-primary';
        timelineBadge.innerHTML = '<i class="fas fa-plane text-white"></i>';
        
        // Create timeline panel (content)
        const timelinePanel = document.createElement('div');
        timelinePanel.className = 'timeline-panel';
        
        const formattedStartDate = formatDate(startDate);
        const formattedEndDate = formatDate(endDate);
        
        timelinePanel.innerHTML = `
            <div class="timeline-heading">
                <h5 class="timeline-title">${trip.title || 'Untitled Trip'}</h5>
                <p class="text-muted">
                    <i class="fas fa-calendar me-1"></i> 
                    ${formattedStartDate} - ${formattedEndDate}
                </p>
            </div>
            <div class="timeline-body">
                <p><strong>Destination:</strong> ${trip.destination || 'Unknown'}</p>
                <p><strong>Duration:</strong> ${duration} days</p>
                ${trip.budget ? `<p><strong>Budget:</strong> $${trip.budget}</p>` : ''}
            </div>
        `;
        
        // Append all elements in the correct order
        timelineItem.appendChild(timelineBadge);
        timelineItem.appendChild(timelinePanel);
        timelineElement.appendChild(timelineItem);
    });
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
    
    // Performance optimization: Limit to 5 destinations to save space
    if (data.destinations.length > 5) {
        data.destinations = data.destinations.slice(0, 5);
    }
    
    // Create radar chart container
    const canvasContainer = document.createElement('div');
    canvasContainer.className = 'radar-chart-container mb-4';
    const canvas = document.createElement('canvas');
    canvasContainer.appendChild(canvas);
    container.appendChild(canvasContainer);
    
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
        
        // Add brief insights directly below the chart (no table)
        const insightDiv = document.createElement('div');
        insightDiv.className = 'insight-box alert alert-light py-1 px-2 mt-3';
        
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
        container.appendChild(insightDiv);
        
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
