"""
Real-time Sync WebSocket Routes
Handles WebSocket connections for multi-device sync
"""

from flask import request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from modules.sync.service import sync_service
import json
import logging

logger = logging.getLogger(__name__)

def init_socketio_events(socketio: SocketIO):
    """Initialize WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        try:
            # Get user info from session or token
            user_id = session.get('user_id')
            if not user_id:
                # Try to get from query params (for mobile apps)
                user_id = request.args.get('user_id')
            
            if not user_id:
                logger.warning("❌ WebSocket connection rejected: No user_id")
                disconnect()
                return False
            
            # Get device info
            device_info = {
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.remote_addr,
                'platform': request.args.get('platform', 'web')
            }
            
            # Register session
            session_id = request.sid
            success = sync_service.register_session(session_id, user_id, device_info)
            
            if success:
                # Join user room for targeted broadcasts
                join_room(f"user_{user_id}")
                
                # Send initial sync data
                latest_data = sync_service.get_latest_data_for_user(user_id)
                emit('initial_sync', {
                    'success': True,
                    'data': latest_data,
                    'message': 'Connected and synced'
                })
                
                # Notify other devices about new connection
                emit('device_connected', {
                    'device_info': device_info,
                    'timestamp': latest_data.get('sync_timestamp')
                }, room=f"user_{user_id}", include_self=False)
                
                logger.info(f"✅ WebSocket connected: {session_id} for user {user_id}")
                
            else:
                disconnect()
                return False
                
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            disconnect()
            return False
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            session_id = request.sid
            if session_id in sync_service.active_sessions:
                user_id = sync_service.active_sessions[session_id]['user_id']
                leave_room(f"user_{user_id}")
                sync_service.unregister_session(session_id)
                
                # Notify other devices about disconnection
                emit('device_disconnected', {
                    'session_id': session_id,
                    'timestamp': sync_service.get_latest_data_for_user(user_id).get('sync_timestamp')
                }, room=f"user_{user_id}")
                
                logger.info(f"✅ WebSocket disconnected: {session_id}")
                
        except Exception as e:
            logger.error(f"❌ WebSocket disconnect error: {e}")
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for keepalive"""
        session_id = request.sid
        sync_service.mark_session_active(session_id)
        emit('pong', {'timestamp': sync_service.get_latest_data_for_user(
            sync_service.active_sessions.get(session_id, {}).get('user_id', '')
        ).get('sync_timestamp')})
    
    @socketio.on('request_sync')
    def handle_sync_request(data):
        """Handle manual sync request"""
        try:
            session_id = request.sid
            if session_id not in sync_service.active_sessions:
                emit('sync_error', {'message': 'Session not found'})
                return
            
            user_id = sync_service.active_sessions[session_id]['user_id']
            since_timestamp = data.get('since_timestamp')
            
            # Get pending sync events
            pending_events = sync_service.get_pending_sync_events(user_id, since_timestamp)
            
            # Get latest data if requested
            include_full_data = data.get('include_full_data', False)
            latest_data = None
            if include_full_data:
                latest_data = sync_service.get_latest_data_for_user(user_id)
            
            emit('sync_response', {
                'success': True,
                'pending_events': pending_events,
                'latest_data': latest_data,
                'timestamp': sync_service.get_latest_data_for_user(user_id).get('sync_timestamp')
            })
            
            sync_service.mark_session_active(session_id)
            
        except Exception as e:
            logger.error(f"❌ Sync request error: {e}")
            emit('sync_error', {'message': str(e)})
    
    @socketio.on('data_changed')
    def handle_data_change(data):
        """Handle data change notification from client"""
        try:
            session_id = request.sid
            if session_id not in sync_service.active_sessions:
                emit('sync_error', {'message': 'Session not found'})
                return
            
            user_id = sync_service.active_sessions[session_id]['user_id']
            
            # Create sync event
            sync_event = sync_service.create_sync_event(
                user_id=user_id,
                event_type=data.get('event_type', 'update'),
                data=data.get('data', {}),
                source_session=session_id
            )
            
            # Broadcast to other devices of the same user
            emit('data_sync', {
                'event': sync_event,
                'source_session': session_id
            }, room=f"user_{user_id}", include_self=False)
            
            sync_service.mark_session_active(session_id)
            
            logger.info(f"📡 Data change broadcasted for user {user_id}: {data.get('event_type')}")
            
        except Exception as e:
            logger.error(f"❌ Data change error: {e}")
            emit('sync_error', {'message': str(e)})

def broadcast_data_change(user_id: str, event_type: str, data: dict, socketio: SocketIO, source_session: str = None):
    """Broadcast data change to all user devices (called from API endpoints)"""
    try:
        # Create sync event
        sync_event = sync_service.create_sync_event(
            user_id=user_id,
            event_type=event_type,
            data=data,
            source_session=source_session
        )
        
        # Broadcast to all user devices
        socketio.emit('data_sync', {
            'event': sync_event,
            'source_session': source_session
        }, room=f"user_{user_id}")
        
        logger.info(f"📡 API data change broadcasted for user {user_id}: {event_type}")
        
    except Exception as e:
        logger.error(f"❌ Broadcast error: {e}")