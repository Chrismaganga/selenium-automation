"""
AI-powered content analysis and automation features
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


class AIContentAnalyzer:
    """AI-powered content analysis for web pages"""
    
    def __init__(self, driver, task):
        self.driver = driver
        self.task = task
        self.analysis_cache = {}
    
    def analyze_page_intelligence(self, url: str) -> Dict[str, Any]:
        """Comprehensive AI-powered page analysis"""
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            analysis = {
                'page_type': self._classify_page_type(soup),
                'content_quality': self._assess_content_quality(soup),
                'user_intent': self._analyze_user_intent(soup),
                'interaction_patterns': self._analyze_interaction_patterns(soup),
                'accessibility_score': self._assess_accessibility(soup),
                'seo_indicators': self._analyze_seo_indicators(soup),
                'security_indicators': self._analyze_security_indicators(soup),
                'performance_indicators': self._analyze_performance_indicators(soup),
                'recommendations': []
            }
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AI page analysis: {e}")
            return {}
    
    def _classify_page_type(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Classify the type of page using AI-like analysis"""
        page_type = {
            'primary_type': 'unknown',
            'confidence': 0.0,
            'subtypes': [],
            'indicators': []
        }
        
        # E-commerce indicators
        ecommerce_indicators = [
            'add to cart', 'buy now', 'price', 'shopping cart', 'checkout',
            'product', 'sale', 'discount', 'inventory', 'stock'
        ]
        
        # Blog/article indicators
        blog_indicators = [
            'article', 'post', 'blog', 'author', 'published', 'comments',
            'read more', 'tags', 'categories'
        ]
        
        # Landing page indicators
        landing_indicators = [
            'sign up', 'get started', 'free trial', 'download', 'learn more',
            'contact us', 'call to action', 'cta'
        ]
        
        # Form page indicators
        form_indicators = [
            'form', 'submit', 'register', 'login', 'contact', 'survey',
            'application', 'registration'
        ]
        
        # Directory/listing indicators
        directory_indicators = [
            'directory', 'listing', 'search results', 'filter', 'sort',
            'categories', 'browse', 'find'
        ]
        
        text_content = soup.get_text().lower()
        
        # Check for each type
        type_scores = {
            'ecommerce': self._calculate_indicator_score(text_content, ecommerce_indicators),
            'blog': self._calculate_indicator_score(text_content, blog_indicators),
            'landing': self._calculate_indicator_score(text_content, landing_indicators),
            'form': self._calculate_indicator_score(text_content, form_indicators),
            'directory': self._calculate_indicator_score(text_content, directory_indicators)
        }
        
        # Find the highest scoring type
        if type_scores:
            primary_type = max(type_scores, key=type_scores.get)
            confidence = type_scores[primary_type]
            
            page_type['primary_type'] = primary_type
            page_type['confidence'] = confidence
            
            # Add subtypes for high-confidence types
            if confidence > 0.3:
                for page_type_name, score in type_scores.items():
                    if score > 0.2 and page_type_name != primary_type:
                        page_type['subtypes'].append(page_type_name)
        
        return page_type
    
    def _calculate_indicator_score(self, text: str, indicators: List[str]) -> float:
        """Calculate score based on indicator presence"""
        matches = sum(1 for indicator in indicators if indicator in text)
        return matches / len(indicators) if indicators else 0.0
    
    def _assess_content_quality(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Assess the quality of page content"""
        quality = {
            'score': 0.0,
            'factors': [],
            'readability': 'unknown',
            'completeness': 0.0
        }
        
        # Get main content
        main_content = self._extract_main_content(soup)
        word_count = len(main_content.split())
        
        # Assess readability
        if word_count > 0:
            avg_word_length = sum(len(word) for word in main_content.split()) / word_count
            sentence_count = main_content.count('.') + main_content.count('!') + main_content.count('?')
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            if avg_word_length < 5 and avg_sentence_length < 20:
                quality['readability'] = 'easy'
            elif avg_word_length < 7 and avg_sentence_length < 25:
                quality['readability'] = 'medium'
            else:
                quality['readability'] = 'difficult'
        
        # Assess completeness
        completeness_factors = [
            'title' in soup.find('title').get_text() if soup.find('title') else False,
            'description' in str(soup.find('meta', attrs={'name': 'description'})),
            len(soup.find_all('h1')) > 0,
            len(soup.find_all('img')) > 0,
            word_count > 100
        ]
        
        quality['completeness'] = sum(completeness_factors) / len(completeness_factors)
        
        # Calculate overall score
        quality['score'] = (quality['completeness'] + (0.8 if quality['readability'] == 'easy' else 0.6)) / 2
        
        return quality
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '.main-content', 
            '.post-content', '.entry-content', '#content'
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text()
        
        # Fallback to body text
        return soup.get_text()
    
    def _analyze_user_intent(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze user intent based on page content"""
        intent = {
            'primary_intent': 'unknown',
            'confidence': 0.0,
            'intent_signals': []
        }
        
        text_content = soup.get_text().lower()
        
        # Define intent patterns
        intent_patterns = {
            'informational': [
                'what is', 'how to', 'guide', 'tutorial', 'learn', 'information',
                'about', 'explain', 'understand', 'help'
            ],
            'navigational': [
                'home', 'menu', 'navigation', 'browse', 'search', 'find',
                'go to', 'visit', 'explore'
            ],
            'transactional': [
                'buy', 'purchase', 'order', 'checkout', 'pay', 'download',
                'sign up', 'register', 'subscribe', 'book'
            ],
            'commercial': [
                'compare', 'price', 'cost', 'deal', 'offer', 'sale',
                'discount', 'promotion', 'best', 'top'
            ]
        }
        
        # Calculate intent scores
        intent_scores = {}
        for intent_type, patterns in intent_patterns.items():
            score = self._calculate_indicator_score(text_content, patterns)
            intent_scores[intent_type] = score
        
        # Find primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[primary_intent]
            
            intent['primary_intent'] = primary_intent
            intent['confidence'] = confidence
            
            # Add signals
            for intent_type, score in intent_scores.items():
                if score > 0.1:
                    intent['intent_signals'].append({
                        'type': intent_type,
                        'strength': score
                    })
        
        return intent
    
    def _analyze_interaction_patterns(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze interaction patterns on the page"""
        patterns = {
            'form_complexity': 'none',
            'interaction_level': 'low',
            'user_engagement_signals': [],
            'conversion_elements': []
        }
        
        # Analyze forms
        forms = soup.find_all('form')
        if forms:
            total_fields = sum(len(form.find_all(['input', 'textarea', 'select'])) for form in forms)
            if total_fields > 10:
                patterns['form_complexity'] = 'high'
            elif total_fields > 5:
                patterns['form_complexity'] = 'medium'
            else:
                patterns['form_complexity'] = 'low'
        
        # Analyze interactive elements
        interactive_elements = soup.find_all(['button', 'a', 'input', 'select', 'textarea'])
        interaction_count = len(interactive_elements)
        
        if interaction_count > 20:
            patterns['interaction_level'] = 'high'
        elif interaction_count > 10:
            patterns['interaction_level'] = 'medium'
        else:
            patterns['interaction_level'] = 'low'
        
        # Look for engagement signals
        engagement_indicators = [
            'comments', 'reviews', 'ratings', 'social', 'share',
            'like', 'follow', 'subscribe', 'newsletter'
        ]
        
        text_content = soup.get_text().lower()
        for indicator in engagement_indicators:
            if indicator in text_content:
                patterns['user_engagement_signals'].append(indicator)
        
        # Look for conversion elements
        conversion_indicators = [
            'buy now', 'add to cart', 'sign up', 'get started',
            'download', 'contact us', 'call now', 'learn more'
        ]
        
        for indicator in conversion_indicators:
            if indicator in text_content:
                patterns['conversion_elements'].append(indicator)
        
        return patterns
    
    def _assess_accessibility(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Assess page accessibility"""
        accessibility = {
            'score': 0.0,
            'issues': [],
            'improvements': []
        }
        
        issues = []
        improvements = []
        
        # Check for alt text on images
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        if images_without_alt:
            issues.append(f"{len(images_without_alt)} images without alt text")
        
        # Check for heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            issues.append("No heading structure found")
        elif not soup.find('h1'):
            issues.append("No H1 heading found")
        
        # Check for form labels
        inputs = soup.find_all('input', type=['text', 'email', 'password', 'tel', 'url'])
        inputs_without_labels = []
        for input_elem in inputs:
            input_id = input_elem.get('id')
            if input_id:
                label = soup.find('label', attrs={'for': input_id})
                if not label:
                    inputs_without_labels.append(input_id)
        
        if inputs_without_labels:
            issues.append(f"{len(inputs_without_labels)} form inputs without labels")
        
        # Check for color contrast (basic check)
        style_elements = soup.find_all(attrs={'style': True})
        if style_elements:
            improvements.append("Consider checking color contrast ratios")
        
        # Calculate score
        total_checks = 4
        passed_checks = total_checks - len(issues)
        accessibility['score'] = passed_checks / total_checks
        accessibility['issues'] = issues
        accessibility['improvements'] = improvements
        
        return accessibility
    
    def _analyze_seo_indicators(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze SEO indicators"""
        seo = {
            'score': 0.0,
            'indicators': {},
            'recommendations': []
        }
        
        indicators = {}
        
        # Title tag
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            indicators['title'] = {
                'present': True,
                'length': len(title_text),
                'optimal': 50 <= len(title_text) <= 60
            }
        else:
            indicators['title'] = {'present': False}
        
        # Meta description
        description = soup.find('meta', attrs={'name': 'description'})
        if description:
            desc_text = description.get('content', '')
            indicators['meta_description'] = {
                'present': True,
                'length': len(desc_text),
                'optimal': 150 <= len(desc_text) <= 160
            }
        else:
            indicators['meta_description'] = {'present': False}
        
        # Heading structure
        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        indicators['headings'] = {
            'h1_count': h1_count,
            'h2_count': h2_count,
            'optimal_h1': h1_count == 1,
            'has_h2': h2_count > 0
        }
        
        # Images with alt text
        images = soup.find_all('img')
        images_with_alt = len([img for img in images if img.get('alt')])
        indicators['images'] = {
            'total': len(images),
            'with_alt': images_with_alt,
            'alt_percentage': (images_with_alt / len(images)) * 100 if images else 0
        }
        
        # Internal links
        links = soup.find_all('a', href=True)
        internal_links = len([link for link in links if link['href'].startswith('/') or link['href'].startswith('http')])
        indicators['links'] = {
            'total': len(links),
            'internal': internal_links
        }
        
        # Calculate overall score
        seo['indicators'] = indicators
        
        # Basic scoring
        score_factors = [
            indicators['title']['present'],
            indicators['meta_description']['present'],
            indicators['headings']['optimal_h1'],
            indicators['headings']['has_h2'],
            indicators['images']['alt_percentage'] > 50
        ]
        
        seo['score'] = sum(score_factors) / len(score_factors)
        
        return seo
    
    def _analyze_security_indicators(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze security indicators"""
        security = {
            'score': 0.0,
            'indicators': {},
            'warnings': []
        }
        
        indicators = {}
        
        # Check for HTTPS
        current_url = self.driver.current_url
        indicators['https'] = current_url.startswith('https://')
        
        # Check for security headers (basic check)
        security_headers = ['content-security-policy', 'x-frame-options', 'x-xss-protection']
        # Note: In a real implementation, you'd check response headers
        
        # Check for mixed content
        http_resources = soup.find_all(['img', 'script', 'link'], src=True)
        http_resources.extend(soup.find_all(['img', 'script', 'link'], href=True))
        
        mixed_content = []
        for resource in http_resources:
            src = resource.get('src') or resource.get('href', '')
            if src.startswith('http://'):
                mixed_content.append(src)
        
        indicators['mixed_content'] = {
            'present': len(mixed_content) > 0,
            'count': len(mixed_content),
            'resources': mixed_content[:5]  # Limit to first 5
        }
        
        # Check for external scripts
        scripts = soup.find_all('script', src=True)
        external_scripts = [script['src'] for script in scripts if script['src'].startswith('http')]
        indicators['external_scripts'] = {
            'count': len(external_scripts),
            'sources': external_scripts[:5]
        }
        
        # Calculate score
        score_factors = [
            indicators['https'],
            not indicators['mixed_content']['present'],
            len(indicators['external_scripts']['sources']) < 10
        ]
        
        security['score'] = sum(score_factors) / len(score_factors)
        security['indicators'] = indicators
        
        return security
    
    def _analyze_performance_indicators(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze performance indicators"""
        performance = {
            'score': 0.0,
            'indicators': {},
            'recommendations': []
        }
        
        indicators = {}
        
        # Count resources
        images = soup.find_all('img')
        scripts = soup.find_all('script', src=True)
        stylesheets = soup.find_all('link', rel='stylesheet')
        
        indicators['resources'] = {
            'images': len(images),
            'scripts': len(scripts),
            'stylesheets': len(stylesheets),
            'total': len(images) + len(scripts) + len(stylesheets)
        }
        
        # Check for large images (basic check)
        large_images = []
        for img in images:
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    if int(width) > 1000 or int(height) > 1000:
                        large_images.append(f"{width}x{height}")
                except ValueError:
                    pass
        
        indicators['large_images'] = {
            'count': len(large_images),
            'sizes': large_images[:5]
        }
        
        # Check for inline styles
        inline_styles = soup.find_all(attrs={'style': True})
        indicators['inline_styles'] = len(inline_styles)
        
        # Check for external resources
        external_resources = []
        for tag in soup.find_all(['img', 'script', 'link'], src=True):
            src = tag.get('src')
            if src and src.startswith('http'):
                external_resources.append(src)
        
        indicators['external_resources'] = {
            'count': len(external_resources),
            'sources': external_resources[:5]
        }
        
        # Calculate score
        score_factors = [
            indicators['resources']['total'] < 50,
            indicators['large_images']['count'] < 5,
            indicators['inline_styles'] < 20,
            indicators['external_resources']['count'] < 20
        ]
        
        performance['score'] = sum(score_factors) / len(score_factors)
        performance['indicators'] = indicators
        
        return performance
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Content quality recommendations
        content_quality = analysis.get('content_quality', {})
        if content_quality.get('readability') == 'difficult':
            recommendations.append("Consider simplifying content for better readability")
        
        if content_quality.get('completeness', 0) < 0.5:
            recommendations.append("Add more comprehensive content to improve page value")
        
        # SEO recommendations
        seo = analysis.get('seo_indicators', {})
        if not seo.get('indicators', {}).get('title', {}).get('present'):
            recommendations.append("Add a title tag for better SEO")
        
        if not seo.get('indicators', {}).get('meta_description', {}).get('present'):
            recommendations.append("Add a meta description for better search visibility")
        
        # Accessibility recommendations
        accessibility = analysis.get('accessibility', {})
        if accessibility.get('score', 0) < 0.7:
            recommendations.append("Improve accessibility by adding alt text to images and proper heading structure")
        
        # Performance recommendations
        performance = analysis.get('performance_indicators', {})
        if performance.get('indicators', {}).get('large_images', {}).get('count', 0) > 3:
            recommendations.append("Optimize large images to improve page load speed")
        
        return recommendations
