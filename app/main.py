"""FastAPI entrypoint for the Foundry chat service."""
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from fastapi import FastAPI, HTTPException
from openai import NotFoundError
from openai import RateLimitError
from pydantic import BaseModel

from app.chat_service import chat_service
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("foundry-sre-demo")

app = FastAPI(title="Foundry SRE Demo", version="1.0.0")
DEFAULT_RETRY_AFTER_SECONDS = 10


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    reply: str
    deployment: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "deployment": settings.deployment}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        reply = chat_service.complete(req.prompt)
        return ChatResponse(reply=reply, deployment=settings.deployment)
    except RateLimitError as exc:
        retry_after = DEFAULT_RETRY_AFTER_SECONDS
        if exc.response is not None:
            retry_after_header = exc.response.headers.get("retry-after")
            if retry_after_header is not None:
                try:
                    retry_after = int(retry_after_header)
                except ValueError:
                    try:
                        retry_after_at = parsedate_to_datetime(retry_after_header)
                        if retry_after_at.tzinfo is None:
                            retry_after_at = retry_after_at.replace(tzinfo=timezone.utc)
                        retry_after = max(
                            0,
                            int(
                                (
                                    retry_after_at - datetime.now(timezone.utc)
                                ).total_seconds()
                            ),
                        )
                    except (TypeError, ValueError, OverflowError):
                        pass

        raise HTTPException(
            status_code=429,
            detail=(
                "Rate limited by Azure OpenAI. "
                f"Please retry after {retry_after} seconds."
            ),
            headers={"Retry-After": str(retry_after)},
        ) from exc
    except NotFoundError as exc:
        # 502: upstream Foundry deployment misconfiguration
        raise HTTPException(
            status_code=502,
            detail=(
                f"DeploymentNotFound: deployment '{settings.deployment}' "
                "does not exist in the Foundry resource."
            ),
        ) from exc
