"""
Transaction model for compliance monitoring
Following SOLID principles - Single Responsibility for transaction data
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

from app.core.database import Base


class Transaction(Base):
    """
    Transaction model for tracking financial transactions
    Following SOLID principles and DRY - single source of transaction data
    """
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Transaction details
    account_id = Column(String(50), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="AUD")
    transaction_type = Column(String(50), nullable=False)  # DEBIT, CREDIT, TRANSFER
    description = Column(Text)
    
    # Counterparty information
    counterparty_account = Column(String(50))
    counterparty_name = Column(String(200))
    counterparty_bank = Column(String(100))
    
    # Geographic and channel information
    transaction_channel = Column(String(50))  # ONLINE, ATM, BRANCH, MOBILE
    location_country = Column(String(3), default="AUS")
    location_city = Column(String(100))
    ip_address = Column(String(45))  # IPv6 compatible
    
    # Timestamps
    transaction_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Compliance flags
    is_flagged = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    compliance_status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED, UNDER_REVIEW
    
    # Relationships
    violations = relationship("ComplianceViolation", back_populates="transaction")
    
    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, amount={self.amount}, type={self.transaction_type})>"
    
    @property
    def is_high_value(self) -> bool:
        """Check if transaction is high value (>$10,000 AUD)"""
        return self.amount > 10000.0
    
    @property
    def is_international(self) -> bool:
        """Check if transaction is international"""
        return self.location_country != "AUS"
    
    @property
    def requires_reporting(self) -> bool:
        """Check if transaction requires regulatory reporting"""
        return self.is_high_value or self.is_international or self.is_flagged


class TransactionPattern(Base):
    """
    Model for storing detected transaction patterns
    Following Single Responsibility Principle
    """
    __tablename__ = "transaction_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Pattern details
    account_id = Column(String(50), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False)  # VELOCITY, AMOUNT, GEOGRAPHIC, TEMPORAL
    pattern_description = Column(Text)
    
    # Pattern metrics
    confidence_score = Column(Float, nullable=False)
    frequency_count = Column(Integer, default=1)
    time_window_hours = Column(Integer, default=24)
    
    # Detection details
    first_detected = Column(DateTime, default=func.now())
    last_detected = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Related transactions
    transaction_ids = Column(Text)  # JSON array of transaction IDs
    
    def __repr__(self):
        return f"<TransactionPattern(id={self.pattern_id}, type={self.pattern_type}, confidence={self.confidence_score})>"
