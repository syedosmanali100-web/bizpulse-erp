// Complete JavaScript functions for low stock management

async function loadLowStockData() {
    try {
        console.log('🔄 Loading low stock data...');
        const response = await fetch('/api/inventory/low-stock');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📊 Data received:', data);
        
        // Always process data, even if empty
        lowStockData = data.low_stock_items || [];
        filteredData = [...lowStockData];
        
        console.log('📦 Low stock items:', lowStockData.length);
        console.log('📊 Summary:', data.summary);
        
        updateStatistics(data.summary || {
            total_low_stock: 0,
            critical_items: 0,
            out_of_stock: 0,
            total_reorder_cost: 0
        });
        
        updateCategoryBreakdown(data.category_summary || []);
        updateRecentMovements(data.recent_movements || []);
        populateCategoryFilter();
        renderTable();
        
        console.log('✅ Low stock data loaded successfully');
        
    } catch (error) {
        console.error('❌ Error loading low stock data:', error);
        showAlert('Error loading data. Please try again.', 'error');
        
        // Show error state in table
        const tableBody = document.getElementById('stockTableBody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px; color: #666;">
                        ❌ Failed to load data. Please refresh the page.
                    </td>
                </tr>
            `;
        }
    }
}

function updateStatistics(summary) {
    console.log('📊 Updating statistics:', summary);
    
    const totalLowStock = document.getElementById('totalLowStock');
    const criticalItems = document.getElementById('criticalItems');
    const outOfStock = document.getElementById('outOfStock');
    const reorderCost = document.getElementById('reorderCost');
    
    if (totalLowStock) totalLowStock.textContent = summary.total_low_stock || 0;
    if (criticalItems) criticalItems.textContent = summary.critical_items || 0;
    if (outOfStock) outOfStock.textContent = summary.out_of_stock || 0;
    if (reorderCost) reorderCost.textContent = `₹${(summary.total_reorder_cost || 0).toLocaleString()}`;
}

function renderTable() {
    console.log('📋 Rendering table with data:', filteredData);
    const tbody = document.getElementById('stockTableBody');
    
    if (!tbody) {
        console.error('❌ Table body not found!');
        return;
    }
    
    if (!filteredData || filteredData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #8B4A5C;">
                    📦 No low stock items found
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filteredData.map(item => `
        <tr>
            <td>
                <div style="font-weight: 500; color: #8B4A5C;">${item.name}</div>
                <div style="font-size: 0.85rem; color: #666;">${item.code}</div>
            </td>
            <td style="color: #8B4A5C;">${item.category}</td>
            <td>
                <span style="font-weight: 500; color: ${item.stock === 0 ? '#e74c3c' : '#8B4A5C'};">
                    ${item.stock} ${item.unit}
                </span>
            </td>
            <td style="color: #8B4A5C;">${item.min_stock} ${item.unit}</td>
            <td>
                <span style="color: #e74c3c; font-weight: 500;">
                    ${item.shortage_quantity} ${item.unit}
                </span>
            </td>
            <td>
                <span class="urgency-badge urgency-${item.urgency_level}">
                    ${item.urgency_level.replace('_', ' ')}
                </span>
            </td>
            <td style="color: #8B4A5C; font-weight: 500;">₹${item.reorder_cost.toFixed(2)}</td>
            <td>
                <div class="stock-actions">
                    <button class="btn btn-success btn-sm" onclick="openRestockModal('${item.id}')">
                        📦 Restock
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="openMinStockModal('${item.id}')">
                        ⚙️ Min Stock
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function refreshData() {
    const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
    const originalText = refreshBtn.innerHTML;
    
    try {
        console.log('🔄 Refresh button clicked');
        
        // Button loading state
        refreshBtn.classList.add('btn-refreshing');
        refreshBtn.innerHTML = '🔄 Refreshing...';
        refreshBtn.disabled = true;
        
        // Clear current data and show loading
        const tableBody = document.getElementById('stockTableBody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="loading">
                        <div class="spinner"></div>
                        Refreshing low stock data...
                    </td>
                </tr>
            `;
        }
        
        // Load fresh data
        await loadLowStockData();
        
        // Success state
        refreshBtn.classList.remove('btn-refreshing');
        refreshBtn.classList.add('refresh-success');
        refreshBtn.innerHTML = '✅ Done';
        
        console.log('✅ Data refreshed successfully');
        
        // Reset button
        setTimeout(() => {
            refreshBtn.classList.remove('refresh-success');
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
        }, 1000);
        
    } catch (error) {
        console.error('❌ Error refreshing data:', error);
        
        // Error state
        refreshBtn.classList.remove('btn-refreshing');
        refreshBtn.innerHTML = '❌ Error';
        refreshBtn.style.background = '#e74c3c';
        
        // Reset button
        setTimeout(() => {
            refreshBtn.innerHTML = originalText;
            refreshBtn.style.background = '';
            refreshBtn.disabled = false;
        }, 1500);
    }
}

function showAlert(message, type, timeout = 3000, containerId = null) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
    const alertHtml = `<div class="alert ${alertClass}">${message}</div>`;
    
    if (containerId) {
        document.getElementById(containerId).innerHTML = alertHtml;
    } else {
        // Simple alert without animations
        const alertContainer = document.createElement('div');
        alertContainer.innerHTML = alertHtml;
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
        
        setTimeout(() => {
            if (document.body.contains(alertContainer)) {
                document.body.removeChild(alertContainer);
            }
        }, timeout);
    }
}