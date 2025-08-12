"""
User model for authentication and authorization
Following SOLID principles - Single Responsibility for user management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database import Base


class User(Base):
    """
    User model for system access and role management
    Following SOLID principles
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # User identification
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Authorization
    role = Column(String(50), nullable=False, default="VIEWER")  # ADMIN, COMPLIANCE_OFFICER, ANALYST, VIEWER
    permissions = Column(JSON)  # Store specific permissions
    
    # Profile information
    department = Column(String(100))
    position = Column(String(100))
    phone = Column(String(20))
    
    # Security
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=func.now())
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(username={self.username}, role={self.role}, active={self.is_active})>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == "ADMIN"
    
    @property
    def is_compliance_officer(self) -> bool:
        """Check if user is a compliance officer"""
        return self.role == "COMPLIANCE_OFFICER"
    
    @property
    def can_manage_violations(self) -> bool:
        """Check if user can manage compliance violations"""
        return self.role in ["ADMIN", "COMPLIANCE_OFFICER"]
    
    @property
    def can_view_sensitive_data(self) -> bool:
        """Check if user can view sensitive compliance data"""
        return self.role in ["ADMIN", "COMPLIANCE_OFFICER", "ANALYST"]
    
    @property
    def is_account_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.account_locked_until:
            return False
        return datetime.utcnow() < self.account_locked_until


class UserSession(Base):
    """
    Model for tracking user sessions
    Following Single Responsibility Principle
    """
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Session details
    user_id = Column(String(50), nullable=False, index=True)
    username = Column(String(100), nullable=False)
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    login_timestamp = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    logout_timestamp = Column(DateTime)
    
    # Session status
    is_active = Column(Boolean, default=True)
    session_duration_minutes = Column(Integer)
    
    def __repr__(self):
        return f"<UserSession(session_id={self.session_id}, username={self.username}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired (inactive for more than 30 minutes)"""
        if not self.is_active or self.logout_timestamp:
            return True
        
        inactive_minutes = (datetime.utcnow() - self.last_activity).total_seconds() / 60
        return inactive_minutes > 30
