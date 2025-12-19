"""
title: DoorDash Drive & Developer API
author: YourName
description: FastAPI wrapper for DoorDash Drive delivery and business/store management APIs
required_open_webui_version: 0.4.0
requirements: fastapi, pydantic, requests, pyjwt[crypto]
version: 1.0.0
licence: MIT
"""

import os
import time
import json
import base64  # Add this import at the top

from typing import Any, Dict, List, Optional, Union

import jwt
import requests
from fastapi import FastAPI, Body, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

app = FastAPI(
    title="DoorDash Drive API",
    version="1.0.0",
    description="Provides HTTP endpoints for DoorDash Drive (quotes, deliveries) and Developer (businesses, stores) APIs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DEVELOPER_ID = os.getenv("DOORDASH_DEVELOPER_ID")
KEY_ID = os.getenv("DOORDASH_KEY_ID")
SIGNING_SECRET = os.getenv("DOORDASH_SIGNING_SECRET")

if not all([DEVELOPER_ID, KEY_ID, SIGNING_SECRET]):
    raise RuntimeError(
        "Missing required environment variables: DOORDASH_DEVELOPER_ID, DOORDASH_KEY_ID, DOORDASH_SIGNING_SECRET"
    )


def generate_jwt_token() -> str:
    """Generate a short-lived JWT for DoorDash API authentication (5-minute expiry)"""
    issued_at = int(time.time())
    payload = {
        "aud": "doordash",
        "iss": DEVELOPER_ID,
        "kid": KEY_ID,
        "exp": issued_at + 300,
        "iat": issued_at,
    }
    headers = {"alg": "HS256", "dd-ver": "DD-JWT-V1"}

    # Since we validated at startup, these are guaranteed to be str
    # But to help type checkers, we assert non-None
    assert SIGNING_SECRET is not None, "SIGNING_SECRET is missing (should have been validated at startup)"

    secret = SIGNING_SECRET

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
        response = requests.request(method, url, json=json_data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        # Now response is guaranteed to exist because raise_for_status() was called
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
# Pydantic Models
# ========================

class DeliveryBase(BaseModel):
    external_delivery_id: str = Field(..., description="Your internal reference ID for the delivery")
    locale: Optional[str] = None
    order_fulfillment_method: Optional[str] = None
    origin_facility_id: Optional[str] = None
    pickup_address: str = "2110 N Alameda Blvd, Las Cruces, NM"
    pickup_business_name: Optional[str] = None
    pickup_phone_number: Optional[str] = None
    pickup_instructions: Optional[str] = None
    pickup_reference_tag: Optional[str] = None
    pickup_external_business_id: Optional[str] = None
    pickup_external_store_id: Optional[str] = None
    pickup_verification_metadata: Optional[Dict[str, Any]] = None

    dropoff_address: str = Field(..., description="Required dropoff address")
    dropoff_business_name: Optional[str] = None
    dropoff_location: Optional[Dict[str, Any]] = None
    dropoff_phone_number: str = Field(..., description="Required dropoff contact phone")
    dropoff_instructions: Optional[str] = None
    dropoff_contact_given_name: Optional[str] = None
    dropoff_contact_family_name: Optional[str] = None
    dropoff_contact_send_notifications: Optional[bool] = None
    dropoff_options: Optional[Dict[str, Any]] = None
    dropoff_address_components: Optional[Dict[str, Any]] = None
    dropoff_pin_code_verification_metadata: Optional[Dict[str, Any]] = None

    shopping_options: Optional[Dict[str, Any]] = None
    order_value: Optional[int] = Field(None, description="Order value in cents")
    items: Optional[List[Dict[str, Any]]] = None
    pickup_time: Optional[str] = None
    dropoff_time: Optional[str] = None
    pickup_window: Optional[Dict[str, Any]] = None
    dropoff_window: Optional[Dict[str, Any]] = None
    customer_expected_sla: Optional[Any] = None
    expires_by: Optional[Any] = None
    shipping_label_metadata: Optional[Dict[str, Any]] = None
    contactless_dropoff: Optional[bool] = None
    action_if_undeliverable: Optional[str] = None
    tip: Optional[int] = Field(None, description="Tip amount in cents")
    order_contains: Optional[Dict[str, Any]] = None
    dasher_allowed_vehicles: Optional[List[str]] = None
    dropoff_requires_signature: Optional[bool] = None
    promotion_id: Optional[str] = None
    dropoff_cash_on_delivery: Optional[int] = None
    order_route_type: Optional[str] = None
    order_route_items: Optional[List[str]] = None


class CreateQuoteRequest(DeliveryBase):
    """Request body for creating a delivery quote"""
    pass


class AcceptQuoteRequest(BaseModel):
    external_delivery_id: str
    tip: Optional[int] = None
    dropoff_phone_number: Optional[str] = None


class CreateDeliveryRequest(DeliveryBase):
    """Request body for creating a delivery directly"""
    pass


class UpdateDeliveryRequest(BaseModel):
    external_delivery_id: str
    # All fields optional for PATCH
    pickup_address: Optional[str] = None
    pickup_business_name: Optional[str] = None
    pickup_phone_number: Optional[str] = None
    pickup_instructions: Optional[str] = None
    pickup_reference_tag: Optional[str] = None
    pickup_external_business_id: Optional[str] = None
    pickup_external_store_id: Optional[str] = None
    dropoff_address: Optional[str] = None
    dropoff_business_name: Optional[str] = None
    dropoff_phone_number: Optional[str] = None
    dropoff_instructions: Optional[str] = None
    tip: Optional[int] = None
    contactless_dropoff: Optional[bool] = None
    action_if_undeliverable: Optional[str] = None
    # ... add more as needed


class CancelDeliveryRequest(BaseModel):
    external_delivery_id: str


class ListBusinessesRequest(BaseModel):
    activationStatus: Optional[str] = Field(None, alias="activationStatus")
    continuationToken: Optional[str] = Field(None, alias="continuationToken")


# Generic response model (you can expand with specific ones if desired)
class DoorDashResponse(BaseModel):
    data: Dict[str, Any]


# ========================
# Endpoints
# ========================

@app.post("/create_quote", response_model=DoorDashResponse)
async def create_quote(data: CreateQuoteRequest = Body(...)):
    """
    Create a delivery quote using DoorDash Drive API.
    """
    response = doordash_request(
        method="POST",
        url="https://openapi.doordash.com/drive/v2/quotes",
        json_data=data.dict(exclude_unset=True),
    )
    return {"data": response}


@app.post("/accept_quote", response_model=DoorDashResponse)
async def accept_quote(data: AcceptQuoteRequest = Body(...)):
    """
    Accept a previously created quote by external_delivery_id.
    """
    external_id = data.external_delivery_id
    payload = data.dict(exclude={"external_delivery_id"}, exclude_unset=True)
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
        json_data=data.dict(exclude_unset=True),
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
    payload = data.dict(exclude={"external_delivery_id"}, exclude_unset=True)
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
