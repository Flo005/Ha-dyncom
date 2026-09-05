"""Sensor platform for the Dyn.com Dynamic DNS integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DynComDataUpdateCoordinator
from .const import CONF_HOSTNAME, DOMAIN

STATUS_LABELS = {
    "good": "Updated",
    "nochg": "No change",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dyn.com status sensor from a config entry."""
    coordinator: DynComDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DynComStatusSensor(coordinator, entry)])


class DynComStatusSensor(CoordinatorEntity[DynComDataUpdateCoordinator], SensorEntity):
    """Reports the outcome of the last Dyn.com update request."""

    _attr_has_entity_name = True
    _attr_translation_key = "dyncom_status"
    _attr_icon = "mdi:ip-network"

    def __init__(
        self, coordinator: DynComDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._hostname = entry.data[CONF_HOSTNAME]
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=self._hostname,
            manufacturer="Dyn.com",
            model="Dynamic DNS",
        )

    @property
    def native_value(self) -> str | None:
        """Return the last update status."""
        if not self.coordinator.data:
            return None
        status = self.coordinator.data.get("status")
        return STATUS_LABELS.get(status, status)

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return the last IP address that was reported to Dyn.com."""
        if not self.coordinator.data:
            return {}
        return {
            "ip_address": self.coordinator.data.get("ip"),
            "hostname": self._hostname,
        }
