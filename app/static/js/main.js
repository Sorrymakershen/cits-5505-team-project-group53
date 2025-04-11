// Main JavaScript file for Travel Planning Platform

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Initialize popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Add fade-in animation to cards
  const cards = document.querySelectorAll('.card');
  setTimeout(() => {
    cards.forEach((card, index) => {
      setTimeout(() => {
        card.classList.add('animate', 'fade-in');
      }, index * 100); // Staggered animation
    });
  }, 300);

  // Initialize timeline animations
  initializeTimelineAnimations();
  
  // Initialize maps if they exist on the page
  if (document.getElementById('planMap')) {
    initializePlanMap();
  }
  
  if (document.getElementById('memoriesMap')) {
    initializeMemoriesMap();
  }
  
  // Form validation
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
  
  // File input preview for photo uploads
  const photoUpload = document.getElementById('photo-upload');
  const previewContainer = document.getElementById('preview-container');
  
  if (photoUpload && previewContainer) {
    photoUpload.addEventListener('change', function() {
      previewContainer.innerHTML = ''; // Clear previous previews
      
      if (this.files) {
        Array.from(this.files).forEach(file => {
          if (file.type.match('image.*')) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
              const preview = document.createElement('div');
              preview.className = 'col-md-4 mb-3';
              preview.innerHTML = `
                <div class="card">
                  <img src="${e.target.result}" class="card-img-top" alt="Preview">
                  <div class="card-body">
                    <p class="card-text small text-muted">${file.name}</p>
                  </div>
                </div>
              `;
              previewContainer.appendChild(preview);
              
              // Add animation
              setTimeout(() => {
                preview.querySelector('.card').classList.add('animate', 'fade-in');
              }, 100);
            }
            
            reader.readAsDataURL(file);
          }
        });
      }
    });
  }
});

// Timeline animations with intersection observer
function initializeTimelineAnimations() {
  const timelineItems = document.querySelectorAll('.timeline-item');
  
  if (timelineItems.length > 0) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });
    
    timelineItems.forEach(item => {
      observer.observe(item);
    });
  }
}

// Initialize map for travel plan view
function initializePlanMap() {
  const mapElement = document.getElementById('planMap');
  const planItems = JSON.parse(mapElement.dataset.items || '[]');
  
  // Create map centered on first location or default to a world view
  let initialLat = 0;
  let initialLng = 0;
  let initialZoom = 2;
  
  if (planItems.length > 0 && planItems[0].lat && planItems[0].lng) {
    initialLat = planItems[0].lat;
    initialLng = planItems[0].lng;
    initialZoom = 12;
  }
  
  const map = L.map('planMap').setView([initialLat, initialLng], initialZoom);
  
  // Add tile layer (OpenStreetMap)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  }).addTo(map);
  
  // Add markers for each itinerary item
  const markers = [];
  planItems.forEach(item => {
    if (item.lat && item.lng) {
      const marker = L.marker([item.lat, item.lng], {
        title: item.activity,
        alt: item.activity
      }).addTo(map);
      
      // Create popup with item details
      marker.bindPopup(`
        <div class="map-popup">
          <h6>${item.activity}</h6>
          <p><strong>Day ${item.day}</strong> ${item.time ? ' - ' + item.time : ''}</p>
          <p>${item.location}</p>
          ${item.cost ? `<p>Cost: $${item.cost}</p>` : ''}
        </div>
      `);
      
      markers.push(marker);
    }
  });
  
  // Create a path connecting all points in order
  if (markers.length > 1) {
    const points = planItems
      .filter(item => item.lat && item.lng)
      .map(item => [item.lat, item.lng]);
      
    const polyline = L.polyline(points, {
      color: '#4285f4',
      weight: 3,
      opacity: 0.7,
      lineJoin: 'round'
    }).addTo(map);
    
    // Zoom map to fit all markers
    map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    
    // Add smooth animation to the polyline
    animatePolyline(polyline);
  } else if (markers.length === 1) {
    // If only one marker, center on it
    map.setView([planItems[0].lat, planItems[0].lng], 13);
  }
}

// Initialize map for memories view
function initializeMemoriesMap() {
  const mapElement = document.getElementById('memoriesMap');
  const memories = JSON.parse(mapElement.dataset.memories || '[]');
  
  // Create map centered on first memory or default to a world view
  let initialLat = 0;
  let initialLng = 0;
  let initialZoom = 2;
  
  if (memories.length > 0 && memories[0].lat && memories[0].lng) {
    initialLat = memories[0].lat;
    initialLng = memories[0].lng;
    initialZoom = 10;
  }
  
  const map = L.map('memoriesMap').setView([initialLat, initialLng], initialZoom);
  
  // Add tile layer (OpenStreetMap)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  }).addTo(map);
  
  // Add markers for each memory
  const markers = [];
  const colors = ['#4285f4', '#ea4335', '#fbbc05', '#34a853', '#46bdc6', '#7baaf7'];
  
  memories.forEach((memory, index) => {
    if (memory.lat && memory.lng) {
      // Create custom marker with rounded style
      const colorIndex = index % colors.length;
      const customIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="background-color: ${colors[colorIndex]};">${index + 1}</div>`,
        iconSize: [36, 36]
      });
      
      const marker = L.marker([memory.lat, memory.lng], {
        icon: customIcon,
        title: memory.title,
        alt: memory.title
      }).addTo(map);
      
      // Create popup with memory details and photo if available
      let popupContent = `
        <div class="map-popup">
          <h6>${memory.title}</h6>
          <p>${memory.visit_date ? new Date(memory.visit_date).toLocaleDateString() : ''}</p>
          <p>${memory.location || ''}</p>
      `;
      
      if (memory.photos && memory.photos.length > 0) {
        popupContent += `<img src="/static/uploads/${memory.photos[0].filename}" alt="${memory.title}" class="img-fluid rounded mb-2">`;
      }
      
      popupContent += `<a href="/memories/${memory.id}" class="btn btn-sm btn-primary">View Details</a></div>`;
      
      marker.bindPopup(popupContent);
      markers.push(marker);
    }
  });
  
  // If we have multiple markers, fit bounds
  if (markers.length > 1) {
    const group = new L.featureGroup(markers);
    map.fitBounds(group.getBounds(), { padding: [50, 50] });
  } else if (markers.length === 1) {
    // If only one marker, center on it
    map.setView([memories[0].lat, memories[0].lng], 13);
  }
}

// Animate polyline drawing
function animatePolyline(polyline) {
  // Hide the polyline initially
  polyline.setStyle({ opacity: 0 });
  
  // Get the polyline coordinates
  const coords = polyline.getLatLngs();
  const segments = [];
  
  // Create segments between each coordinate point
  for (let i = 0; i < coords.length - 1; i++) {
    segments.push([coords[i], coords[i + 1]]);
  }
  
  // Animate each segment with a delay
  segments.forEach((segment, index) => {
    setTimeout(() => {
      L.polyline(segment, {
        color: '#4285f4',
        weight: 3,
        opacity: 0.7,
        lineJoin: 'round'
      }).addTo(polyline._map);
    }, index * 300); // 300ms delay between segments
  });
}

// Handle drag and drop for photo uploads
function initializeDragDrop() {
  const dropArea = document.getElementById('drop-area');
  
  if (!dropArea) return;
  
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });
  
  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }
  
  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
  });
  
  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
  });
  
  function highlight() {
    dropArea.classList.add('highlight');
  }
  
  function unhighlight() {
    dropArea.classList.remove('highlight');
  }
  
  dropArea.addEventListener('drop', handleDrop, false);
  
  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    const photoUpload = document.getElementById('photo-upload');
    
    if (photoUpload) {
      photoUpload.files = files;
      // Trigger change event to show previews
      const event = new Event('change');
      photoUpload.dispatchEvent(event);
    }
  }
}

// Toggle visibility of password
function togglePasswordVisibility(buttonId, inputId) {
  const button = document.getElementById(buttonId);
  const input = document.getElementById(inputId);
  
  if (button && input) {
    button.addEventListener('click', () => {
      // Toggle input type
      input.type = input.type === 'password' ? 'text' : 'password';
      
      // Toggle button icon
      const icon = button.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
      }
    });
  }
}
