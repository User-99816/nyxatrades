from fastapi import APIRouter, HTTPException

from services.strategy_allocator_service import (
    get_strategy_allocations,
    get_best_allocation,
    get_portfolio_summary,
    strategy_is_enabled,
    get_strategy_risk_multiplier
)

from services.strategy_performance_service import (
    get_strategy
)

router = APIRouter(
    prefix="/strategy-allocation",
    tags=["Strategy Allocation"]
)


# ==========================================
# PORTFOLIO SUMMARY
# ==========================================

@router.get("/summary")
def portfolio_summary():

    return get_portfolio_summary()


# ==========================================
# ALL ALLOCATIONS
# ==========================================

@router.get("/")
def allocations():

    data = get_strategy_allocations()

    return {
        "count": len(data),
        "allocations": data
    }


# ==========================================
# BEST ALLOCATION
# ==========================================

@router.get("/best")
def best_allocation():

    allocation = get_best_allocation()

    if not allocation:
        raise HTTPException(
            status_code=404,
            detail="No allocation data available"
        )

    return allocation


# ==========================================
# STRATEGY STATUS
# ==========================================

@router.get("/{strategy_name}/status")
def strategy_status(strategy_name: str):

    strategy = get_strategy(strategy_name)

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail="Strategy not found"
        )

    return {
        "strategy": strategy_name,
        "enabled": strategy_is_enabled(strategy_name),
        "risk_multiplier": get_strategy_risk_multiplier(
            strategy_name
        )
    }


# ==========================================
# STRATEGY ALLOCATION DETAILS
# ==========================================

@router.get("/{strategy_name}")
def strategy_allocation(strategy_name: str):

    strategy = get_strategy(strategy_name)

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail="Strategy not found"
        )

    allocations = get_strategy_allocations()

    allocation = next(
        (
            item
            for item in allocations
            if item["strategy"] == strategy_name
        ),
        None
    )

    if not allocation:
        raise HTTPException(
            status_code=404,
            detail="Allocation not found"
        )

    return {
        "strategy": strategy,
        "allocation": allocation
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@router.get("/health/check")
def allocation_health():

    allocations = get_strategy_allocations()

    enabled = len([
        a for a in allocations
        if a["enabled"]
    ])

    disabled = len([
        a for a in allocations
        if not a["enabled"]
    ])

    return {
        "status": "OK",
        "enabled_strategies": enabled,
        "disabled_strategies": disabled,
        "total_strategies": len(allocations)
    }