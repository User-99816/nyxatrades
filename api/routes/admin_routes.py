from fastapi import APIRouter
from config.supabase_client import supabase
import random
import string

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==========================================
# GENERATE LICENSE KEY
# ==========================================

def generate_license(plan: str):

    prefix = f"NYXA-{plan}-"

    suffix = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=8)
    )

    return prefix + suffix


# ==========================================
# CREATE LICENSE
# ==========================================

@router.post("/create-license")
def create_license(payload: dict):

    email = payload.get("email")
    plan = payload.get("plan", "PRO")

    if not email:
        return {"message": "Email required"}

    license_key = generate_license(plan)

    # Insert into Supabase
    result = supabase.table("licenses").insert({
        "user_email": email,
        "license_key": license_key,
        "plan": plan,
        "status": "active",
        "activated": False
    }).execute()

    return {
        "message": "License created",
        "license_key": license_key
    }