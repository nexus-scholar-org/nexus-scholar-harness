"""Deployment isolation adapter for the AG-03A protected-publisher proof.

Mechanism: **Windows Mandatory Integrity Control (MIC)**.

* The publisher store (approval records, policy, executable code, registry,
  audit, final outputs) runs at the default **Medium** integrity level.
* The restricted scientific worker runs in a process whose token is set to
  **Low** integrity. Windows' default no-write-up policy then denies the worker
  any write to Medium objects, while a Low-labelled *inbox* remains writable.

This is an OS-enforced boundary, not a policy convention: it holds against a
worker that ignores prompts, forges human-looking fields, or calls the harness
API directly. It requires no administrator rights (verified on a non-admin
Windows host) and no container runtime.

Supported host for the *enforcement* tests: Windows. POSIX requires a
separately provisioned arrangement (two OS identities + filesystem modes) that
this proof does not implement; :func:`capability_report` records that honestly
rather than simulating it.
"""

from __future__ import annotations

import ctypes
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

#: Windows token information class / attribute flag for the integrity level.
_TOKEN_INTEGRITY_LEVEL = 25
_SE_GROUP_INTEGRITY = 0x00000020
_LOW_INTEGRITY_SID = "S-1-16-4096"
_MEDIUM_INTEGRITY_SID = "S-1-16-8192"


class IsolationUnavailable(RuntimeError):
    """The requested isolation mechanism is not available on this host."""


def _windows_api() -> dict[str, Any]:
    """Import the Windows API surface lazily so non-Windows imports stay cheap."""
    try:  # pragma: no cover - import guard
        import win32api
        import win32con
        import win32event
        import win32process
        import win32security
    except Exception as exc:  # noqa: BLE001 - pywin32 is not a declared dependency
        raise IsolationUnavailable(
            "pywin32 (win32security/win32process) is required for Windows MIC isolation"
        ) from exc
    return {
        "win32api": win32api,
        "win32con": win32con,
        "win32event": win32event,
        "win32process": win32process,
        "win32security": win32security,
    }


def is_admin() -> bool:
    """Return whether the current process holds administrator rights."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001 - non-Windows
        return False


def available() -> bool:
    """Whether this adapter can establish the boundary on the current host."""
    if sys.platform != "win32":
        return False
    try:
        _windows_api()
    except IsolationUnavailable:
        return False
    return True


def capability_report() -> dict[str, Any]:
    """Return an honest statement of the deployment boundary on this host.

    This proof exposes NO publisher HTTP service, NO credential file, and NO
    operator UI: the ``http_service``/``credential_file``/``operator_ui`` keys
    (and the ``routes`` entries ``tcp_listener``/``credential_artifact``/
    ``desktop_ui_route``) are None because the supported deployment has no
    network listener, no credential artifact, and no desktop/UI approval route,
    so those bypass routes are absent-by-construction (not merely untested).
    """
    _routes: dict[str, Any] = {
        "tcp_listener": None,
        "credential_artifact": None,
        "desktop_ui_route": None,
        "worker_token": "low-integrity (S-1-16-4096)",
        "worker_writable": ["worker inbox (Low label)"],
        "publisher_store": "Medium integrity, worker write denied",
    }
    _absent_note = (
        "The supported deployment has no network listener, no credential "
        "artifact, and no desktop/UI approval route, so those bypass routes "
        "are absent-by-construction (not merely untested)."
    )
    if sys.platform != "win32":
        return {
            "platform": sys.platform,
            "mechanism": None,
            "available": False,
            "reason": (
                "Windows MIC is the mechanism implemented by this proof. POSIX requires a "
                "separately provisioned arrangement: two OS identities (publisher/operator and "
                "restricted worker) plus filesystem ownership/modes giving the worker read-only "
                "evidence and a write-only inbox. Not implemented here, so NOT proven on POSIX."
            ),
            "http_service": None,
            "credential_file": None,
            "operator_ui": None,
            "absent_routes_note": _absent_note,
            "routes": _routes,
        }
    api_ok = True
    reason = (
        "Windows Mandatory Integrity Control: Low-IL worker vs Medium publisher store."
    )
    try:
        _windows_api()
    except IsolationUnavailable as exc:
        api_ok = False
        reason = str(exc)
    return {
        "platform": sys.platform,
        "mechanism": "windows_mandatory_integrity_control",
        "available": api_ok,
        "admin_required": False,
        "is_admin": is_admin(),
        "reason": reason,
        "http_service": None,
        "credential_file": None,
        "operator_ui": None,
        "absent_routes_note": _absent_note,
        "routes": _routes,
    }


def provision_publisher_store(path: Path) -> None:
    """Ensure publisher-owned state is at (or above) Medium integrity."""
    if not available():
        raise IsolationUnavailable("MIC provisioning requires Windows")
    path.mkdir(parents=True, exist_ok=True)
    _run_icacls([str(path), "/setintegritylevel", "(OI)(CI)M"])


def provision_worker_inbox(path: Path) -> None:
    """Label the worker's draft inbox Low so a Low-IL worker may write it."""
    if not available():
        raise IsolationUnavailable("MIC provisioning requires Windows")
    path.mkdir(parents=True, exist_ok=True)
    _run_icacls([str(path), "/setintegritylevel", "(OI)(CI)L"])


def _run_icacls(args: Sequence[str]) -> None:
    result = subprocess.run(
        ["icacls", *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise IsolationUnavailable(
            "icacls failed: " + (result.stdout + result.stderr).strip()
        )


def low_integrity_token() -> Any:
    """Build a primary token whose integrity level is Low (no admin required)."""
    api = _windows_api()
    ws, wp, wc = api["win32security"], api["win32process"], api["win32con"]
    token = ws.OpenProcessToken(
        api["win32api"].GetCurrentProcess(), wc.TOKEN_ALL_ACCESS
    )
    low = ws.ConvertStringSidToSid(_LOW_INTEGRITY_SID)
    primary = ws.DuplicateTokenEx(
        token, ws.SecurityImpersonation, wc.MAXIMUM_ALLOWED, ws.TokenPrimary
    )
    ws.SetTokenInformation(primary, _TOKEN_INTEGRITY_LEVEL, (low, _SE_GROUP_INTEGRITY))
    return primary


def run_low_integrity(
    script: Path, *, cwd: Path, python: str | None = None, timeout: int = 90
) -> int:
    """Run ``script`` in a Low-integrity worker process; return its exit code.

    The worker writes its own report into the (Low) inbox; output is not piped
    back, so the boundary is never bypassed by an inherited handle.
    ``bInheritHandles=False`` is passed to ``CreateProcessAsUser`` so the child
    receives no inheritable handles: a worker that inherited a writable
    publisher handle could bypass the MIC DACLs on the publisher store.
    """
    api = _windows_api()
    wp, we = api["win32process"], api["win32event"]
    token = low_integrity_token()
    startup = wp.STARTUPINFO()
    executable = python or sys.executable
    ph, _th, _pid, _tid = wp.CreateProcessAsUser(
        token,
        None,
        f'"{executable}" "{script}"',
        None,
        None,
        False,
        0,
        None,
        str(cwd),
        startup,
    )
    we.WaitForSingleObject(ph, timeout * 1000)
    return int(wp.GetExitCodeProcess(ph))
