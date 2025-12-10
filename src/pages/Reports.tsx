import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  AppBar,
  Toolbar,
  Tabs,
  Tab
} from '@mui/material';
import {
  Home as HomeIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const Reports: React.FC = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [dateRange, setDateRange] = useState({
    startDate: '2024-01-01',
    endDate: '2024-01-31'
  });

  // Mock data for reports
  const salesData = [
    { date: '2024-01-01', sales: 15000, transactions: 45 },
    { date: '2024-01-02', sales: 18000, transactions: 52 },
    { date: '2024-01-03', sales: 12000, transactions: 38 },
    { date: '2024-01-04', sales: 22000, transactions: 65 },
    { date: '2024-01-05', sales: 19000, transactions: 58 },
    { date: '2024-01-06', sales: 25000, transactions: 72 },
    { date: '2024-01-07', sales: 21000, transactions: 61 }
  ];

  const topProducts = [
    { name: 'Rice 1kg', sales: 150000, quantity: 1875, profit: 15000 },
    { name: 'Dal 500g', sales: 120000, quantity: 1000, profit: 20000 },
    { name: 'Oil 1L', sales: 90000, quantity: 600, profit: 12000 },
    { name: 'Sugar 1kg', sales: 67500, quantity: 1500, profit: 7500 },
    { name: 'Tea 250g', sales: 60000, quantity: 300, profit: 6000 }
  ];

  const categoryData = [
    { name: 'Grains', value: 35, color: '#8884d8' },
    { name: 'Pulses', value: 25, color: '#82ca9d' },
    { name: 'Cooking Oil', value: 20, color: '#ffc658' },
    { name: 'Beverages', value: 15, color: '#ff7300' },
    { name: 'Others', value: 5, color: '#00ff00' }
  ];

  const monthlyStats = {
    totalRevenue: 450000,
    totalTransactions: 1250,
    averageOrderValue: 360,
    topSellingDay: 'Saturday',
    growthRate: 12.5
  };

  const hotelStats = {
    totalRevenue: 1200000,
    totalBookings: 180,
    averageStay: 2.3,
    occupancyRate: 78,
    averageRoomRate: 3500
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static" sx={{ backgroundColor: '#1976d2' }}>
        <Toolbar>
          <IconButton
            color="inherit"
            onClick={() => navigate('/')}
            sx={{ mr: 2 }}
          >
            <HomeIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Reports & Analytics
          </Typography>
          <Button
            color="inherit"
            startIcon={<DownloadIcon />}
            sx={{ mr: 1 }}
          >
            Export
          </Button>
          <Button
            color="inherit"
            startIcon={<PrintIcon />}
          >
            Print
          </Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 3, flexGrow: 1 }}>
        {/* Date Range Selector */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <TextField
                type="date"
                label="Start Date"
                value={dateRange.startDate}
                onChange={(e) => setDateRange({ ...dateRange, startDate: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                type="date"
                label="End Date"
                value={dateRange.endDate}
                onChange={(e) => setDateRange({ ...dateRange, endDate: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
              <Button variant="contained" startIcon={<AssessmentIcon />}>
                Generate Report
              </Button>
            </Box>
          </CardContent>
        </Card>

        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
          <Tab label="Sales Overview" />
          <Tab label="Product Analysis" />
          <Tab label="Hotel Analytics" />
        </Tabs>

        {/* Sales Overview Tab */}
        {tabValue === 0 && (
          <Grid container spacing={3}>
            {/* Key Metrics */}
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <TrendingUpIcon sx={{ fontSize: 40, color: '#1976d2', mb: 1 }} />
                  <Typography variant="h4">₹{monthlyStats.totalRevenue.toLocaleString()}</Typography>
                  <Typography color="text.secondary">Total Revenue</Typography>
                  <Typography variant="caption" color="success.main">
                    +{monthlyStats.growthRate}% from last month
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">{monthlyStats.totalTransactions}</Typography>
                  <Typography color="text.secondary">Total Transactions</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">₹{monthlyStats.averageOrderValue}</Typography>
                  <Typography color="text.secondary">Avg Order Value</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">{monthlyStats.topSellingDay}</Typography>
                  <Typography color="text.secondary">Best Day</Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Sales Trend Chart */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Sales Trend</Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={salesData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="sales" stroke="#8884d8" name="Sales (₹)" />
                      <Line type="monotone" dataKey="transactions" stroke="#82ca9d" name="Transactions" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Product Analysis Tab */}
        {tabValue === 1 && (
          <Grid container spacing={3}>
            {/* Top Products Table */}
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Top Selling Products</Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Product</TableCell>
                          <TableCell align="right">Sales (₹)</TableCell>
                          <TableCell align="right">Quantity</TableCell>
                          <TableCell align="right">Profit (₹)</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {topProducts.map((product, index) => (
                          <TableRow key={product.name}>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Typography variant="body2" sx={{ 
                                  backgroundColor: index < 3 ? '#gold' : 'transparent',
                                  color: index < 3 ? '#fff' : 'inherit',
                                  px: 1,
                                  py: 0.5,
                                  borderRadius: 1,
                                  mr: 1,
                                  minWidth: 20,
                                  textAlign: 'center'
                                }}>
                                  {index + 1}
                                </Typography>
                                {product.name}
                              </Box>
                            </TableCell>
                            <TableCell align="right">₹{product.sales.toLocaleString()}</TableCell>
                            <TableCell align="right">{product.quantity}</TableCell>
                            <TableCell align="right">₹{product.profit.toLocaleString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>

            {/* Category Distribution */}
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Sales by Category</Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {categoryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            {/* Product Performance Chart */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Product Performance</Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={topProducts}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="sales" fill="#8884d8" name="Sales (₹)" />
                      <Bar dataKey="profit" fill="#82ca9d" name="Profit (₹)" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Hotel Analytics Tab */}
        {tabValue === 2 && (
          <Grid container spacing={3}>
            {/* Hotel Key Metrics */}
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">₹{(hotelStats.totalRevenue / 1000).toFixed(0)}K</Typography>
                  <Typography color="text.secondary">Total Revenue</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">{hotelStats.totalBookings}</Typography>
                  <Typography color="text.secondary">Total Bookings</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">{hotelStats.averageStay}</Typography>
                  <Typography color="text.secondary">Avg Stay (days)</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">{hotelStats.occupancyRate}%</Typography>
                  <Typography color="text.secondary">Occupancy Rate</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4">₹{hotelStats.averageRoomRate}</Typography>
                  <Typography color="text.secondary">Avg Room Rate</Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Hotel Revenue Chart */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Monthly Revenue Breakdown</Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={[
                      { month: 'Jan', rooms: 800000, services: 400000 },
                      { month: 'Feb', rooms: 750000, services: 350000 },
                      { month: 'Mar', rooms: 900000, services: 450000 },
                      { month: 'Apr', rooms: 850000, services: 400000 }
                    ]}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="rooms" stackId="a" fill="#8884d8" name="Room Revenue" />
                      <Bar dataKey="services" stackId="a" fill="#82ca9d" name="Service Revenue" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Box>
    </Box>
  );
};

export default Reports;