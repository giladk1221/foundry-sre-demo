"""Application configuration for the Foundry chat service.

NOTE: ``AZURE_OPENAI_DEPLOYMENT`` must match a real model deployment in the
Foundry resource. If it does not, the Azure OpenAI API returns
``DeploymentNotFound`` (HTTP 404).
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    endpoint: str = os.getenv(
        "AZURE_OPENAI_ENDPOINT", "https://sre-demo-foundry.openai.azure.com"
    )
    api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

    # BUG (seeded for SRE Agent demo):
    # The production Foundry resource exposes a deployment named "gpt-4o".
    # This default points at "gpt-4o-prod", which was never created, so every
    # request fails with: DeploymentNotFound - The API deployment for this
    # resource does not exist.
    deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")


settings = Settings()
