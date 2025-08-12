/**
 * Main App Component
 * Following SOLID principles and React best practices
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';

import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import TransactionList from './components/TransactionList';
import ViolationList from './components/ViolationList';
import TransactionForm from './components/TransactionForm';
import { ApiProvider } from './services/ApiContext';

// APRA-themed color palette
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Professional blue
      dark: '#115293',
      light: '#42a5f5',
    },
    secondary: {
      main: '#dc004e', // Alert red for violations
      dark: '#9a0036',
      light: '#e33371',
    },
    error: {
      main: '#d32f2f',
    },
    warning: {
      main: '#ed6c02',
    },
    success: {
      main: '#2e7d32',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 6,
        },
      },
    },
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ApiProvider>
        <Router>
          <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/transactions" element={<TransactionList />} />
                <Route path="/violations" element={<ViolationList />} />
                <Route path="/create-transaction" element={<TransactionForm />} />
              </Routes>
            </Box>
          </Box>
        </Router>
      </ApiProvider>
    </ThemeProvider>
  );
};

export default App;
