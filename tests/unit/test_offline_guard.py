"""The suite runs offline (M4c): a non-loopback connect fails, loopback works."""

from __future__ import annotations

import os
import socket

import pytest


@pytest.mark.skipif(
    os.environ.get("NEXUS_RECORD_CASSETTES") == "1" or os.environ.get("NEXUS_ALLOW_NETWORK") == "1",
    reason="the guard is lifted on purpose",
)
def test_a_test_cannot_reach_the_internet():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock, pytest.raises(RuntimeError, match="NETWORK_BLOCKED"):
        sock.connect(("93.184.216.34", 443))


def test_loopback_is_allowed():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(server.getsockname())
