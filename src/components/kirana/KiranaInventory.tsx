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
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  Search as SearchIcon
} from '@mui/icons-material';

interface Product {
  id: string;
  code: string;
  name: string;
  category: string;
  price: number;
  cost: number;
  stock: number;
  minStock: number;
  unit: string;
}

const KiranaInventory: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([
    { id: '1', code: '001', name: 'Rice 1kg', category: 'Grains', price: 80, cost: 70, stock: 50, minStock: 10, unit: 'kg' },
    { id: '2', code: '002', name: 'Dal 500g', category: 'Pulses', price: 120, cost: 100, stock: 5, minStock: 10, unit: 'pack' },
    { id: '3', code: '003', name: 'Oil 1L', category: 'Cooking', price: 150, cost: 130, stock: 25, minStock: 5, unit: 'bottle' },
    { id: '4', code: '004', name: 'Sugar 1kg', category: 'Sweeteners', price: 45, cost: 40, stock: 30, minStock: 15, unit: 'kg' },
    { id: '5', code: '005', name: 'Tea 250g', category: 'Beverages', price: 200, cost: 180, stock: 2, minStock: 5, unit: 'pack' }
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [addDialog, setAddDialog] = useState(false);
  const [editDialog, setEditDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [newProduct, setNewProduct] = useState<Partial<Product>>({
    code: '',
    name: '',
    category: '',
    price: 0,
    cost: 0,
    stock: 0,
    minStock: 0,
    unit: ''
  });

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const lowStockProducts = products.filter(product => product.stock <= product.minStock);

  const addProduct = () => {
    if (newProduct.name && newProduct.code) {
      const product: Product = {
        id: Date.now().toString(),
        code: newProduct.code!,
        name: newProduct.name!,
        category: newProduct.category || 'General',
        price: newProduct.price || 0,
        cost: newProduct.cost || 0,
        stock: newProduct.stock || 0,
        minStock: newProduct.minStock || 0,
        unit: newProduct.unit || 'piece'
      };
      setProducts([...products, product]);
      setNewProduct({});
      setAddDialog(false);
    }
  };

  const editProduct = () => {
    if (selectedProduct) {
      setProducts(products.map(p => 
        p.id === selectedProduct.id ? selectedProduct : p
      ));
      setEditDialog(false);
      setSelectedProduct(null);
    }
  };

  const deleteProduct = (id: string) => {
    setProducts(products.filter(p => p.id !== id));
  };

  const updateStock = (id: string, newStock: number) => {
    setProducts(products.map(p => 
      p.id === id ? { ...p, stock: newStock } : p
    ));
  };

  const getStockStatus = (product: Product) => {
    if (product.stock === 0) return { label: 'Out of Stock', color: 'error' as const };
    if (product.stock <= product.minStock) return { label: 'Low Stock', color: 'warning' as const };
    return { label: 'In Stock', color: 'success' as const };
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Inventory Management
      </Typography>

      {/* Low Stock Alert */}
      {lowStockProducts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }} icon={<WarningIcon />}>
          {lowStockProducts.length} product(s) are running low on stock: {' '}
          {lowStockProducts.map(p => p.name).join(', ')}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <TextField
                  placeholder="Search products..."
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
                  Add Product
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Products Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Products ({filteredProducts.length})
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Code</TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell align="right">Cost</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell align="right">Stock</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredProducts.map((product) => {
                      const status = getStockStatus(product);
                      return (
                        <TableRow key={product.id}>
                          <TableCell>{product.code}</TableCell>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {product.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Unit: {product.unit}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>{product.category}</TableCell>
                          <TableCell align="right">₹{product.cost}</TableCell>
                          <TableCell align="right">₹{product.price}</TableCell>
                          <TableCell align="right">
                            <TextField
                              size="small"
                              type="number"
                              value={product.stock}
                              onChange={(e) => updateStock(product.id, Number(e.target.value))}
                              sx={{ width: 80 }}
                            />
                            <Typography variant="caption" display="block" color="text.secondary">
                              Min: {product.minStock}
                            </Typography>
                          </TableCell>
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
                                setSelectedProduct(product);
                                setEditDialog(true);
                              }}
                            >
                              <EditIcon />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => deleteProduct(product.id)}
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

      {/* Add Product Dialog */}
      <Dialog open={addDialog} onClose={() => setAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Product</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Product Code"
              value={newProduct.code || ''}
              onChange={(e) => setNewProduct({ ...newProduct, code: e.target.value })}
            />
            <TextField
              fullWidth
              label="Product Name"
              value={newProduct.name || ''}
              onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Category"
              value={newProduct.category || ''}
              onChange={(e) => setNewProduct({ ...newProduct, category: e.target.value })}
            />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Cost Price"
                  value={newProduct.cost || ''}
                  onChange={(e) => setNewProduct({ ...newProduct, cost: Number(e.target.value) })}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Selling Price"
                  value={newProduct.price || ''}
                  onChange={(e) => setNewProduct({ ...newProduct, price: Number(e.target.value) })}
                />
              </Grid>
            </Grid>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Stock"
                  value={newProduct.stock || ''}
                  onChange={(e) => setNewProduct({ ...newProduct, stock: Number(e.target.value) })}
                />
              </Grid>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Min Stock"
                  value={newProduct.minStock || ''}
                  onChange={(e) => setNewProduct({ ...newProduct, minStock: Number(e.target.value) })}
                />
              </Grid>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  label="Unit"
                  value={newProduct.unit || ''}
                  onChange={(e) => setNewProduct({ ...newProduct, unit: e.target.value })}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialog(false)}>Cancel</Button>
          <Button onClick={addProduct} variant="contained">Add Product</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Product Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Product</DialogTitle>
        <DialogContent>
          {selectedProduct && (
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Product Code"
                value={selectedProduct.code}
                onChange={(e) => setSelectedProduct({ ...selectedProduct, code: e.target.value })}
              />
              <TextField
                fullWidth
                label="Product Name"
                value={selectedProduct.name}
                onChange={(e) => setSelectedProduct({ ...selectedProduct, name: e.target.value })}
              />
              <TextField
                fullWidth
                label="Category"
                value={selectedProduct.category}
                onChange={(e) => setSelectedProduct({ ...selectedProduct, category: e.target.value })}
              />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Cost Price"
                    value={selectedProduct.cost}
                    onChange={(e) => setSelectedProduct({ ...selectedProduct, cost: Number(e.target.value) })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Selling Price"
                    value={selectedProduct.price}
                    onChange={(e) => setSelectedProduct({ ...selectedProduct, price: Number(e.target.value) })}
                  />
                </Grid>
              </Grid>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Min Stock"
                    value={selectedProduct.minStock}
                    onChange={(e) => setSelectedProduct({ ...selectedProduct, minStock: Number(e.target.value) })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Unit"
                    value={selectedProduct.unit}
                    onChange={(e) => setSelectedProduct({ ...selectedProduct, unit: e.target.value })}
                  />
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={editProduct} variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KiranaInventory;