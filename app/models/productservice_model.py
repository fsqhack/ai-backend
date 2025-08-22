from pydantic import BaseModel
from typing import Optional

class ProviderSchema(BaseModel):
    name: str
    contact: str
    email: str
    address: str

class AddProductSchema(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    description: str
    usage: str
    image_url: Optional[str] = None
    provider: ProviderSchema

class AddServiceSchema(BaseModel):
    service_id: str
    name: str
    description: str
    provider: ProviderSchema
