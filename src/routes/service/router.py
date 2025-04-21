from fastapi import HTTPException
from src.config.config import supabase
from src.routes.service.models import Service
from typing import Optional
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_services(category: Optional[str] = None):
    query = supabase.table("services").select("*")
    if category:
        query = query.eq("category", category)

    query = query.eq("is_active", True)

    response = query.execute()
    return response.data


@router.post("/")
async def create_service(service: Service):
    try:
        response = supabase.table("services").insert({
            "name": service.name,
            "description": service.description,
            "duration": service.duration,
            "price": service.price,
            "category": service.category,
            "is_active": service.is_active
        }).execute()

        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{service_id}")
async def get_service(service_id: str):
    response = supabase.table("services").select("*").eq("id", service_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Service not found")

    return response.data[0]