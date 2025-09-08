from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    AutomationTask, PageEvent, CaptchaEvent, 
    AutomationLog, AutomationStats
)
from .serializers import (
    AutomationTaskListSerializer, AutomationTaskDetailSerializer,
    TaskCreateSerializer, TaskUpdateSerializer, PageEventSerializer,
    CaptchaEventSerializer, AutomationLogSerializer, AutomationStatsSerializer
)
from .tasks import execute_automation_task, cleanup_old_tasks, generate_daily_report


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AutomationTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing automation tasks
    """
    queryset = AutomationTask.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'created_by', 'assigned_to']
    search_fields = ['name', 'description', 'start_url', 'notes']
    ordering_fields = ['created_at', 'started_at', 'finished_at', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AutomationTaskListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            if self.action == 'create':
                return TaskCreateSerializer
            return TaskUpdateSerializer
        return AutomationTaskDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start an automation task"""
        task = self.get_object()
        
        if task.status not in ['PENDING', 'FAILED', 'CAPTCHA_DETECTED']:
            return Response(
                {'detail': 'Task is not in a startable state.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset task status
        task.status = 'PENDING'
        task.started_at = None
        task.finished_at = None
        task.error_message = ''
        task.save()
        
        # Queue the task
        execute_automation_task.delay(str(task.id))
        
        return Response(
            {'detail': 'Task queued for execution.'},
            status=status.HTTP_202_ACCEPTED
        )
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a running task"""
        task = self.get_object()
        
        if task.status != 'RUNNING':
            return Response(
                {'detail': 'Task is not running.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'PAUSED'
        task.save()
        
        return Response({'detail': 'Task paused.'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a task"""
        task = self.get_object()
        
        if task.status in ['COMPLETED', 'CANCELLED']:
            return Response(
                {'detail': 'Task cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'CANCELLED'
        task.finished_at = timezone.now()
        task.save()
        
        return Response({'detail': 'Task cancelled.'})
    
    @action(detail=True, methods=['post'])
    def solve_captcha(self, request, pk=None):
        """Mark CAPTCHA as solved and restart task"""
        task = self.get_object()
        
        if task.status != 'CAPTCHA_DETECTED':
            return Response(
                {'detail': 'No CAPTCHA detected for this task.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update CAPTCHA events
        captcha_events = task.captcha_events.filter(status='DETECTED')
        for event in captcha_events:
            event.status = 'SOLVED'
            event.solved_at = timezone.now()
            event.solved_by = request.user
            event.save()
        
        # Restart task
        task.status = 'PENDING'
        task.started_at = None
        task.finished_at = None
        task.save()
        
        execute_automation_task.delay(str(task.id))
        
        return Response({'detail': 'CAPTCHA marked as solved. Task restarted.'})
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for a specific task"""
        task = self.get_object()
        logs = task.logs.all().order_by('-timestamp')
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = AutomationLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AutomationLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a specific task"""
        task = self.get_object()
        stats, created = AutomationStats.objects.get_or_create(task=task)
        serializer = AutomationStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_tasks = queryset.count()
        active_tasks = queryset.filter(status__in=['PENDING', 'RUNNING']).count()
        completed_tasks = queryset.filter(status='COMPLETED').count()
        failed_tasks = queryset.filter(status='FAILED').count()
        captcha_tasks = queryset.filter(status='CAPTCHA_DETECTED').count()
        
        # Recent activity
        recent_tasks = queryset.order_by('-created_at')[:10]
        recent_serializer = AutomationTaskListSerializer(recent_tasks, many=True)
        
        # Performance metrics
        stats = AutomationStats.objects.filter(task__in=queryset)
        total_pages = sum(s.total_requests for s in stats)
        total_captchas = sum(s.captcha_detections for s in stats)
        avg_success_rate = stats.aggregate(avg=Avg('successful_requests'))['avg'] or 0
        
        dashboard_data = {
            'summary': {
                'total_tasks': total_tasks,
                'active_tasks': active_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'captcha_tasks': captcha_tasks,
                'total_pages_visited': total_pages,
                'total_captcha_detections': total_captchas,
                'average_success_rate': round(avg_success_rate, 2)
            },
            'recent_tasks': recent_serializer.data
        }
        
        return Response(dashboard_data)


class PageEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing page events
    """
    serializer_class = PageEventSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['task', 'event_type', 'status_code']
    search_fields = ['url', 'title', 'note']
    ordering_fields = ['timestamp', 'load_time']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = PageEvent.objects.all()
        
        # Filter by task if specified
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(task__created_by=self.request.user) | 
                Q(task__assigned_to=self.request.user)
            )
        
        return queryset


class CaptchaEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing CAPTCHA events
    """
    serializer_class = CaptchaEventSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['task', 'captcha_type', 'status']
    search_fields = ['notes']
    ordering_fields = ['detected_at', 'solved_at']
    ordering = ['-detected_at']
    
    def get_queryset(self):
        queryset = CaptchaEvent.objects.all()
        
        # Filter by task if specified
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(task__created_by=self.request.user) | 
                Q(task__assigned_to=self.request.user)
            )
        
        return queryset


class AutomationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing automation logs
    """
    serializer_class = AutomationLogSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['task', 'level']
    search_fields = ['message', 'module', 'function']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = AutomationLog.objects.all()
        
        # Filter by task if specified
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(task__created_by=self.request.user) | 
                Q(task__assigned_to=self.request.user)
            )
        
        return queryset


class SystemViewSet(viewsets.ViewSet):
    """
    System management endpoints
    """
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """Trigger cleanup of old tasks"""
        cleanup_old_tasks.delay()
        return Response({'detail': 'Cleanup task queued.'})
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate daily report"""
        generate_daily_report.delay()
        return Response({'detail': 'Report generation queued.'})
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """System health check"""
        from django.db import connection
        from django.core.cache import cache
        
        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = "OK"
        except Exception as e:
            db_status = f"Error: {e}"
        
        # Check cache
        try:
            cache.set('health_check', 'OK', 10)
            cache_status = "OK" if cache.get('health_check') == 'OK' else "Error"
        except Exception as e:
            cache_status = f"Error: {e}"
        
        return Response({
            'database': db_status,
            'cache': cache_status,
            'timestamp': timezone.now().isoformat()
        })
