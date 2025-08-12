/**
 * Navigation Bar Component
 * Following SOLID principles - Single Responsibility for navigation
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  AccountBalance as BankIcon,
  Warning as WarningIcon,
  Add as AddIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navigationItems = [
    {
      label: 'Dashboard',
      path: '/dashboard',
      icon: <DashboardIcon />,
    },
    {
      label: 'Transactions',
      path: '/transactions',
      icon: <BankIcon />,
    },
    {
      label: 'Violations',
      path: '/violations',
      icon: <WarningIcon />,
    },
    {
      label: 'Create Transaction',
      path: '/create-transaction',
      icon: <AddIcon />,
    },
  ];

  const isActivePath = (path: string): boolean => {
    return location.pathname === path || (path === '/dashboard' && location.pathname === '/');
  };

  return (
    <AppBar position="static" elevation={2}>
      <Toolbar>
        {/* Logo and Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 4 }}>
          <SecurityIcon sx={{ mr: 1, fontSize: 28 }} />
          <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
            APRA Compliance Monitor
          </Typography>
        </Box>

        {/* Navigation Items */}
        <Box sx={{ display: 'flex', gap: 1, flexGrow: 1 }}>
          {navigationItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              sx={{
                backgroundColor: isActivePath(item.path) ? 'rgba(255,255,255,0.1)' : 'transparent',
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.2)',
                },
                borderRadius: 2,
                px: 2,
                py: 1,
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        {/* Status Indicators */}
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Chip
            label="APRA Compliant"
            color="success"
            size="small"
            sx={{
              backgroundColor: 'rgba(76, 175, 80, 0.2)',
              color: '#4caf50',
              fontWeight: 500,
            }}
          />
          <Chip
            label="Real-time Monitoring"
            color="info"
            size="small"
            sx={{
              backgroundColor: 'rgba(33, 150, 243, 0.2)',
              color: '#2196f3',
              fontWeight: 500,
            }}
          />
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
