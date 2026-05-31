"""Chat service that calls an Azure AI Foundry (Azure OpenAI) model deployment."""
import logging
import time

from openai import AzureOpenAI
from openai import APITimeoutError, NotFoundError, RateLimitError

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
        max_rate_limit_retries = 3
        for attempt in range(max_rate_limit_retries + 1):
            try:
                return self._attempt_complete(prompt)
            except RateLimitError:
                if attempt < max_rate_limit_retries:
                    delay = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        "Rate limit hit (attempt %d/%d); retrying in %ds",
                        attempt + 1,
                        max_rate_limit_retries,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Rate limit exhausted after %d retries",
                        max_rate_limit_retries,
                    )
                    raise

    def _call_api(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=settings.deployment,  # <-- stale deployment name
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    def _attempt_complete(self, prompt: str) -> str:
        try:
            return self._call_api(prompt)
        except NotFoundError:
            # Surfaces as: DeploymentNotFound - The API deployment for this
            # resource does not exist.
            logger.exception(
                "Foundry deployment '%s' not found at %s",
                settings.deployment,
                settings.endpoint,
            )
            raise
        except APITimeoutError:
            logger.warning(
                "Request to Foundry deployment '%s' timed out; retrying once",
                settings.deployment,
            )
            try:
                return self._call_api(prompt)
            except APITimeoutError:
                logger.error(
                    "Request to Foundry deployment '%s' timed out on retry",
                    settings.deployment,
                )
                raise


chat_service = ChatService()
