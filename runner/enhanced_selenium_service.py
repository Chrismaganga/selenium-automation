"""
Enhanced Selenium automation service with advanced features
"""
import io
import time
import json
import logging
import psutil
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

from .models import AutomationTask, PageEvent, CaptchaEvent, AutomationLog, AutomationStats
from .data_extractors import DataExtractionManager
from .captcha_detector import AdvancedCaptchaDetector
from .ai_analyzer import AIContentAnalyzer
from .monitoring import alert_manager, performance_monitor, real_time_monitor

logger = logging.getLogger(__name__)


class EnhancedSeleniumAutomationService:
    """Enhanced Selenium automation service with advanced features"""
    
    def __init__(self, task: AutomationTask):
        self.task = task
        self.driver = None
        self.stats = {
            'start_time': time.time(),
            'pages_visited': 0,
            'errors': 0,
            'captcha_detections': 0,
            'memory_peak': 0,
            'cpu_peak': 0,
            'data_extracted': 0,
            'ai_analysis_count': 0
        }
        
        # Initialize advanced components
        self.data_extractor = None
        self.captcha_detector = None
        self.ai_analyzer = None
        
    def _log(self, level: str, message: str, **kwargs):
        """Enhanced logging with metadata"""
        AutomationLog.objects.create(
            task=self.task,
            level=level,
            message=message,
            module=kwargs.get('module', ''),
            function=kwargs.get('function', ''),
            line_number=kwargs.get('line_number', None),
            metadata=kwargs.get('metadata', {})
        )
        getattr(logger, level.lower(), logger.info)(message)
    
    def _update_stats(self):
        """Update resource usage statistics"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            self.stats['memory_peak'] = max(self.stats['memory_peak'], memory_mb)
            self.stats['cpu_peak'] = max(self.stats['cpu_peak'], cpu_percent)
        except Exception as e:
            self._log('WARNING', f"Failed to update stats: {e}")
    
    def _build_driver(self) -> webdriver.Chrome:
        """Build and configure Chrome WebDriver with advanced options"""
        try:
            options = Options()
            
            # Basic options
            if self.task.headless:
                options.add_argument("--headless=new")
            
            # Performance and stability
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            
            # Advanced automation options
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Window size
            if self.task.window_size:
                options.add_argument(f"--window-size={self.task.window_size}")
            
            # User agent
            if self.task.user_agent:
                options.add_argument(f"--user-agent={self.task.user_agent}")
            else:
                options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Enable performance logging
            options.add_argument("--enable-logging")
            options.add_argument("--log-level=0")
            
            # Set up capabilities
            caps = webdriver.DesiredCapabilities.CHROME.copy()
            caps["goog:loggingPrefs"] = {
                "performance": "ALL",
                "browser": "ALL"
            }
            
            # Create driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(
                service=service,
                options=options,
                desired_capabilities=caps
            )
            
            # Set timeouts
            driver.set_page_load_timeout(self.task.timeout)
            driver.implicitly_wait(10)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self._log('INFO', f"Enhanced Chrome driver initialized successfully")
            return driver
            
        except Exception as e:
            self._log('ERROR', f"Failed to initialize Chrome driver: {e}")
            raise
    
    def _save_screenshot(self, note: str = "") -> Optional[str]:
        """Save screenshot with enhanced metadata"""
        try:
            if not self.driver:
                return None
                
            png_data = self.driver.get_screenshot_as_png()
            img = Image.open(io.BytesIO(png_data))
            
            # Create filename with timestamp
            timestamp = int(time.time() * 1000)
            filename = f"task_{self.task.id}_{timestamp}.png"
            
            # Save to media directory
            media_path = Path(settings.MEDIA_ROOT) / "screenshots"
            media_path.mkdir(parents=True, exist_ok=True)
            file_path = media_path / filename
            
            img.save(file_path, 'PNG')
            
            # Return relative path for database
            return f"screenshots/{filename}"
            
        except Exception as e:
            self._log('ERROR', f"Failed to save screenshot: {e}")
            return None
    
    def _save_html(self) -> Optional[str]:
        """Save HTML content with enhanced processing"""
        try:
            if not self.driver:
                return None
                
            html_content = self.driver.page_source
            
            # Create filename with timestamp
            timestamp = int(time.time() * 1000)
            filename = f"task_{self.task.id}_{timestamp}.html"
            
            # Save to media directory
            media_path = Path(settings.MEDIA_ROOT) / "html"
            media_path.mkdir(parents=True, exist_ok=True)
            file_path = media_path / filename
            
            file_path.write_text(html_content, encoding='utf-8')
            
            # Return relative path for database
            return f"html/{filename}"
            
        except Exception as e:
            self._log('ERROR', f"Failed to save HTML: {e}")
            return None
    
    def _handle_captcha_detection(self, page_event: PageEvent) -> bool:
        """Enhanced CAPTCHA detection and handling"""
        try:
            if not self.captcha_detector:
                self.captcha_detector = AdvancedCaptchaDetector(self.driver)
            
            captcha_info = self.captcha_detector.detect_captcha()
            if not captcha_info or not captcha_info.get('detected'):
                return False
            
            # Create CAPTCHA event with enhanced details
            captcha_event = CaptchaEvent.objects.create(
                task=self.task,
                page_event=page_event,
                captcha_type=captcha_info['type'],
                status='DETECTED',
                screenshot=page_event.screenshot,
                notes=f"Confidence: {captcha_info['confidence']:.2f}",
                metadata={
                    'detection_details': captcha_info['details'],
                    'location': captcha_info['location'],
                    'recommendations': captcha_info['recommendations']
                }
            )
            
            self.stats['captcha_detections'] += 1
            self._log('WARNING', f"CAPTCHA detected: {captcha_info['type']} (confidence: {captcha_info['confidence']:.2f})")
            
            # Update task status
            self.task.status = 'CAPTCHA_DETECTED'
            self.task.finished_at = timezone.now()
            self.task.save(update_fields=['status', 'finished_at'])
            
            # Send alert
            alert_manager.send_alert(
                self.task,
                f"CAPTCHA detected: {captcha_info['type']}",
                'warning'
            )
            
            return True
            
        except Exception as e:
            self._log('ERROR', f"Failed to handle CAPTCHA detection: {e}")
            return False
    
    def _extract_data(self, url: str) -> Dict[str, Any]:
        """Extract data using advanced extractors"""
        try:
            if not self.data_extractor:
                self.data_extractor = DataExtractionManager(self.driver, self.task)
            
            extracted_data = self.data_extractor.extract_all(url)
            self.stats['data_extracted'] += 1
            
            self._log('INFO', f"Data extraction completed for {url}")
            return extracted_data
            
        except Exception as e:
            self._log('ERROR', f"Data extraction failed for {url}: {e}")
            return {}
    
    def _analyze_content(self, url: str) -> Dict[str, Any]:
        """Analyze content using AI-powered analyzer"""
        try:
            if not self.ai_analyzer:
                self.ai_analyzer = AIContentAnalyzer(self.driver, self.task)
            
            analysis = self.ai_analyzer.analyze_page_intelligence(url)
            self.stats['ai_analysis_count'] += 1
            
            self._log('INFO', f"AI content analysis completed for {url}")
            return analysis
            
        except Exception as e:
            self._log('ERROR', f"AI content analysis failed for {url}: {e}")
            return {}
    
    def _create_enhanced_page_event(self, event_type: str, url: str, **kwargs) -> PageEvent:
        """Create enhanced page event with additional data"""
        try:
            screenshot_path = self._save_screenshot(kwargs.get('note', ''))
            html_path = self._save_html()
            
            # Extract additional metadata
            metadata = kwargs.get('metadata', {})
            
            # Add extracted data if available
            if 'extracted_data' in kwargs:
                metadata['extracted_data'] = kwargs['extracted_data']
            
            # Add AI analysis if available
            if 'ai_analysis' in kwargs:
                metadata['ai_analysis'] = kwargs['ai_analysis']
            
            page_event = PageEvent.objects.create(
                task=self.task,
                event_type=event_type,
                url=url,
                title=self.driver.title if self.driver else '',
                status_code=kwargs.get('status_code'),
                load_time=kwargs.get('load_time'),
                screenshot=screenshot_path,
                html_content=html_path,
                note=kwargs.get('note', ''),
                metadata=metadata
            )
            
            return page_event
            
        except Exception as e:
            self._log('ERROR', f"Failed to create enhanced page event: {e}")
            return None
    
    def _extract_links(self, current_url: str) -> List[str]:
        """Extract links with enhanced filtering"""
        try:
            if not self.driver:
                return []
            
            links = []
            current_domain = urlparse(current_url).netloc
            
            # Find all links
            link_elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for element in link_elements:
                try:
                    href = element.get_attribute("href")
                    if href:
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(current_url, href)
                        parsed_url = urlparse(absolute_url)
                        
                        # Enhanced filtering
                        if self._should_follow_link(absolute_url, parsed_url, current_domain):
                            links.append(absolute_url)
                            
                except StaleElementReferenceException:
                    continue
                except Exception:
                    continue
            
            # Remove duplicates and limit
            unique_links = list(set(links))[:50]
            return unique_links
            
        except Exception as e:
            self._log('ERROR', f"Failed to extract links: {e}")
            return []
    
    def _should_follow_link(self, url: str, parsed_url, current_domain: str) -> bool:
        """Determine if a link should be followed"""
        # Same domain only
        if parsed_url.netloc != current_domain:
            return False
        
        # Skip certain file types
        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip certain URL patterns
        skip_patterns = ['#', 'javascript:', 'mailto:', 'tel:']
        if any(pattern in url.lower() for pattern in skip_patterns):
            return False
        
        return True
    
    def run_enhanced_automation(self):
        """Main enhanced automation execution method"""
        try:
            self._log('INFO', f"Starting enhanced automation for task {self.task.id}")
            
            # Start monitoring
            real_time_monitor.start_monitoring(self.task)
            
            # Update task status
            self.task.status = 'RUNNING'
            self.task.started_at = timezone.now()
            self.task.save(update_fields=['status', 'started_at'])
            
            # Initialize driver
            self.driver = self._build_driver()
            
            # Initialize advanced components
            self.data_extractor = DataExtractionManager(self.driver, self.task)
            self.captcha_detector = AdvancedCaptchaDetector(self.driver)
            self.ai_analyzer = AIContentAnalyzer(self.driver, self.task)
            
            # URLs to visit
            urls_to_visit = [self.task.start_url]
            visited_urls = set()
            
            while urls_to_visit and self.stats['pages_visited'] < self.task.max_pages:
                try:
                    # Get next URL
                    current_url = urls_to_visit.pop(0)
                    
                    if current_url in visited_urls:
                        continue
                    
                    visited_urls.add(current_url)
                    self._log('INFO', f"Visiting: {current_url}")
                    
                    # Navigate to URL
                    start_time = time.time()
                    self.driver.get(current_url)
                    load_time = time.time() - start_time
                    
                    # Wait for page to load
                    time.sleep(self.task.delay_between_requests)
                    
                    # Update stats
                    self.stats['pages_visited'] += 1
                    self._update_stats()
                    
                    # Extract data
                    extracted_data = self._extract_data(current_url)
                    
                    # Analyze content
                    ai_analysis = self._analyze_content(current_url)
                    
                    # Create enhanced page event
                    page_event = self._create_enhanced_page_event(
                        event_type='PAGE_LOAD',
                        url=current_url,
                        load_time=load_time,
                        note=f"Page {self.stats['pages_visited']}",
                        extracted_data=extracted_data,
                        ai_analysis=ai_analysis
                    )
                    
                    if not page_event:
                        self.stats['errors'] += 1
                        continue
                    
                    # Check for CAPTCHA
                    if self._handle_captcha_detection(page_event):
                        self._log('WARNING', "CAPTCHA detected - stopping automation")
                        break
                    
                    # Extract more links if we haven't reached max pages
                    if self.stats['pages_visited'] < self.task.max_pages:
                        new_links = self._extract_links(current_url)
                        for link in new_links:
                            if link not in visited_urls and len(urls_to_visit) < 100:
                                urls_to_visit.append(link)
                    
                    # Update monitoring
                    real_time_monitor.update_task_status(self.task)
                    
                    # Check performance
                    stats, created = AutomationStats.objects.get_or_create(task=self.task)
                    performance_alerts = performance_monitor.check_performance(self.task, stats)
                    if performance_alerts:
                        for alert in performance_alerts:
                            alert_manager.send_alert(self.task, alert, 'warning')
                    
                    # Small delay between requests
                    time.sleep(self.task.delay_between_requests)
                    
                except TimeoutException:
                    self._log('WARNING', f"Timeout loading {current_url}")
                    self.stats['errors'] += 1
                    continue
                    
                except WebDriverException as e:
                    self._log('ERROR', f"WebDriver error on {current_url}: {e}")
                    self.stats['errors'] += 1
                    continue
                    
                except Exception as e:
                    self._log('ERROR', f"Unexpected error on {current_url}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            # Update final task status
            if self.task.status != 'CAPTCHA_DETECTED':
                self.task.status = 'COMPLETED'
                self.task.finished_at = timezone.now()
            
            self.task.total_pages_visited = self.stats['pages_visited']
            self.task.total_errors = self.stats['errors']
            self.task.save(update_fields=['status', 'finished_at', 'total_pages_visited', 'total_errors'])
            
            # Update or create stats
            stats, created = AutomationStats.objects.get_or_create(task=self.task)
            stats.total_requests = self.stats['pages_visited']
            stats.successful_requests = self.stats['pages_visited'] - self.stats['errors']
            stats.failed_requests = self.stats['errors']
            stats.captcha_detections = self.stats['captcha_detections']
            stats.memory_peak = self.stats['memory_peak']
            stats.cpu_usage_peak = self.stats['cpu_peak']
            stats.total_screenshots = self.stats['pages_visited']
            stats.total_html_pages = self.stats['pages_visited']
            stats.save()
            
            # Check all monitoring rules
            alert_manager.check_all_rules(self.task, stats)
            
            # Stop monitoring
            real_time_monitor.stop_monitoring(str(self.task.id))
            
            self._log('INFO', f"Enhanced automation completed. Pages visited: {self.stats['pages_visited']}, Errors: {self.stats['errors']}")
            
        except Exception as e:
            self._log('ERROR', f"Enhanced automation failed: {e}")
            self.task.status = 'FAILED'
            self.task.error_message = str(e)
            self.task.finished_at = timezone.now()
            self.task.save(update_fields=['status', 'error_message', 'finished_at'])
            
            # Stop monitoring
            real_time_monitor.stop_monitoring(str(self.task.id))
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self._log('INFO', "Enhanced WebDriver closed")
                except Exception as e:
                    self._log('ERROR', f"Error closing WebDriver: {e}")


def run_enhanced_automation_task(task_id: str):
    """Entry point for running enhanced automation tasks"""
    try:
        task = AutomationTask.objects.get(id=task_id)
        service = EnhancedSeleniumAutomationService(task)
        service.run_enhanced_automation()
    except AutomationTask.DoesNotExist:
        logger.error(f"Task {task_id} not found")
    except Exception as e:
        logger.error(f"Failed to run enhanced task {task_id}: {e}")
