// Main JavaScript for Selenium Automation Backend

// Dashboard functionality
class Dashboard {
    constructor() {
        this.charts = {};
        this.init();
    }

    async init() {
        await this.loadDashboardData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    async loadDashboardData() {
        try {
            UIUtils.showLoading(true);
            
            // Load dashboard data
            const dashboardResponse = await api.getDashboardData();
            if (dashboardResponse.success) {
                this.updateStatistics(dashboardResponse.data);
                this.updateRecentTasks(dashboardResponse.data.recent_tasks || []);
            }

            // Load system health
            const healthResponse = await api.getSystemHealth();
            if (healthResponse.success) {
                this.updateSystemHealth(healthResponse.data);
            }

            // Load charts
            this.initializeCharts();

        } catch (error) {
            UIUtils.showAlert('Failed to load dashboard data', 'danger');
            console.error('Dashboard load error:', error);
        } finally {
            UIUtils.showLoading(false);
        }
    }

    updateSystemHealth(data) {
        // Update system status cards
        const healthCards = document.querySelectorAll('.health-card');
        healthCards.forEach(card => {
            const metric = card.dataset.metric;
            const value = data[metric];
            const valueElement = card.querySelector('.metric-value');
            const statusElement = card.querySelector('.metric-status');
            
            if (valueElement) {
                valueElement.textContent = this.formatHealthValue(metric, value);
            }
            
            if (statusElement) {
                const status = this.getHealthStatus(metric, value);
                statusElement.className = `badge ${status.class}`;
                statusElement.textContent = status.text;
            }
        });
    }

    updateStatistics(data) {
        // Update stats cards
        const statsCards = document.querySelectorAll('.stats-card');
        statsCards.forEach(card => {
            const metric = card.dataset.metric;
            const value = data[metric];
            const valueElement = card.querySelector('.stats-value');
            
            if (valueElement && value !== undefined) {
                valueElement.textContent = this.formatStatValue(metric, value);
            }
        });
    }

    updateRecentTasks(tasks) {
        const container = document.getElementById('recent-tasks');
        if (!container) return;

        if (tasks.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent tasks</p>';
            return;
        }

        const tasksHTML = tasks.map(task => `
            <div class="card task-card mb-2 ${UIUtils.getPriorityClass(task.priority)}" onclick="openTaskDetails('${task.id}')">
                <div class="card-body py-2">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h6 class="mb-1">${task.name || 'Unnamed Task'}</h6>
                            <small class="text-muted">${task.template || 'Custom'}</small>
                        </div>
                        <div class="col-md-3">
                            <span class="badge ${UIUtils.getStatusBadgeClass(task.status)}">${task.status}</span>
                        </div>
                        <div class="col-md-3 text-end">
                            <small class="text-muted">${UIUtils.formatDate(task.created_at)}</small>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = tasksHTML;
    }

    initializeCharts() {
        // Task Status Chart
        this.initTaskStatusChart();
        
        // Performance Chart
        this.initPerformanceChart();
        
        // System Resources Chart
        this.initSystemResourcesChart();
    }

    initTaskStatusChart() {
        const ctx = document.getElementById('taskStatusChart');
        if (!ctx) return;

        this.charts.taskStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Running', 'Failed', 'Pending'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#198754',
                        '#0dcaf0',
                        '#dc3545',
                        '#ffc107'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    initPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Success Rate',
                    data: [],
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Error Rate',
                    data: [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    initSystemResourcesChart() {
        const ctx = document.getElementById('systemResourcesChart');
        if (!ctx) return;

        this.charts.systemResources = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['CPU', 'Memory', 'Disk'],
                datasets: [{
                    label: 'Usage %',
                    data: [0, 0, 0],
                    backgroundColor: [
                        '#0dcaf0',
                        '#198754',
                        '#ffc107'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDashboardData());
        }

        // Quick action buttons
        const quickActions = document.querySelectorAll('.quick-action');
        quickActions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleQuickAction(action);
            });
        });
    }

    handleQuickAction(action) {
        switch (action) {
            case 'create-task':
                window.location.href = '/tasks/create/';
                break;
            case 'view-tasks':
                window.location.href = '/tasks/';
                break;
            case 'view-monitoring':
                window.location.href = '/monitoring/';
                break;
            case 'view-logs':
                window.location.href = '/logs/';
                break;
        }
    }

    startAutoRefresh() {
        // Refresh dashboard every 30 seconds
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }

    formatHealthValue(metric, value) {
        switch (metric) {
            case 'cpu_usage':
            case 'memory_usage':
            case 'disk_usage':
                return `${value}%`;
            case 'uptime':
                return UIUtils.formatDuration(value);
            default:
                return value;
        }
    }

    getHealthStatus(metric, value) {
        switch (metric) {
            case 'cpu_usage':
                return value > 80 ? { class: 'bg-danger', text: 'High' } : 
                       value > 60 ? { class: 'bg-warning', text: 'Medium' } : 
                       { class: 'bg-success', text: 'Normal' };
            case 'memory_usage':
                return value > 85 ? { class: 'bg-danger', text: 'High' } : 
                       value > 70 ? { class: 'bg-warning', text: 'Medium' } : 
                       { class: 'bg-success', text: 'Normal' };
            case 'disk_usage':
                return value > 90 ? { class: 'bg-danger', text: 'High' } : 
                       value > 80 ? { class: 'bg-warning', text: 'Medium' } : 
                       { class: 'bg-success', text: 'Normal' };
            default:
                return { class: 'bg-success', text: 'OK' };
        }
    }

    formatStatValue(metric, value) {
        switch (metric) {
            case 'total_tasks':
            case 'completed_tasks':
            case 'failed_tasks':
                return value || 0;
            case 'success_rate':
                return `${(value || 0).toFixed(1)}%`;
            case 'avg_duration':
                return UIUtils.formatDuration(value || 0);
            default:
                return value || 0;
        }
    }
}

// Task Management functionality
class TaskManager {
    constructor() {
        this.tasks = [];
        this.currentPage = 1;
        this.pageSize = 10;
        this.filters = {};
        this.init();
    }

    async init() {
        await this.loadTasks();
        this.setupEventListeners();
        this.setupFilters();
    }

    async loadTasks() {
        try {
            UIUtils.showLoading(true);
            
            const params = {
                page: this.currentPage,
                page_size: this.pageSize,
                ...this.filters
            };

            const response = await api.getTasks(params);
            if (response.success) {
                this.tasks = response.data.results || response.data;
                this.renderTasks();
                this.updatePagination(response.data);
                this.updateTaskCount(response.data.count || 0);
            } else {
                UIUtils.showAlert('Failed to load tasks', 'danger');
            }
        } catch (error) {
            UIUtils.showAlert('Error loading tasks', 'danger');
            console.error('Task load error:', error);
        } finally {
            UIUtils.showLoading(false);
        }
    }

    renderTasks() {
        const container = document.getElementById('tasks-container');
        if (!container) return;

        if (this.tasks.length === 0) {
            container.innerHTML = '<div class="text-center py-5"><p class="text-muted">No tasks found</p></div>';
            return;
        }

        const tasksHTML = this.tasks.map(task => this.renderTaskCard(task)).join('');
        container.innerHTML = tasksHTML;
    }

    renderTaskCard(task) {
        const priorityClass = UIUtils.getPriorityClass(task.priority);
        const statusClass = UIUtils.getStatusBadgeClass(task.status);
        
        return `
            <div class="card task-card mb-3 ${priorityClass}" data-task-id="${task.id}">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-4">
                            <h6 class="mb-1">${task.name || 'Unnamed Task'}</h6>
                            <small class="text-muted">${task.template || 'Custom'}</small>
                        </div>
                        <div class="col-md-2">
                            <span class="badge ${statusClass}">${task.status}</span>
                        </div>
                        <div class="col-md-2">
                            <small class="text-muted">Priority: ${task.priority}</small>
                        </div>
                        <div class="col-md-2">
                            <small class="text-muted">${UIUtils.formatDate(task.created_at)}</small>
                        </div>
                        <div class="col-md-2 text-end">
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-primary" onclick="openTaskDetails('${task.id}')" title="View Details">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-outline-secondary" onclick="editTask('${task.id}')" title="Edit">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-outline-danger" onclick="deleteTask('${task.id}')" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    updateTaskCount(count) {
        const countElement = document.getElementById('task-count');
        if (countElement) {
            countElement.textContent = count;
        }
    }

    setupEventListeners() {
        // Create task button
        const createBtn = document.getElementById('create-task-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateTaskModal());
        }

        // Filter buttons
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.currentTarget.dataset.filter;
                this.applyFilter(JSON.parse(filter));
            });
        });

        // Search input
        const searchInput = document.getElementById('task-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filters.search = e.target.value;
                this.currentPage = 1;
                this.loadTasks();
            });
        }
    }

    setupFilters() {
        // Status filter
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
                this.currentPage = 1;
                this.loadTasks();
            });
        }

        // Priority filter
        const priorityFilter = document.getElementById('priority-filter');
        if (priorityFilter) {
            priorityFilter.addEventListener('change', (e) => {
                this.filters.priority = e.target.value;
                this.currentPage = 1;
                this.loadTasks();
            });
        }
    }

    applyFilter(filter) {
        this.filters = { ...this.filters, ...filter };
        this.currentPage = 1;
        this.loadTasks();
    }

    showCreateTaskModal() {
        $('#createTaskModal').modal('show');
    }

    updatePagination(data) {
        // Update pagination controls
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        // Implementation for pagination
    }
}

// Global functions for task actions
function openTaskDetails(taskId) {
    $('#taskDetailsModal').modal('show');
    loadTaskDetails(taskId);
}

function editTask(taskId) {
    window.location.href = `/tasks/${taskId}/edit/`;
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
        const response = await api.deleteTask(taskId);
        if (response.success) {
            UIUtils.showAlert('Task deleted successfully', 'success');
            // Reload tasks
            if (window.taskManager) {
                window.taskManager.loadTasks();
            }
        } else {
            UIUtils.showAlert('Failed to delete task', 'danger');
        }
    } catch (error) {
        UIUtils.showAlert('Error deleting task', 'danger');
        console.error('Delete task error:', error);
    }
}

async function loadTaskDetails(taskId) {
    try {
        UIUtils.showLoading(true);
        const response = await api.getTask(taskId);
        
        if (response.success) {
            const task = response.data;
            const content = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Basic Information</h6>
                        <table class="table table-sm">
                            <tr><td><strong>Name:</strong></td><td>${task.name || 'N/A'}</td></tr>
                            <tr><td><strong>Status:</strong></td><td><span class="badge ${UIUtils.getStatusBadgeClass(task.status)}">${task.status}</span></td></tr>
                            <tr><td><strong>Priority:</strong></td><td>${task.priority}</td></tr>
                            <tr><td><strong>Template:</strong></td><td>${task.template || 'Custom'}</td></tr>
                            <tr><td><strong>URL:</strong></td><td><a href="${task.url}" target="_blank">${task.url}</a></td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>Configuration</h6>
                        <table class="table table-sm">
                            <tr><td><strong>Max Pages:</strong></td><td>${task.max_pages || 'N/A'}</td></tr>
                            <tr><td><strong>Delay:</strong></td><td>${task.delay_between_requests || 0}s</td></tr>
                            <tr><td><strong>Headless:</strong></td><td>${task.headless ? 'Yes' : 'No'}</td></tr>
                            <tr><td><strong>Screenshots:</strong></td><td>${task.take_screenshots ? 'Yes' : 'No'}</td></tr>
                            <tr><td><strong>Created:</strong></td><td>${UIUtils.formatDate(task.created_at)}</td></tr>
                        </table>
                    </div>
                </div>
                ${task.notes ? `<div class="mt-3"><h6>Notes</h6><p>${task.notes}</p></div>` : ''}
            `;
            
            $('#task-details-content').html(content);
            $('#edit-task-btn').data('task-id', taskId);
        } else {
            UIUtils.showAlert('Failed to load task details', 'danger');
        }
    } catch (error) {
        UIUtils.showAlert('Error loading task details', 'danger');
        console.error('Task details error:', error);
    } finally {
        UIUtils.showLoading(false);
    }
}

// Initialize dashboard when DOM is ready
$(document).ready(function() {
    // Initialize dashboard if on dashboard page
    if (document.getElementById('dashboard-container')) {
        window.dashboard = new Dashboard();
    }

    // Initialize task manager if on tasks page
    if (document.getElementById('tasks-container')) {
        window.taskManager = new TaskManager();
    }
});
