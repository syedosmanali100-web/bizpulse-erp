// Sales Chart Fix for Mobile App
function initializeSalesChart() {
    // Wait for DOM to be ready
    setTimeout(() => {
        const canvas = document.getElementById('salesChartCanvas');
        if (canvas) {
            drawSalesChart();
        }
    }, 500);
}

// Enhanced chart drawing function
function drawSalesChart(data = null) {
    const canvas = document.getElementById('salesChartCanvas');
    if (!canvas) {
        console.log('Canvas not found, retrying...');
        setTimeout(() => drawSalesChart(data), 200);
        return;
    }
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    
    // Set canvas size
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Sample data based on current range
    const chartData = data || getSampleChartData(currentSalesRange);
    
    const maxValue = Math.max(...chartData.map(d => d.value));
    const padding = 30;
    const chartWidth = width - (padding * 2);
    const chartHeight = height - (padding * 2);
    
    // Draw background gradient
    const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
    bgGradient.addColorStop(0, '#f8f9fa');
    bgGradient.addColorStop(1, '#ffffff');
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, width, height);
    
    // Draw grid lines
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }
    
    // Draw bars
    const barWidth = chartWidth / chartData.length * 0.7;
    const barSpacing = chartWidth / chartData.length;
    
    chartData.forEach((item, index) => {
        const barHeight = (item.value / maxValue) * chartHeight * 0.8;
        const x = padding + (barSpacing * index) + (barSpacing - barWidth) / 2;
        const y = height - padding - barHeight;
        
        // Draw bar with gradient
        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        gradient.addColorStop(0, '#732C3F');
        gradient.addColorStop(0.5, '#8B4A5C');
        gradient.addColorStop(1, '#A66B7A');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth, barHeight);
        
        // Draw value on top
        ctx.fillStyle = '#732C3F';
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        const valueText = item.value >= 1000 ? '₹' + (item.value / 1000).toFixed(1) + 'k' : '₹' + item.value;
        ctx.fillText(valueText, x + barWidth/2, y - 5);
        
        // Draw label at bottom
        ctx.fillStyle = '#666';
        ctx.font = '9px Arial';
        ctx.fillText(item.label, x + barWidth/2, height - padding + 15);
    });
    
    console.log('✅ Sales chart drawn successfully');
}

function getSampleChartData(range) {
    const data = {
        'today': [
            { label: '9AM', value: 450 },
            { label: '11AM', value: 680 },
            { label: '1PM', value: 920 },
            { label: '3PM', value: 750 },
            { label: '5PM', value: 1200 },
            { label: '7PM', value: 890 }
        ],
        'week': [
            { label: 'Mon', value: 1200 },
            { label: 'Tue', value: 1800 },
            { label: 'Wed', value: 1500 },
            { label: 'Thu', value: 2200 },
            { label: 'Fri', value: 2800 },
            { label: 'Sat', value: 3200 },
            { label: 'Sun', value: 2100 }
        ],
        'month': [
            { label: 'W1', value: 8500 },
            { label: 'W2', value: 12300 },
            { label: 'W3', value: 15600 },
            { label: 'W4', value: 18900 }
        ],
        'custom': [
            { label: 'Day 1', value: 2200 },
            { label: 'Day 2', value: 1800 },
            { label: 'Day 3', value: 2600 },
            { label: 'Day 4', value: 3100 },
            { label: 'Day 5', value: 2400 }
        ]
    };
    return data[range] || data['today'];
}

// Fix scrolling issue
function fixSalesTabScrolling() {
    const tabContent = document.getElementById('salesTabContent');
    if (tabContent) {
        tabContent.style.maxHeight = 'calc(100vh - 450px)';
        tabContent.style.overflowY = 'auto';
        tabContent.style.paddingBottom = '100px';
        tabContent.style.webkitOverflowScrolling = 'touch';
    }
}

// Initialize when sales screen is shown
function initializeSalesScreen() {
    console.log('🚀 Initializing sales screen...');
    
    // Fix scrolling
    fixSalesTabScrolling();
    
    // Load data
    loadSalesData();
    
    // Initialize chart
    initializeSalesChart();
}