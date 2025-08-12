"""
Transaction API endpoints
Following SOLID principles and RESTful design
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import structlog

from app.core.database import get_db
from app.services.transaction_service import TransactionService
from app.models.transaction import Transaction
from app.core.exceptions import ComplianceException, DataQualityViolation

logger = structlog.get_logger()

router = APIRouter()


# Pydantic models for request/response
class TransactionCreate(BaseModel):
    """Transaction creation request model"""
    account_id: str = Field(..., description="Account identifier")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field("AUD", description="Currency code (3 letters)")
    transaction_type: str = Field(..., description="Transaction type: DEBIT, CREDIT, or TRANSFER")
    description: Optional[str] = Field(None, description="Transaction description")
    counterparty_account: Optional[str] = Field(None, description="Counterparty account")
    counterparty_name: Optional[str] = Field(None, description="Counterparty name")
    counterparty_bank: Optional[str] = Field(None, description="Counterparty bank")
    transaction_channel: str = Field("ONLINE", description="Transaction channel")
    location_country: str = Field("AUS", description="Transaction country")
    location_city: Optional[str] = Field(None, description="Transaction city")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    
    class Config:
        schema_extra = {
            "example": {
                "account_id": "ACC123456",
                "amount": 5000.00,
                "currency": "AUD",
                "transaction_type": "DEBIT",
                "description": "Online purchase",
                "counterparty_account": "MERCHANT001",
                "counterparty_name": "Online Store Pty Ltd",
                "transaction_channel": "ONLINE",
                "location_country": "AUS",
                "location_city": "Sydney"
            }
        }


class TransactionResponse(BaseModel):
    """Transaction response model"""
    transaction_id: str
    account_id: str
    amount: float
    currency: str
    transaction_type: str
    description: Optional[str]
    counterparty_account: Optional[str]
    counterparty_name: Optional[str]
    transaction_channel: str
    location_country: str
    location_city: Optional[str]
    transaction_timestamp: datetime
    is_flagged: bool
    risk_score: float
    compliance_status: str
    
    class Config:
        from_attributes = True


class TransactionStatistics(BaseModel):
    """Transaction statistics response model"""
    total_transactions: int
    total_amount: float
    average_amount: float
    flagged_count: int
    flagged_percentage: float
    high_value_count: int
    international_count: int


@router.post("/", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction with automatic compliance checking
    
    This endpoint creates a transaction and automatically evaluates it against
    all active APRA compliance rules. Any violations will be flagged and logged.
    """
    try:
        service = TransactionService(db)
        
        # Convert Pydantic model to dict
        transaction_data = transaction.dict()
        
        # Create transaction with compliance validation
        created_transaction = service.create_transaction(transaction_data)
        
        logger.info(
            "Transaction created via API",
            transaction_id=created_transaction.transaction_id,
            account_id=created_transaction.account_id,
            amount=created_transaction.amount,
            flagged=created_transaction.is_flagged
        )
        
        return TransactionResponse.from_orm(created_transaction)
        
    except DataQualityViolation as e:
        logger.error("Data quality violation in transaction creation", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
    except ComplianceException as e:
        logger.error("Compliance violation in transaction creation", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
    
    except Exception as e:
        logger.error("Unexpected error creating transaction", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific transaction by ID"""
    service = TransactionService(db)
    transaction = service.get_transaction(transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return TransactionResponse.from_orm(transaction)


@router.get("/account/{account_id}", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific account with optional filtering"""
    service = TransactionService(db)
    
    transactions = service.get_transactions_by_account(
        account_id=account_id,
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date
    )
    
    return [TransactionResponse.from_orm(t) for t in transactions]


@router.get("/flagged/list", response_model=List[TransactionResponse])
async def get_flagged_transactions(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions to return"),
    db: Session = Depends(get_db)
):
    """Get transactions flagged for compliance violations"""
    service = TransactionService(db)
    transactions = service.get_flagged_transactions(limit=limit)
    
    return [TransactionResponse.from_orm(t) for t in transactions]


@router.get("/high-value/list", response_model=List[TransactionResponse])
async def get_high_value_transactions(
    threshold: float = Query(10000.0, gt=0, description="Minimum amount threshold"),
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get high-value transactions within specified time period"""
    service = TransactionService(db)
    transactions = service.get_high_value_transactions(threshold=threshold, days=days)
    
    return [TransactionResponse.from_orm(t) for t in transactions]


@router.get("/statistics/summary", response_model=TransactionStatistics)
async def get_transaction_statistics(
    account_id: Optional[str] = Query(None, description="Optional account ID filter"),
    db: Session = Depends(get_db)
):
    """Get transaction statistics summary"""
    service = TransactionService(db)
    stats = service.get_transaction_statistics(account_id=account_id)
    
    return TransactionStatistics(**stats)


@router.post("/patterns/detect/{account_id}")
async def detect_suspicious_patterns(
    account_id: str,
    db: Session = Depends(get_db)
):
    """
    Detect suspicious transaction patterns for an account
    
    This endpoint analyzes recent transactions for the specified account
    and identifies potentially suspicious patterns such as:
    - High transaction velocity
    - Amount structuring
    - Unusual timing patterns
    """
    service = TransactionService(db)
    patterns = service.detect_suspicious_patterns(account_id)
    
    return {
        "account_id": account_id,
        "patterns_detected": len(patterns),
        "patterns": [
            {
                "pattern_id": p.pattern_id,
                "pattern_type": p.pattern_type,
                "description": p.pattern_description,
                "confidence_score": p.confidence_score,
                "detected_at": p.first_detected
            }
            for p in patterns
        ]
    }


# Example endpoint for testing compliance violations
@router.post("/test/apra-violation", response_model=TransactionResponse)
async def create_test_apra_violation(
    db: Session = Depends(get_db)
):
    """
    Create a test transaction that will trigger APRA compliance violations
    
    This endpoint is for testing purposes and creates a transaction that
    deliberately violates APRA compliance rules to demonstrate the system's
    violation detection capabilities.
    """
    service = TransactionService(db)
    
    # Create a transaction that will trigger multiple violations
    test_transaction_data = {
        "account_id": "TEST_ACCOUNT_001",
        "amount": 25000.00,  # Exceeds transaction limit
        "currency": "AUD",
        "transaction_type": "TRANSFER",
        "description": "Test APRA violation - high amount",
        "counterparty_account": "UNKNOWN_ACCOUNT",
        "counterparty_name": "Suspicious Entity",
        "transaction_channel": "ONLINE",
        "location_country": "IRN",  # High-risk country
        "location_city": "Tehran",
        "ip_address": "192.168.1.100"
    }
    
    created_transaction = service.create_transaction(test_transaction_data)
    
    logger.warning(
        "Test APRA violation transaction created",
        transaction_id=created_transaction.transaction_id,
        amount=created_transaction.amount,
        country=created_transaction.location_country,
        flagged=created_transaction.is_flagged
    )
    
    return TransactionResponse.from_orm(created_transaction)
