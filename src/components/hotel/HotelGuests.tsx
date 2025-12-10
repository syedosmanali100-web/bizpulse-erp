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
  CheckCircle as CheckInIcon,
  ExitToApp as CheckOutIcon,
  Receipt as BillIcon,
  Search as SearchIcon
} from '@mui/icons-material';

interface Guest {
  id: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
  idProof: string;
  roomNumber?: string;
  roomType?: string;
  checkInDate?: Date;
  checkOutDate?: Date;
  guestCount: number;
  status: 'booked' | 'checked-in' | 'checked-out';
  totalBill: number;
  paidAmount: number;
}

const HotelGuests: React.FC = () => {
  const [guests, setGuests] = useState<Guest[]>([
    {
      id: '1',
      name: 'John Smith',
      phone: '9876543210',
      email: 'john@email.com',
      address: '123 Main St, City',
      idProof: 'AADHAR123456789',
      roomNumber: '101',
      roomType: 'Deluxe',
      checkInDate: new Date('2024-01-15'),
      checkOutDate: new Date('2024-01-17'),
      guestCount: 2,
      status: 'checked-in',
      totalBill: 8000,
      paidAmount: 0
    },
    {
      id: '2',
      name: 'Sarah Johnson',
      phone: '9876543211',
      email: 'sarah@email.com',
      idProof: 'PASSPORT987654321',
      roomNumber: '205',
      roomType: 'Suite',
      checkInDate: new Date('2024-01-14'),
      checkOutDate: new Date('2024-01-15'),
      guestCount: 1,
      status: 'checked-out',
      totalBill: 12000,
      paidAmount: 12000
    }
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [checkInDialog, setCheckInDialog] = useState(false);
  const [checkOutDialog, setCheckOutDialog] = useState(false);
  const [addGuestDialog, setAddGuestDialog] = useState(false);
  const [selectedGuest, setSelectedGuest] = useState<Guest | null>(null);
  const [tabValue, setTabValue] = useState(0);

  const [newGuest, setNewGuest] = useState<Partial<Guest>>({
    name: '',
    phone: '',
    email: '',
    address: '',
    idProof: '',
    guestCount: 1,
    status: 'booked'
  });

  const [checkInData, setCheckInData] = useState({
    roomNumber: '',
    roomType: 'Standard',
    checkInDate: new Date().toISOString().split('T')[0],
    checkOutDate: '',
    roomRate: 2000
  });

  const filteredGuests = guests.filter(guest => {
    const matchesSearch = guest.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         guest.phone.includes(searchTerm) ||
                         (guest.roomNumber && guest.roomNumber.includes(searchTerm));
    
    if (tabValue === 0) return matchesSearch; // All guests
    if (tabValue === 1) return matchesSearch && guest.status === 'checked-in'; // Current guests
    if (tabValue === 2) return matchesSearch && guest.status === 'booked'; // Bookings
    return matchesSearch;
  });

  const addGuest = () => {
    if (newGuest.name && newGuest.phone && newGuest.idProof) {
      const guest: Guest = {
        id: Date.now().toString(),
        name: newGuest.name!,
        phone: newGuest.phone!,
        email: newGuest.email,
        address: newGuest.address,
        idProof: newGuest.idProof!,
        guestCount: newGuest.guestCount || 1,
        status: 'booked',
        totalBill: 0,
        paidAmount: 0
      };
      setGuests([...guests, guest]);
      setNewGuest({});
      setAddGuestDialog(false);
    }
  };

  const processCheckIn = () => {
    if (selectedGuest && checkInData.roomNumber && checkInData.checkOutDate) {
      const nights = Math.ceil((new Date(checkInData.checkOutDate).getTime() - new Date(checkInData.checkInDate).getTime()) / (1000 * 60 * 60 * 24));
      const roomCharges = nights * checkInData.roomRate;
      
      const updatedGuest = {
        ...selectedGuest,
        roomNumber: checkInData.roomNumber,
        roomType: checkInData.roomType,
        checkInDate: new Date(checkInData.checkInDate),
        checkOutDate: new Date(checkInData.checkOutDate),
        status: 'checked-in' as const,
        totalBill: roomCharges
      };
      
      setGuests(guests.map(g => g.id === selectedGuest.id ? updatedGuest : g));
      setCheckInDialog(false);
      setSelectedGuest(null);
    }
  };

  const processCheckOut = () => {
    if (selectedGuest) {
      const updatedGuest = {
        ...selectedGuest,
        status: 'checked-out' as const,
        paidAmount: selectedGuest.totalBill
      };
      
      setGuests(guests.map(g => g.id === selectedGuest.id ? updatedGuest : g));
      setCheckOutDialog(false);
      setSelectedGuest(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'checked-in': return 'success';
      case 'checked-out': return 'info';
      case 'booked': return 'warning';
      default: return 'default';
    }
  };

  const roomTypes = ['Standard', 'Deluxe', 'Suite', 'Executive'];
  const roomRates = { Standard: 2000, Deluxe: 3000, Suite: 5000, Executive: 4000 };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Guest Management
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="All Guests" />
          <Tab label="Current Guests" />
          <Tab label="Bookings" />
        </Tabs>
      </Box>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <TextField
                  placeholder="Search guests..."
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
                  onClick={() => setAddGuestDialog(true)}
                >
                  Add Guest
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Guests Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Guests ({filteredGuests.length})
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Guest Name</TableCell>
                      <TableCell>Phone</TableCell>
                      <TableCell>Room</TableCell>
                      <TableCell>Check-in</TableCell>
                      <TableCell>Check-out</TableCell>
                      <TableCell align="right">Bill Amount</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredGuests.map((guest) => (
                      <TableRow key={guest.id}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {guest.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Guests: {guest.guestCount} | ID: {guest.idProof}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>{guest.phone}</TableCell>
                        <TableCell>
                          {guest.roomNumber ? (
                            <Box>
                              <Typography variant="body2">{guest.roomNumber}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {guest.roomType}
                              </Typography>
                            </Box>
                          ) : '-'}
                        </TableCell>
                        <TableCell>
                          {guest.checkInDate ? guest.checkInDate.toLocaleDateString() : '-'}
                        </TableCell>
                        <TableCell>
                          {guest.checkOutDate ? guest.checkOutDate.toLocaleDateString() : '-'}
                        </TableCell>
                        <TableCell align="right">
                          <Typography>₹{guest.totalBill}</Typography>
                          {guest.paidAmount > 0 && (
                            <Typography variant="caption" color="success.main">
                              Paid: ₹{guest.paidAmount}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={guest.status}
                            color={getStatusColor(guest.status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="center">
                          {guest.status === 'booked' && (
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => {
                                setSelectedGuest(guest);
                                setCheckInDialog(true);
                              }}
                              title="Check In"
                            >
                              <CheckInIcon />
                            </IconButton>
                          )}
                          {guest.status === 'checked-in' && (
                            <>
                              <IconButton
                                size="small"
                                color="primary"
                                title="View Bill"
                              >
                                <BillIcon />
                              </IconButton>
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => {
                                  setSelectedGuest(guest);
                                  setCheckOutDialog(true);
                                }}
                                title="Check Out"
                              >
                                <CheckOutIcon />
                              </IconButton>
                            </>
                          )}
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedGuest(guest);
                            }}
                          >
                            <EditIcon />
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

      {/* Add Guest Dialog */}
      <Dialog open={addGuestDialog} onClose={() => setAddGuestDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Guest</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Guest Name *"
              value={newGuest.name || ''}
              onChange={(e) => setNewGuest({ ...newGuest, name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Phone Number *"
              value={newGuest.phone || ''}
              onChange={(e) => setNewGuest({ ...newGuest, phone: e.target.value })}
            />
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={newGuest.email || ''}
              onChange={(e) => setNewGuest({ ...newGuest, email: e.target.value })}
            />
            <TextField
              fullWidth
              label="Address"
              multiline
              rows={2}
              value={newGuest.address || ''}
              onChange={(e) => setNewGuest({ ...newGuest, address: e.target.value })}
            />
            <TextField
              fullWidth
              label="ID Proof *"
              value={newGuest.idProof || ''}
              onChange={(e) => setNewGuest({ ...newGuest, idProof: e.target.value })}
              placeholder="Aadhar/Passport/License number"
            />
            <TextField
              fullWidth
              type="number"
              label="Number of Guests"
              value={newGuest.guestCount || ''}
              onChange={(e) => setNewGuest({ ...newGuest, guestCount: Number(e.target.value) })}
              inputProps={{ min: 1 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddGuestDialog(false)}>Cancel</Button>
          <Button onClick={addGuest} variant="contained">Add Guest</Button>
        </DialogActions>
      </Dialog>

      {/* Check In Dialog */}
      <Dialog open={checkInDialog} onClose={() => setCheckInDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Check In Guest</DialogTitle>
        <DialogContent>
          {selectedGuest && (
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Typography variant="h6">{selectedGuest.name}</Typography>
              <TextField
                fullWidth
                label="Room Number *"
                value={checkInData.roomNumber}
                onChange={(e) => setCheckInData({ ...checkInData, roomNumber: e.target.value })}
              />
              <TextField
                fullWidth
                label="Room Type"
                select
                value={checkInData.roomType}
                onChange={(e) => {
                  const roomType = e.target.value;
                  setCheckInData({ 
                    ...checkInData, 
                    roomType,
                    roomRate: roomRates[roomType as keyof typeof roomRates]
                  });
                }}
                SelectProps={{ native: true }}
              >
                {roomTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </TextField>
              <TextField
                fullWidth
                type="date"
                label="Check-in Date"
                value={checkInData.checkInDate}
                onChange={(e) => setCheckInData({ ...checkInData, checkInDate: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                type="date"
                label="Check-out Date *"
                value={checkInData.checkOutDate}
                onChange={(e) => setCheckInData({ ...checkInData, checkOutDate: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                type="number"
                label="Room Rate per Night"
                value={checkInData.roomRate}
                onChange={(e) => setCheckInData({ ...checkInData, roomRate: Number(e.target.value) })}
              />
              {checkInData.checkOutDate && (
                <Typography variant="body2" color="primary">
                  Total Room Charges: ₹{Math.ceil((new Date(checkInData.checkOutDate).getTime() - new Date(checkInData.checkInDate).getTime()) / (1000 * 60 * 60 * 24)) * checkInData.roomRate}
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCheckInDialog(false)}>Cancel</Button>
          <Button 
            onClick={processCheckIn} 
            variant="contained"
            disabled={!checkInData.roomNumber || !checkInData.checkOutDate}
          >
            Check In
          </Button>
        </DialogActions>
      </Dialog>

      {/* Check Out Dialog */}
      <Dialog open={checkOutDialog} onClose={() => setCheckOutDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Check Out Guest</DialogTitle>
        <DialogContent>
          {selectedGuest && (
            <Box sx={{ pt: 1 }}>
              <Typography variant="h6" gutterBottom>
                {selectedGuest.name} - Room {selectedGuest.roomNumber}
              </Typography>
              <Typography variant="body1" gutterBottom>
                Check-in: {selectedGuest.checkInDate?.toLocaleDateString()}
              </Typography>
              <Typography variant="body1" gutterBottom>
                Check-out: {selectedGuest.checkOutDate?.toLocaleDateString()}
              </Typography>
              <Typography variant="h6" color="primary" gutterBottom>
                Total Bill: ₹{selectedGuest.totalBill}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This will mark the guest as checked out and process payment.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCheckOutDialog(false)}>Cancel</Button>
          <Button onClick={processCheckOut} variant="contained" color="error">
            Check Out & Process Payment
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HotelGuests;