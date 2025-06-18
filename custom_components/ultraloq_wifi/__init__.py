"""The Ultraloq Wifi integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import UltraloqApiClient
from .const import CONF_ADDRESS_ID, CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import UltraloqDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.LOCK]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ultraloq Wifi from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Get configuration data
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    address_id = int(entry.data[CONF_ADDRESS_ID])
    
    # Create API client
    session = async_get_clientsession(hass)
    api_client = UltraloqApiClient(session)
    
    # Authenticate
    await api_client.authenticate(email, password)
    
    # Create data update coordinator
    coordinator = UltraloqDataUpdateCoordinator(hass, api_client, address_id)
    
    # Store coordinator and API client
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api_client": api_client,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok