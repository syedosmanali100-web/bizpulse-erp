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
  Search as SearchIcon
} from '@mui/icons-material';

interface HotelService {
  id: string;
  name: string;
  category: 'Food' | 'Laundry' | 'Spa' | 'Transport' | 'Amenities' | 'Minibar' | 'Other';
  rate: number;
  description?: string;
  isActive: boolean;
  taxRate: number;
}

const HotelServices: React.FC = () => {
  const [services, setServices] = useState<HotelService[]>([
    { id: '1', name: 'Room Service - Breakfast', category: 'Food', rate: 500, description: 'Continental breakfast served in room', isActive: true, taxRate: 5 },
    { id: '2', name: 'Room Service - Lunch', category: 'Food', rate: 800, description: 'Full course lunch menu', isActive: true, taxRate: 5 },
    { id: '3', name: 'Room Service - Dinner', category: 'Food', rate: 1000, description: 'Premium dinner options', isActive: true, taxRate: 5 },
    { id: '4', name: 'Laundry Service', category: 'Laundry', rate: 200, description: 'Same day laundry service', isActive: true, taxRate: 18 },
    { id: '5', name: 'Dry Cleaning', category: 'Laundry', rate: 400, description: 'Professional dry cleaning', isActive: true, taxRate: 18 },
    { id: '6', name: 'Spa Treatment - Basic', category: 'Spa', rate: 2000, description: '60 minutes relaxation therapy', isActive: true, taxRate: 18 },
    { id: '7', name: 'Spa Treatment - Premium', category: 'Spa', rate: 3500, description: '90 minutes full body treatment', isActive: true, taxRate: 18 },
    { id: '8', name: 'Airport Transfer', category: 'Transport', rate: 1500, description: 'One way airport pickup/drop', isActive: true, taxRate: 5 },
    { id: '9', name: 'City Tour', category: 'Transport', rate: 2500, description: 'Half day city sightseeing', isActive: true, taxRate: 5 },
    { id: '10', name: 'Extra Towels', category: 'Amenities', rate: 100, description: 'Additional towel set', isActive: true, taxRate: 18 },
    { id: '11', name: 'Extra Pillows', category: 'Amenities', rate: 150, description: 'Additional pillow set', isActive: true, taxRate: 18 },
    { id: '12', name: 'Minibar - Soft Drinks', category: 'Minibar', rate: 100, description: 'Assorted soft drinks', isActive: true, taxRate: 12 },
    { id: '13', name: 'Minibar - Snacks', category: 'Minibar', rate: 200, description: 'Premium snack items', isActive: true, taxRate: 12 }
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [addDialog, setAddDialog] = useState(false);
  const [editDialog, setEditDialog] = useState(false);
  const [selectedService, setSelectedService] = useState<HotelService | null>(null);

  const [newService, setNewService] = useState<Partial<HotelService>>({
    name: '',
    category: 'Food',
    rate: 0,
    description: '',
    isActive: true,
    taxRate: 18
  });

  const categories = ['All', 'Food', 'Laundry', 'Spa', 'Transport', 'Amenities', 'Minibar', 'Other'];

  const filteredServices = services.filter(service => {
    const matchesSearch = service.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         service.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || service.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const addService = () => {
    if (newService.name && newService.rate) {
      const service: HotelService = {
        id: Date.now().toString(),
        name: newService.name!,
        category: newService.category as HotelService['category'],
        rate: newService.rate!,
        description: newService.description,
        isActive: newService.isActive ?? true,
        taxRate: newService.taxRate ?? 18
      };
      setServices([...services, service]);
      setNewService({});
      setAddDialog(false);
    }
  };

  const editService = () => {
    if (selectedService) {
      setServices(services.map(s => 
        s.id === selectedService.id ? selectedService : s
      ));
      setEditDialog(false);
      setSelectedService(null);
    }
  };

  const deleteService = (id: string) => {
    setServices(services.filter(s => s.id !== id));
  };

  const toggleServiceStatus = (id: string) => {
    setServices(services.map(s => 
      s.id === id ? { ...s, isActive: !s.isActive } : s
    ));
  };

  const getCategoryStats = () => {
    const stats: Record<string, number> = {};
    services.forEach(service => {
      stats[service.category] = (stats[service.category] || 0) + 1;
    });
    return stats;
  };

  const categoryStats = getCategoryStats();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Hotel Services Management
      </Typography>

      {/* Category Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(categoryStats).map(([category, count]) => (
          <Grid item xs={6} sm={4} md={2} key={category}>
            <Card sx={{ textAlign: 'center' }}>
              <CardContent sx={{ py: 1 }}>
                <Typography variant="h6">{count}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {category}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <TextField
                  placeholder="Search services..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />
                  }}
                  sx={{ minWidth: 300 }}
                />
                <TextField
                  label="Category"
                  select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  SelectProps={{ native: true }}
                  sx={{ minWidth: 150 }}
                >
                  {categories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </TextField>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setAddDialog(true)}
                >
                  Add Service
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Services Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Services ({filteredServices.length})
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Service Name</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell align="right">Rate</TableCell>
                      <TableCell align="right">Tax Rate</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredServices.map((service) => (
                      <TableRow key={service.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {service.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={service.category}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {service.description || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="medium">
                            ₹{service.rate}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {service.taxRate}%
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={service.isActive ? 'Active' : 'Inactive'}
                            color={service.isActive ? 'success' : 'default'}
                            size="small"
                            onClick={() => toggleServiceStatus(service.id)}
                            sx={{ cursor: 'pointer' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedService(service);
                              setEditDialog(true);
                            }}
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => deleteService(service.id)}
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

      {/* Add Service Dialog */}
      <Dialog open={addDialog} onClose={() => setAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Service</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Service Name *"
              value={newService.name || ''}
              onChange={(e) => setNewService({ ...newService, name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Category"
              select
              value={newService.category || 'Food'}
              onChange={(e) => setNewService({ ...newService, category: e.target.value as HotelService['category'] })}
              SelectProps={{ native: true }}
            >
              {categories.slice(1).map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </TextField>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Description"
              value={newService.description || ''}
              onChange={(e) => setNewService({ ...newService, description: e.target.value })}
            />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Rate *"
                  value={newService.rate || ''}
                  onChange={(e) => setNewService({ ...newService, rate: Number(e.target.value) })}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Tax Rate (%)"
                  value={newService.taxRate || ''}
                  onChange={(e) => setNewService({ ...newService, taxRate: Number(e.target.value) })}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialog(false)}>Cancel</Button>
          <Button onClick={addService} variant="contained">Add Service</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Service Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Service</DialogTitle>
        <DialogContent>
          {selectedService && (
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Service Name"
                value={selectedService.name}
                onChange={(e) => setSelectedService({ ...selectedService, name: e.target.value })}
              />
              <TextField
                fullWidth
                label="Category"
                select
                value={selectedService.category}
                onChange={(e) => setSelectedService({ ...selectedService, category: e.target.value as HotelService['category'] })}
                SelectProps={{ native: true }}
              >
                {categories.slice(1).map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </TextField>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Description"
                value={selectedService.description || ''}
                onChange={(e) => setSelectedService({ ...selectedService, description: e.target.value })}
              />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Rate"
                    value={selectedService.rate}
                    onChange={(e) => setSelectedService({ ...selectedService, rate: Number(e.target.value) })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Tax Rate (%)"
                    value={selectedService.taxRate}
                    onChange={(e) => setSelectedService({ ...selectedService, taxRate: Number(e.target.value) })}
                  />
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={editService} variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HotelServices;