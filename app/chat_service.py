"""Chat service that calls an Azure AI Foundry (Azure OpenAI) model deployment."""
import logging
import time

from openai import AzureOpenAI
from openai import NotFoundError
from openai import RateLimitError

from app.config import settings

logger = logging.getLogger("foundry-sre-demo.chat")

_RETRY_COUNT = 3
_RETRY_BASE_DELAY = 1.0  # seconds


class ChatService:
    def __init__(self) -> None:
        self._client = AzureOpenAI(
            azure_endpoint=settings.endpoint,
            api_key=settings.api_key,
            api_version=settings.api_version,
        )

    def complete(self, prompt: str) -> str:
        delay = _RETRY_BASE_DELAY
        for attempt in range(1, _RETRY_COUNT + 1):
            try:
                response = self._client.chat.completions.create(
                    model=settings.deployment,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content or ""
            except RateLimitError:
                if attempt == _RETRY_COUNT:
                    logger.exception(
                        "Rate limit exceeded after %d attempts for deployment '%s'",
                        _RETRY_COUNT,
                        settings.deployment,
                    )
                    raise
                logger.warning(
                    "Rate limit hit (attempt %d/%d), retrying in %.1fs",
                    attempt,
                    _RETRY_COUNT,
                    delay,
                )
                time.sleep(delay)
                delay *= 2
            except NotFoundError:
                # Surfaces as: DeploymentNotFound - The API deployment for this
                # resource does not exist.
                logger.exception(
                    "Foundry deployment '%s' not found at %s",
                    settings.deployment,
                    settings.endpoint,
                )
                raise


chat_service = ChatService()
