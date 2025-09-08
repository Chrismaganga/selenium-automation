"""
Enhanced API views with advanced features
"""
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
from .enhanced_tasks import execute_enhanced_automation_task
from .automation_templates import TemplateManager
from .monitoring import (
    alert_manager, performance_monitor, system_health_monitor, 
    real_time_monitor
)

import logging
logger = logging.getLogger(__name__)


class EnhancedAutomationTaskViewSet(viewsets.ModelViewSet):
    """
    Enhanced ViewSet for managing automation tasks with advanced features
    """
    queryset = AutomationTask.objects.all()
    pagination_class = PageNumberPagination
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
    def start_enhanced(self, request, pk=None):
        """Start an enhanced automation task"""
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
        
        # Queue the enhanced task
        execute_enhanced_automation_task.delay(str(task.id))
        
        return Response(
            {'detail': 'Enhanced automation task queued for execution.'},
            status=status.HTTP_202_ACCEPTED
        )
    
    @action(detail=True, methods=['post'])
    def create_from_template(self, request, pk=None):
        """Create a new task from a template"""
        template_name = request.data.get('template_name')
        customizations = request.data.get('customizations', {})
        
        if not template_name:
            return Response(
                {'detail': 'Template name is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            template_manager = TemplateManager()
            task = template_manager.create_task_from_template(
                template_name, 
                request.user, 
                **customizations
            )
            
            serializer = AutomationTaskDetailSerializer(task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': f'Failed to create task from template: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def get_template_recommendations(self, request, pk=None):
        """Get template recommendations for a task"""
        task = self.get_object()
        
        try:
            template_manager = TemplateManager()
            recommendations = template_manager.get_template_recommendations(
                task.start_url,
                task.description
            )
            
            return Response({
                'recommendations': recommendations,
                'available_templates': template_manager.list_templates()
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to get recommendations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def performance_analysis(self, request, pk=None):
        """Get detailed performance analysis for a task"""
        task = self.get_object()
        
        try:
            stats, created = AutomationStats.objects.get_or_create(task=task)
            performance_data = performance_monitor.get_performance_summary(task, stats)
            
            # Add AI insights
            ai_insights = []
            if performance_data.get('error_rate', 0) > 0.3:
                ai_insights.append("High error rate detected - consider reviewing target URLs")
            
            if performance_data.get('memory_peak_mb', 0) > 1000:
                ai_insights.append("High memory usage - consider reducing max_pages")
            
            if performance_data.get('captcha_detections', 0) > 5:
                ai_insights.append("Frequent CAPTCHA detections - consider different approach")
            
            performance_data['ai_insights'] = ai_insights
            
            return Response(performance_data)
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to analyze performance: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def real_time_status(self, request, pk=None):
        """Get real-time status for a running task"""
        task = self.get_object()
        
        try:
            monitoring_data = real_time_monitor.get_monitoring_data(str(task.id))
            
            if monitoring_data:
                return Response({
                    'is_monitored': True,
                    'status': task.status,
                    'start_time': monitoring_data['start_time'].isoformat(),
                    'last_update': monitoring_data['last_update'].isoformat(),
                    'duration_minutes': (monitoring_data['last_update'] - monitoring_data['start_time']).total_seconds() / 60,
                    'status_history': monitoring_data['status_history'][-5:]  # Last 5 updates
                })
            else:
                return Response({
                    'is_monitored': False,
                    'status': task.status,
                    'message': 'Task is not currently being monitored'
                })
                
        except Exception as e:
            return Response(
                {'detail': f'Failed to get real-time status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def enhanced_dashboard(self, request):
        """Get enhanced dashboard with AI insights"""
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
        
        # AI insights
        ai_insights = []
        if avg_success_rate < 70:
            ai_insights.append("Low success rate detected - consider reviewing task configurations")
        
        if total_captchas > 10:
            ai_insights.append("High CAPTCHA detection rate - consider implementing solving strategies")
        
        if active_tasks > 5:
            ai_insights.append("High number of active tasks - monitor system resources")
        
        # System health
        try:
            system_health = system_health_monitor.run_health_checks()
        except Exception:
            system_health = {'overall_status': 'unknown'}
        
        # Real-time monitoring
        real_time_data = real_time_monitor.get_all_monitoring_data()
        
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
            'ai_insights': ai_insights,
            'system_health': system_health,
            'real_time_monitoring': real_time_data,
            'recent_tasks': recent_serializer.data
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'])
    def available_templates(self, request):
        """Get all available automation templates"""
        try:
            template_manager = TemplateManager()
            templates = template_manager.list_templates()
            
            return Response({
                'templates': templates,
                'count': len(templates)
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to get templates: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def bulk_create_from_template(self, request):
        """Create multiple tasks from a template with different configurations"""
        template_name = request.data.get('template_name')
        configurations = request.data.get('configurations', [])
        
        if not template_name or not configurations:
            return Response(
                {'detail': 'Template name and configurations are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            template_manager = TemplateManager()
            created_tasks = []
            
            for config in configurations:
                task = template_manager.create_task_from_template(
                    template_name,
                    request.user,
                    **config
                )
                created_tasks.append(task)
            
            serializer = AutomationTaskListSerializer(created_tasks, many=True)
            return Response({
                'created_tasks': serializer.data,
                'count': len(created_tasks)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to create bulk tasks: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SystemMonitoringViewSet(viewsets.ViewSet):
    """
    System monitoring and health check endpoints
    """
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def health_status(self, request):
        """Get comprehensive system health status"""
        try:
            health_status = system_health_monitor.run_health_checks()
            system_metrics = system_health_monitor.get_system_metrics()
            
            return Response({
                'health_status': health_status,
                'system_metrics': system_metrics,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to get health status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def performance_overview(self, request):
        """Get system performance overview"""
        try:
            from .models import AutomationTask, AutomationStats
            from django.utils import timezone
            from datetime import timedelta
            
            # Get recent performance data
            recent_tasks = AutomationTask.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            )
            
            stats = AutomationStats.objects.filter(task__in=recent_tasks)
            
            performance_data = {
                'total_tasks_week': recent_tasks.count(),
                'completed_tasks_week': recent_tasks.filter(status='COMPLETED').count(),
                'average_success_rate': stats.aggregate(avg=Avg('successful_requests'))['avg'] or 0,
                'total_captcha_detections': sum(s.captcha_detections for s in stats),
                'average_memory_usage': stats.aggregate(avg=Avg('memory_peak'))['avg'] or 0,
                'average_cpu_usage': stats.aggregate(avg=Avg('cpu_usage_peak'))['avg'] or 0,
                'active_monitors': real_time_monitor.get_all_monitoring_data()['active_tasks']
            }
            
            return Response(performance_data)
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to get performance overview: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def trigger_health_check(self, request):
        """Manually trigger system health check"""
        try:
            health_status = system_health_monitor.run_health_checks()
            
            if health_status['overall_status'] != 'healthy':
                alert_manager.send_alert(
                    None,
                    f"Manual health check failed: {health_status['overall_status']}",
                    'warning'
                )
            
            return Response({
                'status': 'completed',
                'health_status': health_status
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Health check failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def alert_history(self, request):
        """Get alert history"""
        try:
            # Get recent alerts from logs
            recent_alerts = AutomationLog.objects.filter(
                message__startswith='ALERT:',
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).order_by('-timestamp')[:50]
            
            alerts = []
            for alert in recent_alerts:
                alerts.append({
                    'task_id': alert.task.id if alert.task else None,
                    'message': alert.message.replace('ALERT: ', ''),
                    'level': alert.level,
                    'timestamp': alert.timestamp.isoformat(),
                    'metadata': alert.metadata
                })
            
            return Response({
                'alerts': alerts,
                'count': len(alerts)
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to get alert history: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataAnalysisViewSet(viewsets.ViewSet):
    """
    Data analysis and insights endpoints
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def content_analysis(self, request):
        """Get content analysis insights"""
        try:
            from .models import PageEvent
            
            # Get recent page events with AI analysis
            recent_events = PageEvent.objects.filter(
                task__created_by=request.user,
                metadata__ai_analysis__isnull=False
            ).order_by('-timestamp')[:100]
            
            analysis_insights = []
            for event in recent_events:
                ai_analysis = event.metadata.get('ai_analysis', {})
                if ai_analysis:
                    analysis_insights.append({
                        'url': event.url,
                        'page_type': ai_analysis.get('page_type', {}),
                        'content_quality': ai_analysis.get('content_quality', {}),
                        'seo_indicators': ai_analysis.get('seo_indicators', {}),
                        'timestamp': event.timestamp.isoformat()
                    })
            
            return Response({
                'insights': analysis_insights,
                'count': len(analysis_insights)
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to get content analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def data_extraction_summary(self, request):
        """Get data extraction summary"""
        try:
            from .models import PageEvent
            
            # Get recent page events with extracted data
            recent_events = PageEvent.objects.filter(
                task__created_by=request.user,
                metadata__extracted_data__isnull=False
            ).order_by('-timestamp')[:100]
            
            extraction_summary = {
                'total_events': recent_events.count(),
                'contact_extractions': 0,
                'product_extractions': 0,
                'content_analyses': 0
            }
            
            for event in recent_events:
                extracted_data = event.metadata.get('extracted_data', {})
                if extracted_data.get('contact'):
                    extraction_summary['contact_extractions'] += 1
                if extracted_data.get('product'):
                    extraction_summary['product_extractions'] += 1
                if extracted_data.get('content'):
                    extraction_summary['content_analyses'] += 1
            
            return Response(extraction_summary)
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to get extraction summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
