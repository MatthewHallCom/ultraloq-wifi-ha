#!/usr/bin/env python3
"""Test the main component API with debug logging."""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the custom_components directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

import aiohttp
import pytest
import pytest_asyncio
from dotenv import load_dotenv

# Import main API from the component
from ultraloq_wifi.api import UltraloqApiClient

# Load environment variables
load_dotenv()

# Configure logging to show debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Set specific logger to DEBUG
logger = logging.getLogger('ultraloq_wifi.api')
logger.setLevel(logging.DEBUG)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def main_api_client():
    """Create a main API client for testing."""
    async with aiohttp.ClientSession() as session:
        client = UltraloqApiClient(session)
        yield client


@pytest.fixture
def test_credentials():
    """Get test credentials from environment."""
    email = os.getenv("ULTRALOQ_EMAIL")
    password = os.getenv("ULTRALOQ_PASSWORD")
    
    if not email or not password:
        pytest.skip("ULTRALOQ_EMAIL and ULTRALOQ_PASSWORD must be set in .env file")
    
    return {"email": email, "password": password}


class TestMainUltraloqApi:
    """Test suite for main Ultraloq API client with debug logging."""
    
    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_main_api_authentication(self, main_api_client, test_credentials):
        """Test main API authentication with debug logging."""
        print("\n=== TESTING MAIN API WITH DEBUG LOGGING ===")
        
        try:
            success = await main_api_client.authenticate(
                test_credentials["email"], 
                test_credentials["password"]
            )
            print(f"Authentication result: {success}")
            
            if success:
                print("✅ Authentication successful!")
            else:
                print("❌ Authentication failed")
                
        except Exception as e:
            print(f"❌ Authentication exception: {e}")
            raise


if __name__ == "__main__":
    # Run tests directly if executed as script
    pytest.main([__file__, "-v", "-s"])