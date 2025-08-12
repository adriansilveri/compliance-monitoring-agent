"""
Compliance violation models
Following SOLID principles - Single Responsibility for compliance data
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database import Base


class ComplianceViolation(Base):
    """
    Model for tracking compliance violations
    Following SOLID and DRY principles
    """
    __tablename__ = "compliance_violations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Violation details
    violation_type = Column(String(50), nullable=False)  # From ViolationType enum
    severity = Column(String(20), nullable=False)  # From ViolationSeverity enum
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Regulatory information
    regulatory_framework = Column(String(50), default="APRA")
    standard_reference = Column(String(100))  # e.g., "CPS 220", "CPS 234"
    requirement_id = Column(String(50))
    
    # Associated transaction
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    transaction = relationship("Transaction", back_populates="violations")
    
    # Violation metrics
    risk_score = Column(Float, nullable=False)
    confidence_score = Column(Float, default=1.0)
    impact_assessment = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Status tracking
    status = Column(String(20), default="OPEN")  # OPEN, INVESTIGATING, RESOLVED, CLOSED
    assigned_to = Column(String(100))
    resolution_notes = Column(Text)
    
    # Timestamps
    detected_at = Column(DateTime, default=func.now())
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Additional data
    violation_data = Column(JSON)  # Store additional violation-specific data
    remediation_actions = Column(JSON)  # Store recommended actions
    
    def __repr__(self):
        return f"<ComplianceViolation(id={self.violation_id}, type={self.violation_type}, severity={self.severity})>"
    
    @property
    def is_critical(self) -> bool:
        """Check if violation is critical severity"""
        return self.severity == "CRITICAL"
    
    @property
    def is_overdue(self) -> bool:
        """Check if violation resolution is overdue"""
        if self.status in ["RESOLVED", "CLOSED"]:
            return False
        
        # Critical violations should be resolved within 24 hours
        if self.is_critical:
            hours_since_detection = (datetime.utcnow() - self.detected_at).total_seconds() / 3600
            return hours_since_detection > 24
        
        # High severity within 72 hours
        if self.severity == "HIGH":
            hours_since_detection = (datetime.utcnow() - self.detected_at).total_seconds() / 3600
            return hours_since_detection > 72
        
        return False


class ComplianceRule(Base):
    """
    Model for storing compliance rules
    Following Open/Closed Principle - extensible rule system
    """
    __tablename__ = "compliance_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Rule identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # TRANSACTION, PATTERN, REPORTING, etc.
    
    # Regulatory mapping
    regulatory_framework = Column(String(50), default="APRA")
    standard_reference = Column(String(100))
    requirement_id = Column(String(50))
    
    # Rule configuration
    rule_logic = Column(JSON, nullable=False)  # Store rule conditions and logic
    threshold_values = Column(JSON)  # Store threshold configurations
    severity_mapping = Column(JSON)  # Map conditions to severity levels
    
    # Rule status
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    effective_date = Column(DateTime, default=func.now())
    expiry_date = Column(DateTime)
    
    # Metadata
    created_by = Column(String(100))
    approved_by = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ComplianceRule(id={self.rule_id}, name={self.name}, active={self.is_active})>"


class AuditLog(Base):
    """
    Model for audit trail
    Following SOLID principles - Single Responsibility for audit logging
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Event details
    event_type = Column(String(50), nullable=False)  # TRANSACTION, VIOLATION, RULE_UPDATE, etc.
    event_description = Column(Text, nullable=False)
    entity_type = Column(String(50))  # TRANSACTION, VIOLATION, RULE, USER
    entity_id = Column(String(50))
    
    # User and system information
    user_id = Column(String(100))
    user_role = Column(String(50))
    system_component = Column(String(100))
    ip_address = Column(String(45))
    
    # Event data
    before_state = Column(JSON)  # State before change
    after_state = Column(JSON)   # State after change
    metadata = Column(JSON)      # Additional event metadata
    
    # Timestamp
    timestamp = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<AuditLog(id={self.log_id}, type={self.event_type}, timestamp={self.timestamp})>"
