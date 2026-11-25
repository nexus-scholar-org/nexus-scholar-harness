"""Two harmless lines the engine's log no longer collects (H-b8-small-faults).

Testing the installed 1.1.0b8 showed two kinds of lines in the log file (and in
the terminal of `nexus-scholar ui`) when nothing had failed:

* on Windows, when the browser drops a connection, the ``asyncio`` logger writes
  "Exception in callback _ProactorBasePipeTransport._call_connection_lost…" with
  a ``ConnectionResetError: [WinError 10054]`` (or ``ConnectionAbortedError``)
  traceback: the proactor loop closing a socket the other side already closed;
* on a stop with a browser tab open, uvicorn writes "Cancel 0 running task(s),
  timeout graceful shutdown exceeded": the grace period ended with nothing left
  to cancel.

A tester asked to send the log reads them as errors. The filters below drop
exactly those records and nothing else. An ``asyncio`` record is dropped only
when its exception is a ``ConnectionResetError`` or ``ConnectionAbortedError``
whose innermost traceback frame is ``_call_connection_lost`` and which carries
no ``__context__`` and no ``__cause__``. Another ``asyncio`` error, a reset
raised deeper (in the protocol's ``connection_lost``) or after another error,
a reset reported from anywhere else, or a stop that really cancelled tasks
("Cancel 2 running task(s)…") is still logged.

The filters sit on the loggers that create the records (``asyncio`` and
``uvicorn.error``). A logger's filters see only its own records, and
``logging.config.dictConfig`` (uvicorn's own set-up, run each time a server is
configured) replaces a configured logger's handlers but keeps its filters;
:func:`install` is called after every configuration anyway and adds each filter
once.
"""

from __future__ import annotations

import logging
import re

#: The callback the proactor event loop runs when a connection is lost.
_CONNECTION_LOST = "_call_connection_lost"
_RESETS = (ConnectionResetError, ConnectionAbortedError)
_NOTHING_CANCELLED = re.compile(r"^Cancel 0 running task\(s\), timeout graceful shutdown exceeded$")


def _raised_in_connection_lost(record: logging.LogRecord) -> bool:
    """The reset was raised by ``_call_connection_lost`` itself, and nothing else went wrong.

    The innermost frame of the traceback must be ``_call_connection_lost`` (its
    socket ``shutdown`` is a C call, so it adds no frame): a reset raised deeper,
    in the protocol's own ``connection_lost``, is kept. The exception must carry
    no ``__context__`` and no ``__cause__``: a reset raised in that method's
    ``finally`` after the protocol failed carries the real fault as its context,
    and is kept. The message is not consulted.
    """
    exc_info = record.exc_info
    if not exc_info or not isinstance(exc_info[1], _RESETS):
        return False
    error = exc_info[1]
    if error.__context__ is not None or error.__cause__ is not None:
        return False
    tb = exc_info[2]
    if tb is None:
        return False
    while tb.tb_next is not None:
        tb = tb.tb_next
    return tb.tb_frame.f_code.co_name == _CONNECTION_LOST


class DroppedConnectionFilter(logging.Filter):
    """On the ``asyncio`` logger: drops a browser's dropped connection seen by the proactor loop."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not (record.name == "asyncio" and _raised_in_connection_lost(record))


class NothingCancelledFilter(logging.Filter):
    """On the ``uvicorn.error`` logger: drops the end of a grace period that cancelled nothing."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a malformed record is someone else's line: keep it
            return True
        return not _NOTHING_CANCELLED.match(message)


_FILTERS: tuple[tuple[str, type[logging.Filter]], ...] = (
    ("asyncio", DroppedConnectionFilter),
    ("uvicorn.error", NothingCancelledFilter),
)


def install() -> None:
    """Add each filter to its logger, once; safe to call before and after any logging set-up."""
    for name, kind in _FILTERS:
        logger = logging.getLogger(name)
        if not any(isinstance(existing, kind) for existing in logger.filters):
            logger.addFilter(kind())
