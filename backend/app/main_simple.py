"""
Simplified APRA Compliance Monitoring Application for Testing
Using in-memory SQLite database for demonstration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json

# Simple in-memory storage for demonstration
transactions_db = []
violations_db = []

app = FastAPI(
    title="APRA Compliance Monitoring API",
    description="Real-time compliance monitoring and violation detection system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TransactionCreate(BaseModel):
    account_id: str = Field(..., description="Account identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field("AUD", description="Currency code")
    transaction_type: str = Field(..., description="Transaction type")
    description: Optional[str] = Field(None, description="Transaction description")
    counterparty_account: Optional[str] = Field(None, description="Counterparty account")
    counterparty_name: Optional[str] = Field(None, description="Counterparty name")
    counterparty_bank: Optional[str] = Field(None, description="Counterparty bank")
    transaction_channel: str = Field("ONLINE", description="Transaction channel")
    location_country: str = Field("AUS", description="Transaction country")
    location_city: Optional[str] = Field(None, description="Transaction city")
    ip_address: Optional[str] = Field(None, description="Client IP address")

class TransactionResponse(BaseModel):
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

class ComplianceViolationResponse(BaseModel):
    violation_id: str
    violation_type: str
    severity: str
    title: str
    description: str
    regulatory_framework: str
    standard_reference: Optional[str]
    requirement_id: Optional[str]
    risk_score: float
    confidence_score: float
    status: str
    detected_at: datetime
    violation_data: Optional[dict]
    remediation_actions: Optional[list]

class ComplianceDashboard(BaseModel):
    total_violations: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    open_violations: int
    resolved_violations: int
    overdue_violations: int
    average_resolution_time_hours: float
    compliance_score: float

class TransactionStatistics(BaseModel):
    total_transactions: int
    total_amount: float
    average_amount: float
    flagged_count: int
    flagged_percentage: float
    high_value_count: int
    international_count: int

# Compliance Rules Implementation
def evaluate_apra_compliance(transaction_data: dict) -> List[dict]:
    """Evaluate transaction against APRA compliance rules"""
    violations = []
    
    # Rule 1: Transaction Limit (APRA-TXN-LIMIT-001)
    if transaction_data["amount"] > 10000.0:
        violations.append({
            "violation_id": str(uuid.uuid4()),
            "violation_type": "TRANSACTION_LIMIT",
            "severity": "HIGH",
            "title": f"Transaction Limit Exceeded - APRA CPS 234",
            "description": f"Transaction amount ${transaction_data['amount']:,.2f} exceeds APRA limit of $10,000.00",
            "regulatory_framework": "APRA",
            "standard_reference": "CPS 234",
            "requirement_id": "CPS234-TXN-001",
            "risk_score": min(transaction_data["amount"] / 10000.0, 10.0),
            "confidence_score": 1.0,
            "status": "OPEN",
            "detected_at": datetime.utcnow(),
            "violation_data": {
                "transaction_amount": transaction_data["amount"],
                "limit_amount": 10000.0,
                "excess_amount": transaction_data["amount"] - 10000.0,
                "violation_percentage": (transaction_data["amount"] / 10000.0) * 100
            },
            "remediation_actions": [
                "Review transaction authorization",
                "Verify customer identity", 
                "Check for suspicious activity",
                "Report to AUSTRAC if required"
            ]
        })
    
    # Rule 2: Geographic Risk (APRA-GEO-001)
    high_risk_countries = ["IRN", "PRK", "SYR", "YEM", "AFG"]
    if transaction_data.get("location_country") in high_risk_countries:
        violations.append({
            "violation_id": str(uuid.uuid4()),
            "violation_type": "SUSPICIOUS_PATTERN",
            "severity": "CRITICAL",
            "title": f"High-Risk Geographic Transaction - APRA CPS 234",
            "description": f"Transaction from high-risk country {transaction_data['location_country']} for amount ${transaction_data['amount']:,.2f}",
            "regulatory_framework": "APRA",
            "standard_reference": "CPS 234",
            "requirement_id": "CPS234-GEO-001",
            "risk_score": 8.0,
            "confidence_score": 1.0,
            "status": "OPEN",
            "detected_at": datetime.utcnow(),
            "violation_data": {
                "country_code": transaction_data["location_country"],
                "risk_category": "HIGH_RISK_COUNTRY",
                "transaction_amount": transaction_data["amount"],
                "requires_enhanced_due_diligence": True
            },
            "remediation_actions": [
                "Enhanced due diligence required",
                "Verify customer identity",
                "Check sanctions lists",
                "Report to AUSTRAC immediately"
            ]
        })
    
    return violations

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "apra-compliance-monitoring"}

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "APRA Compliance Monitoring API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health"
    }

@app.post("/api/v1/transactions/", response_model=TransactionResponse, status_code=201)
async def create_transaction(transaction: TransactionCreate):
    """Create a new transaction with automatic compliance checking"""
    
    # Create transaction record
    transaction_data = transaction.dict()
    transaction_record = {
        "transaction_id": str(uuid.uuid4()),
        "transaction_timestamp": datetime.utcnow(),
        "is_flagged": False,
        "risk_score": 0.0,
        "compliance_status": "PENDING",
        **transaction_data
    }
    
    # Evaluate compliance
    violations = evaluate_apra_compliance(transaction_data)
    
    if violations:
        transaction_record["is_flagged"] = True
        transaction_record["compliance_status"] = "UNDER_REVIEW"
        transaction_record["risk_score"] = max(v["risk_score"] for v in violations)
        
        # Store violations
        violations_db.extend(violations)
    
    # Store transaction
    transactions_db.append(transaction_record)
    
    return TransactionResponse(**transaction_record)

@app.get("/api/v1/transactions/flagged/list", response_model=List[TransactionResponse])
async def get_flagged_transactions(limit: int = 100):
    """Get transactions flagged for compliance violations"""
    flagged = [t for t in transactions_db if t.get("is_flagged", False)]
    return [TransactionResponse(**t) for t in flagged[-limit:]]

@app.get("/api/v1/transactions/high-value/list", response_model=List[TransactionResponse])
async def get_high_value_transactions(threshold: float = 10000.0, days: int = 7):
    """Get high-value transactions"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    high_value = [
        t for t in transactions_db 
        if t["amount"] >= threshold and t["transaction_timestamp"] >= cutoff_date
    ]
    return [TransactionResponse(**t) for t in high_value]

@app.get("/api/v1/transactions/statistics/summary", response_model=TransactionStatistics)
async def get_transaction_statistics():
    """Get transaction statistics summary"""
    if not transactions_db:
        return TransactionStatistics(
            total_transactions=0,
            total_amount=0.0,
            average_amount=0.0,
            flagged_count=0,
            flagged_percentage=0.0,
            high_value_count=0,
            international_count=0
        )
    
    total_amount = sum(t["amount"] for t in transactions_db)
    flagged_count = sum(1 for t in transactions_db if t.get("is_flagged", False))
    high_value_count = sum(1 for t in transactions_db if t["amount"] > 10000)
    international_count = sum(1 for t in transactions_db if t.get("location_country", "AUS") != "AUS")
    
    return TransactionStatistics(
        total_transactions=len(transactions_db),
        total_amount=total_amount,
        average_amount=total_amount / len(transactions_db),
        flagged_count=flagged_count,
        flagged_percentage=(flagged_count / len(transactions_db)) * 100,
        high_value_count=high_value_count,
        international_count=international_count
    )

@app.post("/api/v1/transactions/test/apra-violation", response_model=TransactionResponse)
async def create_test_apra_violation():
    """Create a test transaction that triggers APRA compliance violations"""
    
    test_transaction_data = {
        "account_id": "TEST_ACCOUNT_001",
        "amount": 25000.00,  # Exceeds transaction limit
        "currency": "AUD",
        "transaction_type": "TRANSFER",
        "description": "Test APRA violation - high amount from high-risk country",
        "counterparty_account": "UNKNOWN_ACCOUNT",
        "counterparty_name": "Suspicious Entity",
        "transaction_channel": "ONLINE",
        "location_country": "IRN",  # High-risk country
        "location_city": "Tehran",
        "ip_address": "192.168.1.100"
    }
    
    transaction = TransactionCreate(**test_transaction_data)
    return await create_transaction(transaction)

@app.get("/api/v1/compliance/violations", response_model=List[ComplianceViolationResponse])
async def get_violations(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get compliance violations with optional filtering"""
    filtered_violations = violations_db
    
    if severity:
        filtered_violations = [v for v in filtered_violations if v.get("severity") == severity]
    
    if status:
        filtered_violations = [v for v in filtered_violations if v.get("status") == status]
    
    return [ComplianceViolationResponse(**v) for v in filtered_violations[-limit:]]

@app.post("/api/v1/compliance/violations/{violation_id}/resolve")
async def resolve_violation(violation_id: str, resolution_data: dict):
    """Resolve a compliance violation"""
    for violation in violations_db:
        if violation["violation_id"] == violation_id:
            violation["status"] = "RESOLVED"
            violation["resolved_at"] = datetime.utcnow()
            violation["resolution_notes"] = resolution_data.get("resolution_notes", "")
            violation["assigned_to"] = resolution_data.get("resolved_by", "")
            return {"message": "Violation resolved successfully", "violation_id": violation_id}
    
    raise HTTPException(status_code=404, detail="Violation not found")

@app.get("/api/v1/compliance/dashboard", response_model=ComplianceDashboard)
async def get_compliance_dashboard():
    """Get compliance dashboard summary"""
    if not violations_db:
        return ComplianceDashboard(
            total_violations=0,
            critical_violations=0,
            high_violations=0,
            medium_violations=0,
            low_violations=0,
            open_violations=0,
            resolved_violations=0,
            overdue_violations=0,
            average_resolution_time_hours=0.0,
            compliance_score=100.0
        )
    
    # Count violations by severity
    critical_count = sum(1 for v in violations_db if v.get("severity") == "CRITICAL")
    high_count = sum(1 for v in violations_db if v.get("severity") == "HIGH")
    medium_count = sum(1 for v in violations_db if v.get("severity") == "MEDIUM")
    low_count = sum(1 for v in violations_db if v.get("severity") == "LOW")
    
    # Count violations by status
    open_count = sum(1 for v in violations_db if v.get("status") in ["OPEN", "INVESTIGATING"])
    resolved_count = sum(1 for v in violations_db if v.get("status") in ["RESOLVED", "CLOSED"])
    
    # Calculate compliance score
    total_risk_score = sum(v.get("risk_score", 0) for v in violations_db)
    max_possible_score = len(violations_db) * 10.0 if violations_db else 1.0
    compliance_score = max(0, 100 - (total_risk_score / max_possible_score * 100))
    
    return ComplianceDashboard(
        total_violations=len(violations_db),
        critical_violations=critical_count,
        high_violations=high_count,
        medium_violations=medium_count,
        low_violations=low_count,
        open_violations=open_count,
        resolved_violations=resolved_count,
        overdue_violations=0,  # Simplified for demo
        average_resolution_time_hours=0.0,  # Simplified for demo
        compliance_score=round(compliance_score, 2)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
