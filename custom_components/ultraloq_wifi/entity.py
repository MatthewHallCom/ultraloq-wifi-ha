"""Base entity for Ultraloq Wifi integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UltraloqDataUpdateCoordinator


class UltraloqEntity(CoordinatorEntity[UltraloqDataUpdateCoordinator]):
    """Base entity for Ultraloq devices."""

    def __init__(
        self,
        coordinator: UltraloqDataUpdateCoordinator,
        device_uuid: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_uuid = device_uuid
        self._attr_has_entity_name = True

    @property
    def device_data(self) -> dict:
        """Return device data from coordinator."""
        return self.coordinator.data.get(self._device_uuid, {})

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_data = self.device_data
        
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_uuid)},
            name=device_data.get("name", "Ultraloq Lock"),
            manufacturer="U-tec",
            model=device_data.get("model", "U-Bolt"),
            sw_version=device_data.get("version"),
            serial_number=device_data.get("uuid"),
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for the entity."""
        return f"{DOMAIN}_{self._device_uuid}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        
        device_data = self.device_data
        return device_data.get("online", False)