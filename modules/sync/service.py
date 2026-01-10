"""
Real-time Data Sync Service
Handles multi-device synchronization using WebSockets
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from modules.shared.database import get_db_connection
import logging

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self):
        self.active_sessions = {}  # {session_id: {user_id, device_info, last_seen}}
        self.sync_queue = {}       # {user_id: [sync_events]}
        
    def register_session(self, session_id: str, user_id: str, device_info: Dict) -> bool:
        """Register a new device session"""
        try:
            self.active_sessions[session_id] = {
                'user_id': user_id,
                'device_info': device_info,
                'last_seen': time.time(),
                'connected_at': datetime.now().isoformat()
            }
            
            # Initialize sync queue for user if not exists
            if user_id not in self.sync_queue:
                self.sync_queue[user_id] = []
                
            logger.info(f"✅ Session registered: {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register session: {e}")
            return False
    
    def unregister_session(self, session_id: str) -> bool:
        """Unregister a device session"""
        try:
            if session_id in self.active_sessions:
                user_id = self.active_sessions[session_id]['user_id']
                del self.active_sessions[session_id]
                logger.info(f"✅ Session unregistered: {session_id} for user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to unregister session: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active sessions for a user"""
        return [
            session_id for session_id, data in self.active_sessions.items()
            if data['user_id'] == user_id
        ]
    
    def create_sync_event(self, user_id: str, event_type: str, data: Dict, source_session: str = None) -> Dict:
        """Create a sync event for distribution"""
        sync_event = {
            'id': f"sync_{int(time.time() * 1000)}",
            'user_id': user_id,
            'event_type': event_type,  # 'create', 'update', 'delete'
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'source_session': source_session
        }
        
        # Add to sync queue
        if user_id not in self.sync_queue:
            self.sync_queue[user_id] = []
        
        self.sync_queue[user_id].append(sync_event)
        
        # Keep only last 100 events per user
        if len(self.sync_queue[user_id]) > 100:
            self.sync_queue[user_id] = self.sync_queue[user_id][-100:]
            
        return sync_event
    
    def get_pending_sync_events(self, user_id: str, since_timestamp: str = None) -> List[Dict]:
        """Get pending sync events for a user since timestamp"""
        if user_id not in self.sync_queue:
            return []
        
        events = self.sync_queue[user_id]
        
        if since_timestamp:
            # Filter events after timestamp
            events = [
                event for event in events
                if event['timestamp'] > since_timestamp
            ]
        
        return events
    
    def mark_session_active(self, session_id: str):
        """Update last seen timestamp for session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['last_seen'] = time.time()
    
    def cleanup_inactive_sessions(self, timeout_seconds: int = 300):  # 5 minutes
        """Remove inactive sessions"""
        current_time = time.time()
        inactive_sessions = [
            session_id for session_id, data in self.active_sessions.items()
            if current_time - data['last_seen'] > timeout_seconds
        ]
        
        for session_id in inactive_sessions:
            self.unregister_session(session_id)
            
        if inactive_sessions:
            logger.info(f"🧹 Cleaned up {len(inactive_sessions)} inactive sessions")
    
    def get_sync_stats(self) -> Dict:
        """Get sync system statistics"""
        return {
            'active_sessions': len(self.active_sessions),
            'total_users': len(set(data['user_id'] for data in self.active_sessions.values())),
            'sync_queue_size': sum(len(events) for events in self.sync_queue.values()),
            'sessions_by_user': {
                user_id: len(self.get_user_sessions(user_id))
                for user_id in set(data['user_id'] for data in self.active_sessions.values())
            }
        }
    
    def get_latest_data_for_user(self, user_id: str) -> Dict:
        """Get latest data snapshot for user (called on login)"""
        conn = get_db_connection()
        try:
            # Get latest data from all relevant tables
            latest_data = {}
            
            # Products
            products = conn.execute("""
                SELECT * FROM products 
                WHERE user_id = ? 
                ORDER BY updated_at DESC LIMIT 100
            """, (user_id,)).fetchall()
            latest_data['products'] = [dict(row) for row in products] if products else []
            
            # Sales
            sales = conn.execute("""
                SELECT * FROM sales 
                WHERE user_id = ? 
                ORDER BY created_at DESC LIMIT 50
            """, (user_id,)).fetchall()
            latest_data['sales'] = [dict(row) for row in sales] if sales else []
            
            # Customers
            customers = conn.execute("""
                SELECT * FROM customers 
                WHERE user_id = ? 
                ORDER BY updated_at DESC LIMIT 100
            """, (user_id,)).fetchall()
            latest_data['customers'] = [dict(row) for row in customers] if customers else []
            
            # Invoices (bills)
            invoices = conn.execute("""
                SELECT * FROM bills 
                WHERE user_id = ? 
                ORDER BY created_at DESC LIMIT 50
            """, (user_id,)).fetchall()
            latest_data['invoices'] = [dict(row) for row in invoices] if invoices else []
            
            latest_data['sync_timestamp'] = datetime.now().isoformat()
            
            return latest_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest data: {e}")
            import traceback
            traceback.print_exc()
            return {}
        finally:
            conn.close()

# Global sync service instance
sync_service = SyncService()