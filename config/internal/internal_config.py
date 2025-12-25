from typing import Protocol
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class InternalConfigProtocol(Protocol):
    DOORDASH_DEVELOPER_ID : str
    DOORDASH_KEY_ID : str
    DOORDASH_SIGNING_SECRET : str
    DOORDASH_DB_PW : str
    DOORDASH_WEBHOOK_ID : str
    DOORDASH_WEBHOOK_SECRET : str

class InternalConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="config/internal/.env",
        case_sensitive=True,
        extra="forbid",  # prevents typos in env vars
    )
    DOORDASH_DEVELOPER_ID : str = Field(..., description="")
    DOORDASH_KEY_ID : str = Field(..., description="")
    DOORDASH_SIGNING_SECRET : str = Field(..., description="")
    DOORDASH_DB_PW : str = Field(...,description="")
    DOORDASH_WEBHOOK_ID : str = Field(...,description="")
    DOORDASH_WEBHOOK_SECRET : str = Field(...,description="")
    
config: InternalConfigProtocol = InternalConfig(_env_file="config/internal/.env")  # type: ignore
