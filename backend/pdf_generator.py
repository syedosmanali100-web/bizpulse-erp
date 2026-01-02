"""
PDF Generation Service for Daily Sales Reports
Generates professional PDF reports using HTML templates and WeasyPrint
"""

import os
from datetime import datetime, date
from weasyprint import HTML, CSS
from jinja2 import Template
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFGenerator:
    """
    Service class for generating PDF reports
    """
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    def generate_daily_sales_report(self, company_data, report_data, report_date):
        """
        Generate daily sales report PDF
        
        Args:
            company_data (dict): Company information
            report_data (dict): Sales data for the day
            report_date (date): Date of the report
            
        Returns:
            str: Path to generated PDF file
        """
        try:
            logger.info(f"Generating PDF report for {company_data['business_name']} - {report_date}")
            
            # Create HTML content from template
            html_content = self._create_html_template(company_data, report_data, report_date)
            
            # Generate PDF filename
            pdf_filename = f"DAILY_REPORT_{company_data['business_name'].replace(' ', '_').upper()}_{report_date.strftime('%Y-%m-%d')}.pdf"
            pdf_path = os.path.join(self.temp_dir, pdf_filename)
            
            # Generate PDF using WeasyPrint
            HTML(string=html_content).write_pdf(
                pdf_path,
                stylesheets=[CSS(string=self._get_css_styles())]
            )
            
            logger.info(f"PDF generated successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def _create_html_template(self, company_data, report_data, report_date):
        """
        Create HTML template for the PDF report
        
        Args:
            company_data (dict): Company information
            report_data (dict): Sales data
            report_date (date): Report date
            
        Returns:
            str: HTML content
        """
        
        # Calculate profit margin
        profit_margin = 0
        if report_data['total_sales'] > 0:
            profit_margin = (report_data['total_profit'] / report_data['total_sales']) * 100
        
        # Determine performance status
        performance_status = "Excellent" if profit_margin >= 30 else "Good" if profit_margin >= 20 else "Average" if profit_margin >= 10 else "Needs Improvement"
        performance_color = "#4CAF50" if profit_margin >= 30 else "#FF9800" if profit_margin >= 20 else "#2196F3" if profit_margin >= 10 else "#f44336"
        
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Sales Report - {{ company_name }}</title>
        </head>
        <body>
            <!-- Header Section -->
            <div class="header">
                <div class="logo-section">
                    <h1>📊 DAILY SALES REPORT</h1>
                    <div class="company-name">{{ company_name }}</div>
                </div>
                <div class="report-info">
                    <div class="report-date">{{ report_date_formatted }}</div>
                    <div class="generated-time">Generated: {{ generated_time }}</div>
                </div>
            </div>
            
            <!-- Summary Cards Section -->
            <div class="summary-section">
                <div class="summary-card sales-card">
                    <div class="card-icon">💰</div>
                    <div class="card-content">
                        <div class="card-title">Total Sales</div>
                        <div class="card-value">₹{{ total_sales_formatted }}</div>
                        <div class="card-subtitle">{{ total_invoices }} invoices</div>
                    </div>
                </div>
                
                <div class="summary-card profit-card">
                    <div class="card-icon">📈</div>
                    <div class="card-content">
                        <div class="card-title">Total Profit</div>
                        <div class="card-value">₹{{ total_profit_formatted }}</div>
                        <div class="card-subtitle">{{ profit_margin_formatted }}% margin</div>
                    </div>
                </div>
                
                <div class="summary-card performance-card">
                    <div class="card-icon">🎯</div>
                    <div class="card-content">
                        <div class="card-title">Performance</div>
                        <div class="card-value" style="color: {{ performance_color }}">{{ performance_status }}</div>
                        <div class="card-subtitle">Business health</div>
                    </div>
                </div>
            </div>
            
            <!-- Detailed Metrics Section -->
            <div class="metrics-section">
                <h2>📋 Detailed Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <span class="metric-label">Total Invoices:</span>
                        <span class="metric-value">{{ total_invoices }}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Average Invoice Value:</span>
                        <span class="metric-value">₹{{ avg_invoice_value }}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Total Revenue:</span>
                        <span class="metric-value">₹{{ total_sales_formatted }}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Total Cost:</span>
                        <span class="metric-value">₹{{ total_cost_formatted }}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Net Profit:</span>
                        <span class="metric-value">₹{{ total_profit_formatted }}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Profit Margin:</span>
                        <span class="metric-value">{{ profit_margin_formatted }}%</span>
                    </div>
                </div>
            </div>
            
            <!-- Business Insights Section -->
            <div class="insights-section">
                <h2>💡 Business Insights</h2>
                <div class="insights-grid">
                    {% if total_invoices > 0 %}
                    <div class="insight-item positive">
                        <span class="insight-icon">✅</span>
                        <span class="insight-text">Generated {{ total_invoices }} invoices today</span>
                    </div>
                    {% endif %}
                    
                    {% if profit_margin >= 20 %}
                    <div class="insight-item positive">
                        <span class="insight-icon">🎉</span>
                        <span class="insight-text">Excellent profit margin of {{ profit_margin_formatted }}%</span>
                    </div>
                    {% elif profit_margin >= 10 %}
                    <div class="insight-item neutral">
                        <span class="insight-icon">👍</span>
                        <span class="insight-text">Good profit margin of {{ profit_margin_formatted }}%</span>
                    </div>
                    {% else %}
                    <div class="insight-item warning">
                        <span class="insight-icon">⚠️</span>
                        <span class="insight-text">Consider reviewing pricing strategy</span>
                    </div>
                    {% endif %}
                    
                    {% if avg_invoice_value > 1000 %}
                    <div class="insight-item positive">
                        <span class="insight-icon">💎</span>
                        <span class="insight-text">High average invoice value: ₹{{ avg_invoice_value }}</span>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Footer Section -->
            <div class="footer">
                <div class="footer-content">
                    <div class="company-info">
                        <strong>{{ company_name }}</strong><br>
                        📞 {{ company_phone }}<br>
                        📧 {{ company_email }}
                    </div>
                    <div class="powered-by">
                        <div>Powered by <strong>BizPulse ERP</strong></div>
                        <div class="footer-note">Automated Daily Report System</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Calculate additional metrics
        avg_invoice_value = round(report_data['total_sales'] / report_data['total_invoices'], 2) if report_data['total_invoices'] > 0 else 0
        total_cost = report_data['total_sales'] - report_data['total_profit']
        
        # Prepare template data
        template_data = {
            'company_name': company_data['business_name'],
            'company_phone': company_data.get('phone_number', 'N/A'),
            'company_email': company_data.get('email', 'N/A'),
            'report_date_formatted': report_date.strftime('%B %d, %Y'),
            'generated_time': datetime.now().strftime('%I:%M %p'),
            'total_sales_formatted': f"{report_data['total_sales']:,.2f}",
            'total_profit_formatted': f"{report_data['total_profit']:,.2f}",
            'total_cost_formatted': f"{total_cost:,.2f}",
            'total_invoices': report_data['total_invoices'],
            'profit_margin_formatted': f"{profit_margin:.1f}",
            'avg_invoice_value': f"{avg_invoice_value:,.2f}",
            'performance_status': performance_status,
            'performance_color': performance_color
        }
        
        # Render template
        template = Template(html_template)
        return template.render(**template_data)
    
    def _get_css_styles(self):
        """
        Get CSS styles for the PDF report
        
        Returns:
            str: CSS styles
        """
        return """
        @page {
            size: A4;
            margin: 20mm;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        
        .header {
            background: linear-gradient(135deg, #732C3F 0%, #8B3A47 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .company-name {
            font-size: 20px;
            font-weight: 600;
            opacity: 0.9;
        }
        
        .report-info {
            text-align: right;
        }
        
        .report-date {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .generated-time {
            font-size: 14px;
            opacity: 0.8;
        }
        
        .summary-section {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            flex: 1;
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .card-icon {
            font-size: 40px;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8f9fa;
            border-radius: 50%;
        }
        
        .card-title {
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .card-value {
            font-size: 24px;
            font-weight: bold;
            color: #732C3F;
            margin-bottom: 4px;
        }
        
        .card-subtitle {
            font-size: 12px;
            color: #999;
        }
        
        .metrics-section, .insights-section {
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .metrics-section h2, .insights-section h2 {
            font-size: 20px;
            color: #732C3F;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .metric-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .metric-label {
            font-weight: 500;
            color: #666;
        }
        
        .metric-value {
            font-weight: 600;
            color: #732C3F;
        }
        
        .insights-grid {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .insight-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 8px;
        }
        
        .insight-item.positive {
            background: #e8f5e9;
            border-left: 4px solid #4CAF50;
        }
        
        .insight-item.neutral {
            background: #fff3e0;
            border-left: 4px solid #FF9800;
        }
        
        .insight-item.warning {
            background: #ffebee;
            border-left: 4px solid #f44336;
        }
        
        .insight-icon {
            font-size: 18px;
        }
        
        .insight-text {
            font-weight: 500;
            color: #333;
        }
        
        .footer {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
            border-top: 3px solid #732C3F;
        }
        
        .footer-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .company-info {
            font-size: 14px;
            line-height: 1.8;
        }
        
        .powered-by {
            text-align: right;
            font-size: 14px;
        }
        
        .footer-note {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        """
    
    def cleanup_temp_files(self, file_path):
        """
        Clean up temporary PDF files
        
        Args:
            file_path (str): Path to file to delete
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not clean up file {file_path}: {str(e)}")