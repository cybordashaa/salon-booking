from pydantic import BaseModel
from typing import Optional


class Service(BaseModel):
    name: str
    description: Optional[str] = None
    duration: int
    price: float
    category: Optional[str] = None
    is_active: bool = True