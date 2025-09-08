from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import render

# DRF Spectacular imports
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Import frontend views
from . import views

# Custom homepage view
def homepage_view(request):
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

urlpatterns = [
    # Homepage
    path("", homepage_view, name="homepage"),
    
    # Admin
    path("admin/", admin.site.urls),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # Frontend Views (without authentication for now)
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("tasks/", views.tasks_view, name="tasks"),
    path("monitoring/", views.monitoring_view, name="monitoring"),
    path("logs/", views.logs_view, name="logs"),
    path("events/", views.events_view, name="events"),
    
    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Frontend API Endpoints
    path("api/frontend/dashboard/", views.DashboardDataView.as_view(), name="frontend_dashboard"),
    path("api/frontend/system/health/", views.SystemHealthView.as_view(), name="frontend_system_health"),
    path("api/frontend/tasks/", views.TasksDataView.as_view(), name="frontend_tasks"),
    path("api/frontend/tasks/<str:task_id>/", views.TaskDetailView.as_view(), name="frontend_task_detail"),
    
    # Task Management URLs
    path("tasks/create/", views.task_create_view, name="task_create"),
    path("tasks/<str:task_id>/edit/", views.task_edit_view, name="task_edit"),
    path("tasks/<str:task_id>/", views.task_detail_view, name="task_detail"),
    
    # Additional API Endpoints
    path("api/frontend/logs/", views.TaskLogsView.as_view(), name="frontend_logs"),
    
    # Backend API
    path("api/", include("runner.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
