/**
 * Form Validation Functions
 * Provides client-side validation for various forms throughout the application
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all forms with validation
    initFormValidation();
    
    // Initialize password strength meters if they exist
    initPasswordStrengthMeter();
    
    // Initialize date validation for any date inputs
    initDateValidation();
});

/**
 * Initialize Bootstrap form validation for all forms with 'needs-validation' class
 */
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
            
            // Run custom validations if defined
            if (form.dataset.validateFunction) {
                const validationFunction = window[form.dataset.validateFunction];
                if (typeof validationFunction === 'function') {
                    const isValid = validationFunction(form);
                    if (!isValid) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                }
            }
        }, false);
    });
}

/**
 * Initialize password strength meter
 */
function initPasswordStrengthMeter() {
    const passwordInputs = document.querySelectorAll('input[type="password"][data-strength-meter]');
    
    passwordInputs.forEach(input => {
        const meterContainer = document.createElement('div');
        meterContainer.className = 'password-strength-meter mt-2';
        meterContainer.innerHTML = `
            <div class="progress" style="height: 5px;">
                <div class="progress-bar" role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
            <small class="text-muted strength-text">Password strength: Too weak</small>
        `;
        
        input.parentNode.insertBefore(meterContainer, input.nextSibling);
        
        input.addEventListener('input', () => {
            updatePasswordStrength(input.value, meterContainer);
        });
    });
    
    // Add validation for username field
    const usernameInputs = document.querySelectorAll('input#username');
    usernameInputs.forEach(input => {
        input.addEventListener('input', () => {
            validateUsernameUppercase(input);
        });
    });
}

/**
 * Update password strength indicator
 * @param {string} password - The password to evaluate
 * @param {HTMLElement} container - The container element for the strength meter
 */
function updatePasswordStrength(password, container) {
    const progressBar = container.querySelector('.progress-bar');
    const strengthText = container.querySelector('.strength-text');
    
    // Simple password strength algorithm
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 25;
    
    // Complexity checks
    if (/[A-Z]/.test(password)) strength += 25; // Has uppercase
    if (/[0-9]/.test(password)) strength += 25; // Has number
    if (/[^A-Za-z0-9]/.test(password)) strength += 25; // Has special char
    
    // Update UI
    progressBar.style.width = `${strength}%`;
    progressBar.setAttribute('aria-valuenow', strength);
    
    // Change color based on strength
    if (strength < 25) {
        progressBar.className = 'progress-bar bg-danger';
        strengthText.textContent = 'Password strength: Too weak';
    } else if (strength < 50) {
        progressBar.className = 'progress-bar bg-warning';
        strengthText.textContent = 'Password strength: Weak';
    } else if (strength < 75) {
        progressBar.className = 'progress-bar bg-info';
        strengthText.textContent = 'Password strength: Good';
    } else {
        progressBar.className = 'progress-bar bg-success';
        strengthText.textContent = 'Password strength: Strong';
    }
}

/**
 * Initialize date validation for trip planning
 */
function initDateValidation() {
    const startDateInputs = document.querySelectorAll('input[type="date"][id="start_date"]');
    const endDateInputs = document.querySelectorAll('input[type="date"][id="end_date"]');
    
    startDateInputs.forEach(input => {
        const today = new Date().toISOString().split('T')[0];
        input.setAttribute('min', today);
        
        // Find related end date input in the same form
        const form = input.closest('form');
        if (form) {
            const endDateInput = form.querySelector('#end_date');
            if (endDateInput) {
                input.addEventListener('change', () => {
                    endDateInput.setAttribute('min', input.value);
                    if (endDateInput.value && endDateInput.value < input.value) {
                        endDateInput.value = input.value;
                    }
                });
            }
        }
    });
}

/**
 * Validate registration form with custom rules
 * @param {HTMLFormElement} form - The form element to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateRegistrationForm(form) {
    let isValid = true;
    
    // Get form fields
    const usernameInput = form.querySelector('#username');
    const passwordInput = form.querySelector('#password');
    const confirmPasswordInput = form.querySelector('#confirm_password');
    
    // Check if username contains uppercase letter
    if (usernameInput && usernameInput.value.trim() !== '') {
        if (!/[A-Z]/.test(usernameInput.value)) {
            // Update feedback message
            let feedback = usernameInput.nextElementSibling;
            if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                usernameInput.parentNode.appendChild(feedback);
            }
            feedback.textContent = 'Username must contain at least one uppercase letter';
            usernameInput.setCustomValidity('Username must contain at least one uppercase letter');
            isValid = false;
        } else {
            usernameInput.setCustomValidity('');
        }
    }
    
    // Check if passwords match
    if (passwordInput && confirmPasswordInput) {
        if (passwordInput.value !== confirmPasswordInput.value) {
            // Create or update feedback message
            let feedback = confirmPasswordInput.parentNode.querySelector('.invalid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                confirmPasswordInput.parentNode.appendChild(feedback);
            }
            feedback.textContent = 'Passwords do not match';
            confirmPasswordInput.setCustomValidity('Passwords do not match');
            isValid = false;
        } else {
            confirmPasswordInput.setCustomValidity('');
        }
    }
    
    return isValid;
}

/**
 * Validate login form with custom rules
 * @param {HTMLFormElement} form - The form element to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateLoginForm(form) {
    let isValid = true;
    
    // Get form fields
    const emailInput = form.querySelector('#email');
    const passwordInput = form.querySelector('#password');
    
    // Check email format
    if (emailInput && emailInput.value.trim() !== '') {
        if (!isValidEmail(emailInput.value)) {
            emailInput.setCustomValidity('Please enter a valid email address');
            isValid = false;
        } else {
            emailInput.setCustomValidity('');
        }
    }
    
    // Validate password not empty
    if (passwordInput && passwordInput.value.trim() === '') {
        passwordInput.setCustomValidity('Password cannot be empty');
        isValid = false;
    } else {
        passwordInput.setCustomValidity('');
    }
    
    return isValid;
}

/**
 * Toggle password visibility
 * @param {string} buttonId - ID of the toggle button
 * @param {string} passwordId - ID of the password input
 */
function togglePasswordVisibility(buttonId, passwordId) {
    const passwordInput = document.getElementById(passwordId);
    const toggleButton = document.getElementById(buttonId);
    
    if (!passwordInput || !toggleButton) return;
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleButton.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        passwordInput.type = 'password';
        toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

/**
 * Validate email format
 * @param {string} email - The email to validate
 * @returns {boolean} - Whether the email is valid
 */
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

/**
 * Validate username contains uppercase letters
 * @param {HTMLInputElement} input - The username input element
 * @returns {boolean} - Whether the username is valid
 */
function validateUsernameUppercase(input) {
    const value = input.value;
    const hasUppercase = /[A-Z]/.test(value);
    
    if (!hasUppercase && value.length > 0) {
        input.setCustomValidity('Username must contain at least one uppercase letter');
        return false;
    } else {
        input.setCustomValidity('');
        return true;
    }
}

/**
 * Validate budget input to ensure it's a positive number
 * @param {HTMLInputElement} input - The budget input element
 */
function validateBudgetInput(input) {
    const value = parseFloat(input.value);
    if (isNaN(value) || value < 0) {
        input.setCustomValidity('Please enter a valid positive amount');
    } else {
        input.setCustomValidity('');
    }
}
