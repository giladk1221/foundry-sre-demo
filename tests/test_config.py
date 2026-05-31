import importlib

import app.config as config


def test_default_deployment_name(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)
    importlib.reload(config)
    assert config.settings.deployment == "gpt-4o"
