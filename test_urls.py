#!/usr/bin/env python3
"""
Test script to verify all URLs are working
"""
import requests
import json

def test_urls():
    base_url = "http://localhost:8000"
    
    print("Testing Selenium Automation Backend URLs...")
    print("=" * 50)
    
    # Test basic endpoints
    endpoints = [
        ("/", "Root"),
        ("/admin/", "Admin Interface"),
        ("/api/", "API Root"),
        ("/api/tasks/", "Tasks API"),
        ("/api/enhanced-tasks/", "Enhanced Tasks API"),
        ("/api/monitoring/", "Monitoring API"),
        ("/api/analysis/", "Analysis API"),
        ("/api/system/", "System API"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = "✓" if response.status_code in [200, 302, 401, 403] else "✗"
            print(f"{status} {description:20} - {response.status_code} - {base_url}{endpoint}")
        except requests.exceptions.RequestException as e:
            print(f"✗ {description:20} - ERROR - {str(e)}")
    
    print("\n" + "=" * 50)
    print("URL Testing Complete!")
    print("\nAvailable URLs:")
    print(f"• Admin Interface: {base_url}/admin/")
    print(f"• API Documentation: {base_url}/api/")
    print(f"• Tasks API: {base_url}/api/tasks/")
    print(f"• Enhanced Tasks: {base_url}/api/enhanced-tasks/")
    print(f"• Monitoring: {base_url}/api/monitoring/")
    print(f"• Analysis: {base_url}/api/analysis/")
    print(f"• System Health: {base_url}/api/system/")

if __name__ == "__main__":
    test_urls()
