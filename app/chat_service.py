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
        for attempt in range(3):
            try:
                response = self._client.chat.completions.create(
                    model=settings.deployment,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content or ""
            except RateLimitError:
                if attempt == 2:
                    raise

                backoff_seconds = 2**attempt
                logger.warning(
                    "Rate limited by deployment '%s'; retrying in %s seconds "
                    "(attempt %s/3)",
                    settings.deployment,
                    backoff_seconds,
                    attempt + 1,
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
