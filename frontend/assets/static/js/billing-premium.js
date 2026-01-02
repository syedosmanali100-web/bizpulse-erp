// Premium Billing System JavaScript
class PremiumBilling {
    constructor() {
        this.currentOrder = [];
        this.orderCounter = 1;
        this.selectedPaymentMethod = null;
        this.subtotal = 0;
        this.gstRate = 0.18; // 18% GST (9% CGST + 9% SGST)
        this.orderType = 'dine-in';
        this.selectedTable = null;
        this.currentCustomer = null;
        this.discountAmount = 0;
        this.discountType = 'percentage';
        this.loyaltyPoints = 0;
        this.kotStatus = 'pending';
        this.orderNotes = {
            kitchen: '',
            customer: ''
        };
        
        this.menuItems = [
            // Veg Items
            { id: 'v1', name: 'Paneer Butter Masala', price: 280, category: 'veg', type: 'veg' },
            { id: 'v2', name: 'Dal Makhani', price: 220, category: 'veg', type: 'veg' },
            { id: 'v3', name: 'Veg Biryani', price: 250, category: 'veg', type: 'veg' },
            { id: 'v4', name: 'Palak Paneer', price: 260, category: 'veg', type: 'veg' },
            { id: 'v5', name: 'Aloo Gobi', price: 180, category: 'veg', type: 'veg' },
            { id: 'v6', name: 'Chole Bhature', price: 200, category: 'veg', type: 'veg' },
            
            // Non-Veg Items
            { id: 'n1', name: 'Butter Chicken', price: 320, category: 'non-veg', type: 'non-veg' },
            { id: 'n2', name: 'Chicken Biryani', price: 300, category: 'non-veg', type: 'non-veg' },
            { id: 'n3', name: 'Mutton Curry', price: 380, category: 'non-veg', type: 'non-veg' },
            { id: 'n4', name: 'Fish Fry', price: 280, category: 'non-veg', type: 'non-veg' },
            { id: 'n5', name: 'Chicken Tikka', price: 250, category: 'non-veg', type: 'non-veg' },
            { id: 'n6', name: 'Prawn Curry', price: 350, category: 'non-veg', type: 'non-veg' },
            
            // Drinks
            { id: 'd1', name: 'Lassi', price: 80, category: 'drinks', type: 'drinks' },
            { id: 'd2', name: 'Fresh Lime Soda', price: 60, category: 'drinks', type: 'drinks' },
            { id: 'd3', name: 'Mango Juice', price: 90, category: 'drinks', type: 'drinks' },
            { id: 'd4', name: 'Masala Chai', price: 40, category: 'drinks', type: 'drinks' },
            { id: 'd5', name: 'Cold Coffee', price: 100, category: 'drinks', type: 'drinks' },
            { id: 'd6', name: 'Buttermilk', price: 50, category: 'drinks', type: 'drinks' },
            
            // Combos
            { id: 'c1', name: 'Veg Thali', price: 350, category: 'combos', type: 'veg' },
            { id: 'c2', name: 'Non-Veg Thali', price: 450, category: 'combos', type: 'non-veg' },
            { id: 'c3', name: 'Family Pack Veg', price: 800, category: 'combos', type: 'veg' },
            { id: 'c4', name: 'Family Pack Non-Veg', price: 1200, category: 'combos', type: 'non-veg' }
        ];
        
        this.init();
    }
    
    init() {
        this.renderMenuItems();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.updateBillingSummary();
    }
    
    renderMenuItems(filter = 'all') {
        const itemsGrid = document.getElementById('itemsGrid');
        itemsGrid.innerHTML = '';
        
        const filteredItems = filter === 'all' 
            ? this.menuItems 
            : this.menuItems.filter(item => item.category === filter);
        
        filteredItems.forEach(item => {
            const itemCard = this.createItemCard(item);
            itemsGrid.appendChild(itemCard);
        });
    }
    
    createItemCard(item) {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.dataset.itemId = item.id;
        
        const iconClass = item.type === 'veg' ? 'veg' : 
                         item.type === 'non-veg' ? 'non-veg' : 'drinks';
        
        const iconText = item.type === 'veg' ? 'V' : 
                        item.type === 'non-veg' ? 'N' : 'D';
        
        card.innerHTML = `
            <div class="item-icon ${iconClass}">${iconText}</div>
            <div class="item-name">${item.name}</div>
            <div class="item-price">₹${item.price}</div>
            <div class="item-added-badge">✓</div>
        `;
        
        card.addEventListener('click', () => this.addItemToOrder(item));
        
        return card;
    }
    
    addItemToOrder(item) {
        // Check if item already exists in order
        const existingItem = this.currentOrder.find(orderItem => orderItem.id === item.id);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.currentOrder.push({
                ...item,
                quantity: 1,
                notes: ''
            });
        }
        
        // Show visual feedback
        this.showItemAddedFeedback(item.id);
        
        // Update UI
        this.renderOrderItems();
        this.updateBillingSummary();
    }
    
    showItemAddedFeedback(itemId) {
        const itemCard = document.querySelector(`[data-item-id="${itemId}"]`);
        const badge = itemCard.querySelector('.item-added-badge');
        
        badge.classList.add('show', 'checkmark-animation');
        
        setTimeout(() => {
            badge.classList.remove('show', 'checkmark-animation');
        }, 1000);
    }
    
    renderOrderItems() {
        const orderItems = document.getElementById('orderItems');
        const emptyOrder = document.getElementById('emptyOrder');
        const orderSubtotal = document.getElementById('orderSubtotal');
        
        if (this.currentOrder.length === 0) {
            emptyOrder.style.display = 'flex';
            orderSubtotal.style.display = 'none';
            orderItems.innerHTML = '<div class="empty-order" id="emptyOrder"><i class="fas fa-shopping-cart"></i><div class="empty-order-text">Add items to start billing</div><div class="empty-order-subtext">Click on items from the menu</div></div>';
            return;
        }
        
        emptyOrder.style.display = 'none';
        orderSubtotal.style.display = 'flex';
        
        orderItems.innerHTML = '';
        
        this.currentOrder.forEach((item, index) => {
            const orderItem = this.createOrderItem(item, index);
            orderItems.appendChild(orderItem);
        });
        
        // Update item count and subtotal
        const totalItems = this.currentOrder.reduce((sum, item) => sum + item.quantity, 0);
        document.getElementById('itemCount').textContent = `${totalItems} items`;
        document.getElementById('subtotalAmount').textContent = `₹${this.subtotal}`;
    }
    
    createOrderItem(item, index) {
        const orderItem = document.createElement('div');
        orderItem.className = 'order-item slide-in';
        
        // Add recently added class for new items
        if (index === this.currentOrder.length - 1) {
            orderItem.classList.add('recently-added');
            setTimeout(() => {
                orderItem.classList.remove('recently-added');
            }, 3000);
        }
        
        orderItem.innerHTML = `
            <div class="item-info">
                <div class="item-info-name">${item.name}</div>
                ${item.notes ? `<div class="item-info-notes">${item.notes}</div>` : ''}
            </div>
            <div class="quantity-controls">
                <button class="qty-btn" onclick="billing.updateQuantity('${item.id}', -1)">
                    <i class="fas fa-minus"></i>
                </button>
                <div class="qty-display">${item.quantity}</div>
                <button class="qty-btn" onclick="billing.updateQuantity('${item.id}', 1)">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
            <div class="item-total">
                <div class="item-unit-price">₹${item.price} each</div>
                <div class="item-total-price">₹${item.price * item.quantity}</div>
            </div>
        `;
        
        return orderItem;
    }
    
    updateQuantity(itemId, change) {
        const item = this.currentOrder.find(orderItem => orderItem.id === itemId);
        
        if (item) {
            item.quantity += change;
            
            if (item.quantity <= 0) {
                this.currentOrder = this.currentOrder.filter(orderItem => orderItem.id !== itemId);
            }
            
            this.renderOrderItems();
            this.updateBillingSummary();
        }
    }
    
    updateBillingSummary() {
        // Calculate subtotal
        this.subtotal = this.currentOrder.reduce((sum, item) => {
            return sum + (item.price * item.quantity);
        }, 0);
        
        // Calculate GST
        const cgst = Math.round(this.subtotal * 0.09);
        const sgst = Math.round(this.subtotal * 0.09);
        const totalGst = cgst + sgst;
        const grandTotal = this.subtotal + totalGst;
        
        // Update UI
        document.getElementById('billSubtotal').textContent = `₹${this.subtotal}`;
        document.getElementById('cgstAmount').textContent = `₹${cgst}`;
        document.getElementById('sgstAmount').textContent = `₹${sgst}`;
        document.getElementById('totalGst').textContent = `₹${totalGst}`;
        document.getElementById('grandTotal').textContent = `₹${grandTotal}`;
    }
    
    setupEventListeners() {
        // Category tabs
        document.querySelectorAll('.category-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                this.renderMenuItems(e.target.dataset.category);
            });
        });

        // Order type selector
        document.querySelectorAll('.order-type-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.order-type-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.orderType = e.target.dataset.type;
                this.handleOrderTypeChange();
            });
        });

        // Table selection
        document.querySelectorAll('.table-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (e.target.classList.contains('occupied')) return;
                document.querySelectorAll('.table-btn').forEach(b => b.classList.remove('selected'));
                e.target.classList.add('selected');
                this.selectedTable = e.target.dataset.table;
                this.updateOrderNumber();
            });
        });

        // Customer search
        const customerSearch = document.getElementById('customerSearch');
        if (customerSearch) {
            customerSearch.addEventListener('input', (e) => {
                this.searchCustomers(e.target.value);
            });
        }
        
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', (e) => {
            this.searchItems(e.target.value);
        });
        
        // Payment method selection
        document.querySelectorAll('.payment-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.payment-btn').forEach(b => b.style.opacity = '0.7');
                e.target.style.opacity = '1';
                this.selectedPaymentMethod = e.target.textContent.trim();
            });
        });
        
        // Action buttons
        document.getElementById('printBill').addEventListener('click', () => this.printBill());
        document.getElementById('holdBill').addEventListener('click', () => this.holdBill());
        document.getElementById('cancelOrder').addEventListener('click', () => this.cancelOrder());
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Focus search on '/' key
            if (e.key === '/' && e.target.tagName !== 'INPUT') {
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }
            
            // Print bill on F2
            if (e.key === 'F2') {
                e.preventDefault();
                this.printBill();
            }
            
            // Hold bill on F1
            if (e.key === 'F1') {
                e.preventDefault();
                this.holdBill();
            }
            
            // Cancel order on Escape
            if (e.key === 'Escape') {
                e.preventDefault();
                this.cancelOrder();
            }
        });
    }
    
    searchItems(query) {
        const filteredItems = this.menuItems.filter(item => 
            item.name.toLowerCase().includes(query.toLowerCase())
        );
        
        const itemsGrid = document.getElementById('itemsGrid');
        itemsGrid.innerHTML = '';
        
        filteredItems.forEach(item => {
            const itemCard = this.createItemCard(item);
            itemsGrid.appendChild(itemCard);
        });
    }
    
    printBill() {
        if (this.currentOrder.length === 0) {
            this.showNotification('No items in order', 'error');
            return;
        }
        
        if (!this.selectedPaymentMethod) {
            this.showNotification('Please select payment method', 'warning');
            return;
        }
        
        // Show loading state
        const printBtn = document.getElementById('printBill');
        const originalText = printBtn.innerHTML;
        printBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Printing...';
        printBtn.disabled = true;
        
        // Simulate printing process
        setTimeout(() => {
            this.showNotification('Bill printed successfully!', 'success');
            this.clearOrder();
            
            // Reset button
            printBtn.innerHTML = originalText;
            printBtn.disabled = false;
        }, 2000);
    }
    
    holdBill() {
        if (this.currentOrder.length === 0) {
            this.showNotification('No items to hold', 'error');
            return;
        }
        
        // Save current order (in real app, save to database)
        const heldOrder = {
            id: `HOLD-${Date.now()}`,
            items: [...this.currentOrder],
            timestamp: new Date(),
            customer: document.getElementById('customerPhone').value
        };
        
        // Store in localStorage for demo
        const heldOrders = JSON.parse(localStorage.getItem('heldOrders') || '[]');
        heldOrders.push(heldOrder);
        localStorage.setItem('heldOrders', JSON.stringify(heldOrders));
        
        this.showNotification(`Order held as ${heldOrder.id}`, 'success');
        this.clearOrder();
    }
    
    applyDiscount() {
        const discount = prompt('Enter discount percentage (0-100):');
        if (discount && !isNaN(discount) && discount >= 0 && discount <= 100) {
            // Apply discount logic here
            this.showNotification(`${discount}% discount applied`, 'success');
        }
    }
    
    cancelOrder() {
        if (this.currentOrder.length === 0) {
            return;
        }
        
        if (confirm('Are you sure you want to cancel this order?')) {
            this.clearOrder();
            this.showNotification('Order cancelled', 'info');
        }
    }
    
    clearOrder() {
        this.currentOrder = [];
        this.selectedPaymentMethod = null;
        document.getElementById('customerPhone').value = '';
        document.querySelectorAll('.payment-btn').forEach(btn => btn.style.opacity = '0.7');
        this.renderOrderItems();
        this.updateBillingSummary();
    }
    
    handleOrderTypeChange() {
        const tableSelector = document.getElementById('tableSelector');
        const deliveryChargesLine = document.getElementById('deliveryChargesLine');
        const packingChargesLine = document.getElementById('packingChargesLine');
        
        if (this.orderType === 'dine-in') {
            tableSelector.style.display = 'block';
            deliveryChargesLine.style.display = 'none';
            packingChargesLine.style.display = 'none';
        } else if (this.orderType === 'delivery') {
            tableSelector.style.display = 'none';
            deliveryChargesLine.style.display = 'flex';
            packingChargesLine.style.display = 'flex';
        } else { // takeaway
            tableSelector.style.display = 'none';
            deliveryChargesLine.style.display = 'none';
            packingChargesLine.style.display = 'flex';
        }
        
        this.updateBillingSummary();
    }

    updateOrderNumber() {
        const orderNumber = document.getElementById('orderNumber');
        let prefix = '';
        switch (this.orderType) {
            case 'dine-in':
                prefix = this.selectedTable ? `${this.selectedTable}-` : 'DIN-';
                break;
            case 'takeaway':
                prefix = 'TKW-';
                break;
            case 'delivery':
                prefix = 'DEL-';
                break;
        }
        orderNumber.textContent = `#${prefix}${String(this.orderCounter).padStart(3, '0')}`;
    }

    searchCustomers(query) {
        const suggestions = document.getElementById('customerSuggestions');
        if (query.length < 2) {
            suggestions.style.display = 'none';
            return;
        }
        
        // Mock customer data - replace with actual API call
        const customers = [
            { name: 'John Doe', phone: '9876543210', points: 250 },
            { name: 'Jane Smith', phone: '9876543211', points: 150 },
            { name: 'Mike Johnson', phone: '9876543212', points: 300 }
        ];
        
        const filtered = customers.filter(c => 
            c.name.toLowerCase().includes(query.toLowerCase()) || 
            c.phone.includes(query)
        );
        
        suggestions.innerHTML = '';
        filtered.forEach(customer => {
            const div = document.createElement('div');
            div.className = 'customer-suggestion';
            div.innerHTML = `${customer.name} - ${customer.phone} <span style="color: #F59E0B;">(${customer.points} pts)</span>`;
            div.onclick = () => this.selectCustomer(customer);
            suggestions.appendChild(div);
        });
        
        suggestions.style.display = filtered.length > 0 ? 'block' : 'none';
    }

    selectCustomer(customer) {
        this.currentCustomer = customer;
        document.getElementById('customerSearch').value = `${customer.name} - ${customer.phone}`;
        document.getElementById('customerSuggestions').style.display = 'none';
        
        // Show loyalty points if customer has any
        if (customer.points > 0) {
            document.getElementById('loyaltySection').style.display = 'block';
            document.getElementById('availablePoints').textContent = customer.points;
            this.loyaltyPoints = customer.points;
        }
    }

    applyDiscount() {
        const discountType = document.getElementById('discountType').value;
        const discountValue = parseFloat(document.getElementById('discountValue').value) || 0;
        
        if (discountValue <= 0) {
            this.showNotification('Please enter a valid discount amount', 'error');
            return;
        }
        
        this.discountType = discountType;
        
        if (discountType === 'percentage') {
            if (discountValue > 100) {
                this.showNotification('Discount cannot exceed 100%', 'error');
                return;
            }
            this.discountAmount = (this.subtotal * discountValue) / 100;
        } else {
            if (discountValue > this.subtotal) {
                this.showNotification('Discount cannot exceed subtotal', 'error');
                return;
            }
            this.discountAmount = discountValue;
        }
        
        document.getElementById('discountLine').style.display = 'flex';
        document.getElementById('discountAmount').textContent = `-₹${this.discountAmount.toFixed(0)}`;
        
        this.updateBillingSummary();
        this.showNotification(`Discount of ₹${this.discountAmount.toFixed(0)} applied`, 'success');
    }

    redeemPoints() {
        if (this.loyaltyPoints <= 0) {
            this.showNotification('No loyalty points available', 'error');
            return;
        }
        
        const pointsValue = this.loyaltyPoints; // 1 point = 1 rupee
        const maxRedemption = Math.min(pointsValue, this.subtotal);
        
        this.discountAmount += maxRedemption;
        this.loyaltyPoints -= maxRedemption;
        
        document.getElementById('discountLine').style.display = 'flex';
        document.getElementById('discountAmount').textContent = `-₹${this.discountAmount.toFixed(0)}`;
        document.getElementById('availablePoints').textContent = this.loyaltyPoints;
        
        if (this.loyaltyPoints <= 0) {
            document.getElementById('loyaltySection').style.display = 'none';
        }
        
        this.updateBillingSummary();
        this.showNotification(`₹${maxRedemption} redeemed from loyalty points`, 'success');
    }

    printKOT() {
        if (this.currentOrder.length === 0) {
            this.showNotification('No items to print KOT', 'error');
            return;
        }
        
        this.kotStatus = 'preparing';
        this.updateKOTStatus();
        this.showNotification('KOT sent to kitchen', 'success');
    }

    sendToKitchen() {
        if (this.currentOrder.length === 0) {
            this.showNotification('No items to send to kitchen', 'error');
            return;
        }
        
        this.kotStatus = 'preparing';
        this.updateKOTStatus();
        this.showNotification('Order sent to kitchen', 'success');
    }

    updateKOTStatus() {
        const kotSection = document.querySelector('.kot-status');
        const statusDot = kotSection.querySelector('.status-dot');
        const statusText = kotSection.querySelector('span:last-child');
        
        statusDot.className = `status-dot ${this.kotStatus}`;
        
        const statusTexts = {
            pending: 'KOT Status: Pending',
            preparing: 'KOT Status: Preparing',
            ready: 'KOT Status: Ready'
        };
        
        statusText.textContent = statusTexts[this.kotStatus];
    }

    updateBillingSummary() {
        // Calculate subtotal
        this.subtotal = this.currentOrder.reduce((sum, item) => {
            return sum + (item.price * item.quantity);
        }, 0);
        
        // Apply additional charges based on order type
        let additionalCharges = 0;
        if (this.orderType === 'delivery') {
            additionalCharges += 40; // delivery charges
            additionalCharges += 20; // packing charges
        } else if (this.orderType === 'takeaway') {
            additionalCharges += 20; // packing charges
        }
        
        // Calculate GST on subtotal + additional charges
        const taxableAmount = this.subtotal + additionalCharges - this.discountAmount;
        const cgst = Math.round(taxableAmount * 0.09);
        const sgst = Math.round(taxableAmount * 0.09);
        const totalGst = cgst + sgst;
        const grandTotal = taxableAmount + totalGst;
        
        // Update UI
        document.getElementById('billSubtotal').textContent = `₹${this.subtotal}`;
        document.getElementById('cgstAmount').textContent = `₹${cgst}`;
        document.getElementById('sgstAmount').textContent = `₹${sgst}`;
        document.getElementById('totalGst').textContent = `₹${totalGst}`;
        document.getElementById('grandTotal').textContent = `₹${grandTotal}`;
        
        // Update additional charges
        if (this.orderType === 'delivery') {
            document.getElementById('deliveryCharges').textContent = '₹40';
            document.getElementById('packingCharges').textContent = '₹20';
        } else if (this.orderType === 'takeaway') {
            document.getElementById('packingCharges').textContent = '₹20';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 300ms ease;
        `;
        
        // Set color based on type
        const colors = {
            success: '#10B981',
            error: '#EF4444',
            warning: '#F59E0B',
            info: '#732C3F'
        };
        
        notification.style.background = colors[type] || colors.info;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Additional Professional Functions
function showSplitPayment() {
    document.getElementById('splitPaymentModal').style.display = 'flex';
    document.getElementById('splitTotalAmount').textContent = document.getElementById('grandTotal').textContent.replace('₹', '');
}

function closeSplitPayment() {
    document.getElementById('splitPaymentModal').style.display = 'none';
}

function addSplitItem() {
    const container = document.getElementById('splitPaymentItems');
    const newItem = document.createElement('div');
    newItem.className = 'payment-split-item';
    newItem.innerHTML = `
        <select style="flex: 1; padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px;">
            <option>Cash</option>
            <option>UPI</option>
            <option>Card</option>
        </select>
        <input type="number" placeholder="Amount" style="width: 100px; padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px;">
        <button onclick="removeSplitItem(this)" style="background: #EF4444; color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer;">
            <i class="fas fa-trash"></i>
        </button>
    `;
    container.appendChild(newItem);
}

function removeSplitItem(button) {
    button.parentElement.remove();
}

function processSplitPayment() {
    billing.showNotification('Split payment processed successfully!', 'success');
    closeSplitPayment();
}

function showAddCustomerModal() {
    document.getElementById('addCustomerModal').style.display = 'flex';
}

function closeAddCustomer() {
    document.getElementById('addCustomerModal').style.display = 'none';
}

function saveNewCustomer() {
    const name = document.getElementById('newCustomerName').value;
    const phone = document.getElementById('newCustomerPhone').value;
    
    if (!name || !phone) {
        billing.showNotification('Name and phone are required', 'error');
        return;
    }
    
    billing.showNotification('Customer added successfully!', 'success');
    closeAddCustomer();
}

function addOrderNote() {
    document.getElementById('orderNotesModal').style.display = 'flex';
}

function closeOrderNotes() {
    document.getElementById('orderNotesModal').style.display = 'none';
}

function saveOrderNotes() {
    const kitchenNotes = document.getElementById('kitchenNotes').value;
    const customerNotes = document.getElementById('customerNotes').value;
    
    billing.orderNotes.kitchen = kitchenNotes;
    billing.orderNotes.customer = customerNotes;
    
    billing.showNotification('Order notes saved', 'success');
    closeOrderNotes();
}

function showLoyaltyPoints() {
    if (billing.currentCustomer && billing.currentCustomer.points > 0) {
        document.getElementById('loyaltySection').style.display = 'block';
    } else {
        billing.showNotification('No customer selected or no loyalty points available', 'info');
    }
}

function addCustomization() {
    billing.showNotification('Customization feature - Coming soon!', 'info');
}

function duplicateItem() {
    billing.showNotification('Duplicate item feature - Coming soon!', 'info');
}

function showComboBuilder() {
    billing.showNotification('Combo builder - Coming soon!', 'info');
}

function showCoupons() {
    billing.showNotification('Coupons feature - Coming soon!', 'info');
}

function showOffers() {
    billing.showNotification('Offers feature - Coming soon!', 'info');
}

function saveAndPrint() {
    billing.printBill();
}

function printKOTOnly() {
    billing.printKOT();
}

function emailBill() {
    billing.showNotification('Email bill feature - Coming soon!', 'info');
}

function whatsappBill() {
    billing.showNotification('WhatsApp bill feature - Coming soon!', 'info');
}

function showSettleBill() {
    billing.showNotification('Settle bill feature - Coming soon!', 'info');
}

function duplicateOrder() {
    billing.showNotification('Duplicate order feature - Coming soon!', 'info');
}

function voidOrder() {
    if (confirm('Are you sure you want to void this order?')) {
        billing.clearOrder();
        billing.showNotification('Order voided', 'info');
    }
}

// Initialize billing system
const billing = new PremiumBilling();

// Make updateQuantity globally accessible
window.billing = billing;