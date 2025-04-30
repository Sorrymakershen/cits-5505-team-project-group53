/**
 * Memory Map JavaScript
 * Handles interactive map features for the memory map page
 */

// Global variables
let map;
let markers = [];
let infoWindow;
let markerCluster;
let currentMapType = 'roadmap';
let heatmap = null;
let directionsService;
let directionsRenderer;
let selectedMarkers = [];

// Marker icon options
const markerIcons = {
    default: null, // Use default Google marker
    recent: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
    selected: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
    highlight: 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png'
};

// Initialize the map
function initMap() {
    showLoader();
    
    // Create map instance
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 2,
        center: { lat: 20, lng: 0 },
        mapTypeId: "roadmap",
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
            position: google.maps.ControlPosition.TOP_LEFT,
        },
        zoomControl: true,
        zoomControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM,
        },
        streetViewControl: true,
        streetViewControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM,
        },
        fullscreenControl: true,
        fullscreenControlOptions: {
            position: google.maps.ControlPosition.RIGHT_TOP,
        },
        styles: [
            {
                "featureType": "water",
                "elementType": "geometry",
                "stylers": [{ "color": "#e9e9e9" }, { "lightness": 17 }]
            },
            {
                "featureType": "landscape",
                "elementType": "geometry",
                "stylers": [{ "color": "#f5f5f5" }, { "lightness": 20 }]
            },
            {
                "featureType": "road.highway",
                "elementType": "geometry.fill",
                "stylers": [{ "color": "#ffffff" }, { "lightness": 17 }]
            },
            {
                "featureType": "administrative",
                "elementType": "geometry.stroke",
                "stylers": [{ "color": "#fefefe" }, { "lightness": 17 }, { "weight": 1.2 }]
            }
        ]
    });
    
    // Initialize info window for markers
    infoWindow = new google.maps.InfoWindow();
    
    // Initialize directions service
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        suppressMarkers: true,
        polylineOptions: {
            strokeColor: '#4285F4',
            strokeOpacity: 0.8,
            strokeWeight: 5
        }
    });
    
    // Set up event listeners
    setupEventListeners();
    
    // Load markers for memories
    loadMemoryMarkers();
}

// Show loading indicator
function showLoader() {
    document.getElementById('loader').style.display = 'flex';
}

// Hide loading indicator
function hideLoader() {
    document.getElementById('loader').style.display = 'none';
}

// Set up map control event listeners
function setupEventListeners() {
    // Reset to world view
    document.getElementById('zoomWorld').addEventListener('click', function() {
        map.setZoom(2);
        map.setCenter({ lat: 20, lng: 0 });
    });
    
    // Toggle between map types
    document.getElementById('toggleTerrain').addEventListener('click', function() {
        currentMapType = currentMapType === 'roadmap' ? 'terrain' : 'roadmap';
        map.setMapTypeId(currentMapType);
        
        // Update button icon
        const icon = this.querySelector('i');
        if (currentMapType === 'terrain') {
            icon.className = 'fas fa-map';
            this.title = 'Switch to Road Map';
        } else {
            icon.className = 'fas fa-mountain';
            this.title = 'Switch to Terrain View';
        }
    });
    
    // Add more map controls as needed
    if (document.getElementById('toggleHeatmap')) {
        document.getElementById('toggleHeatmap').addEventListener('click', toggleHeatmap);
    }
    
    if (document.getElementById('showJourney')) {
        document.getElementById('showJourney').addEventListener('click', showJourneyPath);
    }
    
    // Listen for map click to close info windows
    google.maps.event.addListener(map, 'click', function() {
        infoWindow.close();
    });
}

// Load markers for all memories
function loadMemoryMarkers() {
    // This function will be populated with actual data in the template
    // using Jinja2 templating to inject memory data
    
    // After all markers are added, check if there are any
    if (markers.length > 0) {
        // Fit map to show all markers
        const bounds = new google.maps.LatLngBounds();
        markers.forEach(marker => bounds.extend(marker.getPosition()));
        map.fitBounds(bounds);
        
        // Create marker cluster if there are many markers
        if (markers.length > 10) {
            markerCluster = new MarkerClusterer(map, markers, {
                imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m',
                gridSize: 50,
                minimumClusterSize: 3,
                maxZoom: 15
            });
        }
        
        // Hide the "no memories" message
        if (document.getElementById('no-memories')) {
            document.getElementById('no-memories').style.display = 'none';
        }
    } else {
        // Show the "no memories" message
        if (document.getElementById('no-memories')) {
            document.getElementById('no-memories').style.display = 'flex';
        }
    }
    
    // Update the memory counter
    if (document.getElementById('memory-count')) {
        document.getElementById('memory-count').textContent = markers.length;
    }
    
    // Hide the loader
    hideLoader();
}

// Create a memory marker
function createMemoryMarker(memory, isRecent) {
    const marker = new google.maps.Marker({
        position: { lat: memory.lat, lng: memory.lng },
        map: map,
        title: memory.title,
        animation: google.maps.Animation.DROP,
        icon: isRecent ? markerIcons.recent : markerIcons.default,
        memoryId: memory.id
    });
    
    // Create content for info window
    const contentString = createInfoWindowContent(memory);
    
    // Add click event for marker
    marker.addListener("click", () => {
        // Close any open info windows
        infoWindow.close();
        
        // Set new content and open
        infoWindow.setContent(contentString);
        infoWindow.open(map, marker);
        
        // Bounce animation when clicked
        marker.setAnimation(google.maps.Animation.BOUNCE);
        setTimeout(() => {
            marker.setAnimation(null);
        }, 750);
        
        // Highlight in list if list exists
        highlightMemoryInList(memory.id);
    });
    
    return marker;
}

// Create info window content
function createInfoWindowContent(memory) {
    let content = `
        <div class="memory-info-window">
    `;
    
    // Add image if available
    if (memory.image_path) {
        content += `
            <img src="/static/uploads/${memory.image_path}" 
                alt="${memory.title}" class="memory-thumbnail">
        `;
    }
    
    // Add memory details
    content += `
            <h4>${memory.title}</h4>
            <p><i class="fas fa-map-marker-alt"></i> <strong>${memory.location}</strong></p>
            <p><i class="far fa-calendar-alt"></i> ${memory.visit_date || 'Date not specified'}</p>
    `;
    
    // Add description if available
    if (memory.description) {
        // Truncate description if too long
        const truncatedDesc = memory.description.length > 100 
            ? memory.description.substring(0, 97) + '...' 
            : memory.description;
        
        content += `
            <p><i class="fas fa-quote-left"></i> ${truncatedDesc}</p>
        `;
    }
    
    // Add view details link
    content += `
            <a href="/memories/${memory.id}" class="memory-details-link btn btn-sm btn-primary">
                <i class="fas fa-eye"></i> View Details
            </a>
        </div>
    `;
    
    return content;
}

// Highlight a memory in the list view if it exists
function highlightMemoryInList(memoryId) {
    // If there's a list of memories on the page
    const memoryListItems = document.querySelectorAll('.memory-list-item');
    if (memoryListItems.length > 0) {
        // Remove highlight from all items
        memoryListItems.forEach(item => {
            item.classList.remove('highlighted');
        });
        
        // Add highlight to the selected item
        const selectedItem = document.querySelector(`.memory-list-item[data-id="${memoryId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('highlighted');
            selectedItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

// Toggle heatmap visualization
function toggleHeatmap() {
    if (heatmap) {
        heatmap.setMap(heatmap.getMap() ? null : map);
    } else {
        // Create heatmap data from markers
        const heatmapData = markers.map(marker => {
            return {
                location: marker.getPosition(),
                weight: 1
            };
        });
        
        heatmap = new google.maps.visualization.HeatmapLayer({
            data: heatmapData,
            map: map,
            radius: 20,
            opacity: 0.7
        });
    }
    
    // Update button text
    const button = document.getElementById('toggleHeatmap');
    if (button) {
        const icon = button.querySelector('i');
        if (heatmap && heatmap.getMap()) {
            icon.className = 'fas fa-layer-group';
            button.title = 'Hide Heatmap';
        } else {
            icon.className = 'fas fa-fire';
            button.title = 'Show Heatmap';
        }
    }
}

// Show journey path between selected memories
function showJourneyPath() {
    // Clear any existing directions
    if (directionsRenderer) {
        directionsRenderer.setMap(null);
    }
    
    // Need at least 2 markers to show a path
    if (selectedMarkers.length < 2) {
        alert('Please select at least 2 memories to show a journey path');
        return;
    }
    
    // Sort markers by date if possible
    selectedMarkers.sort((a, b) => {
        // If dates exist, sort by date
        if (a.memory && a.memory.visit_date && b.memory && b.memory.visit_date) {
            return new Date(a.memory.visit_date) - new Date(b.memory.visit_date);
        }
        return 0;
    });
    
    // Set up waypoints
    const origin = selectedMarkers[0].getPosition();
    const destination = selectedMarkers[selectedMarkers.length - 1].getPosition();
    const waypoints = selectedMarkers.slice(1, -1).map(marker => ({
        location: marker.getPosition(),
        stopover: true
    }));
    
    // Set up request
    const request = {
        origin: origin,
        destination: destination,
        waypoints: waypoints,
        optimizeWaypoints: false,
        travelMode: google.maps.TravelMode.DRIVING
    };
    
    // Get directions
    directionsService.route(request, (result, status) => {
        if (status === google.maps.DirectionsStatus.OK) {
            directionsRenderer.setMap(map);
            directionsRenderer.setDirections(result);
        } else {
            alert('Could not display directions due to: ' + status);
        }
    });
}

// Filter markers by tags
function filterMarkersByTag(tag) {
    // If tag is empty, show all markers
    if (!tag || tag === 'all') {
        markers.forEach(marker => marker.setVisible(true));
    } else {
        // Hide all markers first
        markers.forEach(marker => {
            // Check if the marker has the tag
            if (marker.memory && marker.memory.tags && marker.memory.tags.includes(tag)) {
                marker.setVisible(true);
            } else {
                marker.setVisible(false);
            }
        });
    }
    
    // Update marker clusters
    if (markerCluster) {
        markerCluster.repaint();
    }
    
    // Update visible memory count
    const visibleMarkers = markers.filter(marker => marker.getVisible());
    document.getElementById('memory-count').textContent = visibleMarkers.length;
}

// Handle map loading errors
function handleMapError() {
    hideLoader();
    const mapElement = document.getElementById('map');
    mapElement.style.height = '100px';
    mapElement.innerHTML = `
        <div class="alert alert-danger m-3">
            <h4><i class="fas fa-exclamation-triangle"></i> Map could not be loaded</h4>
            <p>There was an error loading the Google Maps API. Please try again later or contact support.</p>
        </div>
    `;
}