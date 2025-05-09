
/**
 * Statistics page functionality
 * Handles map initialization, home location setting, recommendations and other statistics features
 */

// Global variables to track initialization state
let isInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    // Prevent duplicate initialization
    if (isInitialized) return;
    isInitialized = true;
    
    console.log('Initializing statistics page...');
    
    // Initialize location setting functionality first
    initLocationSetting();
    
    // Initialize map if home address is set
    const homeAddress = homeAddressData; // This will be defined in the HTML template
    
    if (homeAddress) {
        console.log('Home address found, initializing map');
        initializeStatisticsMap();
    } else {
        console.log('No home address set');
    }
    
    // Load recommendations
    fetchRecommendations();
    
    // Initialize enhanced data visualizations
    initDataVisualizations();
});

function initializeStatisticsMap() {
    // Initialize map centered on home location
    const homeLocation = homeLocationData; // This will be defined in the HTML template
    const map = L.map('statisticsMap').setView(homeLocation, 4);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Add home marker with custom icon
    const homeIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="home-icon-container"><i class="fas fa-home home-icon"></i></div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
    
    const homeMarker = L.marker(homeLocation, {
        icon: homeIcon,
        title: 'Home'
    }).addTo(map);
    homeMarker.bindPopup('<strong>Home Location</strong>');
    
    // Cache for destinations to prevent duplicate requests
    let destinationsCache = null;
    
    // Get actual destination coordinates from travel plans
    fetchDestinationCoordinates()
        .then(destinations => {
            destinationsCache = destinations;
            
            // Add destination markers
            destinations.forEach((destination, index) => {
                if (destination.lat && destination.lng) {
                    const location = [destination.lat, destination.lng];
                    
                    // Create marker with custom icon color based on index
                    const colors = ['#4285f4', '#ea4335', '#fbbc05', '#34a853', '#8a2be2', '#00acc1', '#ff6d00'];
                    const color = colors[index % colors.length];
                    
                    const destinationIcon = L.divIcon({
                        className: 'custom-div-icon',
                        html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
                        iconSize: [12, 12],
                        iconAnchor: [6, 6]
                    });
                    
                    const marker = L.marker(location, {
                        icon: destinationIcon,
                        title: destination.name
                    }).addTo(map);
                    
                    marker.bindPopup(`<strong>${destination.name}</strong>`);
                    
                    // Draw curved route line from home to destination
                    drawCurvedRoute(map, homeLocation, location, color);
                }
            });
            
            // Fit map to show all markers
            if (destinations.length > 0) {
                const bounds = destinations
                    .filter(d => d.lat && d.lng)
                    .map(d => [d.lat, d.lng]);
                
                if (bounds.length > 0) {
                    bounds.push(homeLocation);
                    map.fitBounds(bounds);
                }
            }
        })
        .catch(error => {
            console.error('Error fetching destination coordinates:', error);
        });
}

function fetchDestinationCoordinates() {
    // Prevent caching issues that might cause refreshes
    return fetch(destinationsUrl, {
        headers: {
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            return data.destinations;
        } else {
            throw new Error(data.message || 'Failed to fetch destinations');
        }
    });
}

function drawCurvedRoute(map, start, end, color) {
    // Create a curved path between two points for better visualization
    const offsetX = (end[1] - start[1]) * 0.125;
    const offsetY = (end[0] - start[0]) * 0.125;
    
    // The control point for the curve
    const control = [
        (start[0] + end[0]) / 2 + offsetY,
        (start[1] + end[1]) / 2 - offsetX
    ];
    
    // Generate points along the curve
    const points = [];
    // Start with the exact starting point
    points.push(start);
    
    // Generate intermediate points
    for (let t = 0.05; t < 0.95; t += 0.05) {
        points.push(bezierPoint(start, control, end, t));
    }
    
    // End with the exact destination point
    points.push(end);
    
    // Create polyline with the curved points
    L.polyline(points, {
        color: color || '#4285f4',
        weight: 2.5,
        opacity: 0.7,
        smoothFactor: 1
    }).addTo(map);
    
    // Add travel marker animation
    addTravelMarkerAnimation(map, points, color);
}

function bezierPoint(start, control, end, t) {
    // Quadratic Bezier curve formula
    const lat = Math.pow(1-t, 2) * start[0] + 
                2 * (1-t) * t * control[0] + 
                Math.pow(t, 2) * end[0];
    
    const lng = Math.pow(1-t, 2) * start[1] + 
                2 * (1-t) * t * control[1] + 
                Math.pow(t, 2) * end[1];
    
    return [lat, lng];
}

function addTravelMarkerAnimation(map, points, color) {
    // Create travel marker icon with the route color
    const travelMarkerIcon = L.divIcon({
        className: 'travel-marker-container',
        html: `<div class="travel-marker" style="border-color: ${color}"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });
    
    // Create travel marker
    const travelMarker = L.marker(points[0], {
        icon: travelMarkerIcon,
        interactive: false
    }).addTo(map);
    
    // Animate travel marker along the path
    let index = 0;
    const interval = setInterval(() => {
        if (index < points.length) {
            // Update travel marker position
            travelMarker.setLatLng(points[index]);
            
            index++;
        } else {
            clearInterval(interval);
            // Remove travel marker after journey completes
            setTimeout(() => map.removeLayer(travelMarker), 1000);
        }
    }, 50); // Speed up the animation by reducing interval time
}

function fetchRecommendations() {
    // Fetch AI recommendations
    fetch(recommendationsUrl)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderRecommendations(data.recommendations);
            } else {
                showRecommendationError();
            }
        })
        .catch(error => {
            console.error('Error fetching recommendations:', error);
            showRecommendationError();
        });
}

function renderRecommendations(recommendations) {
    const container = document.getElementById('recommendationsContainer');
    
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

function showRecommendationError() {
    const container = document.getElementById('recommendationsContainer');
    container.innerHTML = `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            Unable to load recommendations. Please try again later.
        </div>
    `;
}

/**
 * Home location setting functionality
 * Handles the setup and interaction for the home location modal
 */
function initLocationSetting() {
    console.log('Initializing location setting...');
    
    const addressInput = document.getElementById('address');
    const validateBtn = document.getElementById('validateAddressBtn');
    const suggestionsContainer = document.getElementById('suggestions-container');
    const saveLocationBtn = document.getElementById('saveLocationBtn');
    const homeLocationForm = document.getElementById('homeLocationForm');
    const homeLocationModal = document.getElementById('homeLocationModal');
    let previewMap = null;
    let previewMarker = null;
    let debounceTimer;
    
    if (!homeLocationModal) {
        console.error('Home location modal not found in DOM');
        return;
    }
    
    // Initialize map when modal is shown using Bootstrap 5 event listener
    homeLocationModal.addEventListener('shown.bs.modal', function() {
        console.log('Home location modal shown');
        if (!previewMap) {
            previewMap = L.map('previewMap').setView([0, 0], 2);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(previewMap);
            
            // If we already have coordinates, show them
            const lat = document.getElementById('lat').value;
            const lng = document.getElementById('lng').value;
            
            if (lat && lng) {
                console.log('Displaying existing location on map:', lat, lng);
                showLocationOnMap(parseFloat(lat), parseFloat(lng), addressInput.value);
            }
        }
        
        // Force map to recalculate size after modal is fully visible
        setTimeout(function() {
            previewMap.invalidateSize();
        }, 200);
    });
    
    // Handle validate button click
    validateBtn.addEventListener('click', function() {
        const query = addressInput.value.trim();
        
        if (query.length > 0) {
            console.log('Validating address:', query);
            fetchAddressSuggestions(query);
        } else {
            console.warn('Empty address query');
        }
    });
    
    // Handle address input (debounced)
    addressInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = this.value.trim();
            
            if (query.length >= 3) {
                fetchAddressSuggestions(query);
            } else {
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.classList.add('d-none');
            }
            
            // Disable save button until address is validated
            saveLocationBtn.disabled = true;
        }, 500);
    });
    
    // Handle save button click
    saveLocationBtn.addEventListener('click', function() {
        if (!saveLocationBtn.disabled && homeLocationForm) {
            console.log('Save button clicked, submitting form');
            homeLocationForm.submit();
        } else {
            console.warn('Save button clicked but it was disabled or form not found');
        }
    });
    
    // Add form submit validation
    if (homeLocationForm) {
        homeLocationForm.addEventListener('submit', function(e) {
            const lat = document.getElementById('lat').value;
            const lng = document.getElementById('lng').value;
            
            if (lat && lng) {
                console.log('Form submitted with valid location data:', {
                    address: addressInput.value,
                    lat: lat,
                    lng: lng
                });
                return true;
            } else {
                e.preventDefault();
                console.error('Missing coordinates. Please validate your address first.');
                alert('Please validate your address first by searching and selecting a result.');
                return false;
            }
        });
    } else {
        console.error('Home location form not found in DOM');
    }    // Fetch address suggestions
    function fetchAddressSuggestions(query) {
        // Show loading state
        suggestionsContainer.innerHTML = '<div class="address-suggestion text-center"><div class="spinner-border spinner-border-sm me-2" role="status"></div> Searching...</div>';
        suggestionsContainer.classList.remove('d-none');
        
        console.log('Fetching address suggestions for:', query);

        // First try direct Nominatim API (simpler, usually works)
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`, {
            headers: {
                'User-Agent': 'TravelPlannerApp/1.0'
            }
        })
        .then(response => {
            console.log('Nominatim API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Nominatim API response data:', data);
            if (data && data.length > 0) {
                renderSuggestions(data);
            } else {
                // If Nominatim doesn't return results, try our backend
                console.log('No results from Nominatim, trying backend API');
                return tryBackendAPI(query);
            }
        })
        .catch(error => {
            console.error('Error with Nominatim API:', error);
            // Try our backend as fallback
            tryBackendAPI(query);
        });

        // Helper function for backend API call
        function tryBackendAPI(query) {
            console.log('Trying backend API for:', query);
            return fetch('/statistics/validate-address', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ address: query })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.location) {
                    // Format the data to match what renderSuggestions expects
                    const suggestion = [{
                        display_name: data.location.display_name,
                        lat: data.location.lat,
                        lon: data.location.lng
                    }];
                    renderSuggestions(suggestion);
                } else {
                    suggestionsContainer.innerHTML = '<div class="address-suggestion text-center">No results found</div>';
                }
            })
            .catch(error => {
                console.error('Error with backend API:', error);
                suggestionsContainer.innerHTML = '<div class="address-suggestion text-center text-danger">Error searching for address</div>';
            });
        }
    }
      // Render suggestions
    function renderSuggestions(suggestions) {
        suggestionsContainer.innerHTML = '';
        
        if (!suggestions || suggestions.length === 0) {
            suggestionsContainer.innerHTML = '<div class="address-suggestion text-center">No results found</div>';
            return;
        }
        
        console.log('Rendering suggestions:', suggestions);
        
        suggestions.forEach(suggestion => {
            const div = document.createElement('div');
            div.className = 'address-suggestion';
            div.textContent = suggestion.display_name;
            
            // Store the coordinates as data attributes
            div.dataset.lat = suggestion.lat;
            div.dataset.lng = suggestion.lon || suggestion.lng; // Handle different property names
            div.dataset.name = suggestion.display_name;
            
            div.addEventListener('click', function() {
                console.log('Suggestion selected:', this.dataset);
                
                // Set the input value
                addressInput.value = this.dataset.name;
                
                // Set the hidden inputs
                document.getElementById('lat').value = this.dataset.lat;
                document.getElementById('lng').value = this.dataset.lng;
                
                // Show location on map
                showLocationOnMap(
                    parseFloat(this.dataset.lat), 
                    parseFloat(this.dataset.lng),
                    this.dataset.name
                );
                
                // Hide suggestions
                suggestionsContainer.classList.add('d-none');
                
                // Enable save button
                saveLocationBtn.disabled = false;
                console.log('Save button enabled');
            });
            
            suggestionsContainer.appendChild(div);
        });
    }
      /**
     * Show selected location on the preview map
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @param {string} address - Display name of the location
     */
    function showLocationOnMap(lat, lng, address) {
        console.log('Showing location on map:', lat, lng, address);
        
        // Safety checks
        if (!lat || !lng) {
            console.error('Invalid coordinates:', lat, lng);
            return;
        }
        
        // Get the preview element
        const locationPreview = document.getElementById('locationPreview');
        if (!locationPreview) {
            console.error('Location preview element not found');
            return;
        }
        
        // Show the map container
        locationPreview.classList.remove('d-none');
        
        // Make sure map is initialized
        if (!previewMap) {
            console.warn('Preview map not initialized yet, creating it now');
            previewMap = L.map('previewMap').setView([lat, lng], 13);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(previewMap);
        } else {
            // Update the map view
            previewMap.setView([lat, lng], 13);
        }
        
        // Remove existing marker if any
        if (previewMarker) {
            previewMap.removeLayer(previewMarker);
        }
        
        // Add a new marker
        previewMarker = L.marker([lat, lng]).addTo(previewMap);
        previewMarker.bindPopup(`<strong>Selected Location</strong><br>${address}`).openPopup();
        
        // Update the coordinates display
        const selectedLat = document.getElementById('selectedLat');
        const selectedLng = document.getElementById('selectedLng');
        
        if (selectedLat && selectedLng) {
            selectedLat.textContent = lat.toFixed(6);
            selectedLng.textContent = lng.toFixed(6);
        }
        
        // Force map to recalculate size
        setTimeout(function() {
            previewMap.invalidateSize();
        }, 100);
    }
}