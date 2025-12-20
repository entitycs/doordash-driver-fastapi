from typing import Protocol
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class MerchantConfigProtocol(Protocol):
    PICKUP_EXTERNAL_BUSINESS_ID : str
    PICKUP_EXTERNAL_STORE_ID : str
    PICKUP_ADDRESS : str
    PICKUP_PHONE_NUMBER : str

class MerchantConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="config/.env",
        case_sensitive=True,
        extra="forbid",  # prevents typos in env vars-
    )
    # Required from env
    PICKUP_EXTERNAL_BUSINESS_ID : str = Field(..., description="Required: Merchant business ID")
    PICKUP_EXTERNAL_STORE_ID : str = Field(..., description="Required: Merchant store ID")
    PICKUP_ADDRESS : str = Field(...,description="Required: Merchant store address")
    PICKUP_PHONE_NUMBER :str = Field(...,description="Required: Merchant store phone #")

config: MerchantConfigProtocol = MerchantConfig()  # type: ignore
