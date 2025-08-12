"""
APRA Compliance Monitoring Application
Main FastAPI application following SOLID principles
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.core.exceptions import ComplianceException

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting APRA Compliance Monitoring Application")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down APRA Compliance Monitoring Application")

def create_application() -> FastAPI:
    """
    Create FastAPI application with proper configuration
    Following SOLID principles - Single Responsibility
    """
    settings = get_settings()
    
    app = FastAPI(
        title="APRA Compliance Monitoring API",
        description="Real-time compliance monitoring and violation detection system",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Global exception handler
    @app.exception_handler(ComplianceException)
    async def compliance_exception_handler(request, exc: ComplianceException):
        logger.error(
            "Compliance violation detected",
            violation_type=exc.violation_type,
            severity=exc.severity,
            details=exc.details
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Compliance Violation",
                "violation_type": exc.violation_type,
                "severity": exc.severity,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint for Kubernetes"""
        return {"status": "healthy", "service": "apra-compliance-monitoring"}
    
    return app

app = create_application()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
