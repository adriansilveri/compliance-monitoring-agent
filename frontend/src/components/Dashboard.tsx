/**
 * Compliance Dashboard Component
 * Following SOLID principles - Single Responsibility for dashboard display
 */

import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Chip,
  LinearProgress,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  Warning,
  CheckCircle,
  Error,
  Security,
  Assessment,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

import { useApi, ComplianceDashboard, TransactionStatistics } from '../services/ApiContext';

// Color scheme for charts
const COLORS = {
  critical: '#d32f2f',
  high: '#ed6c02',
  medium: '#1976d2',
  low: '#2e7d32',
  resolved: '#4caf50',
  open: '#ff9800',
};

const Dashboard: React.FC = () => {
  const apiService = useApi();
  const [dashboardData, setDashboardData] = useState<ComplianceDashboard | null>(null);
  const [transactionStats, setTransactionStats] = useState<TransactionStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [dashboard, stats] = await Promise.all([
        apiService.getComplianceDashboard(),
        apiService.getTransactionStatistics(),
      ]);

      setDashboardData(dashboard);
      setTransactionStats(stats);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
      console.error('Dashboard loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const createTestViolation = async () => {
    try {
      await apiService.createTestViolation();
      // Reload dashboard data to show new violation
      await loadDashboardData();
    } catch (err: any) {
      console.error('Failed to create test violation:', err);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button onClick={loadDashboardData} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  if (!dashboardData || !transactionStats) {
    return (
      <Alert severity="info">
        No dashboard data available
      </Alert>
    );
  }

  // Prepare chart data
  const violationsByType = [
    { name: 'Critical', value: dashboardData.critical_violations, color: COLORS.critical },
    { name: 'High', value: dashboardData.high_violations, color: COLORS.high },
    { name: 'Medium', value: dashboardData.medium_violations, color: COLORS.medium },
    { name: 'Low', value: dashboardData.low_violations, color: COLORS.low },
  ].filter(item => item.value > 0);

  const violationsByStatus = [
    { name: 'Open', value: dashboardData.open_violations, color: COLORS.open },
    { name: 'Resolved', value: dashboardData.resolved_violations, color: COLORS.resolved },
  ].filter(item => item.value > 0);

  const complianceScore = dashboardData.compliance_score;
  const getScoreColor = (score: number) => {
    if (score >= 90) return COLORS.low;
    if (score >= 70) return COLORS.medium;
    if (score >= 50) return COLORS.high;
    return COLORS.critical;
  };

  return (
    <Box>
      {/* Header */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
          APRA Compliance Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Real-time monitoring and compliance status overview
        </Typography>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} mb={4}>
        {/* Compliance Score */}
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)' }}>
            <CardContent sx={{ color: 'white' }}>
              <Box display="flex" alignItems="center" mb={2}>
                <Security sx={{ mr: 1 }} />
                <Typography variant="h6">Compliance Score</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
                {complianceScore.toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={complianceScore}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'rgba(255,255,255,0.3)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: 'white',
                  },
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Total Violations */}
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Warning sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Total Violations</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
                {dashboardData.total_violations}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {dashboardData.overdue_violations} overdue
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Critical Violations */}
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Error sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6">Critical Issues</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'error.main' }}>
                {dashboardData.critical_violations}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Require immediate attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Transaction Volume */}
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Transactions</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                {transactionStats.total_transactions.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ${transactionStats.total_amount.toLocaleString()} total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} mb={4}>
        {/* Violations by Severity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Assessment sx={{ mr: 1 }} />
                Violations by Severity
              </Typography>
              {violationsByType.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={violationsByType}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {violationsByType.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Box display="flex" justifyContent="center" alignItems="center" height={300}>
                  <Typography color="text.secondary">No violations to display</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Violations by Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircle sx={{ mr: 1 }} />
                Resolution Status
              </Typography>
              {violationsByStatus.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={violationsByStatus}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8884d8">
                      {violationsByStatus.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box display="flex" justifyContent="center" alignItems="center" height={300}>
                  <Typography color="text.secondary">No violations to display</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Transaction Statistics */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Transaction Statistics
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary.main" sx={{ fontWeight: 'bold' }}>
                      {transactionStats.flagged_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Flagged Transactions
                    </Typography>
                    <Chip
                      label={`${transactionStats.flagged_percentage.toFixed(1)}%`}
                      color={transactionStats.flagged_percentage > 5 ? 'error' : 'success'}
                      size="small"
                      sx={{ mt: 1 }}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="warning.main" sx={{ fontWeight: 'bold' }}>
                      {transactionStats.high_value_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      High Value (>$10K)
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="info.main" sx={{ fontWeight: 'bold' }}>
                      {transactionStats.international_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      International
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="success.main" sx={{ fontWeight: 'bold' }}>
                      ${transactionStats.average_amount.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Average Amount
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => window.location.href = '/transactions'}
                >
                  View All Transactions
                </Button>
                <Button
                  variant="contained"
                  color="warning"
                  onClick={() => window.location.href = '/violations'}
                >
                  Review Violations
                </Button>
                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={createTestViolation}
                >
                  Create Test Violation
                </Button>
                <Button
                  variant="outlined"
                  onClick={loadDashboardData}
                >
                  Refresh Data
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
