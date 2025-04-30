/**
 * Memory Map Integration for Index Page
 * Adds map view capability to the memories index page
 * With marker clustering and date range filtering
 */

document.addEventListener('DOMContentLoaded', function() {
    // Debug to see if script is loading
    console.log('Memory map script loaded');
    
    // View toggle functionality
    const viewToggleBtns = document.querySelectorAll('.view-toggle-btn');
    const memoryGrid = document.getElementById('memory-grid');
    const mapContainer = document.getElementById('memory-map-container');
    let map;
    let markers = [];
    let markerClusterGroup;
    let allMemories = []; // Store all memory data
    
    // Map initialization flag
    let mapInitialized = false;
    
    // Initialize date range picker
    if ($.fn.daterangepicker) {
        $('#date-range-filter').daterangepicker({
            opens: 'left',
            autoUpdateInput: false,
            locale: {
                cancelLabel: 'Clear',
                format: 'YYYY-MM-DD'
            }
        });
        
        $('#date-range-filter').on('apply.daterangepicker', function(ev, picker) {
            $(this).val(picker.startDate.format('YYYY-MM-DD') + ' to ' + picker.endDate.format('YYYY-MM-DD'));
        });
    
        $('#date-range-filter').on('cancel.daterangepicker', function(ev, picker) {
            $(this).val('');
        });
    } else {
        console.warn('daterangepicker not found, using simple date inputs');
        $('#date-range-filter').attr('type', 'text').attr('placeholder', 'YYYY-MM-DD to YYYY-MM-DD');
    }
    
    // Apply date filter
    $('#apply-date-filter').on('click', function() {
        filterMarkersByDate();
    });
    
    // Reset date filter
    $('#reset-date-filter').on('click', function() {
        $('#date-range-filter').val('');
        resetFilters();
    });
    
    // Toggle between grid and map views
    viewToggleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.getAttribute('data-view');
            console.log('View toggled to:', view);
            
            // Update active button
            viewToggleBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Toggle visibility
            if (view === 'map') {
                memoryGrid.style.display = 'none';
                mapContainer.style.display = 'block';
                
                // Initialize map if not already done
                if (!mapInitialized) {
                    console.log('Initializing map for the first time');
                    initializeMap();
                    mapInitialized = true;
                } else {
                    // If map is already initialized, we might need to refresh it
                    console.log('Map already initialized, invalidating size');
                    if (map) map.invalidateSize();
                }
            } else {
                memoryGrid.style.display = 'flex';
                mapContainer.style.display = 'none';
            }
        });
    });
    
    // Initialize Leaflet map
    function initializeMap() {
        console.log('Creating map object');
        // Create map
        map = L.map('memory-map', {
            center: [20, 0],
            zoom: 2,
            minZoom: 2,
            maxZoom: 18
        });
        
        // Add tile layer (OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(map);
        
        // Initialize marker cluster group
        markerClusterGroup = L.markerClusterGroup({
            disableClusteringAtZoom: 16,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: true,
            zoomToBoundsOnClick: true,
            maxClusterRadius: 50
        });
        
        map.addLayer(markerClusterGroup);
        
        // Wait for map to be ready
        setTimeout(() => {
            console.log('Map is ready, loading markers');
            // Load memory markers
            loadMemoryMarkers();
            
            // Map controls
            setupMapControls();
        }, 300);
    }
    
    // Load markers for memories
    function loadMemoryMarkers() {
        // Process memory data from the page - these are the card elements with memory-list-item inside
        const memoryCards = document.querySelectorAll('.card');
        console.log('Found memory cards:', memoryCards.length);
        
        if (memoryCards.length === 0) {
            console.log('No memory cards found on the page');
            return;
        }
        
        // Bounds to fit all markers
        const bounds = L.latLngBounds();
        let hasValidCoordinates = false;
        
        // Clear existing markers and memory data
        markerClusterGroup.clearLayers();
        markers = [];
        allMemories = [];
        
        // Process each memory card
        memoryCards.forEach(card => {
            const memoryItem = card.querySelector('.memory-list-item');
            if (!memoryItem) {
                console.log('No memory-list-item found in card');
                return;
            }
            
            const memoryId = memoryItem.getAttribute('data-id');
            const lat = parseFloat(memoryItem.getAttribute('data-lat'));
            const lng = parseFloat(memoryItem.getAttribute('data-lng'));
            
            console.log(`Memory ID: ${memoryId}, Lat: ${lat}, Lng: ${lng}`);
            
            // Skip if no valid coordinates
            if (isNaN(lat) || isNaN(lng)) {
                console.log(`Skipping memory ${memoryId} due to invalid coordinates`);
                return;
            }
            
            hasValidCoordinates = true;
            
            // Extract memory data from the card
            const title = card.querySelector('h5.card-title').textContent;
            
            // Location extraction - get the text from p.text-muted that contains map-marker-alt icon
            let location = 'Unknown location';
            const locationEl = memoryItem.querySelector('.text-muted i.fas.fa-map-marker-alt');
            if (locationEl && locationEl.parentNode) {
                const locationText = locationEl.parentNode.textContent;
                // Extract just the location part (remove any date part)
                const locationMatch = locationText.match(/(.+?)(?:\s+•|\s+$)/);
                location = locationMatch ? locationMatch[1].trim() : locationText.trim();
            }
            
            // Visit date extraction
            let visitDate = 'Date not specified';
            let visitDateObj = null;
            const visitDateEl = memoryItem.querySelector('.text-muted i.far.fa-calendar-alt');
            if (visitDateEl && visitDateEl.parentNode) {
                const dateText = visitDateEl.parentNode.textContent;
                const dateMatch = dateText.match(/•\s*(.+)/);
                visitDate = dateMatch ? dateMatch[1].trim() : 'Date not specified';
                
                // Try to parse date for filtering
                try {
                    // Assuming date format is YYYY-MM-DD
                    visitDateObj = new Date(visitDate);
                    if (isNaN(visitDateObj.getTime())) {
                        visitDateObj = null;
                    }
                } catch (e) {
                    console.warn(`Could not parse date: ${visitDate}`);
                    visitDateObj = null;
                }
            }
            
            // Get image if available
            let imagePath = null;
            const img = card.querySelector('img.card-img-top');
            if (img) {
                imagePath = img.getAttribute('src');
                console.log(`Found image for memory ${memoryId}: ${imagePath}`);
            }
            
            // Create memory object
            const memoryData = {
                id: memoryId,
                title: title,
                location: location,
                lat: lat,
                lng: lng,
                visit_date: visitDate,
                visit_date_obj: visitDateObj,
                image_path: imagePath,
                isRecent: memoryItem.classList.contains('recent')
            };
            
            // Store memory data
            allMemories.push(memoryData);
            
            // Create marker
            createMemoryMarker(memoryData);
            
            // Extend bounds
            bounds.extend([lat, lng]);
        });
        
        console.log(`Found ${markers.length} valid markers with coordinates`);
        
        // Fit map to markers if there are any valid coordinates
        if (hasValidCoordinates) {
            console.log('Fitting map to bounds');
            map.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 12
            });
        } else {
            console.log('No valid coordinates found, setting default view');
            map.setView([20, 0], 2);
        }
    }
    
    // Create a marker for a memory
    function createMemoryMarker(memory) {
        console.log(`Creating marker for ${memory.title} at [${memory.lat}, ${memory.lng}]`);
        
        // Create marker icon
        const icon = L.divIcon({
            className: 'custom-marker-icon',
            html: `<div style="background-color: ${memory.isRecent ? '#007bff' : '#dc3545'}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
                    <i class="fas fa-map-marker-alt" style="color: white;"></i>
                  </div>`,
            iconSize: [30, 30],
            iconAnchor: [15, 30],
            popupAnchor: [0, -30]
        });
        
        // Create marker
        const marker = L.marker([memory.lat, memory.lng], {
            icon: icon,
            title: memory.title,
            memoryId: memory.id
        });
        
        // Create popup content
        let popupContent = `
            <div class="memory-info-window">
                <h4>${memory.title}</h4>
                <p><i class="fas fa-map-marker-alt"></i> <strong>${memory.location}</strong></p>
                <p><i class="far fa-calendar-alt"></i> ${memory.visit_date || 'Date not specified'}</p>
        `;
        
        if (memory.image_path) {
            popupContent += `<img src="${memory.image_path}" alt="${memory.title}" class="memory-thumbnail">`;
        }
        
        popupContent += `
                <a href="/memories/${memory.id}" class="memory-details-link btn btn-sm btn-primary">
                    <i class="fas fa-eye"></i> View Details
                </a>
            </div>
        `;
        
        // Add popup to marker
        marker.bindPopup(popupContent);
        
        // Add click event to highlight item in list
        marker.on('click', function() {
            highlightMemoryInList(memory.id);
        });
        
        // Add marker to cluster group
        markerClusterGroup.addLayer(marker);
        
        // Add to markers array
        markers.push({
            marker: marker,
            memory: memory
        });
        
        return marker;
    }
    
    // Filter markers by date range
    function filterMarkersByDate() {
        const dateRangeInput = $('#date-range-filter').val();
        if (!dateRangeInput) {
            console.log('No date range specified, showing all markers');
            resetFilters();
            return;
        }
        
        // Parse date range
        let startDate, endDate;
        
        // Try to parse with daterangepicker format first
        const dateParts = dateRangeInput.split(' to ');
        if (dateParts.length === 2) {
            startDate = new Date(dateParts[0]);
            endDate = new Date(dateParts[1]);
        } else {
            // If not in daterangepicker format, try manual format (YYYY-MM-DD to YYYY-MM-DD)
            const manualMatch = dateRangeInput.match(/(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})/);
            if (manualMatch) {
                startDate = new Date(manualMatch[1]);
                endDate = new Date(manualMatch[2]);
            }
        }
        
        if (!startDate || !endDate || isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
            alert('Please enter a valid date range in the format YYYY-MM-DD to YYYY-MM-DD');
            return;
        }
        
        console.log(`Filtering markers by date range: ${startDate.toISOString().split('T')[0]} to ${endDate.toISOString().split('T')[0]}`);
        
        // Clear existing markers
        markerClusterGroup.clearLayers();
        
        // Filter memories by date range
        const filteredMemories = allMemories.filter(memory => {
            if (!memory.visit_date_obj) return false;
            
            // Set time to midday to avoid timezone issues
            const memoryDate = new Date(memory.visit_date_obj);
            memoryDate.setHours(12, 0, 0, 0);
            
            const startDateAdjusted = new Date(startDate);
            startDateAdjusted.setHours(0, 0, 0, 0);
            
            const endDateAdjusted = new Date(endDate);
            endDateAdjusted.setHours(23, 59, 59, 999);
            
            return memoryDate >= startDateAdjusted && memoryDate <= endDateAdjusted;
        });
        
        console.log(`Found ${filteredMemories.length} memories in the date range`);
        
        if (filteredMemories.length === 0) {
            alert('No memories found in the selected date range');
            return;
        }
        
        // Create new markers for filtered memories
        const bounds = L.latLngBounds();
        
        filteredMemories.forEach(memory => {
            createMemoryMarker(memory);
            bounds.extend([memory.lat, memory.lng]);
        });
        
        // Fit map to filtered markers
        map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 12
        });
    }
    
    // Reset filters and show all markers
    function resetFilters() {
        console.log('Resetting filters');
        
        // Clear existing markers
        markerClusterGroup.clearLayers();
        
        // Add all markers back
        const bounds = L.latLngBounds();
        
        allMemories.forEach(memory => {
            createMemoryMarker(memory);
            bounds.extend([memory.lat, memory.lng]);
        });
        
        // Fit map to all markers
        if (bounds.isValid()) {
            map.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 12
            });
        }
    }
    
    // Highlight a memory in the list
    function highlightMemoryInList(memoryId) {
        const listItems = document.querySelectorAll('.memory-list-item');
        listItems.forEach(item => {
            item.classList.remove('highlighted');
        });
        
        const selectedItem = document.querySelector(`.memory-list-item[data-id="${memoryId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('highlighted');
            selectedItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    // Set up map controls
    function setupMapControls() {
        // World view button
        const zoomWorldBtn = document.getElementById('zoomWorld');
        if (zoomWorldBtn) {
            zoomWorldBtn.addEventListener('click', function() {
                map.setView([20, 0], 2);
            });
        }
        
        // Toggle terrain button
        const toggleTerrainBtn = document.getElementById('toggleTerrain');
        if (toggleTerrainBtn) {
            let terrainMode = false;
            toggleTerrainBtn.addEventListener('click', function() {
                // Remove current tile layers
                map.eachLayer(layer => {
                    if (layer instanceof L.TileLayer) {
                        map.removeLayer(layer);
                    }
                });
                
                if (terrainMode) {
                    // Switch to normal map
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                        maxZoom: 19
                    }).addTo(map);
                    this.querySelector('i').className = 'fas fa-mountain';
                    this.title = 'Switch to Terrain View';
                } else {
                    // Switch to terrain map
                    L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; <a href="https://opentopomap.org">OpenTopoMap</a> contributors',
                        maxZoom: 17
                    }).addTo(map);
                    this.querySelector('i').className = 'fas fa-map';
                    this.title = 'Switch to Street View';
                }
                
                terrainMode = !terrainMode;
            });
        }
    }
});