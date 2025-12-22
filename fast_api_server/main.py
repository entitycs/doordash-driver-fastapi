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
import time
import jwt
import base64  # Add this import at the top
import requests
from typing import Any, Dict, Optional
from fastapi import FastAPI, Body, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse
from logging import Logger
from .models import *
from config.internal.internal_config import config

logger = Logger('uvcorn')
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

if not all([config.DOORDASH_DEVELOPER_ID, config.DOORDASH_KEY_ID, config.DOORDASH_SIGNING_SECRET]):
    raise RuntimeError(
        "Missing required environment variables: DOORDASH_DEVELOPER_ID, DOORDASH_KEY_ID, DOORDASH_SIGNING_SECRET"
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    body = await request.body()
    logger.info(f"→ {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Body: {body.decode('utf-8', errors='replace') or ''}")
    print("log request called")
    response = await call_next(request)

    async def stream():
        async for chunk in response.body_iterator:
            yield chunk
        logger.info(f"← {response.status_code}")

    return StreamingResponse(
        stream(),
        status_code=response.status_code,
        headers=response.headers,
        media_type=response.media_type,
    )

def generate_jwt_token() -> str:
    """Generate a short-lived JWT for DoorDash API authentication (5-minute expiry)"""
    issued_at = int(time.time())
    payload = {
        "aud": "doordash",
        "iss": config.DOORDASH_DEVELOPER_ID,
        "kid": config.DOORDASH_KEY_ID,
        "exp": issued_at + 300,
        "iat": issued_at,
    }
    headers = {"alg": "HS256", "dd-ver": "DD-JWT-V1"}

    # Since we validated at startup, these are guaranteed to be str
    # But to help type checkers, we assert non-None
    assert config.DOORDASH_SIGNING_SECRET is not None, "SIGNING_SECRET is missing (should be validated at startup)"
    secret = config.DOORDASH_SIGNING_SECRET

    # Add padding if needed for base64url decoding
    missing_padding = len(secret) % 4
    if missing_padding:
        secret += "=" * (4 - missing_padding)

    key = base64.urlsafe_b64decode(secret)

    token = jwt.encode(
        payload,
        key=key,
        algorithm="HS256",
        headers=headers,
    )
    return token

def doordash_request(method: str, url: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Centralized request handler with JWT auth"""
    token = generate_jwt_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        if json_data:
            response = requests.request(method, url, json=json_data, headers=headers, timeout=30)
        else:
            response = requests.request(method, url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        error_detail = {}
        if hasattr(e, "response") and e.response is not None:
            try:
                error_detail = e.response.json()
            except ValueError:
                error_detail = {"error": e.response.text}
        else:
            error_detail = {"error": str(e)}
        raise HTTPException(status_code=getattr(e.response, "status_code", 500), detail=error_detail)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail={"error": f"Request failed: {str(e)}"})

# ========================
# Endpoints
# ========================

@app.post("/create_quote", response_model=DoorDashResponse)
async def create_quote(data: CreateQuoteRequest = Body(...)):
    """
    Create a delivery quote using DoorDash Drive API.
    """
    payload = data.model_dump(exclude={"external_delivery_id", "dropoff_address_components"}, exclude_unset=True)

    response = doordash_request(
        method="POST",
        url="https://openapi.doordash.com/drive/v2/quotes",
        json_data=payload,
    )
    return {"data": response}

@app.post("/list_stores", response_model=ListStoreResponse)
async def list_stores(data: ListStoreRequest = Body(...)):
    """
    List Store Request
    
    - Returns list of company stores registered with doordash drive api
    
    This endpoint serves as the FastAPI controller for fetching the company's store IDs registered with the doordash drive api.
    It accepts a ListStoreRequest containing search parameters and executes a call to the doordash drive api.

    Key Features:
    - Fetches the stores the company has registered with the doordash drive api

    Use Cases:
    - Identifying store IDs the company has registered with the doordash drive api

    :param data: Request object containing:
        - external_business_id: Company-defined business ID
    :type data: ListStoreRequest

    :return: ListStoreResponse containing:
        - result: List of Store Objects 
    :rtype: ListStoreResponse
    :raises HTTPException: Various status codes for different error conditions
    """
    external_id = data.external_business_id
    response = doordash_request(
        method="GET",
        url=f"https://openapi.doordash.com/developer/v1/businesses/{external_id}/stores",
    )
    return {"data": response}

@app.post("/accept_quote", response_model=DoorDashResponse)
async def accept_quote(data: AcceptQuoteRequest = Body(...)):
    """
    Accept a previously created quote by external_delivery_id.
    """
    external_id = data.external_delivery_id
    payload = data.model_dump(exclude={"external_delivery_id"}, exclude_unset=True)
    response = doordash_request(
        method="POST",
        url=f"https://openapi.doordash.com/drive/v2/quotes/{external_id}/accept",
        json_data=payload,
    )
    return {"data": response}


@app.post("/create_delivery", response_model=DoorDashResponse)
async def create_delivery(data: CreateDeliveryRequest = Body(...)):
    """
    Create a delivery directly without going through quote flow.
    """
    response = doordash_request(
        method="POST",
        url="https://openapi.doordash.com/drive/v2/deliveries",
        json_data=data.model_dump(exclude_unset=True),
    )
    return {"data": response}

@app.post("/get_delivery_request", response_model=DoorDashResponse)
async def get_delivery_request(data: GetDeliveryRequest = Body(...)):
    external_delivery_id = data.external_delivery_id
    response = doordash_request(
        method="GET",
        url=f"https://openapi.doordash.com/drive/v2/deliveries/{external_delivery_id}"
    )
    return {"data": response}

@app.get("/get_delivery/{external_delivery_id}", response_model=DoorDashResponse)
async def get_delivery(external_delivery_id: str):
    """
    Retrieve details and status of a delivery.
    """
    response = doordash_request(
        method="GET",
        url=f"https://openapi.doordash.com/drive/v2/deliveries/{external_delivery_id}",
    )
    return {"data": response}


@app.patch("/update_delivery", response_model=DoorDashResponse)
async def update_delivery(data: UpdateDeliveryRequest = Body(...)):
    """
    Update fields of an existing delivery.
    """
    external_id = data.external_delivery_id
    payload = data.model_dump(exclude={"external_delivery_id"}, exclude_unset=True)
    response = doordash_request(
        method="PATCH",
        url=f"https://openapi.doordash.com/drive/v2/deliveries/{external_id}",
        json_data=payload,
    )
    return {"data": response}


@app.put("/cancel_delivery", response_model=DoorDashResponse)
async def cancel_delivery(data: CancelDeliveryRequest = Body(...)):
    """
    Cancel a delivery.
    """
    response = doordash_request(
        method="PUT",
        url=f"https://openapi.doordash.com/drive/v2/deliveries/{data.external_delivery_id}/cancel",
    )
    return {"data": response}


@app.get("/list_businesses", response_model=DoorDashResponse)
async def list_businesses(activationStatus: Optional[str] = None, continuationToken: Optional[str] = None):
    """
    List all businesses associated with your developer account.
    """
    params = {}
    if activationStatus:
        params["activationStatus"] = activationStatus
    if continuationToken:
        params["continuationToken"] = continuationToken

    url = "https://openapi.doordash.com/developer/v1/businesses"
    if params:
        import urllib.parse
        url += "?" + urllib.parse.urlencode(params)

    response = doordash_request(method="GET", url=url)
    return {"data": response}


# Add more endpoints as needed (get_business, create_store, etc.)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "DoorDash Drive API"}
