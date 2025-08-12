"""
Main API router
Following SOLID principles - Single Responsibility for API routing
"""

from fastapi import APIRouter

from app.api.v1.endpoints import transactions, compliance

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"]
)

api_router.include_router(
    compliance.router,
    prefix="/compliance",
    tags=["compliance"]
)

@api_router.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "APRA Compliance Monitoring API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health"
    }
