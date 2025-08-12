-- APRA Compliance Monitoring Database Initialization
-- Following SOLID principles and proper database design

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS compliance_db;
USE compliance_db;

-- Create tables (these will also be created by SQLAlchemy, but this ensures proper setup)

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) NOT NULL DEFAULT 'VIEWER',
    permissions JSON,
    department VARCHAR(100),
    position VARCHAR(100),
    phone VARCHAR(20),
    last_login DATETIME,
    failed_login_attempts INT DEFAULT 0,
    account_locked_until DATETIME,
    password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'AUD',
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    counterparty_account VARCHAR(50),
    counterparty_name VARCHAR(200),
    counterparty_bank VARCHAR(100),
    transaction_channel VARCHAR(50),
    location_country VARCHAR(3) DEFAULT 'AUS',
    location_city VARCHAR(100),
    ip_address VARCHAR(45),
    transaction_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_flagged BOOLEAN DEFAULT FALSE,
    risk_score DECIMAL(4,2) DEFAULT 0.0,
    compliance_status VARCHAR(20) DEFAULT 'PENDING',
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_account_id (account_id),
    INDEX idx_amount (amount),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_location_country (location_country),
    INDEX idx_transaction_timestamp (transaction_timestamp),
    INDEX idx_is_flagged (is_flagged),
    INDEX idx_compliance_status (compliance_status)
);

-- Transaction patterns table
CREATE TABLE IF NOT EXISTS transaction_patterns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pattern_id VARCHAR(50) UNIQUE NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_description TEXT,
    confidence_score DECIMAL(4,3) NOT NULL,
    frequency_count INT DEFAULT 1,
    time_window_hours INT DEFAULT 24,
    first_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    transaction_ids TEXT,
    INDEX idx_pattern_id (pattern_id),
    INDEX idx_account_id (account_id),
    INDEX idx_pattern_type (pattern_type),
    INDEX idx_confidence_score (confidence_score),
    INDEX idx_first_detected (first_detected)
);

-- Compliance violations table
CREATE TABLE IF NOT EXISTS compliance_violations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    violation_id VARCHAR(50) UNIQUE NOT NULL,
    violation_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    regulatory_framework VARCHAR(50) DEFAULT 'APRA',
    standard_reference VARCHAR(100),
    requirement_id VARCHAR(50),
    transaction_id INT,
    risk_score DECIMAL(4,2) NOT NULL,
    confidence_score DECIMAL(4,3) DEFAULT 1.0,
    impact_assessment VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(20) DEFAULT 'OPEN',
    assigned_to VARCHAR(100),
    resolution_notes TEXT,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at DATETIME,
    resolved_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    violation_data JSON,
    remediation_actions JSON,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE SET NULL,
    INDEX idx_violation_id (violation_id),
    INDEX idx_violation_type (violation_type),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    INDEX idx_regulatory_framework (regulatory_framework),
    INDEX idx_detected_at (detected_at),
    INDEX idx_risk_score (risk_score)
);

-- Compliance rules table
CREATE TABLE IF NOT EXISTS compliance_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    regulatory_framework VARCHAR(50) DEFAULT 'APRA',
    standard_reference VARCHAR(100),
    requirement_id VARCHAR(50),
    rule_logic JSON NOT NULL,
    threshold_values JSON,
    severity_mapping JSON,
    is_active BOOLEAN DEFAULT TRUE,
    version VARCHAR(20) DEFAULT '1.0',
    effective_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATETIME,
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rule_id (rule_id),
    INDEX idx_category (category),
    INDEX idx_regulatory_framework (regulatory_framework),
    INDEX idx_is_active (is_active)
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    log_id VARCHAR(50) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    user_id VARCHAR(100),
    user_role VARCHAR(50),
    system_component VARCHAR(100),
    ip_address VARCHAR(45),
    before_state JSON,
    after_state JSON,
    metadata JSON,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_log_id (log_id),
    INDEX idx_event_type (event_type),
    INDEX idx_entity_type (entity_type),
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    username VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    login_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    logout_timestamp DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    session_duration_minutes INT,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_login_timestamp (login_timestamp)
);

-- Insert sample compliance rules
INSERT INTO compliance_rules (
    rule_id, name, description, category, regulatory_framework, 
    standard_reference, requirement_id, rule_logic, threshold_values, 
    severity_mapping, created_by, approved_by
) VALUES 
(
    'APRA-TXN-LIMIT-001',
    'APRA Transaction Limit Rule',
    'Monitors transactions against APRA prescribed limits for reporting requirements',
    'TRANSACTION',
    'APRA',
    'CPS 234',
    'CPS234-TXN-001',
    '{"condition": "amount > threshold", "threshold_field": "limit_amount"}',
    '{"limit_amount": 10000.0, "currency": "AUD"}',
    '{"HIGH": "amount > limit_amount", "CRITICAL": "amount > limit_amount * 2"}',
    'system',
    'compliance.admin'
),
(
    'APRA-VELOCITY-001',
    'APRA Transaction Velocity Rule',
    'Monitors transaction velocity patterns for suspicious activity detection',
    'PATTERN',
    'APRA',
    'CPS 234',
    'CPS234-VEL-001',
    '{"condition": "velocity_check", "time_window": 3600, "max_transactions": 10, "max_amount": 50000}',
    '{"max_transactions_per_hour": 10, "max_amount_per_hour": 50000.0}',
    '{"HIGH": "count > max_transactions OR amount > max_amount", "CRITICAL": "count > max_transactions * 2"}',
    'system',
    'compliance.admin'
),
(
    'APRA-GEO-001',
    'APRA Geographic Risk Rule',
    'Monitors transactions from high-risk geographic locations',
    'GEOGRAPHIC',
    'APRA',
    'CPS 234',
    'CPS234-GEO-001',
    '{"condition": "country_risk_check", "high_risk_countries": ["IRN", "PRK", "SYR", "YEM", "AFG"]}',
    '{"high_risk_countries": ["IRN", "PRK", "SYR", "YEM", "AFG"]}',
    '{"CRITICAL": "country in high_risk_countries"}',
    'system',
    'compliance.admin'
);

-- Insert sample user
INSERT INTO users (
    user_id, username, email, full_name, hashed_password, 
    role, department, position, is_verified
) VALUES (
    'USER001',
    'compliance.officer',
    'compliance.officer@bank.com',
    'Compliance Officer',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5e', -- password: 'password123'
    'COMPLIANCE_OFFICER',
    'Risk & Compliance',
    'Senior Compliance Officer',
    TRUE
);

-- Create indexes for performance optimization
CREATE INDEX idx_transactions_composite ON transactions(account_id, transaction_timestamp, is_flagged);
CREATE INDEX idx_violations_composite ON compliance_violations(severity, status, detected_at);
CREATE INDEX idx_patterns_composite ON transaction_patterns(account_id, pattern_type, confidence_score);

-- Create views for common queries
CREATE VIEW active_violations AS
SELECT 
    v.*,
    t.account_id,
    t.amount as transaction_amount,
    t.transaction_timestamp
FROM compliance_violations v
LEFT JOIN transactions t ON v.transaction_id = t.id
WHERE v.status IN ('OPEN', 'INVESTIGATING');

CREATE VIEW high_risk_transactions AS
SELECT 
    t.*,
    CASE 
        WHEN t.amount > 10000 THEN 'HIGH_VALUE'
        WHEN t.location_country != 'AUS' THEN 'INTERNATIONAL'
        WHEN t.is_flagged = TRUE THEN 'FLAGGED'
        ELSE 'NORMAL'
    END as risk_category
FROM transactions t
WHERE t.amount > 10000 OR t.location_country != 'AUS' OR t.is_flagged = TRUE;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON compliance_db.* TO 'compliance'@'%';
FLUSH PRIVILEGES;
