"""Utility helpers for the factory UI simulator."""

import socket
import logging


def resolve_address(hostname: str) -> str:
    """Resolve hostname to an IP address, fallback to the original hostname.

    Keeps behavior simple and robust for the simulator's use in dev environments.
    """
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        logging.debug(f"Could not resolve '{hostname}', using as-is")
        return hostname
