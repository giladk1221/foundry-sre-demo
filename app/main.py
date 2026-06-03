"""FastAPI entrypoint for the Foundry chat service."""
import logging

from fastapi import FastAPI, HTTPException
from openai import NotFoundError
from openai import RateLimitError
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from app.chat_service import chat_service
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("foundry-sre-demo")

MAX_PROMPT_CHARS = 4000
LIMITS = {"max_length": 4000}

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
        # Guardrail: reject oversized prompts before calling the model.
        if len(req.prompt) > MAX_INPUT_LENGTH:
            raise HTTPException(status_code=413, detail="Prompt too long.")
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
            headers={"Retry-After": "60"},
            content={"error": "Rate limited. Please retry after 60 seconds."},
        )
