from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from config.merchant_config import config as internal_config
# ========================
# Pydantic Models
# ========================

class DeliveryBase(BaseModel):
    external_delivery_id: str = Field(..., description="Your internal reference ID for the delivery")
    locale: Optional[str] = None
    order_fulfillment_method: Optional[str] = None
    origin_facility_id: Optional[str] = None
    pickup_address: str = Field(internal_config.PICKUP_ADDRESS)
    pickup_business_name: Optional[str] = None
    pickup_phone_number: str = Field(internal_config.PICKUP_PHONE_NUMBER)
    pickup_instructions: Optional[str] = "Walk inside to pick up order."
    pickup_reference_tag: Optional[str] = None
    pickup_external_business_id: str = Field(internal_config.PICKUP_EXTERNAL_BUSINESS_ID, description="")
    pickup_external_store_id: str = Field(default_factory=lambda: internal_config.PICKUP_EXTERNAL_STORE_ID)
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
    dropoff_address_components:Dict[str, Any] = Field(...,description= "")
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

class ListStoreRequest(BaseModel):
    """
    Request for list of company's stores registered with Doordash Drive API
    """
    external_business_id: str = internal_config.PICKUP_EXTERNAL_BUSINESS_ID
class ListStoreResponse(BaseModel):
    """
    Response for list of company's stores registered with Doordash Drive API
    """
    data: Dict[str, Any]

class GetDeliveryRequest(BaseModel):
    """
    Get the status of a doordash delivery given its external delivery id
    """
    external_delivery_id: str = Field(..., description="external delivery id")

# Generic response model (you can expand with specific ones if desired)
class DoorDashResponse(BaseModel):
    data: Dict[str, Any]
