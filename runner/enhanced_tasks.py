from celery import shared_task
from .enhanced_selenium_service import run_enhanced_automation_task
from .monitoring import alert_manager, system_health_monitor
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_enhanced_automation_task(self, task_id: str):
    """
    Enhanced Celery task to execute automation with advanced features
    """
    try:
        logger.info(f"Starting enhanced automation task {task_id}")
        run_enhanced_automation_task(task_id)
        logger.info(f"Completed enhanced automation task {task_id}")
    except Exception as e:
        logger.error(f"Enhanced automation task {task_id} failed: {e}")
        raise


@shared_task
def cleanup_old_tasks():
    """
    Enhanced cleanup task with monitoring
    """
    from datetime import timedelta
    from django.utils import timezone
    from .models import AutomationTask
    import os
    
    try:
        # Delete tasks older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        old_tasks = AutomationTask.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['COMPLETED', 'FAILED', 'CANCELLED']
        )
        
        count = 0
        for task in old_tasks:
            # Delete associated files
            for event in task.events.all():
                if event.screenshot:
                    try:
                        os.remove(event.screenshot.path)
                    except (OSError, ValueError):
                        pass
                if event.html_content:
                    try:
                        os.remove(event.html_content.path)
                    except (OSError, ValueError):
                        pass
            
            # Delete task
            task.delete()
            count += 1
        
        logger.info(f"Enhanced cleanup completed: {count} old tasks removed")
        return f"Enhanced cleanup completed: {count} old tasks removed"
        
    except Exception as e:
        logger.error(f"Enhanced cleanup failed: {e}")
        raise


@shared_task
def generate_enhanced_daily_report():
    """
    Generate enhanced daily automation report with AI insights
    """
    from datetime import timedelta
    from django.utils import timezone
    from .models import AutomationTask, AutomationStats
    from django.contrib.auth.models import User
    
    try:
        yesterday = timezone.now() - timedelta(days=1)
        today = timezone.now()
        
        # Get yesterday's tasks
        tasks = AutomationTask.objects.filter(
            created_at__gte=yesterday,
            created_at__lt=today
        )
        
        # Calculate enhanced statistics
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='COMPLETED').count()
        failed_tasks = tasks.filter(status='FAILED').count()
        captcha_tasks = tasks.filter(status='CAPTCHA_DETECTED').count()
        
        # Get enhanced stats
        stats = AutomationStats.objects.filter(
            task__created_at__gte=yesterday,
            task__created_at__lt=today
        )
        
        total_pages = sum(s.total_requests for s in stats)
        total_captchas = sum(s.captcha_detections for s in stats)
        avg_memory = sum(s.memory_peak for s in stats) / len(stats) if stats else 0
        avg_cpu = sum(s.cpu_usage_peak for s in stats) / len(stats) if stats else 0
        
        # AI insights
        ai_insights = []
        if completed_tasks > 0:
            success_rate = (completed_tasks / total_tasks) * 100
            if success_rate > 90:
                ai_insights.append("Excellent automation performance - consider scaling up")
            elif success_rate < 70:
                ai_insights.append("Performance below optimal - review error patterns")
        
        if total_captchas > 0:
            captcha_rate = (total_captchas / total_pages) * 100 if total_pages > 0 else 0
            if captcha_rate > 10:
                ai_insights.append("High CAPTCHA detection rate - consider using different strategies")
        
        if avg_memory > 500:
            ai_insights.append("High memory usage detected - consider optimizing tasks")
        
        report = {
            'date': yesterday.date().isoformat(),
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'captcha_tasks': captcha_tasks,
                'total_pages_visited': total_pages,
                'total_captcha_detections': total_captchas,
                'success_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            'performance': {
                'average_memory_mb': round(avg_memory, 2),
                'average_cpu_percent': round(avg_cpu, 2),
                'captcha_detection_rate': round(captcha_rate, 2) if total_pages > 0 else 0
            },
            'ai_insights': ai_insights,
            'recommendations': _generate_recommendations(tasks, stats)
        }
        
        logger.info(f"Enhanced daily report generated: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Enhanced daily report generation failed: {e}")
        raise


def _generate_recommendations(tasks, stats):
    """Generate AI-powered recommendations"""
    recommendations = []
    
    # Task completion analysis
    if tasks.count() > 0:
        completion_rate = tasks.filter(status='COMPLETED').count() / tasks.count()
        if completion_rate < 0.8:
            recommendations.append("Consider reviewing failed tasks to identify common issues")
    
    # Performance analysis
    if stats:
        avg_memory = sum(s.memory_peak for s in stats) / len(stats)
        if avg_memory > 800:
            recommendations.append("High memory usage detected - consider reducing concurrent tasks")
        
        avg_cpu = sum(s.cpu_usage_peak for s in stats) / len(stats)
        if avg_cpu > 70:
            recommendations.append("High CPU usage detected - consider optimizing task configurations")
    
    # CAPTCHA analysis
    total_captchas = sum(s.captcha_detections for s in stats)
    if total_captchas > 5:
        recommendations.append("Frequent CAPTCHA detections - consider implementing CAPTCHA solving strategies")
    
    return recommendations


@shared_task
def monitor_system_health():
    """
    Monitor system health and send alerts if needed
    """
    try:
        health_status = system_health_monitor.run_health_checks()
        
        if health_status['overall_status'] != 'healthy':
            # Send alert for unhealthy system
            alert_manager.send_alert(
                None,  # No specific task
                f"System health check failed: {health_status['overall_status']}",
                'critical'
            )
        
        logger.info(f"System health check completed: {health_status['overall_status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"System health monitoring failed: {e}")
        raise


@shared_task
def process_ai_insights():
    """
    Process AI insights and generate recommendations
    """
    from .models import AutomationTask, PageEvent
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Get recent tasks
        recent_tasks = AutomationTask.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        )
        
        insights = []
        
        # Analyze task patterns
        for task in recent_tasks:
            if task.status == 'COMPLETED':
                # Analyze page events for patterns
                events = task.events.filter(event_type='PAGE_LOAD')
                
                if events.count() > 10:
                    # High page count - might be inefficient
                    insights.append({
                        'task_id': str(task.id),
                        'type': 'efficiency',
                        'message': 'High page count detected - consider optimizing crawling strategy',
                        'severity': 'medium'
                    })
                
                # Check for CAPTCHA patterns
                captcha_events = task.captcha_events.all()
                if captcha_events.count() > 3:
                    insights.append({
                        'task_id': str(task.id),
                        'type': 'captcha',
                        'message': 'Frequent CAPTCHA detections - consider different approach',
                        'severity': 'high'
                    })
        
        logger.info(f"AI insights processed: {len(insights)} insights generated")
        return insights
        
    except Exception as e:
        logger.error(f"AI insights processing failed: {e}")
        raise


@shared_task
def optimize_task_performance():
    """
    Analyze and optimize task performance
    """
    from .models import AutomationTask, AutomationStats
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Get recent tasks with stats
        recent_tasks = AutomationTask.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7),
            status='COMPLETED'
        )
        
        optimizations = []
        
        for task in recent_tasks:
            try:
                stats = task.stats
                if not stats:
                    continue
                
                # Memory optimization
                if stats.memory_peak > 1000:
                    optimizations.append({
                        'task_id': str(task.id),
                        'optimization': 'memory',
                        'current_value': stats.memory_peak,
                        'recommendation': 'Reduce max_pages or enable headless mode'
                    })
                
                # CPU optimization
                if stats.cpu_usage_peak > 80:
                    optimizations.append({
                        'task_id': str(task.id),
                        'optimization': 'cpu',
                        'current_value': stats.cpu_usage_peak,
                        'recommendation': 'Increase delay_between_requests'
                    })
                
                # Success rate optimization
                if stats.success_rate < 70:
                    optimizations.append({
                        'task_id': str(task.id),
                        'optimization': 'success_rate',
                        'current_value': stats.success_rate,
                        'recommendation': 'Review error patterns and improve error handling'
                    })
                
            except Exception as e:
                logger.error(f"Error analyzing task {task.id}: {e}")
                continue
        
        logger.info(f"Performance optimization completed: {len(optimizations)} optimizations suggested")
        return optimizations
        
    except Exception as e:
        logger.error(f"Performance optimization failed: {e}")
        raise
