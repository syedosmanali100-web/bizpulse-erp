"""
Sync Utilities
Helper functions for broadcasting data changes
"""

from flask import current_app, session
import logging

logger = logging.getLogger(__name__)

def broadcast_data_change(event_type: str, table_name: str, record_data: dict, user_id: str = None):
    """
    Broadcast data change to all connected devices
    
    Args:
        event_type: 'create', 'update', 'delete'
        table_name: Name of the table/entity that changed
        record_data: The record data that changed
        user_id: User ID (if not provided, will try to get from session)
    """
    try:
        # Get user_id from session if not provided
        if not user_id:
            user_id = session.get('user_id')
        
        if not user_id:
            logger.warning("❌ Cannot broadcast data change: No user_id")
            return False
        
        # Get socketio instance from app
        socketio = getattr(current_app, 'socketio', None)
        if not socketio:
            logger.warning("❌ SocketIO not available for broadcasting")
            return False
        
        # Import here to avoid circular imports
        from modules.sync.routes import broadcast_data_change as broadcast_func
        
        # Broadcast the change
        broadcast_func(
            user_id=user_id,
            event_type=event_type,
            data={
                'table': table_name,
                'record': record_data,
                'timestamp': record_data.get('updated_at') or record_data.get('created_at')
            },
            socketio=socketio
        )
        
        logger.info(f"📡 Broadcasted {event_type} on {table_name} for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to broadcast data change: {e}")
        return False

def sync_on_login(user_id: str):
    """
    Trigger sync when user logs in
    """
    try:
        from modules.sync.service import sync_service
        
        # Get latest data for user
        latest_data = sync_service.get_latest_data_for_user(user_id)
        
        logger.info(f"✅ Sync data prepared for user {user_id} login")
        return latest_data
        
    except Exception as e:
        logger.error(f"❌ Failed to prepare sync data on login: {e}")
        return {}

def queue_offline_change(event_type: str, table_name: str, record_data: dict):
    """
    Queue data change for offline sync (fallback when WebSocket fails)
    """
    try:
        from modules.sync.service import sync_service
        
        # This would be called when WebSocket is not available
        # For now, we'll just log it
        logger.info(f"📦 Queued offline change: {event_type} on {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to queue offline change: {e}")
        return False