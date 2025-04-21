from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AppointmentCreate(BaseModel):
    customer_id: str
    staff_id: str
    service_id: str
    start_time: datetime
    notes: Optional[str] = None