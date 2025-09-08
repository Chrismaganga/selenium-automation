import logging
import platform
import sys
import psutil
import time
from datetime import datetime, timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import AutomationTask, PageEvent, CaptchaEvent, AutomationLog, AutomationStats
from .serializers import AutomationTaskSerializer, PageEventSerializer, CaptchaEventSerializer, \
    AutomationLogSerializer, AutomationStatsSerializer, SystemHealthSerializer
from .tasks import execute_automation_task, cleanup_old_tasks, generate_daily_report, optimize_performance_task
from .automation_templates import get_available_templates, get_template_config, recommend_templates
from .monitoring import alert_manager, get_system_metrics
from .content_analysis import ai_content_analysis
from .data_extraction import intelligent_data_extraction

logger = logging.getLogger(__name__)

@extend_schema_view(
    list=extend_schema(
        summary="List all automation tasks",
        description="Retrieve a list of all automation tasks with pagination and filtering options.",
        tags=["Tasks"]
    ),
    create=extend_schema(
        summary="Create a new automation task",
        description="Create a new automation task with specified parameters.",
        tags=["Tasks"]
    ),
    retrieve=extend_schema(
        summary="Retrieve a specific task",
        description="Get detailed information about a specific automation task.",
        tags=["Tasks"]
    ),
    update=extend_schema(
        summary="Update a task",
        description="Update an existing automation task.",
        tags=["Tasks"]
    ),
    destroy=extend_schema(
        summary="Delete a task",
        description="Delete an automation task and all associated data.",
        tags=["Tasks"]
    )
)
class AutomationTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing automation tasks.
    
    Provides full CRUD operations for automation tasks including:
    - Creating and configuring tasks
    - Starting, pausing, and stopping tasks
    - Monitoring task progress
    - Viewing task results and logs
    """
    queryset = AutomationTask.objects.all().order_by("-created_at")
    serializer_class = AutomationTaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        AutomationLog.objects.create(
            task=serializer.instance,
            level="INFO",
            message=f"Task {serializer.instance.id} created by user {self.request.user.username if self.request.user.is_authenticated else 'anonymous'}."
        )

    @extend_schema(
        summary="Start enhanced automation task",
        description="Start an automation task with enhanced features including AI analysis and monitoring.",
        responses={202: {"description": "Task enqueued for execution"}},
        tags=["Tasks"]
    )
    @action(detail=True, methods=["post"])
    def start_enhanced(self, request, pk=None):
        """Start an automation task with enhanced features."""
        task = self.get_object()
        if task.status not in [AutomationTask.PENDING, AutomationTask.FAILED, AutomationTask.CAPTCHA_DETECTED, AutomationTask.PAUSED]:
            return Response({"detail": f"Task not in a startable state. Current status: {task.status}"},
                            status=status.HTTP_400_BAD_REQUEST)
        
        task.status = AutomationTask.PENDING
        task.started_at = None
        task.finished_at = None
        task.save()
        
        execute_automation_task.delay(str(task.id))
        AutomationLog.objects.create(task=task, level="INFO", message="Task enqueued for enhanced execution.")
        return Response({"detail": "Enhanced task enqueued."}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Pause running task",
        description="Pause a currently running automation task.",
        responses={200: {"description": "Task paused successfully"}},
        tags=["Tasks"]
    )
    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause a running automation task."""
        task = self.get_object()
        if task.status != AutomationTask.RUNNING:
            return Response({"detail": "Task is not running."}, status=status.HTTP_400_BAD_REQUEST)
        task.status = AutomationTask.PAUSED
        task.save()
        AutomationLog.objects.create(task=task, level="INFO", message="Task paused.")
        return Response({"detail": "Task paused (prototype: worker might not immediately halt)."}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Resume paused task",
        description="Resume a paused automation task.",
        responses={202: {"description": "Task resumed and enqueued"}},
        tags=["Tasks"]
    )
    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume a paused automation task."""
        task = self.get_object()
        if task.status != AutomationTask.PAUSED:
            return Response({"detail": "Task is not paused."}, status=status.HTTP_400_BAD_REQUEST)
        task.status = AutomationTask.PENDING
        task.save()
        execute_automation_task.delay(str(task.id))
        AutomationLog.objects.create(task=task, level="INFO", message="Task resumed and re-enqueued.")
        return Response({"detail": "Task resumed and enqueued."}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Cancel task",
        description="Cancel a running, paused, or pending automation task.",
        responses={200: {"description": "Task cancelled successfully"}},
        tags=["Tasks"]
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an automation task."""
        task = self.get_object()
        if task.status in [AutomationTask.COMPLETED, AutomationTask.FAILED, AutomationTask.CANCELLED]:
            return Response({"detail": "Task already finished or cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        task.status = AutomationTask.CANCELLED
        task.finished_at = timezone.now()
        task.save()
        AutomationLog.objects.create(task=task, level="INFO", message="Task cancelled.")
        return Response({"detail": "Task cancelled (prototype: worker might not immediately halt)."}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get available templates",
        description="Retrieve a list of available automation templates.",
        responses={200: {"description": "List of available templates"}},
        tags=["Tasks"]
    )
    @action(detail=False, methods=["get"])
    def available_templates(self, request):
        """Get available automation templates."""
        templates = get_available_templates()
        return Response(templates, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create task from template",
        description="Create a new automation task using a predefined template.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'template_key': {'type': 'string', 'description': 'Template identifier'},
                    'start_url': {'type': 'string', 'format': 'uri', 'description': 'Target URL'},
                    'name': {'type': 'string', 'description': 'Task name'},
                    'config': {'type': 'object', 'description': 'Additional configuration'}
                },
                'required': ['template_key', 'start_url']
            }
        },
        responses={201: AutomationTaskSerializer},
        tags=["Tasks"]
    )
    @action(detail=False, methods=["post"])
    def create_from_template(self, request):
        """Create a task from a template."""
        template_key = request.data.get("template_key")
        start_url = request.data.get("start_url")
        name = request.data.get("name", f"Task from {template_key} template")

        if not template_key or not start_url:
            return Response({"detail": "template_key and start_url are required."}, status=status.HTTP_400_BAD_REQUEST)

        template_config = get_template_config(template_key)
        if not template_config:
            return Response({"detail": f"Template '{template_key}' not found."}, status=status.HTTP_404_NOT_FOUND)

        task_data = {
            **template_config,
            "start_url": start_url,
            "name": name,
            "template_name": template_key,
            "config": {**template_config.get("config", {}), **request.data.get("config", {})}
        }
        task_data.pop("name", None)
        task_data.pop("description", None)
        task_data.pop("recommended_for", None)
        task_data.pop("ai_keywords", None)

        serializer = self.get_serializer(data=task_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        AutomationLog.objects.create(task=serializer.instance, level="INFO", message=f"Task {serializer.instance.id} created from template {template_key}.")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Get real-time task status",
        description="Get real-time status and monitoring data for a specific task.",
        responses={200: {"description": "Real-time task status and metrics"}},
        tags=["Tasks"]
    )
    @action(detail=True, methods=["get"])
    def real_time_status(self, request, pk=None):
        """Get real-time status of a task."""
        task = self.get_object()
        serializer = self.get_serializer(task)
        
        latest_logs = task.logs.order_by('-timestamp')[:5]
        log_serializer = AutomationLogSerializer(latest_logs, many=True)

        latest_captchas = task.captcha_events.order_by('-timestamp')[:3]
        captcha_serializer = CaptchaEventSerializer(latest_captchas, many=True)

        return Response({
            "task": serializer.data,
            "latest_logs": log_serializer.data,
            "latest_captcha_events": captcha_serializer.data,
            "system_metrics": get_system_metrics()
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get enhanced dashboard",
        description="Get comprehensive dashboard data with system metrics and task statistics.",
        responses={200: {"description": "Dashboard data with metrics and statistics"}},
        tags=["Tasks"]
    )
    @action(detail=False, methods=["get"])
    def enhanced_dashboard(self, request):
        """Get enhanced dashboard data."""
        total_tasks = AutomationTask.objects.count()
        running_tasks = AutomationTask.objects.filter(status=AutomationTask.RUNNING).count()
        captcha_tasks = AutomationTask.objects.filter(status=AutomationTask.CAPTCHA_DETECTED).count()
        completed_tasks = AutomationTask.objects.filter(status=AutomationTask.COMPLETED).count()
        failed_tasks = AutomationTask.objects.filter(status=AutomationTask.FAILED).count()

        avg_runtime = AutomationStats.objects.aggregate(Avg('total_runtime_seconds'))['total_runtime_seconds__avg']
        total_pages_visited = AutomationStats.objects.aggregate(Sum('pages_visited'))['pages_visited__sum']
        total_data_extracted = AutomationStats.objects.aggregate(Sum('data_extracted_count'))['data_extracted_count__sum']

        return Response({
            "total_tasks": total_tasks,
            "running_tasks": running_tasks,
            "captcha_detected_tasks": captcha_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "average_runtime_seconds": round(avg_runtime, 2) if avg_runtime else 0,
            "total_pages_visited": total_pages_visited if total_pages_visited else 0,
            "total_data_extracted_items": total_data_extracted if total_data_extracted else 0,
            "system_health": SystemViewSet.get_health_status_data(),
            "alert_history": alert_manager.get_alert_history()
        }, status=status.HTTP_200_OK)

@extend_schema_view(
    list=extend_schema(
        summary="List page events",
        description="Retrieve a list of page events with filtering options.",
        tags=["Events"]
    ),
    retrieve=extend_schema(
        summary="Retrieve page event",
        description="Get detailed information about a specific page event.",
        tags=["Events"]
    )
)
class PageEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing page events.
    
    Page events represent individual page visits during automation tasks,
    including screenshots, HTML content, and extracted data.
    """
    queryset = PageEvent.objects.all().order_by("-timestamp")
    serializer_class = PageEventSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["task", "event_type"]
    search_fields = ["url", "title", "note"]

    def get_queryset(self):
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return self.queryset.filter(task__id=task_id)
        return super().get_queryset()

@extend_schema_view(
    list=extend_schema(
        summary="List CAPTCHA events",
        description="Retrieve a list of CAPTCHA detection events.",
        tags=["CAPTCHA"]
    ),
    retrieve=extend_schema(
        summary="Retrieve CAPTCHA event",
        description="Get detailed information about a specific CAPTCHA event.",
        tags=["CAPTCHA"]
    )
)
class CaptchaEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing CAPTCHA events.
    
    CAPTCHA events are created when CAPTCHAs are detected during automation.
    This includes detection details, screenshots, and resolution status.
    """
    queryset = CaptchaEvent.objects.all().order_by("-detected_at")
    serializer_class = CaptchaEventSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["task", "captcha_type", "status"]

    @extend_schema(
        summary="Mark CAPTCHA as solved",
        description="Mark a CAPTCHA event as manually solved.",
        responses={200: {"description": "CAPTCHA marked as solved"}},
        tags=["CAPTCHA"]
    )
    @action(detail=True, methods=["post"])
    def mark_solved(self, request, pk=None):
        """Mark a CAPTCHA event as solved."""
        captcha_event = self.get_object()
        if captcha_event.status == "SOLVED":
            return Response({"detail": "Captcha already marked as solved."}, status=status.HTTP_400_BAD_REQUEST)
        
        captcha_event.status = "SOLVED"
        captcha_event.solved_at = timezone.now()
        captcha_event.save()

        task = captcha_event.task
        if task.status == AutomationTask.CAPTCHA_DETECTED:
            task.status = AutomationTask.PAUSED
            task.notes = (task.notes or "") + f"\nCaptcha on {captcha_event.page_event.url} marked as solved. Task paused for review."
            task.save()
            AutomationLog.objects.create(task=task, level="INFO", message=f"Captcha event {captcha_event.id} marked as solved. Task {task.id} status updated to {task.status}.")
        
        stats, created = AutomationStats.objects.get_or_create(task=task)
        stats.captcha_solves += 1
        stats.save()

        return Response({"detail": "Captcha event marked as solved."}, status=status.HTTP_200_OK)

@extend_schema_view(
    list=extend_schema(
        summary="List automation logs",
        description="Retrieve a list of system and task logs.",
        tags=["Logs"]
    ),
    retrieve=extend_schema(
        summary="Retrieve log entry",
        description="Get detailed information about a specific log entry.",
        tags=["Logs"]
    )
)
class AutomationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing automation logs.
    
    Provides access to system logs, task logs, and error messages
    for debugging and monitoring purposes.
    """
    queryset = AutomationLog.objects.all().order_by("-timestamp")
    serializer_class = AutomationLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["task", "level"]
    search_fields = ["message", "details"]

    def get_queryset(self):
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return self.queryset.filter(task__id=task_id)
        return super().get_queryset()

@extend_schema_view(
    list=extend_schema(
        summary="List automation statistics",
        description="Retrieve a list of automation task statistics.",
        tags=["System"]
    ),
    retrieve=extend_schema(
        summary="Retrieve task statistics",
        description="Get detailed statistics for a specific automation task.",
        tags=["System"]
    )
)
class AutomationStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing automation statistics.
    
    Provides access to performance metrics, resource usage,
    and task completion statistics.
    """
    queryset = AutomationStats.objects.all()
    serializer_class = AutomationStatsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["task"]

@extend_schema_view(
    list=extend_schema(
        summary="Get system health status",
        description="Retrieve current system health and status information.",
        tags=["System"]
    )
)
class SystemViewSet(viewsets.ViewSet):
    """
    ViewSet for system health and monitoring.
    
    Provides system health checks, performance metrics,
    and monitoring data for the automation platform.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_health_status_data():
        """Get comprehensive system health data."""
        django_version = f"{platform.python_version()}"
        python_version = f"{sys.version.split(' ')[0]}"

        try:
            from celery.app.control import Control
            from automation_backend.celery import app as celery_app
            i = celery_app.control.inspect()
            active_workers = i.active()
            celery_status = "UP" if active_workers else "DOWN"
        except Exception as e:
            celery_status = f"ERROR: {e}"
            logger.error(f"Celery health check failed: {e}")

        redis_status = "DOWN"
        try:
            import redis
            r = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=1)
            r.ping()
            redis_status = "UP"
        except Exception as e:
            redis_status = f"ERROR: {e}"
            logger.error(f"Redis health check failed: {e}")

        db_status = "DOWN"
        try:
            connection.ensure_connection()
            db_status = "UP"
        except Exception as e:
            db_status = f"ERROR: {e}"
            logger.error(f"Database health check failed: {e}")

        system_metrics = get_system_metrics()

        active_tasks = AutomationTask.objects.filter(status=AutomationTask.RUNNING).count()
        pending_tasks = AutomationTask.objects.filter(status=AutomationTask.PENDING).count()
        failed_tasks = AutomationTask.objects.filter(status=AutomationTask.FAILED).count()

        uptime_seconds = (timezone.now() - AutomationTask.objects.order_by('created_at').first().created_at).total_seconds() if AutomationTask.objects.exists() else 0

        return {
            "status": "OK",
            "timestamp": timezone.now().isoformat(),
            "django_version": django_version,
            "python_version": python_version,
            "celery_status": celery_status,
            "redis_status": redis_status,
            "database_status": db_status,
            "memory_usage_mb": round(system_metrics.get("memory_usage_mb", 0.0), 2),
            "cpu_usage_percent": round(system_metrics.get("cpu_usage_percent", 0.0), 2),
            "disk_usage_percent": round(system_metrics.get("disk_usage_percent", 0.0), 2),
            "active_tasks": active_tasks,
            "pending_tasks": pending_tasks,
            "failed_tasks": failed_tasks,
            "uptime_seconds": round(uptime_seconds, 2)
        }

    @extend_schema(
        summary="Get system health",
        description="Get current system health status and metrics.",
        responses={200: SystemHealthSerializer},
        tags=["System"]
    )
    @action(detail=False, methods=["get"])
    def health_status(self, request):
        """Get system health status."""
        data = self.get_health_status_data()
        serializer = SystemHealthSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get performance overview",
        description="Get aggregated performance metrics across all tasks.",
        responses={200: {"description": "Performance overview data"}},
        tags=["System"]
    )
    @action(detail=False, methods=["get"])
    def performance_overview(self, request):
        """Get performance overview data."""
        total_stats = AutomationStats.objects.aggregate(
            avg_runtime=Avg('total_runtime_seconds'),
            avg_page_load=Avg('avg_page_load_time'),
            total_pages=Sum('pages_visited'),
            total_data=Sum('data_extracted_count'),
            total_captchas=Sum('captcha_detections'),
            total_errors=Sum('errors_encountered')
        )
        
        system_metrics = get_system_metrics()

        return Response({
            "overall_avg_runtime_seconds": round(total_stats['avg_runtime'], 2) if total_stats['avg_runtime'] else 0,
            "overall_avg_page_load_time_seconds": round(total_stats['avg_page_load'], 2) if total_stats['avg_page_load'] else 0,
            "overall_total_pages_visited": total_stats['total_pages'] if total_stats['total_pages'] else 0,
            "overall_total_data_extracted_items": total_stats['total_data'] if total_stats['total_data'] else 0,
            "overall_total_captcha_detections": total_stats['total_captchas'] if total_stats['total_captchas'] else 0,
            "overall_total_errors": total_stats['total_errors'] if total_stats['total_errors'] else 0,
            "current_system_cpu_usage_percent": round(system_metrics.get("cpu_usage_percent", 0.0), 2),
            "current_system_memory_usage_mb": round(system_metrics.get("memory_usage_mb", 0.0), 2),
        }, status=status.HTTP_200_OK)
