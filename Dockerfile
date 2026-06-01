# Foundry SRE Demo — container image for Azure Container Apps.
# Base image is pulled from Microsoft Artifact Registry (MCR) to avoid
# Docker Hub anonymous pull rate limits during ACR builds.
FROM mcr.microsoft.com/azurelinux/base/python:3.12

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Container Apps sets $PORT; bind uvicorn to it.
CMD ["sh", "-c", "python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
