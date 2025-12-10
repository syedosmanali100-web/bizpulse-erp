import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Container,
  Grid,
  Paper
} from '@mui/material';
import {
  Store as StoreIcon,
  Hotel as HotelIcon,
  Assessment as ReportsIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

const BusinessSelector: React.FC = () => {
  const navigate = useNavigate();

  const businessTypes = [
    {
      title: 'Retail Store',
      description: 'Quick billing, inventory management, and customer accounts',
      icon: <StoreIcon sx={{ fontSize: 60, color: '#1976d2' }} />,
      path: '/retail',
      color: '#e3f2fd'
    },
    {
      title: 'Hotel Management',
      description: 'Guest billing, room charges, and service management',
      icon: <HotelIcon sx={{ fontSize: 60, color: '#d32f2f' }} />,
      path: '/hotel',
      color: '#ffebee'
    }
  ];

  const quickActions = [
    {
      title: 'Reports & Analytics',
      icon: <ReportsIcon sx={{ fontSize: 40 }} />,
      path: '/reports'
    },
    {
      title: 'Settings',
      icon: <SettingsIcon sx={{ fontSize: 40 }} />,
      path: '/settings'
    }
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box textAlign="center" mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          Billing Software
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Choose your business type to get started
        </Typography>
      </Box>

      <Grid container spacing={4} justifyContent="center">
        {businessTypes.map((business) => (
          <Grid item xs={12} md={5} key={business.title}>
            <Card 
              sx={{ 
                height: '100%',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
              onClick={() => navigate(business.path)}
            >
              <CardContent sx={{ textAlign: 'center', p: 4 }}>
                <Paper 
                  sx={{ 
                    backgroundColor: business.color,
                    p: 3,
                    mb: 3,
                    display: 'inline-block',
                    borderRadius: 2
                  }}
                >
                  {business.icon}
                </Paper>
                <Typography variant="h4" component="h2" gutterBottom>
                  {business.title}
                </Typography>
                <Typography variant="body1" color="text.secondary" mb={3}>
                  {business.description}
                </Typography>
                <Button 
                  variant="contained" 
                  size="large"
                  onClick={() => navigate(business.path)}
                >
                  Get Started
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box mt={6}>
        <Typography variant="h5" textAlign="center" mb={3}>
          Quick Actions
        </Typography>
        <Grid container spacing={2} justifyContent="center">
          {quickActions.map((action) => (
            <Grid item xs={6} sm={3} key={action.title}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  textAlign: 'center',
                  '&:hover': { boxShadow: 3 }
                }}
                onClick={() => navigate(action.path)}
              >
                <CardContent>
                  {action.icon}
                  <Typography variant="body2" mt={1}>
                    {action.title}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Container>
  );
};

export default BusinessSelector;