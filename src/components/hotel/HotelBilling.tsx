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
  Autocomplete
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Payment as PaymentIcon,
  Print as PrintIcon,
  Receipt as ReceiptIcon
} from '@mui/icons-material';

interface BillItem {
  id: string;
  type: 'room' | 'service';
  description: string;
  quantity: number;
  rate: number;
  total: number;
  date: Date;
}

interface Guest {
  id: string;
  name: string;
  roomNumber: string;
  checkInDate: Date;
  checkOutDate: Date;
}

const HotelBilling: React.FC = () => {
  const [selectedGuest, setSelectedGuest] = useState<Guest | null>(null);
  const [billItems, setBillItems] = useState<BillItem[]>([]);
  const [serviceDialog, setServiceDialog] = useState(false);
  const [paymentDialog, setPaymentDialog] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [amountReceived, setAmountReceived] = useState('');

  // Mock data
  const currentGuests: Guest[] = [
    {
      id: '1',
      name: 'John Smith',
      roomNumber: '101',
      checkInDate: new Date('2024-01-15'),
      checkOutDate: new Date('2024-01-17')
    },
    {
      id: '2',
      name: 'Emily Davis',
      roomNumber: '102',
      checkInDate: new Date('2024-01-13'),
      checkOutDate: new Date('2024-01-16')
    }
  ];

  const hotelServices = [
    { id: '1', name: 'Room Service - Breakfast', rate: 500, category: 'Food' },
    { id: '2', name: 'Room Service - Lunch', rate: 800, category: 'Food' },
    { id: '3', name: 'Room Service - Dinner', rate: 1000, category: 'Food' },
    { id: '4', name: 'Laundry Service', rate: 200, category: 'Laundry' },
    { id: '5', name: 'Spa Treatment', rate: 2000, category: 'Spa' },
    { id: '6', name: 'Airport Transfer', rate: 1500, category: 'Transport' },
    { id: '7', name: 'Extra Towels', rate: 100, category: 'Amenities' },
    { id: '8', name: 'Minibar Items', rate: 300, category: 'Minibar' }
  ];

  const [newService, setNewService] = useState({
    serviceId: '',
    quantity: 1,
    customRate: ''
  });

  const loadGuestBill = (guest: Guest) => {
    setSelectedGuest(guest);
    
    // Calculate room charges
    const nights = Math.ceil((guest.checkOutDate.getTime() - guest.checkInDate.getTime()) / (1000 * 60 * 60 * 24));
    const roomRate = 3000; // Base room rate
    
    const roomCharges: BillItem = {
      id: 'room-charges',
      type: 'room',
      description: `Room ${guest.roomNumber} - ${nights} nights`,
      quantity: nights,
      rate: roomRate,
      total: nights * roomRate,
      date: guest.checkInDate
    };

    // Mock some services for demo
    const mockServices: BillItem[] = [
      {
        id: '1',
        type: 'service',
        description: 'Room Service - Breakfast',
        quantity: 2,
        rate: 500,
        total: 1000,
        date: new Date('2024-01-15')
      },
      {
        id: '2',
        type: 'service',
        description: 'Laundry Service',
        quantity: 1,
        rate: 200,
        total: 200,
        date: new Date('2024-01-16')
      }
    ];

    setBillItems([roomCharges, ...mockServices]);
  };

  const addService = () => {
    if (newService.serviceId && selectedGuest) {
      const service = hotelServices.find(s => s.id === newService.serviceId);
      if (service) {
        const rate = newService.customRate ? Number(newService.customRate) : service.rate;
        const newItem: BillItem = {
          id: Date.now().toString(),
          type: 'service',
          description: service.name,
          quantity: newService.quantity,
          rate: rate,
          total: rate * newService.quantity,
          date: new Date()
        };
        setBillItems([...billItems, newItem]);
        setNewService({ serviceId: '', quantity: 1, customRate: '' });
        setServiceDialog(false);
      }
    }
  };

  const removeItem = (id: string) => {
    setBillItems(billItems.filter(item => item.id !== id));
  };

  const calculateSubtotal = () => {
    return billItems.reduce((sum, item) => sum + item.total, 0);
  };

  const calculateTax = () => {
    return calculateSubtotal() * 0.18; // 18% GST
  };

  const calculateServiceCharge = () => {
    const serviceItems = billItems.filter(item => item.type === 'service');
    const serviceTotal = serviceItems.reduce((sum, item) => sum + item.total, 0);
    return serviceTotal * 0.10; // 10% service charge on services
  };

  const calculateTotal = () => {
    return calculateSubtotal() + calculateTax() + calculateServiceCharge();
  };

  const processPayment = () => {
    alert('Payment processed successfully!');
    setBillItems([]);
    setSelectedGuest(null);
    setPaymentDialog(false);
    setAmountReceived('');
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Hotel Billing
      </Typography>

      <Grid container spacing={3}>
        {/* Guest Selection */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Select Guest
              </Typography>
              
              <Autocomplete
                options={currentGuests}
                getOptionLabel={(guest) => `${guest.name} - Room ${guest.roomNumber}`}
                value={selectedGuest}
                onChange={(event, newValue) => {
                  if (newValue) {
                    loadGuestBill(newValue);
                  }
                }}
                renderInput={(params) => (
                  <TextField {...params} label="Current Guests" fullWidth />
                )}
                sx={{ mb: 2 }}
              />

              {selectedGuest && (
                <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Guest Details
                  </Typography>
                  <Typography variant="body2">
                    Name: {selectedGuest.name}
                  </Typography>
                  <Typography variant="body2">
                    Room: {selectedGuest.roomNumber}
                  </Typography>
                  <Typography variant="body2">
                    Check-in: {selectedGuest.checkInDate.toLocaleDateString()}
                  </Typography>
                  <Typography variant="body2">
                    Check-out: {selectedGuest.checkOutDate.toLocaleDateString()}
                  </Typography>
                </Box>
              )}

              {selectedGuest && (
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => setServiceDialog(true)}
                  sx={{ mt: 2 }}
                >
                  Add Service
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Bill Details */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Bill Details
                {selectedGuest && ` - ${selectedGuest.name}`}
              </Typography>

              {!selectedGuest ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="text.secondary">
                    Please select a guest to view their bill
                  </Typography>
                </Box>
              ) : (
                <>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Description</TableCell>
                          <TableCell>Date</TableCell>
                          <TableCell align="right">Qty</TableCell>
                          <TableCell align="right">Rate</TableCell>
                          <TableCell align="right">Total</TableCell>
                          <TableCell align="center">Action</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {billItems.map((item) => (
                          <TableRow key={item.id}>
                            <TableCell>
                              <Box>
                                <Typography variant="body2">
                                  {item.description}
                                </Typography>
                                <Chip
                                  label={item.type}
                                  size="small"
                                  color={item.type === 'room' ? 'primary' : 'secondary'}
                                />
                              </Box>
                            </TableCell>
                            <TableCell>{item.date.toLocaleDateString()}</TableCell>
                            <TableCell align="right">{item.quantity}</TableCell>
                            <TableCell align="right">₹{item.rate}</TableCell>
                            <TableCell align="right">₹{item.total}</TableCell>
                            <TableCell align="center">
                              {item.type === 'service' && (
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => removeItem(item.id)}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Bill Summary */}
                  <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2">
                          Subtotal: ₹{calculateSubtotal().toFixed(2)}
                        </Typography>
                        <Typography variant="body2">
                          Service Charge (10%): ₹{calculateServiceCharge().toFixed(2)}
                        </Typography>
                        <Typography variant="body2">
                          Tax (18%): ₹{calculateTax().toFixed(2)}
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', mt: 1 }}>
                          Total: ₹{calculateTotal().toFixed(2)}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sx={{ textAlign: 'right' }}>
                        <Button
                          variant="contained"
                          color="success"
                          startIcon={<PaymentIcon />}
                          onClick={() => setPaymentDialog(true)}
                          sx={{ mr: 1, mb: 1 }}
                        >
                          Process Payment
                        </Button>
                        <Button
                          variant="outlined"
                          startIcon={<PrintIcon />}
                          sx={{ mb: 1 }}
                        >
                          Print Bill
                        </Button>
                        <Button
                          variant="outlined"
                          startIcon={<ReceiptIcon />}
                          fullWidth
                        >
                          Generate Invoice
                        </Button>
                      </Grid>
                    </Grid>
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add Service Dialog */}
      <Dialog open={serviceDialog} onClose={() => setServiceDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Service</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Autocomplete
              options={hotelServices}
              getOptionLabel={(service) => `${service.name} - ₹${service.rate}`}
              groupBy={(service) => service.category}
              onChange={(event, newValue) => {
                setNewService({ ...newService, serviceId: newValue?.id || '' });
              }}
              renderInput={(params) => (
                <TextField {...params} label="Select Service" fullWidth />
              )}
            />
            
            <TextField
              fullWidth
              type="number"
              label="Quantity"
              value={newService.quantity}
              onChange={(e) => setNewService({ ...newService, quantity: Number(e.target.value) })}
              inputProps={{ min: 1 }}
            />
            
            <TextField
              fullWidth
              type="number"
              label="Custom Rate (Optional)"
              value={newService.customRate}
              onChange={(e) => setNewService({ ...newService, customRate: e.target.value })}
              placeholder="Leave empty to use default rate"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setServiceDialog(false)}>Cancel</Button>
          <Button 
            onClick={addService} 
            variant="contained"
            disabled={!newService.serviceId}
          >
            Add Service
          </Button>
        </DialogActions>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={paymentDialog} onClose={() => setPaymentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Process Payment</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Typography variant="h6" gutterBottom>
              Total Amount: ₹{calculateTotal().toFixed(2)}
            </Typography>
            
            <TextField
              fullWidth
              label="Payment Method"
              select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              SelectProps={{ native: true }}
              sx={{ mb: 2 }}
            >
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="upi">UPI</option>
              <option value="bank-transfer">Bank Transfer</option>
            </TextField>

            <TextField
              fullWidth
              type="number"
              label="Amount Received"
              value={amountReceived}
              onChange={(e) => setAmountReceived(e.target.value)}
              sx={{ mb: 2 }}
            />

            {amountReceived && Number(amountReceived) > calculateTotal() && (
              <Typography variant="body2" color="success.main">
                Change: ₹{(Number(amountReceived) - calculateTotal()).toFixed(2)}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPaymentDialog(false)}>Cancel</Button>
          <Button 
            onClick={processPayment} 
            variant="contained"
            disabled={!amountReceived || Number(amountReceived) < calculateTotal()}
          >
            Complete Payment
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HotelBilling;