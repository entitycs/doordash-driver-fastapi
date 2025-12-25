"""
title: DoorDash Drive & Developer API
author: YourName
description: FastAPI wrapper for DoorDash Drive delivery and business/store management APIs
required_open_webui_version: 0.4.0
requirements: fastapi, pydantic, requests, pyjwt[crypto]
version: 1.0.1
licence: MIT
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from config.internal.internal_config import config
from fast_api_server.routers.doordash import router as doordash_router
from fast_api_server.routers.webhooks import router as webhook_router
from core.logging.logger import logger

if not all([config.DOORDASH_DEVELOPER_ID, config.DOORDASH_KEY_ID, config.DOORDASH_SIGNING_SECRET, config.DOORDASH_DB_PW]):
    raise RuntimeError(
        "Missing required environment variables: DOORDASH_DEVELOPER_ID, DOORDASH_KEY_ID, DOORDASH_SIGNING_SECRET, DOORDASH_DB_PW"
    )

app = FastAPI(
    title="DoorDash Drive API",
    version="1.0.2",
    description="Provides HTTP endpoints for DoorDash Drive (quotes, deliveries) and Developer (businesses, stores) APIs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Read and log the request body (FastAPI caches it)
    body = await request.body()
    logger.info(f"→ {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Body: {body.decode('utf-8', errors='replace') or ''}")
    # Let the request proceed unchanged
    response = await call_next(request)
    # Log response status code (no body introspection)
    logger.info(f"← {response.status_code}")
    return response

app.include_router(doordash_router)
app.include_router(webhook_router)

