"""
Defines host network helpers for the launcher

The frontend container builds a self-signed TLS certificate for the host's LAN
IPv4 at runtime, so the launcher must resolve and pass that address through as
`HOST_LAN_IP`
"""

import logging
import socket

LOGGER = logging.getLogger(__name__)


def get_host_lan_ip() -> str:
    """
    Resolves the host's primary LAN IPv4 address

    Opens a throw-away UDP socket toward a public address to discover which
    local interface the OS would route through. No packets are sent

    Returns:
        The primary LAN IPv4 address, or `127.0.0.1` if it cannot be resolved
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip: str = sock.getsockname()[0]
        return ip
    except OSError as exc:
        LOGGER.warning(f"Could Not Resolve LAN IP, Falling Back : {exc}")
        return "127.0.0.1"
    finally:
        sock.close()
