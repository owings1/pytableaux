from datetime import datetime
import logging
from enum import Enum
from typing import Any, Mapping

from _typeshed import Incomplete

from pytableaux import __docformat__ as __docformat__
from pytableaux import package as package
from pytableaux import tools as tools
from pytableaux.tools.abcs import ItemMapEnum

class Wevent(Enum):
    before_dispatch: object
    after_dispatch: object

def get_logger(name: str|Any, conf: Mapping[str, Any] = ...) -> logging.Logger: ...
def set_conf_loglevel(logger: logging.Logger, conf: Mapping[str, Any]): ...

class EnvConfig(ItemMapEnum):
    app_name: Incomplete
    host: Incomplete
    port: Incomplete
    metrics_port: Incomplete
    is_debug: Incomplete
    loglevel: Incomplete
    maxtimeout: Incomplete
    google_analytics_id: Incomplete
    feedback_enabled: Incomplete
    feedback_to_address: Incomplete
    feedback_from_address: Incomplete
    smtp_host: Incomplete
    smtp_port: Incomplete
    smtp_helo: Incomplete
    smtp_starttls: Incomplete
    smtp_tlscertfile: Incomplete
    smtp_tlskeyfile: Incomplete
    smtp_tlskeypass: Incomplete
    smtp_username: Incomplete
    smtp_password: Incomplete
    mailroom_interval: Incomplete
    mailroom_requeue_interval: Incomplete
    def __init__(self, m) -> None: ...
    def resolve(): ...
    @classmethod
    def env_config(cls, env: Mapping[str, Any] = ...) -> dict[str, Any]: ...

class StaticResource:
    path: str
    content: bytes
    headers: Mapping
    modtime: datetime
    def __init__(self, path: str, content: str|bytes) -> None: ...
    def is_modified_since(self, modstr: str|None) -> bool: ...

def tojson(*args, **kw) -> str: ...
def fix_uri_req_data(form_data: dict[str, Any]) -> dict[str, Any]: ...
