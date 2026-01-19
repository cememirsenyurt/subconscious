"""
Debug routes for testing and monitoring.
"""

from flask import Blueprint, jsonify
from services import customer_db, smart_memory
from services.subconscious_api import SUBCONSCIOUS_API_KEY, SDK_AVAILABLE

debug_bp = Blueprint('debug', __name__)


@debug_bp.route('/api/health')
def health_check():
    """Health check endpoint with system status."""
    return jsonify({
        "status": "healthy",
        "api_configured": bool(SUBCONSCIOUS_API_KEY),
        "sdk_available": SDK_AVAILABLE,
        "active_sessions": len(smart_memory.sessions),
        "customers_in_db": len(customer_db.customers),
    })


@debug_bp.route('/api/debug/customers')
def debug_customers():
    """View all stored customer data (for debugging)."""
    return jsonify({
        "persistent_database": customer_db.customers,
        "active_sessions": {
            sid: {
                "business_id": session.get("business_id"),
                "customer_details": session.get("customer_details", {}),
                "message_count": len(session.get("messages", []))
            }
            for sid, session in smart_memory.sessions.items()
        }
    })


@debug_bp.route('/api/debug/memory/<session_id>')
def debug_session_memory(session_id: str):
    """View memory for a specific session."""
    if session_id in smart_memory.sessions:
        session = smart_memory.sessions[session_id]
        return jsonify({
            "session_id": session_id,
            "business_id": session.get("business_id"),
            "customer_details": session.get("customer_details", {}),
            "messages": session.get("messages", [])[-10:],  # Last 10 messages
            "context_string": smart_memory.get_context_for_ai(session_id)
        })
    return jsonify({"error": "Session not found"}), 404
