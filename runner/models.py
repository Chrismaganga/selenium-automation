from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class AutomationTask(models.Model):
    """Main automation task model"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('CAPTCHA_DETECTED', 'Captcha Detected'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('PAUSED', 'Paused'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    
    # Task configuration
    start_url = models.URLField()
    max_pages = models.PositiveIntegerField(default=3)
    max_depth = models.PositiveIntegerField(default=2)
    delay_between_requests = models.FloatField(default=1.0)
    timeout = models.PositiveIntegerField(default=30)
    
    # Browser configuration
    user_agent = models.CharField(max_length=512, blank=True, default='')
    headless = models.BooleanField(default=True)
    window_size = models.CharField(max_length=20, default='1920x1080')
    
    # Task management
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Results and metadata
    total_pages_visited = models.PositiveIntegerField(default=0)
    total_errors = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    
    # Configuration JSON for advanced settings
    config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"Task {self.id} - {self.name or self.start_url} ({self.status})"
    
    @property
    def duration(self):
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return None
    
    @property
    def is_active(self):
        return self.status in ['PENDING', 'RUNNING']


class PageEvent(models.Model):
    """Individual page visit events"""
    
    EVENT_TYPES = [
        ('PAGE_LOAD', 'Page Load'),
        ('CAPTCHA_DETECTED', 'Captcha Detected'),
        ('ERROR', 'Error'),
        ('REDIRECT', 'Redirect'),
        ('FORM_SUBMIT', 'Form Submit'),
        ('CLICK', 'Click'),
        ('SCROLL', 'Scroll'),
    ]
    
    task = models.ForeignKey(AutomationTask, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='PAGE_LOAD')
    
    # Page information
    url = models.URLField()
    title = models.CharField(max_length=512, blank=True, default='')
    status_code = models.PositiveIntegerField(null=True, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    load_time = models.FloatField(null=True, blank=True)  # in seconds
    
    # Screenshots and HTML
    screenshot = models.ImageField(upload_to='screenshots/', null=True, blank=True)
    html_content = models.FileField(upload_to='html/', null=True, blank=True)
    
    # Additional data
    note = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['task', 'timestamp']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.url} ({self.timestamp})"


class CaptchaEvent(models.Model):
    """Specific CAPTCHA detection events"""
    
    CAPTCHA_TYPES = [
        ('RECAPTCHA_V2', 'reCAPTCHA v2'),
        ('RECAPTCHA_V3', 'reCAPTCHA v3'),
        ('HCAPTCHA', 'hCaptcha'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    STATUS_CHOICES = [
        ('DETECTED', 'Detected'),
        ('SOLVED', 'Solved'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped'),
    ]
    
    task = models.ForeignKey(AutomationTask, on_delete=models.CASCADE, related_name='captcha_events')
    page_event = models.ForeignKey(PageEvent, on_delete=models.CASCADE, related_name='captcha_events')
    
    captcha_type = models.CharField(max_length=20, choices=CAPTCHA_TYPES, default='UNKNOWN')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DETECTED')
    
    # Detection details
    detected_at = models.DateTimeField(auto_now_add=True)
    solved_at = models.DateTimeField(null=True, blank=True)
    solved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Visual evidence
    screenshot = models.ImageField(upload_to='captcha_screenshots/', null=True, blank=True)
    
    # Additional data
    notes = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"{self.captcha_type} - {self.status} ({self.detected_at})"


class AutomationLog(models.Model):
    """Detailed logging for debugging and monitoring"""
    
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    task = models.ForeignKey(AutomationTask, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='INFO')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional context
    module = models.CharField(max_length=100, blank=True, default='')
    function = models.CharField(max_length=100, blank=True, default='')
    line_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['task', 'timestamp']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.message[:50]}..."


class AutomationStats(models.Model):
    """Aggregated statistics for monitoring"""
    
    task = models.OneToOneField(AutomationTask, on_delete=models.CASCADE, related_name='stats')
    
    # Performance metrics
    total_requests = models.PositiveIntegerField(default=0)
    successful_requests = models.PositiveIntegerField(default=0)
    failed_requests = models.PositiveIntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    
    # CAPTCHA metrics
    captcha_detections = models.PositiveIntegerField(default=0)
    captcha_solves = models.PositiveIntegerField(default=0)
    
    # Resource usage
    memory_peak = models.PositiveIntegerField(default=0)  # in MB
    cpu_usage_peak = models.FloatField(default=0.0)  # percentage
    
    # Data collected
    total_screenshots = models.PositiveIntegerField(default=0)
    total_html_pages = models.PositiveIntegerField(default=0)
    total_data_size = models.PositiveIntegerField(default=0)  # in bytes
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stats for Task {self.task.id}"
    
    @property
    def success_rate(self):
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def captcha_solve_rate(self):
        if self.captcha_detections == 0:
            return 0.0
        return (self.captcha_solves / self.captcha_detections) * 100
