"""
Daily Reports Scheduler
Runs daily at 11:55 PM to send WhatsApp reports to all companies
"""

import schedule
import time
import logging
from datetime import datetime
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_daily_reports():
    """
    Execute daily reports job
    """
    try:
        logger.info("🕐 Starting scheduled daily reports...")
        
        # Import services
        from services.report_service import ReportService
        
        # Initialize service
        report_service = ReportService()
        
        # Send reports to all companies
        result = report_service.send_reports_to_all_companies()
        
        if result['successful_reports'] > 0:
            logger.info(f"✅ Daily reports completed successfully:")
            logger.info(f"   - Total companies: {result['total_companies']}")
            logger.info(f"   - Successful: {result['successful_reports']}")
            logger.info(f"   - Failed: {result['failed_reports']}")
        else:
            logger.warning(f"⚠️  No reports sent successfully:")
            logger.warning(f"   - Total companies: {result['total_companies']}")
            logger.warning(f"   - Failed: {result['failed_reports']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Daily reports job failed: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """
    Main scheduler function
    """
    logger.info("🚀 BizPulse Daily Reports Scheduler Starting...")
    logger.info("📅 Scheduled to run daily at 11:55 PM")
    
    # Schedule the job for 11:55 PM daily
    schedule.every().day.at("23:55").do(run_daily_reports)
    
    # Also add a test schedule (every 5 minutes for testing - comment out in production)
    # schedule.every(5).minutes.do(run_daily_reports)
    
    logger.info("⏰ Scheduler is running. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {str(e)}")

if __name__ == "__main__":
    main()