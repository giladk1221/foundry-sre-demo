# foundry-sre-demo

A minimal **Azure AI Foundry** chat microservice used to demonstrate the
**Azure SRE Agent** incident-to-fix workflow.

The service exposes a `/chat` endpoint that proxies requests to an Azure OpenAI
(Foundry) **model deployment**. In production it is reporting:

```
DeploymentNotFound: The API deployment for this resource does not exist.
```

…because the configured deployment name does not match a real deployment in the
Foundry resource. The SRE Agent investigates this signal, finds the root cause in
this codebase, and opens a fix PR (assigned to GitHub Copilot).

## Architecture

```
client ──► POST /chat ──► ChatService ──► Azure OpenAI / Foundry
                                              deployment: $AZURE_OPENAI_DEPLOYMENT
```

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your Foundry endpoint + key
uvicorn app.main:app --reload
```

## Configuration

| Env var | Description |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Foundry resource endpoint, e.g. `https://my-foundry.openai.azure.com` |
| `AZURE_OPENAI_API_KEY` | API key (or use Entra ID) |
| `AZURE_OPENAI_DEPLOYMENT` | **Model deployment name** — must exist in the Foundry resource |
| `AZURE_OPENAI_API_VERSION` | API version, e.g. `2024-10-21` |

> Known issue: the default deployment name in `app/config.py` is stale. See `logs/`.
