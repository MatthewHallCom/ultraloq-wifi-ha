"""Integration tests for Ultraloq API endpoints."""
import asyncio
import os
import sys
from pathlib import Path

import aiohttp
import pytest
from dotenv import load_dotenv

# Add the custom_components directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from ultraloq_wifi.api import UltraloqApiClient, UltraloqApiError, UltraloqAuthError

# Load environment variables
load_dotenv()


@pytest.fixture
async def api_client():
    """Create an API client for testing."""
    async with aiohttp.ClientSession() as session:
        client = UltraloqApiClient(session)
        yield client


@pytest.fixture
def credentials():
    """Get test credentials from environment."""
    email = os.getenv("ULTRALOQ_EMAIL")
    password = os.getenv("ULTRALOQ_PASSWORD")
    
    if not email or not password:
        pytest.skip("ULTRALOQ_EMAIL and ULTRALOQ_PASSWORD environment variables required")
    
    return {
        "email": email,
        "password": password,
        "test_uuid": os.getenv("ULTRALOQ_TEST_UUID"),
        "address_id": os.getenv("ULTRALOQ_ADDRESS_ID"),
    }


class TestUltraloqApiAuth:
    """Test authentication flow."""

    async def test_get_api_token(self, api_client):
        """Test getting API token from token endpoint."""
        # This is a private method, but we can test it indirectly through authenticate
        await api_client._get_api_token()
        
        assert api_client._api_token is not None
        assert api_client._api_base_url is not None
        assert "https://cloud.u-tec.com/app" in api_client._api_base_url

    async def test_authenticate_success(self, api_client, credentials):
        """Test successful authentication."""
        result = await api_client.authenticate(
            credentials["email"], 
            credentials["password"]
        )
        
        assert result is True
        assert api_client.is_authenticated
        assert api_client._api_token is not None
        assert api_client._access_token is not None

    async def test_authenticate_invalid_credentials(self, api_client):
        """Test authentication with invalid credentials."""
        with pytest.raises(UltraloqAuthError):
            await api_client.authenticate("invalid@email.com", "wrongpassword")

    async def test_authenticate_empty_credentials(self, api_client):
        """Test authentication with empty credentials."""
        with pytest.raises(UltraloqAuthError):
            await api_client.authenticate("", "")


class TestUltraloqApiAddresses:
    """Test address-related endpoints."""

    @pytest.fixture(autouse=True)
    async def setup(self, api_client, credentials):
        """Authenticate before each test."""
        await api_client.authenticate(credentials["email"], credentials["password"])
        self.api_client = api_client

    async def test_get_addresses(self):
        """Test getting list of addresses."""
        addresses = await self.api_client.get_addresses()
        
        assert isinstance(addresses, list)
        assert len(addresses) > 0
        
        # Check structure of first address
        address = addresses[0]
        assert "id" in address
        assert "name" in address
        assert isinstance(address["id"], int)


class TestUltraloqApiDevices:
    """Test device-related endpoints."""

    @pytest.fixture(autouse=True)
    async def setup(self, api_client, credentials):
        """Authenticate and get address ID before each test."""
        await api_client.authenticate(credentials["email"], credentials["password"])
        self.api_client = api_client
        
        # Get address ID for device tests
        if credentials["address_id"]:
            self.address_id = int(credentials["address_id"])
        else:
            addresses = await api_client.get_addresses()
            assert len(addresses) > 0, "No addresses found for testing"
            self.address_id = addresses[0]["id"]

    async def test_get_devices(self):
        """Test getting list of devices for an address."""
        devices = await self.api_client.get_devices(self.address_id)
        
        assert isinstance(devices, list)
        # Note: might be empty if no devices at address
        
        for device_group in devices:
            assert "id" in device_group
            assert "devices" in device_group
            assert isinstance(device_group["devices"], list)

    async def test_get_locks(self):
        """Test getting filtered list of U-Bolt locks."""
        locks = await self.api_client.get_locks(self.address_id)
        
        assert isinstance(locks, list)
        
        # If we have locks, verify they're U-Bolt models
        for lock in locks:
            assert lock["model"] == "U-Bolt"
            assert "uuid" in lock
            assert "name" in lock
            assert lock["uuid"] is not None


class TestUltraloqApiLockStatus:
    """Test lock status and control endpoints."""

    @pytest.fixture(autouse=True)
    async def setup(self, api_client, credentials):
        """Authenticate and find a test lock before each test."""
        await api_client.authenticate(credentials["email"], credentials["password"])
        self.api_client = api_client
        
        # Get a lock UUID for testing
        if credentials["test_uuid"]:
            self.lock_uuid = credentials["test_uuid"]
        else:
            # Find address and get first lock
            if credentials["address_id"]:
                address_id = int(credentials["address_id"])
            else:
                addresses = await api_client.get_addresses()
                assert len(addresses) > 0, "No addresses found"
                address_id = addresses[0]["id"]
            
            locks = await api_client.get_locks(address_id)
            assert len(locks) > 0, "No locks found for testing"
            self.lock_uuid = locks[0]["uuid"]

    async def test_get_lock_status(self):
        """Test getting lock status."""
        status = await self.api_client.get_lock_status(self.lock_uuid)
        
        assert isinstance(status, dict)
        assert "uuid" in status
        assert "model" in status
        assert "is_locked" in status
        assert "is_unlocked" in status
        assert "online" in status
        assert "battery" in status
        
        # Verify lock state consistency
        assert status["is_locked"] != status["is_unlocked"]
        assert status["uuid"] == self.lock_uuid
        assert status["model"] == "U-Bolt"

    async def test_toggle_lock(self):
        """Test toggling lock state."""
        # Get initial status
        initial_status = await self.api_client.get_lock_status(self.lock_uuid)
        initial_locked = initial_status["is_locked"]
        
        # Toggle the lock
        result = await self.api_client.toggle_lock(self.lock_uuid)
        assert result is True
        
        # Wait a moment for the lock to respond
        await asyncio.sleep(2)
        
        # Get new status and verify it changed
        new_status = await self.api_client.get_lock_status(self.lock_uuid)
        new_locked = new_status["is_locked"]
        
        # The state should have changed
        assert new_locked != initial_locked
        
        # Toggle back to original state
        await self.api_client.toggle_lock(self.lock_uuid)
        await asyncio.sleep(2)
        
        # Verify we're back to original state
        final_status = await self.api_client.get_lock_status(self.lock_uuid)
        final_locked = final_status["is_locked"]
        assert final_locked == initial_locked


class TestUltraloqApiErrors:
    """Test error handling."""

    async def test_unauthenticated_requests(self, api_client):
        """Test that unauthenticated requests raise appropriate errors."""
        # Try to get addresses without authentication
        with pytest.raises(UltraloqAuthError, match="Not authenticated"):
            await api_client.get_addresses()
        
        # Try to get devices without authentication
        with pytest.raises(UltraloqAuthError, match="Not authenticated"):
            await api_client.get_devices(12345)
        
        # Try to get lock status without authentication
        with pytest.raises(UltraloqAuthError, match="Not authenticated"):
            await api_client.get_lock_status("AC:4D:16:A0:55:D8")
        
        # Try to toggle lock without authentication
        with pytest.raises(UltraloqAuthError, match="Not authenticated"):
            await api_client.toggle_lock("AC:4D:16:A0:55:D8")

    async def test_invalid_device_uuid(self, api_client, credentials):
        """Test error handling for invalid device UUID."""
        await api_client.authenticate(credentials["email"], credentials["password"])
        
        # Try to get status for non-existent device
        with pytest.raises(UltraloqApiError):
            await api_client.get_lock_status("INVALID:UUID:HERE")

    async def test_invalid_address_id(self, api_client, credentials):
        """Test error handling for invalid address ID."""
        await api_client.authenticate(credentials["email"], credentials["password"])
        
        # Try to get devices for non-existent address
        devices = await api_client.get_devices(999999)
        # This might return empty list rather than error, depending on API behavior
        assert isinstance(devices, list)


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(pytest.main([__file__, "-v"]))