// TimeGuard Enhanced JavaScript

// Global state management
const TimeGuard = {
    timers: new Map(),
    notifications: [],
    theme: localStorage.getItem('theme') || 'light',
    
    // Initialize application
    init() {
        this.initializeComponents();
        this.setupEventListeners();
        this.loadTheme();
        this.startPeriodicUpdates();
    },
    
    // Initialize Bootstrap components
    initializeComponents() {
        // Tooltips
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });
        
        // Popovers
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => {
            new bootstrap.Popover(el);
        });
        
        // Auto-hide alerts
        this.autoHideAlerts();
        
        // Animate elements on load
        this.animateOnLoad();
    },
    
    // Setup event listeners
    setupEventListeners() {
        // Form submissions with loading states
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Button clicks with ripple effect
        document.addEventListener('click', this.handleButtonClick.bind(this));
        
        // Input validation
        document.addEventListener('input', this.handleInputChange.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboard.bind(this));
    },
    
    // Handle form submissions
    handleFormSubmit(event) {
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Skip validation for forms with no-validation class
        if (form.classList.contains('no-validation')) {
            return;
        }
        
        if (submitBtn && !form.classList.contains('no-loading')) {
            this.showLoading(submitBtn);
        }
        
        // Validate form
        if (!this.validateForm(form)) {
            event.preventDefault();
            this.hideLoading(submitBtn);
        }
    },
    
    // Handle button clicks with ripple effect
    handleButtonClick(event) {
        const btn = event.target.closest('.btn');
        if (btn && !btn.classList.contains('no-ripple')) {
            this.createRipple(btn, event);
        }
        
        // Handle specific button actions
        if (btn?.dataset.action) {
            this.handleAction(btn.dataset.action, btn);
        }
    },
    
    // Create ripple effect
    createRipple(button, event) {
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    },
    
    // Handle input changes with real-time validation
    handleInputChange(event) {
        const input = event.target;
        if (input.matches('input, select, textarea')) {
            this.validateInput(input);
            
            // Auto-save functionality
            if (input.dataset.autosave) {
                this.debounce(() => this.autoSave(input), 1000)();
            }
        }
    },
    
    // Handle keyboard shortcuts
    handleKeyboard(event) {
        // Ctrl/Cmd + S for save
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            const form = document.querySelector('form');
            if (form) form.requestSubmit();
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const modal = document.querySelector('.modal.show');
            if (modal) {
                bootstrap.Modal.getInstance(modal)?.hide();
            }
        }
    },
    
    // Enhanced form validation
    validateForm(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    },
    
    // Validate individual input
    validateInput(input) {
        const value = input.value.trim();
        const type = input.type;
        const form = input.closest('form');
        const isLoginForm = form && form.action && form.action.includes('/login');
        let isValid = true;
        let message = '';
        
        // Required validation
        if (input.hasAttribute('required') && !value) {
            isValid = false;
            message = 'This field is required';
        }
        // Email validation
        else if (type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            isValid = false;
            message = 'Please enter a valid email';
        }
        // Password validation - skip length check for login forms
        else if (type === 'password' && value && !isLoginForm && value.length < 6) {
            isValid = false;
            message = 'Password must be at least 6 characters';
        }
        
        this.updateInputState(input, isValid, message);
        return isValid;
    },
    
    // Update input validation state
    updateInputState(input, isValid, message) {
        input.classList.toggle('is-valid', isValid);
        input.classList.toggle('is-invalid', !isValid);
        
        let feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!isValid) {
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                input.parentNode.appendChild(feedback);
            }
            feedback.textContent = message;
        } else if (feedback) {
            feedback.remove();
        }
    },
    
    // Enhanced loading states
    showLoading(element, text = 'Loading...') {
        if (!element) return;
        
        element.dataset.originalText = element.innerHTML;
        element.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${text}
        `;
        element.disabled = true;
        element.classList.add('loading');
    },
    
    hideLoading(element) {
        if (!element) return;
        
        element.innerHTML = element.dataset.originalText || 'Submit';
        element.disabled = false;
        element.classList.remove('loading');
        delete element.dataset.originalText;
    },
    
    // Enhanced notifications
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getNotificationIcon(type)} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    },
    
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            danger: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    },
    
    // Auto-hide alerts with animation
    autoHideAlerts() {
        document.querySelectorAll('.alert:not(.alert-permanent)').forEach((alert, index) => {
            setTimeout(() => {
                alert.style.animation = 'fadeOut 0.5s ease-out';
                setTimeout(() => alert.remove(), 500);
            }, 5000 + (index * 200));
        });
    },
    
    // Animate elements on load
    animateOnLoad() {
        const elements = document.querySelectorAll('.card, .btn, .table');
        elements.forEach((el, index) => {
            el.style.animationDelay = `${index * 0.1}s`;
            el.classList.add('fade-in');
        });
    },
    
    // Theme management
    loadTheme() {
        document.body.dataset.theme = this.theme;
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.innerHTML = this.theme === 'light' ? 
                '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
        }
    },
    
    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.loadTheme();
        
        // Animate theme change
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    },
    
    // Utility functions
    debounce(func, wait) {
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
    
    formatTime(hours) {
        if (!hours) return '0h 0m';
        const h = Math.floor(hours);
        const m = Math.round((hours - h) * 60);
        return `${h}h ${m}m`;
    },
    
    // AJAX helper
    async request(url, options = {}) {
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            this.showNotification('Request failed. Please try again.', 'danger');
            throw error;
        }
    },
    
    // Periodic updates
    startPeriodicUpdates() {
        setInterval(() => {
            this.updateNotificationCount();
            this.updateTimers();
        }, 30000);
    },
    
    async updateNotificationCount() {
        try {
            const data = await this.request('/api/notifications/count');
            const badge = document.getElementById('notification-count');
            if (badge) {
                badge.textContent = data.count || '0';
                badge.style.display = data.count > 0 ? 'inline' : 'none';
            }
        } catch (error) {
            console.error('Failed to update notifications:', error);
        }
    },
    
    updateTimers() {
        this.timers.forEach((timer, taskId) => {
            if (timer.active) {
                const elapsed = Date.now() - timer.startTime + (timer.elapsed || 0);
                this.updateTimerDisplay(taskId, elapsed);
            }
        });
    },
    
    updateTimerDisplay(taskId, elapsed) {
        const element = document.getElementById(`timer-${taskId}`);
        if (element) {
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            element.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => TimeGuard.init());

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to { transform: scale(4); opacity: 0; }
    }
    @keyframes fadeOut {
        to { opacity: 0; transform: translateY(-10px); }
    }
    @keyframes slideOut {
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Export for global access
window.TimeGuard = TimeGuard;