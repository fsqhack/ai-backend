from pydantic import BaseModel
from typing import Dict, List, Optional

class LocationSchema(BaseModel):
    latitude: float
    longitude: float

class AddUserSchema(BaseModel):
    user_id: str
    name: str
    email: str
    whatsapp_number: str
    location: LocationSchema

class FieldLocationSchema(BaseModel):
    latitude: float
    longitude: float

class AddFieldSchema(BaseModel):
    field_id: str
    user_id: str
    field_name: str
    field_location: FieldLocationSchema
    sensor_hub_id: str
    crop_type: str
    user_texts: List[str] = []

class ProviderSchema(BaseModel):
    name: str
    contact: str
    email: str
    address: str