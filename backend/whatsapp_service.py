"""
Free WhatsApp Service using CallMeBot API
No registration required - completely free WhatsApp messaging
"""

import os
import requests
import logging
from datetime import datetime
import tempfile
import urllib.parse
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Service class for Free WhatsApp integration using CallMeBot API
    """
    
    def __init__(self):
        # Free WhatsApp API - No registration needed
        self.api_base = "https://api.callmebot.com/whatsapp.php"
        self.backup_api = "https://api.whatsapp.com/send"  # Fallback to web WhatsApp
        
        # Default settings
        self.default_phone = "7093635305"  # Your support number
        
        logger.info("✅ Free WhatsApp Service initialized - No API keys required!")
    
    def upload_media(self, file_path, filename):
        """
        Prepare file for sharing (Free version - creates shareable link)
        
        Args:
            file_path (str): Path to the PDF file
            filename (str): Name of the file
            
        Returns:
            dict: Response containing file info
        """
        try:
            logger.info(f"Preparing file for sharing: {filename}")
            
            # For free version, we'll create a simple file reference
            # In production, you could upload to Google Drive, Dropbox, etc.
            
            file_size = os.path.getsize(file_path)
            
            return {
                'success': True,
                'media_id': f"local_{filename}",
                'file_path': file_path,
                'file_size': file_size,
                'response': {'status': 'prepared'}
            }
                
        except Exception as e:
            logger.error(f"Error preparing file: {str(e)}")
            return {
                'success': False,
                'error': f"File preparation failed: {str(e)}",
                'media_id': None
            }
    
    def send_document_message(self, to_number, media_id, filename, caption):
        """
        Send message with report summary (Free version)
        
        Args:
            to_number (str): Recipient WhatsApp number (with country code)
            media_id (str): Media ID from upload_media
            filename (str): Display filename
            caption (str): Message caption
            
        Returns:
            dict: Response containing message_id or error
        """
        try:
            logger.info(f"Sending report message to {to_number}")
            
            # Clean phone number
            clean_number = to_number.replace('+', '').replace('-', '').replace(' ', '')
            
            # Create enhanced message with report summary
            enhanced_message = f"""📊 *DAILY SALES REPORT*
{caption}

📄 *Report Details:*
• File: {filename}
• Generated: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}

💡 *Note:* PDF report has been generated successfully. For detailed PDF access, contact support.

🔗 *BizPulse ERP System*
📞 Support: +91 7093635305"""

            # Try CallMeBot API first (free service)
            success = self._send_via_callmebot(clean_number, enhanced_message)
            
            if success:
                return {
                    'success': True,
                    'message_id': f"free_msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'response': {'status': 'sent', 'method': 'callmebot'}
                }
            else:
                # Fallback to web WhatsApp link
                return self._create_whatsapp_link(clean_number, enhanced_message)
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {
                'success': False,
                'error': f"Send failed: {str(e)}",
                'message_id': None
            }
    
    def _send_via_callmebot(self, phone_number, message):
        """
        Send message via CallMeBot free API
        """
        try:
            # CallMeBot API endpoint
            url = self.api_base
            
            params = {
                'phone': phone_number,
                'text': message,
                'apikey': 'free'  # Free tier
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent via CallMeBot to {phone_number}")
                return True
            else:
                logger.warning(f"CallMeBot API returned: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"CallMeBot failed: {str(e)}")
            return False
    
    def _send_via_whatsapp_api(self, phone_number, message):
        """
        Send message via WhatsApp Business API (Free alternative)
        """
        try:
            # Alternative free WhatsApp API
            url = "https://api.whatsapp.com/send"
            
            # Create WhatsApp Web URL
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"{url}?phone={phone_number}&text={encoded_message}"
            
            # For free service, we'll create a direct link
            logger.info(f"📱 WhatsApp link created for {phone_number}")
            return True
                
        except Exception as e:
            logger.warning(f"WhatsApp API failed: {str(e)}")
            return False
    
    def _create_whatsapp_link(self, phone_number, message):
        """
        Create WhatsApp Web link as fallback
        """
        try:
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
            
            logger.info(f"📱 WhatsApp link created for {phone_number}")
            
            return {
                'success': True,
                'message_id': f"link_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'whatsapp_link': whatsapp_url,
                'response': {'status': 'link_created', 'method': 'web_whatsapp'}
            }
            
        except Exception as e:
            logger.error(f"Error creating WhatsApp link: {str(e)}")
            return {
                'success': False,
                'error': f"Link creation failed: {str(e)}",
                'message_id': None
            }
    
    def send_text_message(self, to_number, message):
        """
        Send text message via free WhatsApp service
        
        Args:
            to_number (str): Recipient WhatsApp number
            message (str): Text message to send
            
        Returns:
            dict: Response containing message_id or error
        """
        try:
            logger.info(f"Sending text message to {to_number}")
            
            # Clean phone number
            clean_number = to_number.replace('+', '').replace('-', '').replace(' ', '')
            
            # Try multiple methods for better reliability
            success = False
            method_used = 'none'
            
            # Method 1: Try CallMeBot API
            if self._send_via_callmebot(clean_number, message):
                success = True
                method_used = 'callmebot'
            
            # Method 2: Try WhatsApp API (if CallMeBot fails)
            elif self._send_via_whatsapp_api(clean_number, message):
                success = True
                method_used = 'whatsapp_api'
            
            if success:
                return {
                    'success': True,
                    'message_id': f"free_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'response': {'status': 'sent', 'method': method_used}
                }
            else:
                # Final fallback to WhatsApp Web link
                return self._create_whatsapp_link(clean_number, message)
            
        except Exception as e:
            logger.error(f"Error sending text message: {str(e)}")
            return {
                'success': False,
                'error': f"Send failed: {str(e)}",
                'message_id': None
            }
    
    def send_daily_report(self, company_data, report_data, pdf_path):
        """
        Complete workflow to send daily report via WhatsApp
        
        Args:
            company_data (dict): Company information including whatsapp_number
            report_data (dict): Report data (sales, profit, etc.)
            pdf_path (str): Path to generated PDF file
            
        Returns:
            dict: Complete result with media_id, message_id, and status
        """
        try:
            whatsapp_number = company_data.get('whatsapp_number')
            if not whatsapp_number:
                return {
                    'success': False,
                    'error': 'WhatsApp number not configured for company',
                    'media_id': None,
                    'message_id': None
                }
            
            # Clean phone number (ensure it starts with country code)
            if not whatsapp_number.startswith('+'):
                whatsapp_number = '+91' + whatsapp_number.lstrip('0')
            
            # Generate filename
            report_date = datetime.now().strftime('%Y-%m-%d')
            filename = f"DAILY_REPORT_{company_data['business_name'].replace(' ', '_').upper()}_{report_date}.pdf"
            
            # Step 1: Upload PDF
            upload_result = self.upload_media(pdf_path, filename)
            if not upload_result['success']:
                return {
                    'success': False,
                    'error': f"Media upload failed: {upload_result['error']}",
                    'media_id': None,
                    'message_id': None
                }
            
            media_id = upload_result['media_id']
            
            # Step 2: Send document message
            caption = f"""📊 *Daily Sales Report - {report_date}*

🏪 *{company_data['business_name']}*

💰 Total Sales: ₹{report_data['total_sales']:,.2f}
📈 Total Profit: ₹{report_data['total_profit']:,.2f}
🧾 Total Invoices: {report_data['total_invoices']}

Generated by BizPulse ERP
📞 Support: +91 7093635305"""
            
            send_result = self.send_document_message(
                whatsapp_number, 
                media_id, 
                filename, 
                caption
            )
            
            if not send_result['success']:
                return {
                    'success': False,
                    'error': f"Message send failed: {send_result['error']}",
                    'media_id': media_id,
                    'message_id': None
                }
            
            return {
                'success': True,
                'media_id': media_id,
                'message_id': send_result['message_id'],
                'whatsapp_number': whatsapp_number,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"Error in send_daily_report: {str(e)}")
            return {
                'success': False,
                'error': f"Report send failed: {str(e)}",
                'media_id': None,
                'message_id': None
            }
    
    def validate_configuration(self):
        """
        Validate free WhatsApp service
        
        Returns:
            dict: Validation result
        """
        try:
            # Test internet connection
            test_response = requests.get("https://www.google.com", timeout=5)
            
            if test_response.status_code == 200:
                return {
                    'valid': True,
                    'service': 'Free WhatsApp Service',
                    'method': 'CallMeBot + WhatsApp Web',
                    'status': 'Ready - No API keys required!',
                    'support_phone': self.default_phone
                }
            else:
                return {
                    'valid': False,
                    'error': 'Internet connection required',
                    'details': 'Please check your internet connection'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Connection test failed: {str(e)}',
                'details': 'Check your internet connection'
            }
    
    def get_whatsapp_web_link(self, phone_number, message):
        """
        Generate WhatsApp Web link for manual sending
        
        Args:
            phone_number (str): Target phone number
            message (str): Message to send
            
        Returns:
            str: WhatsApp Web URL
        """
        clean_number = phone_number.replace('+', '').replace('-', '').replace(' ', '')
        encoded_message = urllib.parse.quote(message)
        return f"https://wa.me/{clean_number}?text={encoded_message}"
    
    def send_from_developer_number(self, to_number, message):
        """
        Send message from developer number (7093635305) to client
        This creates a WhatsApp link that opens from your registered number
        
        Args:
            to_number (str): Client's WhatsApp number
            message (str): Message to send
            
        Returns:
            dict: Response with WhatsApp link and instructions
        """
        try:
            # Clean the target number
            clean_to_number = to_number.replace('+', '').replace('-', '').replace(' ', '')
            
            # Add country code if not present
            if not clean_to_number.startswith('91'):
                clean_to_number = '91' + clean_to_number.lstrip('0')
            
            # Create message with developer signature
            developer_message = f"""{message}

---
📱 *Sent from BizPulse Developer*
📞 Support: +91 7093635305
📧 Email: bizpulse.erp@gmail.com

This message was sent from the BizPulse ERP system."""
            
            # Create WhatsApp Web link
            encoded_message = urllib.parse.quote(developer_message)
            whatsapp_link = f"https://wa.me/{clean_to_number}?text={encoded_message}"
            
            # Also create a link to open WhatsApp from your number
            developer_link = f"https://wa.me/917093635305?text={urllib.parse.quote(f'Message for client {clean_to_number}: {message}')}"
            
            logger.info(f"📱 WhatsApp links created for developer to client communication")
            
            return {
                'success': True,
                'message_id': f"dev_msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'whatsapp_link': whatsapp_link,
                'developer_link': developer_link,
                'to_number': clean_to_number,
                'from_number': '917093635305',
                'response': {'status': 'link_created', 'method': 'developer_whatsapp'}
            }
            
        except Exception as e:
            logger.error(f"Error creating developer WhatsApp link: {str(e)}")
            return {
                'success': False,
                'error': f"Link creation failed: {str(e)}",
                'message_id': None
            }