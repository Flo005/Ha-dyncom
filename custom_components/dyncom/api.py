"""Minimal DynDNS2 client for updating a Dyn.com hostname."""

from __future__ import annotations

import logging

import aiohttp

from .const import UPDATE_URL

_LOGGER = logging.getLogger(__name__)

# Statuses returned by the DynDNS2 protocol that indicate success.
SUCCESS_STATUSES = ("good", "nochg")


class DynComError(Exception):
    """Raised when a Dyn.com update request fails."""


class DynComAuthError(DynComError):
    """Raised when Dyn.com rejects the supplied credentials."""


async def async_update_dns(
    session: aiohttp.ClientSession,
    hostname: str,
    username: str,
    password: str,
) -> tuple[str, str | None]:
    """Send a DynDNS2 update request for hostname.

    No `myip` parameter is sent, so Dyn.com determines the IP from the
    request's source address. Returns a (status, ip) tuple on success.
    """
    try:
        async with session.get(
            UPDATE_URL,
            params={"hostname": hostname},
            auth=aiohttp.BasicAuth(username, password),
            headers={"User-Agent": "HomeAssistant-dyncom/1.0"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            text = (await response.text()).strip()
    except aiohttp.ClientError as err:
        raise DynComError(f"Error communicating with Dyn.com: {err}") from err

    _LOGGER.debug("Dyn.com response for %s: %s", hostname, text)

    parts = text.split()
    status = parts[0] if parts else ""
    ip = parts[1] if len(parts) > 1 else None

    if status == "badauth":
        raise DynComAuthError("Invalid Dyn.com username or password")
    if status in SUCCESS_STATUSES:
        return status, ip

    raise DynComError(f"Dyn.com update failed: {text or response.status}")
