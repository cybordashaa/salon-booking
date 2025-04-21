from fastapi import HTTPException
from src.config.config import supabase
from src.routes.apointment.models import AppointmentCreate
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter
import json
router = APIRouter()

@router.post("/")
async def create_appointment(appointment: AppointmentCreate):
    try:
        # Get service details to calculate end time
        service_response = supabase.table("services") \
            .select("duration") \
            .eq("id", appointment.service_id) \
            .execute()

        if not service_response.data:
            raise HTTPException(status_code=404, detail="Service not found")

        service_duration = service_response.data[0]["duration"]
        end_time = appointment.start_time + timedelta(minutes=service_duration)

        # Check for conflicts
        conflict_check = supabase.table("appointments") \
            .select("id") \
            .eq("staff_id", appointment.staff_id) \
            .lt("end_time", end_time.isoformat()) \
            .gt("start_time", appointment.start_time.isoformat()) \
            .not_.eq("status", "cancelled") \
            .execute()

        if conflict_check.data:
            raise HTTPException(status_code=409, detail="This time slot is already booked")

        # Start transaction
        response = supabase.rpc('begin_transaction').execute()

        try:
            # Create appointment
            appointment_data = {
                "customer_id": appointment.customer_id,
                "staff_id": appointment.staff_id,
                "service_id": appointment.service_id,
                "start_time": appointment.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "notes": appointment.notes,
                "status": "booked"
            }

            response = supabase.table("appointments").insert(appointment_data).execute()

            # Create notification for confirmation
            notification_data = {
                "user_id": appointment.customer_id,
                "appointment_id": response.data[0]["id"],
                "type": "confirmation", 
                "delivery_method": "email",
                "status": "pending"
            }

            supabase.table("notifications").insert(notification_data).execute()

            # Commit transaction
            supabase.rpc('commit_transaction').execute()

            return response.data[0]

        except Exception as e:
            # Rollback transaction on error
            supabase.rpc('rollback_transaction').execute()
            raise e

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.post("/transaction")
async def create_appointment_transaction(appointment: AppointmentCreate):
    try:
        response = supabase.rpc(
            "create_appointment", 
            {
                "p_customer_id": appointment.customer_id,
                "p_staff_id": appointment.staff_id,
                "p_service_id": appointment.service_id,
                "p_start_time": appointment.start_time.isoformat(),
                "p_notes": appointment.notes
            }
        ).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to create appointment")
    except Exception as e:
        # Extract error message from Supabase error response
        error_message = str(e)
        if "details" in error_message:
            try:
                error_details = json.loads(error_message)
                error_message = error_details.get("message", error_message)
            except:
                pass
        
        raise HTTPException(status_code=400, detail=error_message)

@router.get("/customer/{customer_id}")
async def get_customer_appointments(customer_id: str, status: Optional[str] = None):
    query = supabase.table("appointments") \
        .select("*, services(*), staff_profiles(*, users(first_name, last_name))") \
        .eq("customer_id", customer_id)

    if status:
        query = query.eq("status", status)

    query = query.order("start_time", desc=False)

    response = query.execute()
    return response.data


@router.get("/staff/{staff_id}")
async def get_staff_appointments(staff_id: str, date: Optional[str] = None):
    query = supabase.table("appointments") \
        .select("*, services(*), users(first_name, last_name)") \
        .eq("staff_id", staff_id)

    if date:
        query = query.gte("start_time", f"{date}T00:00:00").lt("start_time", f"{date}T23:59:59")

    query = query.order("start_time", desc=False)

    response = query.execute()
    return response.data


@router.put("/{appointment_id}/status")
async def update_appointment_status(appointment_id: str, status: str):
    valid_statuses = ["booked", "confirmed", "completed", "cancelled", "no_show"]

    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of {', '.join(valid_statuses)}"
        )

    try:
        # Get appointment customer ID for notification
        appointment_response = supabase.table("appointments") \
            .select("customer_id") \
            .eq("id", appointment_id) \
            .execute()

        if not appointment_response.data:
            raise HTTPException(status_code=404, detail="Appointment not found")

        customer_id = appointment_response.data[0]["customer_id"]

        # Update appointment status
        response = supabase.table("appointments") \
            .update({"status": status, "updated_at": datetime.now().isoformat()}) \
            .eq("id", appointment_id) \
            .execute()

        # Create notification for status update
        if status in ["confirmed", "cancelled"]:
            notification_data = {
                "user_id": customer_id,
                "appointment_id": appointment_id,
                "type": "confirmation" if status == "confirmed" else "cancellation",
                "delivery_method": "email",
                "status": "pending"
            }

            supabase.table("notifications").insert(notification_data).execute()

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
