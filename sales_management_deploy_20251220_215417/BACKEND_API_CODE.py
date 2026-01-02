
# Enhanced Sales API with Bill Grouping and Pagination
# Add this to your production app.py file

@app.route('/api/sales/all', methods=['GET'])
def get_all_sales():
    """Get all sales entries with proper date filtering and bill grouping"""
    from datetime import datetime, timedelta
    
    # Get filter parameters
    date_filter = request.args.get('filter', '')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    category = request.args.get('category', 'all')
    payment_method = request.args.get('payment_method', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 15))  # 15 records per page
    
    # Get current date in local time
    now = datetime.now()
    
    # Validate and set date range
    if date_filter == 'today':
        start_date = now.strftime('%Y-%m-%d')
        end_date = start_date
    elif date_filter == 'yesterday':
        yesterday = now - timedelta(days=1)
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = start_date
    elif date_filter == 'week':
        week_start = now - timedelta(days=now.weekday())
        start_date = week_start.strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
    elif date_filter == 'month':
        month_start = now.replace(day=1)
        start_date = month_start.strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
    elif date_filter == 'custom':
        if not start_date or not end_date:
            return jsonify({"success": False, "error": "Custom filter requires startDate and endDate"}), 400
    else:
        if not start_date or not end_date:
            return jsonify({"success": False, "error": "Missing startDate or endDate parameters"}), 400
    
    # Validate date format and range
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        if start_dt > end_dt:
            return jsonify({"success": False, "error": "startDate cannot be greater than endDate"}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    conn = get_db_connection()
    
    # First, get grouped bills (one row per bill with product list)
    bills_query = """
        SELECT 
            s.bill_id,
            s.bill_number,
            s.customer_id,
            s.customer_name,
            s.payment_method,
            s.sale_date as date,
            s.sale_time as time,
            s.created_at,
            COUNT(s.id) as total_items,
            SUM(s.quantity) as total_quantity,
            SUM(s.total_price) as total_amount,
            SUM(s.tax_amount) as tax_amount,
            SUM(s.discount_amount) as discount_amount,
            GROUP_CONCAT(s.product_name || ' (' || s.quantity || 'x)', ', ') as product_list,
            SUM(s.total_price - (COALESCE(p.cost, 0) * s.quantity)) as profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
    """
    
    params = [start_date, end_date]
    
    # Add category filter
    if category != 'all':
        bills_query += ' AND s.category = ?'
        params.append(category)
    
    # Add payment method filter
    if payment_method != 'all':
        bills_query += ' AND s.payment_method = ?'
        params.append(payment_method)
    
    bills_query += """
        GROUP BY s.bill_id, s.bill_number, s.customer_id, s.customer_name, 
                 s.payment_method, s.sale_date, s.sale_time, s.created_at
        ORDER BY s.created_at DESC
    """
    
    # Get total count for pagination
    count_query = """
        SELECT COUNT(DISTINCT s.bill_id) as total_bills
        FROM sales s
        WHERE DATE(s.created_at) BETWEEN ? AND ?
    """
    count_params = [start_date, end_date]
    
    if category != 'all':
        count_query += ' AND s.category = ?'
        count_params.append(category)
    
    if payment_method != 'all':
        count_query += ' AND s.payment_method = ?'
        count_params.append(payment_method)
    
    total_bills = conn.execute(count_query, count_params).fetchone()['total_bills']
    
    # Add pagination
    offset = (page - 1) * per_page
    bills_query += f' LIMIT {per_page} OFFSET {offset}'
    
    bills = conn.execute(bills_query, params).fetchall()
    
    # Convert to list of dicts and add serial numbers
    bills_list = []
    for i, bill in enumerate(bills):
        bill_dict = dict(bill)
        bill_dict['serial_no'] = offset + i + 1  # Serial number with pagination
        bills_list.append(bill_dict)
    
    # Get summary statistics with separate net profit and receivable profit
    summary_query = """
        SELECT 
            COUNT(DISTINCT s.bill_id) as total_bills,
            COUNT(*) as total_items,
            COALESCE(SUM(s.quantity), 0) as total_quantity,
            COALESCE(SUM(s.total_price), 0) as total_sales,
            COALESCE(SUM(s.tax_amount), 0) as total_tax,
            COALESCE(SUM(s.discount_amount), 0) as total_discount,
            COALESCE(AVG(s.total_price), 0) as avg_sale_value,
            COALESCE(SUM(CASE 
                WHEN b.payment_status = 'paid' OR b.is_credit = 0 
                THEN (s.total_price - (COALESCE(p.cost, 0) * s.quantity))
                WHEN b.payment_status = 'partial' 
                THEN ((s.total_price - (COALESCE(p.cost, 0) * s.quantity)) * b.credit_paid_amount / b.total_amount)
                ELSE 0 
            END), 0) as net_profit,
            COALESCE(SUM(CASE 
                WHEN b.payment_status = 'pending' OR (b.is_credit = 1 AND b.payment_status != 'paid')
                THEN (s.total_price - (COALESCE(p.cost, 0) * s.quantity))
                WHEN b.payment_status = 'partial' 
                THEN ((s.total_price - (COALESCE(p.cost, 0) * s.quantity)) * b.credit_balance / b.total_amount)
                ELSE 0 
            END), 0) as receivable_profit,
            COALESCE(SUM(s.total_price - (COALESCE(p.cost, 0) * s.quantity)), 0) as total_profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        LEFT JOIN bills b ON s.bill_id = b.id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
    """
    
    summary_params = [start_date, end_date]
    
    if category != 'all':
        summary_query += ' AND s.category = ?'
        summary_params.append(category)
    
    if payment_method != 'all':
        summary_query += ' AND s.payment_method = ?'
        summary_params.append(payment_method)
    
    summary = conn.execute(summary_query, summary_params).fetchone()
    
    conn.close()
    
    # Calculate pagination info
    total_pages = (total_bills + per_page - 1) // per_page
    
    return jsonify({
        'success': True,
        'bills': bills_list,  # Changed from 'sales' to 'bills' for clarity
        'summary': dict(summary) if summary else {},
        'pagination': {
            'current_page': page,
            'per_page': per_page,
            'total_records': total_bills,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        },
        'filters': {
            'filter': date_filter,
            'startDate': start_date,
            'endDate': end_date,
            'category': category,
            'payment_method': payment_method,
            'page': page,
            'per_page': per_page
        },
        'debug_info': {
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'query_dates': f"{start_date} to {end_date}"
        }
    })
