"""
Debug routes for development and testing.

These routes should be disabled or protected in production.
"""

from flask import Blueprint, jsonify

from services import customer_db, conversation_manager, call_subconscious_api

debug_bp = Blueprint('debug', __name__)


@debug_bp.route("/api/debug/customers")
def debug_customers():
    """Debug endpoint to see stored customers."""
    return jsonify({
        "customers": customer_db.get_all_customers(),
        "sessions": {k: v["customer_info"] for k, v in conversation_manager.conversations.items()}
    })


@debug_bp.route("/api/debug/test", methods=["POST"])
def debug_test():
    """Test the Subconscious API connection."""
    result = call_subconscious_api("Say 'API connection successful!' and nothing else.")
    return jsonify(result)
