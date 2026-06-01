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
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self._client.chat.completions.create(
                    model=settings.deployment,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content or ""
            except RateLimitError:
                if attempt == max_attempts - 1:
                    raise
                backoff_seconds = 2**attempt
                logger.warning(
                    "Rate-limited by Foundry deployment '%s'; retrying in %s second(s) (attempt %s/%s)",
                    settings.deployment,
                    backoff_seconds,
                    attempt + 1,
                    max_attempts,
                )
                time.sleep(backoff_seconds)
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
