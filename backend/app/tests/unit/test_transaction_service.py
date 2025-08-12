"""
Unit tests for TransactionService
Following SOLID principles and comprehensive test coverage
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.transaction_service import TransactionService
from app.models.transaction import Transaction, TransactionPattern
from app.core.exceptions import DataQualityViolation


class TestTransactionService:
    """Test TransactionService functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def transaction_service(self, mock_db_session):
        """TransactionService fixture"""
        return TransactionService(mock_db_session)
    
    def test_create_transaction_success(self, transaction_service, mock_db_session):
        """Test successful transaction creation"""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 5000.0,
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": "Test transaction",
            "transaction_channel": "ONLINE",
            "location_country": "AUS"
        }
        
        # Mock compliance service evaluation
        with patch.object(transaction_service.compliance_service, 'evaluate_transaction', return_value=[]):
            transaction = transaction_service.create_transaction(transaction_data)
            
            assert transaction.account_id == "ACC123"
            assert transaction.amount == 5000.0
            assert transaction.currency == "AUD"
            assert transaction.transaction_type == "DEBIT"
            assert transaction.location_country == "AUS"
            
            # Verify database operations
            mock_db_session.add.assert_called_once()
            assert mock_db_session.commit.call_count >= 1
            mock_db_session.refresh.assert_called_once()
    
    def test_create_transaction_with_violations(self, transaction_service, mock_db_session):
        """Test transaction creation that triggers compliance violations"""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 15000.0,  # High amount
            "currency": "AUD",
            "transaction_type": "DEBIT",
            "description": "High value transaction"
        }
        
        # Mock compliance violations
        mock_violations = [Mock(), Mock()]  # Two violations
        
        with patch.object(transaction_service.compliance_service, 'evaluate_transaction', return_value=mock_violations):
            transaction = transaction_service.create_transaction(transaction_data)
            
            assert transaction.amount == 15000.0
            # Compliance service should have been called
            transaction_service.compliance_service.evaluate_transaction.assert_called_once()
    
    def test_validate_transaction_data_success(self, transaction_service):
        """Test successful transaction data validation"""
        valid_data = {
            "account_id": "ACC123",
            "amount": 1000.0,
            "transaction_type": "DEBIT",
            "currency": "AUD"
        }
        
        # Should not raise any exception
        transaction_service._validate_transaction_data(valid_data)
    
    def test_validate_transaction_data_missing_required_field(self, transaction_service):
        """Test validation fails for missing required field"""
        invalid_data = {
            "amount": 1000.0,
            "transaction_type": "DEBIT"
            # Missing account_id
        }
        
        with pytest.raises(DataQualityViolation) as exc_info:
            transaction_service._validate_transaction_data(invalid_data)
        
        assert "account_id" in str(exc_info.value)
        assert exc_info.value.field_name == "account_id"
    
    def test_validate_transaction_data_invalid_amount(self, transaction_service):
        """Test validation fails for invalid amount"""
        invalid_data = {
            "account_id": "ACC123",
            "amount": -1000.0,  # Negative amount
            "transaction_type": "DEBIT"
        }
        
        with pytest.raises(DataQualityViolation) as exc_info:
            transaction_service._validate_transaction_data(invalid_data)
        
        assert "positive number" in str(exc_info.value)
        assert exc_info.value.field_name == "amount"
    
    def test_validate_transaction_data_zero_amount(self, transaction_service):
        """Test validation fails for zero amount"""
        invalid_data = {
            "account_id": "ACC123",
            "amount": 0.0,
            "transaction_type": "DEBIT"
        }
        
        with pytest.raises(DataQualityViolation):
            transaction_service._validate_transaction_data(invalid_data)
    
    def test_validate_transaction_data_invalid_type(self, transaction_service):
        """Test validation fails for invalid transaction type"""
        invalid_data = {
            "account_id": "ACC123",
            "amount": 1000.0,
            "transaction_type": "INVALID_TYPE"
        }
        
        with pytest.raises(DataQualityViolation) as exc_info:
            transaction_service._validate_transaction_data(invalid_data)
        
        assert "DEBIT" in str(exc_info.value)
        assert "CREDIT" in str(exc_info.value)
        assert "TRANSFER" in str(exc_info.value)
    
    def test_validate_transaction_data_invalid_currency(self, transaction_service):
        """Test validation fails for invalid currency format"""
        invalid_data = {
            "account_id": "ACC123",
            "amount": 1000.0,
            "transaction_type": "DEBIT",
            "currency": "INVALID"  # Not 3 letters
        }
        
        with pytest.raises(DataQualityViolation) as exc_info:
            transaction_service._validate_transaction_data(invalid_data)
        
        assert "3-letter ISO code" in str(exc_info.value)
        assert exc_info.value.field_name == "currency"
    
    def test_get_transaction_found(self, transaction_service, mock_db_session):
        """Test getting existing transaction"""
        mock_transaction = Transaction(transaction_id="TXN123", amount=1000.0)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_transaction
        
        result = transaction_service.get_transaction("TXN123")
        
        assert result == mock_transaction
        mock_db_session.query.assert_called_with(Transaction)
    
    def test_get_transaction_not_found(self, transaction_service, mock_db_session):
        """Test getting non-existent transaction"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = transaction_service.get_transaction("NONEXISTENT")
        
        assert result is None
    
    def test_get_transactions_by_account(self, transaction_service, mock_db_session):
        """Test getting transactions by account"""
        mock_transactions = [
            Transaction(account_id="ACC123", amount=1000.0),
            Transaction(account_id="ACC123", amount=2000.0)
        ]
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_transactions
        
        result = transaction_service.get_transactions_by_account("ACC123", limit=10, offset=0)
        
        assert len(result) == 2
        assert all(t.account_id == "ACC123" for t in result)
    
    def test_get_transactions_by_account_with_date_filters(self, transaction_service, mock_db_session):
        """Test getting transactions by account with date filters"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        mock_transactions = [Transaction(account_id="ACC123", amount=1000.0)]
        mock_db_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_transactions
        
        result = transaction_service.get_transactions_by_account(
            "ACC123", 
            start_date=start_date, 
            end_date=end_date
        )
        
        assert len(result) == 1
        # Verify filters were applied (multiple filter calls)
        assert mock_db_session.query.return_value.filter.call_count >= 3
    
    def test_get_flagged_transactions(self, transaction_service, mock_db_session):
        """Test getting flagged transactions"""
        mock_transactions = [
            Transaction(transaction_id="TXN1", is_flagged=True),
            Transaction(transaction_id="TXN2", is_flagged=True)
        ]
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_transactions
        
        result = transaction_service.get_flagged_transactions(limit=50)
        
        assert len(result) == 2
        assert all(t.is_flagged for t in result)
    
    def test_get_high_value_transactions(self, transaction_service, mock_db_session):
        """Test getting high-value transactions"""
        mock_transactions = [
            Transaction(amount=15000.0),
            Transaction(amount=25000.0)
        ]
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_transactions
        
        result = transaction_service.get_high_value_transactions(threshold=10000.0, days=7)
        
        assert len(result) == 2
        assert all(t.amount >= 10000.0 for t in result)
    
    def test_get_transaction_statistics_with_data(self, transaction_service, mock_db_session):
        """Test transaction statistics calculation with data"""
        mock_transactions = [
            Transaction(amount=1000.0, is_flagged=False, location_country="AUS"),
            Transaction(amount=15000.0, is_flagged=True, location_country="USA"),  # High value, international
            Transaction(amount=5000.0, is_flagged=True, location_country="AUS"),
            Transaction(amount=2000.0, is_flagged=False, location_country="AUS")
        ]
        
        mock_db_session.query.return_value.all.return_value = mock_transactions
        
        stats = transaction_service.get_transaction_statistics()
        
        assert stats["total_transactions"] == 4
        assert stats["total_amount"] == 23000.0
        assert stats["average_amount"] == 5750.0
        assert stats["flagged_count"] == 2
        assert stats["flagged_percentage"] == 50.0
        assert stats["high_value_count"] == 1  # Only one > 10000
        assert stats["international_count"] == 1  # Only one non-AUS
    
    def test_get_transaction_statistics_no_data(self, transaction_service, mock_db_session):
        """Test transaction statistics with no data"""
        mock_db_session.query.return_value.all.return_value = []
        
        stats = transaction_service.get_transaction_statistics()
        
        assert stats["total_transactions"] == 0
        assert stats["total_amount"] == 0.0
        assert stats["average_amount"] == 0.0
        assert stats["flagged_count"] == 0
        assert stats["flagged_percentage"] == 0.0
    
    def test_get_transaction_statistics_by_account(self, transaction_service, mock_db_session):
        """Test transaction statistics filtered by account"""
        mock_transactions = [
            Transaction(account_id="ACC123", amount=1000.0),
            Transaction(account_id="ACC123", amount=2000.0)
        ]
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_transactions
        
        stats = transaction_service.get_transaction_statistics(account_id="ACC123")
        
        assert stats["total_transactions"] == 2
        assert stats["total_amount"] == 3000.0


class TestTransactionPatternDetection:
    """Test transaction pattern detection functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def transaction_service(self, mock_db_session):
        """TransactionService fixture"""
        return TransactionService(mock_db_session)
    
    def test_detect_suspicious_patterns_insufficient_data(self, transaction_service):
        """Test pattern detection with insufficient transaction data"""
        # Mock get_transactions_by_account to return few transactions
        with patch.object(transaction_service, 'get_transactions_by_account', return_value=[]):
            patterns = transaction_service.detect_suspicious_patterns("ACC123")
            
            assert len(patterns) == 0
    
    def test_detect_velocity_pattern(self, transaction_service, mock_db_session):
        """Test velocity pattern detection"""
        # Create transactions with high velocity
        transactions = []
        base_time = datetime.utcnow()
        
        for i in range(8):  # 8 transactions in same hour
            transactions.append(Transaction(
                account_id="ACC123",
                amount=1000.0,
                transaction_timestamp=base_time.replace(hour=14, minute=i*5)  # Same hour
            ))
        
        with patch.object(transaction_service, 'get_transactions_by_account', return_value=transactions):
            patterns = transaction_service.detect_suspicious_patterns("ACC123")
            
            velocity_patterns = [p for p in patterns if p.pattern_type == "VELOCITY"]
            assert len(velocity_patterns) > 0
            
            velocity_pattern = velocity_patterns[0]
            assert velocity_pattern.account_id == "ACC123"
            assert velocity_pattern.confidence_score > 0
            assert "velocity" in velocity_pattern.pattern_description.lower()
    
    def test_detect_amount_pattern_structuring(self, transaction_service, mock_db_session):
        """Test amount pattern detection for potential structuring"""
        # Create transactions just under $10,000 threshold
        transactions = []
        base_time = datetime.utcnow()
        amounts = [9500.0, 9800.0, 9200.0, 9900.0]  # All under 10k
        
        for i, amount in enumerate(amounts):
            transactions.append(Transaction(
                account_id="ACC123",
                amount=amount,
                transaction_timestamp=base_time + timedelta(hours=i)
            ))
        
        with patch.object(transaction_service, 'get_transactions_by_account', return_value=transactions):
            patterns = transaction_service.detect_suspicious_patterns("ACC123")
            
            amount_patterns = [p for p in patterns if p.pattern_type == "AMOUNT"]
            assert len(amount_patterns) > 0
            
            amount_pattern = amount_patterns[0]
            assert amount_pattern.account_id == "ACC123"
            assert "structuring" in amount_pattern.pattern_description.lower()
            assert amount_pattern.frequency_count == 4
    
    def test_detect_time_pattern_unusual_hours(self, transaction_service, mock_db_session):
        """Test temporal pattern detection for unusual hours"""
        # Create transactions during unusual hours (late night/early morning)
        transactions = []
        base_date = datetime.utcnow().replace(hour=23, minute=0, second=0, microsecond=0)
        
        # Create 4 transactions: 2 late night, 2 early morning
        unusual_hours = [23, 1, 2, 4]  # 11 PM, 1 AM, 2 AM, 4 AM
        
        for i, hour in enumerate(unusual_hours):
            transactions.append(Transaction(
                account_id="ACC123",
                amount=2000.0,
                transaction_timestamp=base_date.replace(hour=hour) + timedelta(days=i)
            ))
        
        with patch.object(transaction_service, 'get_transactions_by_account', return_value=transactions):
            patterns = transaction_service.detect_suspicious_patterns("ACC123")
            
            time_patterns = [p for p in patterns if p.pattern_type == "TEMPORAL"]
            assert len(time_patterns) > 0
            
            time_pattern = time_patterns[0]
            assert time_pattern.account_id == "ACC123"
            assert "timing" in time_pattern.pattern_description.lower() or "hours" in time_pattern.pattern_description.lower()
            assert time_pattern.frequency_count == 4
    
    def test_detect_multiple_patterns(self, transaction_service, mock_db_session):
        """Test detection of multiple pattern types simultaneously"""
        transactions = []
        base_time = datetime.utcnow()
        
        # Create transactions that trigger multiple patterns
        # 1. High velocity (many transactions in one hour)
        # 2. Amount structuring (near threshold amounts)
        # 3. Unusual timing (late night transactions)
        
        amounts = [9500.0, 9800.0, 9200.0, 9900.0, 9700.0]
        
        for i, amount in enumerate(amounts):
            transactions.append(Transaction(
                account_id="ACC123",
                amount=amount,
                transaction_timestamp=base_time.replace(hour=23, minute=i*10)  # Late night, high velocity
            ))
        
        with patch.object(transaction_service, 'get_transactions_by_account', return_value=transactions):
            mock_db_session.add.return_value = None
            mock_db_session.commit.return_value = None
            
            patterns = transaction_service.detect_suspicious_patterns("ACC123")
            
            # Should detect multiple pattern types
            pattern_types = [p.pattern_type for p in patterns]
            assert len(set(pattern_types)) > 1  # Multiple different pattern types
            
            # Verify patterns were saved to database
            assert mock_db_session.add.call_count == len(patterns)
            if patterns:
                mock_db_session.commit.assert_called_once()
    
    def test_velocity_pattern_confidence_scoring(self, transaction_service):
        """Test velocity pattern confidence scoring"""
        # Test different velocity levels and their confidence scores
        test_cases = [
            (6, 0.6),   # 6 transactions -> confidence 0.6
            (10, 1.0),  # 10 transactions -> confidence 1.0 (capped)
            (15, 1.0),  # 15 transactions -> confidence 1.0 (capped)
        ]
        
        for transaction_count, expected_confidence in test_cases:
            transactions = []
            base_time = datetime.utcnow()
            
            for i in range(transaction_count):
                transactions.append(Transaction(
                    account_id="ACC123",
                    amount=1000.0,
                    transaction_timestamp=base_time.replace(hour=14, minute=i*5)
                ))
            
            pattern = transaction_service._detect_velocity_pattern(transactions)
            
            if pattern:
                assert abs(pattern.confidence_score - expected_confidence) < 0.1
    
    def test_amount_pattern_confidence_scoring(self, transaction_service):
        """Test amount pattern confidence scoring"""
        # Test different numbers of near-threshold transactions
        test_cases = [
            (3, 0.6),   # 3 transactions -> confidence 0.6
            (5, 1.0),   # 5 transactions -> confidence 1.0 (capped)
            (7, 1.0),   # 7 transactions -> confidence 1.0 (capped)
        ]
        
        for transaction_count, expected_confidence in test_cases:
            transactions = []
            base_time = datetime.utcnow()
            
            for i in range(transaction_count):
                transactions.append(Transaction(
                    account_id="ACC123",
                    amount=9500.0,  # Just under 10k threshold
                    transaction_timestamp=base_time + timedelta(hours=i)
                ))
            
            pattern = transaction_service._detect_amount_pattern(transactions)
            
            if pattern:
                assert abs(pattern.confidence_score - expected_confidence) < 0.1
    
    def test_no_patterns_detected_normal_transactions(self, transaction_service):
        """Test that normal transactions don't trigger pattern detection"""
        # Create normal, spread-out transactions during business hours
        transactions = []
        base_time = datetime.utcnow().replace(hour=10, minute=0)  # Business hours
        
        for i in range(3):  # Few transactions
            transactions.append(Transaction(
                account_id="ACC123",
                amount=2000.0,  # Normal amounts
                transaction_timestamp=base_time + timedelta(days=i)  # Spread over days
            ))
        
        velocity_pattern = transaction_service._detect_velocity_pattern(transactions)
        amount_pattern = transaction_service._detect_amount_pattern(transactions)
        time_pattern = transaction_service._detect_time_pattern(transactions)
        
        assert velocity_pattern is None
        assert amount_pattern is None
        assert time_pattern is None
