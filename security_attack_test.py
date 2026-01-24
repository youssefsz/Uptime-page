
import asyncio
import httpx
import sys
import time

BASE_URL = "http://localhost:8000/api/servers"

async def test_rate_limit(client, endpoint, limit, name):
    print(f"\n--- Testing {name} (Limit: {limit}/min) ---")
    
    success_count = 0
    blocked_count = 0
    
    # Try to exceed the limit by sending limit + 5 requests
    total_requests = limit + 5
    
    start_time = time.time()
    
    for i in range(total_requests):
        try:
            response = await client.get(endpoint)
            if response.status_code == 200:
                success_count += 1
                print(f"Request {i+1}: Success (200)")
            elif response.status_code == 429:
                blocked_count += 1
                print(f"Request {i+1}: BLOCKED (429) - Rate Limit Working!")
            else:
                print(f"Request {i+1}: Unexpected status {response.status_code}")
        except Exception as e:
            print(f"Request {i+1}: Error - {e}")
            
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nResults for {name}:")
    print(f"Total Requests: {total_requests}")
    print(f"Successful: {success_count}")
    print(f"Blocked: {blocked_count}")
    print(f"Time taken: {duration:.2f} seconds")
    
    if blocked_count > 0:
        print("✅ SUCCESS: Rate limiting is active and blocking attacks.")
    else:
        print("❌ FAILURE: Rate limiting did not block any requests.")

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Test "Get All Servers" (Limit: 60/min)
        # We need to hit it 65 times to trigger the block
        await test_rate_limit(client, BASE_URL, 60, "Get All Servers Endpoint")
        
        # 2. Test "Get With Bars" (Limit: 20/min)
        # We need to hit it 25 times to trigger the block
        # Note: We need to use a different client IP or wait if the limiter is global, 
        # but SlowAPI usually limits by IP + Route.
        await test_rate_limit(client, f"{BASE_URL}/with-bars", 20, "Get With Bars Endpoint")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted.")
