from typing import Optional
import psycopg
from psycopg.types.json import Jsonb
from fastapi import APIRouter, Body
from core.models import (
    ListStoreRequest, ListStoreResponse,
    UpdateStoreRequest, CreateQuoteRequest, CancelDeliveryRequest,
    AcceptQuoteRequest, UpdateDeliveryRequest,
    GetDeliveryRequest, CreateDeliveryRequest, DoorDashResponse,  )
from fast_api_server.services.doordash_client import doordash_request
from core.logging.logger import logger
from config.merchant_config import config as settings
from config.internal.internal_config import config

router = APIRouter(prefix="/doordash", tags=["DoorDash"])

@router.post("/create_quote", response_model=DoorDashResponse)
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


@router.post("/list_stores", response_model=ListStoreResponse)
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


@router.post("/accept_quote", response_model=DoorDashResponse)
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


@router.post("/create_delivery", response_model=DoorDashResponse)
async def create_delivery(data: CreateDeliveryRequest = Body(...)):
    """
    Create a delivery directly without going through quote flow.
    """
    response = doordash_request(
        method="POST",
        url="https://openapi.doordash.com/drive/v2/deliveries",
        json_data=data.model_dump(exclude_unset=True),
    )
    try:
        if response:
            logger.info("Response received")
            conn = None
            try:
                conn = psycopg.connect(f"host=postgresql port=5432 dbname=doordash user=doordash password={config.DOORDASH_DB_PW} connect_timeout=10")
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO deliveries (store_id, order_data, dropoff_address, dropoff_phone) VALUES (%s, %s, %s, %s)",
                        (1, Jsonb(data.model_dump_json()), data.dropoff_address, data.dropoff_phone_number)
                    )
                    conn.commit()
                    logger.info("Request logged to PostgreSQL successfully")
            except Exception as db_error:
                if conn is not None:
                    conn.rollback()
                logger.error(f"Failed to log request to PostgreSQL: {str(db_error)}")
                raise
            finally:
                if conn is not None:
                    conn.close()
    except Exception as e:
        logger.error(f"Error in database operation: {str(e)}")
        raise
    return {"data": response}


@router.post("/get_delivery_request", response_model=DoorDashResponse)
async def get_delivery_request(data: GetDeliveryRequest = Body(...)):
    external_delivery_id = data.external_delivery_id
    response = doordash_request(
        method="GET",
        url=f"https://openapi.doordash.com/drive/v2/deliveries/{external_delivery_id}"
    )
    return {"data": response}


@router.patch("/update_store", response_model=DoorDashResponse)
async def update_store(data: UpdateStoreRequest):
    """
    Update fields of an existing store.
    """
    payload = data.model_dump(exclude={"external_business_id", "external_store_id"}, exclude_unset=True)
    response = doordash_request(
        method="PATCH",
        url=f"https://openapi.doordash.com/developer/v1/businesses/{settings.PICKUP_EXTERNAL_BUSINESS_ID}/stores/{settings.PICKUP_EXTERNAL_STORE_ID}",
        json_data=payload,
    )
    return {"data": response}


@router.patch("/update_delivery", response_model=DoorDashResponse)
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


@router.put("/cancel_delivery", response_model=DoorDashResponse)
async def cancel_delivery(data: CancelDeliveryRequest = Body(...)):
    """
    Cancel a delivery.
    """
    response = doordash_request(
        method="PUT",
        url=f"https://openapi.doordash.com/drive/v2/deliveries/{data.external_delivery_id}/cancel",
    )
    return {"data": response}


@router.get("/list_businesses", response_model=DoorDashResponse)
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

@router.get("/health")
async def health():
    return {"status": "healthy", "service": "DoorDash Drive API"}
