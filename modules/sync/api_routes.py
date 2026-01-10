"""
Sync API Routes
REST endpoints for data synchronization
"""

from flask import Blueprint, request, jsonify, session
from modules.sync.service import sync_service
from modules.shared.auth_decorators import require_auth
import logging

logger = logging.getLogger(__name__)

sync_api_bp = Blueprint('sync_api', __name__, url_prefix='/api/sync')

@sync_api_bp.route('/status', methods=['GET'])
@require_auth
def get_sync_status():
    """Get sync system status"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User not authenticated'}), 401
        
        stats = sync_service.get_sync_stats()
        user_sessions = sync_service.get_user_sessions(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'user_sessions': len(user_sessions),
                'system_stats': stats,
                'connected_devices': user_sessions
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Sync status error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@sync_api_bp.route('/latest-data', methods=['GET'])
@require_auth
def get_latest_data():
    """Get latest data for user (called on login)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User not authenticated'}), 401
        
        latest_data = sync_service.get_latest_data_for_user(user_id)
        
        return jsonify({
            'success': True,
            'data': latest_data,
            'message': 'Latest data retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Latest data error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@sync_api_bp.route('/pending-events', methods=['GET'])
@require_auth
def get_pending_events():
    """Get pending sync events for user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User not authenticated'}), 401
        
        since_timestamp = request.args.get('since')
        pending_events = sync_service.get_pending_sync_events(user_id, since_timestamp)
        
        return jsonify({
            'success': True,
            'data': {
                'events': pending_events,
                'count': len(pending_events)
            },
            'message': f'Retrieved {len(pending_events)} pending events'
        })
        
    except Exception as e:
        logger.error(f"❌ Pending events error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@sync_api_bp.route('/force-sync', methods=['POST'])
@require_auth
def force_sync():
    """Force sync for user (manual trigger)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User not authenticated'}), 401
        
        # Get latest data
        latest_data = sync_service.get_latest_data_for_user(user_id)
        
        # Get pending events
        pending_events = sync_service.get_pending_sync_events(user_id)
        
        # Broadcast sync event to all user devices
        from app import socketio
        socketio.emit('force_sync', {
            'latest_data': latest_data,
            'pending_events': pending_events,
            'timestamp': latest_data.get('sync_timestamp')
        }, room=f"user_{user_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'latest_data': latest_data,
                'pending_events': pending_events,
                'synced_devices': len(sync_service.get_user_sessions(user_id))
            },
            'message': 'Force sync completed successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Force sync error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500