import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🏪 Billing Software</h1>
      <div style={{ display: 'flex', gap: '20px', marginTop: '30px' }}>
        <div style={{ 
          padding: '20px', 
          border: '2px solid #1976d2', 
          borderRadius: '8px',
          cursor: 'pointer',
          textAlign: 'center',
          minWidth: '200px'
        }}>
          <h2>🛒 Retail Store</h2>
          <p>Quick billing, inventory management</p>
          <button style={{ 
            padding: '10px 20px', 
            backgroundColor: '#1976d2', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}>
            Get Started
          </button>
        </div>
        
        <div style={{ 
          padding: '20px', 
          border: '2px solid #d32f2f', 
          borderRadius: '8px',
          cursor: 'pointer',
          textAlign: 'center',
          minWidth: '200px'
        }}>
          <h2>🏨 Hotel Management</h2>
          <p>Guest billing, room management</p>
          <button style={{ 
            padding: '10px 20px', 
            backgroundColor: '#d32f2f', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}>
            Get Started
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;