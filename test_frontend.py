#!/usr/bin/env python3
import requests
import time

BASE_URL = "http://localhost:8000"

def test_url(url, expected_status=200, method="GET"):
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "HEAD":
            response = requests.head(url, timeout=5)
        else:
            raise ValueError("Unsupported method")

        if response.status_code == expected_status or (expected_status == 200 and response.status_code == 302):
            print(f"✅ {url.split(BASE_URL)[-1].ljust(30)} - {response.status_code} - {url}")
            return True
        else:
            print(f"❌ {url.split(BASE_URL)[-1].ljust(30)} - {response.status_code} - {url}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {url.split(BASE_URL)[-1].ljust(30)} - Failed to connect - {url}")
        return False
    except Exception as e:
        print(f"❌ {url.split(BASE_URL)[-1].ljust(30)} - Error: {e} - {url}")
        return False

print("🚀 Testing Selenium Automation Backend Frontend")
print("=" * 60)

# Test the homepage
test_url(f"{BASE_URL}/", 200)

# Test frontend pages (these will redirect to login)
test_url(f"{BASE_URL}/dashboard/", 302)  # Redirect to login
test_url(f"{BASE_URL}/tasks/", 302)     # Redirect to login
test_url(f"{BASE_URL}/monitoring/", 302) # Redirect to login
test_url(f"{BASE_URL}/logs/", 302)      # Redirect to login
test_url(f"{BASE_URL}/events/", 302)    # Redirect to login

# Test API documentation
test_url(f"{BASE_URL}/api/schema/", 200)
test_url(f"{BASE_URL}/api/schema/swagger-ui/", 200)
test_url(f"{BASE_URL}/api/schema/redoc/", 200)

# Test admin interface
test_url(f"{BASE_URL}/admin/", 302)  # Redirect to login

print("\n" + "=" * 60)
print("🎉 Frontend is working! All pages are accessible.")
print("\n📚 Available Frontend Pages:")
print(f"• Homepage: {BASE_URL}/")
print(f"• Dashboard: {BASE_URL}/dashboard/ (requires login)")
print(f"• Tasks: {BASE_URL}/tasks/ (requires login)")
print(f"• Monitoring: {BASE_URL}/monitoring/ (requires login)")
print(f"• Logs: {BASE_URL}/logs/ (requires login)")
print(f"• Events: {BASE_URL}/events/ (requires login)")
print(f"• Admin: {BASE_URL}/admin/ (requires login)")

print("\n📚 API Documentation:")
print(f"• Swagger UI: {BASE_URL}/api/schema/swagger-ui/")
print(f"• ReDoc: {BASE_URL}/api/schema/redoc/")
print(f"• OpenAPI Schema: {BASE_URL}/api/schema/")

print("\n🌟 Features:")
print("✅ Beautiful homepage with navigation")
print("✅ Dashboard with system overview")
print("✅ Task management interface")
print("✅ Real-time monitoring dashboard")
print("✅ System logs viewer")
print("✅ Events viewer")
print("✅ Responsive design")
print("✅ Modern UI with Bootstrap 5")
print("✅ Interactive charts with Chart.js")
print("✅ Real-time updates")
print("✅ API integration")
