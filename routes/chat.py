"""
Chat routes for the Voice Agent application.

Handles:
- Main chat endpoint
- Streaming chat endpoint
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context

from models import BUSINESSES
from services import conversation_manager, call_subconscious_api, stream_subconscious_response

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
    
    # Get or create conversation with system prompt
    conversation_manager.get_or_create(session_id, business_id)
    
    # FIRST: Extract info from the message and lookup in database
    # This populates customer_info with any remembered data
    conversation_manager._extract_customer_info(session_id, message)
    conversation_manager._lookup_customer_in_db(session_id)
    
    # NOW build context (which will include the looked-up memory)
    instructions = conversation_manager.build_full_context(session_id, message)
    
    # Add user message to history for future context (extraction already done)
    if session_id in conversation_manager.conversations:
        conversation_manager.conversations[session_id]["messages"].append({
            "role": "user",
            "content": message
        })
        # Save to database
        conversation_manager._save_customer_to_db(session_id)
    
    # Call Subconscious API
    result = call_subconscious_api(instructions)
    
    if result["success"]:
        answer = result["answer"]
        # Clean up any role prefixes that might have leaked through
        for prefix in ["You:", "Assistant:", "Agent:", f"{BUSINESSES[business_id].name}:"]:
            if answer.startswith(prefix):
                answer = answer[len(prefix):].strip()
        
        # Add assistant response to history
        conversation_manager.add_message(session_id, "assistant", answer)
        
        return jsonify({
            "success": True,
            "response": answer,
            "business": BUSINESSES[business_id].name
        })
    else:
        return jsonify({
            "success": False,
            "response": result["answer"],
            "error": result.get("error", "Unknown error")
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
    
    conversation_manager.get_or_create(session_id, business_id)
    conversation_manager.add_message(session_id, "user", message)
    
    instructions = conversation_manager.build_full_context(session_id, message)
    
    return Response(
        stream_with_context(stream_subconscious_response(instructions)),
        mimetype="text/event-stream"
    )
