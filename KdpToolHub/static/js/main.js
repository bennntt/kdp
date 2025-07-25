// KDP Tools - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeSidebar();
    initializeTooltips();
    initializePopovers();
    initializeFormValidation();
    initializeLoadingStates();
    initializeAutoSave();
    initializePrintHandlers();
    
    // Show page loaded animation
    document.body.classList.add('fade-in');
});

// Sidebar Management (Toggle functionality removed)
function initializeSidebar() {
    // Sidebar functionality has been disabled
    // The sidebar is now always visible without toggle capability
}

// Initialize Bootstrap Components
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Form Validation and Enhancement
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add client-side validation
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation for specific fields
        const emailFields = form.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            field.addEventListener('blur', validateEmail);
        });
        
        const passwordFields = form.querySelectorAll('input[type="password"]');
        passwordFields.forEach(field => {
            field.addEventListener('input', validatePassword);
        });
    });
}

function validateEmail(event) {
    const field = event.target;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (field.value && !emailRegex.test(field.value)) {
        field.setCustomValidity('Please enter a valid email address');
    } else {
        field.setCustomValidity('');
    }
}

function validatePassword(event) {
    const field = event.target;
    const minLength = 6;
    
    if (field.value.length < minLength) {
        field.setCustomValidity(`Password must be at least ${minLength} characters long`);
    } else {
        field.setCustomValidity('');
    }
    
    // Check for confirm password field
    const confirmField = document.querySelector('input[name*="confirm"]');
    if (confirmField && field.name.includes('password')) {
        validatePasswordConfirmation(confirmField);
    }
}

function validatePasswordConfirmation(confirmField) {
    const passwordField = document.querySelector('input[name*="password"]:not([name*="confirm"])');
    
    if (passwordField && confirmField.value !== passwordField.value) {
        confirmField.setCustomValidity('Passwords do not match');
    } else {
        confirmField.setCustomValidity('');
    }
}

// Loading States
function initializeLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                showLoading(submitBtn);
            }
        });
    });
}

function showLoading(element, text = 'Loading...') {
    element.disabled = true;
    element.dataset.originalText = element.innerHTML;
    element.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${text}`;
}

function hideLoading(element) {
    element.disabled = false;
    element.innerHTML = element.dataset.originalText || element.innerHTML;
}

// Auto-save Functionality
function initializeAutoSave() {
    const textareas = document.querySelectorAll('textarea');
    const inputs = document.querySelectorAll('input[type="text"], input[type="email"]');
    
    [...textareas, ...inputs].forEach(field => {
        if (field.form && field.form.dataset.autosave) {
            field.addEventListener('input', debounce(function() {
                autoSaveField(field);
            }, 2000));
            
            // Load saved data
            loadSavedData(field);
        }
    });
}

function autoSaveField(field) {
    const key = `autosave_${field.name}_${window.location.pathname}`;
    localStorage.setItem(key, field.value);
    
    // Show save indicator
    showSaveIndicator(field);
}

function loadSavedData(field) {
    const key = `autosave_${field.name}_${window.location.pathname}`;
    const savedValue = localStorage.getItem(key);
    
    if (savedValue && !field.value) {
        field.value = savedValue;
    }
}

function showSaveIndicator(field) {
    // Remove existing indicator
    const existingIndicator = field.parentNode.querySelector('.save-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Add new indicator
    const indicator = document.createElement('small');
    indicator.className = 'save-indicator text-success';
    indicator.innerHTML = '<i class="fas fa-check me-1"></i>Saved';
    field.parentNode.appendChild(indicator);
    
    // Remove after 2 seconds
    setTimeout(() => {
        indicator.remove();
    }, 2000);
}

// Print Handlers
function initializePrintHandlers() {
    const printButtons = document.querySelectorAll('[onclick*="print"]');
    
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            preparePrint();
            window.print();
        });
    });
}

function preparePrint() {
    // Hide non-essential elements for printing
    const elementsToHide = [
        '.btn', '.navbar', '.sidebar', '.alert-dismissible .btn-close'
    ];
    
    elementsToHide.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            el.style.display = 'none';
        });
    });
    
    // Restore after print
    window.addEventListener('afterprint', function() {
        elementsToHide.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.display = '';
            });
        });
    });
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showToast(message, type = 'success') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    
    // Add to page
    document.body.appendChild(toast);
    
    // Remove after delay
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function copyToClipboard(text, buttonId) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            if (buttonId) {
                showInlineCopied(buttonId);
            } else {
                showToast('Copied to clipboard!');
            }
        }).catch(() => {
            fallbackCopyToClipboard(text, buttonId);
        });
    } else {
        fallbackCopyToClipboard(text, buttonId);
    }
}

function fallbackCopyToClipboard(text, buttonId) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        if (buttonId) {
            showInlineCopied(buttonId);
        } else {
            showToast('Copied to clipboard!');
        }
    } catch (err) {
        showToast('Failed to copy to clipboard', 'error');
    }
    
    document.body.removeChild(textArea);
}

// Analytics and Tracking
function trackEvent(category, action, label = null) {
    // Add your analytics tracking code here
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            event_category: category,
            event_label: label
        });
    }
    
    // Console log for development
    console.log('Event tracked:', { category, action, label });
}

// Form Enhancement for Specific Pages
function enhanceRegistrationForm() {
    const form = document.querySelector('#registrationForm');
    if (!form) return;
    
    const detectLocationBtn = document.querySelector('#detectLocation');
    if (detectLocationBtn) {
        detectLocationBtn.addEventListener('click', function() {
            if (navigator.geolocation) {
                showLoading(detectLocationBtn, 'Detecting...');
                
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        // In a real implementation, reverse geocode these coordinates
                        hideLoading(detectLocationBtn);
                        showToast('Location detected! Please verify the details.');
                        
                        // Populate form fields (demo)
                        document.querySelector('[name="country"]').value = 'United States';
                        document.querySelector('[name="city"]').value = 'New York';
                    },
                    function(error) {
                        hideLoading(detectLocationBtn);
                        showToast('Unable to detect location. Please enter manually.', 'warning');
                    }
                );
            } else {
                showToast('Geolocation is not supported by this browser.', 'error');
            }
        });
    }
}

// Tool-specific enhancements
function enhanceToolPages() {
    // Character counters for text fields
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        addCharacterCounter(textarea);
    });
    
    // Progress indicators for forms
    const forms = document.querySelectorAll('.tool-form');
    forms.forEach(form => {
        addProgressIndicator(form);
    });
}

function addCharacterCounter(textarea) {
    const counter = document.createElement('small');
    counter.className = 'text-muted character-counter';
    textarea.parentNode.appendChild(counter);
    
    function updateCounter() {
        const length = textarea.value.length;
        const maxLength = textarea.getAttribute('maxlength');
        
        if (maxLength) {
            counter.textContent = `${length}/${maxLength} characters`;
            
            if (length > maxLength * 0.9) {
                counter.className = 'text-warning character-counter';
            } else {
                counter.className = 'text-muted character-counter';
            }
        } else {
            counter.textContent = `${length} characters`;
        }
    }
    
    textarea.addEventListener('input', updateCounter);
    updateCounter(); // Initial count
}

function addProgressIndicator(form) {
    const fields = form.querySelectorAll('input[required], textarea[required], select[required]');
    const progressBar = document.createElement('div');
    progressBar.className = 'progress mb-3';
    progressBar.innerHTML = '<div class="progress-bar" role="progressbar"></div>';
    
    form.insertBefore(progressBar, form.firstChild);
    
    function updateProgress() {
        const filledFields = Array.from(fields).filter(field => field.value.trim() !== '').length;
        const progress = (filledFields / fields.length) * 100;
        
        const bar = progressBar.querySelector('.progress-bar');
        bar.style.width = `${progress}%`;
        bar.setAttribute('aria-valuenow', progress);
    }
    
    fields.forEach(field => {
        field.addEventListener('input', updateProgress);
        field.addEventListener('change', updateProgress);
    });
    
    updateProgress(); // Initial progress
}

// Initialize page-specific enhancements
if (document.querySelector('#registrationForm')) {
    enhanceRegistrationForm();
}

if (document.querySelector('.tool-form')) {
    enhanceToolPages();
}

// Global error handler
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    // Optionally send to error tracking service
});

// Performance monitoring
window.addEventListener('load', function() {
    // Track page load time
    const loadTime = performance.now();
    trackEvent('Performance', 'Page Load Time', Math.round(loadTime));
});

function showInlineCopied(buttonId) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i> Copied';
    button.classList.remove('btn-outline-secondary', 'btn-outline-primary');
    button.classList.add('btn-success');
    
    setTimeout(() => {
        button.innerHTML = originalContent;
        button.classList.remove('btn-success');
        button.classList.add('btn-outline-secondary');
    }, 2000);
}

// Export functions for global use
window.KDPTools = {
    showToast,
    copyToClipboard,
    showInlineCopied,
    trackEvent,
    showLoading,
    hideLoading
};
