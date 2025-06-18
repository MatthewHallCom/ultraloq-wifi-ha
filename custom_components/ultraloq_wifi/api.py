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
                    # Extract the lock information we need
                    lock_info = {
                        "uuid": device.get("uuid"),
                        "name": device.get("name"),
                        "model": device.get("model"),
                        "status": device.get("status"),
                        "params": device.get("params", {}),
                        "bridge": device.get("bridge", {}),
                        "user": device.get("user", {}),
                        "entry_id": entry.get("id"),  # Store the parent entry ID
                    }
                    locks.append(lock_info)
        
        return locks

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

    async def toggle_lock(self, uuid: str) -> bool:
        """Toggle lock state (lock/unlock)."""
        if not self._api_token:
            raise UltraloqAuthError("Not authenticated - no API token")

        headers = {
            **self._default_headers,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Prepare form data with UUID
        form_data = {
            "token": self._api_token,
            "data": json.dumps({"uuid": uuid}),
        }

        try:
            async with self._session.post(
                DEVICE_TOGGLE_URL,
                data=form_data,
                headers=headers,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 200:
                        _LOGGER.debug("Lock toggle successful for %s", uuid)
                        return True
                    else:
                        _LOGGER.error("Lock toggle failed with code %s for %s", result.get("code"), uuid)
                        raise UltraloqApiError(f"Lock toggle failed: {result.get('description', 'Unknown error')}")
                else:
                    _LOGGER.error("Lock toggle request failed with status %s for %s", response.status, uuid)
                    raise UltraloqApiError(f"Lock toggle request failed with status {response.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during lock toggle for %s: %s", uuid, err)
            raise UltraloqApiError(f"Network error: {err}") from err

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._access_token is not None