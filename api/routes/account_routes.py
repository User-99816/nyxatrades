from fastapi import APIRouter, HTTPException

from services.license_service import validate_license
from services.risk_service import update_risk_metrics

router = APIRouter(
    prefix="/account",
    tags=["Account"]
)


@router.post("/metrics")
async def update_account_metrics(
    payload: dict
):

    api_key = payload.get("api_key")

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key Missing"
        )

    license_data = validate_license(api_key)

    if not license_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid License"
        )

    update_risk_metrics(
        user_email=license_data["user_email"],

        trades_today=payload.get(
            "trades_today",
            0
        ),

        daily_loss_percent=payload.get(
            "daily_loss_percent",
            0
        ),

        current_drawdown_percent=payload.get(
            "current_drawdown_percent",
            0
        ),

        account_balance=payload.get(
            "account_balance",
            0
        ),

        account_equity=payload.get(
            "account_equity",
            0
        )
    )

    return {
        "success": True,
        "message": "Metrics Updated"
    }