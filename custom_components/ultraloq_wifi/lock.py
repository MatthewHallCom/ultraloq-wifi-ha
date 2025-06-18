"""Lock platform for Ultraloq Wifi integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import UltraloqDataUpdateCoordinator
from .entity import UltraloqEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up lock entities from a config entry."""
    coordinator: UltraloqDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    # Get initial lock data to create entities
    await coordinator.async_config_entry_first_refresh()
    
    # Create lock entities for all discovered locks
    entities = []
    for device_uuid in coordinator.data:
        entities.append(UltraloqLock(coordinator, device_uuid))
    
    async_add_entities(entities)


class UltraloqLock(UltraloqEntity, LockEntity):
    """Representation of an Ultraloq lock."""

    _attr_supported_features = LockEntityFeature.OPEN

    def __init__(
        self,
        coordinator: UltraloqDataUpdateCoordinator,
        device_uuid: str,
    ) -> None:
        """Initialize the lock."""
        super().__init__(coordinator, device_uuid)
        self._attr_name = None  # Use device name from device_info

    @property
    def unique_id(self) -> str:
        """Return unique ID for the lock entity."""
        return f"{DOMAIN}_{self._device_uuid}_lock"

    @property
    def is_locked(self) -> bool | None:
        """Return true if the lock is locked."""
        device_data = self.device_data
        if not device_data:
            return None
        return device_data.get("is_locked", False)

    @property
    def is_locking(self) -> bool | None:
        """Return true if the lock is locking."""
        # Ultraloq API doesn't provide intermediate states
        return None

    @property
    def is_unlocking(self) -> bool | None:
        """Return true if the lock is unlocking."""
        # Ultraloq API doesn't provide intermediate states
        return None

    @property
    def is_jammed(self) -> bool | None:
        """Return true if the lock is jammed."""
        device_data = self.device_data
        if not device_data:
            return None
        return device_data.get("is_jam", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device_data = self.device_data
        if not device_data:
            return {}

        attributes = {
            "battery_level": device_data.get("battery", 0),
            "wifi_strength": device_data.get("wifi_strength", 0),
            "ble_strength": device_data.get("ble_strength", 0),
            "net_strength": device_data.get("net_strength", 0),
            "version": device_data.get("version", ""),
            "sleep_mode": device_data.get("sleep", False),
            "raw_lock_state": device_data.get("raw_lock_state", 0),
        }

        # Add timestamp information if available
        if "timestamp" in device_data:
            attributes["last_update"] = device_data["timestamp"]
        if "lasttime" in device_data:
            attributes["last_activity"] = device_data["lasttime"]

        return attributes

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        current_state = self.is_locked
        if current_state is True:
            _LOGGER.info("Lock %s is already locked", self._device_uuid)
            return

        _LOGGER.info("Locking %s", self._device_uuid)
        try:
            await self.coordinator.api_client.lock(self._device_uuid, self.coordinator.address_id)
            # Request immediate refresh to update state
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to lock %s: %s", self._device_uuid, err)
            raise

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        current_state = self.is_locked
        if current_state is False:
            _LOGGER.info("Lock %s is already unlocked", self._device_uuid)
            return

        _LOGGER.info("Unlocking %s", self._device_uuid)
        try:
            await self.coordinator.api_client.unlock(self._device_uuid, self.coordinator.address_id)
            # Request immediate refresh to update state
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to unlock %s: %s", self._device_uuid, err)
            raise

    async def async_open(self, **kwargs: Any) -> None:
        """Open the lock."""
        await self.async_unlock(**kwargs)