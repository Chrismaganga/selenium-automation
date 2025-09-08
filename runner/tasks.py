from celery import shared_task
from .selenium_service import run_automation_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_automation_task(self, task_id: str):
    """
    Celery task to execute automation
    """
    try:
        logger.info(f"Starting automation task {task_id}")
        run_automation_task(task_id)
        logger.info(f"Completed automation task {task_id}")
    except Exception as e:
        logger.error(f"Automation task {task_id} failed: {e}")
        raise


@shared_task
def cleanup_old_tasks():
    """
    Cleanup task to remove old completed tasks and their files
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
        
        logger.info(f"Cleaned up {count} old tasks")
        return f"Cleaned up {count} old tasks"
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise


@shared_task
def generate_daily_report():
    """
    Generate daily automation report
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
        
        # Calculate statistics
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='COMPLETED').count()
        failed_tasks = tasks.filter(status='FAILED').count()
        captcha_tasks = tasks.filter(status='CAPTCHA_DETECTED').count()
        
        # Get stats
        stats = AutomationStats.objects.filter(
            task__created_at__gte=yesterday,
            task__created_at__lt=today
        )
        
        total_pages = sum(s.total_requests for s in stats)
        total_captchas = sum(s.captcha_detections for s in stats)
        
        report = {
            'date': yesterday.date().isoformat(),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'captcha_tasks': captcha_tasks,
            'total_pages_visited': total_pages,
            'total_captcha_detections': total_captchas,
            'success_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
        
        logger.info(f"Daily report generated: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        raise

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def optimize_performance_task(self, task_id: str):
    """
    Simulates an AI-driven performance optimization task for a given automation task.
    This would analyze past runs and suggest config changes.
    """
    try:
        task = AutomationTask.objects.get(id=task_id)
        logger.info(f"Analyzing performance for task {task_id} for optimization.")

        # Placeholder for actual AI/ML logic
        # This would involve:
        # 1. Retrieving historical PageEvent and AutomationStats data for the task/template.
        # 2. Analyzing metrics like avg_page_load_time, resource usage, error patterns.
        # 3. Suggesting changes to task.delay_between_requests, task.headless, task.window_size, user_agent, etc.
        
        # Simulate some recommendations
        recommendations = []
        if hasattr(task, 'stats') and task.stats.avg_page_load_time > 5.0:
            recommendations.append("Consider increasing 'delay_between_requests' for stability.")
        if hasattr(task, 'stats') and task.stats.cpu_usage_percent > 70:
            recommendations.append("Consider reducing 'max_pages' or 'max_depth' to lower CPU load.")
        if task.headless is False and hasattr(task, 'stats') and task.stats.memory_usage_mb > 1000:
            recommendations.append("Switch to 'headless' mode to reduce memory consumption.")
        
        if recommendations:
            task.notes = (task.notes or "") + "\nPerformance Optimization Suggestions:\n" + "\n".join(recommendations)
            task.save(update_fields=["notes"])
            AutomationLog.objects.create(task=task, level="INFO", message="Performance optimization suggestions generated.", details={"recommendations": recommendations})
            logger.info(f"Performance optimization suggestions for task {task_id}: {recommendations}")
        else:
            AutomationLog.objects.create(task=task, level="INFO", message="No specific performance optimization suggestions at this time.")
            logger.info(f"No specific performance optimization suggestions for task {task_id}.")

    except AutomationTask.DoesNotExist:
        logger.error(f"AutomationTask {task_id} not found for performance optimization.")
    except Exception as e:
        logger.error(f"Performance optimization failed: {e}", exc_info=True)
        raise
