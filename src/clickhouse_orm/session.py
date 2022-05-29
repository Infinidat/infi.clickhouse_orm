import uuid
from typing import Optional
from contextvars import ContextVar

ctx_session_id: ContextVar[str] = ContextVar('ck.session_id')
ctx_session_timeout: ContextVar[int] = ContextVar('ck.session_timeout')


class SessionContext:
    def __init__(self, session: str, timeout: int):
        self.session = session
        self.timeout = timeout
        self.token1 = None
        self.token2 = None

    def __enter__(self) -> str:
        self.token1 = ctx_session_id.set(self.session)
        self.token2 = ctx_session_timeout.set(self.timeout)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        ctx_session_id.reset(self.token1)
        ctx_session_timeout.reset(self.token2)


def in_session(session: Optional[str] = None, timeout: int = 60):
    session = session or str(uuid.uuid4())
    return SessionContext(session, timeout)
