#!/bin/bash

# Create a test user for OmicsOracle
echo "Creating test user..."

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@omicsoracle.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }' | python3 -m json.tool

echo -e "\n\nTest user created!"
echo "Email: test@omicsoracle.com"
echo "Password: TestPassword123!"
echo -e "\nNow login at: http://localhost:8000/login"
