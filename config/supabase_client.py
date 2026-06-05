from supabase import create_client, Client

from config.settings import (
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)


# ==========================================
# VALIDATION
# ==========================================

if not SUPABASE_URL:
    raise ValueError(
        "SUPABASE_URL is missing in .env"
    )

if not SUPABASE_SERVICE_KEY:
    raise ValueError(
        "SUPABASE_SERVICE_KEY is missing in .env"
    )


# ==========================================
# CREATE CLIENT
# ==========================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)