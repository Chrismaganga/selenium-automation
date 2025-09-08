"""
Data extraction module for intelligent data extraction from HTML content.
"""
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def intelligent_data_extraction(html_content: str, config: dict = None) -> dict:
    """
    Extracts various types of data from HTML content based on configuration.
    This is a simplified version for demonstration purposes.
    """
    if not html_content:
        return {"error": "No HTML content provided for extraction."}
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        return {"error": f"Error parsing HTML: {e}"}
    
    extracted_data = {}
    
    # Extract contact information
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_content)
    if emails:
        extracted_data['emails'] = list(set(emails))
    
    # Extract phone numbers
    phones = re.findall(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', html_content)
    if phones:
        extracted_data['phones'] = list(set(phones))
    
    # Extract social media links
    social_links = {}
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'facebook.com' in href:
            social_links.setdefault('facebook', []).append(href)
        elif 'twitter.com' in href or 'x.com' in href:
            social_links.setdefault('twitter', []).append(href)
        elif 'linkedin.com' in href:
            social_links.setdefault('linkedin', []).append(href)
        elif 'instagram.com' in href:
            social_links.setdefault('instagram', []).append(href)
    
    if social_links:
        extracted_data['social_media_links'] = {k: list(set(v)) for k, v in social_links.items()}
    
    # Extract forms
    forms = []
    for form in soup.find_all('form'):
        form_data = {
            'action': form.get('action', ''),
            'method': form.get('method', 'get'),
            'inputs': []
        }
        for input_tag in form.find_all(['input', 'textarea', 'select']):
            input_data = {
                'type': input_tag.get('type', input_tag.name),
                'name': input_tag.get('name', ''),
                'placeholder': input_tag.get('placeholder', ''),
                'required': input_tag.has_attr('required')
            }
            form_data['inputs'].append(input_data)
        forms.append(form_data)
    
    if forms:
        extracted_data['forms'] = forms
    
    # Extract basic page information
    title = soup.find('title')
    if title:
        extracted_data['title'] = title.get_text(strip=True)
    
    meta_description = soup.find('meta', attrs={'name': 'description'})
    if meta_description:
        extracted_data['meta_description'] = meta_description.get('content', '')
    
    # Extract headings
    headings = []
    for i in range(1, 7):
        for heading in soup.find_all(f'h{i}'):
            headings.append({
                'level': i,
                'text': heading.get_text(strip=True)
            })
    
    if headings:
        extracted_data['headings'] = headings
    
    logger.info(f"Data extraction completed. Extracted {len(extracted_data)} data categories.")
    return extracted_data
