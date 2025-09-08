#!/bin/bash

# API testing script for Selenium Automation Backend

BASE_URL="http://localhost:8000/api"
ADMIN_TOKEN=""

echo "Testing Selenium Automation Backend API..."

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local headers=$4
    
    if [ -n "$data" ]; then
        curl -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -H "$headers" \
            -d "$data"
    else
        curl -X $method "$BASE_URL$endpoint" \
            -H "$headers"
    fi
}

# Test 1: Health check
echo "1. Testing system health..."
api_call "GET" "/system/health/" ""

echo -e "\n\n2. Testing task creation..."

# Test 2: Create a task
TASK_DATA='{
    "name": "Test Automation Task",
    "description": "Testing the API functionality",
    "start_url": "https://httpbin.org/get",
    "max_pages": 3,
    "max_depth": 1,
    "delay_between_requests": 1.0,
    "headless": true,
    "priority": "NORMAL"
}'

RESPONSE=$(api_call "POST" "/tasks/" "$TASK_DATA" "")
echo "$RESPONSE"

# Extract task ID from response
TASK_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "Created task with ID: $TASK_ID"

if [ -n "$TASK_ID" ]; then
    echo -e "\n3. Testing task start..."
    api_call "POST" "/tasks/$TASK_ID/start/" "" ""
    
    echo -e "\n4. Testing task details..."
    api_call "GET" "/tasks/$TASK_ID/" "" ""
    
    echo -e "\n5. Testing task logs..."
    api_call "GET" "/tasks/$TASK_ID/logs/" "" ""
    
    echo -e "\n6. Testing task stats..."
    api_call "GET" "/tasks/$TASK_ID/stats/" "" ""
    
    echo -e "\n7. Testing dashboard..."
    api_call "GET" "/tasks/dashboard/" "" ""
fi

echo -e "\n\nAPI testing completed!"
