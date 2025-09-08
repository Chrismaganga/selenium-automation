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

logger = logging.getLogger(__name__)


class SeleniumAutomationService:
    """Comprehensive Selenium automation service with CAPTCHA detection"""
    
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
        }
        
    def _log(self, level: str, message: str, **kwargs):
        """Log message to database and console"""
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
        """Build and configure Chrome WebDriver"""
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
            options.add_argument("--disable-images")  # Speed up loading
            options.add_argument("--disable-javascript")  # Optional: disable JS for faster loading
            
            # Window size
            if self.task.window_size:
                options.add_argument(f"--window-size={self.task.window_size}")
            
            # User agent
            if self.task.user_agent:
                options.add_argument(f"--user-agent={self.task.user_agent}")
            else:
                # Default modern user agent
                options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Additional options for better automation
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
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
            
            self._log('INFO', f"Chrome driver initialized successfully")
            return driver
            
        except Exception as e:
            self._log('ERROR', f"Failed to initialize Chrome driver: {e}")
            raise
    
    def _save_screenshot(self, note: str = "") -> Optional[str]:
        """Save screenshot and return relative path"""
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
        """Save HTML content and return relative path"""
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
    
    def _detect_captcha(self) -> Optional[Dict[str, Any]]:
        """
        Detect various types of CAPTCHAs without attempting to bypass them
        Returns captcha info if detected, None otherwise
        """
        try:
            if not self.driver:
                return None
            
            captcha_info = {
                'type': 'UNKNOWN',
                'confidence': 0.0,
                'selectors_found': [],
                'iframes_found': []
            }
            
            # Check for reCAPTCHA v2
            recaptcha_selectors = [
                '.g-recaptcha',
                '#g-recaptcha',
                '.g-recaptcha-response',
                '[data-sitekey]',
                'iframe[src*="google.com/recaptcha"]',
                'iframe[src*="gstatic.com/recaptcha"]'
            ]
            
            for selector in recaptcha_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        captcha_info['selectors_found'].append(selector)
                        captcha_info['type'] = 'RECAPTCHA_V2'
                        captcha_info['confidence'] += 0.3
                except Exception:
                    continue
            
            # Check for reCAPTCHA v3
            recaptcha_v3_selectors = [
                'script[src*="recaptcha/releases"]',
                'script[src*="recaptcha/api.js"]',
                '[data-callback*="recaptcha"]'
            ]
            
            for selector in recaptcha_v3_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        captcha_info['selectors_found'].append(selector)
                        if captcha_info['type'] == 'UNKNOWN':
                            captcha_info['type'] = 'RECAPTCHA_V3'
                        captcha_info['confidence'] += 0.2
                except Exception:
                    continue
            
            # Check for hCaptcha
            hcaptcha_selectors = [
                '.h-captcha',
                '#h-captcha',
                '[data-hcaptcha-response]',
                'iframe[src*="hcaptcha.com"]',
                'div[role="presentation"][data-hcaptcha-response]'
            ]
            
            for selector in hcaptcha_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        captcha_info['selectors_found'].append(selector)
                        captcha_info['type'] = 'HCAPTCHA'
                        captcha_info['confidence'] += 0.3
                except Exception:
                    continue
            
            # Check for iframes that might contain CAPTCHAs
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    src = iframe.get_attribute("src") or ""
                    if any(domain in src for domain in [
                        "google.com/recaptcha", "gstatic.com/recaptcha", 
                        "hcaptcha.com", "captcha"
                    ]):
                        captcha_info['iframes_found'].append(src)
                        captcha_info['confidence'] += 0.2
            except Exception:
                pass
            
            # Check for common CAPTCHA text patterns
            captcha_text_patterns = [
                "captcha", "verify you are human", "prove you are not a robot",
                "security check", "verification", "challenge"
            ]
            
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                for pattern in captcha_text_patterns:
                    if pattern in page_text:
                        captcha_info['confidence'] += 0.1
            except Exception:
                pass
            
            # Only return if confidence is above threshold
            if captcha_info['confidence'] >= 0.3:
                return captcha_info
            
            return None
            
        except Exception as e:
            self._log('ERROR', f"Error detecting CAPTCHA: {e}")
            return None
    
    def _create_page_event(self, event_type: str, url: str, **kwargs) -> PageEvent:
        """Create a page event record"""
        try:
            screenshot_path = self._save_screenshot(kwargs.get('note', ''))
            html_path = self._save_html()
            
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
                metadata=kwargs.get('metadata', {})
            )
            
            return page_event
            
        except Exception as e:
            self._log('ERROR', f"Failed to create page event: {e}")
            return None
    
    def _handle_captcha_detection(self, page_event: PageEvent) -> bool:
        """Handle CAPTCHA detection - halt execution and notify"""
        try:
            captcha_info = self._detect_captcha()
            if not captcha_info:
                return False
            
            # Create CAPTCHA event
            captcha_event = CaptchaEvent.objects.create(
                task=self.task,
                page_event=page_event,
                captcha_type=captcha_info['type'],
                status='DETECTED',
                screenshot=page_event.screenshot,
                notes=f"Confidence: {captcha_info['confidence']:.2f}",
                metadata=captcha_info
            )
            
            self.stats['captcha_detections'] += 1
            self._log('WARNING', f"CAPTCHA detected: {captcha_info['type']} (confidence: {captcha_info['confidence']:.2f})")
            
            # Update task status
            self.task.status = 'CAPTCHA_DETECTED'
            self.task.finished_at = timezone.now()
            self.task.save(update_fields=['status', 'finished_at'])
            
            return True
            
        except Exception as e:
            self._log('ERROR', f"Failed to handle CAPTCHA detection: {e}")
            return False
    
    def _extract_links(self, current_url: str) -> List[str]:
        """Extract links from current page for further crawling"""
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
                        
                        # Only include same-domain links
                        if parsed_url.netloc == current_domain:
                            links.append(absolute_url)
                            
                except StaleElementReferenceException:
                    continue
                except Exception:
                    continue
            
            # Remove duplicates and limit
            unique_links = list(set(links))[:50]  # Limit to 50 links
            return unique_links
            
        except Exception as e:
            self._log('ERROR', f"Failed to extract links: {e}")
            return []
    
    def run_automation(self):
        """Main automation execution method"""
        try:
            self._log('INFO', f"Starting automation for task {self.task.id}")
            
            # Update task status
            self.task.status = 'RUNNING'
            self.task.started_at = timezone.now()
            self.task.save(update_fields=['status', 'started_at'])
            
            # Initialize driver
            self.driver = self._build_driver()
            
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
                    
                    # Create page event
                    page_event = self._create_page_event(
                        event_type='PAGE_LOAD',
                        url=current_url,
                        load_time=load_time,
                        note=f"Page {self.stats['pages_visited']}"
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
                            if link not in visited_urls and len(urls_to_visit) < 100:  # Limit queue size
                                urls_to_visit.append(link)
                    
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
            
            self._log('INFO', f"Automation completed. Pages visited: {self.stats['pages_visited']}, Errors: {self.stats['errors']}")
            
        except Exception as e:
            self._log('ERROR', f"Automation failed: {e}")
            self.task.status = 'FAILED'
            self.task.error_message = str(e)
            self.task.finished_at = timezone.now()
            self.task.save(update_fields=['status', 'error_message', 'finished_at'])
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self._log('INFO', "WebDriver closed")
                except Exception as e:
                    self._log('ERROR', f"Error closing WebDriver: {e}")


def run_automation_task(task_id: str):
    """Entry point for running automation tasks"""
    try:
        task = AutomationTask.objects.get(id=task_id)
        service = SeleniumAutomationService(task)
        service.run_automation()
    except AutomationTask.DoesNotExist:
        logger.error(f"Task {task_id} not found")
    except Exception as e:
        logger.error(f"Failed to run task {task_id}: {e}")
