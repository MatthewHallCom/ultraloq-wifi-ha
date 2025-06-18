"""Standalone API client for testing without Home Assistant dependencies."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp
from aiohttp import ClientSession

# Constants
USER_AGENT = "U home/3.2.9.2 (Linux; U; Android 12; Android SDK built for arm64 Build/SE1A.220621.001)"
TOKEN_URL = "https://uemc.u-tec.com/app/token"
LOGIN_URL = "https://cloud.u-tec.com/app/user/login"
ADDRESS_URL = "https://cloud.u-tec.com/app/address"
DEVICE_LIST_URL = "https://cloud.u-tec.com/app/device/list/address"
DEVICE_STATUS_URL = "https://cloud.u-tec.com/app/device/status"
DEVICE_TOGGLE_URL = "https://cloud.u-tec.com/app/device/lock/logs/add"
DEVICE_ONLINE_CHECK_URL = "https://cloud.u-tec.com/app/device/lock/share/get/isopen"

# App credentials (using working values from main API)
APP_ID = "13ca0de1e6054747c44665ae13e36c2c"
CLIENT_ID = "1375ac0809878483ee236497d57f371f"
UUID = "77b7de5d1a5efd83"
VERSION = "3.2"
TIMEZONE = "-8"

_LOGGER = logging.getLogger(__name__)


class UltraloqApiError(Exception):
    """Base exception for Ultraloq API errors."""


class UltraloqAuthError(UltraloqApiError):
    """Authentication error."""


class UltraloqApiClient:
    """Ultraloq API client."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the API client."""
        self._session = session
        self._access_token: str | None = None
        self._api_token: str | None = None
        self._api_base_url: str | None = None
        
        # Set default headers for all requests
        default_headers = {
            "User-Agent": USER_AGENT,
            "X-Api-Version": "3.3",
            "X-Build": "Release",
            "X-Stage": "Release",
        }
        self._session.headers.update(default_headers)

    @property
    def token(self) -> str | None:
        """Get the current API token."""
        return self._api_token

    @property
    def auth_data(self) -> dict | None:
        """Get authentication data."""
        return {"token": self._api_token, "base_url": self._api_base_url}

    async def _get_api_token(self) -> str:
        """Get API token from token endpoint."""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }

        data = {
            "appid": APP_ID,
            "clientid": CLIENT_ID,
            "uuid": UUID,
            "version": VERSION,
            "timezone": TIMEZONE,
        }

        async with self._session.post(
            TOKEN_URL, json=data, headers=headers
        ) as response:
            if response.status != 200:
                raise UltraloqApiError(f"Token request failed: {response.status}")

            # Debug: Check response content type and body
            content_type = response.headers.get("Content-Type", "")
            print(f"DEBUG: Response status: {response.status}")
            print(f"DEBUG: Response content-type: {content_type}")
            
            # Try to get response text first
            response_text = await response.text()
            print(f"DEBUG: Response body: {response_text[:200]}...")
            
            try:
                # Try to parse as JSON despite content type
                result = await response.json(content_type=None)
                print(f"DEBUG: Parsed JSON response: {result}")
                
                # Handle different response codes
                if result.get("code") in [200, 202]:
                    # Check if we have token data
                    if "data" in result and result["data"]:
                        token_data = result["data"]
                        if isinstance(token_data, dict) and "token" in token_data:
                            self._api_token = token_data["token"]
                            self._api_base_url = token_data.get("url")
                            print(f"DEBUG: Successfully extracted token")
                            return self._api_token
                        else:
                            print(f"DEBUG: Data exists but no token found: {token_data}")
                    else:
                        print(f"DEBUG: No data in response or data is empty")
                
                raise UltraloqApiError(f"Token request failed: {result}")
            except Exception as e:
                print(f"DEBUG: Failed to parse JSON: {e}")
                raise UltraloqApiError(f"Token request failed - invalid response format: {response_text[:100]}")

    async def authenticate(self, email: str, password: str) -> bool:
        """Authenticate with Ultraloq API."""
        try:
            # Step 1: Get API token
            print(f"DEBUG: Starting authentication for email: {email}")
            await self._get_api_token()
            print(f"DEBUG: Token obtained: {self._api_token[:20]}..." if self._api_token else "None")

            # Step 2: Login with credentials using form-encoded data
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            }

            # Form-encoded data with JSON-encoded credentials as in raw request
            credentials_json = json.dumps({
                "email": email,
                "password": password,
            })
            
            form_data = {
                "data": credentials_json,
                "token": self._api_token,
            }

            print(f"DEBUG: Login request URL: {LOGIN_URL}")
            print(f"DEBUG: Login request headers: {headers}")
            print(f"DEBUG: Login request data: {form_data}")

            async with self._session.post(
                LOGIN_URL, data=form_data, headers=headers
            ) as response:
                print(f"DEBUG: Login response status: {response.status}")
                print(f"DEBUG: Login response headers: {dict(response.headers)}")
                
                if response.status != 200:
                    response_text = await response.text()
                    print(f"DEBUG: Login error response body: {response_text[:200]}...")
                    raise UltraloqAuthError(f"Login failed: {response.status}")

                response_text = await response.text()
                print(f"DEBUG: Login response body: {response_text[:200]}...")
                
                try:
                    result = await response.json(content_type=None)
                    print(f"DEBUG: Login parsed JSON: {result}")
                    
                    if result.get("code") != 200:
                        raise UltraloqAuthError(f"Login failed: {result}")

                    # Login successful - user data received, use API token for subsequent requests
                    self._access_token = self._api_token  # Use the API token as access token
                    print(f"DEBUG: Login successful, user UUID: {result['data'].get('uuid')}")
                    print(f"DEBUG: Using API token as access token: {self._access_token[:20]}...")
                    return True
                except Exception as e:
                    print(f"DEBUG: Failed to parse login JSON: {e}")
                    raise UltraloqAuthError(f"Login response parse failed: {response_text[:100]}")

        except Exception as e:
            _LOGGER.error("Authentication failed: %s", e)
            print(f"DEBUG: Authentication exception: {e}")
            raise UltraloqAuthError(f"Authentication failed: {e}") from e

    async def get_addresses(self) -> list[dict[str, Any]]:
        """Get user addresses."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"token": self._api_token}

        async with self._session.post(
            ADDRESS_URL, data=data, headers=headers
        ) as response:
            if response.status != 200:
                raise UltraloqApiError(f"Address request failed: {response.status}")

            result = await response.json()
            if result.get("code") != 200:
                raise UltraloqApiError(f"Address request failed: {result}")

            return result.get("data", [])

    async def get_devices(self, address_id: str) -> list[dict[str, Any]]:
        """Get devices for an address."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated")

        headers = {}

        # Create multipart form data
        data = aiohttp.FormData()
        data.add_field("token", self._api_token)
        data.add_field("data", json.dumps({"address_id": address_id}))

        async with self._session.post(
            DEVICE_LIST_URL, data=data, headers=headers
        ) as response:
            if response.status != 200:
                raise UltraloqApiError(f"Device request failed: {response.status}")

            result = await response.json()
            if result.get("code") != 200:
                raise UltraloqApiError(f"Device request failed: {result}")

            return result.get("data", [])

    async def get_locks(self, address_id: str) -> list[dict[str, Any]]:
        """Get U-Bolt locks for an address."""
        devices_data = await self.get_devices(address_id)
        locks = []

        for location in devices_data:
            if "devices" in location:
                for device in location["devices"]:
                    if device.get("model") == "U-Bolt":
                        # Add user UID for lock commands
                        user_data = device.get("user", {})
                        device["user_uid"] = user_data.get("uid")
                        locks.append(device)

        return locks

    async def get_lock_status(self, device_uuid: str) -> dict[str, Any]:
        """Get status of a specific lock."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated")

        headers = {}

        # Create multipart form data
        data = aiohttp.FormData()
        data.add_field("token", self._api_token)
        data.add_field("data", json.dumps({"uuid": device_uuid}))

        async with self._session.post(
            DEVICE_STATUS_URL, data=data, headers=headers
        ) as response:
            if response.status != 200:
                raise UltraloqApiError(f"Status request failed: {response.status}")

            result = await response.json()
            if result.get("code") != 200:
                raise UltraloqApiError(f"Status request failed: {result}")

            device_data = result.get("data", {})
            return {
                "is_locked": device_data.get("is_locked") == 2,  # 2 = locked, 1 = unlocked
                "battery": device_data.get("battery", 0),
                "online": device_data.get("is_connected", 0) == 1,
            }

    async def check_lock_online(self, device_uuid: str) -> dict[str, Any]:
        """Check if lock is online (both BLE and remote connectivity)."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }

        form_data = {
            "token": self._api_token,
            "data": json.dumps({"uuid": device_uuid})
        }

        async with self._session.post(
            DEVICE_ONLINE_CHECK_URL, data=form_data, headers=headers
        ) as response:
            if response.status != 200:
                raise UltraloqApiError(f"Online check request failed: {response.status}")

            result = await response.json()
            if result.get("code") != 200:
                raise UltraloqApiError(f"Online check request failed: {result}")

            data = result.get("data", {})
            ble_online = data.get("ble", 0) == 1
            remote_online = data.get("remote", 0) == 1
            
            return {
                "ble_online": ble_online,
                "remote_online": remote_online,
                "is_online": ble_online and remote_online,
                "raw_data": data
            }

    async def lock(self, device_uuid: str, user_uid: int) -> bool:
        """Lock the device."""
        return await self._send_lock_command(device_uuid, user_uid, "lock/lock", "LOCK")

    async def unlock(self, device_uuid: str, user_uid: int) -> bool:
        """Unlock the device."""
        return await self._send_lock_command(device_uuid, user_uid, "lock/unlock", "UNLOCK")

    async def _send_lock_command(self, device_uuid: str, user_uid: int, topic: str, action: str) -> bool:
        """Send specific lock command (lock/unlock)."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated")

        # SKIP online check for now to match HAR exactly
        print(f"Skipping online check - proceeding directly with {action}")

        # Use default headers for the request (matching HAR exactly)
        headers = {
            "connection": "keep-alive",
            "platform": "2",
            "x-stage": "Release",
            "x-api-version": "3.3",
            "x-build": "Release", 
            "user-agent": USER_AGENT,
            "content-type": "application/x-www-form-urlencoded; charset=utf-8",
            "accept-encoding": "gzip",
        }
        
        # Create lock command data
        import time
        command_data = {
            "device_uuid": device_uuid,
            "payload": {
                "param": str(user_uid),  # Use the actual user UID from device data
                "info": 8
            },
            "timestamp": int(time.time()),
            "topic": topic
        }
        
        # Create form data
        form_data = {
            "token": self._api_token,
            "data": json.dumps(command_data)
        }

        print(f"DEBUG: {action} request URL: {DEVICE_TOGGLE_URL}")
        print(f"DEBUG: {action} request headers: {headers}")
        print(f"DEBUG: {action} request data: {command_data}")
        print(f"DEBUG: {action} JSON string: {json.dumps(command_data)}")
        print(f"DEBUG: {action} form data: {form_data}")

        async with self._session.post(
            DEVICE_TOGGLE_URL, data=form_data, headers=headers
        ) as response:
            print(f"DEBUG: {action} response status: {response.status}")
            print(f"DEBUG: {action} response headers: {dict(response.headers)}")
            
            response_text = await response.text()
            print(f"DEBUG: {action} response body: {response_text}")
            
            if response.status != 200:
                raise UltraloqApiError(f"{action} request failed: {response.status}")

            result = await response.json(content_type=None)
            print(f"DEBUG: {action} parsed JSON: {result}")
            
            if result.get("code") != 200:
                raise UltraloqApiError(f"{action} request failed: {result}")

            # Wait a moment and verify the state actually changed
            import asyncio
            print("⏳ Waiting 3 seconds to verify state change...")
            await asyncio.sleep(3)
            
            try:
                current_status = await self.get_lock_status(device_uuid)
                current_state = 'LOCKED' if current_status['is_locked'] else 'UNLOCKED'
                print(f"DEBUG: Status after {action}: {current_state}")
                
                # Verify the lock state matches the expected action
                expected_locked = (action == "LOCK")
                actual_locked = current_status.get("is_locked", False)
                
                if actual_locked == expected_locked:
                    print(f"✅ {action} command succeeded - lock state is correct")
                    return True
                else:
                    expected_state = "LOCKED" if expected_locked else "UNLOCKED"
                    actual_state = "LOCKED" if actual_locked else "UNLOCKED"
                    error_msg = f"❌ {action} command failed - expected {expected_state}, got {actual_state}"
                    print(error_msg)
                    raise UltraloqApiError(error_msg)
                    
            except UltraloqApiError:
                # Re-raise API errors (including our state verification error)
                raise
            except Exception as status_err:
                print(f"⚠️ Could not verify lock status after {action}: {status_err}")
                # Still return True since the API call succeeded, just couldn't verify
                return True