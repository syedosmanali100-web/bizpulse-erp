"""
Report Generation Service for Daily Sales Reports
Handles data collection, PDF generation, and WhatsApp delivery
"""

import sqlite3
import logging
from datetime import datetime, date, timedelta
from .pdf_generator import PDFGenerator
from .whatsapp_service import WhatsAppService
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportService:
    """
    Service class for generating and sending daily reports
    """
    
    def __init__(self, db_path='billing.db'):
        self.db_path = db_path
        self.pdf_generator = PDFGenerator()
        self.whatsapp_service = WhatsAppService()
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def generate_id(self):
        """Generate unique ID"""
        return str(uuid.uuid4())
    
    def get_companies_for_reports(self):
        """
        Get all companies that should receive daily reports
        
        Returns:
            list: Companies with send_daily_report = True
        """
        conn = self.get_db_connection()
        
        companies = conn.execute('''
            SELECT * FROM companies 
            WHERE is_active = 1 AND send_daily_report = 1
            ORDER BY business_name
        ''').fetchall()
        
        conn.close()
        return [dict(row) for row in companies]
    
    def get_daily_sales_data(self, company_id, report_date):
        """
        Get daily sales data for a specific company and date
        
        Args:
            company_id (str): Company ID
            report_date (date): Date for the report
            
        Returns:
            dict: Sales data including totals and profit
        """
        conn = self.get_db_connection()
        
        try:
            # Get invoices for the day
            invoices_data = conn.execute('''
                SELECT 
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_sales,
                    COALESCE(SUM(total_cost), 0) as total_cost,
                    COALESCE(SUM(profit_amount), 0) as total_profit
                FROM invoices 
                WHERE company_id = ? AND DATE(invoice_date) = ?
            ''', (company_id, report_date.strftime('%Y-%m-%d'))).fetchone()
            
            # If no invoices table data, fall back to bills table
            if not invoices_data or invoices_data['total_invoices'] == 0:
                bills_data = conn.execute('''
                    SELECT 
                        COUNT(*) as total_invoices,
                        COALESCE(SUM(total_amount), 0) as total_sales
                    FROM bills 
                    WHERE DATE(created_at) = ?
                ''', (report_date.strftime('%Y-%m-%d'),)).fetchone()
                
                # Calculate estimated profit (assuming 20% margin if no cost data)
                total_sales = float(bills_data['total_sales']) if bills_data else 0
                estimated_profit = total_sales * 0.20  # 20% estimated margin
                
                return {
                    'total_invoices': bills_data['total_invoices'] if bills_data else 0,
                    'total_sales': total_sales,
                    'total_cost': total_sales - estimated_profit,
                    'total_profit': estimated_profit
                }
            
            return {
                'total_invoices': invoices_data['total_invoices'],
                'total_sales': float(invoices_data['total_sales']),
                'total_cost': float(invoices_data['total_cost']),
                'total_profit': float(invoices_data['total_profit'])
            }
            
        except Exception as e:
            logger.error(f"Error getting sales data: {str(e)}")
            return {
                'total_invoices': 0,
                'total_sales': 0.0,
                'total_cost': 0.0,
                'total_profit': 0.0
            }
        finally:
            conn.close()
    
    def generate_daily_report(self, company_id, report_date=None):
        """
        Generate daily report for a specific company
        
        Args:
            company_id (str): Company ID
            report_date (date, optional): Date for report. Defaults to today.
            
        Returns:
            dict: Result with PDF path and report data
        """
        if report_date is None:
            report_date = date.today()
        
        conn = self.get_db_connection()
        
        try:
            # Get company data
            company = conn.execute('''
                SELECT * FROM companies WHERE id = ? AND is_active = 1
            ''', (company_id,)).fetchone()
            
            if not company:
                return {
                    'success': False,
                    'error': f'Company not found or inactive: {company_id}'
                }
            
            company_data = dict(company)
            
            # Get sales data for the date
            report_data = self.get_daily_sales_data(company_id, report_date)
            
            # Generate PDF
            pdf_path = self.pdf_generator.generate_daily_sales_report(
                company_data, 
                report_data, 
                report_date
            )
            
            logger.info(f"Daily report generated for {company_data['business_name']} - {report_date}")
            
            return {
                'success': True,
                'pdf_path': pdf_path,
                'company_data': company_data,
                'report_data': report_data,
                'report_date': report_date
            }
            
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
            return {
                'success': False,
                'error': f'Report generation failed: {str(e)}'
            }
        finally:
            conn.close()
    
    def send_daily_report_whatsapp(self, company_id, report_date=None):
        """
        Generate and send daily report via WhatsApp
        
        Args:
            company_id (str): Company ID
            report_date (date, optional): Date for report. Defaults to today.
            
        Returns:
            dict: Complete result with all details
        """
        if report_date is None:
            report_date = date.today()
        
        # Generate report
        report_result = self.generate_daily_report(company_id, report_date)
        
        if not report_result['success']:
            return report_result
        
        # Send via WhatsApp
        whatsapp_result = self.whatsapp_service.send_daily_report(
            report_result['company_data'],
            report_result['report_data'],
            report_result['pdf_path']
        )
        
        # Log the attempt
        log_result = self.log_whatsapp_report(
            company_id,
            report_date,
            report_result['report_data'],
            whatsapp_result
        )
        
        # Clean up PDF file
        try:
            self.pdf_generator.cleanup_temp_files(report_result['pdf_path'])
        except Exception as e:
            logger.warning(f"Could not clean up PDF file: {str(e)}")
        
        return {
            'success': whatsapp_result['success'],
            'company_data': report_result['company_data'],
            'report_data': report_result['report_data'],
            'whatsapp_result': whatsapp_result,
            'log_id': log_result.get('log_id'),
            'error': whatsapp_result.get('error') if not whatsapp_result['success'] else None
        }
    
    def log_whatsapp_report(self, company_id, report_date, report_data, whatsapp_result):
        """
        Log WhatsApp report attempt to database
        
        Args:
            company_id (str): Company ID
            report_date (date): Report date
            report_data (dict): Report data
            whatsapp_result (dict): WhatsApp send result
            
        Returns:
            dict: Log result
        """
        conn = self.get_db_connection()
        
        try:
            log_id = self.generate_id()
            
            status = 'sent' if whatsapp_result['success'] else 'failed'
            error_message = whatsapp_result.get('error') if not whatsapp_result['success'] else None
            
            conn.execute('''
                INSERT INTO whatsapp_reports_log (
                    id, company_id, report_date, report_type, whatsapp_number,
                    pdf_filename, media_id, message_id, status,
                    total_sales, total_profit, total_invoices,
                    error_message, sent_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id, company_id, report_date.strftime('%Y-%m-%d'), 'daily_sales',
                whatsapp_result.get('whatsapp_number'),
                whatsapp_result.get('filename'),
                whatsapp_result.get('media_id'),
                whatsapp_result.get('message_id'),
                status,
                report_data['total_sales'],
                report_data['total_profit'],
                report_data['total_invoices'],
                error_message,
                datetime.now().isoformat() if whatsapp_result['success'] else None
            ))
            
            conn.commit()
            
            logger.info(f"WhatsApp report logged: {log_id} - Status: {status}")
            
            return {
                'success': True,
                'log_id': log_id
            }
            
        except Exception as e:
            logger.error(f"Error logging WhatsApp report: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def send_reports_to_all_companies(self, report_date=None):
        """
        Send daily reports to all companies that have it enabled
        
        Args:
            report_date (date, optional): Date for reports. Defaults to today.
            
        Returns:
            dict: Summary of all sent reports
        """
        if report_date is None:
            report_date = date.today()
        
        companies = self.get_companies_for_reports()
        results = []
        
        logger.info(f"Starting daily reports for {len(companies)} companies - {report_date}")
        
        for company in companies:
            try:
                result = self.send_daily_report_whatsapp(company['id'], report_date)
                results.append({
                    'company_id': company['id'],
                    'company_name': company['business_name'],
                    'success': result['success'],
                    'error': result.get('error'),
                    'total_sales': result.get('report_data', {}).get('total_sales', 0),
                    'total_profit': result.get('report_data', {}).get('total_profit', 0),
                    'total_invoices': result.get('report_data', {}).get('total_invoices', 0)
                })
                
                if result['success']:
                    logger.info(f"✅ Report sent to {company['business_name']}")
                else:
                    logger.error(f"❌ Failed to send report to {company['business_name']}: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {company['business_name']}: {str(e)}")
                results.append({
                    'company_id': company['id'],
                    'company_name': company['business_name'],
                    'success': False,
                    'error': str(e),
                    'total_sales': 0,
                    'total_profit': 0,
                    'total_invoices': 0
                })
        
        # Summary
        successful = len([r for r in results if r['success']])
        failed = len(results) - successful
        
        logger.info(f"Daily reports completed: {successful} successful, {failed} failed")
        
        return {
            'success': True,
            'report_date': report_date.strftime('%Y-%m-%d'),
            'total_companies': len(companies),
            'successful_reports': successful,
            'failed_reports': failed,
            'results': results
        }
    
    def get_report_logs(self, company_id=None, days=7):
        """
        Get WhatsApp report logs
        
        Args:
            company_id (str, optional): Filter by company ID
            days (int): Number of days to look back
            
        Returns:
            list: Report logs
        """
        conn = self.get_db_connection()
        
        try:
            query = '''
                SELECT 
                    wrl.*,
                    c.business_name
                FROM whatsapp_reports_log wrl
                JOIN companies c ON wrl.company_id = c.id
                WHERE wrl.report_date >= DATE('now', '-{} days')
            '''.format(days)
            
            params = []
            
            if company_id:
                query += ' AND wrl.company_id = ?'
                params.append(company_id)
            
            query += ' ORDER BY wrl.created_at DESC'
            
            logs = conn.execute(query, params).fetchall()
            
            return [dict(row) for row in logs]
            
        except Exception as e:
            logger.error(f"Error getting report logs: {str(e)}")
            return []
        finally:
            conn.close()
    
    def validate_whatsapp_config(self):
        """
        Validate WhatsApp configuration
        
        Returns:
            dict: Validation result
        """
        return self.whatsapp_service.validate_configuration()