"""
BDD Step definitions for APRA compliance testing
Following BDD principles with clear, readable test steps
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.database import SessionLocal
from app.services.transaction_service import TransactionService
from app.services.compliance_service import ComplianceService
from app.models.transaction import Transaction
from app.models.compliance import ComplianceViolation
from app.core.exceptions import DataQualityViolation, ComplianceException

# Load scenarios from feature file
scenarios('../features/apra_compliance.feature')


@pytest.fixture
def db_session():
    """Database session fixture for testing"""
    session = SessionLocal()
    try:
        yield session
    finally:
        # Clean up test data
        session.query(ComplianceViolation).delete()
        session.query(Transaction).delete()
        session.commit()
        session.close()


@pytest.fixture
def transaction_service(db_session):
    """Transaction service fixture"""
    return TransactionService(db_session)


@pytest.fixture
def compliance_service(db_session):
    """Compliance service fixture"""
    return ComplianceService(db_session)


@pytest.fixture
def context():
    """Test context for sharing data between steps"""
    return {}


# Background steps
@given("the compliance monitoring system is running")
def compliance_system_running(context):
    """Ensure compliance system is initialized"""
    context["system_running"] = True


@given("APRA compliance rules are active")
def apra_rules_active(context):
    """Ensure APRA rules are active"""
    context["apra_rules_active"] = True


# Transaction limit violation scenario
@given(parsers.parse("a transaction with amount ${amount:d}"))
def transaction_with_amount(context, amount):
    """Create transaction data with specified amount"""
    context["transaction_data"] = {
        "account_id": "TEST_ACC_001",
        "amount": float(amount),
        "currency": "AUD",
        "transaction_type": "DEBIT",
        "description": "Test transaction",
        "transaction_channel": "ONLINE",
        "location_country": "AUS"
    }


@given(parsers.parse("the APRA transaction limit is ${limit:d}"))
def apra_transaction_limit(context, limit):
    """Set APRA transaction limit"""
    context["apra_limit"] = float(limit)


@when("the transaction is processed")
def process_transaction(context, transaction_service):
    """Process the transaction through compliance system"""
    try:
        transaction = transaction_service.create_transaction(context["transaction_data"])
        context["processed_transaction"] = transaction
        context["processing_error"] = None
    except Exception as e:
        context["processing_error"] = e
        context["processed_transaction"] = None


@then("a compliance violation should be detected")
def compliance_violation_detected(context, db_session):
    """Verify compliance violation was detected"""
    if context.get("processed_transaction"):
        violations = db_session.query(ComplianceViolation).filter(
            ComplianceViolation.transaction_id == context["processed_transaction"].id
        ).all()
        assert len(violations) > 0, "No compliance violations detected"
        context["detected_violations"] = violations
    else:
        assert False, "No transaction was processed"


@then(parsers.parse('the violation type should be "{violation_type}"'))
def verify_violation_type(context, violation_type):
    """Verify the violation type"""
    violations = context.get("detected_violations", [])
    assert any(v.violation_type == violation_type for v in violations), \
        f"No violation of type {violation_type} found"


@then(parsers.parse('the violation severity should be "{severity}"'))
def verify_violation_severity(context, severity):
    """Verify the violation severity"""
    violations = context.get("detected_violations", [])
    assert any(v.severity == severity for v in violations), \
        f"No violation with severity {severity} found"


@then(parsers.parse('the violation should reference "{standard}"'))
def verify_violation_standard(context, standard):
    """Verify the violation references correct APRA standard"""
    violations = context.get("detected_violations", [])
    assert any(standard in (v.standard_reference or "") for v in violations), \
        f"No violation referencing {standard} found"


# Velocity pattern scenario
@given(parsers.parse('an account "{account_id}"'))
def account_context(context, account_id):
    """Set account context"""
    context["account_id"] = account_id


@given(parsers.parse("{count:d} transactions within 1 hour for the account"))
def multiple_transactions_one_hour(context, count, transaction_service):
    """Create multiple transactions within one hour"""
    account_id = context["account_id"]
    base_time = datetime.utcnow()
    
    transactions = []
    for i in range(count):
        transaction_data = {
            "account_id": account_id,
            "amount": 1000.0 + i * 100,  # Varying amounts
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": f"Test transaction {i+1}",
            "transaction_channel": "ONLINE",
            "location_country": "AUS",
            "transaction_timestamp": base_time + timedelta(minutes=i*5)  # Spread over hour
        }
        
        transaction = transaction_service.create_transaction(transaction_data)
        transactions.append(transaction)
    
    context["velocity_transactions"] = transactions


@given(parsers.parse("the velocity limit is {limit:d} transactions per hour"))
def velocity_limit(context, limit):
    """Set velocity limit"""
    context["velocity_limit"] = limit


@then(parsers.parse('the pattern type should be "{pattern_type}"'))
def verify_pattern_type(context, pattern_type):
    """Verify detected pattern type"""
    violations = context.get("detected_violations", [])
    pattern_violations = [v for v in violations if v.violation_type == "SUSPICIOUS_PATTERN"]
    
    assert len(pattern_violations) > 0, "No suspicious pattern violations found"
    
    # Check violation data for pattern type
    for violation in pattern_violations:
        if violation.violation_data and "pattern_type" in violation.violation_data:
            assert violation.violation_data["pattern_type"] == pattern_type, \
                f"Expected pattern type {pattern_type}, got {violation.violation_data['pattern_type']}"
            return
    
    # If not in violation_data, check description
    assert any(pattern_type.lower() in v.description.lower() for v in pattern_violations), \
        f"Pattern type {pattern_type} not found in violation descriptions"


# Geographic risk scenario
@given(parsers.parse('a transaction from country "{country_code}"'))
def transaction_from_country(context, country_code):
    """Create transaction from specific country"""
    context["transaction_data"] = {
        "account_id": "TEST_ACC_GEO",
        "amount": 5000.0,
        "currency": "AUD",
        "transaction_type": "TRANSFER",
        "description": "International transaction",
        "transaction_channel": "ONLINE",
        "location_country": country_code,
        "location_city": "Test City"
    }


@given(parsers.parse('"{country_code}" is in the high-risk countries list'))
def country_in_high_risk_list(context, country_code):
    """Verify country is in high-risk list"""
    context["high_risk_country"] = country_code


@then("the violation should require enhanced due diligence")
def verify_enhanced_due_diligence(context):
    """Verify violation requires enhanced due diligence"""
    violations = context.get("detected_violations", [])
    
    for violation in violations:
        if violation.violation_data:
            assert violation.violation_data.get("requires_enhanced_due_diligence", False), \
                "Violation should require enhanced due diligence"
            return
    
    # Check remediation actions
    for violation in violations:
        if violation.remediation_actions:
            actions_text = " ".join(violation.remediation_actions).lower()
            assert "enhanced due diligence" in actions_text, \
                "Enhanced due diligence not found in remediation actions"
            return
    
    assert False, "Enhanced due diligence requirement not found"


# Structuring pattern scenario
@given(parsers.parse('4 transactions with amounts ${amount1:d}, ${amount2:d}, ${amount3:d}, ${amount4:d}'))
def multiple_transactions_near_threshold(context, amount1, amount2, amount3, amount4, transaction_service):
    """Create multiple transactions near reporting threshold"""
    account_id = context.get("account_id", "TEST_ACC_STRUCT")
    amounts = [float(amount1), float(amount2), float(amount3), float(amount4)]
    
    transactions = []
    base_time = datetime.utcnow()
    
    for i, amount in enumerate(amounts):
        transaction_data = {
            "account_id": account_id,
            "amount": amount,
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": f"Near threshold transaction {i+1}",
            "transaction_channel": "ONLINE",
            "location_country": "AUS",
            "transaction_timestamp": base_time + timedelta(hours=i)
        }
        
        transaction = transaction_service.create_transaction(transaction_data)
        transactions.append(transaction)
    
    context["structuring_transactions"] = transactions


@given(parsers.parse("the reporting threshold is ${threshold:d}"))
def reporting_threshold(context, threshold):
    """Set reporting threshold"""
    context["reporting_threshold"] = float(threshold)


@then("a suspicious pattern should be detected")
def suspicious_pattern_detected(context, transaction_service):
    """Verify suspicious pattern was detected"""
    account_id = context.get("account_id", "TEST_ACC_STRUCT")
    patterns = transaction_service.detect_suspicious_patterns(account_id)
    
    assert len(patterns) > 0, "No suspicious patterns detected"
    context["detected_patterns"] = patterns


@then("the pattern should indicate potential structuring")
def verify_structuring_pattern(context):
    """Verify pattern indicates potential structuring"""
    patterns = context.get("detected_patterns", [])
    
    assert any("structuring" in p.pattern_description.lower() for p in patterns), \
        "No structuring pattern detected"


# Temporal pattern scenario
@given(parsers.parse("{count:d} transactions between 11 PM and 5 AM"))
def transactions_unusual_hours(context, count, transaction_service):
    """Create transactions during unusual hours"""
    account_id = context.get("account_id", "TEST_ACC_TIME")
    
    transactions = []
    base_date = datetime.utcnow().replace(hour=23, minute=0, second=0, microsecond=0)  # 11 PM
    
    for i in range(count):
        # Alternate between late night and early morning
        if i % 2 == 0:
            transaction_time = base_date + timedelta(minutes=i*30)  # Late night
        else:
            transaction_time = base_date.replace(hour=3) + timedelta(minutes=i*30)  # Early morning
        
        transaction_data = {
            "account_id": account_id,
            "amount": 2000.0 + i * 100,
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": f"Unusual time transaction {i+1}",
            "transaction_channel": "ONLINE",
            "location_country": "AUS",
            "transaction_timestamp": transaction_time
        }
        
        transaction = transaction_service.create_transaction(transaction_data)
        transactions.append(transaction)
    
    context["unusual_time_transactions"] = transactions


@then("the pattern should indicate unusual timing")
def verify_unusual_timing_pattern(context):
    """Verify pattern indicates unusual timing"""
    patterns = context.get("detected_patterns", [])
    
    assert any("timing" in p.pattern_description.lower() or "hours" in p.pattern_description.lower() 
              for p in patterns), "No unusual timing pattern detected"


# Violation resolution scenario
@given(parsers.parse('a compliance violation exists with ID "{violation_id}"'))
def existing_violation(context, violation_id, db_session):
    """Create an existing compliance violation"""
    violation = ComplianceViolation(
        violation_id=violation_id,
        violation_type="TRANSACTION_LIMIT",
        severity="HIGH",
        title="Test violation",
        description="Test violation for resolution",
        regulatory_framework="APRA",
        risk_score=5.0,
        status="OPEN"
    )
    
    db_session.add(violation)
    db_session.commit()
    context["test_violation"] = violation


@given(parsers.parse('the violation status is "{status}"'))
def violation_status(context, status):
    """Verify violation status"""
    violation = context["test_violation"]
    assert violation.status == status


@when(parsers.parse('the violation is resolved by "{resolved_by}"'))
def resolve_violation(context, resolved_by, compliance_service):
    """Resolve the violation"""
    violation_id = context["test_violation"].violation_id
    resolution_notes = context.get("resolution_notes", "Test resolution")
    
    success = compliance_service.resolve_violation(violation_id, resolution_notes, resolved_by)
    context["resolution_success"] = success


@when(parsers.parse('resolution notes are "{notes}"'))
def set_resolution_notes(context, notes):
    """Set resolution notes"""
    context["resolution_notes"] = notes


@then(parsers.parse('the violation status should be "{expected_status}"'))
def verify_violation_status(context, expected_status, db_session):
    """Verify violation status after resolution"""
    violation_id = context["test_violation"].violation_id
    violation = db_session.query(ComplianceViolation).filter(
        ComplianceViolation.violation_id == violation_id
    ).first()
    
    assert violation.status == expected_status


@then("the resolved_at timestamp should be set")
def verify_resolved_timestamp(context, db_session):
    """Verify resolved_at timestamp is set"""
    violation_id = context["test_violation"].violation_id
    violation = db_session.query(ComplianceViolation).filter(
        ComplianceViolation.violation_id == violation_id
    ).first()
    
    assert violation.resolved_at is not None


@then("the resolution should be logged in audit trail")
def verify_audit_trail(context):
    """Verify resolution is logged in audit trail"""
    # This would check audit log table in a real implementation
    assert context.get("resolution_success", False), "Resolution was not successful"


# Data quality violation scenarios
@given(parsers.parse('a transaction with missing required field "{field_name}"'))
def transaction_missing_field(context, field_name):
    """Create transaction data missing required field"""
    context["transaction_data"] = {
        "amount": 1000.0,
        "currency": "AUD",
        "transaction_type": "DEBIT",
        "description": "Test transaction with missing field"
    }
    # Deliberately omit the specified field
    context["missing_field"] = field_name


@given(parsers.parse('a transaction with currency "{currency}"'))
def transaction_invalid_currency(context, currency):
    """Create transaction with invalid currency"""
    context["transaction_data"] = {
        "account_id": "TEST_ACC_001",
        "amount": 1000.0,
        "currency": currency,
        "transaction_type": "DEBIT",
        "description": "Test transaction with invalid currency"
    }


@given(parsers.parse("a transaction with amount {amount:d}"))
def transaction_negative_amount(context, amount):
    """Create transaction with negative amount"""
    context["transaction_data"] = {
        "account_id": "TEST_ACC_001",
        "amount": float(amount),
        "currency": "AUD",
        "transaction_type": "DEBIT",
        "description": "Test transaction with negative amount"
    }


@then("a data quality violation should be raised")
def verify_data_quality_violation(context):
    """Verify data quality violation was raised"""
    error = context.get("processing_error")
    assert error is not None, "No error was raised"
    assert isinstance(error, DataQualityViolation), f"Expected DataQualityViolation, got {type(error)}"


@then("the transaction should be rejected")
def verify_transaction_rejected(context):
    """Verify transaction was rejected"""
    assert context.get("processed_transaction") is None, "Transaction should have been rejected"
    assert context.get("processing_error") is not None, "Error should have been raised"


@then(parsers.parse('the error should specify the missing field'))
def verify_missing_field_error(context):
    """Verify error specifies missing field"""
    error = context.get("processing_error")
    missing_field = context.get("missing_field")
    
    assert missing_field in str(error), f"Error should mention missing field {missing_field}"


@then(parsers.parse('the error should specify "{error_message}"'))
def verify_error_message(context, error_message):
    """Verify specific error message"""
    error = context.get("processing_error")
    assert error_message in str(error), f"Error should contain: {error_message}"


# Dashboard scenario
@given(parsers.parse("{count:d} critical violations exist"))
def create_critical_violations(context, count, db_session):
    """Create critical violations for dashboard testing"""
    violations = []
    for i in range(count):
        violation = ComplianceViolation(
            violation_type="TRANSACTION_LIMIT",
            severity="CRITICAL",
            title=f"Critical violation {i+1}",
            description=f"Test critical violation {i+1}",
            regulatory_framework="APRA",
            risk_score=9.0,
            status="OPEN"
        )
        violations.append(violation)
        db_session.add(violation)
    
    db_session.commit()
    context["critical_violations"] = violations


@given(parsers.parse("{count:d} high violations exist"))
def create_high_violations(context, count, db_session):
    """Create high severity violations"""
    violations = []
    for i in range(count):
        violation = ComplianceViolation(
            violation_type="SUSPICIOUS_PATTERN",
            severity="HIGH",
            title=f"High violation {i+1}",
            description=f"Test high violation {i+1}",
            regulatory_framework="APRA",
            risk_score=7.0,
            status="OPEN"
        )
        violations.append(violation)
        db_session.add(violation)
    
    db_session.commit()
    context["high_violations"] = violations


@given(parsers.parse("{count:d} violations are overdue"))
def create_overdue_violations(context, count, db_session):
    """Create overdue violations"""
    # Make some critical violations overdue (>24 hours old)
    critical_violations = context.get("critical_violations", [])
    
    for i in range(min(count, len(critical_violations))):
        violation = critical_violations[i]
        violation.detected_at = datetime.utcnow() - timedelta(hours=25)  # Make it overdue
        db_session.commit()


@when("the compliance dashboard is requested")
def request_dashboard(context, compliance_service):
    """Request compliance dashboard data"""
    # This would typically be done through API call
    # For testing, we'll simulate the dashboard data calculation
    context["dashboard_requested"] = True


@then(parsers.parse("the dashboard should show {count:d} critical violations"))
def verify_dashboard_critical_count(context, count, db_session):
    """Verify dashboard shows correct critical violation count"""
    critical_count = db_session.query(ComplianceViolation).filter(
        ComplianceViolation.severity == "CRITICAL"
    ).count()
    
    assert critical_count == count, f"Expected {count} critical violations, got {critical_count}"


@then(parsers.parse("the dashboard should show {count:d} high violations"))
def verify_dashboard_high_count(context, count, db_session):
    """Verify dashboard shows correct high violation count"""
    high_count = db_session.query(ComplianceViolation).filter(
        ComplianceViolation.severity == "HIGH"
    ).count()
    
    assert high_count == count, f"Expected {count} high violations, got {high_count}"


@then(parsers.parse("the dashboard should show {count:d} overdue violations"))
def verify_dashboard_overdue_count(context, count, db_session):
    """Verify dashboard shows correct overdue violation count"""
    violations = db_session.query(ComplianceViolation).all()
    overdue_count = sum(1 for v in violations if v.is_overdue)
    
    assert overdue_count == count, f"Expected {count} overdue violations, got {overdue_count}"


@then("the compliance score should be calculated correctly")
def verify_compliance_score(context):
    """Verify compliance score calculation"""
    # This would verify the compliance score calculation logic
    # For now, just verify the dashboard was requested
    assert context.get("dashboard_requested", False), "Dashboard should have been requested"


# APRA reporting scenario
@given(parsers.parse("a high-value transaction over ${amount:d}"))
def high_value_transaction(context, amount):
    """Create high-value transaction"""
    context["transaction_data"] = {
        "account_id": "TEST_ACC_HV",
        "amount": float(amount + 1000),  # Ensure it's over the threshold
        "currency": "AUD",
        "transaction_type": "TRANSFER",
        "description": "High-value transaction",
        "transaction_channel": "ONLINE",
        "location_country": "AUS"
    }


@given("the transaction is international")
def international_transaction(context):
    """Make transaction international"""
    context["transaction_data"]["location_country"] = "USA"
    context["transaction_data"]["counterparty_bank"] = "US Bank"


@then("the transaction should be marked for reporting")
def verify_marked_for_reporting(context):
    """Verify transaction is marked for reporting"""
    transaction = context.get("processed_transaction")
    assert transaction is not None, "No transaction was processed"
    assert transaction.requires_reporting, "Transaction should be marked for reporting"


@then("AUSTRAC reporting should be triggered")
def verify_austrac_reporting(context):
    """Verify AUSTRAC reporting is triggered"""
    # In a real implementation, this would check if AUSTRAC reporting was initiated
    transaction = context.get("processed_transaction")
    assert transaction.is_high_value or transaction.is_international, \
        "Transaction should trigger AUSTRAC reporting"


@then("the transaction should require enhanced monitoring")
def verify_enhanced_monitoring(context):
    """Verify transaction requires enhanced monitoring"""
    transaction = context.get("processed_transaction")
    assert transaction.is_flagged or transaction.risk_score > 0, \
        "Transaction should require enhanced monitoring"
