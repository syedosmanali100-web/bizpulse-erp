import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import KiranaLayout from '../components/kirana/KiranaLayout';
import KiranaBilling from '../components/kirana/KiranaBilling';
import KiranaInventory from '../components/kirana/KiranaInventory';
import KiranaCustomers from '../components/kirana/KiranaCustomers';

const KiranaStore: React.FC = () => {
  return (
    <KiranaLayout>
      <Routes>
        <Route path="/" element={<KiranaBilling />} />
        <Route path="/billing" element={<KiranaBilling />} />
        <Route path="/inventory" element={<KiranaInventory />} />
        <Route path="/customers" element={<KiranaCustomers />} />
      </Routes>
    </KiranaLayout>
  );
};

export default KiranaStore;