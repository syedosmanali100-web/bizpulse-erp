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
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  QrCodeScanner as ScanIcon,
  Payment as PaymentIcon,
  Print as PrintIcon,
  Person as CustomerIcon
} from '@mui/icons-material';

interface BillItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  total: number;
}

const KiranaBilling: React.FC = () => {
  const [billItems, setBillItems] = useState<BillItem[]>([]);
  const [productCode, setProductCode] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [customerName, setCustomerName] = useState('');
  const [paymentDialog, setPaymentDialog] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [amountReceived, setAmountReceived] = useState('');

  // Mock product data
  const products = {
    '001': { name: 'Rice 1kg', price: 80 },
    '002': { name: 'Dal 500g', price: 120 },
    '003': { name: 'Oil 1L', price: 150 },
    '004': { name: 'Sugar 1kg', price: 45 },
    '005': { name: 'Tea 250g', price: 200 }
  };

  const addItem = () => {
    if (productCode && products[productCode as keyof typeof products]) {
      const product = products[productCode as keyof typeof products];
      const newItem: BillItem = {
        id: Date.now().toString(),
        name: product.name,
        price: product.price,
        quantity: quantity,
        total: product.price * quantity
      };
      setBillItems([...billItems, newItem]);
      setProductCode('');
      setQuantity(1);
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

  const calculateTotal = () => {
    return calculateSubtotal() + calculateTax();
  };

  const handlePayment = () => {
    setPaymentDialog(true);
  };

  const processPayment = () => {
    // Process payment logic here
    alert('Payment processed successfully!');
    setBillItems([]);
    setCustomerName('');
    setPaymentDialog(false);
    setAmountReceived('');
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Quick Billing
      </Typography>

      <Grid container spacing={3}>
        {/* Product Entry Section */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Add Products
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  label="Product Code / Barcode"
                  value={productCode}
                  onChange={(e) => setProductCode(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addItem()}
                  InputProps={{
                    endAdornment: (
                      <IconButton>
                        <ScanIcon />
                      </IconButton>
                    )
                  }}
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  type="number"
                  label="Quantity"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  inputProps={{ min: 1 }}
                />
              </Box>

              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                onClick={addItem}
                sx={{ mb: 2 }}
              >
                Add Item
              </Button>

              <Divider sx={{ my: 2 }} />

              <TextField
                fullWidth
                label="Customer Name (Optional)"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                InputProps={{
                  startAdornment: <CustomerIcon sx={{ mr: 1, color: 'action.active' }} />
                }}
              />

              {/* Quick Add Buttons */}
              <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                Quick Add:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(products).map(([code, product]) => (
                  <Chip
                    key={code}
                    label={product.name}
                    onClick={() => {
                      setProductCode(code);
                      addItem();
                    }}
                    variant="outlined"
                    size="small"
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Bill Items Section */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Current Bill
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Item</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell align="right">Qty</TableCell>
                      <TableCell align="right">Total</TableCell>
                      <TableCell align="center">Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {billItems.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.name}</TableCell>
                        <TableCell align="right">₹{item.price}</TableCell>
                        <TableCell align="right">{item.quantity}</TableCell>
                        <TableCell align="right">₹{item.total}</TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => removeItem(item.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                    {billItems.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                          No items added yet
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Bill Summary */}
              {billItems.length > 0 && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2">
                        Subtotal: ₹{calculateSubtotal().toFixed(2)}
                      </Typography>
                      <Typography variant="body2">
                        Tax (18%): ₹{calculateTax().toFixed(2)}
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        Total: ₹{calculateTotal().toFixed(2)}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sx={{ textAlign: 'right' }}>
                      <Button
                        variant="contained"
                        color="success"
                        startIcon={<PaymentIcon />}
                        onClick={handlePayment}
                        sx={{ mr: 1 }}
                      >
                        Process Payment
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<PrintIcon />}
                      >
                        Print Bill
                      </Button>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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
              <option value="credit">Credit</option>
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

export default KiranaBilling;