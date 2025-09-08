from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json

# Frontend Views (temporarily without authentication)
def homepage_view(request):
    """Custom homepage with navigation to documentation"""
    return render(request, 'homepage.html', {
        'title': 'Selenium Automation Backend API',
        'description': 'Advanced Web Automation Platform with AI-Powered Features',
        'endpoints': {
            'admin': '/admin/',
            'api_schema': '/api/schema/',
            'swagger_ui': '/api/schema/swagger-ui/',
            'redoc': '/api/schema/redoc/',
            'tasks': '/api/tasks/',
            'page_events': '/api/page-events/',
            'captcha_events': '/api/captcha-events/',
            'logs': '/api/logs/',
            'stats': '/api/stats/',
            'system_health': '/api/system/health/',
            'available_templates': '/api/tasks/available_templates/',
            'enhanced_dashboard': '/api/tasks/enhanced_dashboard/',
        }
    })

def dashboard_view(request):
    """Main dashboard view"""
    return render(request, 'dashboard.html', {
        'title': 'Dashboard',
        'page_title': 'Dashboard'
    })

def tasks_view(request):
    """Task management view"""
    return render(request, 'tasks.html', {
        'title': 'Task Management',
        'page_title': 'Task Management'
    })

def monitoring_view(request):
    """System monitoring view"""
    return render(request, 'monitoring.html', {
        'title': 'System Monitoring',
        'page_title': 'System Monitoring'
    })

def logs_view(request):
    """System logs view"""
    return render(request, 'logs.html', {
        'title': 'System Logs',
        'page_title': 'System Logs'
    })

def events_view(request):
    """Events view"""
    return render(request, 'events.html', {
        'title': 'Events',
        'page_title': 'Events'
    })

# Authentication Views
def login_view(request):
    """Login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'Successfully logged out!')
    return redirect('homepage')

# API Views for Frontend
@method_decorator(csrf_exempt, name='dispatch')
class FrontendAPIView(View):
    """Base class for frontend API views"""
    
    def get_json_data(self, request):
        """Extract JSON data from request"""
        try:
            return json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return {}

@method_decorator(csrf_exempt, name='dispatch')
class DashboardDataView(FrontendAPIView):
    """API endpoint for dashboard data"""
    
    def get(self, request):
        """Get dashboard data"""
        try:
            # Import here to avoid circular imports
            from runner.models import AutomationTask, AutomationStats
            
            # Get basic statistics
            total_tasks = AutomationTask.objects.count()
            completed_tasks = AutomationTask.objects.filter(status='COMPLETED').count()
            failed_tasks = AutomationTask.objects.filter(status='FAILED').count()
            running_tasks = AutomationTask.objects.filter(status='RUNNING').count()
            
            # Calculate success rate
            success_rate = 0
            if total_tasks > 0:
                success_rate = (completed_tasks / total_tasks) * 100
            
            # Get recent tasks
            recent_tasks = AutomationTask.objects.order_by('-created_at')[:10]
            recent_tasks_data = []
            for task in recent_tasks:
                recent_tasks_data.append({
                    'id': str(task.id),
                    'name': task.name or 'Unnamed Task',
                    'status': task.status.lower(),
                    'priority': task.priority.lower(),
                    'template': 'Custom',  # Default since no template field
                    'created_at': task.created_at.isoformat(),
                    'url': task.start_url
                })
            
            data = {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'running_tasks': running_tasks,
                'success_rate': round(success_rate, 2),
                'recent_tasks': recent_tasks_data
            }
            
            return JsonResponse({'success': True, 'data': data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SystemHealthView(FrontendAPIView):
    """API endpoint for system health data"""
    
    def get(self, request):
        """Get system health data"""
        try:
            import psutil
            import redis
            from celery import current_app
            
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check Redis connection
            try:
                r = redis.Redis(host='localhost', port=6379, db=0)
                redis_connected = r.ping()
            except:
                redis_connected = False
            
            # Check Celery workers
            try:
                inspect = current_app.control.inspect()
                active_workers = inspect.active()
                celery_workers = len(active_workers) if active_workers else 0
            except:
                celery_workers = 0
            
            # Calculate uptime (simplified)
            import time
            uptime = time.time() - psutil.boot_time()
            
            data = {
                'overall_health': redis_connected and celery_workers > 0,
                'cpu_usage': round(cpu_usage, 2),
                'memory_usage': round(memory.percent, 2),
                'disk_usage': round(disk.percent, 2),
                'redis_connected': redis_connected,
                'celery_workers': celery_workers,
                'uptime': int(uptime),
                'active_tasks': 0,  # This would need to be calculated from actual running tasks
                'captcha_events': 0,  # This would need to be calculated from actual events
                'success_rate': 0  # This would need to be calculated from actual stats
            }
            
            return JsonResponse({'success': True, 'data': data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TasksDataView(FrontendAPIView):
    """API endpoint for tasks data"""
    
    def get(self, request):
        """Get tasks data"""
        try:
            from runner.models import AutomationTask
            from django.core.paginator import Paginator
            from django.db.models import Q
            
            # Get query parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            search = request.GET.get('search', '')
            status = request.GET.get('status', '')
            priority = request.GET.get('priority', '')
            
            # Build query
            queryset = AutomationTask.objects.all()
            
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) | 
                    Q(start_url__icontains=search) |
                    Q(description__icontains=search)
                )
            
            if status:
                queryset = queryset.filter(status=status.upper())
            
            if priority:
                queryset = queryset.filter(priority=priority.upper())
            
            # Order by created date
            queryset = queryset.order_by('-created_at')
            
            # Paginate
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize tasks
            tasks_data = []
            for task in page_obj:
                tasks_data.append({
                    'id': str(task.id),
                    'name': task.name or 'Unnamed Task',
                    'status': task.status.lower(),
                    'priority': task.priority.lower(),
                    'template': 'Custom',  # Default since no template field
                    'url': task.start_url,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat(),
                    'max_pages': task.max_pages,
                    'delay_between_requests': task.delay_between_requests,
                    'headless': task.headless,
                    'take_screenshots': False,  # Default since no screenshots field
                    'notes': task.description
                })
            
            data = {
                'results': tasks_data,
                'count': paginator.count,
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
            
            return JsonResponse({'success': True, 'data': data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def post(self, request):
        """Create new task"""
        try:
            from runner.models import AutomationTask
            from django.contrib.auth.models import User
            
            data = self.get_json_data(request)
            
            # Get or create a default user
            user, created = User.objects.get_or_create(
                username='admin',
                defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
            )
            
            # Create task
            task = AutomationTask.objects.create(
                name=data.get('name', 'Unnamed Task'),
                description=data.get('notes', ''),
                start_url=data.get('url', ''),
                priority=data.get('priority', 'NORMAL').upper(),
                max_pages=data.get('max_pages', 10),
                delay_between_requests=data.get('delay_between_requests', 2),
                headless=data.get('headless', True),
                created_by=user
            )
            
            return JsonResponse({
                'success': True, 
                'data': {
                    'id': str(task.id),
                    'message': 'Task created successfully'
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TaskDetailView(FrontendAPIView):
    """API endpoint for individual task data"""
    
    def get(self, request, task_id):
        """Get task details"""
        try:
            from runner.models import AutomationTask
            
            task = AutomationTask.objects.get(id=task_id)
            
            data = {
                'id': str(task.id),
                'name': task.name or 'Unnamed Task',
                'status': task.status.lower(),
                'priority': task.priority.lower(),
                'template': 'Custom',  # Default since no template field
                'url': task.start_url,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat(),
                'max_pages': task.max_pages,
                'delay_between_requests': task.delay_between_requests,
                'headless': task.headless,
                'take_screenshots': False,  # Default since no screenshots field
                'notes': task.description
            }
            
            return JsonResponse({'success': True, 'data': data})
            
        except AutomationTask.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def delete(self, request, task_id):
        """Delete task"""
        try:
            from runner.models import AutomationTask
            
            task = AutomationTask.objects.get(id=task_id)
            task.delete()
            
            return JsonResponse({'success': True, 'message': 'Task deleted successfully'})
            
        except AutomationTask.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

def task_create_view(request):
    """Task creation view"""
    return render(request, 'task_create.html', {
        'title': 'Create New Task',
        'page_title': 'Create New Task'
    })

def task_edit_view(request, task_id):
    """Task edit view"""
    return render(request, 'task_edit.html', {
        'title': f'Edit Task {task_id}',
        'page_title': f'Edit Task {task_id}',
        'task_id': task_id
    })

def task_detail_view(request, task_id):
    """Task detail view"""
    return render(request, 'task_detail.html', {
        'title': f'Task {task_id} Details',
        'page_title': f'Task {task_id} Details',
        'task_id': task_id
    })

class TaskDetailView(View):
    """API view for getting individual task details"""
    
    def get(self, request, task_id):
        try:
            from runner.models import AutomationTask
            task = AutomationTask.objects.get(id=task_id)
            
            # Calculate additional fields
            duration = None
            if task.started_at and task.finished_at:
                duration = str(task.finished_at - task.started_at)
            elif task.started_at:
                from django.utils import timezone
                duration = str(timezone.now() - task.started_at)
            
            task_data = {
                'id': str(task.id),
                'name': task.name,
                'status': task.status,
                'priority': task.priority,
                'start_url': task.start_url,
                'description': task.description,
                'max_pages': task.max_pages,
                'delay': task.delay,
                'take_screenshots': task.take_screenshots,
                'detect_captchas': task.detect_captchas,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'finished_at': task.finished_at.isoformat() if task.finished_at else None,
                'total_pages_visited': task.total_pages_visited,
                'duration': duration,
                'success_rate': 0,  # Placeholder
                'captcha_events_count': task.captcha_events.count(),
                'error_count': task.logs.filter(level='ERROR').count(),
            }
            
            return JsonResponse({'success': True, 'data': task_data})
        except AutomationTask.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

class TaskLogsView(View):
    """API view for getting task logs"""
    
    def get(self, request):
        try:
            from runner.models import AutomationLog
            from django.core.paginator import Paginator
            
            # Get query parameters
            task_id = request.GET.get('task_id')
            level = request.GET.get('level')
            limit = int(request.GET.get('limit', 50))
            
            # Build query
            logs = AutomationLog.objects.all()
            if task_id:
                logs = logs.filter(task_id=task_id)
            if level:
                logs = logs.filter(level=level)
            
            logs = logs.order_by('-timestamp')[:limit]
            
            log_list = []
            for log in logs:
                log_list.append({
                    'id': str(log.id),
                    'task_id': str(log.task.id) if log.task else None,
                    'level': log.level,
                    'message': log.message,
                    'timestamp': log.timestamp.isoformat(),
                    'details': log.details,
                })
            
            return JsonResponse({'success': True, 'results': log_list, 'count': len(log_list)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
