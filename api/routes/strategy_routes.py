from fastapi import APIRouter, HTTPException

from services.strategy_performance_service import (
    get_strategy,
    get_all_strategies,
    get_best_strategy,
    get_worst_strategy,
    get_top_strategies,
    get_strategy_rankings,
    reset_strategy
)

router = APIRouter(
    prefix="/strategy",
    tags=["Strategy Analytics"]
)


# ==========================================
# GET ALL STRATEGIES
# ==========================================

@router.get("/")
def get_all():

    return {
        "count": len(get_all_strategies()),
        "strategies": get_all_strategies()
    }


# ==========================================
# GET STRATEGY RANKINGS
# ==========================================

@router.get("/rankings")
def rankings():

    return {
        "rankings": get_strategy_rankings()
    }


# ==========================================
# GET TOP STRATEGIES
# ==========================================

@router.get("/top")
def top_strategies(limit: int = 5):

    return {
        "count": limit,
        "strategies": get_top_strategies(limit)
    }


# ==========================================
# GET BEST STRATEGY
# ==========================================

@router.get("/best")
def best_strategy():

    strategy = get_best_strategy()

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail="No strategy data found"
        )

    return strategy


# ==========================================
# GET WORST STRATEGY
# ==========================================

@router.get("/worst")
def worst_strategy():

    strategy = get_worst_strategy()

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail="No strategy data found"
        )

    return strategy


# ==========================================
# GET SINGLE STRATEGY
# ==========================================

@router.get("/{strategy_name}")
def strategy_details(strategy_name: str):

    strategy = get_strategy(strategy_name)

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail="Strategy not found"
        )

    return strategy


# ==========================================
# RESET STRATEGY STATS
# ==========================================

@router.post("/{strategy_name}/reset")
def reset_strategy_stats(strategy_name: str):

    strategy = get_strategy(strategy_name)

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail="Strategy not found"
        )

    reset_strategy(strategy_name)

    return {
        "success": True,
        "message": f"{strategy_name} statistics reset"
    }