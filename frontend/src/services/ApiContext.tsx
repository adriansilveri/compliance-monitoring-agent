/**
 * API Context Provider
 * Following SOLID principles - Single Responsibility for API management
 */

import React, { createContext, useContext, ReactNode } from 'react';
import axios, { AxiosInstance } from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Types
export interface Transaction {
  transaction_id: string;
  account_id: string;
  amount: number;
  currency: string;
  transaction_type: string;
  description?: string;
  counterparty_account?: string;
  counterparty_name?: string;
  transaction_channel: string;
  location_country: string;
  location_city?: string;
  transaction_timestamp: string;
  is_flagged: boolean;
  risk_score: number;
  compliance_status: string;
}

export interface ComplianceViolation {
  violation_id: string;
  violation_type: string;
  severity: string;
  title: string;
  description: string;
  regulatory_framework: string;
  standard_reference?: string;
  requirement_id?: string;
  risk_score: number;
  confidence_score: number;
  impact_assessment: string;
  status: string;
  assigned_to?: string;
  resolution_notes?: string;
  detected_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  violation_data?: any;
  remediation_actions?: string[];
}

export interface ComplianceDashboard {
  total_violations: number;
  critical_violations: number;
  high_violations: number;
  medium_violations: number;
  low_violations: number;
  open_violations: number;
  resolved_violations: number;
  overdue_violations: number;
  average_resolution_time_hours: number;
  compliance_score: number;
}

export interface TransactionStatistics {
  total_transactions: number;
  total_amount: number;
  average_amount: number;
  flagged_count: number;
  flagged_percentage: number;
  high_value_count: number;
  international_count: number;
}

// API Service Class following SOLID principles
class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Transaction API methods
  async createTransaction(transactionData: Partial<Transaction>): Promise<Transaction> {
    const response = await this.client.post('/transactions/', transactionData);
    return response.data;
  }

  async getTransaction(transactionId: string): Promise<Transaction> {
    const response = await this.client.get(`/transactions/${transactionId}`);
    return response.data;
  }

  async getAccountTransactions(
    accountId: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<Transaction[]> {
    const response = await this.client.get(`/transactions/account/${accountId}`, {
      params: { limit, offset },
    });
    return response.data;
  }

  async getFlaggedTransactions(limit: number = 100): Promise<Transaction[]> {
    const response = await this.client.get('/transactions/flagged/list', {
      params: { limit },
    });
    return response.data;
  }

  async getHighValueTransactions(
    threshold: number = 10000,
    days: number = 7
  ): Promise<Transaction[]> {
    const response = await this.client.get('/transactions/high-value/list', {
      params: { threshold, days },
    });
    return response.data;
  }

  async getTransactionStatistics(accountId?: string): Promise<TransactionStatistics> {
    const response = await this.client.get('/transactions/statistics/summary', {
      params: accountId ? { account_id: accountId } : {},
    });
    return response.data;
  }

  async detectSuspiciousPatterns(accountId: string): Promise<any> {
    const response = await this.client.post(`/transactions/patterns/detect/${accountId}`);
    return response.data;
  }

  async createTestViolation(): Promise<Transaction> {
    const response = await this.client.post('/transactions/test/apra-violation');
    return response.data;
  }

  // Compliance API methods
  async getViolations(
    severity?: string,
    status?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<ComplianceViolation[]> {
    const response = await this.client.get('/compliance/violations', {
      params: { severity, status, limit, offset },
    });
    return response.data;
  }

  async getViolation(violationId: string): Promise<ComplianceViolation> {
    const response = await this.client.get(`/compliance/violations/${violationId}`);
    return response.data;
  }

  async resolveViolation(
    violationId: string,
    resolutionNotes: string,
    resolvedBy: string
  ): Promise<any> {
    const response = await this.client.post(`/compliance/violations/${violationId}/resolve`, {
      resolution_notes: resolutionNotes,
      resolved_by: resolvedBy,
    });
    return response.data;
  }

  async getActiveViolationsSummary(): Promise<any> {
    const response = await this.client.get('/compliance/violations/active/summary');
    return response.data;
  }

  async getComplianceDashboard(): Promise<ComplianceDashboard> {
    const response = await this.client.get('/compliance/dashboard');
    return response.data;
  }

  async getComplianceRules(activeOnly: boolean = true, category?: string): Promise<any[]> {
    const response = await this.client.get('/compliance/rules', {
      params: { active_only: activeOnly, category },
    });
    return response.data;
  }

  async getApraStandards(): Promise<any> {
    const response = await this.client.get('/compliance/apra/standards');
    return response.data;
  }
}

// Context
interface ApiContextType {
  apiService: ApiService;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

// Provider component
interface ApiProviderProps {
  children: ReactNode;
}

export const ApiProvider: React.FC<ApiProviderProps> = ({ children }) => {
  const apiService = new ApiService();

  return (
    <ApiContext.Provider value={{ apiService }}>
      {children}
    </ApiContext.Provider>
  );
};

// Custom hook to use API service
export const useApi = (): ApiService => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context.apiService;
};
