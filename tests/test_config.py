import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PRINT_DEPLOYMENT = "from app.config import settings; print(settings.deployment)"


def _read_deployment(env: dict[str, str]) -> str:
    result = subprocess.run(
        [sys.executable, "-c", PRINT_DEPLOYMENT],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_default_deployment_name():
    env = os.environ.copy()
    env.pop("AZURE_OPENAI_DEPLOYMENT", None)
    assert _read_deployment(env) == "gpt-4o"


def test_deployment_env_override():
    env = os.environ.copy()
    env["AZURE_OPENAI_DEPLOYMENT"] = "custom-deployment"
    assert _read_deployment(env) == "custom-deployment"
