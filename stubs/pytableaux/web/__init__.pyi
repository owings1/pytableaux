import logging
from typing import Any, Mapping

from _typeshed import Incomplete
from pytableaux import __docformat__ as __docformat__
from pytableaux import package as package
from pytableaux import tools as tools
from pytableaux.tools.abcs import Ebc as Ebc
from pytableaux.tools.abcs import ItemMapEnum


class Wevent(Ebc):
    before_dispatch: Incomplete

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
