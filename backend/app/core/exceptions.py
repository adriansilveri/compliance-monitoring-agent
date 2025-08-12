"""
Custom exceptions for compliance monitoring
Following SOLID principles - Single Responsibility for error handling
"""

from typing import Dict, Any, Optional
from enum import Enum


class ViolationSeverity(str, Enum):
    """Compliance violation severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ViolationType(str, Enum):
    """Types of compliance violations"""
    TRANSACTION_LIMIT = "TRANSACTION_LIMIT"
    SUSPICIOUS_PATTERN = "SUSPICIOUS_PATTERN"
    REGULATORY_BREACH = "REGULATORY_BREACH"
    DATA_QUALITY = "DATA_QUALITY"
    AUTHORIZATION = "AUTHORIZATION"
    REPORTING = "REPORTING"
    RISK_THRESHOLD = "RISK_THRESHOLD"


class ComplianceException(Exception):
    """
    Base exception for compliance violations
    Following KISS principle - simple, clear error structure
    """
    
    def __init__(
        self,
        message: str,
        violation_type: ViolationType,
        severity: ViolationSeverity = ViolationSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ):
        self.message = message
        self.violation_type = violation_type
        self.severity = severity
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class APRAComplianceViolation(ComplianceException):
    """Specific APRA compliance violations"""
    
    def __init__(
        self,
        message: str,
        apra_standard: str,
        requirement_id: str,
        severity: ViolationSeverity = ViolationSeverity.HIGH,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "apra_standard": apra_standard,
            "requirement_id": requirement_id,
            "regulatory_framework": "APRA"
        })
        
        super().__init__(
            message=message,
            violation_type=ViolationType.REGULATORY_BREACH,
            severity=severity,
            details=details,
            status_code=422
        )


class TransactionLimitViolation(ComplianceException):
    """Transaction limit exceeded violations"""
    
    def __init__(
        self,
        message: str,
        transaction_amount: float,
        limit_amount: float,
        account_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "transaction_amount": transaction_amount,
            "limit_amount": limit_amount,
            "account_id": account_id,
            "violation_percentage": (transaction_amount / limit_amount) * 100
        })
        
        super().__init__(
            message=message,
            violation_type=ViolationType.TRANSACTION_LIMIT,
            severity=ViolationSeverity.HIGH,
            details=details,
            status_code=422
        )


class SuspiciousPatternViolation(ComplianceException):
    """Suspicious transaction pattern violations"""
    
    def __init__(
        self,
        message: str,
        pattern_type: str,
        confidence_score: float,
        account_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "pattern_type": pattern_type,
            "confidence_score": confidence_score,
            "account_id": account_id,
            "requires_investigation": confidence_score > 0.8
        })
        
        severity = ViolationSeverity.CRITICAL if confidence_score > 0.9 else ViolationSeverity.HIGH
        
        super().__init__(
            message=message,
            violation_type=ViolationType.SUSPICIOUS_PATTERN,
            severity=severity,
            details=details,
            status_code=422
        )


class DataQualityViolation(ComplianceException):
    """Data quality and integrity violations"""
    
    def __init__(
        self,
        message: str,
        field_name: str,
        expected_format: str,
        actual_value: Any,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "field_name": field_name,
            "expected_format": expected_format,
            "actual_value": str(actual_value),
            "data_quality_issue": True
        })
        
        super().__init__(
            message=message,
            violation_type=ViolationType.DATA_QUALITY,
            severity=ViolationSeverity.MEDIUM,
            details=details,
            status_code=400
        )
