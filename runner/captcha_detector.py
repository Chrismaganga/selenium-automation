"""
Advanced CAPTCHA detection and handling system
"""
import re
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class AdvancedCaptchaDetector:
    """Advanced CAPTCHA detection system"""
    
    def __init__(self, driver):
        self.driver = driver
        self.detection_patterns = self._load_detection_patterns()
        self.confidence_threshold = 0.7
    
    def _load_detection_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive CAPTCHA detection patterns"""
        return {
            'recaptcha_v2': {
                'selectors': [
                    '.g-recaptcha',
                    '#g-recaptcha',
                    '.g-recaptcha-response',
                    '[data-sitekey]',
                    'iframe[src*="google.com/recaptcha"]',
                    'iframe[src*="gstatic.com/recaptcha"]',
                    'div[class*="recaptcha"]',
                    'div[id*="recaptcha"]'
                ],
                'text_patterns': [
                    r'verify\s+you\s+are\s+not\s+a\s+robot',
                    r'i\'m\s+not\s+a\s+robot',
                    r'prove\s+you\s+are\s+human',
                    r'security\s+check',
                    r'captcha'
                ],
                'iframe_patterns': [
                    r'google\.com/recaptcha',
                    r'gstatic\.com/recaptcha'
                ],
                'weight': 1.0
            },
            'recaptcha_v3': {
                'selectors': [
                    'script[src*="recaptcha/releases"]',
                    'script[src*="recaptcha/api.js"]',
                    '[data-callback*="recaptcha"]',
                    'script[src*="recaptcha"]'
                ],
                'text_patterns': [
                    r'grecaptcha',
                    r'recaptcha'
                ],
                'iframe_patterns': [],
                'weight': 0.8
            },
            'hcaptcha': {
                'selectors': [
                    '.h-captcha',
                    '#h-captcha',
                    '[data-hcaptcha-response]',
                    'iframe[src*="hcaptcha.com"]',
                    'div[role="presentation"][data-hcaptcha-response]',
                    'div[class*="hcaptcha"]'
                ],
                'text_patterns': [
                    r'hcaptcha',
                    r'verify\s+you\s+are\s+human',
                    r'security\s+check'
                ],
                'iframe_patterns': [
                    r'hcaptcha\.com'
                ],
                'weight': 1.0
            },
            'funcaptcha': {
                'selectors': [
                    '.funcaptcha',
                    '#funcaptcha',
                    'iframe[src*="funcaptcha.com"]',
                    'div[class*="funcaptcha"]'
                ],
                'text_patterns': [
                    r'funcaptcha',
                    r'arkose\s+labs'
                ],
                'iframe_patterns': [
                    r'funcaptcha\.com',
                    r'arkoselabs\.com'
                ],
                'weight': 0.9
            },
            'cloudflare': {
                'selectors': [
                    '.cf-challenge',
                    '#cf-challenge',
                    'iframe[src*="cloudflare.com"]',
                    'div[class*="cf-"]'
                ],
                'text_patterns': [
                    r'checking\s+your\s+browser',
                    r'cloudflare',
                    r'security\s+check',
                    r'please\s+wait'
                ],
                'iframe_patterns': [
                    r'cloudflare\.com'
                ],
                'weight': 0.9
            },
            'generic_captcha': {
                'selectors': [
                    '[class*="captcha"]',
                    '[id*="captcha"]',
                    'input[name*="captcha"]',
                    'img[src*="captcha"]',
                    'canvas[id*="captcha"]'
                ],
                'text_patterns': [
                    r'captcha',
                    r'verification\s+code',
                    r'enter\s+the\s+code',
                    r'type\s+the\s+characters',
                    r'security\s+code'
                ],
                'iframe_patterns': [],
                'weight': 0.7
            }
        }
    
    def detect_captcha(self) -> Dict[str, Any]:
        """Comprehensive CAPTCHA detection"""
        detection_result = {
            'detected': False,
            'type': 'unknown',
            'confidence': 0.0,
            'details': {},
            'location': {},
            'recommendations': []
        }
        
        try:
            # Check each CAPTCHA type
            for captcha_type, patterns in self.detection_patterns.items():
                confidence = self._calculate_confidence(captcha_type, patterns)
                
                if confidence > detection_result['confidence']:
                    detection_result['confidence'] = confidence
                    detection_result['type'] = captcha_type
                    detection_result['detected'] = confidence >= self.confidence_threshold
            
            if detection_result['detected']:
                detection_result['details'] = self._get_detection_details(detection_result['type'])
                detection_result['location'] = self._get_captcha_location()
                detection_result['recommendations'] = self._get_recommendations(detection_result['type'])
            
            return detection_result
            
        except Exception as e:
            logger.error(f"Error in CAPTCHA detection: {e}")
            return detection_result
    
    def _calculate_confidence(self, captcha_type: str, patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for a specific CAPTCHA type"""
        confidence = 0.0
        weight = patterns.get('weight', 1.0)
        
        # Check selectors
        selector_matches = 0
        for selector in patterns.get('selectors', []):
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    selector_matches += 1
            except Exception:
                continue
        
        if selector_matches > 0:
            confidence += (selector_matches / len(patterns.get('selectors', []))) * 0.4
        
        # Check text patterns
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        text_matches = 0
        for pattern in patterns.get('text_patterns', []):
            if re.search(pattern, page_text, re.IGNORECASE):
                text_matches += 1
        
        if text_matches > 0:
            confidence += (text_matches / len(patterns.get('text_patterns', []))) * 0.3
        
        # Check iframe patterns
        iframe_matches = 0
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            for pattern in patterns.get('iframe_patterns', []):
                if re.search(pattern, src, re.IGNORECASE):
                    iframe_matches += 1
                    break
        
        if iframe_matches > 0:
            confidence += (iframe_matches / len(patterns.get('iframe_patterns', []))) * 0.3
        
        return confidence * weight
    
    def _get_detection_details(self, captcha_type: str) -> Dict[str, Any]:
        """Get detailed information about detected CAPTCHA"""
        details = {
            'type': captcha_type,
            'elements_found': [],
            'iframes_found': [],
            'text_matches': []
        }
        
        patterns = self.detection_patterns.get(captcha_type, {})
        
        # Find matching elements
        for selector in patterns.get('selectors', []):
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    details['elements_found'].append({
                        'selector': selector,
                        'tag': element.tag_name,
                        'class': element.get_attribute('class'),
                        'id': element.get_attribute('id'),
                        'visible': element.is_displayed()
                    })
            except Exception:
                continue
        
        # Find matching iframes
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            for pattern in patterns.get('iframe_patterns', []):
                if re.search(pattern, src, re.IGNORECASE):
                    details['iframes_found'].append({
                        'src': src,
                        'pattern': pattern,
                        'visible': iframe.is_displayed()
                    })
                    break
        
        # Find text matches
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        for pattern in patterns.get('text_patterns', []):
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                details['text_matches'].extend(matches)
        
        return details
    
    def _get_captcha_location(self) -> Dict[str, Any]:
        """Get the location of the CAPTCHA on the page"""
        location = {
            'viewport_visible': False,
            'coordinates': None,
            'size': None,
            'z_index': None
        }
        
        try:
            # Find the most likely CAPTCHA element
            captcha_element = None
            for captcha_type, patterns in self.detection_patterns.items():
                for selector in patterns.get('selectors', []):
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                captcha_element = element
                                break
                        if captcha_element:
                            break
                    except Exception:
                        continue
                if captcha_element:
                    break
            
            if captcha_element:
                location['viewport_visible'] = captcha_element.is_displayed()
                location['coordinates'] = {
                    'x': captcha_element.location['x'],
                    'y': captcha_element.location['y']
                }
                location['size'] = {
                    'width': captcha_element.size['width'],
                    'height': captcha_element.size['height']
                }
                location['z_index'] = captcha_element.value_of_css_property('z-index')
        
        except Exception as e:
            logger.error(f"Error getting CAPTCHA location: {e}")
        
        return location
    
    def _get_recommendations(self, captcha_type: str) -> List[str]:
        """Get recommendations for handling the detected CAPTCHA"""
        recommendations = {
            'recaptcha_v2': [
                "Human intervention required - reCAPTCHA v2 detected",
                "Consider using reCAPTCHA test keys for development",
                "Implement proper error handling for CAPTCHA challenges",
                "Add user notification about CAPTCHA requirement"
            ],
            'recaptcha_v3': [
                "reCAPTCHA v3 detected - may require score analysis",
                "Consider implementing score-based handling",
                "Monitor for CAPTCHA challenges in form submissions",
                "Implement fallback for low scores"
            ],
            'hcaptcha': [
                "hCaptcha detected - human intervention required",
                "Consider hCaptcha test keys for development",
                "Implement proper error handling",
                "Add user notification about CAPTCHA requirement"
            ],
            'funcaptcha': [
                "FunCaptcha/Arkose Labs detected",
                "Human intervention required",
                "Consider alternative authentication methods",
                "Implement proper error handling"
            ],
            'cloudflare': [
                "Cloudflare challenge detected",
                "Wait for challenge to complete automatically",
                "Implement retry logic with delays",
                "Consider using residential proxies"
            ],
            'generic_captcha': [
                "Generic CAPTCHA detected",
                "Human intervention required",
                "Implement CAPTCHA solving service integration",
                "Add proper error handling and user notification"
            ]
        }
        
        return recommendations.get(captcha_type, [
            "Unknown CAPTCHA type detected",
            "Human intervention required",
            "Implement proper error handling"
        ])
    
    def wait_for_captcha_completion(self, timeout: int = 30) -> bool:
        """Wait for CAPTCHA to be completed automatically (for some types)"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if CAPTCHA is still present
                detection = self.detect_captcha()
                if not detection['detected']:
                    logger.info("CAPTCHA appears to have been completed")
                    return True
                
                # For Cloudflare, wait a bit longer
                if detection['type'] == 'cloudflare':
                    time.sleep(2)
                else:
                    time.sleep(1)
            
            logger.warning(f"CAPTCHA still present after {timeout} seconds")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for CAPTCHA completion: {e}")
            return False
    
    def get_captcha_screenshot(self) -> Optional[bytes]:
        """Get screenshot of CAPTCHA area"""
        try:
            # Find CAPTCHA element
            captcha_element = None
            for captcha_type, patterns in self.detection_patterns.items():
                for selector in patterns.get('selectors', []):
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                captcha_element = element
                                break
                        if captcha_element:
                            break
                    except Exception:
                        continue
                if captcha_element:
                    break
            
            if captcha_element:
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView(true);", captcha_element)
                time.sleep(1)
                
                # Take screenshot of element
                return captcha_element.screenshot_as_png
            else:
                # Take full page screenshot
                return self.driver.get_screenshot_as_png()
                
        except Exception as e:
            logger.error(f"Error taking CAPTCHA screenshot: {e}")
            return None
    
    def analyze_captcha_complexity(self, detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the complexity of the detected CAPTCHA"""
        complexity = {
            'level': 'unknown',
            'factors': [],
            'estimated_solve_time': 0,
            'human_required': True
        }
        
        captcha_type = detection_result.get('type', 'unknown')
        details = detection_result.get('details', {})
        
        # Analyze based on type
        if captcha_type == 'recaptcha_v2':
            complexity['level'] = 'high'
            complexity['factors'].append('Image recognition required')
            complexity['factors'].append('Multiple challenges possible')
            complexity['estimated_solve_time'] = 30  # seconds
        elif captcha_type == 'recaptcha_v3':
            complexity['level'] = 'low'
            complexity['factors'].append('Background verification')
            complexity['factors'].append('Score-based analysis')
            complexity['estimated_solve_time'] = 5
            complexity['human_required'] = False
        elif captcha_type == 'hcaptcha':
            complexity['level'] = 'high'
            complexity['factors'].append('Image recognition required')
            complexity['factors'].append('Multiple selection tasks')
            complexity['estimated_solve_time'] = 45
        elif captcha_type == 'cloudflare':
            complexity['level'] = 'medium'
            complexity['factors'].append('JavaScript challenge')
            complexity['factors'].append('May resolve automatically')
            complexity['estimated_solve_time'] = 10
            complexity['human_required'] = False
        else:
            complexity['level'] = 'medium'
            complexity['factors'].append('Text recognition required')
            complexity['estimated_solve_time'] = 20
        
        # Analyze element visibility and positioning
        location = detection_result.get('location', {})
        if location.get('viewport_visible'):
            complexity['factors'].append('Visible in viewport')
        else:
            complexity['factors'].append('Not visible in viewport')
            complexity['estimated_solve_time'] += 10
        
        return complexity
