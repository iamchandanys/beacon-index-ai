import uuid

from pydantic import BaseModel, Field

class UserRegistrationModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    password: str
