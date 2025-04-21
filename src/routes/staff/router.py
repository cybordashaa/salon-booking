from fastapi import HTTPException
from src.config.config import supabase
from fastapi import APIRouter
from datetime import datetime, timedelta
router = APIRouter()

@router.get("/")
async def get_staff_members():
    response = supabase.table("staff_profiles") \
        .select("*, users(first_name, last_name, email)") \
        .eq("is_active", True) \
        .execute()

    return response.data


@router.get("/{staff_id}/services")
async def get_staff_services(staff_id: str):
    response = supabase.table("staff_services") \
        .select("services(*)") \
        .eq("staff_id", staff_id) \
        .execute()

    return [item["services"] for item in response.data]


@router.get("/{staff_id}/availability")
async def get_staff_availability(staff_id: str, date: str):
    try:
        # Convert string date to datetime
        target_date = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = target_date.weekday()

        # Get working hours
        working_hours_response = supabase.table("working_hours") \
            .select("*") \
            .eq("staff_id", staff_id) \
            .eq("day_of_week", day_of_week) \
            .eq("is_working", True) \
            .execute()

        if not working_hours_response.data:
            return {"available_slots": []}

        working_hours = working_hours_response.data[0]

        # Get time off for this date
        time_off_response = supabase.table("time_off") \
            .select("*") \
            .eq("staff_id", staff_id) \
            .lte("start_datetime", f"{date}T23:59:59") \
            .gte("end_datetime", f"{date}T00:00:00") \
            .execute()

        # Get booked appointments for this date
        appointments_response = supabase.table("appointments") \
            .select("*") \
            .eq("staff_id", staff_id) \
            .lte("start_time", f"{date}T23:59:59") \
            .gte("end_time", f"{date}T00:00:00") \
            .not_.eq("status", "cancelled") \
            .execute()

        # Calculate available slots (simplified logic - would need more complex implementation in production)
        start_time = datetime.strptime(f"{working_hours['start_time']}", "%H:%M:%S").time()
        end_time = datetime.strptime(f"{working_hours['end_time']}", "%H:%M:%S").time()

        # Create datetime objects for start and end times
        start_datetime = datetime.combine(target_date, start_time)
        end_datetime = datetime.combine(target_date, end_time)

        # Generate slots in 30-minute increments
        slots = []
        current = start_datetime

        while current < end_datetime:
            slot_end = current + timedelta(minutes=30)

            # Check if this slot conflicts with any booked appointments
            is_available = True

            for appointment in appointments_response.data:
                appt_start = datetime.fromisoformat(appointment["start_time"].replace("Z", "+00:00"))
                appt_end = datetime.fromisoformat(appointment["end_time"].replace("Z", "+00:00"))

                if (current < appt_end and slot_end > appt_start):
                    is_available = False
                    break

            # Check if this slot conflicts with any time off
            for off_time in time_off_response.data:
                off_start = datetime.fromisoformat(off_time["start_datetime"].replace("Z", "+00:00"))
                off_end = datetime.fromisoformat(off_time["end_datetime"].replace("Z", "+00:00"))

                if (current < off_end and slot_end > off_start):
                    is_available = False
                    break

            if is_available:
                slots.append({
                    "start": current.strftime("%H:%M"),
                    "end": slot_end.strftime("%H:%M")
                })

            current = slot_end

        return {"available_slots": slots}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))