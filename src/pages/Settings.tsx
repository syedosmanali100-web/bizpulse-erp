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
  Switch,
  FormControlLabel,
  Divider,
  AppBar,
  Toolbar,
  IconButton,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Home as HomeIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

interface TaxRate {
  id: string;
  name: string;
  rate: number;
  category: string;
  isActive: boolean;
}

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [saveDialog, setSaveDialog] = useState(false);

  // Business Settings
  const [businessSettings, setBusinessSettings] = useState({
    businessName: 'My Business',
    address: '123 Main Street, City, State - 123456',
    phone: '+91 9876543210',
    email: 'business@example.com',
    gstNumber: '22AAAAA0000A1Z5',
    logo: '',
    receiptFooter: 'Thank you for your business!'
  });

  // Tax Settings
  const [taxRates, setTaxRates] = useState<TaxRate[]>([
    { id: '1', name: 'CGST', rate: 9, category: 'GST', isActive: true },
    { id: '2', name: 'SGST', rate: 9, category: 'GST', isActive: true },
    { id: '3', name: 'IGST', rate: 18, category: 'GST', isActive: true },
    { id: '4', name: 'Service Charge', rate: 10, category: 'Service', isActive: true }
  ]);

  // System Settings
  const [systemSettings, setSystemSettings] = useState({
    autoBackup: true,
    backupFrequency: 'daily',
    lowStockAlert: true,
    lowStockThreshold: 10,
    printReceipt: true,
    emailReceipt: false,
    smsNotifications: true,
    soundAlerts: true
  });

  // Hotel Specific Settings
  const [hotelSettings, setHotelSettings] = useState({
    checkInTime: '14:00',
    checkOutTime: '11:00',
    gracePeriod: 30,
    lateCheckoutCharge: 500,
    cancellationPolicy: '24 hours before check-in',
    defaultRoomRates: {
      standard: 2000,
      deluxe: 3000,
      suite: 5000,
      executive: 4000
    }
  });

  const [newTaxRate, setNewTaxRate] = useState({
    name: '',
    rate: 0,
    category: 'GST'
  });

  const [taxDialog, setTaxDialog] = useState(false);

  const handleSaveSettings = () => {
    // Save settings logic here
    setSaveDialog(true);
    setTimeout(() => setSaveDialog(false), 2000);
  };

  const addTaxRate = () => {
    if (newTaxRate.name && newTaxRate.rate) {
      const taxRate: TaxRate = {
        id: Date.now().toString(),
        name: newTaxRate.name,
        rate: newTaxRate.rate,
        category: newTaxRate.category,
        isActive: true
      };
      setTaxRates([...taxRates, taxRate]);
      setNewTaxRate({ name: '', rate: 0, category: 'GST' });
      setTaxDialog(false);
    }
  };

  const deleteTaxRate = (id: string) => {
    setTaxRates(taxRates.filter(tax => tax.id !== id));
  };

  const toggleTaxRate = (id: string) => {
    setTaxRates(taxRates.map(tax => 
      tax.id === id ? { ...tax, isActive: !tax.isActive } : tax
    ));
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
            Settings
          </Typography>
          <Button
            color="inherit"
            startIcon={<SaveIcon />}
            onClick={handleSaveSettings}
          >
            Save All
          </Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 3, flexGrow: 1 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
          <Tab label="Business Info" />
          <Tab label="Tax Settings" />
          <Tab label="System Settings" />
          <Tab label="Hotel Settings" />
        </Tabs>

        {/* Business Information Tab */}
        {tabValue === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Business Information</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      fullWidth
                      label="Business Name"
                      value={businessSettings.businessName}
                      onChange={(e) => setBusinessSettings({ ...businessSettings, businessName: e.target.value })}
                    />
                    <TextField
                      fullWidth
                      label="Address"
                      multiline
                      rows={3}
                      value={businessSettings.address}
                      onChange={(e) => setBusinessSettings({ ...businessSettings, address: e.target.value })}
                    />
                    <TextField
                      fullWidth
                      label="Phone Number"
                      value={businessSettings.phone}
                      onChange={(e) => setBusinessSettings({ ...businessSettings, phone: e.target.value })}
                    />
                    <TextField
                      fullWidth
                      label="Email"
                      type="email"
                      value={businessSettings.email}
                      onChange={(e) => setBusinessSettings({ ...businessSettings, email: e.target.value })}
                    />
                    <TextField
                      fullWidth
                      label="GST Number"
                      value={businessSettings.gstNumber}
                      onChange={(e) => setBusinessSettings({ ...businessSettings, gstNumber: e.target.value })}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Receipt Settings</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      fullWidth
                      label="Logo URL"
                      value={businessSettings.logo}
                      onChange={(e) => setBusinessSettings({ ...businessSettings, logo: e.target.value })}
                      placeholder="https://example.com/logo.png"
                    />
                    <TextField
                      fullWidth
                      label="Receipt Footer"
                      multiline
                      rows={3}
                      value={businessSettings.receiptFooter}
                      onChange={(e) => setBusinessSettings({ ...businessSettings, receiptFooter: e.target.value })}
                    />
                    <Button variant="outlined" component="label">
                      Upload Logo
                      <input type="file" hidden accept="image/*" />
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Tax Settings Tab */}
        {tabValue === 1 && (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">Tax Rates</Typography>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => setTaxDialog(true)}
                    >
                      Add Tax Rate
                    </Button>
                  </Box>

                  <TableContainer component={Paper} variant="outlined">
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Tax Name</TableCell>
                          <TableCell>Category</TableCell>
                          <TableCell align="right">Rate (%)</TableCell>
                          <TableCell align="center">Status</TableCell>
                          <TableCell align="center">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {taxRates.map((tax) => (
                          <TableRow key={tax.id}>
                            <TableCell>{tax.name}</TableCell>
                            <TableCell>{tax.category}</TableCell>
                            <TableCell align="right">{tax.rate}%</TableCell>
                            <TableCell align="center">
                              <Switch
                                checked={tax.isActive}
                                onChange={() => toggleTaxRate(tax.id)}
                                size="small"
                              />
                            </TableCell>
                            <TableCell align="center">
                              <IconButton size="small">
                                <EditIcon />
                              </IconButton>
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => deleteTaxRate(tax.id)}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* System Settings Tab */}
        {tabValue === 2 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Backup Settings</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={systemSettings.autoBackup}
                          onChange={(e) => setSystemSettings({ ...systemSettings, autoBackup: e.target.checked })}
                        />
                      }
                      label="Enable Auto Backup"
                    />
                    <TextField
                      fullWidth
                      label="Backup Frequency"
                      select
                      value={systemSettings.backupFrequency}
                      onChange={(e) => setSystemSettings({ ...systemSettings, backupFrequency: e.target.value })}
                      SelectProps={{ native: true }}
                    >
                      <option value="hourly">Hourly</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                    </TextField>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="h6" gutterBottom>Inventory Alerts</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={systemSettings.lowStockAlert}
                          onChange={(e) => setSystemSettings({ ...systemSettings, lowStockAlert: e.target.checked })}
                        />
                      }
                      label="Low Stock Alerts"
                    />
                    <TextField
                      fullWidth
                      type="number"
                      label="Low Stock Threshold"
                      value={systemSettings.lowStockThreshold}
                      onChange={(e) => setSystemSettings({ ...systemSettings, lowStockThreshold: Number(e.target.value) })}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Receipt & Notifications</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={systemSettings.printReceipt}
                          onChange={(e) => setSystemSettings({ ...systemSettings, printReceipt: e.target.checked })}
                        />
                      }
                      label="Auto Print Receipt"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={systemSettings.emailReceipt}
                          onChange={(e) => setSystemSettings({ ...systemSettings, emailReceipt: e.target.checked })}
                        />
                      }
                      label="Email Receipt"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={systemSettings.smsNotifications}
                          onChange={(e) => setSystemSettings({ ...systemSettings, smsNotifications: e.target.checked })}
                        />
                      }
                      label="SMS Notifications"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={systemSettings.soundAlerts}
                          onChange={(e) => setSystemSettings({ ...systemSettings, soundAlerts: e.target.checked })}
                        />
                      }
                      label="Sound Alerts"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Hotel Settings Tab */}
        {tabValue === 3 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Check-in/Check-out</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      fullWidth
                      type="time"
                      label="Check-in Time"
                      value={hotelSettings.checkInTime}
                      onChange={(e) => setHotelSettings({ ...hotelSettings, checkInTime: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      fullWidth
                      type="time"
                      label="Check-out Time"
                      value={hotelSettings.checkOutTime}
                      onChange={(e) => setHotelSettings({ ...hotelSettings, checkOutTime: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      fullWidth
                      type="number"
                      label="Grace Period (minutes)"
                      value={hotelSettings.gracePeriod}
                      onChange={(e) => setHotelSettings({ ...hotelSettings, gracePeriod: Number(e.target.value) })}
                    />
                    <TextField
                      fullWidth
                      type="number"
                      label="Late Checkout Charge (₹)"
                      value={hotelSettings.lateCheckoutCharge}
                      onChange={(e) => setHotelSettings({ ...hotelSettings, lateCheckoutCharge: Number(e.target.value) })}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Room Rates</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Standard Room (₹)"
                      value={hotelSettings.defaultRoomRates.standard}
                      onChange={(e) => setHotelSettings({ 
                        ...hotelSettings, 
                        defaultRoomRates: { 
                          ...hotelSettings.defaultRoomRates, 
                          standard: Number(e.target.value) 
                        }
                      })}
                    />
                    <TextField
                      fullWidth
                      type="number"
                      label="Deluxe Room (₹)"
                      value={hotelSettings.defaultRoomRates.deluxe}
                      onChange={(e) => setHotelSettings({ 
                        ...hotelSettings, 
                        defaultRoomRates: { 
                          ...hotelSettings.defaultRoomRates, 
                          deluxe: Number(e.target.value) 
                        }
                      })}
                    />
                    <TextField
                      fullWidth
                      type="number"
                      label="Suite (₹)"
                      value={hotelSettings.defaultRoomRates.suite}
                      onChange={(e) => setHotelSettings({ 
                        ...hotelSettings, 
                        defaultRoomRates: { 
                          ...hotelSettings.defaultRoomRates, 
                          suite: Number(e.target.value) 
                        }
                      })}
                    />
                    <TextField
                      fullWidth
                      type="number"
                      label="Executive Room (₹)"
                      value={hotelSettings.defaultRoomRates.executive}
                      onChange={(e) => setHotelSettings({ 
                        ...hotelSettings, 
                        defaultRoomRates: { 
                          ...hotelSettings.defaultRoomRates, 
                          executive: Number(e.target.value) 
                        }
                      })}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Policies</Typography>
                  <TextField
                    fullWidth
                    label="Cancellation Policy"
                    multiline
                    rows={3}
                    value={hotelSettings.cancellationPolicy}
                    onChange={(e) => setHotelSettings({ ...hotelSettings, cancellationPolicy: e.target.value })}
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Box>

      {/* Add Tax Rate Dialog */}
      <Dialog open={taxDialog} onClose={() => setTaxDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Tax Rate</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Tax Name"
              value={newTaxRate.name}
              onChange={(e) => setNewTaxRate({ ...newTaxRate, name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Category"
              select
              value={newTaxRate.category}
              onChange={(e) => setNewTaxRate({ ...newTaxRate, category: e.target.value })}
              SelectProps={{ native: true }}
            >
              <option value="GST">GST</option>
              <option value="Service">Service</option>
              <option value="Other">Other</option>
            </TextField>
            <TextField
              fullWidth
              type="number"
              label="Rate (%)"
              value={newTaxRate.rate}
              onChange={(e) => setNewTaxRate({ ...newTaxRate, rate: Number(e.target.value) })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTaxDialog(false)}>Cancel</Button>
          <Button onClick={addTaxRate} variant="contained">Add Tax Rate</Button>
        </DialogActions>
      </Dialog>

      {/* Save Confirmation Dialog */}
      <Dialog open={saveDialog} onClose={() => setSaveDialog(false)}>
        <DialogContent>
          <Typography>Settings saved successfully!</Typography>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default Settings;