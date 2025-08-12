Feature: APRA Compliance Monitoring
  As a compliance officer
  I want to monitor transactions for APRA compliance violations
  So that I can ensure regulatory compliance and prevent violations

  Background:
    Given the compliance monitoring system is running
    And APRA compliance rules are active

  Scenario: Transaction exceeds APRA limit threshold
    Given a transaction with amount $15000
    And the APRA transaction limit is $10000
    When the transaction is processed
    Then a compliance violation should be detected
    And the violation type should be "TRANSACTION_LIMIT"
    And the violation severity should be "HIGH"
    And the violation should reference "CPS 234"

  Scenario: High velocity transaction pattern detected
    Given an account "ACC123456"
    And 12 transactions within 1 hour for the account
    And the velocity limit is 10 transactions per hour
    When the transactions are processed
    Then a compliance violation should be detected
    And the violation type should be "SUSPICIOUS_PATTERN"
    And the violation severity should be "HIGH"
    And the pattern type should be "VELOCITY"

  Scenario: Transaction from high-risk country
    Given a transaction from country "IRN"
    And "IRN" is in the high-risk countries list
    When the transaction is processed
    Then a compliance violation should be detected
    And the violation type should be "SUSPICIOUS_PATTERN"
    And the violation severity should be "CRITICAL"
    And the violation should require enhanced due diligence

  Scenario: Multiple transactions near reporting threshold (Structuring)
    Given an account "ACC789012"
    And 4 transactions with amounts $9500, $9800, $9200, $9900
    And the reporting threshold is $10000
    When the transactions are processed
    Then a suspicious pattern should be detected
    And the pattern type should be "AMOUNT"
    And the pattern should indicate potential structuring

  Scenario: Transactions outside business hours
    Given an account "ACC345678"
    And 5 transactions between 11 PM and 5 AM
    When the transactions are processed
    Then a suspicious pattern should be detected
    And the pattern type should be "TEMPORAL"
    And the pattern should indicate unusual timing

  Scenario: Compliance violation resolution
    Given a compliance violation exists with ID "VIO123"
    And the violation status is "OPEN"
    When the violation is resolved by "compliance.officer@bank.com"
    And resolution notes are "Customer verified via phone call"
    Then the violation status should be "RESOLVED"
    And the resolved_at timestamp should be set
    And the resolution should be logged in audit trail

  Scenario: Failed compliance check - Invalid transaction data
    Given a transaction with missing required field "account_id"
    When the transaction is processed
    Then a data quality violation should be raised
    And the transaction should be rejected
    And the error should specify the missing field

  Scenario: Failed compliance check - Invalid currency format
    Given a transaction with currency "INVALID"
    When the transaction is processed
    Then a data quality violation should be raised
    And the error should specify "Currency must be a 3-letter ISO code"

  Scenario: Failed compliance check - Negative transaction amount
    Given a transaction with amount -1000
    When the transaction is processed
    Then a data quality violation should be raised
    And the error should specify "Transaction amount must be a positive number"

  Scenario: Compliance dashboard metrics
    Given 5 critical violations exist
    And 10 high violations exist
    And 3 violations are overdue
    When the compliance dashboard is requested
    Then the dashboard should show 5 critical violations
    And the dashboard should show 10 high violations
    And the dashboard should show 3 overdue violations
    And the compliance score should be calculated correctly

  Scenario: APRA reporting requirements
    Given a high-value transaction over $10000
    And the transaction is international
    When the transaction is processed
    Then the transaction should be marked for reporting
    And AUSTRAC reporting should be triggered
    And the transaction should require enhanced monitoring
