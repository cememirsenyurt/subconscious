"""
Main routes for the Voice Agent application.

Handles:
- Main page rendering
- Business listing
- Greetings
- Health checks
"""

from datetime import datetime
from flask import Blueprint, render_template, jsonify, request

from config import SUBCONSCIOUS_API_KEY
from models import BUSINESSES
from services import conversation_manager

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def index():
    """Serve the main application page."""
    return render_template("index.html", businesses=BUSINESSES)


@main_bp.route("/api/businesses")
def get_businesses():
    """Get list of available discovery agents."""
    return jsonify({
        business_id: {
            "id": biz.id,
            "name": biz.name,
            "icon": biz.icon,
            "color": biz.color,
            "category": biz.category,
            "greeting": biz.greeting,
            "sample_queries": biz.sample_queries
        }
        for business_id, biz in BUSINESSES.items()
    })


@main_bp.route("/api/greeting", methods=["POST"])
def get_greeting():
    """Get the greeting for a specific business."""
    data = request.get_json() or {}
    business_id = data.get("business_id", "hotel")
    business = BUSINESSES.get(business_id, BUSINESSES["hotel"])
    return jsonify({
        "greeting": business.greeting,
        "name": business.name,
        "icon": business.icon
    })


@main_bp.route("/api/reset", methods=["POST"])
def reset_conversation():
    """Reset conversation history for a session."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")
    conversation_manager.reset_session(session_id)
    return jsonify({"success": True, "message": "Conversation reset"})


@main_bp.route("/api/health")
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "api_configured": bool(SUBCONSCIOUS_API_KEY),
        "timestamp": datetime.now().isoformat()
    })
