"""
Pre-built automation templates for common use cases
"""
import logging
from typing import Dict, List, Any, Optional
from .models import AutomationTask

logger = logging.getLogger(__name__)


class AutomationTemplate:
    """Base class for automation templates"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.config = {}
    
    def get_config(self) -> Dict[str, Any]:
        """Get template configuration"""
        return self.config
    
    def customize(self, **kwargs) -> Dict[str, Any]:
        """Customize template with user parameters"""
        config = self.config.copy()
        config.update(kwargs)
        return config


class EcommerceScrapingTemplate(AutomationTemplate):
    """Template for e-commerce product scraping"""
    
    def __init__(self):
        super().__init__(
            name="E-commerce Product Scraping",
            description="Scrape product information from e-commerce websites"
        )
        self.config = {
            'max_pages': 10,
            'max_depth': 3,
            'delay_between_requests': 2.0,
            'headless': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'window_size': '1920x1080',
            'priority': 'NORMAL',
            'config': {
                'extract_products': True,
                'extract_prices': True,
                'extract_images': True,
                'extract_reviews': True,
                'follow_product_links': True,
                'extract_categories': True,
                'wait_for_dynamic_content': True,
                'scroll_to_load_content': True
            }
        }
    
    def customize(self, target_domain: str = None, product_categories: List[str] = None, **kwargs):
        """Customize for specific e-commerce site"""
        config = super().customize(**kwargs)
        
        if target_domain:
            config['start_url'] = f"https://{target_domain}"
        
        if product_categories:
            config['config']['target_categories'] = product_categories
        
        return config


class LeadGenerationTemplate(AutomationTemplate):
    """Template for lead generation and contact information extraction"""
    
    def __init__(self):
        super().__init__(
            name="Lead Generation",
            description="Extract contact information and generate leads from business websites"
        )
        self.config = {
            'max_pages': 5,
            'max_depth': 2,
            'delay_between_requests': 3.0,
            'headless': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'window_size': '1920x1080',
            'priority': 'NORMAL',
            'config': {
                'extract_contacts': True,
                'extract_emails': True,
                'extract_phones': True,
                'extract_addresses': True,
                'extract_social_links': True,
                'extract_contact_forms': True,
                'extract_company_info': True,
                'follow_contact_pages': True
            }
        }
    
    def customize(self, industry: str = None, company_size: str = None, **kwargs):
        """Customize for specific industry or company type"""
        config = super().customize(**kwargs)
        
        if industry:
            config['config']['target_industry'] = industry
        
        if company_size:
            config['config']['company_size_filter'] = company_size
        
        return config


class CompetitorAnalysisTemplate(AutomationTemplate):
    """Template for competitor analysis and monitoring"""
    
    def __init__(self):
        super().__init__(
            name="Competitor Analysis",
            description="Analyze competitor websites for pricing, content, and features"
        )
        self.config = {
            'max_pages': 15,
            'max_depth': 4,
            'delay_between_requests': 2.5,
            'headless': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'window_size': '1920x1080',
            'priority': 'HIGH',
            'config': {
                'analyze_pricing': True,
                'extract_features': True,
                'analyze_content_strategy': True,
                'monitor_changes': True,
                'extract_technologies': True,
                'analyze_seo': True,
                'extract_testimonials': True,
                'analyze_ui_ux': True
            }
        }
    
    def customize(self, competitors: List[str] = None, analysis_focus: str = None, **kwargs):
        """Customize for specific competitors and analysis focus"""
        config = super().customize(**kwargs)
        
        if competitors:
            config['config']['target_competitors'] = competitors
        
        if analysis_focus:
            config['config']['analysis_focus'] = analysis_focus
        
        return config


class ContentAuditTemplate(AutomationTemplate):
    """Template for content auditing and SEO analysis"""
    
    def __init__(self):
        super().__init__(
            name="Content Audit",
            description="Audit website content for SEO, accessibility, and quality"
        )
        self.config = {
            'max_pages': 20,
            'max_depth': 3,
            'delay_between_requests': 1.5,
            'headless': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'window_size': '1920x1080',
            'priority': 'NORMAL',
            'config': {
                'analyze_seo': True,
                'check_accessibility': True,
                'analyze_content_quality': True,
                'extract_metadata': True,
                'analyze_performance': True,
                'check_mobile_responsiveness': True,
                'analyze_heading_structure': True,
                'extract_keywords': True
            }
        }
    
    def customize(self, seo_focus: bool = True, accessibility_focus: bool = True, **kwargs):
        """Customize for specific audit focus areas"""
        config = super().customize(**kwargs)
        
        config['config']['seo_analysis'] = seo_focus
        config['config']['accessibility_analysis'] = accessibility_focus
        
        return config


class SocialMediaMonitoringTemplate(AutomationTemplate):
    """Template for social media monitoring and analysis"""
    
    def __init__(self):
        super().__init__(
            name="Social Media Monitoring",
            description="Monitor social media presence and engagement"
        )
        self.config = {
            'max_pages': 8,
            'max_depth': 2,
            'delay_between_requests': 4.0,
            'headless': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'window_size': '1920x1080',
            'priority': 'NORMAL',
            'config': {
                'extract_social_links': True,
                'analyze_engagement': True,
                'monitor_mentions': True,
                'extract_follower_counts': True,
                'analyze_content_strategy': True,
                'extract_hashtags': True,
                'monitor_competitors': True
            }
        }
    
    def customize(self, platforms: List[str] = None, monitoring_keywords: List[str] = None, **kwargs):
        """Customize for specific social media platforms and keywords"""
        config = super().customize(**kwargs)
        
        if platforms:
            config['config']['target_platforms'] = platforms
        
        if monitoring_keywords:
            config['config']['monitoring_keywords'] = monitoring_keywords
        
        return config


class FormTestingTemplate(AutomationTemplate):
    """Template for form testing and validation"""
    
    def __init__(self):
        super().__init__(
            name="Form Testing",
            description="Test and validate web forms for functionality and security"
        )
        self.config = {
            'max_pages': 5,
            'max_depth': 1,
            'delay_between_requests': 2.0,
            'headless': False,  # Need to see forms
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'window_size': '1920x1080',
            'priority': 'HIGH',
            'config': {
                'test_form_validation': True,
                'test_form_submission': True,
                'analyze_form_security': True,
                'extract_form_fields': True,
                'test_error_handling': True,
                'analyze_form_accessibility': True,
                'test_captcha_handling': True
            }
        }
    
    def customize(self, form_types: List[str] = None, security_focus: bool = True, **kwargs):
        """Customize for specific form types and security requirements"""
        config = super().customize(**kwargs)
        
        if form_types:
            config['config']['target_form_types'] = form_types
        
        config['config']['security_analysis'] = security_focus
        
        return config


class TemplateManager:
    """Manage and provide access to automation templates"""
    
    def __init__(self):
        self.templates = {
            'ecommerce': EcommerceScrapingTemplate(),
            'lead_generation': LeadGenerationTemplate(),
            'competitor_analysis': CompetitorAnalysisTemplate(),
            'content_audit': ContentAuditTemplate(),
            'social_media': SocialMediaMonitoringTemplate(),
            'form_testing': FormTestingTemplate()
        }
    
    def get_template(self, template_name: str) -> Optional[AutomationTemplate]:
        """Get a specific template by name"""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates"""
        return [
            {
                'name': template.name,
                'key': key,
                'description': template.description
            }
            for key, template in self.templates.items()
        ]
    
    def create_task_from_template(self, template_name: str, user, **customizations) -> AutomationTask:
        """Create an AutomationTask from a template"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        config = template.customize(**customizations)
        
        # Create the task
        task = AutomationTask.objects.create(
            name=config.get('name', template.name),
            description=config.get('description', template.description),
            start_url=config.get('start_url', ''),
            max_pages=config.get('max_pages', 5),
            max_depth=config.get('max_depth', 2),
            delay_between_requests=config.get('delay_between_requests', 2.0),
            headless=config.get('headless', True),
            user_agent=config.get('user_agent', ''),
            window_size=config.get('window_size', '1920x1080'),
            priority=config.get('priority', 'NORMAL'),
            config=config.get('config', {}),
            created_by=user
        )
        
        return task
    
    def get_template_recommendations(self, url: str, page_content: str = None) -> List[str]:
        """Get template recommendations based on URL and content"""
        recommendations = []
        
        url_lower = url.lower()
        content_lower = (page_content or '').lower()
        
        # E-commerce indicators
        if any(indicator in url_lower for indicator in ['shop', 'store', 'buy', 'product', 'cart']):
            recommendations.append('ecommerce')
        
        # Lead generation indicators
        if any(indicator in content_lower for indicator in ['contact', 'about', 'company', 'business']):
            recommendations.append('lead_generation')
        
        # Competitor analysis indicators
        if any(indicator in content_lower for indicator in ['competitor', 'compare', 'pricing', 'features']):
            recommendations.append('competitor_analysis')
        
        # Content audit indicators
        if any(indicator in content_lower for indicator in ['blog', 'article', 'content', 'seo']):
            recommendations.append('content_audit')
        
        # Social media indicators
        if any(indicator in url_lower for indicator in ['facebook', 'twitter', 'instagram', 'linkedin']):
            recommendations.append('social_media')
        
        # Form testing indicators
        if any(indicator in content_lower for indicator in ['form', 'register', 'login', 'signup']):
            recommendations.append('form_testing')
        
        return recommendations[:3]  # Return top 3 recommendations

# Compatibility functions for the views
def get_available_templates() -> dict:
    """Returns a simplified list of available templates."""
    manager = TemplateManager()
    templates = manager.list_templates()
    return {template['name']: {'name': template['name'], 'description': template['description']} for template in templates}

def get_template_config(template_key: str) -> dict:
    """Returns the default configuration for a given template key."""
    manager = TemplateManager()
    template = manager.get_template(template_key)
    if template:
        return template.get_config()
    return {}

def recommend_templates(url: str, content_keywords: list = None) -> list:
    """Simulates AI-powered template recommendation based on URL and content keywords."""
    manager = TemplateManager()
    return manager.get_template_recommendations(url)
