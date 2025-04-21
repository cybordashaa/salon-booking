from pydantic import BaseModel
from typing import Optional


class ReviewCreate(BaseModel):
    appointment_id: str
    rating: int
    comment: Optional[str] = None
