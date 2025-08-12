/**
 * Transaction Form Component
 * Following SOLID principles - Single Responsibility for transaction creation
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Box,
  Alert,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Add as AddIcon, Warning as WarningIcon } from '@mui/icons-material';

import { useApi, Transaction } from '../services/ApiContext';

interface TransactionFormData {
  account_id: string;
  amount: string;
  currency: string;
  transaction_type: string;
  description: string;
  counterparty_account: string;
  counterparty_name: string;
  counterparty_bank: string;
  transaction_channel: string;
  location_country: string;
  location_city: string;
  ip_address: string;
}

const TransactionForm: React.FC = () => {
  const apiService = useApi();
  const [formData, setFormData] = useState<TransactionFormData>({
    account_id: '',
    amount: '',
    currency: 'AUD',
    transaction_type: 'DEBIT',
    description: '',
    counterparty_account: '',
    counterparty_name: '',
    counterparty_bank: '',
    transaction_channel: 'ONLINE',
    location_country: 'AUS',
    location_city: '',
    ip_address: '',
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<Transaction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [violations, setViolations] = useState<string[]>([]);

  const transactionTypes = [
    { value: 'DEBIT', label: 'Debit' },
    { value: 'CREDIT', label: 'Credit' },
    { value: 'TRANSFER', label: 'Transfer' },
  ];

  const currencies = [
    { value: 'AUD', label: 'Australian Dollar (AUD)' },
    { value: 'USD', label: 'US Dollar (USD)' },
    { value: 'EUR', label: 'Euro (EUR)' },
    { value: 'GBP', label: 'British Pound (GBP)' },
    { value: 'JPY', label: 'Japanese Yen (JPY)' },
  ];

  const channels = [
    { value: 'ONLINE', label: 'Online Banking' },
    { value: 'ATM', label: 'ATM' },
    { value: 'BRANCH', label: 'Branch' },
    { value: 'MOBILE', label: 'Mobile App' },
    { value: 'PHONE', label: 'Phone Banking' },
  ];

  const countries = [
    { value: 'AUS', label: 'Australia' },
    { value: 'USA', label: 'United States' },
    { value: 'GBR', label: 'United Kingdom' },
    { value: 'CAN', label: 'Canada' },
    { value: 'NZL', label: 'New Zealand' },
    { value: 'SGP', label: 'Singapore' },
    { value: 'HKG', label: 'Hong Kong' },
    { value: 'IRN', label: 'Iran (High Risk)' },
    { value: 'PRK', label: 'North Korea (High Risk)' },
  ];

  // Test scenarios for demonstration
  const testScenarios = [
    {
      name: 'Normal Transaction',
      data: {
        account_id: 'ACC001',
        amount: '2500.00',
        description: 'Normal business transaction',
        counterparty_name: 'ABC Company Pty Ltd',
        location_city: 'Sydney',
      },
    },
    {
      name: 'High Value (APRA Violation)',
      data: {
        account_id: 'ACC002',
        amount: '15000.00',
        description: 'High value transaction - will trigger APRA limit violation',
        counterparty_name: 'Large Corporation',
        location_city: 'Melbourne',
      },
    },
    {
      name: 'High Risk Country',
      data: {
        account_id: 'ACC003',
        amount: '5000.00',
        description: 'International transfer to high-risk country',
        counterparty_name: 'Foreign Entity',
        location_country: 'IRN',
        location_city: 'Tehran',
      },
    },
    {
      name: 'Structuring Pattern',
      data: {
        account_id: 'ACC004',
        amount: '9800.00',
        description: 'Transaction just under reporting threshold',
        counterparty_name: 'Cash Business',
        location_city: 'Brisbane',
      },
    },
  ];

  const handleInputChange = (field: keyof TransactionFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Clear previous results when form changes
    if (success || error) {
      setSuccess(null);
      setError(null);
      setViolations([]);
    }
  };

  const loadTestScenario = (scenario: typeof testScenarios[0]) => {
    setFormData(prev => ({
      ...prev,
      ...scenario.data,
    }));
    setSuccess(null);
    setError(null);
    setViolations([]);
  };

  const validateForm = (): string[] => {
    const errors: string[] = [];
    
    if (!formData.account_id.trim()) errors.push('Account ID is required');
    if (!formData.amount.trim()) errors.push('Amount is required');
    if (isNaN(parseFloat(formData.amount)) || parseFloat(formData.amount) <= 0) {
      errors.push('Amount must be a positive number');
    }
    if (!formData.transaction_type) errors.push('Transaction type is required');
    
    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
      setError(validationErrors.join(', '));
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setViolations([]);

    try {
      // Convert form data to API format
      const transactionData = {
        ...formData,
        amount: parseFloat(formData.amount),
      };

      const result = await apiService.createTransaction(transactionData);
      setSuccess(result);

      // Check if transaction was flagged
      if (result.is_flagged) {
        setViolations([
          `Transaction flagged with risk score: ${result.risk_score}`,
          `Compliance status: ${result.compliance_status}`,
        ]);
      }

      // Reset form for next transaction
      setFormData({
        account_id: '',
        amount: '',
        currency: 'AUD',
        transaction_type: 'DEBIT',
        description: '',
        counterparty_account: '',
        counterparty_name: '',
        counterparty_bank: '',
        transaction_channel: 'ONLINE',
        location_country: 'AUS',
        location_city: '',
        ip_address: '',
      });

    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create transaction');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
          Create Transaction
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Create a new transaction with automatic APRA compliance checking
        </Typography>
      </Box>

      {/* Test Scenarios */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Test Scenarios
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Quick-fill the form with predefined scenarios to test compliance rules
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            {testScenarios.map((scenario, index) => (
              <Button
                key={index}
                variant="outlined"
                size="small"
                onClick={() => loadTestScenario(scenario)}
                sx={{ mb: 1 }}
              >
                {scenario.name}
              </Button>
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Success Message */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            Transaction created successfully!
          </Typography>
          <Typography variant="body2">
            Transaction ID: {success.transaction_id}
          </Typography>
          {violations.length > 0 && (
            <Box mt={1}>
              <Typography variant="body2" color="warning.main">
                <WarningIcon sx={{ fontSize: 16, mr: 0.5 }} />
                Compliance Alerts:
              </Typography>
              {violations.map((violation, index) => (
                <Chip
                  key={index}
                  label={violation}
                  color="warning"
                  size="small"
                  sx={{ mr: 1, mt: 0.5 }}
                />
              ))}
            </Box>
          )}
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Transaction Form */}
      <Card>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              {/* Basic Information */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Basic Information
                </Typography>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Account ID"
                  value={formData.account_id}
                  onChange={(e) => handleInputChange('account_id', e.target.value)}
                  required
                  placeholder="e.g., ACC123456"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Amount"
                  type="number"
                  value={formData.amount}
                  onChange={(e) => handleInputChange('amount', e.target.value)}
                  required
                  inputProps={{ min: 0, step: 0.01 }}
                  placeholder="0.00"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Currency</InputLabel>
                  <Select
                    value={formData.currency}
                    label="Currency"
                    onChange={(e) => handleInputChange('currency', e.target.value)}
                  >
                    {currencies.map((currency) => (
                      <MenuItem key={currency.value} value={currency.value}>
                        {currency.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Transaction Type</InputLabel>
                  <Select
                    value={formData.transaction_type}
                    label="Transaction Type"
                    onChange={(e) => handleInputChange('transaction_type', e.target.value)}
                  >
                    {transactionTypes.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  multiline
                  rows={2}
                  placeholder="Transaction description..."
                />
              </Grid>

              {/* Counterparty Information */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Counterparty Information
                </Typography>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Counterparty Account"
                  value={formData.counterparty_account}
                  onChange={(e) => handleInputChange('counterparty_account', e.target.value)}
                  placeholder="e.g., MERCHANT001"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Counterparty Name"
                  value={formData.counterparty_name}
                  onChange={(e) => handleInputChange('counterparty_name', e.target.value)}
                  placeholder="e.g., ABC Company Pty Ltd"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Counterparty Bank"
                  value={formData.counterparty_bank}
                  onChange={(e) => handleInputChange('counterparty_bank', e.target.value)}
                  placeholder="e.g., Commonwealth Bank"
                />
              </Grid>

              {/* Transaction Details */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Transaction Details
                </Typography>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Transaction Channel</InputLabel>
                  <Select
                    value={formData.transaction_channel}
                    label="Transaction Channel"
                    onChange={(e) => handleInputChange('transaction_channel', e.target.value)}
                  >
                    {channels.map((channel) => (
                      <MenuItem key={channel.value} value={channel.value}>
                        {channel.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Location Country</InputLabel>
                  <Select
                    value={formData.location_country}
                    label="Location Country"
                    onChange={(e) => handleInputChange('location_country', e.target.value)}
                  >
                    {countries.map((country) => (
                      <MenuItem key={country.value} value={country.value}>
                        {country.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Location City"
                  value={formData.location_city}
                  onChange={(e) => handleInputChange('location_city', e.target.value)}
                  placeholder="e.g., Sydney"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="IP Address"
                  value={formData.ip_address}
                  onChange={(e) => handleInputChange('ip_address', e.target.value)}
                  placeholder="e.g., 192.168.1.100"
                />
              </Grid>

              {/* Submit Button */}
              <Grid item xs={12}>
                <Box display="flex" justifyContent="flex-end" gap={2} mt={2}>
                  <Button
                    type="button"
                    variant="outlined"
                    onClick={() => {
                      setFormData({
                        account_id: '',
                        amount: '',
                        currency: 'AUD',
                        transaction_type: 'DEBIT',
                        description: '',
                        counterparty_account: '',
                        counterparty_name: '',
                        counterparty_bank: '',
                        transaction_channel: 'ONLINE',
                        location_country: 'AUS',
                        location_city: '',
                        ip_address: '',
                      });
                      setSuccess(null);
                      setError(null);
                      setViolations([]);
                    }}
                  >
                    Clear Form
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={loading ? <CircularProgress size={20} /> : <AddIcon />}
                    disabled={loading}
                  >
                    {loading ? 'Creating...' : 'Create Transaction'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default TransactionForm;
