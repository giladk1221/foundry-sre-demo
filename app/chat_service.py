"""Chat service that calls an Azure AI Foundry (Azure OpenAI) model deployment."""
import logging
import time

from openai import AzureOpenAI
from openai import NotFoundError
from openai import RateLimitError

from app.config import settings

logger = logging.getLogger("foundry-sre-demo.chat")


class ChatService:
    def __init__(self) -> None:
        self._client = AzureOpenAI(
            azure_endpoint=settings.endpoint,
            api_key=settings.api_key,
            api_version=settings.api_version,
        )

    def complete(self, prompt: str) -> str:
        backoff_seconds = [1, 2, 4]
        for attempt, wait in enumerate(backoff_seconds, start=1):
            try:
                response = self._client.chat.completions.create(
                    model=settings.deployment,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content or ""
            except RateLimitError:
                if attempt < len(backoff_seconds):
                    logger.warning(
                        "Rate limit hit for deployment '%s', retrying in %ds (attempt %d/%d)",
                        settings.deployment,
                        wait,
                        attempt,
                        len(backoff_seconds),
                    )
                    time.sleep(wait)
                else:
                    logger.warning(
                        "Rate limit exceeded for deployment '%s' after %d attempts",
                        settings.deployment,
                        attempt,
                    )
                    raise
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
