#!/usr/bin/env python3
"""Standalone API tests that don't require Home Assistant."""
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

# Import standalone API classes
from .api_standalone import UltraloqApiClient

# Load environment variables
load_dotenv()

# Configure logging to show debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def api_client():
    """Create an API client for testing."""
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


class TestUltraloqApi:
    """Test suite for Ultraloq API client."""
    
    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_authentication_success(self, api_client, test_credentials):
        """Test successful authentication."""
        success = await api_client.authenticate(
            test_credentials["email"], 
            test_credentials["password"]
        )
        assert success is True
        assert api_client.token is not None
        assert api_client.auth_data is not None
    
    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_get_addresses(self, api_client, test_credentials):
        """Test getting addresses after authentication."""
        # First authenticate
        await api_client.authenticate(
            test_credentials["email"], 
            test_credentials["password"]
        )
        
        addresses = await api_client.get_addresses()
        assert isinstance(addresses, list)
        assert len(addresses) > 0
        
        # Check address structure
        for address in addresses:
            assert "id" in address
            assert "name" in address
    
    @pytest.mark.asyncio
    @pytest.mark.devices
    async def test_get_devices(self, api_client, test_credentials):
        """Test getting devices for an address."""
        # First authenticate and get addresses
        await api_client.authenticate(
            test_credentials["email"], 
            test_credentials["password"]
        )
        
        addresses = await api_client.get_addresses()
        assert len(addresses) > 0
        
        address_id = addresses[0]["id"]
        devices = await api_client.get_devices(address_id)
        
        assert isinstance(devices, list)
        # May be empty if no devices, so just check it's a list
    
    @pytest.mark.asyncio
    @pytest.mark.devices
    async def test_get_locks(self, api_client, test_credentials):
        """Test getting U-Bolt locks specifically."""
        # First authenticate and get addresses
        await api_client.authenticate(
            test_credentials["email"], 
            test_credentials["password"]
        )
        
        addresses = await api_client.get_addresses()
        assert len(addresses) > 0
        
        address_id = addresses[0]["id"]
        locks = await api_client.get_locks(address_id)
        
        assert isinstance(locks, list)
        
        # If locks exist, check their structure
        for lock in locks:
            assert "uuid" in lock
            assert "name" in lock
            assert "model" in lock
            assert lock["model"] == "U-Bolt"
    
    @pytest.mark.asyncio
    @pytest.mark.locks
    async def test_lock_status(self, api_client, test_credentials):
        """Test getting lock status."""
        # First authenticate and get locks
        await api_client.authenticate(
            test_credentials["email"], 
            test_credentials["password"]
        )
        
        addresses = await api_client.get_addresses()
        assert len(addresses) > 0
        
        address_id = addresses[0]["id"]
        locks = await api_client.get_locks(address_id)
        
        if not locks:
            pytest.skip("No locks found for testing")
        
        lock_uuid = locks[0]["uuid"]
        status = await api_client.get_lock_status(lock_uuid)
        
        assert isinstance(status, dict)
        assert "is_locked" in status
        assert "battery" in status
        assert "online" in status
        assert isinstance(status["is_locked"], bool)
    
    @pytest.mark.asyncio
    @pytest.mark.locks
    async def test_toggle_lock_dry_run(self, api_client, test_credentials):
        """Test toggle lock command (dry run - checks API call only)."""
        # First authenticate and get locks
        await api_client.authenticate(
            test_credentials["email"], 
            test_credentials["password"]
        )
        
        addresses = await api_client.get_addresses()
        assert len(addresses) > 0
        
        address_id = addresses[0]["id"]
        locks = await api_client.get_locks(address_id)
        
        if not locks:
            pytest.skip("No locks found for testing")
        
        lock_uuid = locks[0]["uuid"]
        
        # Get initial status
        initial_status = await api_client.get_lock_status(lock_uuid)
        print(f"Initial lock state: {'LOCKED' if initial_status['is_locked'] else 'UNLOCKED'}")
        
        # Note: Uncomment below to actually toggle the lock
        # WARNING: This will physically operate your lock!
        # result = await api_client.toggle_lock(lock_uuid)
        # assert result is True
        
        print("⚠️ Lock toggle test skipped - uncomment to actually test lock operation")


if __name__ == "__main__":
    # Run tests directly if executed as script
    pytest.main([__file__, "-v"])