from fastapi import HTTPException
from src.config.config import supabase
from src.routes.auth.models import UserCreate
from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
async def register_user(user: UserCreate):
    try:
        # Register with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })

        user_id = auth_response.user.id

        # Create user record in users table
        user_data = {
            "id": user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": user.role
        }

        supabase.table("users").insert(user_data).execute()

        return {"message": "User registered successfully", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login")
async def login(email: str, password: str):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user_id": response.user.id
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

