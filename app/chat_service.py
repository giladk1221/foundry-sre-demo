"""Chat service that calls an Azure AI Foundry (Azure OpenAI) model deployment."""
import logging

from openai import AzureOpenAI
from openai import APIError, APITimeoutError, NotFoundError, RateLimitError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.config import settings

logger = logging.getLogger("foundry-sre-demo.chat")


class ChatService:
    def __init__(self) -> None:
        self._client = AzureOpenAI(
            azure_endpoint=settings.endpoint,
            api_key=settings.api_key,
            api_version=settings.api_version,
        )

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=10),
        reraise=True,
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def complete(self, prompt: str) -> str:
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
        except RateLimitError:
            logger.warning(
                "OpenAI API rate limit hit for deployment '%s' at %s",
                settings.deployment,
                settings.endpoint,
            )
            raise
        except APITimeoutError:
            logger.exception(
                "OpenAI API request timed out for deployment '%s' at %s",
                settings.deployment,
                settings.endpoint,
            )
            raise
        except APIError:
            logger.exception(
                "Unexpected OpenAI API error for deployment '%s' at %s",
                settings.deployment,
                settings.endpoint,
            )
            raise


chat_service = ChatService()
