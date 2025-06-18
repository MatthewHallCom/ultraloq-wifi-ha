"""API client for Ultraloq Wifi integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp
from aiohttp import ClientSession

from .const import (
    ADDRESS_URL,
    APP_ID,
    CLIENT_ID,
    DEVICE_LIST_URL,
    DEVICE_ONLINE_CHECK_URL,
    DEVICE_STATUS_URL,
    DEVICE_TOGGLE_URL,
    LOGIN_URL,
    TIMEZONE,
    TOKEN_URL,
    USER_AGENT,
    UUID,
    VERSION,
)

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
        
        # Store default headers for use in requests
        self._default_headers = {
            "User-Agent": USER_AGENT,
            "X-Api-Version": "3.3",
            "X-Build": "Release",
            "X-Stage": "Release",
        }

    async def _get_api_token(self) -> str:
        """Get API token from token endpoint."""
        headers = {
            **self._default_headers,
            "Content-Type": "application/json; charset=utf-8",
        }

        data = {
            "appid": APP_ID,
            "clientid": CLIENT_ID,
            "uuid": UUID,
            "version": VERSION,
            "timezone": TIMEZONE,
        }

        _LOGGER.debug("Token request URL: %s", TOKEN_URL)
        _LOGGER.debug("Token request headers: %s", headers)
        _LOGGER.debug("Token request data: %s", data)
        
        # Also print for immediate visibility during testing
        print(f"DEBUG: Token request URL: {TOKEN_URL}")
        print(f"DEBUG: Token request headers: {headers}")
        print(f"DEBUG: Token request data: {data}")

        try:
            async with self._session.post(
                TOKEN_URL,
                json=data,
                headers=headers,
            ) as response:
                _LOGGER.debug("Token response status: %s", response.status)
                _LOGGER.debug("Token response headers: %s", dict(response.headers))
                
                # Also print for immediate visibility
                print(f"DEBUG: Token response status: {response.status}")
                print(f"DEBUG: Token response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    response_text = await response.text()
                    _LOGGER.debug("Token response body: %s", response_text[:200])
                    
                    # Also print for immediate visibility
                    print(f"DEBUG: Token response body: {response_text[:200]}...")
                    
                    try:
                        result = await response.json()
                        _LOGGER.debug("Token parsed JSON: %s", result)
                        print(f"DEBUG: Token parsed JSON: {result}")
                    except Exception as json_err:
                        _LOGGER.error("Failed to parse token JSON: %s", json_err)
                        raise UltraloqApiError(f"Invalid token response format: {response_text[:100]}")
                    if result.get("code") == 200:
                        token_data = result.get("data", {})
                        self._api_token = token_data.get("token")
                        urls = token_data.get("urls", {})
                        self._api_base_url = urls.get("utec")
                        
                        if self._api_token and self._api_base_url:
                            _LOGGER.debug("API token obtained successfully: %s...", self._api_token[:20])
                            return self._api_token
                        else:
                            _LOGGER.error("Missing token or URL in response")
                            raise UltraloqApiError("Invalid token response")
                    else:
                        _LOGGER.error("Token request failed with code %s", result.get("code"))
                        raise UltraloqApiError(f"Token request failed: {result.get('code')}")
                else:
                    response_text = await response.text()
                    _LOGGER.error("Token request failed with status %s: %s", response.status, response_text[:200])
                    raise UltraloqApiError(f"Token request failed with status {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during token request: %s", err)
            raise UltraloqApiError(f"Network error: {err}") from err

    async def authenticate(self, email: str, password: str) -> bool:
        """Authenticate with Ultraloq API using two-step process."""
        _LOGGER.debug("Starting authentication for email: %s", email)
        
        # Step 1: Get API token
        await self._get_api_token()
        
        if not self._api_token or not self._api_base_url:
            raise UltraloqApiError("Failed to obtain API token")

        _LOGGER.debug("Token obtained: %s..., Base URL: %s", 
                     self._api_token[:20] if self._api_token else "None", 
                     self._api_base_url)

        # Step 2: Use token to authenticate with credentials
        headers = {
            **self._default_headers,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }

        # Form-encoded data with JSON-encoded credentials
        credentials_json = json.dumps({
            "email": email,
            "password": password,
        })
        
        form_data = {
            "data": credentials_json,
            "token": self._api_token,
        }

        _LOGGER.debug("Login request URL: %s", LOGIN_URL)
        _LOGGER.debug("Login request headers: %s", headers)
        _LOGGER.debug("Login request data: %s", form_data)
        
        # Also print for immediate visibility
        print(f"DEBUG: Login request URL: {LOGIN_URL}")
        print(f"DEBUG: Login request headers: {headers}")
        print(f"DEBUG: Login request data: {form_data}")

        try:
            async with self._session.post(
                LOGIN_URL,
                data=form_data,
                headers=headers,
            ) as response:
                _LOGGER.debug("Login response status: %s", response.status)
                _LOGGER.debug("Login response headers: %s", dict(response.headers))
                
                # Also print for immediate visibility
                print(f"DEBUG: Login response status: {response.status}")
                print(f"DEBUG: Login response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    response_text = await response.text()
                    _LOGGER.debug("Login response body: %s", response_text[:200])
                    
                    try:
                        result = await response.json()
                        _LOGGER.debug("Login parsed JSON: %s", result)
                        
                        # Check if login was successful
                        if result.get("code") == 200:
                            data = result.get("data", {})
                            # Login successful - user data received, use API token for subsequent requests
                            self._access_token = self._api_token
                            _LOGGER.debug("Authentication successful, user UUID: %s", data.get("uuid"))
                            _LOGGER.debug("Using API token as access token: %s...", self._access_token[:20])
                            print(f"DEBUG: Login successful, user UUID: {data.get('uuid')}")
                            print(f"DEBUG: Using API token as access token: {self._access_token[:20]}...")
                            return True
                        elif result.get("code") == 401:
                            _LOGGER.error("Invalid credentials")
                            raise UltraloqAuthError("Invalid email or password")
                        else:
                            _LOGGER.error("Login failed with code %s", result.get("code"))
                    except Exception as json_err:
                        _LOGGER.error("Failed to parse login JSON response: %s", json_err)
                        raise UltraloqAuthError(f"Invalid login response format: {response_text[:100]}")
                else:
                    response_text = await response.text()
                    _LOGGER.error("Login request failed with status %s: %s", response.status, response_text[:200])
                    raise UltraloqAuthError(f"Login request failed with status {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during authentication: %s", err)
            raise UltraloqApiError(f"Network error: {err}") from err

    async def get_addresses(self) -> list[dict[str, Any]]:
        """Get list of addresses/locations."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated - no API token")

        headers = {
            **self._default_headers,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        form_data = {
            "token": self._api_token,
        }

        try:
            async with self._session.post(
                ADDRESS_URL,
                data=form_data,
                headers=headers,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 200:
                        return result.get("data", [])
                    else:
                        _LOGGER.error("Address request failed with code %s", result.get("code"))
                        raise UltraloqApiError(f"Address request failed: {result.get('description', 'Unknown error')}")
                else:
                    _LOGGER.error("Address request failed with status %s", response.status)
                    raise UltraloqApiError(f"Address request failed with status {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error getting addresses: %s", err)
            raise UltraloqApiError(f"Network error: {err}") from err

    async def get_devices(self, address_id: int) -> list[dict[str, Any]]:
        """Get list of devices for a specific address."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated - no API token")

        headers = self._default_headers.copy()

        # Create multipart form data
        data = aiohttp.FormData()
        data.add_field("token", self._api_token)
        data.add_field("data", json.dumps({"address_id": address_id}))

        try:
            async with self._session.post(
                DEVICE_LIST_URL,
                data=data,
                headers=headers,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 200:
                        return result.get("data", [])
                    else:
                        _LOGGER.error("Device list request failed with code %s", result.get("code"))
                        raise UltraloqApiError(f"Device list request failed: {result.get('description', 'Unknown error')}")
                else:
                    _LOGGER.error("Device list request failed with status %s", response.status)
                    raise UltraloqApiError(f"Device list request failed with status {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error getting devices: %s", err)
            raise UltraloqApiError(f"Network error: {err}") from err

    async def get_locks(self, address_id: int) -> list[dict[str, Any]]:
        """Get list of U-Bolt locks for a specific address."""
        device_data = await self.get_devices(address_id)
        
        locks = []
        
        # Iterate through each entry in the data array
        for entry in device_data:
            devices = entry.get("devices", [])
            
            # Iterate through each device in the devices array
            for device in devices:
                model = device.get("model", "")
                
                # Filter for U-Bolt model locks
                if model == "U-Bolt":
                    user_data = device.get("user", {})
                    # Extract the lock information we need
                    lock_info = {
                        "uuid": device.get("uuid"),
                        "name": device.get("name"),
                        "model": device.get("model"),
                        "status": device.get("status"),
                        "params": device.get("params", {}),
                        "bridge": device.get("bridge", {}),
                        "user": user_data,
                        "user_uid": user_data.get("uid"),  # Store the user UID for lock commands
                        "entry_id": entry.get("id"),  # Store the parent entry ID
                    }
                    locks.append(lock_info)
        
        return locks

    async def get_device_user_uid(self, uuid: str, address_id: int) -> int:
        """Get the user UID for a specific device UUID."""
        device_data = await self.get_devices(address_id)
        
        # Search through all entries and devices to find the matching UUID
        for entry in device_data:
            devices = entry.get("devices", [])
            for device in devices:
                if device.get("uuid") == uuid:
                    user_data = device.get("user", {})
                    user_uid = user_data.get("uid")
                    if user_uid is not None:
                        return user_uid
                    else:
                        raise UltraloqApiError(f"No user UID found for device {uuid}")
        
        raise UltraloqApiError(f"Device {uuid} not found")

    async def get_lock_status(self, uuid: str) -> dict[str, Any]:
        """Get real-time status of a specific lock."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated - no API token")

        headers = self._default_headers.copy()

        # Create multipart form data
        data = aiohttp.FormData()
        data.add_field("token", self._api_token)
        data.add_field("data", json.dumps({"uuid": uuid}))

        try:
            async with self._session.post(
                DEVICE_STATUS_URL,
                data=data,
                headers=headers,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 200:
                        status_data = result.get("data", {})
                        
                        # Parse lock state (1 = unlocked/open, 2 = locked/closed)
                        is_locked_value = status_data.get("is_locked", 0)
                        is_locked = is_locked_value == 2
                        is_unlocked = is_locked_value == 1
                        
                        # Return structured status information
                        return {
                            "uuid": status_data.get("uuid"),
                            "model": status_data.get("model"),
                            "is_locked": is_locked,
                            "is_unlocked": is_unlocked,
                            "raw_lock_state": is_locked_value,
                            "online": bool(status_data.get("online", 0)),
                            "battery": status_data.get("battery", 0),
                            "wifi_strength": status_data.get("wifi_strength", 0),
                            "ble_strength": status_data.get("ble_strength", 0),
                            "net_strength": status_data.get("net_strength", 0),
                            "version": status_data.get("version", ""),
                            "is_jam": bool(status_data.get("is_jam", 0)),
                            "sleep": bool(status_data.get("sleep", 0)),
                            "timestamp": status_data.get("timestamp", 0),
                            "lasttime": status_data.get("lasttime", 0),
                        }
                    else:
                        _LOGGER.error("Lock status request failed with code %s", result.get("code"))
                        raise UltraloqApiError(f"Lock status request failed: {result.get('description', 'Unknown error')}")
                else:
                    _LOGGER.error("Lock status request failed with status %s", response.status)
                    raise UltraloqApiError(f"Lock status request failed with status {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error getting lock status: %s", err)
            raise UltraloqApiError(f"Network error: {err}") from err

    async def check_lock_online(self, uuid: str) -> dict[str, Any]:
        """Check if lock is online (both BLE and remote connectivity)."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated - no API token")

        headers = {
            **self._default_headers,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }

        # Create form data with JSON-encoded UUID
        form_data = {
            "token": self._api_token,
            "data": json.dumps({"uuid": uuid})
        }

        _LOGGER.debug("Check lock online request URL: %s", DEVICE_ONLINE_CHECK_URL)
        _LOGGER.debug("Check lock online request data: %s", form_data)

        try:
            async with self._session.post(
                DEVICE_ONLINE_CHECK_URL,
                data=form_data,
                headers=headers,
            ) as response:
                _LOGGER.debug("Check lock online response status: %s", response.status)
                
                if response.status == 200:
                    response_text = await response.text()
                    _LOGGER.debug("Check lock online response body: %s", response_text)
                    
                    try:
                        result = await response.json()
                        _LOGGER.debug("Check lock online parsed JSON: %s", result)
                        
                        if result.get("code") == 200:
                            data = result.get("data", {})
                            ble_online = data.get("ble", 0) == 1
                            remote_online = data.get("remote", 0) == 1
                            
                            return {
                                "ble_online": ble_online,
                                "remote_online": remote_online,
                                "is_online": ble_online and remote_online,
                                "raw_data": data
                            }
                        else:
                            _LOGGER.error("Check lock online failed with code %s", result.get("code"))
                            raise UltraloqApiError(f"Check lock online failed: {result.get('description', 'Unknown error')}")
                    except Exception as json_err:
                        _LOGGER.error("Failed to parse online check response JSON: %s", json_err)
                        raise UltraloqApiError(f"Invalid online check response format: {response_text[:100]}")
                else:
                    response_text = await response.text()
                    _LOGGER.error("Check lock online request failed with status %s: %s", response.status, response_text[:200])
                    raise UltraloqApiError(f"Check lock online request failed with status {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error checking lock online status: %s", err)
            raise UltraloqApiError(f"Network error: {err}") from err


    async def lock(self, uuid: str, address_id: int) -> bool:
        """Lock the device."""
        return await self._send_lock_command(uuid, address_id, "lock/lock", "LOCK")

    async def unlock(self, uuid: str, address_id: int) -> bool:
        """Unlock the device."""
        return await self._send_lock_command(uuid, address_id, "lock/unlock", "UNLOCK")

    async def _send_lock_command(self, uuid: str, address_id: int, topic: str, action: str) -> bool:
        """Send a specific lock command (lock or unlock)."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated - no API token")

        # Check if lock is online before attempting command
        try:
            online_status = await self.check_lock_online(uuid)
            if not online_status.get("is_online", False):
                ble_online = online_status.get("ble_online", False)
                remote_online = online_status.get("remote_online", False)
                _LOGGER.error("Lock is not online - BLE: %s, Remote: %s", ble_online, remote_online)
                raise UltraloqApiError(f"Lock is not online (BLE: {ble_online}, Remote: {remote_online})")
            else:
                _LOGGER.debug("Lock is online - proceeding with %s", action)
        except UltraloqApiError:
            raise
        except Exception as online_err:
            _LOGGER.warning("Could not check lock online status: %s - proceeding anyway", online_err)

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

        # Get the user UID for this device
        try:
            user_uid = await self.get_device_user_uid(uuid, address_id)
            _LOGGER.debug("Using user UID %s for device %s", user_uid, uuid)
        except Exception as uid_err:
            _LOGGER.error("Could not get user UID for device %s: %s", uuid, uid_err)
            raise UltraloqApiError(f"Could not get user UID for device: {uid_err}")

        # Create lock command data
        import time
        command_data = {
            "device_uuid": uuid,
            "payload": {
                "param": str(user_uid),  # Use the actual user UID from device data
                "info": 8
            },
            "timestamp": int(time.time()),
            "topic": topic
        }
        
        form_data = {
            "token": self._api_token,
            "data": json.dumps(command_data)
        }

        _LOGGER.debug("%s request URL: %s", action, DEVICE_TOGGLE_URL)
        _LOGGER.debug("%s request data: %s", action, command_data)
        print(f"DEBUG: {action} request URL: {DEVICE_TOGGLE_URL}")
        print(f"DEBUG: {action} request data: {command_data}")

        try:
            async with self._session.post(
                DEVICE_TOGGLE_URL,
                data=form_data,
                headers=headers,
            ) as response:
                _LOGGER.debug("%s response status: %s", action, response.status)
                print(f"DEBUG: {action} response status: {response.status}")
                
                if response.status == 200:
                    response_text = await response.text()
                    _LOGGER.debug("%s response body: %s", action, response_text)
                    print(f"DEBUG: {action} response body: {response_text}")
                    
                    try:
                        result = await response.json()
                        _LOGGER.debug("%s parsed JSON: %s", action, result)
                        print(f"DEBUG: {action} parsed JSON: {result}")
                        
                        if result.get("code") == 200:
                            _LOGGER.debug("%s API call successful for %s", action, uuid)
                            print(f"DEBUG: {action} API call successful for {uuid}")
                            
                            # Wait a moment and verify the state actually changed
                            import asyncio
                            await asyncio.sleep(2)
                            
                            try:
                                current_status = await self.get_lock_status(uuid)
                                _LOGGER.debug("Lock status after %s: %s", action, current_status)
                                print(f"DEBUG: Lock status after {action}: {current_status}")
                                
                                # Verify the lock state matches the expected action
                                expected_locked = (action == "LOCK")
                                actual_locked = current_status.get("is_locked", False)
                                
                                if actual_locked == expected_locked:
                                    _LOGGER.debug("%s command succeeded - lock state is correct", action)
                                    print(f"DEBUG: {action} command succeeded - lock state is correct")
                                    return True
                                else:
                                    expected_state = "LOCKED" if expected_locked else "UNLOCKED"
                                    actual_state = "LOCKED" if actual_locked else "UNLOCKED"
                                    error_msg = f"{action} command failed - expected {expected_state}, got {actual_state}"
                                    _LOGGER.error(error_msg)
                                    print(f"DEBUG: {error_msg}")
                                    raise UltraloqApiError(error_msg)
                                    
                            except UltraloqApiError:
                                # Re-raise API errors (including our state verification error)
                                raise
                            except Exception as status_err:
                                _LOGGER.warning("Could not verify lock status after %s: %s", action, status_err)
                                print(f"DEBUG: Could not verify lock status after {action}: {status_err}")
                                # Still return True since the API call succeeded, just couldn't verify
                                return True
                        else:
                            _LOGGER.error("%s failed with code %s for %s", action, result.get("code"), uuid)
                            raise UltraloqApiError(f"{action} failed: {result.get('description', 'Unknown error')}")
                    except Exception as json_err:
                        _LOGGER.error("Failed to parse %s response JSON: %s", action, json_err)
                        raise UltraloqApiError(f"Invalid {action} response format: {response_text[:100]}")
                else:
                    response_text = await response.text()
                    _LOGGER.error("%s request failed with status %s for %s: %s", action, response.status, uuid, response_text[:200])
                    raise UltraloqApiError(f"{action} request failed with status {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during %s for %s: %s", action, uuid, err)
            raise UltraloqApiError(f"Network error: {err}") from err

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._access_token is not None