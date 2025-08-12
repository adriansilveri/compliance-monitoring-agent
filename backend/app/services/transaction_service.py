"""
Transaction Service - Business logic for transaction processing
Following SOLID principles and DRY
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import structlog

from app.models.transaction import Transaction, TransactionPattern
from app.models.compliance import ComplianceViolation
from app.services.compliance_service import ComplianceService
from app.core.exceptions import DataQualityViolation

logger = structlog.get_logger()


class TransactionService:
    """
    Service for transaction operations
    Following Single Responsibility Principle
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.compliance_service = ComplianceService(db_session)
    
    def create_transaction(self, transaction_data: Dict[str, Any]) -> Transaction:
        """
        Create a new transaction with compliance validation
        Following SOLID principles
        """
        # Validate transaction data
        self._validate_transaction_data(transaction_data)
        
        # Create transaction object
        transaction = Transaction(
            account_id=transaction_data["account_id"],
            amount=transaction_data["amount"],
            currency=transaction_data.get("currency", "AUD"),
            transaction_type=transaction_data["transaction_type"],
            description=transaction_data.get("description", ""),
            counterparty_account=transaction_data.get("counterparty_account"),
            counterparty_name=transaction_data.get("counterparty_name"),
            counterparty_bank=transaction_data.get("counterparty_bank"),
            transaction_channel=transaction_data.get("transaction_channel", "ONLINE"),
            location_country=transaction_data.get("location_country", "AUS"),
            location_city=transaction_data.get("location_city"),
            ip_address=transaction_data.get("ip_address"),
            transaction_timestamp=transaction_data.get("transaction_timestamp", datetime.utcnow())
        )
        
        # Save transaction
        self.db_session.add(transaction)
        self.db_session.commit()
        self.db_session.refresh(transaction)
        
        logger.info(
            "Transaction created",
            transaction_id=transaction.transaction_id,
            account_id=transaction.account_id,
            amount=transaction.amount,
            type=transaction.transaction_type
        )
        
        # Evaluate compliance rules
        violations = self.compliance_service.evaluate_transaction(transaction)
        
        if violations:
            logger.warning(
                "Compliance violations detected for transaction",
                transaction_id=transaction.transaction_id,
                violation_count=len(violations)
            )
        
        return transaction
    
    def _validate_transaction_data(self, data: Dict[str, Any]) -> None:
        """
        Validate transaction data quality
        Following KISS principle - simple validation
        """
        required_fields = ["account_id", "amount", "transaction_type"]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                raise DataQualityViolation(
                    message=f"Required field '{field}' is missing",
                    field_name=field,
                    expected_format="non-null value",
                    actual_value=data.get(field)
                )
        
        # Validate amount
        if not isinstance(data["amount"], (int, float)) or data["amount"] <= 0:
            raise DataQualityViolation(
                message="Transaction amount must be a positive number",
                field_name="amount",
                expected_format="positive number",
                actual_value=data.get("amount")
            )
        
        # Validate transaction type
        valid_types = ["DEBIT", "CREDIT", "TRANSFER"]
        if data["transaction_type"] not in valid_types:
            raise DataQualityViolation(
                message=f"Invalid transaction type. Must be one of: {valid_types}",
                field_name="transaction_type",
                expected_format=f"one of {valid_types}",
                actual_value=data.get("transaction_type")
            )
        
        # Validate currency if provided
        if "currency" in data and len(data["currency"]) != 3:
            raise DataQualityViolation(
                message="Currency must be a 3-letter ISO code",
                field_name="currency",
                expected_format="3-letter ISO code (e.g., AUD, USD)",
                actual_value=data.get("currency")
            )
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        return self.db_session.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()
    
    def get_transactions_by_account(
        self, 
        account_id: str, 
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """
        Get transactions for an account with filtering
        Following DRY principle - reusable query method
        """
        query = self.db_session.query(Transaction).filter(
            Transaction.account_id == account_id
        )
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(Transaction.transaction_timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_timestamp <= end_date)
        
        return query.order_by(desc(Transaction.transaction_timestamp)).offset(offset).limit(limit).all()
    
    def get_flagged_transactions(self, limit: int = 100) -> List[Transaction]:
        """Get transactions flagged for compliance violations"""
        return self.db_session.query(Transaction).filter(
            Transaction.is_flagged == True
        ).order_by(desc(Transaction.transaction_timestamp)).limit(limit).all()
    
    def get_high_value_transactions(
        self, 
        threshold: float = 10000.0,
        days: int = 7
    ) -> List[Transaction]:
        """Get high-value transactions within specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db_session.query(Transaction).filter(
            and_(
                Transaction.amount >= threshold,
                Transaction.transaction_timestamp >= cutoff_date
            )
        ).order_by(desc(Transaction.amount)).all()
    
    def get_transaction_statistics(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get transaction statistics
        Following KISS principle - simple statistics calculation
        """
        query = self.db_session.query(Transaction)
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        
        transactions = query.all()
        
        if not transactions:
            return {
                "total_transactions": 0,
                "total_amount": 0.0,
                "average_amount": 0.0,
                "flagged_count": 0,
                "flagged_percentage": 0.0
            }
        
        total_amount = sum(t.amount for t in transactions)
        flagged_count = sum(1 for t in transactions if t.is_flagged)
        
        return {
            "total_transactions": len(transactions),
            "total_amount": total_amount,
            "average_amount": total_amount / len(transactions),
            "flagged_count": flagged_count,
            "flagged_percentage": (flagged_count / len(transactions)) * 100,
            "high_value_count": sum(1 for t in transactions if t.is_high_value),
            "international_count": sum(1 for t in transactions if t.is_international)
        }
    
    def detect_suspicious_patterns(self, account_id: str) -> List[TransactionPattern]:
        """
        Detect suspicious transaction patterns
        Following Single Responsibility Principle
        """
        patterns = []
        
        # Get recent transactions for pattern analysis
        recent_transactions = self.get_transactions_by_account(
            account_id=account_id,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        if len(recent_transactions) < 5:  # Need minimum transactions for pattern detection
            return patterns
        
        # Detect velocity patterns
        velocity_pattern = self._detect_velocity_pattern(recent_transactions)
        if velocity_pattern:
            patterns.append(velocity_pattern)
        
        # Detect amount patterns
        amount_pattern = self._detect_amount_pattern(recent_transactions)
        if amount_pattern:
            patterns.append(amount_pattern)
        
        # Detect time patterns
        time_pattern = self._detect_time_pattern(recent_transactions)
        if time_pattern:
            patterns.append(time_pattern)
        
        # Save detected patterns
        for pattern in patterns:
            self.db_session.add(pattern)
        
        if patterns:
            self.db_session.commit()
            
            logger.info(
                "Suspicious patterns detected",
                account_id=account_id,
                pattern_count=len(patterns)
            )
        
        return patterns
    
    def _detect_velocity_pattern(self, transactions: List[Transaction]) -> Optional[TransactionPattern]:
        """Detect high-velocity transaction patterns"""
        # Group transactions by hour
        hourly_counts = {}
        for transaction in transactions:
            hour_key = transaction.transaction_timestamp.strftime("%Y-%m-%d-%H")
            hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
        
        # Check for hours with excessive transactions
        max_hourly_count = max(hourly_counts.values()) if hourly_counts else 0
        
        if max_hourly_count > 5:  # Threshold for suspicious velocity
            confidence_score = min(max_hourly_count / 10.0, 1.0)
            
            pattern = TransactionPattern(
                account_id=transactions[0].account_id,
                pattern_type="VELOCITY",
                pattern_description=f"High transaction velocity detected: {max_hourly_count} transactions in one hour",
                confidence_score=confidence_score,
                frequency_count=max_hourly_count,
                time_window_hours=1,
                transaction_ids=str([t.transaction_id for t in transactions])
            )
            
            return pattern
        
        return None
    
    def _detect_amount_pattern(self, transactions: List[Transaction]) -> Optional[TransactionPattern]:
        """Detect suspicious amount patterns (e.g., structuring)"""
        # Look for multiple transactions just under reporting thresholds
        threshold = 10000.0
        near_threshold_transactions = [
            t for t in transactions 
            if 9000.0 <= t.amount < threshold
        ]
        
        if len(near_threshold_transactions) >= 3:
            confidence_score = min(len(near_threshold_transactions) / 5.0, 1.0)
            
            pattern = TransactionPattern(
                account_id=transactions[0].account_id,
                pattern_type="AMOUNT",
                pattern_description=f"Potential structuring detected: {len(near_threshold_transactions)} transactions near ${threshold:,.2f} threshold",
                confidence_score=confidence_score,
                frequency_count=len(near_threshold_transactions),
                time_window_hours=24,
                transaction_ids=str([t.transaction_id for t in near_threshold_transactions])
            )
            
            return pattern
        
        return None
    
    def _detect_time_pattern(self, transactions: List[Transaction]) -> Optional[TransactionPattern]:
        """Detect unusual timing patterns"""
        # Check for transactions outside normal business hours
        unusual_time_transactions = []
        
        for transaction in transactions:
            hour = transaction.transaction_timestamp.hour
            # Consider 10 PM to 6 AM as unusual hours
            if hour >= 22 or hour <= 6:
                unusual_time_transactions.append(transaction)
        
        if len(unusual_time_transactions) >= 3:
            confidence_score = min(len(unusual_time_transactions) / 10.0, 1.0)
            
            pattern = TransactionPattern(
                account_id=transactions[0].account_id,
                pattern_type="TEMPORAL",
                pattern_description=f"Unusual timing pattern: {len(unusual_time_transactions)} transactions outside business hours",
                confidence_score=confidence_score,
                frequency_count=len(unusual_time_transactions),
                time_window_hours=24,
                transaction_ids=str([t.transaction_id for t in unusual_time_transactions])
            )
            
            return pattern
        
        return None
