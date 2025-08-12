"""
Compliance API endpoints
Following SOLID principles and RESTful design
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import structlog

from app.core.database import get_db
from app.services.compliance_service import ComplianceService
from app.models.compliance import ComplianceViolation, ComplianceRule
from app.core.exceptions import ViolationSeverity, ViolationType

logger = structlog.get_logger()

router = APIRouter()


# Pydantic models for request/response
class ComplianceViolationResponse(BaseModel):
    """Compliance violation response model"""
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
    impact_assessment: str
    status: str
    assigned_to: Optional[str]
    resolution_notes: Optional[str]
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    violation_data: Optional[dict]
    remediation_actions: Optional[list]
    
    class Config:
        from_attributes = True


class ViolationResolution(BaseModel):
    """Violation resolution request model"""
    resolution_notes: str = Field(..., description="Notes explaining the resolution")
    resolved_by: str = Field(..., description="User who resolved the violation")
    
    class Config:
        schema_extra = {
            "example": {
                "resolution_notes": "Customer verified transaction via phone call. Enhanced due diligence completed.",
                "resolved_by": "compliance.officer@bank.com"
            }
        }


class ComplianceRuleResponse(BaseModel):
    """Compliance rule response model"""
    rule_id: str
    name: str
    description: str
    category: str
    regulatory_framework: str
    standard_reference: Optional[str]
    requirement_id: Optional[str]
    is_active: bool
    version: str
    effective_date: datetime
    rule_logic: Optional[dict]
    threshold_values: Optional[dict]
    
    class Config:
        from_attributes = True


class ComplianceDashboard(BaseModel):
    """Compliance dashboard summary model"""
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


@router.get("/violations", response_model=List[ComplianceViolationResponse])
async def get_violations(
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    status: Optional[str] = Query(None, description="Filter by status: OPEN, INVESTIGATING, RESOLVED, CLOSED"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of violations to return"),
    offset: int = Query(0, ge=0, description="Number of violations to skip"),
    db: Session = Depends(get_db)
):
    """
    Get compliance violations with optional filtering
    
    Returns a list of compliance violations that can be filtered by severity
    and status. Results are ordered by detection date (most recent first).
    """
    query = db.query(ComplianceViolation)
    
    # Apply filters
    if severity:
        if severity not in [s.value for s in ViolationSeverity]:
            raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {[s.value for s in ViolationSeverity]}")
        query = query.filter(ComplianceViolation.severity == severity)
    
    if status:
        valid_statuses = ["OPEN", "INVESTIGATING", "RESOLVED", "CLOSED"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        query = query.filter(ComplianceViolation.status == status)
    
    violations = query.order_by(ComplianceViolation.detected_at.desc()).offset(offset).limit(limit).all()
    
    return [ComplianceViolationResponse.from_orm(v) for v in violations]


@router.get("/violations/{violation_id}", response_model=ComplianceViolationResponse)
async def get_violation(
    violation_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific compliance violation by ID"""
    violation = db.query(ComplianceViolation).filter(
        ComplianceViolation.violation_id == violation_id
    ).first()
    
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    return ComplianceViolationResponse.from_orm(violation)


@router.post("/violations/{violation_id}/resolve")
async def resolve_violation(
    violation_id: str,
    resolution: ViolationResolution,
    db: Session = Depends(get_db)
):
    """
    Resolve a compliance violation
    
    Marks a violation as resolved with resolution notes and the user who
    resolved it. This action is logged in the audit trail.
    """
    service = ComplianceService(db)
    
    success = service.resolve_violation(
        violation_id=violation_id,
        resolution_notes=resolution.resolution_notes,
        resolved_by=resolution.resolved_by
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    logger.info(
        "Violation resolved via API",
        violation_id=violation_id,
        resolved_by=resolution.resolved_by
    )
    
    return {"message": "Violation resolved successfully", "violation_id": violation_id}


@router.get("/violations/active/summary")
async def get_active_violations_summary(
    db: Session = Depends(get_db)
):
    """
    Get summary of active compliance violations
    
    Returns counts of violations by severity level for violations that
    are currently open or under investigation.
    """
    service = ComplianceService(db)
    
    # Get active violations by severity
    critical_violations = service.get_active_violations(ViolationSeverity.CRITICAL)
    high_violations = service.get_active_violations(ViolationSeverity.HIGH)
    medium_violations = service.get_active_violations(ViolationSeverity.MEDIUM)
    low_violations = service.get_active_violations(ViolationSeverity.LOW)
    
    return {
        "critical_count": len(critical_violations),
        "high_count": len(high_violations),
        "medium_count": len(medium_violations),
        "low_count": len(low_violations),
        "total_active": len(critical_violations) + len(high_violations) + len(medium_violations) + len(low_violations),
        "critical_violations": [
            {
                "violation_id": v.violation_id,
                "title": v.title,
                "detected_at": v.detected_at,
                "is_overdue": v.is_overdue
            }
            for v in critical_violations[:5]  # Show top 5 critical
        ]
    }


@router.get("/rules", response_model=List[ComplianceRuleResponse])
async def get_compliance_rules(
    active_only: bool = Query(True, description="Return only active rules"),
    category: Optional[str] = Query(None, description="Filter by rule category"),
    db: Session = Depends(get_db)
):
    """Get compliance rules with optional filtering"""
    query = db.query(ComplianceRule)
    
    if active_only:
        query = query.filter(ComplianceRule.is_active == True)
    
    if category:
        query = query.filter(ComplianceRule.category == category)
    
    rules = query.order_by(ComplianceRule.name).all()
    
    return [ComplianceRuleResponse.from_orm(r) for r in rules]


@router.get("/dashboard", response_model=ComplianceDashboard)
async def get_compliance_dashboard(
    db: Session = Depends(get_db)
):
    """
    Get compliance dashboard summary
    
    Returns key metrics and statistics for the compliance dashboard including
    violation counts by severity, resolution statistics, and overall compliance score.
    """
    # Get all violations
    all_violations = db.query(ComplianceViolation).all()
    
    if not all_violations:
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
    critical_count = sum(1 for v in all_violations if v.severity == "CRITICAL")
    high_count = sum(1 for v in all_violations if v.severity == "HIGH")
    medium_count = sum(1 for v in all_violations if v.severity == "MEDIUM")
    low_count = sum(1 for v in all_violations if v.severity == "LOW")
    
    # Count violations by status
    open_count = sum(1 for v in all_violations if v.status in ["OPEN", "INVESTIGATING"])
    resolved_count = sum(1 for v in all_violations if v.status in ["RESOLVED", "CLOSED"])
    
    # Count overdue violations
    overdue_count = sum(1 for v in all_violations if v.is_overdue)
    
    # Calculate average resolution time
    resolved_violations = [v for v in all_violations if v.resolved_at and v.detected_at]
    if resolved_violations:
        total_resolution_time = sum(
            (v.resolved_at - v.detected_at).total_seconds() / 3600
            for v in resolved_violations
        )
        average_resolution_time = total_resolution_time / len(resolved_violations)
    else:
        average_resolution_time = 0.0
    
    # Calculate compliance score (simple scoring based on violation severity and resolution)
    total_risk_score = sum(v.risk_score for v in all_violations)
    max_possible_score = len(all_violations) * 10.0  # Assuming max risk score is 10
    
    if max_possible_score > 0:
        compliance_score = max(0, 100 - (total_risk_score / max_possible_score * 100))
    else:
        compliance_score = 100.0
    
    # Adjust score based on overdue violations
    if overdue_count > 0:
        compliance_score = max(0, compliance_score - (overdue_count * 5))  # Penalty for overdue
    
    return ComplianceDashboard(
        total_violations=len(all_violations),
        critical_violations=critical_count,
        high_violations=high_count,
        medium_violations=medium_count,
        low_violations=low_count,
        open_violations=open_count,
        resolved_violations=resolved_count,
        overdue_violations=overdue_count,
        average_resolution_time_hours=round(average_resolution_time, 2),
        compliance_score=round(compliance_score, 2)
    )


@router.get("/apra/standards")
async def get_apra_standards():
    """
    Get APRA compliance standards information
    
    Returns information about APRA prudential standards that are
    monitored by the compliance system.
    """
    return {
        "standards": [
            {
                "code": "CPS 220",
                "name": "Risk Management",
                "description": "Requirements for risk management framework, risk appetite, and risk culture",
                "key_requirements": [
                    "Board-approved risk management framework",
                    "Risk appetite statement with measurable limits",
                    "Three lines of defense model",
                    "Risk culture assessment"
                ]
            },
            {
                "code": "CPS 234", 
                "name": "Information Security",
                "description": "Requirements for information security capability and incident response",
                "key_requirements": [
                    "Board oversight of information security",
                    "Information security capability",
                    "Third party arrangements",
                    "Incident response plan"
                ]
            },
            {
                "code": "CPS 232",
                "name": "Business Continuity Management", 
                "description": "Requirements for business continuity planning and operational resilience",
                "key_requirements": [
                    "Business continuity plan",
                    "Testing and maintenance",
                    "Crisis management",
                    "Recovery time objectives"
                ]
            }
        ],
        "monitoring_capabilities": [
            "Real-time transaction monitoring",
            "Automated violation detection",
            "Risk scoring and assessment",
            "Regulatory reporting",
            "Audit trail maintenance"
        ]
    }
