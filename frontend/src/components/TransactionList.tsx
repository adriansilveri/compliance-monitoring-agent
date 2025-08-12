/**
 * Transaction List Component
 * Following SOLID principles - Single Responsibility for transaction display
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

import { useApi, Transaction } from '../services/ApiContext';

const TransactionList: React.FC = () => {
  const apiService = useApi();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'flagged' | 'high-value'>('all');
  const [searchAccount, setSearchAccount] = useState('');

  useEffect(() => {
    loadTransactions();
  }, [filter]);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      setError(null);

      let data: Transaction[];
      
      switch (filter) {
        case 'flagged':
          data = await apiService.getFlaggedTransactions(100);
          break;
        case 'high-value':
          data = await apiService.getHighValueTransactions(10000, 30);
          break;
        default:
          // For demo purposes, we'll get flagged transactions as a sample
          // In a real app, you'd have an endpoint to get all transactions
          data = await apiService.getFlaggedTransactions(100);
          break;
      }

      setTransactions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load transactions');
      console.error('Transaction loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const searchByAccount = async () => {
    if (!searchAccount.trim()) {
      loadTransactions();
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const data = await apiService.getAccountTransactions(searchAccount.trim(), 100);
      setTransactions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to search transactions');
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (transaction: Transaction) => {
    if (transaction.is_flagged) {
      return (
        <Chip
          icon={<WarningIcon />}
          label="Flagged"
          color="error"
          size="small"
        />
      );
    }
    
    switch (transaction.compliance_status) {
      case 'APPROVED':
        return (
          <Chip
            icon={<CheckIcon />}
            label="Approved"
            color="success"
            size="small"
          />
        );
      case 'UNDER_REVIEW':
        return (
          <Chip
            icon={<WarningIcon />}
            label="Under Review"
            color="warning"
            size="small"
          />
        );
      case 'REJECTED':
        return (
          <Chip
            icon={<ErrorIcon />}
            label="Rejected"
            color="error"
            size="small"
          />
        );
      default:
        return (
          <Chip
            label="Pending"
            color="default"
            size="small"
          />
        );
    }
  };

  const getRiskScoreColor = (score: number) => {
    if (score >= 8) return 'error';
    if (score >= 5) return 'warning';
    if (score >= 2) return 'info';
    return 'success';
  };

  const formatCurrency = (amount: number, currency: string = 'AUD') => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-AU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
          Transaction Monitoring
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Monitor transactions and compliance status in real-time
        </Typography>
      </Box>

      {/* Filters and Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Filter</InputLabel>
                <Select
                  value={filter}
                  label="Filter"
                  onChange={(e) => setFilter(e.target.value as any)}
                >
                  <MenuItem value="all">All Transactions</MenuItem>
                  <MenuItem value="flagged">Flagged Only</MenuItem>
                  <MenuItem value="high-value">High Value (>$10K)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search by Account ID"
                value={searchAccount}
                onChange={(e) => setSearchAccount(e.target.value)}
                placeholder="e.g., ACC123456"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    searchByAccount();
                  }
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={5}>
              <Box display="flex" gap={1}>
                <Button
                  variant="contained"
                  onClick={searchByAccount}
                  disabled={loading}
                >
                  Search
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={loadTransactions}
                  disabled={loading}
                >
                  Refresh
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<TrendingUpIcon />}
                  onClick={() => window.location.href = '/dashboard'}
                >
                  View Dashboard
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
          <Button onClick={loadTransactions} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      )}

      {/* Transaction Table */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Transactions ({transactions.length})
            </Typography>
            <Box display="flex" gap={1}>
              <Chip
                label={`${filter.charAt(0).toUpperCase() + filter.slice(1)} View`}
                color="primary"
                size="small"
              />
            </Box>
          </Box>

          {transactions.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography color="text.secondary">
                No transactions found for the current filter
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Transaction ID</TableCell>
                    <TableCell>Account</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Country</TableCell>
                    <TableCell>Channel</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="center">Risk Score</TableCell>
                    <TableCell>Date/Time</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactions.map((transaction) => (
                    <TableRow
                      key={transaction.transaction_id}
                      sx={{
                        backgroundColor: transaction.is_flagged ? 'rgba(255, 152, 0, 0.04)' : 'inherit',
                        '&:hover': {
                          backgroundColor: transaction.is_flagged ? 'rgba(255, 152, 0, 0.08)' : 'rgba(0, 0, 0, 0.04)',
                        },
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {transaction.transaction_id.substring(0, 8)}...
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {transaction.account_id}
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          fontWeight="medium"
                          color={transaction.amount > 10000 ? 'warning.main' : 'text.primary'}
                        >
                          {formatCurrency(transaction.amount, transaction.currency)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={transaction.transaction_type}
                          size="small"
                          variant="outlined"
                          color={
                            transaction.transaction_type === 'DEBIT' ? 'error' :
                            transaction.transaction_type === 'CREDIT' ? 'success' : 'info'
                          }
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <Typography variant="body2">
                            {transaction.location_country}
                          </Typography>
                          {transaction.location_country !== 'AUS' && (
                            <Chip
                              label="International"
                              size="small"
                              color="warning"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2">
                          {transaction.transaction_channel}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        {getStatusChip(transaction)}
                      </TableCell>
                      
                      <TableCell align="center">
                        <Chip
                          label={transaction.risk_score.toFixed(1)}
                          size="small"
                          color={getRiskScoreColor(transaction.risk_score)}
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2">
                          {formatDateTime(transaction.transaction_timestamp)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="center">
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => {
                              // In a real app, this would open a detail modal or navigate to detail page
                              alert(`Transaction Details:\n\nID: ${transaction.transaction_id}\nAccount: ${transaction.account_id}\nAmount: ${formatCurrency(transaction.amount, transaction.currency)}\nDescription: ${transaction.description || 'N/A'}\nCounterparty: ${transaction.counterparty_name || 'N/A'}\nRisk Score: ${transaction.risk_score}\nStatus: ${transaction.compliance_status}`);
                            }}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Summary Statistics */}
      {transactions.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Summary Statistics
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary.main">
                    {transactions.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Transactions
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="error.main">
                    {transactions.filter(t => t.is_flagged).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Flagged
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="warning.main">
                    {transactions.filter(t => t.amount > 10000).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Value
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="info.main">
                    {transactions.filter(t => t.location_country !== 'AUS').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    International
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default TransactionList;
