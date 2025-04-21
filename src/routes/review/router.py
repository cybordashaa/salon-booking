from fastapi import HTTPException
from src.config.config import supabase
from src.routes.review.models import ReviewCreate
from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def create_review(review: ReviewCreate):
    if not 1 <= review.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    try:
        # Check if appointment exists and belongs to the customer
        appointment_response = supabase.table("appointments") \
            .select("*") \
            .eq("id", review.appointment_id) \
            .eq("status", "completed") \
            .execute()

        if not appointment_response.data:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found or not eligible for review"
            )

        # Check if review already exists
        existing_review = supabase.table("reviews") \
            .select("*") \
            .eq("appointment_id", review.appointment_id) \
            .execute()

        if existing_review.data:
            raise HTTPException(
                status_code=409,
                detail="Review already exists for this appointment"
            )

        # Create review
        response = supabase.table("reviews").insert({
            "appointment_id": review.appointment_id,
            "rating": review.rating,
            "comment": review.comment
        }).execute()

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

