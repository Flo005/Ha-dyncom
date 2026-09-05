"""The Dyn.com Dynamic DNS integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DynComAuthError, DynComError, async_update_dns
from .const import CONF_HOSTNAME, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


class DynComDataUpdateCoordinator(DataUpdateCoordinator[dict[str, str | None]]):
    """Coordinator that periodically pushes the current IP to Dyn.com."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval),
        )
        self.entry = entry
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict[str, str | None]:
        """Send the update request and return the resulting status."""
        data = self.entry.data
        try:
            status, ip = await async_update_dns(
                self.session,
                data[CONF_HOSTNAME],
                data[CONF_USERNAME],
                data[CONF_PASSWORD],
            )
        except DynComAuthError as err:
            raise ConfigEntryAuthFailed("Invalid Dyn.com credentials") from err
        except DynComError as err:
            raise UpdateFailed(str(err)) from err

        return {"status": status, "ip": ip}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dyn.com Dynamic DNS from a config entry."""
    coordinator = DynComDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
