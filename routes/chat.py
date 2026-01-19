"""
Chat routes for the Voice Agent application.

Handles:
- Main chat endpoint
- Streaming chat endpoint
- Reset and greeting endpoints
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context

from models import BUSINESSES
from services import conversation_manager, stream_subconscious_response

chat_bp = Blueprint('chat', __name__)


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint - receives text, returns agent response.
    
    Expected JSON:
    {
        "message": "user message text",
        "business_id": "hotel",
        "session_id": "unique-session-id"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    message = data.get("message", "").strip()
    business_id = data.get("business_id", "hotel")
    session_id = data.get("session_id", "default")
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    if business_id not in BUSINESSES:
        return jsonify({"error": f"Unknown business: {business_id}"}), 400
    
    # Process message through conversation manager
    # This handles: extraction, memory lookup, context building, API call
    response = conversation_manager.process_message(session_id, business_id, message)
    
    # Clean up any role prefixes that might have leaked through
    for prefix in ["You:", "Assistant:", "Agent:", f"{BUSINESSES[business_id].name}:"]:
        if response.startswith(prefix):
            response = response[len(prefix):].strip()
    
    return jsonify({
        "success": True,
        "response": response,
        "business": BUSINESSES[business_id].name
    })


@chat_bp.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """
    Streaming chat endpoint using Server-Sent Events.
    """
    data = request.get_json()
    
    message = data.get("message", "").strip()
    business_id = data.get("business_id", "hotel")
    session_id = data.get("session_id", "default")
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    # Create session and build context
    conversation_manager.create_session(session_id, business_id)
    
    # For streaming, we need to build the prompt manually
    from services.memory import smart_memory
    session = smart_memory.get_session(session_id, business_id)
    customer_context = smart_memory.get_context_for_ai(session_id)
    
    business = BUSINESSES[business_id]
    instructions = f"""You are {business.name}, a professional voice agent.

{business.system_prompt}

{f"CUSTOMER INFORMATION: {customer_context}" if customer_context else ""}

Customer says: {message}

Respond naturally and concisely:"""
    
    return Response(
        stream_with_context(stream_subconscious_response(instructions)),
        mimetype="text/event-stream"
    )


@chat_bp.route("/api/reset", methods=["POST"])
def reset():
    """Reset a conversation session."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")
    
    conversation_manager.reset_session(session_id)
    
    return jsonify({"success": True, "message": "Session reset"})


@chat_bp.route("/api/greeting", methods=["POST"])
def greeting():
    """Get the greeting message for a business."""
    data = request.get_json() or {}
    business_id = data.get("business_id", "hotel")
    session_id = data.get("session_id", "default")
    
    if business_id not in BUSINESSES:
        return jsonify({"error": f"Unknown business: {business_id}"}), 400
    
    greeting_text = conversation_manager.get_greeting(session_id, business_id)
    
    return jsonify({
        "success": True,
        "greeting": greeting_text,
        "business": BUSINESSES[business_id].name
    })
