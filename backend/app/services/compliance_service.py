"""
Compliance Service - Core business logic for compliance monitoring
Following SOLID principles:
- Single Responsibility: Compliance rule evaluation and violation detection
- Open/Closed: Extensible rule system
- Liskov Substitution: Interface-based rule implementations
- Interface Segregation: Specific interfaces for different rule types
- Dependency Inversion: Depends on abstractions, not concretions
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionPattern
from app.models.compliance import ComplianceViolation, ComplianceRule
from app.core.exceptions import (
    APRAComplianceViolation, 
    TransactionLimitViolation,
    SuspiciousPatternViolation,
    ViolationSeverity,
    ViolationType
)

logger = structlog.get_logger()


class ComplianceRuleInterface(ABC):
    """
    Interface for compliance rules
    Following Interface Segregation Principle
    """
    
    @abstractmethod
    def evaluate(self, transaction: Transaction, context: Dict[str, Any]) -> Optional[ComplianceViolation]:
        """Evaluate transaction against compliance rule"""
        pass
    
    @abstractmethod
    def get_rule_id(self) -> str:
        """Get unique rule identifier"""
        pass
    
    @abstractmethod
    def get_severity(self) -> ViolationSeverity:
        """Get violation severity level"""
        pass


class APRATransactionLimitRule(ComplianceRuleInterface):
    """
    APRA transaction limit compliance rule
    Following Single Responsibility Principle
    """
    
    def __init__(self, limit_amount: float = 10000.0):
        self.limit_amount = limit_amount
        self.rule_id = "APRA-TXN-LIMIT-001"
        self.apra_standard = "CPS 234"
        self.requirement_id = "CPS234-TXN-001"
    
    def evaluate(self, transaction: Transaction, context: Dict[str, Any]) -> Optional[ComplianceViolation]:
        """Evaluate transaction against APRA limit rules"""
        
        if transaction.amount > self.limit_amount:
            logger.warning(
                "APRA transaction limit exceeded",
                transaction_id=transaction.transaction_id,
                amount=transaction.amount,
                limit=self.limit_amount
            )
            
            # Create violation record
            violation = ComplianceViolation(
                violation_type=ViolationType.TRANSACTION_LIMIT.value,
                severity=self.get_severity().value,
                title=f"Transaction Limit Exceeded - APRA {self.apra_standard}",
                description=f"Transaction amount ${transaction.amount:,.2f} exceeds APRA limit of ${self.limit_amount:,.2f}",
                regulatory_framework="APRA",
                standard_reference=self.apra_standard,
                requirement_id=self.requirement_id,
                risk_score=min(transaction.amount / self.limit_amount, 10.0),
                confidence_score=1.0,
                violation_data={
                    "transaction_amount": transaction.amount,
                    "limit_amount": self.limit_amount,
                    "excess_amount": transaction.amount - self.limit_amount,
                    "violation_percentage": (transaction.amount / self.limit_amount) * 100
                },
                remediation_actions=[
                    "Review transaction authorization",
                    "Verify customer identity",
                    "Check for suspicious activity",
                    "Report to AUSTRAC if required"
                ]
            )
            
            return violation
        
        return None
    
    def get_rule_id(self) -> str:
        return self.rule_id
    
    def get_severity(self) -> ViolationSeverity:
        return ViolationSeverity.HIGH


class APRAVelocityRule(ComplianceRuleInterface):
    """
    APRA transaction velocity monitoring rule
    Following Single Responsibility Principle
    """
    
    def __init__(self, max_transactions_per_hour: int = 10, max_amount_per_hour: float = 50000.0):
        self.max_transactions_per_hour = max_transactions_per_hour
        self.max_amount_per_hour = max_amount_per_hour
        self.rule_id = "APRA-VELOCITY-001"
        self.apra_standard = "CPS 234"
        self.requirement_id = "CPS234-VEL-001"
    
    def evaluate(self, transaction: Transaction, context: Dict[str, Any]) -> Optional[ComplianceViolation]:
        """Evaluate transaction velocity patterns"""
        
        # Get recent transactions for the same account
        recent_transactions = context.get("recent_transactions", [])
        
        # Filter transactions within the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_hour_transactions = [
            t for t in recent_transactions 
            if t.transaction_timestamp >= one_hour_ago and t.account_id == transaction.account_id
        ]
        
        transaction_count = len(recent_hour_transactions) + 1  # Include current transaction
        total_amount = sum(t.amount for t in recent_hour_transactions) + transaction.amount
        
        # Check velocity violations
        if transaction_count > self.max_transactions_per_hour or total_amount > self.max_amount_per_hour:
            severity = ViolationSeverity.CRITICAL if transaction_count > self.max_transactions_per_hour * 2 else ViolationSeverity.HIGH
            
            logger.warning(
                "APRA velocity rule violation",
                account_id=transaction.account_id,
                transaction_count=transaction_count,
                total_amount=total_amount,
                max_transactions=self.max_transactions_per_hour,
                max_amount=self.max_amount_per_hour
            )
            
            violation = ComplianceViolation(
                violation_type=ViolationType.SUSPICIOUS_PATTERN.value,
                severity=severity.value,
                title=f"Transaction Velocity Violation - APRA {self.apra_standard}",
                description=f"Account {transaction.account_id} exceeded velocity limits: {transaction_count} transactions totaling ${total_amount:,.2f} in 1 hour",
                regulatory_framework="APRA",
                standard_reference=self.apra_standard,
                requirement_id=self.requirement_id,
                risk_score=max(
                    transaction_count / self.max_transactions_per_hour,
                    total_amount / self.max_amount_per_hour
                ),
                confidence_score=0.9,
                violation_data={
                    "transaction_count": transaction_count,
                    "max_transactions": self.max_transactions_per_hour,
                    "total_amount": total_amount,
                    "max_amount": self.max_amount_per_hour,
                    "time_window_hours": 1,
                    "account_id": transaction.account_id
                },
                remediation_actions=[
                    "Freeze account temporarily",
                    "Contact customer for verification",
                    "Review transaction patterns",
                    "Escalate to compliance team"
                ]
            )
            
            return violation
        
        return None
    
    def get_rule_id(self) -> str:
        return self.rule_id
    
    def get_severity(self) -> ViolationSeverity:
        return ViolationSeverity.HIGH


class APRAGeographicRule(ComplianceRuleInterface):
    """
    APRA geographic anomaly detection rule
    Following Single Responsibility Principle
    """
    
    def __init__(self, high_risk_countries: List[str] = None):
        self.high_risk_countries = high_risk_countries or [
            "AFG", "IRN", "IRQ", "PRK", "SYR", "YEM"  # Example high-risk countries
        ]
        self.rule_id = "APRA-GEO-001"
        self.apra_standard = "CPS 234"
        self.requirement_id = "CPS234-GEO-001"
    
    def evaluate(self, transaction: Transaction, context: Dict[str, Any]) -> Optional[ComplianceViolation]:
        """Evaluate geographic risk factors"""
        
        # Check for high-risk country transactions
        if transaction.location_country in self.high_risk_countries:
            logger.warning(
                "High-risk country transaction detected",
                transaction_id=transaction.transaction_id,
                country=transaction.location_country,
                amount=transaction.amount
            )
            
            violation = ComplianceViolation(
                violation_type=ViolationType.SUSPICIOUS_PATTERN.value,
                severity=ViolationSeverity.CRITICAL.value,
                title=f"High-Risk Geographic Transaction - APRA {self.apra_standard}",
                description=f"Transaction from high-risk country {transaction.location_country} for amount ${transaction.amount:,.2f}",
                regulatory_framework="APRA",
                standard_reference=self.apra_standard,
                requirement_id=self.requirement_id,
                risk_score=8.0,  # High risk score for sanctioned countries
                confidence_score=1.0,
                violation_data={
                    "country_code": transaction.location_country,
                    "risk_category": "HIGH_RISK_COUNTRY",
                    "transaction_amount": transaction.amount,
                    "requires_enhanced_due_diligence": True
                },
                remediation_actions=[
                    "Enhanced due diligence required",
                    "Verify customer identity",
                    "Check sanctions lists",
                    "Report to AUSTRAC immediately"
                ]
            )
            
            return violation
        
        return None
    
    def get_rule_id(self) -> str:
        return self.rule_id
    
    def get_severity(self) -> ViolationSeverity:
        return ViolationSeverity.CRITICAL


class ComplianceService:
    """
    Main compliance service orchestrating rule evaluation
    Following SOLID principles - Single Responsibility for compliance orchestration
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.rules: List[ComplianceRuleInterface] = []
        self._initialize_rules()
    
    def _initialize_rules(self):
        """
        Initialize compliance rules
        Following Open/Closed Principle - easy to add new rules
        """
        self.rules = [
            APRATransactionLimitRule(limit_amount=10000.0),
            APRAVelocityRule(max_transactions_per_hour=10, max_amount_per_hour=50000.0),
            APRAGeographicRule()
        ]
        
        logger.info("Compliance rules initialized", rule_count=len(self.rules))
    
    def evaluate_transaction(self, transaction: Transaction) -> List[ComplianceViolation]:
        """
        Evaluate transaction against all compliance rules
        Following DRY principle - single evaluation method
        """
        violations = []
        
        # Build context for rule evaluation
        context = self._build_evaluation_context(transaction)
        
        # Evaluate against each rule
        for rule in self.rules:
            try:
                violation = rule.evaluate(transaction, context)
                if violation:
                    violation.transaction_id = transaction.id
                    violations.append(violation)
                    
                    logger.info(
                        "Compliance violation detected",
                        rule_id=rule.get_rule_id(),
                        violation_type=violation.violation_type,
                        severity=violation.severity,
                        transaction_id=transaction.transaction_id
                    )
                    
            except Exception as e:
                logger.error(
                    "Error evaluating compliance rule",
                    rule_id=rule.get_rule_id(),
                    error=str(e),
                    transaction_id=transaction.transaction_id
                )
        
        # Save violations to database
        for violation in violations:
            self.db_session.add(violation)
        
        if violations:
            self.db_session.commit()
            
            # Update transaction compliance status
            transaction.is_flagged = True
            transaction.compliance_status = "UNDER_REVIEW"
            transaction.risk_score = max(v.risk_score for v in violations)
            self.db_session.commit()
        
        return violations
    
    def _build_evaluation_context(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Build context for rule evaluation
        Following DRY principle - centralized context building
        """
        # Get recent transactions for pattern analysis
        recent_transactions = self.db_session.query(Transaction).filter(
            Transaction.account_id == transaction.account_id,
            Transaction.transaction_timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        return {
            "recent_transactions": recent_transactions,
            "account_id": transaction.account_id,
            "evaluation_timestamp": datetime.utcnow()
        }
    
    def get_active_violations(self, severity: Optional[ViolationSeverity] = None) -> List[ComplianceViolation]:
        """Get active compliance violations"""
        query = self.db_session.query(ComplianceViolation).filter(
            ComplianceViolation.status.in_(["OPEN", "INVESTIGATING"])
        )
        
        if severity:
            query = query.filter(ComplianceViolation.severity == severity.value)
        
        return query.order_by(ComplianceViolation.detected_at.desc()).all()
    
    def resolve_violation(self, violation_id: str, resolution_notes: str, resolved_by: str) -> bool:
        """Resolve a compliance violation"""
        violation = self.db_session.query(ComplianceViolation).filter(
            ComplianceViolation.violation_id == violation_id
        ).first()
        
        if violation:
            violation.status = "RESOLVED"
            violation.resolved_at = datetime.utcnow()
            violation.resolution_notes = resolution_notes
            violation.assigned_to = resolved_by
            
            self.db_session.commit()
            
            logger.info(
                "Compliance violation resolved",
                violation_id=violation_id,
                resolved_by=resolved_by
            )
            
            return True
        
        return False
