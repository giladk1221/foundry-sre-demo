"""FastAPI entrypoint for the Foundry chat service."""
import logging

from fastapi import FastAPI, HTTPException
from openai import APITimeoutError, NotFoundError, RateLimitError
from pydantic import BaseModel

from app.chat_service import chat_service
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("foundry-sre-demo")

app = FastAPI(title="Foundry SRE Demo", version="1.0.0")


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
    except NotFoundError as exc:
        # 502: upstream Foundry deployment misconfiguration
        raise HTTPException(
            status_code=502,
            detail=(
                f"DeploymentNotFound: deployment '{settings.deployment}' "
                "does not exist in the Foundry resource."
            ),
        ) from exc
    except RateLimitError as exc:
        retry_after = 10
        if exc.response is not None:
            retry_after_header = exc.response.headers.get("Retry-After")
            if retry_after_header is not None:
                try:
                    retry_after = int(retry_after_header)
                except ValueError:
                    pass
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        ) from exc
    except APITimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=(
                "Gateway Timeout: the upstream Foundry deployment did not respond in time."
            ),
        ) from exc
