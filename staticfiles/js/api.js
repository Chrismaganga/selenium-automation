// API Integration for Selenium Automation Backend

class AutomationAPI {
    constructor() {
        this.baseURL = '/api';
        this.frontendURL = '/api/frontend';
        this.csrfToken = this.getCSRFToken();
        this.setupAjaxDefaults();
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    setupAjaxDefaults() {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", this.csrfToken);
                }
            }
        });
    }

    // Generic API call method
    async apiCall(endpoint, method = 'GET', data = null, useFrontend = false) {
        const baseURL = useFrontend ? this.frontendURL : this.baseURL;
        const config = {
            url: `${baseURL}${endpoint}`,
            method: method,
            headers: {
                'X-CSRFToken': this.csrfToken,
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            config.data = JSON.stringify(data);
        }

        try {
            const response = await $.ajax(config);
            return { success: true, data: response };
        } catch (error) {
            console.error(`API Error (${method} ${endpoint}):`, error);
            return { 
                success: false, 
                error: error.responseJSON || { message: error.statusText || 'Unknown error' }
            };
        }
    }

    // Dashboard Data
    async getDashboardData() {
        return await this.apiCall('/dashboard/', 'GET', null, true);
    }

    // System Health
    async getSystemHealth() {
        return await this.apiCall('/system/health/', 'GET', null, true);
    }

    // Task Management
    async getTasks(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.apiCall(`/tasks/${queryString ? '?' + queryString : ''}`, 'GET', null, true);
    }

    async getTask(taskId) {
        return await this.apiCall(`/tasks/${taskId}/`, 'GET', null, true);
    }

    async createTask(taskData) {
        return await this.apiCall('/tasks/', 'POST', taskData, true);
    }

    async updateTask(taskId, taskData) {
        return await this.apiCall(`/tasks/${taskId}/`, 'PUT', taskData, true);
    }

    async deleteTask(taskId) {
        return await this.apiCall(`/tasks/${taskId}/`, 'DELETE', null, true);
    }

    // Backend API calls (for advanced features)
    async startTask(taskId) {
        return await this.apiCall(`/tasks/${taskId}/start_enhanced/`, 'POST');
    }

    async pauseTask(taskId) {
        return await this.apiCall(`/tasks/${taskId}/pause/`, 'POST');
    }

    async resumeTask(taskId) {
        return await this.apiCall(`/tasks/${taskId}/resume/`, 'POST');
    }

    async cancelTask(taskId) {
        return await this.apiCall(`/tasks/${taskId}/cancel/`, 'POST');
    }

    // Events and Logs
    async getPageEvents(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.apiCall(`/page-events/${queryString ? '?' + queryString : ''}`);
    }

    async getCaptchaEvents(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.apiCall(`/captcha-events/${queryString ? '?' + queryString : ''}`);
    }

    async getLogs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.apiCall(`/logs/${queryString ? '?' + queryString : ''}`);
    }

    // Statistics
    async getStats() {
        return await this.apiCall('/stats/');
    }

    // Templates
    async getAvailableTemplates() {
        return await this.apiCall('/tasks/available_templates/');
    }

    async getTemplateConfig(templateName) {
        return await this.apiCall(`/tasks/template_config/${templateName}/`);
    }

    async recommendTemplates(url) {
        return await this.apiCall('/tasks/recommend_templates/', 'POST', { url });
    }
}

// Global API instance
window.api = new AutomationAPI();

// Utility functions
class UIUtils {
    static showAlert(message, type = 'info', duration = 5000) {
        const alertContainer = document.getElementById('alert-container');
        const alertId = 'alert-' + Date.now();
        
        const alertHTML = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHTML);
        
        if (duration > 0) {
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, duration);
        }
    }

    static getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    static showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }

    static formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    }

    static formatDuration(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    }

    static formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    static getStatusBadgeClass(status) {
        const classes = {
            'pending': 'status-pending',
            'running': 'status-running',
            'completed': 'status-completed',
            'failed': 'status-failed',
            'cancelled': 'status-cancelled'
        };
        return classes[status] || 'status-pending';
    }

    static getPriorityClass(priority) {
        const classes = {
            'high': 'task-priority-high',
            'medium': 'task-priority-medium',
            'low': 'task-priority-low'
        };
        return classes[priority] || 'task-priority-low';
    }
}

// Real-time updates
class RealTimeUpdates {
    constructor() {
        this.updateInterval = 5000; // 5 seconds
        this.isActive = false;
        this.intervals = {};
    }

    start() {
        if (this.isActive) return;
        this.isActive = true;
        
        // Update system status
        this.intervals.systemStatus = setInterval(() => {
            this.updateSystemStatus();
        }, this.updateInterval);
        
        // Update task status
        this.intervals.taskStatus = setInterval(() => {
            this.updateTaskStatus();
        }, this.updateInterval);
    }

    stop() {
        this.isActive = false;
        Object.values(this.intervals).forEach(interval => clearInterval(interval));
        this.intervals = {};
    }

    async updateSystemStatus() {
        try {
            const response = await api.getSystemHealth();
            if (response.success) {
                this.updateStatusIndicators(response.data);
            }
        } catch (error) {
            console.error('Failed to update system status:', error);
        }
    }

    async updateTaskStatus() {
        // This would update running tasks status
        // Implementation depends on specific requirements
    }

    updateStatusIndicators(data) {
        // Update Redis status
        const redisStatus = document.getElementById('redis-status');
        if (redisStatus) {
            redisStatus.className = `badge ${data.redis_connected ? 'bg-success' : 'bg-danger'}`;
            redisStatus.textContent = data.redis_connected ? 'Connected' : 'Disconnected';
        }

        // Update Celery status
        const celeryStatus = document.getElementById('celery-status');
        if (celeryStatus) {
            celeryStatus.className = `badge ${data.celery_workers > 0 ? 'bg-success' : 'bg-danger'}`;
            celeryStatus.textContent = data.celery_workers > 0 ? 'Running' : 'Stopped';
        }

        // Update system status
        const systemStatus = document.getElementById('system-status');
        if (systemStatus) {
            systemStatus.className = `badge ${data.overall_health ? 'bg-success' : 'bg-danger'}`;
            systemStatus.textContent = data.overall_health ? 'Online' : 'Offline';
        }
    }
}

// Global real-time updates instance
window.realTimeUpdates = new RealTimeUpdates();

// Initialize when DOM is ready
$(document).ready(function() {
    // Start real-time updates
    realTimeUpdates.start();
    
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        $('.alert').alert('close');
    }, 5000);
});

// Export for use in other scripts
window.UIUtils = UIUtils;
window.RealTimeUpdates = RealTimeUpdates;
