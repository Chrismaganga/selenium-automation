from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    AutomationTask, PageEvent, CaptchaEvent, 
    AutomationLog, AutomationStats
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class PageEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageEvent
        fields = [
            'id', 'event_type', 'url', 'title', 'status_code',
            'timestamp', 'load_time', 'screenshot', 'html_content',
            'note', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']


class CaptchaEventSerializer(serializers.ModelSerializer):
    solved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CaptchaEvent
        fields = [
            'id', 'captcha_type', 'status', 'detected_at',
            'solved_at', 'solved_by', 'screenshot', 'notes', 'metadata'
        ]
        read_only_fields = ['id', 'detected_at']


class AutomationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationLog
        fields = [
            'id', 'level', 'message', 'timestamp', 'module',
            'function', 'line_number', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']


class AutomationStatsSerializer(serializers.ModelSerializer):
    success_rate = serializers.ReadOnlyField()
    captcha_solve_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = AutomationStats
        fields = [
            'total_requests', 'successful_requests', 'failed_requests',
            'average_response_time', 'captcha_detections', 'captcha_solves',
            'memory_peak', 'cpu_usage_peak', 'total_screenshots',
            'total_html_pages', 'total_data_size', 'success_rate',
            'captcha_solve_rate', 'updated_at'
        ]
        read_only_fields = ['updated_at']


class AutomationTaskListSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    duration = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = AutomationTask
        fields = [
            'id', 'name', 'description', 'start_url', 'status',
            'priority', 'created_by', 'assigned_to', 'created_at',
            'started_at', 'finished_at', 'total_pages_visited',
            'total_errors', 'duration', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'started_at', 'finished_at']


class AutomationTaskDetailSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    events = PageEventSerializer(many=True, read_only=True)
    captcha_events = CaptchaEventSerializer(many=True, read_only=True)
    logs = AutomationLogSerializer(many=True, read_only=True)
    stats = AutomationStatsSerializer(read_only=True)
    duration = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = AutomationTask
        fields = [
            'id', 'name', 'description', 'start_url', 'max_pages',
            'max_depth', 'delay_between_requests', 'timeout',
            'user_agent', 'headless', 'window_size', 'status',
            'priority', 'created_by', 'assigned_to', 'created_at',
            'started_at', 'finished_at', 'updated_at', 'total_pages_visited',
            'total_errors', 'notes', 'error_message', 'config',
            'events', 'captcha_events', 'logs', 'stats',
            'duration', 'is_active'
        ]
        read_only_fields = [
            'id', 'created_at', 'started_at', 'finished_at',
            'updated_at', 'total_pages_visited', 'total_errors'
        ]


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationTask
        fields = [
            'name', 'description', 'start_url', 'max_pages',
            'max_depth', 'delay_between_requests', 'timeout',
            'user_agent', 'headless', 'window_size', 'priority',
            'assigned_to', 'notes', 'config'
        ]
    
    def validate_start_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value
    
    def validate_max_pages(self, value):
        if value < 1 or value > 1000:
            raise serializers.ValidationError("Max pages must be between 1 and 1000")
        return value
    
    def validate_delay_between_requests(self, value):
        if value < 0.1 or value > 60:
            raise serializers.ValidationError("Delay must be between 0.1 and 60 seconds")
        return value


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationTask
        fields = [
            'name', 'description', 'priority', 'assigned_to',
            'notes', 'config'
        ]
    
    def validate(self, data):
        # Prevent updating certain fields if task is running
        if self.instance and self.instance.status == 'RUNNING':
            if 'priority' in data and data['priority'] != self.instance.priority:
                raise serializers.ValidationError("Cannot change priority while task is running")
        return data
