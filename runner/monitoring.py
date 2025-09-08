"""
Advanced monitoring and alerting system for automation tasks
"""
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import AutomationTask, AutomationLog, AutomationStats

logger = logging.getLogger(__name__)


class MonitoringRule:
    """Base class for monitoring rules"""
    
    def __init__(self, name: str, condition: Callable, action: Callable, enabled: bool = True):
        self.name = name
        self.condition = condition
        self.action = action
        self.enabled = enabled
        self.last_triggered = None
    
    def check(self, task: AutomationTask, stats: AutomationStats = None) -> bool:
        """Check if rule condition is met"""
        if not self.enabled:
            return False
        
        try:
            result = self.condition(task, stats)
            if result and self.last_triggered != task.id:
                self.last_triggered = task.id
                self.action(task, stats)
                return True
        except Exception as e:
            logger.error(f"Error in monitoring rule '{self.name}': {e}")
        
        return False


class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self):
        self.rules = []
        self.alert_history = []
    
    def add_rule(self, rule: MonitoringRule):
        """Add a monitoring rule"""
        self.rules.append(rule)
        logger.info(f"Added monitoring rule: {rule.name}")
    
    def check_all_rules(self, task: AutomationTask, stats: AutomationStats = None):
        """Check all monitoring rules for a task"""
        for rule in self.rules:
            rule.check(task, stats)
    
    def send_alert(self, task: AutomationTask, message: str, alert_type: str = 'info'):
        """Send an alert"""
        alert = {
            'task_id': str(task.id),
            'task_name': task.name,
            'message': message,
            'alert_type': alert_type,
            'timestamp': timezone.now().isoformat()
        }
        
        self.alert_history.append(alert)
        
        # Log the alert
        AutomationLog.objects.create(
            task=task,
            level='WARNING' if alert_type in ['error', 'critical'] else 'INFO',
            message=f"ALERT: {message}",
            metadata={'alert_type': alert_type}
        )
        
        # Send email if configured
        if hasattr(settings, 'ALERT_EMAIL') and settings.ALERT_EMAIL:
            self._send_email_alert(alert)
        
        logger.warning(f"Alert for task {task.id}: {message}")
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert"""
        try:
            subject = f"Automation Alert: {alert['task_name']}"
            message = f"""
Task: {alert['task_name']}
Type: {alert['alert_type']}
Message: {alert['message']}
Time: {alert['timestamp']}
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ALERT_EMAIL],
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")


class PerformanceMonitor:
    """Monitor task performance and resource usage"""
    
    def __init__(self):
        self.performance_history = []
        self.thresholds = {
            'max_memory_mb': 1000,
            'max_cpu_percent': 80,
            'max_duration_minutes': 60,
            'max_error_rate': 0.3
        }
    
    def check_performance(self, task: AutomationTask, stats: AutomationStats = None):
        """Check task performance against thresholds"""
        if not stats:
            return
        
        alerts = []
        
        # Check memory usage
        if stats.memory_peak > self.thresholds['max_memory_mb']:
            alerts.append(f"High memory usage: {stats.memory_peak:.1f}MB")
        
        # Check CPU usage
        if stats.cpu_usage_peak > self.thresholds['max_cpu_percent']:
            alerts.append(f"High CPU usage: {stats.cpu_usage_peak:.1f}%")
        
        # Check duration
        if task.started_at and task.finished_at:
            duration = (task.finished_at - task.started_at).total_seconds() / 60
            if duration > self.thresholds['max_duration_minutes']:
                alerts.append(f"Long duration: {duration:.1f} minutes")
        
        # Check error rate
        if stats.total_requests > 0:
            error_rate = stats.failed_requests / stats.total_requests
            if error_rate > self.thresholds['max_error_rate']:
                alerts.append(f"High error rate: {error_rate:.1%}")
        
        return alerts
    
    def get_performance_summary(self, task: AutomationTask, stats: AutomationStats = None) -> Dict[str, Any]:
        """Get performance summary for a task"""
        if not stats:
            return {}
        
        summary = {
            'memory_peak_mb': stats.memory_peak,
            'cpu_peak_percent': stats.cpu_usage_peak,
            'total_requests': stats.total_requests,
            'success_rate': stats.success_rate,
            'error_rate': 1 - (stats.success_rate / 100) if stats.success_rate else 0,
            'captcha_detections': stats.captcha_detections,
            'captcha_solve_rate': stats.captcha_solve_rate
        }
        
        if task.started_at and task.finished_at:
            summary['duration_minutes'] = (task.finished_at - task.started_at).total_seconds() / 60
        elif task.started_at:
            summary['duration_minutes'] = (timezone.now() - task.started_at).total_seconds() / 60
        
        return summary


class SystemHealthMonitor:
    """Monitor overall system health"""
    
    def __init__(self):
        self.health_checks = []
        self.last_check = None
    
    def add_health_check(self, name: str, check_function: Callable):
        """Add a health check function"""
        self.health_checks.append({
            'name': name,
            'function': check_function
        })
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        for check in self.health_checks:
            try:
                check_result = check['function']()
                results['checks'][check['name']] = {
                    'status': 'pass' if check_result.get('healthy', False) else 'fail',
                    'message': check_result.get('message', ''),
                    'details': check_result.get('details', {})
                }
                
                if not check_result.get('healthy', False):
                    results['overall_status'] = 'unhealthy'
                    
            except Exception as e:
                results['checks'][check['name']] = {
                    'status': 'error',
                    'message': str(e),
                    'details': {}
                }
                results['overall_status'] = 'unhealthy'
        
        self.last_check = results
        return results
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get task metrics
            active_tasks = AutomationTask.objects.filter(status__in=['PENDING', 'RUNNING']).count()
            completed_today = AutomationTask.objects.filter(
                created_at__date=timezone.now().date(),
                status='COMPLETED'
            ).count()
            
            failed_today = AutomationTask.objects.filter(
                created_at__date=timezone.now().date(),
                status='FAILED'
            ).count()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'active_tasks': active_tasks,
                'completed_today': completed_today,
                'failed_today': failed_today,
                'success_rate_today': completed_today / (completed_today + failed_today) if (completed_today + failed_today) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}


class RealTimeMonitor:
    """Real-time monitoring for active tasks"""
    
    def __init__(self):
        self.active_monitors = {}
        self.monitor_interval = 30  # seconds
    
    def start_monitoring(self, task: AutomationTask):
        """Start monitoring a task"""
        self.active_monitors[str(task.id)] = {
            'task': task,
            'start_time': timezone.now(),
            'last_update': timezone.now(),
            'status_history': []
        }
        logger.info(f"Started monitoring task {task.id}")
    
    def stop_monitoring(self, task_id: str):
        """Stop monitoring a task"""
        if task_id in self.active_monitors:
            del self.active_monitors[task_id]
            logger.info(f"Stopped monitoring task {task_id}")
    
    def update_task_status(self, task: AutomationTask):
        """Update task status in monitoring"""
        task_id = str(task.id)
        if task_id in self.active_monitors:
            monitor = self.active_monitors[task_id]
            monitor['last_update'] = timezone.now()
            monitor['status_history'].append({
                'status': task.status,
                'timestamp': timezone.now().isoformat(),
                'pages_visited': task.total_pages_visited,
                'errors': task.total_errors
            })
            
            # Keep only last 10 status updates
            if len(monitor['status_history']) > 10:
                monitor['status_history'] = monitor['status_history'][-10:]
    
    def get_monitoring_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get monitoring data for a task"""
        return self.active_monitors.get(task_id)
    
    def get_all_monitoring_data(self) -> Dict[str, Any]:
        """Get all active monitoring data"""
        return {
            'active_tasks': len(self.active_monitors),
            'monitors': {
                task_id: {
                    'task_name': monitor['task'].name,
                    'status': monitor['task'].status,
                    'start_time': monitor['start_time'].isoformat(),
                    'last_update': monitor['last_update'].isoformat(),
                    'duration_minutes': (monitor['last_update'] - monitor['start_time']).total_seconds() / 60,
                    'status_history': monitor['status_history'][-5:]  # Last 5 updates
                }
                for task_id, monitor in self.active_monitors.items()
            }
        }


# Pre-defined monitoring rules
def create_default_rules(alert_manager: AlertManager):
    """Create default monitoring rules"""
    
    # Task stuck rule
    def task_stuck_condition(task: AutomationTask, stats: AutomationStats = None) -> bool:
        if task.status == 'RUNNING' and task.started_at:
            duration = (timezone.now() - task.started_at).total_seconds() / 60
            return duration > 30  # 30 minutes
        return False
    
    def task_stuck_action(task: AutomationTask, stats: AutomationStats = None):
        alert_manager.send_alert(
            task,
            f"Task has been running for over 30 minutes",
            'warning'
        )
    
    alert_manager.add_rule(MonitoringRule(
        'task_stuck',
        task_stuck_condition,
        task_stuck_action
    ))
    
    # High error rate rule
    def high_error_rate_condition(task: AutomationTask, stats: AutomationStats = None) -> bool:
        if stats and stats.total_requests > 10:
            error_rate = stats.failed_requests / stats.total_requests
            return error_rate > 0.5  # 50% error rate
        return False
    
    def high_error_rate_action(task: AutomationTask, stats: AutomationStats = None):
        error_rate = stats.failed_requests / stats.total_requests
        alert_manager.send_alert(
            task,
            f"High error rate detected: {error_rate:.1%}",
            'error'
        )
    
    alert_manager.add_rule(MonitoringRule(
        'high_error_rate',
        high_error_rate_condition,
        high_error_rate_action
    ))
    
    # CAPTCHA detection rule
    def captcha_detected_condition(task: AutomationTask, stats: AutomationStats = None) -> bool:
        return task.status == 'CAPTCHA_DETECTED'
    
    def captcha_detected_action(task: AutomationTask, stats: AutomationStats = None):
        alert_manager.send_alert(
            task,
            "CAPTCHA detected - human intervention required",
            'warning'
        )
    
    alert_manager.add_rule(MonitoringRule(
        'captcha_detected',
        captcha_detected_condition,
        captcha_detected_action
    ))
    
    # Task completion rule
    def task_completed_condition(task: AutomationTask, stats: AutomationStats = None) -> bool:
        return task.status == 'COMPLETED'
    
    def task_completed_action(task: AutomationTask, stats: AutomationStats = None):
        pages_visited = task.total_pages_visited
        errors = task.total_errors
        alert_manager.send_alert(
            task,
            f"Task completed successfully. Pages visited: {pages_visited}, Errors: {errors}",
            'info'
        )
    
    alert_manager.add_rule(MonitoringRule(
        'task_completed',
        task_completed_condition,
        task_completed_action
    ))


# Global instances
alert_manager = AlertManager()
performance_monitor = PerformanceMonitor()
system_health_monitor = SystemHealthMonitor()
real_time_monitor = RealTimeMonitor()

# Create default rules
create_default_rules(alert_manager)

# Compatibility functions for the views
def get_system_metrics() -> Dict[str, Any]:
    """Get current system resource usage metrics."""
    health_monitor = HealthMonitor()
    return health_monitor.get_system_metrics()

def alert_manager():
    """Get the alert manager instance."""
    return AlertManager()
