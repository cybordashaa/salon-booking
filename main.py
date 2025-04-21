# app.py
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from src.config.config import supabase
from fastapi.middleware.cors import CORSMiddleware
from src.routes.auth.router import router as auth_router
from src.routes.service.router import router as service_router
from src.routes.staff.router import router as staff_router
from src.routes.apointment.router import router as appointment_router
from src.routes.review.router import router as review_router
app = FastAPI(title="Salon Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(service_router, prefix="/services")
app.include_router(staff_router, prefix="/staff")
app.include_router(appointment_router, prefix="/appointments")
app.include_router(review_router, prefix="/reviews")
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)