"""Platform gate: sandbox relies on fcntl locking and POSIX tooling (Linux and macOS only)."""

import sys

from sandbox.errors import SandboxError

SUPPORTED_PLATFORMS = ("linux", "darwin")


def ensure_supported_platform(platform: str | None = None) -> None:
    """Fail with a clear message on anything other than Linux or macOS."""
    current = sys.platform if platform is None else platform
    if current.startswith("win") or current == "cygwin":
        raise SandboxError(
            f"unsupported platform {current!r}: sandbox runs on Linux and macOS only "
            "(it needs fcntl file locking, loopback aliases and /etc/hosts)"
        )
    if not current.startswith(SUPPORTED_PLATFORMS):
        raise SandboxError(
            f"unsupported platform {current!r}: sandbox runs on Linux and macOS only"
        )
