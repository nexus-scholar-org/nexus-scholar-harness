"""H-b8-small-faults, fault 2: two harmless lines leave the engine's log, nothing else does.

Testing the installed 1.1.0b8 on Windows: a browser dropping a connection wrote a
`ConnectionResetError: [WinError 10054]` traceback from the proactor loop's
`_call_connection_lost`, and a stop with a tab open wrote "Cancel 0 running task(s),
timeout graceful shutdown exceeded". The filters must survive uvicorn's own logging
set-up in both starts (terminal: uvicorn's default `log_config`; no console: `None`).
"""

from __future__ import annotations

import asyncio
import logging
import sys

import pytest

from scholar_harness.console import launcher, log_noise


class Keep(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.WARNING)  # not the loop's "Using proactor" debug line
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def kept():
    """A handler on each of the two loggers (a logger's filters run before its handlers)."""
    handler = Keep()
    loggers = [logging.getLogger(name) for name in ("asyncio", "uvicorn.error")]
    saved = [(lg.level, list(lg.filters)) for lg in loggers]
    for lg in loggers:
        lg.addHandler(handler)
        lg.setLevel(logging.DEBUG)
    yield handler
    for lg, (level, filters) in zip(loggers, saved, strict=True):
        lg.removeHandler(handler)
        lg.setLevel(level)
        lg.filters[:] = filters


def _call_connection_lost(exc: BaseException) -> None:
    """Named as the proactor transport's callback, as the real traceback shows it."""
    raise exc


def _log_from_the_loop(callback, *args) -> None:
    """Run a callback on a real event loop: its default exception handler logs to `asyncio`."""
    loop = asyncio.new_event_loop()
    try:
        loop.call_soon(callback, *args)
        loop.run_until_complete(asyncio.sleep(0))
    finally:
        loop.close()


def _windows_reset() -> ConnectionResetError:
    return ConnectionResetError(10054, "An existing connection was forcibly closed by the remote host")


def _messages(handler: Keep) -> list[str]:
    return [r.getMessage() for r in handler.records]


class Transport:
    """The shape of the proactor transport's callback: the protocol first, then the socket in ``finally``."""

    def __init__(self, protocol_error: BaseException | None = None, socket_error: BaseException | None = None):
        self.protocol_error, self.socket_error = protocol_error, socket_error

    def connection_lost(self, exc: BaseException | None) -> None:  # the protocol's own method
        if self.protocol_error is not None:
            raise self.protocol_error

    def _call_connection_lost(self, exc: BaseException | None) -> None:
        try:
            self.connection_lost(exc)
        finally:
            if self.socket_error is not None:
                raise self.socket_error  # the socket's shutdown is a C call: no frame of its own


def test_a_dropped_browser_connection_and_a_stop_that_cancelled_nothing_are_not_logged(kept):
    log_noise.install()
    _log_from_the_loop(_call_connection_lost, _windows_reset())
    _log_from_the_loop(_call_connection_lost, ConnectionAbortedError(10053, "aborted"))
    _log_from_the_loop(Transport(socket_error=_windows_reset())._call_connection_lost, None)
    try:  # a real raise: the record carries the traceback the filter reads
        _call_connection_lost(_windows_reset())
    except ConnectionResetError as error:
        logging.getLogger("asyncio").error(
            "Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)", exc_info=error
        )
    logging.getLogger("uvicorn.error").error("Cancel %s running task(s), timeout graceful shutdown exceeded", 0)
    assert kept.records == []


def test_everything_else_is_still_logged(kept):
    log_noise.install()

    def other_callback() -> None:
        raise RuntimeError("a real fault")

    _log_from_the_loop(other_callback)  # an unrelated asyncio error
    _log_from_the_loop(lambda: _raise(_windows_reset()))  # a reset raised in another callback
    # Review round 1, finding 1 (a): the protocol failed, then the socket reset in `finally`;
    # the real fault rides as the reset's __context__.
    _log_from_the_loop(
        Transport(protocol_error=RuntimeError("protocol fault"), socket_error=_windows_reset())._call_connection_lost, None
    )
    # (b): the reset raised deeper, inside the protocol's own connection_lost.
    _log_from_the_loop(Transport(protocol_error=_windows_reset())._call_connection_lost, None)
    # The callback's name in the message, with no traceback: the message alone drops nothing.
    logging.getLogger("asyncio").error(
        "Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)", exc_info=_windows_reset()
    )
    logging.getLogger("scholar_harness.something").error("reset elsewhere", exc_info=_windows_reset())
    logging.getLogger("asyncio").error("Exception in callback _call_connection_lost", exc_info=ValueError("x"))
    logging.getLogger("uvicorn.error").error("Cancel %s running task(s), timeout graceful shutdown exceeded", 2)
    logging.getLogger("uvicorn.error").error("Cancel 10 running task(s), timeout graceful shutdown exceeded")
    records = kept.records
    messages = _messages(kept)
    assert any("other_callback" in m for m in messages)
    assert any("<lambda>" in m for m in messages)
    transport = [r for r in records if r.getMessage().startswith("Exception in callback Transport._call_connection_lost")]
    assert len(transport) == 2
    assert isinstance(transport[0].exc_info[1].__context__, RuntimeError)  # (a) kept with the real fault
    assert transport[1].exc_info[1].__context__ is None  # (b) kept: raised in connection_lost
    assert "Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)" in messages
    assert "Exception in callback _call_connection_lost" in messages  # not a reset: kept
    assert "Cancel 2 running task(s), timeout graceful shutdown exceeded" in messages
    assert "Cancel 10 running task(s), timeout graceful shutdown exceeded" in messages
    assert len(messages) == 8  # the `scholar_harness` record goes to its own logger, not to these two


def _raise(exc: BaseException) -> None:
    raise exc


def test_a_reset_logged_from_elsewhere_passes(kept, caplog):
    log_noise.install()  # `kept` removes the filters again afterwards
    with caplog.at_level(logging.ERROR):
        logging.getLogger("scholar_harness.console").error("the browser went away", exc_info=_windows_reset())
    assert [r.getMessage() for r in caplog.records] == ["the browser went away"]


def test_install_adds_each_filter_once(kept):
    for _ in range(3):
        log_noise.install()
    assert sum(isinstance(f, log_noise.DroppedConnectionFilter) for f in logging.getLogger("asyncio").filters) == 1
    assert sum(isinstance(f, log_noise.NothingCancelledFilter) for f in logging.getLogger("uvicorn.error").filters) == 1


@pytest.mark.parametrize("no_console", [False, True], ids=["terminal-default-log-config", "no-console-log-config-none"])
def test_the_filters_survive_uvicorns_logging_set_up_in_both_starts(kept, monkeypatch, no_console):
    from fastapi import FastAPI

    for name in ("asyncio", "uvicorn.error"):  # start from loggers with no filter of ours
        lg = logging.getLogger(name)
        lg.filters[:] = [f for f in lg.filters if not isinstance(f, log_noise.DroppedConnectionFilter | log_noise.NothingCancelledFilter)]
    if no_console:
        monkeypatch.setattr(sys, "stdout", None)
        monkeypatch.setattr(sys, "stderr", None)
    server = launcher._uvicorn_server(FastAPI(), "127.0.0.1", launcher.free_port("127.0.0.1", 0))
    assert (server.config.log_config is None) is no_console
    server.config.load()  # what `Server.run` does first
    for lg in (logging.getLogger("asyncio"), logging.getLogger("uvicorn.error")):
        if kept not in lg.handlers:  # uvicorn's dictConfig replaced the handlers of loggers it names
            lg.addHandler(kept)
        lg.setLevel(logging.DEBUG)
    _log_from_the_loop(_call_connection_lost, _windows_reset())
    logging.getLogger("uvicorn.error").error("Cancel %s running task(s), timeout graceful shutdown exceeded", 0)
    logging.getLogger("uvicorn.error").error("Cancel %s running task(s), timeout graceful shutdown exceeded", 1)
    assert _messages(kept) == ["Cancel 1 running task(s), timeout graceful shutdown exceeded"]
