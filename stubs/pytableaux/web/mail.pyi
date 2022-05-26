import logging
import ssl
from collections import deque
from typing import Any, Mapping, Sequence

def validate_feedback_form(form_data: dict[str, str]) -> None:...
def is_valid_email(value: str) -> bool:...

class Mailroom:
    config: Mapping[str, Any]
    logger: logging.Logger
    loaded: bool
    should_stop: bool
    last_was_success: bool
    queue: deque
    failqueue: deque
    tlscontext: ssl.SSLContext|None
    def __init__(self, config: Mapping[str, Any]) -> None: ...
    @property
    def enabled(self): ...
    @property
    def tls_enabled(self): ...
    @property
    def auth_enabled(self): ...
    @property
    def running(self): ...
    def start(self) -> None: ...
    def stop(self, timeout: float = ...): ...
    def enqueue(self, from_addr: str, to_addrs: Sequence[str], msg: str): ...
