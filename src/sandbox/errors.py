"""Exception types that the CLI turns into clean, non-traceback error messages."""


class SandboxError(Exception):
    """A user-facing failure: the message is printed as-is and the CLI exits non-zero."""
