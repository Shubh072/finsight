import requests
import json

BASE_URL = "http://localhost:5000/api"

print("=" * 60)
print("TEST 1: Register a new user")
print("=" * 60)

register_data = {
    "full_name": "Test User",
    "username": "testuser_" + str(hash("test") % 10000),
    "email": "test_fix@test.com",
    "phone": "9876543210",
    "password": "TestPass123",
    "confirm_password": "TestPass123"
}

resp = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print(f"Status: {resp.status_code}")
try:
    result = resp.json()
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    token = result.get('access_token')
    print(f"Token received: {bool(token)}")
    if token:
        print(f"Token: {token[:50]}...")
except:
    print(f"Response: {resp.text}")

print()
print("=" * 60)
print("TEST 2: Login with same user")
print("=" * 60)

login_data = {"email": "test_fix@test.com", "password": "TestPass123"}
resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Status: {resp.status_code}")
try:
    result = resp.json()
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    token = result.get('access_token')
    print(f"Token received: {bool(token)}")
    if token:
        print(f"Token: {token[:50]}...")
except:
    print(f"Response: {resp.text}")

print()
print("=" * 60)
print("TEST 3: Add an expense")
print("=" * 60)

# Get a token by logging in
resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
login_result = resp.json()
token = login_result.get('access_token', '')

if token:
    expense_data = {
        "title": "Test Expense",
        "category": "Food",
        "amount": 25.50,
        "expense_date": "2026-07-10",
        "payment_method": "UPI"
    }
    
    resp = requests.post(
        f"{BASE_URL}/expenses/",
        json=expense_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {resp.status_code}")
    try:
        result = resp.json()
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
    except:
        print(f"Response: {resp.text}")
else:
    print("Cannot test - no token")

print()
print("=" * 60)
print("TEST 4: Get expenses list")
print("=" * 60)

if token:
    resp = requests.get(
        f"{BASE_URL}/expenses/",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {resp.status_code}")
    try:
        result = resp.json()
        print(f"Success: {result.get('success')}")
        data = result.get('data', {})
        expenses = data.get('expenses', [])
        print(f"Expenses count: {len(expenses)}")
        for e in expenses:
            print(f"  - {e['title']}: {e['amount']} ({e['category']})")
    except:
        print(f"Response: {resp.text}")

print()
print("=" * 60)
print("TEST 5: Verify user persistence - restart simulation")
print("=" * 60)

# Check that user is still in DB by logging in again
resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Login after restart: Status {resp.status_code}")
result = resp.json()
print(f"Success: {result.get('success')}")
user = result.get('user', {})
print(f"User info: {user}")

print()
print("=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)