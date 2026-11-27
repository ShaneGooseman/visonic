"""Transport layer (TCP socket and Serial/USB via serialx) for Visonic integration."""

from __future__ import annotations

import asyncio
from functools import partial
import logging
import socket
from typing import Any

import aioesphomeapi
import serialx
from serialx import create_serial_connection

from .pyvisonic import VisonicProtocol

_LOGGER = logging.getLogger(__name__)


class ClientVisonicProtocol(asyncio.Protocol):
    """Bridge asyncio.Protocol data stream to VisonicProtocol."""

    def __init__(self, vp: VisonicProtocol, client: Any) -> None:
        self._transport: asyncio.Transport | None = None
        self.vp: VisonicProtocol = vp
        self.client: Any = client

    def data_received(self, data: bytes) -> None:
        if self.vp is not None and self._transport is not None:
            self.vp.data_received(data)

    def connection_made(self, transport: asyncio.Transport) -> None:
        p = transport.get_protocol()
        if self.client is None or self.client.visonicProtocol is not self.vp or p is not self:
            _LOGGER.debug("[ClientVisonicProtocol] connection_made for an orphaned protocol, closing transport")
            transport.close()
            return
        _LOGGER.debug("[ClientVisonicProtocol] connection_made")
        self._transport = transport
        self.vp.setTransportConnection(self._transport)

    def connection_lost(self, exc: Exception | None) -> None:
        self.vp.setTransportConnection(None)
        if self.client is not None:
            _LOGGER.debug("[ClientVisonicProtocol] connection_lost, stopping transport and calling client handler")
            self.client.connection_lost(exc)
        self.client = None
        self._transport = None

    def close(self) -> None:
        # Clear client before closing transport so connection_lost does not trigger reconnect callback.
        self.client = None
        if self._transport is not None:
            _LOGGER.debug("[ClientVisonicProtocol] protocol closing down => closing transport")
            self._transport.close()
        self._transport = None


def create_tcp_socket_connection(address: str, port: int) -> socket.socket | None:
    """Create a TCP socket to the panel adapter (intended to run in an executor thread)."""
    sock = None
    try:
        _LOGGER.debug("Creating TCP Connection, Creating socket and setting socket options")
        if ":" in address:
            family = socket.AF_INET6
            timeout = 5.0
        else:
            family = socket.AF_INET
            timeout = 1.0

        sock = socket.socket(family, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setblocking(True)
        sock.settimeout(timeout)

        _LOGGER.debug("Creating TCP %s Connection", family.name)
        sock.connect((address, port))

        sock.settimeout(1.0)
        try:
            sock.recv(10000)
            _LOGGER.debug("Creating TCP Connection, Buffer Flushed and Received some data!")
        except socket.timeout:
            pass

        sock.settimeout(None)
        return sock
    except socket.error as err:
        _LOGGER.debug("Setting TCP socket Options Exception %s", err)
        if sock is not None:
            sock.close()
    return None


async def async_create_tcp_connection(
    hass: Any,
    vp: VisonicProtocol,
    client: Any,
    address: str,
    port: int | str,
) -> ClientVisonicProtocol | None:
    """Create an async TCP protocol connection without blocking the event loop."""
    try:
        sock = await hass.async_add_executor_job(create_tcp_socket_connection, address, int(port))
        if sock is not None:
            _, protocol = await hass.loop.create_connection(
                lambda: ClientVisonicProtocol(vp=vp, client=client),
                sock=sock,
            )
            return protocol
    except Exception as ex:
        client.logstate_warning(f"Creating TCP Connection, TCP Connection Exception {ex}")
    client.logstate_info("Creating TCP has a Connection problem, returning not-connected condition")
    return None


async def async_create_usb_connection(
    hass: Any,
    vp: VisonicProtocol,
    client: Any,
    path: str,
    baud: int,
) -> ClientVisonicProtocol | None:
    """Create an async serial/USB protocol connection via serialx."""
    protocol = partial(
        ClientVisonicProtocol,
        vp=vp,
        client=client,
    )
    try:
        client.logstate_debug(f"Creating USB Connection {path=} {baud=}")
        _, proto = await create_serial_connection(
            hass.loop,
            protocol,
            path,
            baud,
        )
    except (aioesphomeapi.core.APIConnectionError, serialx.common.SerialException) as ex:
        client.logstate_debug(f"    Failed to create it, connection error {ex}")
    except Exception as ex:
        client.logstate_warning(f"Creating USB Connection, USB Connection Exception {ex}")
    else:
        return proto

    client.logstate_info("Creating USB Connection problem, returning not-connected condition")
    return None
