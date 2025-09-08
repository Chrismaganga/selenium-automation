"""
URL configuration for automation_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    """API root view with available endpoints"""
    return JsonResponse({
        'message': 'Selenium Automation Backend API',
        'version': '2.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'tasks': '/api/tasks/',
            'page_events': '/api/page-events/',
            'captcha_events': '/api/captcha-events/',
            'logs': '/api/logs/',
            'system': '/api/system/',
        },
        'documentation': 'Visit /admin/ for Django admin interface'
    })

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/', include('runner.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
