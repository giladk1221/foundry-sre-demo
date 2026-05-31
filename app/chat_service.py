"""Chat service that calls an Azure AI Foundry (Azure OpenAI) model deployment."""
import logging
import time

from openai import APITimeoutError
from openai import AzureOpenAI
from openai import NotFoundError
from openai import RateLimitError

from app.config import settings

logger = logging.getLogger("foundry-sre-demo.chat")

_RATE_LIMIT_MAX_ATTEMPTS = 3
_RATE_LIMIT_BASE_DELAY = 1  # seconds


class ChatService:
    def __init__(self) -> None:
        self._client = AzureOpenAI(
            azure_endpoint=settings.endpoint,
            api_key=settings.api_key,
            api_version=settings.api_version,
        )

    def complete(self, prompt: str) -> str:
        last_timeout_exc: APITimeoutError | None = None
        for attempt in range(1, _RATE_LIMIT_MAX_ATTEMPTS + 1):
            try:
                response = self._client.chat.completions.create(
                    model=settings.deployment,  # <-- stale deployment name
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content or ""
            except NotFoundError:
                # Surfaces as: DeploymentNotFound - The API deployment for this
                # resource does not exist.
                logger.exception(
                    "Foundry deployment '%s' not found at %s",
                    settings.deployment,
                    settings.endpoint,
                )
                raise
            except RateLimitError as exc:
                if attempt < _RATE_LIMIT_MAX_ATTEMPTS:
                    delay = _RATE_LIMIT_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "Rate limit hit (attempt %d/%d); retrying in %.1fs",
                        attempt,
                        _RATE_LIMIT_MAX_ATTEMPTS,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Rate limit exceeded after %d attempts",
                        _RATE_LIMIT_MAX_ATTEMPTS,
                    )
                    raise
            except APITimeoutError as exc:
                if last_timeout_exc is None:
                    last_timeout_exc = exc
                    logger.warning(
                        "Request timed out (attempt %d/%d); retrying once",
                        attempt,
                        _RATE_LIMIT_MAX_ATTEMPTS,
                    )
                else:
                    logger.error("Request timed out on retry; giving up")
                    raise
        # Should be unreachable, but satisfy the type-checker.
        raise RuntimeError("Unexpected exit from retry loop")


chat_service = ChatService()
