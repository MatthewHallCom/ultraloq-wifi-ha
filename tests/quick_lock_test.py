#!/usr/bin/env python3
"""Quick lock/unlock test script with debug logging."""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the tests directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

import aiohttp
from dotenv import load_dotenv

# Import standalone API classes
from api_standalone import UltraloqApiClient

# Load environment variables
load_dotenv()

# Configure logging to show debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


async def test_lock_unlock():
    """Quick test of lock/unlock functionality."""
    # Get credentials from environment
    email = os.getenv("ULTRALOQ_EMAIL")
    password = os.getenv("ULTRALOQ_PASSWORD")
    
    if not email or not password:
        print("❌ ULTRALOQ_EMAIL and ULTRALOQ_PASSWORD must be set in .env file")
        return
    
    async with aiohttp.ClientSession() as session:
        client = UltraloqApiClient(session)
        
        try:
            print("🔐 Starting lock/unlock test...")
            
            # Step 1: Authenticate
            print("\n=== AUTHENTICATION ===")
            auth_success = await client.authenticate(email, password)
            if not auth_success:
                print("❌ Authentication failed")
                return
            print("✅ Authentication successful")
            
            # Step 2: Get locks
            print("\n=== GETTING LOCKS ===")
            addresses = await client.get_addresses()
            if not addresses:
                print("❌ No addresses found")
                return
            
            address_id = addresses[0]["id"]
            print(f"Using address ID: {address_id}")
            
            locks = await client.get_locks(address_id)
            if not locks:
                print("❌ No locks found")
                return
                
            lock = locks[0]
            lock_uuid = lock["uuid"]
            user_uid = lock.get("user_uid")
            
            print(f"Found lock: {lock['name']} ({lock_uuid})")
            print(f"User UID: {user_uid}")
            
            if not user_uid:
                print("❌ No user UID found - cannot send commands")
                return
            
            # Step 3: Check initial status
            print("\n=== INITIAL STATUS ===")
            initial_status = await client.get_lock_status(lock_uuid)
            initial_state = 'LOCKED' if initial_status['is_locked'] else 'UNLOCKED'
            print(f"Initial lock state: {initial_state}")
            
            # Step 4: Check online status
            print("\n=== ONLINE STATUS ===")
            online_status = await client.check_lock_online(lock_uuid)
            is_online = online_status.get('is_online', False)
            print(f"BLE online: {online_status.get('ble_online', False)}")
            print(f"Remote online: {online_status.get('remote_online', False)}")
            print(f"Overall online: {is_online}")
            
            if not is_online:
                print("⚠️ WARNING: Lock is OFFLINE - commands may not work!")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("Aborting test")
                    return
            
            # Step 5: UNLOCK
            print("\n=== UNLOCK COMMAND ===")
            print("⚠️ About to UNLOCK the lock - this will physically operate your lock!")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("Skipping unlock")
                unlock_worked = None
            else:
                try:
                    unlock_result = await client.unlock(lock_uuid, user_uid)
                    print(f"✅ Unlock API call succeeded: {unlock_result}")
                    unlock_worked = True
                except Exception as e:
                    print(f"❌ Unlock failed: {e}")
                    unlock_worked = False
                    if "expected UNLOCKED, got LOCKED" in str(e):
                        print("🔍 This indicates the unlock command was sent but the lock didn't physically unlock")
            
            # Step 6: LOCK
            print("\n=== LOCK COMMAND ===")
            print("⚠️ About to LOCK the lock - this will physically operate your lock!")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("Skipping lock")
                lock_worked = None
            else:
                try:
                    lock_result = await client.lock(lock_uuid, user_uid)
                    print(f"✅ Lock API call succeeded: {lock_result}")
                    lock_worked = True
                except Exception as e:
                    print(f"❌ Lock failed: {e}")
                    lock_worked = False
                    if "expected LOCKED, got UNLOCKED" in str(e):
                        print("🔍 This indicates the lock command was sent but the lock didn't physically lock")
            
            # Final analysis
            print("\n=== FINAL ANALYSIS ===")
            if unlock_worked is not None:
                print(f"Unlock command: {'✅ SUCCESS' if unlock_worked else '❌ FAILED'}")
            if lock_worked is not None:
                print(f"Lock command: {'✅ SUCCESS' if lock_worked else '❌ FAILED'}")
                
            if unlock_worked is False or lock_worked is False:
                print("\n⚠️ Some commands failed - this could indicate:")
                print("  - Wrong user UID being used")
                print("  - Lock is not responding to remote commands")
                print("  - API endpoint or command format issues")
                print("  - Lock firmware or connectivity problems")
            
            print("\n✅ Test completed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_lock_unlock())