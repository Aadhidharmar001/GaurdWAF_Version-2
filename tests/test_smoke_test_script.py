import builtins
import importlib.util
import sys
import types
from pathlib import Path


def _load_smoke_test_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "smoke_test.py"
    spec = importlib.util.spec_from_file_location("guardwaf_smoke_test_script", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_client_target_url_does_not_require_fastapi(monkeypatch):
    smoke_test = _load_smoke_test_module()

    class DummyClient:
        def __init__(self, base_url, timeout):
            self.base_url = base_url
            self.timeout = timeout

    monkeypatch.setitem(sys.modules, "httpx", types.SimpleNamespace(Client=DummyClient))

    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "fastapi" or name.startswith("fastapi."):
            raise ModuleNotFoundError("No module named 'fastapi'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    client = smoke_test._build_client("http://localhost:8000")
    assert isinstance(client, DummyClient)
    assert client.base_url == "http://localhost:8000"
    assert client.timeout == 10.0
