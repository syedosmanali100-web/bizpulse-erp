import React, { useState } from 'react';
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
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Payment as PaymentIcon,
  History as HistoryIcon,
  Search as SearchIcon
} from '@mui/icons-material';

interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
  creditLimit: number;
  currentBalance: number;
  totalPurchases: number;
  lastPurchase?: Date;
}

interface Transaction {
  id: string;
  customerId: string;
  type: 'sale' | 'payment';
  amount: number;
  date: Date;
  description: string;
  balance: number;
}

const KiranaCustomers: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([
    {
      id: '1',
      name: 'Rajesh Kumar',
      phone: '9876543210',
      email: 'rajesh@email.com',
      address: '123 Main Street',
      creditLimit: 5000,
      currentBalance: 1200,
      totalPurchases: 15000,
      lastPurchase: new Date('2024-01-15')
    },
    {
      id: '2',
      name: 'Priya Sharma',
      phone: '9876543211',
      creditLimit: 3000,
      currentBalance: 0,
      totalPurchases: 8000,
      lastPurchase: new Date('2024-01-10')
    },
    {
      id: '3',
      name: 'Amit Singh',
      phone: '9876543212',
      creditLimit: 2000,
      currentBalance: 500,
      totalPurchases: 5000,
      lastPurchase: new Date('2024-01-12')
    }
  ]);

  const [transactions, setTransactions] = useState<Transaction[]>([
    {
      id: '1',
      customerId: '1',
      type: 'sale',
      amount: 500,
      date: new Date('2024-01-15'),
      description: 'Grocery purchase',
      balance: 1200
    },
    {
      id: '2',
      customerId: '1',
      type: 'payment',
      amount: -300,
      date: new Date('2024-01-14'),
      description: 'Cash payment',
      balance: 700
    }
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [addDialog, setAddDialog] = useState(false);
  const [editDialog, setEditDialog] = useState(false);
  const [paymentDialog, setPaymentDialog] = useState(false);
  const [historyDialog, setHistoryDialog] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [tabValue, setTabValue] = useState(0);

  const [newCustomer, setNewCustomer] = useState<Partial<Customer>>({
    name: '',
    phone: '',
    email: '',
    address: '',
    creditLimit: 1000,
    currentBalance: 0,
    totalPurchases: 0
  });

  const filteredCustomers = customers.filter(customer =>
    customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    customer.phone.includes(searchTerm)
  );

  const creditCustomers = customers.filter(customer => customer.currentBalance > 0);

  const addCustomer = () => {
    if (newCustomer.name && newCustomer.phone) {
      const customer: Customer = {
        id: Date.now().toString(),
        name: newCustomer.name!,
        phone: newCustomer.phone!,
        email: newCustomer.email,
        address: newCustomer.address,
        creditLimit: newCustomer.creditLimit || 1000,
        currentBalance: 0,
        totalPurchases: 0
      };
      setCustomers([...customers, customer]);
      setNewCustomer({});
      setAddDialog(false);
    }
  };

  const editCustomer = () => {
    if (selectedCustomer) {
      setCustomers(customers.map(c => 
        c.id === selectedCustomer.id ? selectedCustomer : c
      ));
      setEditDialog(false);
      setSelectedCustomer(null);
    }
  };

  const deleteCustomer = (id: string) => {
    setCustomers(customers.filter(c => c.id !== id));
  };

  const processPayment = () => {
    if (selectedCustomer && paymentAmount) {
      const amount = Number(paymentAmount);
      const updatedCustomer = {
        ...selectedCustomer,
        currentBalance: Math.max(0, selectedCustomer.currentBalance - amount)
      };
      
      setCustomers(customers.map(c => 
        c.id === selectedCustomer.id ? updatedCustomer : c
      ));

      // Add transaction record
      const newTransaction: Transaction = {
        id: Date.now().toString(),
        customerId: selectedCustomer.id,
        type: 'payment',
        amount: -amount,
        date: new Date(),
        description: 'Payment received',
        balance: updatedCustomer.currentBalance
      };
      setTransactions([...transactions, newTransaction]);

      setPaymentDialog(false);
      setPaymentAmount('');
      setSelectedCustomer(null);
    }
  };

  const getCustomerTransactions = (customerId: string) => {
    return transactions.filter(t => t.customerId === customerId);
  };

  const getCreditStatus = (customer: Customer) => {
    const utilization = (customer.currentBalance / customer.creditLimit) * 100;
    if (utilization === 0) return { label: 'Clear', color: 'success' as const };
    if (utilization < 50) return { label: 'Good', color: 'info' as const };
    if (utilization < 80) return { label: 'Moderate', color: 'warning' as const };
    return { label: 'High', color: 'error' as const };
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Customer Management
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="All Customers" />
          <Tab label={`Credit Customers (${creditCustomers.length})`} />
        </Tabs>
      </Box>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <TextField
                  placeholder="Search customers..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />
                  }}
                  sx={{ minWidth: 300 }}
                />
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setAddDialog(true)}
                >
                  Add Customer
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Customers Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {tabValue === 0 ? 'All Customers' : 'Credit Customers'} 
                ({tabValue === 0 ? filteredCustomers.length : creditCustomers.length})
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Phone</TableCell>
                      <TableCell align="right">Credit Limit</TableCell>
                      <TableCell align="right">Current Balance</TableCell>
                      <TableCell align="right">Total Purchases</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(tabValue === 0 ? filteredCustomers : creditCustomers.filter(c => 
                      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      c.phone.includes(searchTerm)
                    )).map((customer) => {
                      const status = getCreditStatus(customer);
                      return (
                        <TableRow key={customer.id}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {customer.name}
                              </Typography>
                              {customer.email && (
                                <Typography variant="caption" color="text.secondary">
                                  {customer.email}
                                </Typography>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>{customer.phone}</TableCell>
                          <TableCell align="right">₹{customer.creditLimit}</TableCell>
                          <TableCell align="right">
                            <Typography 
                              color={customer.currentBalance > 0 ? 'error.main' : 'text.primary'}
                              fontWeight={customer.currentBalance > 0 ? 'bold' : 'normal'}
                            >
                              ₹{customer.currentBalance}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">₹{customer.totalPurchases}</TableCell>
                          <TableCell align="center">
                            <Chip
                              label={status.label}
                              color={status.color}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedCustomer(customer);
                                setHistoryDialog(true);
                              }}
                              title="View History"
                            >
                              <HistoryIcon />
                            </IconButton>
                            {customer.currentBalance > 0 && (
                              <IconButton
                                size="small"
                                color="success"
                                onClick={() => {
                                  setSelectedCustomer(customer);
                                  setPaymentDialog(true);
                                }}
                                title="Receive Payment"
                              >
                                <PaymentIcon />
                              </IconButton>
                            )}
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedCustomer(customer);
                                setEditDialog(true);
                              }}
                            >
                              <EditIcon />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => deleteCustomer(customer.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add Customer Dialog */}
      <Dialog open={addDialog} onClose={() => setAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Customer</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Customer Name *"
              value={newCustomer.name || ''}
              onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Phone Number *"
              value={newCustomer.phone || ''}
              onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
            />
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={newCustomer.email || ''}
              onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
            />
            <TextField
              fullWidth
              label="Address"
              multiline
              rows={2}
              value={newCustomer.address || ''}
              onChange={(e) => setNewCustomer({ ...newCustomer, address: e.target.value })}
            />
            <TextField
              fullWidth
              type="number"
              label="Credit Limit"
              value={newCustomer.creditLimit || ''}
              onChange={(e) => setNewCustomer({ ...newCustomer, creditLimit: Number(e.target.value) })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialog(false)}>Cancel</Button>
          <Button onClick={addCustomer} variant="contained">Add Customer</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Customer Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Customer</DialogTitle>
        <DialogContent>
          {selectedCustomer && (
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Customer Name"
                value={selectedCustomer.name}
                onChange={(e) => setSelectedCustomer({ ...selectedCustomer, name: e.target.value })}
              />
              <TextField
                fullWidth
                label="Phone Number"
                value={selectedCustomer.phone}
                onChange={(e) => setSelectedCustomer({ ...selectedCustomer, phone: e.target.value })}
              />
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={selectedCustomer.email || ''}
                onChange={(e) => setSelectedCustomer({ ...selectedCustomer, email: e.target.value })}
              />
              <TextField
                fullWidth
                label="Address"
                multiline
                rows={2}
                value={selectedCustomer.address || ''}
                onChange={(e) => setSelectedCustomer({ ...selectedCustomer, address: e.target.value })}
              />
              <TextField
                fullWidth
                type="number"
                label="Credit Limit"
                value={selectedCustomer.creditLimit}
                onChange={(e) => setSelectedCustomer({ ...selectedCustomer, creditLimit: Number(e.target.value) })}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={editCustomer} variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={paymentDialog} onClose={() => setPaymentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Receive Payment</DialogTitle>
        <DialogContent>
          {selectedCustomer && (
            <Box sx={{ pt: 1 }}>
              <Typography variant="h6" gutterBottom>
                Customer: {selectedCustomer.name}
              </Typography>
              <Typography variant="body1" gutterBottom>
                Outstanding Balance: ₹{selectedCustomer.currentBalance}
              </Typography>
              <TextField
                fullWidth
                type="number"
                label="Payment Amount"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                inputProps={{ max: selectedCustomer.currentBalance }}
                sx={{ mt: 2 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPaymentDialog(false)}>Cancel</Button>
          <Button 
            onClick={processPayment} 
            variant="contained"
            disabled={!paymentAmount || Number(paymentAmount) <= 0}
          >
            Receive Payment
          </Button>
        </DialogActions>
      </Dialog>

      {/* Transaction History Dialog */}
      <Dialog open={historyDialog} onClose={() => setHistoryDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Transaction History</DialogTitle>
        <DialogContent>
          {selectedCustomer && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedCustomer.name} - Transaction History
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell align="right">Balance</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {getCustomerTransactions(selectedCustomer.id).map((transaction) => (
                      <TableRow key={transaction.id}>
                        <TableCell>{transaction.date.toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Chip
                            label={transaction.type}
                            color={transaction.type === 'sale' ? 'error' : 'success'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{transaction.description}</TableCell>
                        <TableCell align="right">
                          <Typography color={transaction.amount > 0 ? 'error.main' : 'success.main'}>
                            {transaction.amount > 0 ? '+' : ''}₹{Math.abs(transaction.amount)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">₹{transaction.balance}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KiranaCustomers;