from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AutomationTaskViewSet, PageEventViewSet, 
    CaptchaEventViewSet, AutomationLogViewSet, SystemViewSet
)

router = DefaultRouter()
router.register(r'tasks', AutomationTaskViewSet, basename='task')
router.register(r'page-events', PageEventViewSet, basename='page-event')
router.register(r'captcha-events', CaptchaEventViewSet, basename='captcha-event')
router.register(r'logs', AutomationLogViewSet, basename='log')
router.register(r'system', SystemViewSet, basename='system')

urlpatterns = [
    path('', include(router.urls)),
]
