"""
ClickHouse sessions in the HTTP protocol.
To do this, you need to use a context manager to add the session_id parameter to the request.
By default, the session is terminated after 60 seconds of inactivity.

https://clickhouse.com/docs/en/interfaces/http/
"""

import uuid
from typing import Optional
from contextvars import ContextVar, Token

ctx_session_id: ContextVar[str] = ContextVar("ck.session_id")
ctx_session_timeout: ContextVar[float] = ContextVar("ck.session_timeout")


class SessionContext:
    """Session context manager"""

    def __init__(self, session: str, timeout: float):
        self.session = session
        self.timeout = timeout
        self.token1: Optional[Token[str]] = None
        self.token2: Optional[Token[float]] = None

    def __enter__(self) -> str:
        self.token1 = ctx_session_id.set(self.session)
        self.token2 = ctx_session_timeout.set(self.timeout)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        ctx_session_id.reset(self.token1)
        ctx_session_timeout.reset(self.token2)


def in_session(session: Optional[str] = None, timeout: int = 60):
    """
    Add a session_id for subsequent requests
    You can use this context manager safely in coroutines or threads
    """
    session = session or str(uuid.uuid4())
    return SessionContext(session, timeout)
