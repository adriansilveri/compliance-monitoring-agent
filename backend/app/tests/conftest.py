"""
Test configuration and fixtures
Following SOLID principles for test setup
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

from app.core.database import Base
from app.models import transaction, compliance, user  # Import all models


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    # Use in-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return {
        "account_id": "TEST_ACC_001",
        "amount": 5000.0,
        "currency": "AUD",
        "transaction_type": "DEBIT",
        "description": "Test transaction",
        "counterparty_account": "COUNTERPARTY_001",
        "counterparty_name": "Test Counterparty",
        "transaction_channel": "ONLINE",
        "location_country": "AUS",
        "location_city": "Sydney"
    }


@pytest.fixture
def sample_high_value_transaction_data():
    """Sample high-value transaction data for testing violations"""
    return {
        "account_id": "TEST_ACC_002",
        "amount": 15000.0,  # Exceeds APRA limit
        "currency": "AUD",
        "transaction_type": "TRANSFER",
        "description": "High value test transaction",
        "counterparty_account": "COUNTERPARTY_002",
        "counterparty_name": "High Value Counterparty",
        "transaction_channel": "ONLINE",
        "location_country": "AUS",
        "location_city": "Melbourne"
    }


@pytest.fixture
def sample_high_risk_transaction_data():
    """Sample high-risk transaction data for testing violations"""
    return {
        "account_id": "TEST_ACC_003",
        "amount": 8000.0,
        "currency": "AUD",
        "transaction_type": "TRANSFER",
        "description": "High risk country transaction",
        "counterparty_account": "FOREIGN_001",
        "counterparty_name": "Foreign Entity",
        "transaction_channel": "ONLINE",
        "location_country": "IRN",  # High-risk country
        "location_city": "Tehran"
    }


@pytest.fixture
def sample_structuring_transaction_data():
    """Sample transaction data for structuring pattern testing"""
    return [
        {
            "account_id": "TEST_ACC_004",
            "amount": 9500.0,
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": "Near threshold transaction 1",
            "transaction_channel": "ONLINE",
            "location_country": "AUS"
        },
        {
            "account_id": "TEST_ACC_004",
            "amount": 9800.0,
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": "Near threshold transaction 2",
            "transaction_channel": "ONLINE",
            "location_country": "AUS"
        },
        {
            "account_id": "TEST_ACC_004",
            "amount": 9200.0,
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": "Near threshold transaction 3",
            "transaction_channel": "ONLINE",
            "location_country": "AUS"
        },
        {
            "account_id": "TEST_ACC_004",
            "amount": 9900.0,
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": "Near threshold transaction 4",
            "transaction_channel": "ONLINE",
            "location_country": "AUS"
        }
    ]


# Pytest markers for organizing tests
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "bdd: Behavior-driven development tests")
    config.addinivalue_line("markers", "compliance: Compliance-related tests")
    config.addinivalue_line("markers", "apra: APRA-specific compliance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data(test_db_session):
    """Automatically cleanup test data after each test"""
    yield
    # Cleanup is handled by session rollback in test_db_session fixture
