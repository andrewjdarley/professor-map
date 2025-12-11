import requests
import json

SUPABASE_URL = 'https://dltiuafpersxnnwxfwve.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRsdGl1YWZwZXJzeG5ud3hmd3ZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODMxODUsImV4cCI6MjA4MDI1OTE4NX0.zuThXcIZVh0eyWLGBJZrrgBMFQQbUm302GOSHRlpc-E'

print("=" * 80)
print("SUPABASE API DEBUGGER")
print("=" * 80)

# Test 1: Check if we can reach Supabase
print("\n[TEST 1] Connecting to Supabase...")
try:
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/',
        headers={
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
        }
    )
    print(f"✓ Connected! Status: {response.status_code}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# Test 2: List all tables
print("\n[TEST 2] Listing all tables...")
try:
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/information_schema.tables',
        headers={
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
        }
    )
    if response.status_code == 200:
        tables = response.json()
        if tables:
            print(f"✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table.get('table_name', 'unknown')}")
        else:
            print("✗ No tables found")
    else:
        print(f"✗ Status {response.status_code}: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Try to query professors table
print("\n[TEST 3] Querying professors table...")
try:
    url = f'{SUPABASE_URL}/rest/v1/professors?select=*&limit=5'
    print(f"URL: {url}")
    
    response = requests.get(
        url,
        headers={
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Got {len(data)} rows")
        if data:
            print("\nFirst row:")
            print(json.dumps(data[0], indent=2))
            print("\nColumn names:")
            print(list(data[0].keys()))
    else:
        print(f"✗ Error response:")
        print(response.text[:500])
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Response text: {response.text[:500]}")

# Test 4: Query by name
print("\n[TEST 4] Querying by professor name (Paul Jenkins)...")
try:
    url = f'{SUPABASE_URL}/rest/v1/professors?select=*&first_name=ilike.%Paul%&last_name=ilike.%Jenkins%'
    print(f"URL: {url}")
    
    response = requests.get(
        url,
        headers={
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
        }
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {len(data)} matching professors")
        if data:
            print("\nResult:")
            print(json.dumps(data[0], indent=2))
    else:
        print(f"✗ Error: {response.text[:500]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Check what columns exist
print("\n[TEST 5] Checking table schema...")
try:
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/professors?select=*&limit=1',
        headers={
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"✓ Table columns:")
            for col in data[0].keys():
                print(f"  - {col}")
    else:
        print(f"✗ Failed to get schema")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)