#!/usr/bin/env python3
"""Simple test runner script for manual execution."""
import asyncio
import os
import sys
from pathlib import Path

# Add the custom_components directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

import aiohttp
from dotenv import load_dotenv

from ultraloq_wifi.api import UltraloqApiClient

# Load environment variables
load_dotenv()


async def run_api_tests():
    """Run basic API tests manually."""
    email = os.getenv("ULTRALOQ_EMAIL")
    password = os.getenv("ULTRALOQ_PASSWORD")
    
    if not email or not password:
        print("❌ Please set ULTRALOQ_EMAIL and ULTRALOQ_PASSWORD in .env file")
        return False
    
    print("🔧 Testing Ultraloq API endpoints...")
    
    async with aiohttp.ClientSession() as session:
        client = UltraloqApiClient(session)
        
        try:
            # Test 1: Authentication
            print("\n1️⃣ Testing authentication...")
            success = await client.authenticate(email, password)
            if success:
                print("✅ Authentication successful")
            else:
                print("❌ Authentication failed")
                return False
            
            # Test 2: Get addresses
            print("\n2️⃣ Testing get addresses...")
            addresses = await client.get_addresses()
            print(f"✅ Found {len(addresses)} addresses:")
            for addr in addresses:
                print(f"   - {addr['name']} (ID: {addr['id']})")
            
            if not addresses:
                print("❌ No addresses found, cannot continue with device tests")
                return False
            
            address_id = addresses[0]["id"]
            
            # Test 3: Get devices
            print("\n3️⃣ Testing get devices...")
            devices = await client.get_devices(address_id)
            print(f"✅ Found {len(devices)} device groups")
            
            # Test 4: Get locks
            print("\n4️⃣ Testing get locks...")
            locks = await client.get_locks(address_id)
            print(f"✅ Found {len(locks)} U-Bolt locks:")
            for lock in locks:
                print(f"   - {lock['name']} ({lock['uuid']})")
            
            if not locks:
                print("⚠️ No locks found, skipping lock-specific tests")
                return True
            
            lock_uuid = locks[0]["uuid"]
            
            # Test 5: Get lock status
            print("\n5️⃣ Testing get lock status...")
            status = await client.get_lock_status(lock_uuid)
            lock_state = "🔒 LOCKED" if status["is_locked"] else "🔓 UNLOCKED"
            battery = status["battery"]
            online = "🟢 ONLINE" if status["online"] else "🔴 OFFLINE"
            print(f"✅ Lock status: {lock_state}, Battery: {battery}, Status: {online}")
            
            # Test 6: Toggle lock (optional - uncomment if you want to test)
            # print("\n6️⃣ Testing toggle lock...")
            # print("⚠️ This will actually lock/unlock your door!")
            # confirm = input("Continue? (y/N): ")
            # if confirm.lower() == 'y':
            #     initial_state = status["is_locked"]
            #     await client.toggle_lock(lock_uuid)
            #     print("✅ Lock toggle command sent")
            #     
            #     # Wait and check new state
            #     await asyncio.sleep(3)
            #     new_status = await client.get_lock_status(lock_uuid)
            #     new_state = new_status["is_locked"]
            #     
            #     if new_state != initial_state:
            #         print(f"✅ Lock state changed: {initial_state} → {new_state}")
            #     else:
            #         print("⚠️ Lock state did not change (might take longer)")
            # else:
            #     print("ℹ️ Skipping toggle test")
            
            print("\n🎉 All tests completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(run_api_tests())
    sys.exit(0 if success else 1)