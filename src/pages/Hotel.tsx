import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import HotelLayout from '../components/hotel/HotelLayout';
import HotelDashboard from '../components/hotel/HotelDashboard';
import HotelGuests from '../components/hotel/HotelGuests';
import HotelBilling from '../components/hotel/HotelBilling';
import HotelServices from '../components/hotel/HotelServices';

const Hotel: React.FC = () => {
  return (
    <HotelLayout>
      <Routes>
        <Route path="/" element={<HotelDashboard />} />
        <Route path="/dashboard" element={<HotelDashboard />} />
        <Route path="/guests" element={<HotelGuests />} />
        <Route path="/billing" element={<HotelBilling />} />
        <Route path="/services" element={<HotelServices />} />
      </Routes>
    </HotelLayout>
  );
};

export default Hotel;