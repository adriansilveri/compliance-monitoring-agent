# Banking Compliance Rules - Part 2
## Consumer Protection and Operational Regulations

---

## 5. Consumer Protection Regulations

### 5.1 Truth in Lending Act (TILA) Compliance

#### 5.1.1 APR Disclosure Requirements
```yaml
tila_rules:
  apr_disclosure:
    - rule_id: "TILA-001"
      name: "Annual Percentage Rate Disclosure"
      description: "Accurate APR calculation and disclosure for credit products"
      applicable_products: ["credit_cards", "personal_loans", "mortgages", "auto_loans"]
      requirements:
        - "apr_calculated_using_regulation_z_method = true"
        - "apr_disclosed_prominently = true"
        - "apr_accuracy_tolerance <= 0.125"  # 1/8 of 1% tolerance
      action: "VALIDATE_APR_DISCLOSURE"
      severity: "HIGH"
      regulatory_reference: "12 CFR 1026"
      
    - rule_id: "TILA-002"
      name: "Credit Card CARD Act Compliance"
      description: "Credit card specific TILA requirements"
      conditions:
        - "product_type = 'credit_card'"
      requirements:
        - "21_day_payment_period = true"
        - "rate_increase_45_day_notice = true"
        - "overlimit_fee_opt_in = true"
        - "minimum_payment_warning = true"
      action: "VALIDATE_CARD_ACT_COMPLIANCE"
      severity: "CRITICAL"
```

#### 5.1.2 Right of Rescission Rules
```python
class TILARescissionRules:
    def __init__(self):
        self.rescission_period_days = 3
        self.applicable_transactions = [
            'home_equity_loan',
            'home_equity_line_of_credit',
            'refinance_not_same_creditor'
        ]
    
    def validate_rescission_rights(self, loan_application):
        """
        Validate right of rescission compliance
        """
        violations = []
        loan_type = loan_application.get('loan_type')
        property_type = loan_application.get('property_type')
        
        # Check if rescission rights apply
        if (loan_type in self.applicable_transactions and 
            property_type == 'primary_residence'):
            
            rescission_notice_provided = loan_application.get('rescission_notice_provided')
            if not rescission_notice_provided:
                violations.append({
                    'rule_id': 'TILA-003',
                    'violation': 'Right of rescission notice not provided',
                    'loan_id': loan_application.get('id'),
                    'severity': 'CRITICAL',
                    'regulatory_reference': '12 CFR 1026.23',
                    'required_action': 'PROVIDE_RESCISSION_NOTICE'
                })
            
            # Check rescission period compliance
            funding_date = loan_application.get('funding_date')
            if funding_date and not self.is_rescission_period_expired(funding_date):
                if loan_application.get('funds_disbursed'):
                    violations.append({
                        'rule_id': 'TILA-004',
                        'violation': 'Funds disbursed before rescission period expired',
                        'loan_id': loan_application.get('id'),
                        'severity': 'CRITICAL',
                        'rescission_period_remaining': self.get_remaining_rescission_days(funding_date)
                    })
        
        return violations
```

### 5.2 Real Estate Settlement Procedures Act (RESPA)

#### 5.2.1 Mortgage Disclosure Requirements
```yaml
respa_rules:
  mortgage_disclosures:
    - rule_id: "RESPA-001"
      name: "Loan Estimate Timing"
      description: "Provide Loan Estimate within 3 business days"
      conditions:
        - "loan_type IN ['mortgage', 'home_equity']"
        - "application_received = true"
      timing_requirement: "3_business_days"
      action: "GENERATE_LOAN_ESTIMATE"
      severity: "HIGH"
      regulatory_reference: "12 CFR 1026.19(e)"
      
    - rule_id: "RESPA-002"
      name: "Closing Disclosure Timing"
      description: "Provide Closing Disclosure 3 business days before closing"
      conditions:
        - "loan_approved = true"
        - "closing_scheduled = true"
      timing_requirement: "3_business_days_before_closing"
      action: "GENERATE_CLOSING_DISCLOSURE"
      severity: "CRITICAL"
      
    - rule_id: "RESPA-003"
      name: "Affiliated Business Arrangement Disclosure"
      description: "Disclose affiliated business arrangements"
      conditions:
        - "referral_to_affiliated_business = true"
      requirements:
        - "aba_disclosure_provided = true"
        - "customer_not_required_to_use_affiliate = true"
      action: "VALIDATE_ABA_DISCLOSURE"
      severity: "MEDIUM"
```

### 5.3 Fair Debt Collection Practices Act (FDCPA)

#### 5.3.1 Debt Collection Communication Rules
```python
class FDCPAComplianceRules:
    def __init__(self):
        self.prohibited_contact_times = {
            'before': '08:00',  # 8 AM local time
            'after': '21:00'    # 9 PM local time
        }
        self.prohibited_contact_locations = [
            'workplace_if_prohibited',
            'inconvenient_places'
        ]
        self.validation_period_days = 30
    
    def validate_collection_communication(self, communication_attempt):
        """
        Validate debt collection communication compliance
        """
        violations = []
        
        # Check communication timing
        contact_time = communication_attempt.get('contact_time')
        debtor_timezone = communication_attempt.get('debtor_timezone')
        
        if not self.is_appropriate_contact_time(contact_time, debtor_timezone):
            violations.append({
                'rule_id': 'FDCPA-001',
                'violation': f'Contact attempted outside permitted hours: {contact_time}',
                'severity': 'MEDIUM',
                'regulatory_reference': '15 USC 1692c(a)(1)',
                'debtor_id': communication_attempt.get('debtor_id')
            })
        
        # Check validation notice requirement
        if communication_attempt.get('initial_communication'):
            validation_notice_sent = communication_attempt.get('validation_notice_sent')
            if not validation_notice_sent:
                violations.append({
                    'rule_id': 'FDCPA-002',
                    'violation': 'Validation notice not sent within 5 days of initial communication',
                    'severity': 'HIGH',
                    'regulatory_reference': '15 USC 1692g(a)'
                })
        
        # Check for prohibited practices
        communication_content = communication_attempt.get('content', '')
        if self.contains_prohibited_language(communication_content):
            violations.append({
                'rule_id': 'FDCPA-003',
                'violation': 'Communication contains prohibited language or threats',
                'severity': 'CRITICAL',
                'regulatory_reference': '15 USC 1692d, 1692e, 1692f'
            })
        
        return violations
```

## 6. Privacy and Data Protection Regulations

### 6.1 Gramm-Leach-Bliley Act (GLBA) Privacy Rules

#### 6.1.1 Privacy Notice Requirements
```yaml
glba_privacy_rules:
  privacy_notices:
    - rule_id: "GLBA-001"
      name: "Initial Privacy Notice"
      description: "Provide privacy notice before sharing nonpublic personal information"
      trigger: "customer_relationship_establishment"
      timing: "before_sharing_npi"
      required_content:
        - "categories_of_npi_collected"
        - "categories_of_npi_disclosed"
        - "categories_of_affiliates_recipients"
        - "opt_out_rights_explanation"
        - "security_measures_description"
      action: "PROVIDE_PRIVACY_NOTICE"
      severity: "HIGH"
      
    - rule_id: "GLBA-002"
      name: "Annual Privacy Notice"
      description: "Provide annual privacy notice to customers"
      frequency: "annual"
      conditions:
        - "customer_relationship_continues = true"
        - "privacy_practices_unchanged = false OR annual_notice_required = true"
      action: "SEND_ANNUAL_PRIVACY_NOTICE"
      severity: "MEDIUM"
```

#### 6.1.2 Opt-Out Rights Implementation
```python
class GLBAOptOutRules:
    def __init__(self):
        self.opt_out_period_days = 30
        self.reasonable_opt_out_methods = [
            'toll_free_phone',
            'opt_out_form',
            'electronic_means'
        ]
    
    def validate_opt_out_compliance(self, customer_data, sharing_request):
        """
        Validate opt-out rights compliance
        """
        violations = []
        customer_id = customer_data.get('customer_id')
        
        # Check if customer has opted out
        opt_out_status = customer_data.get('opt_out_status')
        if opt_out_status == 'opted_out':
            sharing_category = sharing_request.get('sharing_category')
            
            # Check if sharing is permitted despite opt-out
            if not self.is_sharing_permitted_despite_opt_out(sharing_category):
                violations.append({
                    'rule_id': 'GLBA-003',
                    'violation': f'Attempted to share NPI after customer opt-out: {sharing_category}',
                    'customer_id': customer_id,
                    'severity': 'CRITICAL',
                    'regulatory_reference': '12 CFR 1016.10'
                })
        
        # Check opt-out notice adequacy
        if sharing_request.get('requires_opt_out_notice'):
            opt_out_notice = customer_data.get('opt_out_notice_provided')
            if not opt_out_notice or not self.is_adequate_opt_out_notice(opt_out_notice):
                violations.append({
                    'rule_id': 'GLBA-004',
                    'violation': 'Inadequate opt-out notice provided',
                    'customer_id': customer_id,
                    'severity': 'HIGH'
                })
        
        return violations
```

### 6.2 California Consumer Privacy Act (CCPA) Compliance

#### 6.2.1 Consumer Rights Implementation
```yaml
ccpa_rules:
  consumer_rights:
    - rule_id: "CCPA-001"
      name: "Right to Know"
      description: "Provide information about personal information collection and use"
      consumer_request_types: ["categories_collected", "sources", "business_purposes", "third_parties"]
      response_timeframe: "45_days"
      extension_allowed: "45_additional_days"
      action: "PROVIDE_INFORMATION_DISCLOSURE"
      severity: "HIGH"
      
    - rule_id: "CCPA-002"
      name: "Right to Delete"
      description: "Delete personal information upon consumer request"
      exceptions:
        - "complete_transaction"
        - "detect_security_incidents"
        - "comply_with_legal_obligation"
        - "exercise_free_speech"
        - "engage_in_research"
      response_timeframe: "45_days"
      action: "DELETE_PERSONAL_INFORMATION"
      severity: "HIGH"
      
    - rule_id: "CCPA-003"
      name: "Right to Opt-Out of Sale"
      description: "Honor consumer requests to opt-out of personal information sale"
      implementation_requirements:
        - "do_not_sell_link_on_homepage = true"
        - "opt_out_process_simple = true"
        - "no_opt_out_fee = true"
      action: "STOP_SELLING_PERSONAL_INFO"
      severity: "CRITICAL"
```

## 7. Operational Risk Management

### 7.1 Vendor Management and Third-Party Risk

#### 7.1.1 Third-Party Risk Assessment Rules
```python
class ThirdPartyRiskRules:
    def __init__(self):
        self.risk_categories = {
            'critical': ['core_banking', 'payment_processing', 'cybersecurity'],
            'high': ['customer_data_processing', 'compliance_services'],
            'medium': ['marketing_services', 'facilities_management'],
            'low': ['office_supplies', 'non_critical_services']
        }
        
        self.due_diligence_requirements = {
            'critical': [
                'financial_stability_assessment',
                'cybersecurity_assessment',
                'business_continuity_plan_review',
                'regulatory_compliance_validation',
                'on_site_inspection',
                'continuous_monitoring'
            ],
            'high': [
                'financial_stability_assessment',
                'cybersecurity_assessment',
                'regulatory_compliance_validation',
                'periodic_review'
            ]
        }
    
    def assess_third_party_risk(self, vendor_data):
        """
        Assess third-party vendor risk and compliance requirements
        """
        violations = []
        vendor_id = vendor_data.get('vendor_id')
        service_category = vendor_data.get('service_category')
        
        # Determine risk level
        risk_level = self.determine_risk_level(service_category)
        required_due_diligence = self.due_diligence_requirements.get(risk_level, [])
        
        # Check due diligence completion
        completed_assessments = vendor_data.get('completed_assessments', [])
        missing_assessments = set(required_due_diligence) - set(completed_assessments)
        
        if missing_assessments:
            violations.append({
                'rule_id': 'TPR-001',
                'violation': f'Incomplete due diligence for {risk_level} risk vendor',
                'vendor_id': vendor_id,
                'missing_assessments': list(missing_assessments),
                'severity': 'HIGH' if risk_level in ['critical', 'high'] else 'MEDIUM',
                'required_action': 'COMPLETE_DUE_DILIGENCE'
            })
        
        # Check contract compliance
        contract_terms = vendor_data.get('contract_terms', {})
        if risk_level in ['critical', 'high']:
            required_contract_terms = [
                'data_protection_clause',
                'right_to_audit',
                'business_continuity_requirements',
                'regulatory_compliance_clause',
                'termination_rights'
            ]
            
            missing_terms = [term for term in required_contract_terms 
                           if not contract_terms.get(term)]
            
            if missing_terms:
                violations.append({
                    'rule_id': 'TPR-002',
                    'violation': 'Contract missing required terms for high-risk vendor',
                    'vendor_id': vendor_id,
                    'missing_terms': missing_terms,
                    'severity': 'HIGH'
                })
        
        return violations
```

### 7.2 Cybersecurity and Information Security

#### 7.2.1 Data Security Requirements
```yaml
cybersecurity_rules:
  data_protection:
    - rule_id: "CYBER-001"
      name: "Encryption at Rest"
      description: "Encrypt sensitive data stored in databases and files"
      applicable_data_types: ["customer_pii", "account_numbers", "ssn", "payment_card_data"]
      encryption_standard: "AES-256"
      key_management: "FIPS_140-2_Level_3"
      action: "VALIDATE_ENCRYPTION"
      severity: "CRITICAL"
      
    - rule_id: "CYBER-002"
      name: "Encryption in Transit"
      description: "Encrypt data transmitted over networks"
      minimum_tls_version: "1.2"
      preferred_tls_version: "1.3"
      certificate_requirements: "valid_ca_signed"
      action: "VALIDATE_TRANSMISSION_SECURITY"
      severity: "CRITICAL"
      
    - rule_id: "CYBER-003"
      name: "Access Control Validation"
      description: "Implement proper access controls for sensitive systems"
      requirements:
        - "multi_factor_authentication = true"
        - "principle_of_least_privilege = true"
        - "regular_access_review = true"
        - "privileged_access_monitoring = true"
      action: "VALIDATE_ACCESS_CONTROLS"
      severity: "HIGH"
```

#### 7.2.2 Incident Response Requirements
```python
class CybersecurityIncidentRules:
    def __init__(self):
        self.incident_severity_levels = {
            'critical': {
                'notification_timeframe_hours': 1,
                'regulatory_notification_hours': 24,
                'customer_notification_required': True
            },
            'high': {
                'notification_timeframe_hours': 4,
                'regulatory_notification_hours': 72,
                'customer_notification_required': False
            },
            'medium': {
                'notification_timeframe_hours': 24,
                'regulatory_notification_hours': None,
                'customer_notification_required': False
            }
        }
    
    def validate_incident_response(self, incident_data):
        """
        Validate cybersecurity incident response compliance
        """
        violations = []
        incident_id = incident_data.get('incident_id')
        severity = incident_data.get('severity')
        detection_time = incident_data.get('detection_time')
        
        # Check notification timeframes
        severity_requirements = self.incident_severity_levels.get(severity, {})
        
        # Internal notification check
        internal_notification_time = incident_data.get('internal_notification_time')
        if internal_notification_time:
            notification_delay = self.calculate_hours_difference(
                detection_time, internal_notification_time
            )
            max_delay = severity_requirements.get('notification_timeframe_hours')
            
            if max_delay and notification_delay > max_delay:
                violations.append({
                    'rule_id': 'CYBER-004',
                    'violation': f'Internal notification exceeded timeframe: {notification_delay}h > {max_delay}h',
                    'incident_id': incident_id,
                    'severity': 'HIGH',
                    'actual_delay_hours': notification_delay,
                    'required_timeframe_hours': max_delay
                })
        
        # Regulatory notification check
        regulatory_notification_hours = severity_requirements.get('regulatory_notification_hours')
        if regulatory_notification_hours:
            regulatory_notification_time = incident_data.get('regulatory_notification_time')
            if not regulatory_notification_time:
                violations.append({
                    'rule_id': 'CYBER-005',
                    'violation': f'Regulatory notification required within {regulatory_notification_hours} hours',
                    'incident_id': incident_id,
                    'severity': 'CRITICAL',
                    'required_action': 'NOTIFY_REGULATORS'
                })
        
        # Customer notification check
        if severity_requirements.get('customer_notification_required'):
            customer_notification_sent = incident_data.get('customer_notification_sent')
            if not customer_notification_sent:
                violations.append({
                    'rule_id': 'CYBER-006',
                    'violation': 'Customer notification required for critical security incident',
                    'incident_id': incident_id,
                    'severity': 'HIGH',
                    'required_action': 'NOTIFY_CUSTOMERS'
                })
        
        return violations
```

## 8. Market Conduct and Sales Practices

### 8.1 Unfair, Deceptive, or Abusive Acts or Practices (UDAAP)

#### 8.1.1 Sales Practice Monitoring
```yaml
udaap_rules:
  sales_practices:
    - rule_id: "UDAAP-001"
      name: "Product Suitability Assessment"
      description: "Ensure products are suitable for customer needs and circumstances"
      applicable_products: ["credit_cards", "loans", "investment_products"]
      requirements:
        - "customer_needs_assessment_completed = true"
        - "product_features_explained = true"
        - "risks_disclosed = true"
        - "alternatives_discussed = true"
      action: "VALIDATE_SUITABILITY"
      severity: "HIGH"
      
    - rule_id: "UDAAP-002"
      name: "Clear and Conspicuous Disclosures"
      description: "Ensure all material terms are clearly disclosed"
      disclosure_requirements:
        - "font_size >= 10_point"
        - "contrasting_color = true"
        - "plain_language = true"
        - "prominent_placement = true"
      action: "VALIDATE_DISCLOSURES"
      severity: "MEDIUM"
      
    - rule_id: "UDAAP-003"
      name: "Prohibition of Deceptive Practices"
      description: "Prevent misleading or deceptive marketing and sales practices"
      prohibited_practices:
        - "false_or_misleading_statements"
        - "material_omissions"
        - "bait_and_switch_tactics"
        - "hidden_fees_or_charges"
      action: "MONITOR_SALES_PRACTICES"
      severity: "CRITICAL"
```

### 8.2 Community Reinvestment Act (CRA) Compliance

#### 8.2.1 Community Investment Monitoring
```python
class CRAComplianceRules:
    def __init__(self):
        self.assessment_areas = {}  # Bank's defined assessment areas
        self.income_categories = {
            'low_income': {'max_percent_ami': 50},
            'moderate_income': {'min_percent_ami': 50, 'max_percent_ami': 80},
            'middle_income': {'min_percent_ami': 80, 'max_percent_ami': 120},
            'upper_income': {'min_percent_ami': 120}
        }
    
    def monitor_cra_performance(self, lending_data, investment_data, service_data):
        """
        Monitor Community Reinvestment Act performance
        """
        violations = []
        
        # Analyze lending performance
        lending_analysis = self.analyze_lending_performance(lending_data)
        if lending_analysis.get('lmi_lending_ratio') < 0.12:  # Example threshold
            violations.append({
                'rule_id': 'CRA-001',
                'violation': 'Low- and moderate-income lending below expected levels',
                'current_ratio': lending_analysis.get('lmi_lending_ratio'),
                'severity': 'MEDIUM',
                'recommended_action': 'INCREASE_LMI_LENDING'
            })
        
        # Check for lending discrimination patterns
        if lending_analysis.get('potential_redlining_detected'):
            violations.append({
                'rule_id': 'CRA-002',
                'violation': 'Potential redlining pattern detected in lending',
                'affected_areas': lending_analysis.get('underserved_areas'),
                'severity': 'HIGH',
                'regulatory_reference': 'CRA and Fair Housing Act'
            })
        
        # Validate community development activities
        cd_investments = investment_data.get('community_development_investments', 0)
        total_assets = investment_data.get('total_assets', 1)
        cd_ratio = cd_investments / total_assets
        
        if cd_ratio < 0.01:  # Example threshold of 1%
            violations.append({
                'rule_id': 'CRA-003',
                'violation': 'Community development investments below expected levels',
                'current_ratio': cd_ratio,
                'severity': 'MEDIUM',
                'recommended_action': 'INCREASE_CD_INVESTMENTS'
            })
        
        return violations
```

## 9. Implementation Framework

### 9.1 Rule Engine Configuration
```python
class BankingComplianceRuleEngine:
    def __init__(self):
        self.rule_categories = {
            'aml_kyc': ['BSA', 'CDD', 'SAR', 'CTR'],
            'consumer_protection': ['TILA', 'RESPA', 'FDCPA', 'UDAAP'],
            'privacy_data': ['GLBA', 'CCPA', 'GDPR'],
            'capital_liquidity': ['Basel_III', 'LCR', 'NSFR'],
            'operational_risk': ['Third_Party', 'Cybersecurity', 'BCP'],
            'market_conduct': ['CRA', 'Fair_Lending', 'Sales_Practices']
        }
        
        self.severity_escalation = {
            'LOW': {'notification': 'email', 'timeframe': '24_hours'},
            'MEDIUM': {'notification': 'email_sms', 'timeframe': '4_hours'},
            'HIGH': {'notification': 'email_sms_call', 'timeframe': '1_hour'},
            'CRITICAL': {'notification': 'immediate_alert', 'timeframe': '15_minutes'}
        }
    
    def process_compliance_check(self, transaction_data, customer_data, context):
        """
        Process comprehensive compliance check across all banking regulations
        """
        all_violations = []
        
        # AML/KYC Checks
        aml_violations = self.check_aml_compliance(transaction_data, customer_data)
        all_violations.extend(aml_violations)
        
        # Consumer Protection Checks
        consumer_violations = self.check_consumer_protection(transaction_data, customer_data)
        all_violations.extend(consumer_violations)
        
        # Privacy and Data Protection
        privacy_violations = self.check_privacy_compliance(customer_data, context)
        all_violations.extend(privacy_violations)
        
        # Operational Risk Checks
        operational_violations = self.check_operational_risk(transaction_data, context)
        all_violations.extend(operational_violations)
        
        # Process violations and trigger appropriate responses
        for violation in all_violations:
            self.process_violation(violation)
        
        return {
            'total_violations': len(all_violations),
            'violations_by_severity': self.group_by_severity(all_violations),
            'immediate_actions_required': self.get_immediate_actions(all_violations),
            'compliance_score': self.calculate_compliance_score(all_violations)
        }
```

### 9.2 Real-Time Monitoring Integration
```python
class RealTimeBankingMonitor:
    def __init__(self):
        self.monitoring_streams = {
            'transactions': 'kafka://transactions-topic',
            'customer_updates': 'kafka://customer-updates-topic',
            'market_data': 'kafka://market-data-topic',
            'regulatory_updates': 'kafka://regulatory-updates-topic'
        }
    
    async def monitor_banking_compliance(self):
        """
        Real-time monitoring of banking compliance across all regulatory frameworks
        """
        while True:
            # Process transaction stream
            async for transaction in self.get_transaction_stream():
                compliance_result = await self.check_transaction_compliance(transaction)
                
                if compliance_result.get('violations'):
                    await self.handle_compliance_violations(
                        transaction, compliance_result['violations']
                    )
                
                # Update real-time compliance dashboard
                await self.update_compliance_metrics(compliance_result)
            
            await asyncio.sleep(0.1)  # 100ms processing cycle
```

---

This completes the comprehensive banking compliance rules specification. The system now covers:

✅ **Anti-Money Laundering (AML)** - BSA, SAR, CTR requirements  
✅ **Know Your Customer (KYC)** - CIP, CDD, ongoing monitoring  
✅ **OFAC Sanctions** - Real-time screening, geographic restrictions  
✅ **Consumer Protection** - TILA, RESPA, FDCPA compliance  
✅ **Privacy Regulations** - GLBA, CCPA data protection  
✅ **Capital Requirements** - Basel III, LCR, NSFR monitoring  
✅ **Operational Risk** - Third-party risk, cybersecurity  
✅ **Market Conduct** - UDAAP, CRA, fair lending  

The implementation provides real-time monitoring, automated violation detection, and comprehensive reporting across all major banking regulatory frameworks. Would you like me to create additional documentation for specific regulatory areas or implementation guides?
