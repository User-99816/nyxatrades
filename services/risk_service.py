from config.supabase_client import supabase


# ==========================================
# GET USER RISK METRICS
# ==========================================

def get_risk_metrics(user_email: str):

    response = (
        supabase
        .table("risk_metrics")
        .select("*")
        .eq("user_email", user_email)
        .limit(1)
        .execute()
    )

    if not response.data:
        return {
            "trades_today": 0,
            "daily_loss_percent": 0,
            "current_drawdown_percent": 0,
            "account_balance": 0,
            "account_equity": 0,
            "kill_switch_active": False
        }

    return response.data[0]


# ==========================================
# CREATE / UPDATE USER METRICS
# ==========================================

def update_risk_metrics(
    user_email: str,
    trades_today: int,
    daily_loss_percent: float,
    current_drawdown_percent: float,
    account_balance: float,
    account_equity: float,
    kill_switch_active: bool = False
):

    existing = (
        supabase
        .table("risk_metrics")
        .select("id")
        .eq("user_email", user_email)
        .limit(1)
        .execute()
    )

    payload = {
        "trades_today": trades_today,
        "daily_loss_percent": daily_loss_percent,
        "current_drawdown_percent": current_drawdown_percent,
        "account_balance": account_balance,
        "account_equity": account_equity,
        "kill_switch_active": kill_switch_active
    }

    if existing.data:

        return (
            supabase
            .table("risk_metrics")
            .update(payload)
            .eq("user_email", user_email)
            .execute()
        )

    payload["user_email"] = user_email

    return (
        supabase
        .table("risk_metrics")
        .insert(payload)
        .execute()
    )


# ==========================================
# KILL SWITCH
# ==========================================

def activate_kill_switch(user_email: str):

    return (
        supabase
        .table("risk_metrics")
        .update({
            "kill_switch_active": True
        })
        .eq("user_email", user_email)
        .execute()
    )


def deactivate_kill_switch(user_email: str):

    return (
        supabase
        .table("risk_metrics")
        .update({
            "kill_switch_active": False
        })
        .eq("user_email", user_email)
        .execute()
    )


# ==========================================
# RESET DAILY METRICS
# ==========================================

def reset_daily_metrics(user_email: str):

    return (
        supabase
        .table("risk_metrics")
        .update({
            "trades_today": 0,
            "daily_loss_percent": 0
        })
        .eq("user_email", user_email)
        .execute()
    )