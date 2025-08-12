"""
Unit tests for ComplianceService
Following SOLID principles and comprehensive test coverage
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.compliance_service import (
    ComplianceService,
    APRATransactionLimitRule,
    APRAVelocityRule,
    APRAGeographicRule
)
from app.models.transaction import Transaction
from app.models.compliance import ComplianceViolation
from app.core.exceptions import ViolationSeverity, ViolationType


class TestAPRATransactionLimitRule:
    """Test APRA transaction limit rule"""
    
    def test_transaction_within_limit(self):
        """Test transaction within APRA limit passes"""
        rule = APRATransactionLimitRule(limit_amount=10000.0)
        
        transaction = Transaction(
            account_id="TEST001",
            amount=5000.0,
            transaction_type="DEBIT"
        )
        
        violation = rule.evaluate(transaction, {})
        assert violation is None
    
    def test_transaction_exceeds_limit(self):
        """Test transaction exceeding APRA limit creates violation"""
        rule = APRATransactionLimitRule(limit_amount=10000.0)
        
        transaction = Transaction(
            account_id="TEST001",
            amount=15000.0,
            transaction_type="DEBIT",
            transaction_id="TXN001"
        )
        
        violation = rule.evaluate(transaction, {})
        
        assert violation is not None
        assert violation.violation_type == ViolationType.TRANSACTION_LIMIT.value
        assert violation.severity == ViolationSeverity.HIGH.value
        assert violation.regulatory_framework == "APRA"
        assert violation.standard_reference == "CPS 234"
        assert violation.risk_score == 1.5  # 15000/10000
        assert violation.confidence_score == 1.0
        
        # Check violation data
        assert violation.violation_data["transaction_amount"] == 15000.0
        assert violation.violation_data["limit_amount"] == 10000.0
        assert violation.violation_data["excess_amount"] == 5000.0
        assert violation.violation_data["violation_percentage"] == 150.0
    
    def test_transaction_at_exact_limit(self):
        """Test transaction at exact limit passes"""
        rule = APRATransactionLimitRule(limit_amount=10000.0)
        
        transaction = Transaction(
            account_id="TEST001",
            amount=10000.0,
            transaction_type="DEBIT"
        )
        
        violation = rule.evaluate(transaction, {})
        assert violation is None
    
    def test_rule_properties(self):
        """Test rule properties"""
        rule = APRATransactionLimitRule(limit_amount=5000.0)
        
        assert rule.get_rule_id() == "APRA-TXN-LIMIT-001"
        assert rule.get_severity() == ViolationSeverity.HIGH


class TestAPRAVelocityRule:
    """Test APRA velocity rule"""
    
    def test_velocity_within_limits(self):
        """Test velocity within limits passes"""
        rule = APRAVelocityRule(max_transactions_per_hour=10, max_amount_per_hour=50000.0)
        
        transaction = Transaction(
            account_id="TEST001",
            amount=1000.0,
            transaction_type="DEBIT"
        )
        
        # Create context with few recent transactions
        recent_transactions = [
            Transaction(
                account_id="TEST001",
                amount=1000.0,
                transaction_timestamp=datetime.utcnow() - timedelta(minutes=30)
            )
        ]
        
        context = {"recent_transactions": recent_transactions}
        violation = rule.evaluate(transaction, context)
        
        assert violation is None
    
    def test_velocity_exceeds_transaction_count(self):
        """Test velocity exceeding transaction count limit"""
        rule = APRAVelocityRule(max_transactions_per_hour=5, max_amount_per_hour=50000.0)
        
        transaction = Transaction(
            account_id="TEST001",
            amount=1000.0,
            transaction_type="DEBIT",
            transaction_id="TXN001"
        )
        
        # Create context with many recent transactions
        recent_transactions = []
        base_time = datetime.utcnow() - timedelta(minutes=30)
        
        for i in range(6):  # 6 transactions + current = 7 > limit of 5
            recent_transactions.append(Transaction(
                account_id="TEST001",
                amount=1000.0,
                transaction_timestamp=base_time + timedelta(minutes=i*5)
            ))
        
        context = {"recent_transactions": recent_transactions}
        violation = rule.evaluate(transaction, context)
        
        assert violation is not None
        assert violation.violation_type == ViolationType.SUSPICIOUS_PATTERN.value
        assert violation.severity == ViolationSeverity.HIGH.value
        assert "velocity" in violation.title.lower()
        
        # Check violation data
        assert violation.violation_data["transaction_count"] == 7  # 6 + 1
        assert violation.violation_data["max_transactions"] == 5
    
    def test_velocity_exceeds_amount_limit(self):
        """Test velocity exceeding amount limit"""
        rule = APRAVelocityRule(max_transactions_per_hour=10, max_amount_per_hour=20000.0)
        
        transaction = Transaction(
            account_id="TEST001",
            amount=15000.0,
            transaction_type="DEBIT",
            transaction_id="TXN001"
        )
        
        # Create context with high-value recent transactions
        recent_transactions = [
            Transaction(
                account_id="TEST001",
                amount=10000.0,
                transaction_timestamp=datetime.utcnow() - timedelta(minutes=30)
            )
        ]
        
        context = {"recent_transactions": recent_transactions}
        violation = rule.evaluate(transaction, context)
        
        assert violation is not None
        assert violation.violation_data["total_amount"] == 25000.0  # 10000 + 15000
        assert violation.violation_data["max_amount"] == 20000.0
    
    def test_velocity_critical_severity(self):
        """Test velocity rule assigns critical severity for extreme violations"""
        rule = APRAVelocityRule(max_transactions_per_hour=5, max_amount_per_hour=50000.0)
        
        transaction = Transaction(
            account_id="TEST001",
            amount=1000.0,
            transaction_type="DEBIT",
            transaction_id="TXN001"
        )
        
        # Create context with double the transaction limit
        recent_transactions = []
        base_time = datetime.utcnow() - timedelta(minutes=30)
        
        for i in range(11):  # 11 transactions + current = 12 > 2 * limit of 5
            recent_transactions.append(Transaction(
                account_id="TEST001",
                amount=1000.0,
                transaction_timestamp=base_time + timedelta(minutes=i*3)
            ))
        
        context = {"recent_transactions": recent_transactions}
        violation = rule.evaluate(transaction, context)
        
        assert violation is not None
        assert violation.severity == ViolationSeverity.CRITICAL.value
    
    def test_velocity_different_account_ignored(self):
        """Test velocity rule ignores transactions from different accounts"""
        rule = APRAVelocityRule(max_transactions_per_hour=5, max_amount_per_hour=50000.0)
        
        transaction = Transaction(
            account_id="TEST001",
            amount=1000.0,
            transaction_type="DEBIT"
        )
        
        # Create context with many transactions from different account
        recent_transactions = []
        base_time = datetime.utcnow() - timedelta(minutes=30)
        
        for i in range(10):
            recent_transactions.append(Transaction(
                account_id="DIFFERENT_ACCOUNT",  # Different account
                amount=1000.0,
                transaction_timestamp=base_time + timedelta(minutes=i*3)
            ))
        
        context = {"recent_transactions": recent_transactions}
        violation = rule.evaluate(transaction, context)
        
        assert violation is None  # Should not trigger because different account


class TestAPRAGeographicRule:
    """Test APRA geographic rule"""
    
    def test_transaction_from_safe_country(self):
        """Test transaction from safe country passes"""
        rule = APRAGeographicRule(high_risk_countries=["IRN", "PRK"])
        
        transaction = Transaction(
            account_id="TEST001",
            amount=5000.0,
            location_country="AUS",
            transaction_type="DEBIT"
        )
        
        violation = rule.evaluate(transaction, {})
        assert violation is None
    
    def test_transaction_from_high_risk_country(self):
        """Test transaction from high-risk country creates violation"""
        rule = APRAGeographicRule(high_risk_countries=["IRN", "PRK", "SYR"])
        
        transaction = Transaction(
            account_id="TEST001",
            amount=5000.0,
            location_country="IRN",
            transaction_type="TRANSFER",
            transaction_id="TXN001"
        )
        
        violation = rule.evaluate(transaction, {})
        
        assert violation is not None
        assert violation.violation_type == ViolationType.SUSPICIOUS_PATTERN.value
        assert violation.severity == ViolationSeverity.CRITICAL.value
        assert violation.risk_score == 8.0
        assert violation.confidence_score == 1.0
        
        # Check violation data
        assert violation.violation_data["country_code"] == "IRN"
        assert violation.violation_data["risk_category"] == "HIGH_RISK_COUNTRY"
        assert violation.violation_data["requires_enhanced_due_diligence"] is True
        
        # Check remediation actions
        actions_text = " ".join(violation.remediation_actions).lower()
        assert "enhanced due diligence" in actions_text
        assert "austrac" in actions_text
    
    def test_default_high_risk_countries(self):
        """Test default high-risk countries list"""
        rule = APRAGeographicRule()
        
        # Test with default high-risk country
        transaction = Transaction(
            account_id="TEST001",
            amount=5000.0,
            location_country="AFG",  # Afghanistan in default list
            transaction_type="TRANSFER",
            transaction_id="TXN001"
        )
        
        violation = rule.evaluate(transaction, {})
        assert violation is not None
        assert violation.severity == ViolationSeverity.CRITICAL.value


class TestComplianceService:
    """Test ComplianceService orchestration"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def compliance_service(self, mock_db_session):
        """ComplianceService fixture"""
        return ComplianceService(mock_db_session)
    
    def test_service_initialization(self, compliance_service):
        """Test service initializes with rules"""
        assert len(compliance_service.rules) == 3  # 3 APRA rules
        
        rule_ids = [rule.get_rule_id() for rule in compliance_service.rules]
        assert "APRA-TXN-LIMIT-001" in rule_ids
        assert "APRA-VELOCITY-001" in rule_ids
        assert "APRA-GEO-001" in rule_ids
    
    def test_evaluate_transaction_no_violations(self, compliance_service, mock_db_session):
        """Test transaction evaluation with no violations"""
        transaction = Transaction(
            id=1,
            account_id="TEST001",
            amount=5000.0,
            location_country="AUS",
            transaction_type="DEBIT",
            transaction_id="TXN001"
        )
        
        # Mock recent transactions query
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        violations = compliance_service.evaluate_transaction(transaction)
        
        assert len(violations) == 0
        assert not transaction.is_flagged
        assert transaction.compliance_status == "PENDING"
    
    def test_evaluate_transaction_with_violations(self, compliance_service, mock_db_session):
        """Test transaction evaluation with violations"""
        transaction = Transaction(
            id=1,
            account_id="TEST001",
            amount=15000.0,  # Exceeds limit
            location_country="IRN",  # High-risk country
            transaction_type="DEBIT",
            transaction_id="TXN001"
        )
        
        # Mock recent transactions query
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        violations = compliance_service.evaluate_transaction(transaction)
        
        assert len(violations) >= 2  # Should have limit and geographic violations
        assert transaction.is_flagged
        assert transaction.compliance_status == "UNDER_REVIEW"
        assert transaction.risk_score > 0
        
        # Verify violations were added to session
        assert mock_db_session.add.call_count == len(violations)
        assert mock_db_session.commit.call_count >= 1
    
    def test_evaluate_transaction_rule_error_handling(self, compliance_service, mock_db_session):
        """Test error handling when rule evaluation fails"""
        transaction = Transaction(
            id=1,
            account_id="TEST001",
            amount=5000.0,
            transaction_type="DEBIT",
            transaction_id="TXN001"
        )
        
        # Mock recent transactions query
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        # Mock a rule to raise an exception
        with patch.object(compliance_service.rules[0], 'evaluate', side_effect=Exception("Rule error")):
            violations = compliance_service.evaluate_transaction(transaction)
            
            # Should continue with other rules despite one failing
            assert isinstance(violations, list)
    
    def test_build_evaluation_context(self, compliance_service, mock_db_session):
        """Test evaluation context building"""
        transaction = Transaction(
            account_id="TEST001",
            amount=5000.0,
            transaction_type="DEBIT"
        )
        
        # Mock recent transactions
        mock_recent_transactions = [
            Transaction(account_id="TEST001", amount=1000.0),
            Transaction(account_id="TEST001", amount=2000.0)
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_recent_transactions
        
        context = compliance_service._build_evaluation_context(transaction)
        
        assert "recent_transactions" in context
        assert "account_id" in context
        assert "evaluation_timestamp" in context
        assert context["account_id"] == "TEST001"
        assert len(context["recent_transactions"]) == 2
    
    def test_get_active_violations(self, compliance_service, mock_db_session):
        """Test getting active violations"""
        mock_violations = [
            ComplianceViolation(violation_id="V1", status="OPEN", severity="HIGH"),
            ComplianceViolation(violation_id="V2", status="INVESTIGATING", severity="CRITICAL")
        ]
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_violations
        
        violations = compliance_service.get_active_violations()
        
        assert len(violations) == 2
        mock_db_session.query.assert_called_with(ComplianceViolation)
    
    def test_get_active_violations_by_severity(self, compliance_service, mock_db_session):
        """Test getting active violations filtered by severity"""
        mock_violations = [
            ComplianceViolation(violation_id="V1", status="OPEN", severity="CRITICAL")
        ]
        
        mock_db_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = mock_violations
        
        violations = compliance_service.get_active_violations(ViolationSeverity.CRITICAL)
        
        assert len(violations) == 1
        assert violations[0].severity == "CRITICAL"
    
    def test_resolve_violation_success(self, compliance_service, mock_db_session):
        """Test successful violation resolution"""
        mock_violation = ComplianceViolation(
            violation_id="V1",
            status="OPEN"
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_violation
        
        result = compliance_service.resolve_violation("V1", "Resolved by investigation", "officer@bank.com")
        
        assert result is True
        assert mock_violation.status == "RESOLVED"
        assert mock_violation.resolution_notes == "Resolved by investigation"
        assert mock_violation.assigned_to == "officer@bank.com"
        assert mock_violation.resolved_at is not None
        mock_db_session.commit.assert_called_once()
    
    def test_resolve_violation_not_found(self, compliance_service, mock_db_session):
        """Test violation resolution when violation not found"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = compliance_service.resolve_violation("NONEXISTENT", "Notes", "officer@bank.com")
        
        assert result is False
        mock_db_session.commit.assert_not_called()


class TestComplianceServiceIntegration:
    """Integration tests for ComplianceService with multiple rules"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    def test_multiple_violations_single_transaction(self, mock_db_session):
        """Test transaction triggering multiple violations"""
        service = ComplianceService(mock_db_session)
        
        # Transaction that should trigger multiple violations
        transaction = Transaction(
            id=1,
            account_id="TEST001",
            amount=25000.0,  # Exceeds limit
            location_country="IRN",  # High-risk country
            transaction_type="TRANSFER",
            transaction_id="TXN001"
        )
        
        # Mock recent transactions for velocity check
        recent_transactions = []
        base_time = datetime.utcnow() - timedelta(minutes=30)
        
        for i in range(12):  # High velocity
            recent_transactions.append(Transaction(
                account_id="TEST001",
                amount=1000.0,
                transaction_timestamp=base_time + timedelta(minutes=i*3)
            ))
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = recent_transactions
        
        violations = service.evaluate_transaction(transaction)
        
        # Should have violations from all three rules
        assert len(violations) == 3
        
        violation_types = [v.violation_type for v in violations]
        assert ViolationType.TRANSACTION_LIMIT.value in violation_types
        assert ViolationType.SUSPICIOUS_PATTERN.value in violation_types
        
        # Check that transaction is properly flagged
        assert transaction.is_flagged
        assert transaction.compliance_status == "UNDER_REVIEW"
        assert transaction.risk_score > 0
    
    def test_risk_score_calculation(self, mock_db_session):
        """Test risk score calculation with multiple violations"""
        service = ComplianceService(mock_db_session)
        
        transaction = Transaction(
            id=1,
            account_id="TEST001",
            amount=20000.0,  # 2x the limit
            location_country="IRN",  # High-risk country
            transaction_type="TRANSFER",
            transaction_id="TXN001"
        )
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        violations = service.evaluate_transaction(transaction)
        
        # Risk score should be the maximum of all violation risk scores
        max_violation_risk = max(v.risk_score for v in violations)
        assert transaction.risk_score == max_violation_risk
        assert transaction.risk_score >= 2.0  # At least 2x limit violation
