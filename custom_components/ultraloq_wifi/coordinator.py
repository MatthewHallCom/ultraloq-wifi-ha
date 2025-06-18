"""Data update coordinator for Ultraloq Wifi integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import UltraloqApiClient, UltraloqApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)


class UltraloqDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Ultraloq data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: UltraloqApiClient,
        address_id: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api_client = api_client
        self.address_id = address_id
        self._lock_uuids: list[str] = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get list of locks if we don't have them
            if not self._lock_uuids:
                locks = await self.api_client.get_locks(self.address_id)
                self._lock_uuids = [lock["uuid"] for lock in locks if lock.get("uuid")]
                _LOGGER.debug("Found %d locks: %s", len(self._lock_uuids), self._lock_uuids)

            # Get status for each lock
            lock_data = {}
            
            # Use asyncio.gather to fetch all lock statuses concurrently
            if self._lock_uuids:
                tasks = [
                    self.api_client.get_lock_status(uuid)
                    for uuid in self._lock_uuids
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for uuid, result in zip(self._lock_uuids, results):
                    if isinstance(result, Exception):
                        _LOGGER.warning("Failed to get status for lock %s: %s", uuid, result)
                        # Keep existing data if available
                        if uuid in self.data:
                            lock_data[uuid] = self.data[uuid]
                    else:
                        lock_data[uuid] = result
                        _LOGGER.debug("Updated status for lock %s", uuid)

            return lock_data

        except UltraloqApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_refresh_locks(self) -> None:
        """Refresh the list of locks."""
        self._lock_uuids = []
        await self.async_refresh()