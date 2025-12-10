import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  Hotel as HotelIcon,
  People as PeopleIcon,
  AttachMoney as MoneyIcon,
  RoomService as ServiceIcon
} from '@mui/icons-material';

const HotelDashboard: React.FC = () => {
  // Mock data
  const stats = {
    totalRooms: 50,
    occupiedRooms: 35,
    availableRooms: 15,
    todayRevenue: 45000,
    monthlyRevenue: 1200000,
    checkInsToday: 8,
    checkOutsToday: 6
  };

  const recentGuests = [
    { id: '1', name: 'John Smith', room: '101', checkIn: '2024-01-15', status: 'checked-in' },
    { id: '2', name: 'Sarah Johnson', room: '205', checkIn: '2024-01-14', status: 'checked-out' },
    { id: '3', name: 'Mike Wilson', room: '303', checkIn: '2024-01-15', status: 'checked-in' },
    { id: '4', name: 'Emily Davis', room: '102', checkIn: '2024-01-13', status: 'checked-in' }
  ];

  const roomStatus = [
    { room: '101', type: 'Deluxe', status: 'occupied', guest: 'John Smith' },
    { room: '102', type: 'Standard', status: 'occupied', guest: 'Emily Davis' },
    { room: '103', type: 'Suite', status: 'available', guest: null },
    { room: '104', type: 'Standard', status: 'maintenance', guest: null },
    { room: '105', type: 'Deluxe', status: 'available', guest: null }
  ];

  const occupancyRate = (stats.occupiedRooms / stats.totalRooms) * 100;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'occupied': return 'error';
      case 'available': return 'success';
      case 'maintenance': return 'warning';
      default: return 'default';
    }
  };

  const getGuestStatusColor = (status: string) => {
    switch (status) {
      case 'checked-in': return 'success';
      case 'checked-out': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Hotel Dashboard
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <HotelIcon sx={{ fontSize: 40, color: '#1976d2', mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Room Occupancy
                  </Typography>
                  <Typography variant="h5">
                    {stats.occupiedRooms}/{stats.totalRooms}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={occupancyRate} 
                    sx={{ mt: 1 }}
                  />
                  <Typography variant="caption" color="textSecondary">
                    {occupancyRate.toFixed(1)}% occupied
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <PeopleIcon sx={{ fontSize: 40, color: '#388e3c', mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Today's Activity
                  </Typography>
                  <Typography variant="h5">
                    {stats.checkInsToday + stats.checkOutsToday}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {stats.checkInsToday} check-ins, {stats.checkOutsToday} check-outs
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <MoneyIcon sx={{ fontSize: 40, color: '#f57c00', mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Today's Revenue
                  </Typography>
                  <Typography variant="h5">
                    ₹{stats.todayRevenue.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Monthly: ₹{(stats.monthlyRevenue / 1000).toFixed(0)}K
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <ServiceIcon sx={{ fontSize: 40, color: '#7b1fa2', mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Available Rooms
                  </Typography>
                  <Typography variant="h5">
                    {stats.availableRooms}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Ready for booking
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Guests */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Guest Activity
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Guest Name</TableCell>
                      <TableCell>Room</TableCell>
                      <TableCell>Check-in</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentGuests.map((guest) => (
                      <TableRow key={guest.id}>
                        <TableCell>{guest.name}</TableCell>
                        <TableCell>{guest.room}</TableCell>
                        <TableCell>{new Date(guest.checkIn).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Chip
                            label={guest.status}
                            color={getGuestStatusColor(guest.status) as any}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Room Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Room Status Overview
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Room</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Guest</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {roomStatus.map((room) => (
                      <TableRow key={room.room}>
                        <TableCell>{room.room}</TableCell>
                        <TableCell>{room.type}</TableCell>
                        <TableCell>
                          <Chip
                            label={room.status}
                            color={getStatusColor(room.status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{room.guest || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HotelDashboard;