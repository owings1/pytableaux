from typing import Any, Mapping

def fix_uri_req_data(form_data: Mapping[str, Any]) -> dict[str, Any]: ...
def tojson(*args, **kw) -> str: ...
def tojsonb(*args, **kw) -> bytes: ...
def errstr(err: Exception) -> str: ...
