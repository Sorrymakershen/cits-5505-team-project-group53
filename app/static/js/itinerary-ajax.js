/**
 * Itinerary AJAX Operations
 * Provides functionality for real-time updates to travel itinerary items
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize itinerary item operations if we're on the itinerary page
    if (document.getElementById('itineraryItems') || document.querySelector('.itinerary-container')) {
        initItineraryOperations();
    }
});

/**
 * Initialize all itinerary related operations
 */
function initItineraryOperations() {
    // Add event listeners for add/edit/delete buttons
    setupItineraryControls();
    
    // Setup drag and drop for itinerary items if the library is available
    if (typeof Sortable !== 'undefined') {
        setupItineraryDragDrop();
    }
    
    // Listen for form submissions on add/edit forms
    const addItemForm = document.getElementById('addItemForm');
    if (addItemForm) {
        addItemForm.addEventListener('submit', handleAddItemSubmit);
    }
    
    const editItemForms = document.querySelectorAll('.edit-item-form');
    editItemForms.forEach(form => {
        form.addEventListener('submit', handleEditItemSubmit);
    });
}

/**
 * Setup event listeners for itinerary control buttons
 */
function setupItineraryControls() {
    // Add item button
    const addButtons = document.querySelectorAll('.add-item-btn');
    addButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const dayNumber = this.getAttribute('data-day');
            showAddItemModal(dayNumber);
        });
    });
    
    // Edit buttons - use event delegation for dynamically added elements
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('edit-item-btn')) {
            const itemId = e.target.getAttribute('data-item-id');
            showEditItemModal(itemId);
        }
    });
    
    // Delete buttons - use event delegation
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('delete-item-btn')) {
            const itemId = e.target.getAttribute('data-item-id');
            confirmDeleteItem(itemId);
        }
    });
}

/**
 * Setup drag and drop functionality for itinerary items
 */
function setupItineraryDragDrop() {
    const containers = document.querySelectorAll('.day-items-container');
    
    containers.forEach(container => {
        new Sortable(container, {
            group: 'itinerary',
            animation: 150,
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            dragClass: 'sortable-drag',
            onEnd: function(evt) {
                // Get the new order and update in the database
                const itemId = evt.item.getAttribute('data-item-id');
                const newDay = evt.to.getAttribute('data-day');
                const newIndex = evt.newIndex;
                
                updateItemOrder(itemId, newDay, newIndex);
            }
        });
    });
}

/**
 * Handle add item form submission via AJAX
 * @param {Event} e - Form submit event
 */
function handleAddItemSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const planId = form.getAttribute('data-plan-id');
    const formData = new FormData(form);
    
    // Show loading state
    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';
    
    // Send AJAX request
    fetch(`/planner/${planId}/itinerary/add-item`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addItemModal'));
            modal.hide();
            
            // Add the new item to the page
            addItemToDOM(data.item);
            
            // Reset the form
            form.reset();
            
            // Show success message
            showNotification('Item added successfully!', 'success');
            
            // Refresh map markers if map exists
            if (typeof refreshMapMarkers === 'function') {
                refreshMapMarkers();
            }
        } else {
            showNotification(data.message || 'Failed to add item', 'danger');
        }
    })
    .catch(error => {
        console.error('Error adding item:', error);
        showNotification('An error occurred while adding the item', 'danger');
    })
    .finally(() => {
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

/**
 * Handle edit item form submission via AJAX
 * @param {Event} e - Form submit event
 */
function handleEditItemSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const itemId = form.getAttribute('data-item-id');
    const formData = new FormData(form);
    
    // Show loading state
    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    
    // Send AJAX request
    fetch(`/planner/itinerary/edit-item/${itemId}`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editItemModal'));
            modal.hide();
            
            // Update the item in the DOM
            updateItemInDOM(data.item);
            
            // Show success message
            showNotification('Item updated successfully!', 'success');
            
            // Refresh map markers if map exists
            if (typeof refreshMapMarkers === 'function') {
                refreshMapMarkers();
            }
        } else {
            showNotification(data.message || 'Failed to update item', 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating item:', error);
        showNotification('An error occurred while updating the item', 'danger');
    })
    .finally(() => {
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

/**
 * Confirm and delete an itinerary item
 * @param {string} itemId - ID of the item to delete
 */
function confirmDeleteItem(itemId) {
    if (confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
        deleteItem(itemId);
    }
}

/**
 * Delete an itinerary item via AJAX
 * @param {string} itemId - ID of the item to delete
 */
function deleteItem(itemId) {
    // Get the CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    // Create form data with CSRF token
    const formData = new FormData();
    if (csrfToken) {
        formData.append('csrf_token', csrfToken);
    }
    
    // Send AJAX request
    fetch(`/planner/itinerary/delete-item/${itemId}`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Remove the item from the DOM
            removeItemFromDOM(itemId);
            
            // Show success message
            showNotification('Item deleted successfully!', 'success');
            
            // Refresh map markers if map exists
            if (typeof refreshMapMarkers === 'function') {
                refreshMapMarkers();
            }
        } else {
            showNotification(data.message || 'Failed to delete item', 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting item:', error);
        showNotification('An error occurred while deleting the item', 'danger');
    });
}

/**
 * Update item order after drag and drop
 * @param {string} itemId - ID of the item being moved
 * @param {string} newDay - The new day number
 * @param {number} newIndex - The new position index
 */
function updateItemOrder(itemId, newDay, newIndex) {
    // Get the CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    // Create form data
    const formData = new FormData();
    formData.append('day', newDay);
    formData.append('position', newIndex);
    if (csrfToken) {
        formData.append('csrf_token', csrfToken);
    }
    
    // Send AJAX request
    fetch(`/planner/itinerary/reorder-item/${itemId}`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification('Item order updated!', 'success');
        } else {
            showNotification(data.message || 'Failed to update item order', 'danger');
            // Should refresh the page to get the correct order
            setTimeout(() => window.location.reload(), 2000);
        }
    })
    .catch(error => {
        console.error('Error updating item order:', error);
        showNotification('An error occurred while updating the order', 'danger');
        // Should refresh the page to get the correct order
        setTimeout(() => window.location.reload(), 2000);
    });
}

/**
 * Show modal for adding a new itinerary item
 * @param {string} dayNumber - The day number for the new item
 */
function showAddItemModal(dayNumber) {
    const modal = document.getElementById('addItemModal');
    if (!modal) return;
    
    // Set the day in the form
    const dayInput = modal.querySelector('#day');
    if (dayInput) {
        dayInput.value = dayNumber;
    }
    
    // Set the modal title
    const modalTitle = modal.querySelector('.modal-title');
    if (modalTitle) {
        modalTitle.textContent = `Add Activity for Day ${dayNumber}`;
    }
    
    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

/**
 * Show modal for editing an existing itinerary item
 * @param {string} itemId - ID of the item to edit
 */
function showEditItemModal(itemId) {
    // Fetch the item data first
    fetch(`/planner/itinerary/get-item/${itemId}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            populateEditModal(data.item);
        } else {
            showNotification(data.message || 'Failed to load item data', 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading item data:', error);
        showNotification('An error occurred while loading the item data', 'danger');
    });
}

/**
 * Populate the edit modal with item data
 * @param {Object} item - The item data
 */
function populateEditModal(item) {
    const modal = document.getElementById('editItemModal');
    if (!modal) return;
    
    // Set the item ID in the form
    const form = modal.querySelector('form');
    form.setAttribute('data-item-id', item.id);
    
    // Fill in form fields
    const dayInput = modal.querySelector('#edit_day');
    const timeInput = modal.querySelector('#edit_time');
    const activityInput = modal.querySelector('#edit_activity');
    const locationInput = modal.querySelector('#edit_location');
    const latInput = modal.querySelector('#edit_lat');
    const lngInput = modal.querySelector('#edit_lng');
    const costInput = modal.querySelector('#edit_cost');
    const notesInput = modal.querySelector('#edit_notes');
    
    if (dayInput) dayInput.value = item.day;
    if (timeInput) timeInput.value = item.time || '';
    if (activityInput) activityInput.value = item.activity;
    if (locationInput) locationInput.value = item.location || '';
    if (latInput) latInput.value = item.lat || '';
    if (lngInput) lngInput.value = item.lng || '';
    if (costInput) costInput.value = item.cost || '';
    if (notesInput) notesInput.value = item.notes || '';
    
    // Set the modal title
    const modalTitle = modal.querySelector('.modal-title');
    if (modalTitle) {
        modalTitle.textContent = `Edit Activity: ${item.activity}`;
    }
    
    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

/**
 * Add a new item to the DOM
 * @param {Object} item - The new item data
 */
function addItemToDOM(item) {
    const container = document.querySelector(`.day-items-container[data-day="${item.day}"]`);
    if (!container) return;
    
    // Create the new item element
    const itemElement = document.createElement('div');
    itemElement.className = 'itinerary-item';
    itemElement.setAttribute('data-item-id', item.id);
    
    // Format time if available
    const timeDisplay = item.time ? `${item.time} - ` : '';
    
    // Format cost if available
    const costDisplay = item.cost ? `<span class="badge bg-success">$${item.cost.toFixed(2)}</span>` : '';
    
    // Create the item HTML
    itemElement.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <h5 class="mb-1">${timeDisplay}${item.activity}</h5>
                <p class="mb-1">${item.location || 'No location specified'}</p>
                <p class="text-muted small mb-2">${item.notes || ''}</p>
            </div>
            <div class="ms-3">
                ${costDisplay}
            </div>
        </div>
        <div class="d-flex mt-2">
            <button type="button" class="btn btn-sm btn-outline-primary edit-item-btn me-2" data-item-id="${item.id}">
                <i class="fas fa-edit"></i> Edit
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger delete-item-btn" data-item-id="${item.id}">
                <i class="fas fa-trash"></i> Delete
            </button>
        </div>
    `;
    
    // Add the new item to the container
    container.appendChild(itemElement);
}

/**
 * Update an existing item in the DOM
 * @param {Object} item - The updated item data
 */
function updateItemInDOM(item) {
    const itemElement = document.querySelector(`.itinerary-item[data-item-id="${item.id}"]`);
    if (!itemElement) return;
    
    // If the day has changed, we need to move the element
    const currentDay = itemElement.closest('.day-items-container')?.getAttribute('data-day');
    if (currentDay && currentDay !== item.day.toString()) {
        // Remove from current container
        itemElement.remove();
        
        // Add to new container
        addItemToDOM(item);
        return;
    }
    
    // Format time if available
    const timeDisplay = item.time ? `${item.time} - ` : '';
    
    // Format cost if available
    const costDisplay = item.cost ? `<span class="badge bg-success">$${item.cost.toFixed(2)}</span>` : '';
    
    // Update the item HTML
    itemElement.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <h5 class="mb-1">${timeDisplay}${item.activity}</h5>
                <p class="mb-1">${item.location || 'No location specified'}</p>
                <p class="text-muted small mb-2">${item.notes || ''}</p>
            </div>
            <div class="ms-3">
                ${costDisplay}
            </div>
        </div>
        <div class="d-flex mt-2">
            <button type="button" class="btn btn-sm btn-outline-primary edit-item-btn me-2" data-item-id="${item.id}">
                <i class="fas fa-edit"></i> Edit
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger delete-item-btn" data-item-id="${item.id}">
                <i class="fas fa-trash"></i> Delete
            </button>
        </div>
    `;
}

/**
 * Remove an item from the DOM
 * @param {string} itemId - ID of the item to remove
 */
function removeItemFromDOM(itemId) {
    const itemElement = document.querySelector(`.itinerary-item[data-item-id="${itemId}"]`);
    if (itemElement) {
        // Add a fade out animation
        itemElement.style.transition = 'opacity 0.3s ease';
        itemElement.style.opacity = '0';
        
        // Remove after animation completes
        setTimeout(() => {
            itemElement.remove();
            
            // If this was the last item in the day, show an empty message
            const container = document.querySelector(`.day-items-container[data-day]`);
            if (container && container.children.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">No activities planned for this day. Click "Add Activity" to get started.</p>';
            }
        }, 300);
    }
}

/**
 * Show a notification to the user
 * @param {string} message - The message to display
 * @param {string} type - The notification type (success, danger, warning, info)
 */
function showNotification(message, type = 'info') {
    // Create notification container if it doesn't exist
    let notifContainer = document.getElementById('notification-container');
    if (!notifContainer) {
        notifContainer = document.createElement('div');
        notifContainer.id = 'notification-container';
        notifContainer.style.position = 'fixed';
        notifContainer.style.top = '20px';
        notifContainer.style.right = '20px';
        notifContainer.style.zIndex = '9999';
        document.body.appendChild(notifContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to container
    notifContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove from DOM after hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}
