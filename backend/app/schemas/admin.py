from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ProviderConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    role: str
    provider_label: str
    base_url: str | None
    api_key_set: bool
    model_name: str
    temperature: float | None
    updated_at: datetime

class ProviderConfigUpdateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider_label: str
    base_url: str | None = None
    model_name: str
    temperature: float | None = None
    api_key: str | None = None
    clear_api_key: bool = False
