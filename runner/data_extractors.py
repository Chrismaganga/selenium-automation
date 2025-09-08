"""
Advanced data extraction modules for web automation
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class DataExtractor:
    """Base class for data extraction"""
    
    def __init__(self, driver, task):
        self.driver = driver
        self.task = task
        self.extracted_data = {}
    
    def extract(self, url: str) -> Dict[str, Any]:
        """Main extraction method to be overridden"""
        raise NotImplementedError


class ContactInfoExtractor(DataExtractor):
    """Extract contact information from web pages"""
    
    def extract(self, url: str) -> Dict[str, Any]:
        """Extract contact information"""
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            contact_data = {
                'emails': self._extract_emails(soup),
                'phones': self._extract_phones(soup),
                'addresses': self._extract_addresses(soup),
                'social_links': self._extract_social_links(soup),
                'contact_forms': self._extract_contact_forms(soup)
            }
            
            return contact_data
            
        except Exception as e:
            logger.error(f"Error extracting contact info from {url}: {e}")
            return {}
    
    def _extract_emails(self, soup: BeautifulSoup) -> List[str]:
        """Extract email addresses"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = soup.get_text()
        emails = re.findall(email_pattern, text)
        return list(set(emails))
    
    def _extract_phones(self, soup: BeautifulSoup) -> List[str]:
        """Extract phone numbers"""
        phone_patterns = [
            r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
            r'\+?[0-9]{1,3}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}',
            r'\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        ]
        
        text = soup.get_text()
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))
    
    def _extract_addresses(self, soup: BeautifulSoup) -> List[str]:
        """Extract addresses"""
        # Look for common address patterns
        address_selectors = [
            '[itemprop="address"]',
            '.address',
            '.location',
            '[class*="address"]',
            '[class*="location"]'
        ]
        
        addresses = []
        for selector in address_selectors:
            elements = soup.select(selector)
            for element in elements:
                address_text = element.get_text(strip=True)
                if len(address_text) > 10:  # Basic length filter
                    addresses.append(address_text)
        
        return addresses
    
    def _extract_social_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links"""
        social_platforms = {
            'facebook': ['facebook.com', 'fb.com'],
            'twitter': ['twitter.com', 'x.com'],
            'linkedin': ['linkedin.com'],
            'instagram': ['instagram.com'],
            'youtube': ['youtube.com', 'youtu.be'],
            'tiktok': ['tiktok.com'],
            'pinterest': ['pinterest.com']
        }
        
        social_links = {}
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            for platform, domains in social_platforms.items():
                if any(domain in href.lower() for domain in domains):
                    social_links[platform] = href
                    break
        
        return social_links
    
    def _extract_contact_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract contact form information"""
        forms = soup.find_all('form')
        contact_forms = []
        
        for form in forms:
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'GET'),
                'fields': []
            }
            
            inputs = form.find_all(['input', 'textarea', 'select'])
            for input_elem in inputs:
                field_data = {
                    'type': input_elem.get('type', input_elem.name),
                    'name': input_elem.get('name', ''),
                    'placeholder': input_elem.get('placeholder', ''),
                    'required': input_elem.has_attr('required')
                }
                form_data['fields'].append(field_data)
            
            contact_forms.append(form_data)
        
        return contact_forms


class ProductInfoExtractor(DataExtractor):
    """Extract product information from e-commerce pages"""
    
    def extract(self, url: str) -> Dict[str, Any]:
        """Extract product information"""
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            product_data = {
                'title': self._extract_title(soup),
                'price': self._extract_price(soup),
                'description': self._extract_description(soup),
                'images': self._extract_images(soup),
                'availability': self._extract_availability(soup),
                'reviews': self._extract_reviews(soup),
                'specifications': self._extract_specifications(soup)
            }
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product info from {url}: {e}")
            return {}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract product title"""
        selectors = [
            'h1[class*="title"]',
            'h1[class*="product"]',
            '.product-title',
            '.product-name',
            'h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_price(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract price information"""
        price_data = {
            'current': '',
            'original': '',
            'currency': '',
            'discount': ''
        }
        
        # Look for price elements
        price_selectors = [
            '[class*="price"]',
            '[class*="cost"]',
            '[itemprop="price"]',
            '.price'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                price_match = re.search(r'[\$€£¥₹]?[\d,]+\.?\d*', text)
                if price_match:
                    price_data['current'] = price_match.group()
                    break
        
        return price_data
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description"""
        selectors = [
            '[class*="description"]',
            '[class*="summary"]',
            '[itemprop="description"]',
            '.product-description'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product images"""
        images = []
        img_elements = soup.find_all('img')
        
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src:
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.driver.current_url, src)
                images.append(src)
        
        return images
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract availability status"""
        availability_indicators = [
            'in stock', 'out of stock', 'available', 'unavailable',
            'pre-order', 'coming soon', 'discontinued'
        ]
        
        text = soup.get_text().lower()
        for indicator in availability_indicators:
            if indicator in text:
                return indicator.title()
        
        return "Unknown"
    
    def _extract_reviews(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract review information"""
        review_data = {
            'rating': '',
            'count': '',
            'reviews': []
        }
        
        # Look for rating elements
        rating_selectors = [
            '[class*="rating"]',
            '[class*="star"]',
            '[itemprop="ratingValue"]'
        ]
        
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                rating_match = re.search(r'[\d.]+', text)
                if rating_match:
                    review_data['rating'] = rating_match.group()
                    break
        
        return review_data
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product specifications"""
        specs = {}
        
        # Look for specification tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        specs[key] = value
        
        return specs


class ContentAnalyzer(DataExtractor):
    """Analyze page content for various patterns"""
    
    def extract(self, url: str) -> Dict[str, Any]:
        """Analyze page content"""
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            analysis = {
                'content_type': self._analyze_content_type(soup),
                'language': self._detect_language(soup),
                'keywords': self._extract_keywords(soup),
                'headings': self._extract_headings(soup),
                'links': self._analyze_links(soup),
                'images': self._analyze_images(soup),
                'forms': self._analyze_forms(soup),
                'metadata': self._extract_metadata(soup)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content from {url}: {e}")
            return {}
    
    def _analyze_content_type(self, soup: BeautifulSoup) -> str:
        """Determine the type of content"""
        # Check for common page types
        if soup.find('form'):
            return 'form_page'
        elif soup.find_all('img'):
            return 'image_gallery'
        elif soup.find('table'):
            return 'data_table'
        elif soup.find_all('article'):
            return 'article'
        elif soup.find('iframe'):
            return 'embedded_content'
        else:
            return 'general'
    
    def _detect_language(self, soup: BeautifulSoup) -> str:
        """Detect page language"""
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag.get('lang')
        
        # Fallback to text analysis
        text = soup.get_text()[:1000]  # First 1000 characters
        # Simple language detection based on common words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le']
        
        text_lower = text.lower()
        english_count = sum(1 for word in english_words if word in text_lower)
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        
        if english_count > spanish_count:
            return 'en'
        elif spanish_count > english_count:
            return 'es'
        else:
            return 'unknown'
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract important keywords from the page"""
        # Get meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            return [kw.strip() for kw in meta_keywords['content'].split(',')]
        
        # Extract from headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        keywords = []
        for heading in headings:
            text = heading.get_text(strip=True)
            if text:
                keywords.extend(text.split())
        
        # Return most common words
        from collections import Counter
        word_count = Counter(keywords)
        return [word for word, count in word_count.most_common(10)]
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract all headings from the page"""
        headings = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []}
        
        for tag in headings.keys():
            elements = soup.find_all(tag)
            headings[tag] = [elem.get_text(strip=True) for elem in elements]
        
        return headings
    
    def _analyze_links(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze links on the page"""
        links = soup.find_all('a', href=True)
        
        analysis = {
            'total_links': len(links),
            'internal_links': 0,
            'external_links': 0,
            'broken_links': 0,
            'mailto_links': 0,
            'tel_links': 0
        }
        
        current_domain = urlparse(self.driver.current_url).netloc
        
        for link in links:
            href = link['href']
            if href.startswith('mailto:'):
                analysis['mailto_links'] += 1
            elif href.startswith('tel:'):
                analysis['tel_links'] += 1
            elif href.startswith('http'):
                if urlparse(href).netloc == current_domain:
                    analysis['internal_links'] += 1
                else:
                    analysis['external_links'] += 1
            elif href.startswith('/'):
                analysis['internal_links'] += 1
        
        return analysis
    
    def _analyze_images(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze images on the page"""
        images = soup.find_all('img')
        
        analysis = {
            'total_images': len(images),
            'images_with_alt': 0,
            'images_without_alt': 0,
            'large_images': 0,
            'small_images': 0
        }
        
        for img in images:
            if img.get('alt'):
                analysis['images_with_alt'] += 1
            else:
                analysis['images_without_alt'] += 1
            
            # Check image size if available
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    w, h = int(width), int(height)
                    if w > 500 or h > 500:
                        analysis['large_images'] += 1
                    else:
                        analysis['small_images'] += 1
                except ValueError:
                    pass
        
        return analysis
    
    def _analyze_forms(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze forms on the page"""
        forms = soup.find_all('form')
        
        analysis = {
            'total_forms': len(forms),
            'forms_with_validation': 0,
            'forms_with_captcha': 0,
            'contact_forms': 0,
            'search_forms': 0
        }
        
        for form in forms:
            action = form.get('action', '').lower()
            if 'contact' in action or 'message' in action:
                analysis['contact_forms'] += 1
            elif 'search' in action or 'query' in action:
                analysis['search_forms'] += 1
            
            # Check for validation
            if form.find(['input', 'textarea'], attrs={'required': True}):
                analysis['forms_with_validation'] += 1
            
            # Check for CAPTCHA
            if form.find(['iframe', 'div'], attrs={'class': lambda x: x and 'captcha' in x.lower()}):
                analysis['forms_with_captcha'] += 1
        
        return analysis
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract page metadata"""
        metadata = {}
        
        # Title
        title = soup.find('title')
        if title:
            metadata['title'] = title.get_text(strip=True)
        
        # Meta description
        description = soup.find('meta', attrs={'name': 'description'})
        if description and description.get('content'):
            metadata['description'] = description['content']
        
        # Meta author
        author = soup.find('meta', attrs={'name': 'author'})
        if author and author.get('content'):
            metadata['author'] = author['content']
        
        # Open Graph tags
        og_tags = soup.find_all('meta', attrs={'property': lambda x: x and x.startswith('og:')})
        for tag in og_tags:
            prop = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            if prop and content:
                metadata[f'og_{prop}'] = content
        
        return metadata


class DataExtractionManager:
    """Manage all data extraction processes"""
    
    def __init__(self, driver, task):
        self.driver = driver
        self.task = task
        self.extractors = {
            'contact': ContactInfoExtractor(driver, task),
            'product': ProductInfoExtractor(driver, task),
            'content': ContentAnalyzer(driver, task)
        }
    
    def extract_all(self, url: str) -> Dict[str, Any]:
        """Run all extractors and return combined data"""
        all_data = {
            'url': url,
            'timestamp': None,
            'extracted_data': {}
        }
        
        for name, extractor in self.extractors.items():
            try:
                data = extractor.extract(url)
                all_data['extracted_data'][name] = data
            except Exception as e:
                logger.error(f"Error in {name} extractor: {e}")
                all_data['extracted_data'][name] = {}
        
        return all_data
