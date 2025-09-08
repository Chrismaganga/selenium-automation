from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AutomationTask, PageEvent, CaptchaEvent, 
    AutomationLog, AutomationStats
)


@admin.register(AutomationTask)
class AutomationTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'start_url', 'status', 'priority', 
        'created_by', 'created_at', 'total_pages_visited', 'total_errors'
    ]
    list_filter = ['status', 'priority', 'created_at', 'headless']
    search_fields = ['name', 'start_url', 'notes']
    readonly_fields = ['id', 'created_at', 'started_at', 'finished_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'start_url')
        }),
        ('Configuration', {
            'fields': (
                'max_pages', 'max_depth', 'delay_between_requests', 
                'timeout', 'user_agent', 'headless', 'window_size'
            )
        }),
        ('Management', {
            'fields': ('status', 'priority', 'created_by', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'finished_at', 'updated_at')
        }),
        ('Results', {
            'fields': ('total_pages_visited', 'total_errors', 'notes', 'error_message')
        }),
        ('Advanced', {
            'fields': ('config',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'assigned_to')


@admin.register(PageEvent)
class PageEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'task', 'event_type', 'url', 'status_code', 
        'timestamp', 'load_time'
    ]
    list_filter = ['event_type', 'status_code', 'timestamp']
    search_fields = ['url', 'title', 'note']
    readonly_fields = ['id', 'timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task')


@admin.register(CaptchaEvent)
class CaptchaEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'task', 'captcha_type', 'status', 
        'detected_at', 'solved_at', 'solved_by'
    ]
    list_filter = ['captcha_type', 'status', 'detected_at']
    search_fields = ['notes']
    readonly_fields = ['id', 'detected_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'solved_by')


@admin.register(AutomationLog)
class AutomationLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'level', 'message_short', 'timestamp']
    list_filter = ['level', 'timestamp', 'module']
    search_fields = ['message', 'module', 'function']
    readonly_fields = ['id', 'timestamp']
    
    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task')


@admin.register(AutomationStats)
class AutomationStatsAdmin(admin.ModelAdmin):
    list_display = [
        'task', 'total_requests', 'successful_requests', 
        'success_rate', 'captcha_detections', 'updated_at'
    ]
    readonly_fields = ['updated_at']
    
    def success_rate(self, obj):
        return f"{obj.success_rate:.1f}%"
    success_rate.short_description = 'Success Rate'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task')
