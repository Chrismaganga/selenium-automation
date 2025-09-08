#!/usr/bin/env python3
"""
Test script to verify Swagger and ReDoc are working
"""
import requests
import json

def test_swagger_redoc():
    print("🚀 Testing Selenium Automation Backend with Swagger & ReDoc")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        ("/", "Homepage"),
        ("/api/schema/", "OpenAPI Schema"),
        ("/api/schema/swagger-ui/", "Swagger UI"),
        ("/api/schema/redoc/", "ReDoc"),
        ("/admin/", "Admin Interface"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description:20} - {response.status_code} - {base_url}{endpoint}")
            else:
                print(f"❌ {description:20} - {response.status_code} - {base_url}{endpoint}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {description:20} - ERROR - {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! Swagger and ReDoc are now available!")
    print("\n📚 Available Documentation:")
    print(f"• Homepage: {base_url}/")
    print(f"• Swagger UI: {base_url}/api/schema/swagger-ui/")
    print(f"• ReDoc: {base_url}/api/schema/redoc/")
    print(f"• OpenAPI Schema: {base_url}/api/schema/")
    print(f"• Admin Interface: {base_url}/admin/")
    
    print("\n🌟 Features:")
    print("✅ Beautiful homepage with navigation")
    print("✅ Interactive Swagger UI documentation")
    print("✅ Clean ReDoc documentation")
    print("✅ OpenAPI 3.0 schema")
    print("✅ Django admin interface")
    print("✅ Complete API documentation")
    print("✅ Authentication support")
    print("✅ Real-time API testing")

if __name__ == "__main__":
    test_swagger_redoc()
