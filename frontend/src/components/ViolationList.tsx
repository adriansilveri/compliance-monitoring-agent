/**
 * Violation List Component
 * Following SOLID principles - Single Responsibility for violation display
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
  Gavel as ResolveIcon,
  ExpandMore as ExpandMoreIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

import { useApi, ComplianceViolation } from '../services/ApiContext';

const ViolationList: React.FC = () => {
  const apiService = useApi();
  const [violations, setViolations] = useState<ComplianceViolation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<{
    severity: string;
    status: string;
  }>({
    severity: '',
    status: '',
  });

  // Resolution dialog state
  const [resolveDialog, setResolveDialog] = useState<{
    open: boolean;
    violation: ComplianceViolation | null;
    notes: string;
    resolvedBy: string;
    submitting: boolean;
  }>({
    open: false,
    violation: null,
    notes: '',
    resolvedBy: '',
    submitting: false,
  });

  useEffect(() => {
    loadViolations();
  }, [filter]);

  const loadViolations = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiService.getViolations(
        filter.severity || undefined,
        filter.status || undefined,
        100
      );

      setViolations(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load violations');
      console.error('Violation loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const openResolveDialog = (violation: ComplianceViolation) => {
    setResolveDialog({
      open: true,
      violation,
      notes: '',
      resolvedBy: 'compliance.officer@bank.com', // Default user
      submitting: false,
    });
  };

  const closeResolveDialog = () => {
    setResolveDialog({
      open: false,
      violation: null,
      notes: '',
      resolvedBy: '',
      submitting: false,
    });
  };

  const handleResolveViolation = async () => {
    if (!resolveDialog.violation || !resolveDialog.notes.trim() || !resolveDialog.resolvedBy.trim()) {
      return;
    }

    try {
      setResolveDialog(prev => ({ ...prev, submitting: true }));

      await apiService.resolveViolation(
        resolveDialog.violation.violation_id,
        resolveDialog.notes,
        resolveDialog.resolvedBy
      );

      // Reload violations to show updated status
      await loadViolations();
      closeResolveDialog();

    } catch (err: any) {
      setError(err.message || 'Failed to resolve violation');
    } finally {
      setResolveDialog(prev => ({ ...prev, submitting: false }));
    }
  };

  const getSeverityChip = (severity: string) => {
    const config = {
      CRITICAL: { color: 'error' as const, icon: <ErrorIcon /> },
      HIGH: { color: 'warning' as const, icon: <WarningIcon /> },
      MEDIUM: { color: 'info' as const, icon: <WarningIcon /> },
      LOW: { color: 'success' as const, icon: <CheckIcon /> },
    };

    const { color, icon } = config[severity as keyof typeof config] || config.MEDIUM;

    return (
      <Chip
        icon={icon}
        label={severity}
        color={color}
        size="small"
        sx={{ fontWeight: 'bold' }}
      />
    );
  };

  const getStatusChip = (status: string) => {
    const config = {
      OPEN: { color: 'error' as const, label: 'Open' },
      INVESTIGATING: { color: 'warning' as const, label: 'Investigating' },
      RESOLVED: { color: 'success' as const, label: 'Resolved' },
      CLOSED: { color: 'default' as const, label: 'Closed' },
    };

    const { color, label } = config[status as keyof typeof config] || config.OPEN;

    return (
      <Chip
        label={label}
        color={color}
        size="small"
      />
    );
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

  const getTimeSinceDetection = (detectedAt: string) => {
    const now = new Date();
    const detected = new Date(detectedAt);
    const diffHours = Math.floor((now.getTime() - detected.getTime()) / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Less than 1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} days ago`;
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
          Compliance Violations
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Monitor and manage APRA compliance violations
        </Typography>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={filter.severity}
                  label="Severity"
                  onChange={(e) => setFilter(prev => ({ ...prev, severity: e.target.value }))}
                >
                  <MenuItem value="">All Severities</MenuItem>
                  <MenuItem value="CRITICAL">Critical</MenuItem>
                  <MenuItem value="HIGH">High</MenuItem>
                  <MenuItem value="MEDIUM">Medium</MenuItem>
                  <MenuItem value="LOW">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filter.status}
                  label="Status"
                  onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))}
                >
                  <MenuItem value="">All Statuses</MenuItem>
                  <MenuItem value="OPEN">Open</MenuItem>
                  <MenuItem value="INVESTIGATING">Investigating</MenuItem>
                  <MenuItem value="RESOLVED">Resolved</MenuItem>
                  <MenuItem value="CLOSED">Closed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box display="flex" gap={1} justifyContent="flex-end">
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={loadViolations}
                  disabled={loading}
                >
                  Refresh
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<SecurityIcon />}
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
          <Button onClick={loadViolations} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      )}

      {/* Violations List */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Violations ({violations.length})
            </Typography>
            <Box display="flex" gap={1}>
              {filter.severity && (
                <Chip
                  label={`${filter.severity} Severity`}
                  color="primary"
                  size="small"
                />
              )}
              {filter.status && (
                <Chip
                  label={`${filter.status} Status`}
                  color="secondary"
                  size="small"
                />
              )}
            </Box>
          </Box>

          {violations.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography color="text.secondary">
                No violations found for the current filter
              </Typography>
            </Box>
          ) : (
            <Box>
              {violations.map((violation) => (
                <Accordion key={violation.violation_id} sx={{ mb: 1 }}>
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    sx={{
                      backgroundColor: violation.severity === 'CRITICAL' ? 'rgba(211, 47, 47, 0.04)' :
                                     violation.severity === 'HIGH' ? 'rgba(237, 108, 2, 0.04)' : 'inherit',
                    }}
                  >
                    <Box display="flex" alignItems="center" width="100%" gap={2}>
                      <Box flex={1}>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {violation.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {violation.regulatory_framework} - {violation.standard_reference}
                        </Typography>
                      </Box>
                      
                      <Box display="flex" gap={1} alignItems="center">
                        {getSeverityChip(violation.severity)}
                        {getStatusChip(violation.status)}
                        
                        <Chip
                          label={`Risk: ${violation.risk_score.toFixed(1)}`}
                          size="small"
                          color={violation.risk_score >= 8 ? 'error' : violation.risk_score >= 5 ? 'warning' : 'info'}
                        />
                        
                        <Typography variant="caption" color="text.secondary">
                          {getTimeSinceDetection(violation.detected_at)}
                        </Typography>
                      </Box>
                    </Box>
                  </AccordionSummary>
                  
                  <AccordionDetails>
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={8}>
                        <Typography variant="body1" paragraph>
                          {violation.description}
                        </Typography>
                        
                        {violation.violation_data && (
                          <Box mb={2}>
                            <Typography variant="subtitle2" gutterBottom>
                              Violation Details:
                            </Typography>
                            <Paper variant="outlined" sx={{ p: 2, backgroundColor: 'grey.50' }}>
                              <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                                {JSON.stringify(violation.violation_data, null, 2)}
                              </pre>
                            </Paper>
                          </Box>
                        )}
                        
                        {violation.remediation_actions && violation.remediation_actions.length > 0 && (
                          <Box mb={2}>
                            <Typography variant="subtitle2" gutterBottom>
                              Recommended Actions:
                            </Typography>
                            <Box component="ul" sx={{ pl: 2 }}>
                              {violation.remediation_actions.map((action, index) => (
                                <Typography component="li" key={index} variant="body2">
                                  {action}
                                </Typography>
                              ))}
                            </Box>
                          </Box>
                        )}
                        
                        {violation.resolution_notes && (
                          <Box mb={2}>
                            <Typography variant="subtitle2" gutterBottom>
                              Resolution Notes:
                            </Typography>
                            <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                              {violation.resolution_notes}
                            </Typography>
                          </Box>
                        )}
                      </Grid>
                      
                      <Grid item xs={12} md={4}>
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            Violation Information
                          </Typography>
                          
                          <Box mb={2}>
                            <Typography variant="caption" color="text.secondary">
                              Violation ID
                            </Typography>
                            <Typography variant="body2" fontFamily="monospace">
                              {violation.violation_id}
                            </Typography>
                          </Box>
                          
                          <Box mb={2}>
                            <Typography variant="caption" color="text.secondary">
                              Detected At
                            </Typography>
                            <Typography variant="body2">
                              {formatDateTime(violation.detected_at)}
                            </Typography>
                          </Box>
                          
                          {violation.resolved_at && (
                            <Box mb={2}>
                              <Typography variant="caption" color="text.secondary">
                                Resolved At
                              </Typography>
                              <Typography variant="body2">
                                {formatDateTime(violation.resolved_at)}
                              </Typography>
                            </Box>
                          )}
                          
                          <Box mb={2}>
                            <Typography variant="caption" color="text.secondary">
                              Confidence Score
                            </Typography>
                            <Typography variant="body2">
                              {(violation.confidence_score * 100).toFixed(1)}%
                            </Typography>
                          </Box>
                          
                          {violation.assigned_to && (
                            <Box mb={2}>
                              <Typography variant="caption" color="text.secondary">
                                Assigned To
                              </Typography>
                              <Typography variant="body2">
                                {violation.assigned_to}
                              </Typography>
                            </Box>
                          )}
                          
                          {violation.status === 'OPEN' && (
                            <Button
                              variant="contained"
                              color="primary"
                              startIcon={<ResolveIcon />}
                              onClick={() => openResolveDialog(violation)}
                              fullWidth
                              sx={{ mt: 2 }}
                            >
                              Resolve Violation
                            </Button>
                          )}
                        </Box>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Resolution Dialog */}
      <Dialog
        open={resolveDialog.open}
        onClose={closeResolveDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Resolve Compliance Violation
        </DialogTitle>
        <DialogContent>
          {resolveDialog.violation && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                {resolveDialog.violation.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {resolveDialog.violation.description}
              </Typography>
              
              <TextField
                fullWidth
                label="Resolved By"
                value={resolveDialog.resolvedBy}
                onChange={(e) => setResolveDialog(prev => ({ ...prev, resolvedBy: e.target.value }))}
                margin="normal"
                placeholder="e.g., compliance.officer@bank.com"
              />
              
              <TextField
                fullWidth
                label="Resolution Notes"
                value={resolveDialog.notes}
                onChange={(e) => setResolveDialog(prev => ({ ...prev, notes: e.target.value }))}
                margin="normal"
                multiline
                rows={4}
                placeholder="Describe how this violation was resolved..."
                required
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeResolveDialog} disabled={resolveDialog.submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleResolveViolation}
            variant="contained"
            disabled={resolveDialog.submitting || !resolveDialog.notes.trim() || !resolveDialog.resolvedBy.trim()}
            startIcon={resolveDialog.submitting ? <CircularProgress size={20} /> : <ResolveIcon />}
          >
            {resolveDialog.submitting ? 'Resolving...' : 'Resolve Violation'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ViolationList;
