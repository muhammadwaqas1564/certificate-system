/**
 * Main JavaScript for Certificate Verification System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Form validation enhancement
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
    
    // File upload validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const files = this.files;
            const maxSize = 16 * 1024 * 1024; // 16MB
            const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                
                // Check file size
                if (file.size > maxSize) {
                    alert(`File "${file.name}" exceeds maximum size of 16MB`);
                    this.value = '';
                    return;
                }
                
                // Check file type
                if (!allowedTypes.includes(file.type)) {
                    alert(`File "${file.name}" is not a supported file type. Please upload PDF, PNG, or JPG files.`);
                    this.value = '';
                    return;
                }
            }
        });
    });
    
    // Email validation helper
    window.validateGmail = function(email) {
        const pattern = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;
        return pattern.test(email);
    };
    
    // Copy to clipboard functionality
    window.copyToClipboard = function(text, button) {
        navigator.clipboard.writeText(text).then(function() {
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.classList.add('btn-success');
            button.classList.remove('btn-outline-secondary');
            
            setTimeout(function() {
                button.innerHTML = originalHTML;
                button.classList.remove('btn-success');
                button.classList.add('btn-outline-secondary');
            }, 2000);
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            alert('Failed to copy to clipboard');
        });
    };
    
    // Print certificate
    window.printCertificate = function() {
        window.print();
    };
    
    // Share certificate functionality
    window.shareCertificate = function(url, title) {
        if (navigator.share) {
            navigator.share({
                title: title,
                text: 'Check out my certificate',
                url: url
            })
            .then(() => console.log('Successful share'))
            .catch(error => console.log('Error sharing:', error));
        } else {
            // Fallback: copy link to clipboard
            copyToClipboard(url, document.querySelector('#shareBtn'));
        }
    };
    
    // File size formatter
    window.formatFileSize = function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    // Initialize file size display
    const fileSizeElements = document.querySelectorAll('.file-size');
    fileSizeElements.forEach(el => {
        const bytes = parseInt(el.dataset.size);
        if (!isNaN(bytes)) {
            el.textContent = formatFileSize(bytes);
        }
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Auto-focus on search input
    const searchInput = document.querySelector('input[name="email"]');
    if (searchInput && !searchInput.value) {
        searchInput.focus();
    }
    
    // Admin session timeout warning
    if (window.location.pathname.includes('/admin/')) {
        let timeoutWarning;
        
        function resetTimer() {
            clearTimeout(timeoutWarning);
            // Warn after 25 minutes of inactivity
            timeoutWarning = setTimeout(showTimeoutWarning, 25 * 60 * 1000);
        }
        
        function showTimeoutWarning() {
            if (confirm('Your session will expire in 5 minutes due to inactivity. Click OK to stay logged in.')) {
                resetTimer();
                // Send keep-alive request
                fetch('/admin/keep-alive', { method: 'POST' });
            }
        }
        
        // Reset timer on user activity
        ['click', 'mousemove', 'keypress', 'scroll'].forEach(event => {
            document.addEventListener(event, resetTimer);
        });
        
        resetTimer();
    }
    
    // Enhanced form submission with loading states
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(button => {
        const form = button.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                button.disabled = true;
                const originalText = button.innerHTML;
                button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
                
                // Re-enable button if form submission fails
                setTimeout(() => {
                    if (button.disabled) {
                        button.disabled = false;
                        button.innerHTML = originalText;
                    }
                }, 5000);
            });
        }
    });
});

// Utility functions
window.utils = {
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
};