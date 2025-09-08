# Selenium Automation Backend

A comprehensive Django backend for automated web browsing with Selenium, featuring CAPTCHA detection and ethical automation practices.

## ⚠️ Important Notice

This application is designed for **legitimate automation purposes only**:
- Testing your own websites
- Internal QA processes
- Data collection with proper permissions
- Educational purposes

**This tool does NOT bypass CAPTCHAs** - it detects them and halts execution for human intervention.

## Features

### Core Functionality
- **Chrome Selenium Integration**: Automated web browsing with Chrome WebDriver
- **CAPTCHA Detection**: Identifies reCAPTCHA v2, reCAPTCHA v3, and hCaptcha without bypassing
- **Comprehensive Data Collection**: Screenshots, HTML snapshots, performance metrics
- **Background Processing**: Celery-based task queue for scalable automation
- **REST API**: Full-featured API for task management and monitoring

### Advanced Features
- **Multi-user Support**: User authentication and task assignment
- **Real-time Monitoring**: Live task status and progress tracking
- **Detailed Logging**: Comprehensive logging for debugging and analysis
- **Statistics Dashboard**: Performance metrics and analytics
- **Admin Interface**: Django admin for system management
- **Docker Support**: Containerized deployment with Docker Compose

## Quick Start

### Prerequisites
- Python 3.11+
- Redis server
- Chrome browser (for local development)

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd selenium-automation
python setup.py
```

2. **Start Redis** (required for Celery):
```bash
# Using Docker
docker run -p 6379:6379 -d redis:7

# Or install locally
# Ubuntu/Debian: sudo apt-get install redis-server
# macOS: brew install redis
```

3. **Start the application**:
```bash
# Terminal 1: Start Celery worker
celery -A automation_backend worker -l info

# Terminal 2: Start Django server
python manage.py runserver
```

4. **Access the application**:
- Admin interface: http://localhost:8000/admin/
- API: http://localhost:8000/api/
- Default admin: username=`admin`, password=`admin123`

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Usage

### Creating an Automation Task

```bash
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your-token-here" \
  -d '{
    "name": "Website Analysis",
    "description": "Analyze example.com for content",
    "start_url": "https://example.com",
    "max_pages": 5,
    "max_depth": 2,
    "delay_between_requests": 2.0,
    "headless": true,
    "priority": "NORMAL"
  }'
```

### Starting a Task

```bash
curl -X POST http://localhost:8000/api/tasks/{task-id}/start/ \
  -H "Authorization: Token your-token-here"
```

### Monitoring Task Progress

```bash
# Get task details
curl http://localhost:8000/api/tasks/{task-id}/

# Get task logs
curl http://localhost:8000/api/tasks/{task-id}/logs/

# Get task statistics
curl http://localhost:8000/api/tasks/{task-id}/stats/

# Get dashboard data
curl http://localhost:8000/api/tasks/dashboard/
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgres://user:pass@localhost:5432/automation_db

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Security
SECRET_KEY=your-secret-key-here
DEBUG=False

# Media files
MEDIA_ROOT=/path/to/media
MEDIA_URL=/media/
```

### Task Configuration

Tasks support extensive configuration options:

```json
{
  "name": "Custom Task",
  "start_url": "https://example.com",
  "max_pages": 10,
  "max_depth": 3,
  "delay_between_requests": 1.5,
  "timeout": 30,
  "user_agent": "Custom Bot 1.0",
  "headless": true,
  "window_size": "1920x1080",
  "priority": "HIGH",
  "config": {
    "custom_setting": "value",
    "advanced_options": true
  }
}
```

## CAPTCHA Handling

When a CAPTCHA is detected:

1. **Task Status**: Changes to `CAPTCHA_DETECTED`
2. **Screenshot**: Captured for human review
3. **Logging**: Detailed detection information logged
4. **Human Intervention**: Required to mark as solved

### Solving CAPTCHAs

```bash
# Mark CAPTCHA as solved and restart task
curl -X POST http://localhost:8000/api/tasks/{task-id}/solve_captcha/ \
  -H "Authorization: Token your-token-here"
```

## Monitoring and Analytics

### Dashboard Metrics
- Total tasks and completion rates
- CAPTCHA detection statistics
- Performance metrics
- Recent activity feed

### Logging Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General information
- **WARNING**: CAPTCHA detections and minor issues
- **ERROR**: Task failures and errors
- **CRITICAL**: System-level issues

### Statistics Tracking
- Pages visited per task
- Success/failure rates
- Resource usage (memory, CPU)
- CAPTCHA detection frequency
- Average response times

## Security Considerations

### Authentication
- Token-based authentication
- User-specific task filtering
- Admin-only system operations

### Rate Limiting
- Configurable delays between requests
- Task queue management
- Resource usage monitoring

### Data Privacy
- Secure file storage
- Configurable data retention
- User data isolation

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure proper database
- [ ] Set up Redis cluster
- [ ] Configure static file serving
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up SSL/TLS
- [ ] Configure firewall rules

### Scaling Considerations
- Multiple Celery workers
- Load balancer for web servers
- Redis cluster for high availability
- Database connection pooling
- CDN for static files

## Troubleshooting

### Common Issues

1. **Chrome WebDriver Issues**:
   - Ensure Chrome is installed
   - Check ChromeDriver compatibility
   - Verify system dependencies

2. **Celery Connection Issues**:
   - Verify Redis is running
   - Check connection settings
   - Review firewall rules

3. **Database Issues**:
   - Run migrations: `python manage.py migrate`
   - Check database connectivity
   - Verify user permissions

4. **Permission Issues**:
   - Check file permissions
   - Verify media directory access
   - Review user authentication

### Debug Mode

Enable debug logging:
```python
LOGGING = {
    'loggers': {
        'runner': {
            'level': 'DEBUG',
        }
    }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

## Disclaimer

This tool is intended for legitimate automation purposes only. Users are responsible for:
- Complying with website terms of service
- Respecting robots.txt files
- Following applicable laws and regulations
- Obtaining proper permissions for data collection
- Using ethical automation practices

The developers are not responsible for misuse of this tool.
