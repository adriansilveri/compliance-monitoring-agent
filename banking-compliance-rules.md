# Banking Industry Compliance Rules Specification
## Comprehensive Regulatory Framework Implementation

---

## 1. Executive Summary

This document outlines the comprehensive set of banking compliance rules that can be incorporated into the compliance monitoring agent. The banking industry is one of the most heavily regulated sectors, with multiple overlapping regulatory frameworks that require continuous monitoring and enforcement.

## 2. Core Banking Regulatory Frameworks

### 2.1 Anti-Money Laundering (AML) Regulations

#### 2.1.1 Bank Secrecy Act (BSA) Rules
```yaml
aml_rules:
  currency_transaction_reports:
    - rule_id: "CTR-001"
      name: "Currency Transaction Report Threshold"
      description: "Report cash transactions over $10,000"
      condition: "cash_transaction_amount > 10000"
      action: "GENERATE_CTR"
      severity: "CRITICAL"
      regulatory_reference: "31 CFR 1020.320"
      
  suspicious_activity_reports:
    - rule_id: "SAR-001"
      name: "Suspicious Activity Detection"
      description: "Detect and report suspicious activities"
      conditions:
        - "transaction_amount > 5000 AND unusual_pattern = true"
        - "structuring_detected = true"
        - "known_criminal_association = true"
      action: "GENERATE_SAR"
      severity: "HIGH"
      timeframe: "30_days"
      regulatory_reference: "31 CFR 1020.320"
```

#### 2.1.2 Customer Due Diligence (CDD) Rules
```python
class CDDComplianceRules:
    def __init__(self):
        self.cdd_requirements = {
            'customer_identification': {
                'individual_customers': [
                    'full_legal_name',
                    'date_of_birth',
                    'residential_address',
                    'identification_number'
                ],
                'business_customers': [
                    'legal_name',
                    'business_address',
                    'tax_identification_number',
                    'beneficial_ownership_info'
                ]
            },
            'beneficial_ownership': {
                'threshold': 25,  # 25% ownership threshold
                'required_info': [
                    'name',
                    'date_of_birth',
                    'address',
                    'identification_number'
                ]
            }
        }
    
    def validate_cdd_compliance(self, customer_data):
        """
        Validate Customer Due Diligence compliance
        """
        violations = []
        
        # Check customer identification requirements
        if not self.validate_customer_identification(customer_data):
            violations.append({
                'rule_id': 'CDD-001',
                'violation': 'Incomplete customer identification',
                'severity': 'HIGH',
                'regulatory_reference': '31 CFR 1020.220'
            })
        
        # Check beneficial ownership for business customers
        if customer_data.get('customer_type') == 'business':
            if not self.validate_beneficial_ownership(customer_data):
                violations.append({
                    'rule_id': 'CDD-002',
                    'violation': 'Missing beneficial ownership information',
                    'severity': 'CRITICAL',
                    'regulatory_reference': '31 CFR 1010.230'
                })
        
        return violations
```

### 2.2 Know Your Customer (KYC) Regulations

#### 2.2.1 Customer Identification Program (CIP)
```yaml
kyc_rules:
  customer_identification_program:
    - rule_id: "CIP-001"
      name: "Customer Identity Verification"
      description: "Verify customer identity before account opening"
      requirements:
        - "government_issued_id_verified = true"
        - "address_verification_completed = true"
        - "identity_verification_method IN ['documentary', 'non_documentary']"
      action: "BLOCK_ACCOUNT_OPENING"
      severity: "CRITICAL"
      regulatory_reference: "31 CFR 1020.220"
      
    - rule_id: "CIP-002"
      name: "Enhanced Due Diligence for High-Risk Customers"
      description: "Additional verification for high-risk customers"
      conditions:
        - "customer_risk_rating = 'HIGH'"
        - "pep_status = true OR sanctions_list_match = true"
      requirements:
        - "source_of_funds_documented = true"
        - "enhanced_monitoring_enabled = true"
        - "senior_management_approval = true"
      action: "REQUIRE_EDD"
      severity: "HIGH"
```

#### 2.2.2 Ongoing Customer Monitoring
```python
class OngoingMonitoringRules:
    def __init__(self):
        self.monitoring_thresholds = {
            'transaction_velocity': {
                'low_risk': {'daily': 50000, 'monthly': 500000},
                'medium_risk': {'daily': 25000, 'monthly': 250000},
                'high_risk': {'daily': 10000, 'monthly': 100000}
            },
            'geographic_risk': {
                'high_risk_countries': [
                    'Afghanistan', 'Iran', 'North Korea', 'Syria'
                ],
                'sanctions_jurisdictions': [
                    'Cuba', 'Russia', 'Belarus'
                ]
            }
        }
    
    def monitor_customer_activity(self, customer_id, transactions):
        """
        Continuous monitoring of customer transactions
        """
        violations = []
        customer_profile = self.get_customer_profile(customer_id)
        risk_level = customer_profile.get('risk_rating', 'MEDIUM')
        
        # Check transaction velocity
        daily_volume = self.calculate_daily_volume(transactions)
        threshold = self.monitoring_thresholds['transaction_velocity'][risk_level.lower()]['daily']
        
        if daily_volume > threshold:
            violations.append({
                'rule_id': 'MON-001',
                'violation': f'Daily transaction volume exceeded: ${daily_volume} > ${threshold}',
                'severity': 'MEDIUM',
                'customer_id': customer_id,
                'recommended_action': 'REVIEW_CUSTOMER_PROFILE'
            })
        
        # Check geographic risk
        for transaction in transactions:
            if self.is_high_risk_jurisdiction(transaction.get('destination_country')):
                violations.append({
                    'rule_id': 'MON-002',
                    'violation': f'Transaction to high-risk jurisdiction: {transaction.get("destination_country")}',
                    'severity': 'HIGH',
                    'transaction_id': transaction.get('id'),
                    'recommended_action': 'ENHANCED_REVIEW'
                })
        
        return violations
```

### 2.3 Office of Foreign Assets Control (OFAC) Sanctions

#### 2.3.1 Sanctions Screening Rules
```yaml
ofac_sanctions_rules:
  sanctions_screening:
    - rule_id: "OFAC-001"
      name: "Real-time Sanctions Screening"
      description: "Screen all transactions against OFAC sanctions lists"
      screening_lists:
        - "SDN" # Specially Designated Nationals
        - "SSI" # Sectoral Sanctions Identifications
        - "FSE" # Foreign Sanctions Evaders
        - "NS-MBS" # Non-SDN Menu-Based Sanctions
      match_threshold: 95 # Percentage match threshold
      action: "BLOCK_TRANSACTION"
      severity: "CRITICAL"
      regulatory_reference: "31 CFR Chapter V"
      
    - rule_id: "OFAC-002"
      name: "50% Rule Compliance"
      description: "Block transactions with entities 50%+ owned by sanctioned parties"
      condition: "beneficial_ownership_sanctioned_percentage >= 50"
      action: "BLOCK_AND_REPORT"
      severity: "CRITICAL"
```

#### 2.3.2 Geographic Sanctions
```python
class GeographicSanctionsRules:
    def __init__(self):
        self.sanctioned_countries = {
            'comprehensive_sanctions': [
                'Cuba', 'Iran', 'North Korea', 'Syria', 'Russia', 'Belarus'
            ],
            'sectoral_sanctions': [
                'Russia', 'Ukraine'  # Specific sectors only
            ],
            'targeted_sanctions': [
                'Venezuela', 'Myanmar', 'Mali'
            ]
        }
        
        self.prohibited_activities = {
            'Cuba': ['all_transactions_except_authorized'],
            'Iran': ['all_transactions_except_humanitarian'],
            'North Korea': ['all_transactions'],
            'Syria': ['petroleum_transactions', 'luxury_goods'],
            'Russia': ['energy_sector', 'defense_sector', 'financial_sector']
        }
    
    def validate_geographic_compliance(self, transaction):
        """
        Validate transaction against geographic sanctions
        """
        violations = []
        destination_country = transaction.get('destination_country')
        transaction_type = transaction.get('type')
        
        # Check comprehensive sanctions
        if destination_country in self.sanctioned_countries['comprehensive_sanctions']:
            if not self.is_authorized_transaction(transaction):
                violations.append({
                    'rule_id': 'GEO-001',
                    'violation': f'Transaction to comprehensively sanctioned country: {destination_country}',
                    'severity': 'CRITICAL',
                    'action': 'BLOCK_TRANSACTION',
                    'regulatory_reference': 'OFAC Country Sanctions'
                })
        
        # Check sectoral sanctions
        if destination_country in self.sanctioned_countries['sectoral_sanctions']:
            prohibited_sectors = self.prohibited_activities.get(destination_country, [])
            if any(sector in transaction_type for sector in prohibited_sectors):
                violations.append({
                    'rule_id': 'GEO-002',
                    'violation': f'Sectoral sanctions violation: {transaction_type} to {destination_country}',
                    'severity': 'HIGH',
                    'action': 'BLOCK_TRANSACTION'
                })
        
        return violations
```

### 2.4 Fair Credit Reporting Act (FCRA) Compliance

#### 2.4.1 Credit Reporting Rules
```yaml
fcra_rules:
  credit_reporting:
    - rule_id: "FCRA-001"
      name: "Permissible Purpose Verification"
      description: "Verify permissible purpose before accessing credit reports"
      conditions:
        - "credit_report_request = true"
        - "permissible_purpose IN ['credit_application', 'account_review', 'collection']"
      action: "VERIFY_PURPOSE"
      severity: "HIGH"
      regulatory_reference: "15 USC 1681b"
      
    - rule_id: "FCRA-002"
      name: "Adverse Action Notice Requirement"
      description: "Send adverse action notice when credit decision is negative"
      conditions:
        - "credit_decision = 'DENIED' OR credit_terms_less_favorable = true"
        - "credit_report_used = true"
      required_actions:
        - "send_adverse_action_notice"
        - "provide_credit_score_disclosure"
        - "include_credit_reporting_agency_contact"
      timeframe: "30_days"
      severity: "MEDIUM"
```

### 2.5 Equal Credit Opportunity Act (ECOA) Compliance

#### 2.5.1 Fair Lending Rules
```python
class FairLendingRules:
    def __init__(self):
        self.protected_classes = [
            'race', 'color', 'religion', 'national_origin',
            'sex', 'marital_status', 'age', 'receipt_of_public_assistance'
        ]
        
        self.prohibited_practices = [
            'disparate_treatment',
            'disparate_impact',
            'redlining',
            'steering'
        ]
    
    def validate_fair_lending_compliance(self, loan_application, decision):
        """
        Validate fair lending compliance
        """
        violations = []
        
        # Check for prohibited basis in decision factors
        decision_factors = decision.get('factors_considered', [])
        for factor in decision_factors:
            if any(protected_class in factor.lower() for protected_class in self.protected_classes):
                violations.append({
                    'rule_id': 'ECOA-001',
                    'violation': f'Prohibited basis used in credit decision: {factor}',
                    'severity': 'CRITICAL',
                    'regulatory_reference': '15 USC 1691',
                    'recommended_action': 'REVIEW_DECISION_PROCESS'
                })
        
        # Check adverse action notice requirements
        if decision.get('status') in ['DENIED', 'COUNTEROFFER']:
            if not decision.get('adverse_action_notice_sent'):
                violations.append({
                    'rule_id': 'ECOA-002',
                    'violation': 'Adverse action notice not sent within required timeframe',
                    'severity': 'HIGH',
                    'timeframe_violation': True
                })
        
        return violations
```

## 3. Transaction Monitoring Rules

### 3.1 Wire Transfer Regulations

#### 3.1.1 Funds Transfer Recordkeeping Rule
```yaml
wire_transfer_rules:
  domestic_wire_transfers:
    - rule_id: "WIRE-001"
      name: "Domestic Wire Transfer Information Requirements"
      description: "Collect required information for domestic wires $3,000+"
      conditions:
        - "transfer_amount >= 3000"
        - "transfer_type = 'domestic_wire'"
      required_information:
        - "originator_name"
        - "originator_address"
        - "originator_account_number"
        - "beneficiary_name"
        - "beneficiary_account_number"
        - "beneficiary_financial_institution"
      action: "VALIDATE_INFORMATION"
      severity: "HIGH"
      
  international_wire_transfers:
    - rule_id: "WIRE-002"
      name: "International Wire Transfer Requirements"
      description: "Enhanced requirements for international wires $1,000+"
      conditions:
        - "transfer_amount >= 1000"
        - "transfer_type = 'international_wire'"
      required_information:
        - "originator_name"
        - "originator_address"
        - "originator_account_number"
        - "originator_financial_institution"
        - "beneficiary_name"
        - "beneficiary_address"
        - "beneficiary_account_number"
        - "beneficiary_financial_institution"
        - "purpose_of_payment"
      additional_screening:
        - "ofac_sanctions_check"
        - "correspondent_bank_verification"
      action: "ENHANCED_VALIDATION"
      severity: "CRITICAL"
```

### 3.2 Large Cash Transaction Monitoring

#### 3.2.1 Currency Transaction Reports (CTR)
```python
class CashTransactionMonitoring:
    def __init__(self):
        self.ctr_threshold = 10000
        self.structuring_detection_window = 24  # hours
        self.structuring_threshold = 0.8  # 80% of CTR threshold
    
    def monitor_cash_transactions(self, transactions, customer_id):
        """
        Monitor cash transactions for CTR and structuring
        """
        violations = []
        
        # Check individual transactions for CTR threshold
        for transaction in transactions:
            if transaction.get('type') == 'cash' and transaction.get('amount') >= self.ctr_threshold:
                violations.append({
                    'rule_id': 'CTR-001',
                    'violation': f'Cash transaction over $10,000 requires CTR filing',
                    'transaction_id': transaction.get('id'),
                    'amount': transaction.get('amount'),
                    'severity': 'CRITICAL',
                    'required_action': 'FILE_CTR',
                    'deadline': '15_days'
                })
        
        # Check for structuring (multiple transactions just under threshold)
        cash_transactions_24h = self.get_cash_transactions_in_window(
            transactions, self.structuring_detection_window
        )
        
        total_amount = sum(t.get('amount', 0) for t in cash_transactions_24h)
        if (len(cash_transactions_24h) > 1 and 
            total_amount >= self.ctr_threshold and
            all(t.get('amount') < self.ctr_threshold * self.structuring_threshold 
                for t in cash_transactions_24h)):
            
            violations.append({
                'rule_id': 'STR-001',
                'violation': 'Potential structuring detected',
                'customer_id': customer_id,
                'total_amount': total_amount,
                'transaction_count': len(cash_transactions_24h),
                'severity': 'HIGH',
                'required_action': 'INVESTIGATE_STRUCTURING'
            })
        
        return violations
```

## 4. Capital and Liquidity Requirements

### 4.1 Basel III Capital Requirements

#### 4.1.1 Capital Adequacy Rules
```yaml
capital_requirements:
  basel_iii_ratios:
    - rule_id: "CAP-001"
      name: "Common Equity Tier 1 Capital Ratio"
      description: "Maintain minimum CET1 capital ratio"
      minimum_ratio: 4.5  # 4.5% minimum
      calculation: "common_equity_tier1_capital / risk_weighted_assets"
      action: "CAPITAL_ALERT"
      severity: "CRITICAL"
      regulatory_reference: "Basel III Framework"
      
    - rule_id: "CAP-002"
      name: "Tier 1 Capital Ratio"
      description: "Maintain minimum Tier 1 capital ratio"
      minimum_ratio: 6.0  # 6% minimum
      calculation: "tier1_capital / risk_weighted_assets"
      action: "REGULATORY_NOTIFICATION"
      severity: "HIGH"
      
    - rule_id: "CAP-003"
      name: "Total Capital Ratio"
      description: "Maintain minimum total capital ratio"
      minimum_ratio: 8.0  # 8% minimum
      calculation: "total_capital / risk_weighted_assets"
      action: "CORRECTIVE_ACTION_PLAN"
      severity: "HIGH"
```

### 4.2 Liquidity Coverage Ratio (LCR)

#### 4.2.1 Liquidity Requirements
```python
class LiquidityMonitoring:
    def __init__(self):
        self.lcr_minimum = 100  # 100% minimum LCR
        self.nsfr_minimum = 100  # 100% minimum NSFR
    
    def monitor_liquidity_ratios(self, bank_data):
        """
        Monitor liquidity coverage and net stable funding ratios
        """
        violations = []
        
        # Calculate Liquidity Coverage Ratio
        hqla = bank_data.get('high_quality_liquid_assets', 0)
        net_cash_outflows = bank_data.get('net_cash_outflows_30_days', 0)
        
        if net_cash_outflows > 0:
            lcr = (hqla / net_cash_outflows) * 100
            
            if lcr < self.lcr_minimum:
                violations.append({
                    'rule_id': 'LIQ-001',
                    'violation': f'Liquidity Coverage Ratio below minimum: {lcr:.2f}% < {self.lcr_minimum}%',
                    'current_ratio': lcr,
                    'minimum_required': self.lcr_minimum,
                    'severity': 'CRITICAL',
                    'regulatory_reference': 'Basel III LCR',
                    'required_action': 'INCREASE_LIQUID_ASSETS'
                })
        
        # Calculate Net Stable Funding Ratio
        available_stable_funding = bank_data.get('available_stable_funding', 0)
        required_stable_funding = bank_data.get('required_stable_funding', 0)
        
        if required_stable_funding > 0:
            nsfr = (available_stable_funding / required_stable_funding) * 100
            
            if nsfr < self.nsfr_minimum:
                violations.append({
                    'rule_id': 'LIQ-002',
                    'violation': f'Net Stable Funding Ratio below minimum: {nsfr:.2f}% < {self.nsfr_minimum}%',
                    'current_ratio': nsfr,
                    'minimum_required': self.nsfr_minimum,
                    'severity': 'HIGH',
                    'regulatory_reference': 'Basel III NSFR'
                })
        
        return violations
```

---

This is Part 1 of the banking compliance rules specification. Would you like me to continue with Part 2, which will cover additional regulatory frameworks including:

- Consumer protection regulations (TILA, RESPA, etc.)
- Privacy and data protection (GLBA, CCPA)
- Operational risk management
- Market conduct rules
- Stress testing requirements
- And more specific implementation examples?
