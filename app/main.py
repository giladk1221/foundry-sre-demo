"""FastAPI entrypoint for the Foundry chat service."""
import logging

from fastapi import FastAPI, HTTPException
from openai import NotFoundError, RateLimitError
from pydantic import BaseModel
from starlette.responses import JSONResponse

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
    except RateLimitError:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Service is temporarily rate limited. Please retry after 60 seconds."
            },
            headers={"Retry-After": "60"},
        )
