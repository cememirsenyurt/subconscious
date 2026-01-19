"""
Conversation Service - Manages AI conversations with smart memory.

Uses Subconscious AI for both:
1. Generating responses (with tools for web search when needed)
2. Extracting customer details from messages
"""

from typing import Dict, Optional
from models.business import BUSINESSES
from .memory import smart_memory, extract_details_from_message
from .subconscious_api import call_subconscious_api, extract_details_with_ai


class ConversationManager:
    """Manages conversations with AI-powered memory."""
    
    def __init__(self):
        pass
    
    def create_session(self, session_id: str, business_id: str):
        """Create a new conversation session."""
        smart_memory.get_session(session_id, business_id)
        print(f"[Conversation] Created session {session_id} for {business_id}")
    
    def process_message(self, session_id: str, business_id: str, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        """
        session = smart_memory.get_session(session_id, business_id)
        
        business = BUSINESSES.get(business_id)
        if not business:
            return "Sorry, this business is not available."
        
        # Extract details from user message
        local_details = extract_details_from_message(user_message)
        if local_details:
            print(f"[Conversation] Local extraction: {local_details}")
            smart_memory.update_customer_details(session_id, local_details)
        
        # Look up existing customer if we found a name
        if "name" in local_details:
            smart_memory.lookup_customer(session_id, local_details["name"])
        
        smart_memory.add_message(session_id, "user", user_message)
        
        # Build context
        customer_context = smart_memory.get_context_for_ai(session_id)
        messages = session.get("messages", [])[-6:]
        history = "\n".join([
            f"{'Customer' if m['role'] == 'user' else 'Agent'}: {m['content']}"
            for m in messages[:-1]
        ])
        
        prompt = self._build_prompt(business, user_message, customer_context, history)
        
        # Enable tools for questions that might need real info
        needs_search = self._might_need_search(user_message)
        
        result = call_subconscious_api(
            instructions=prompt,
            enable_tools=needs_search
        )
        
        response = result.get("answer", "I'm sorry, could you repeat that?")
        smart_memory.add_message(session_id, "assistant", response)
        
        # Extract details from AI response too
        ai_details = extract_details_from_message(response)
        if ai_details:
            ai_details.pop("name", None)
            if ai_details:
                smart_memory.update_customer_details(session_id, ai_details)
        
        # Use AI extraction for complex messages
        if len(user_message.split()) > 5:
            self._async_ai_extraction(session_id, user_message, customer_context)
        
        return response
    
    def _build_prompt(self, business, user_message: str, customer_context: str, history: str) -> str:
        """Build the full prompt for the AI."""
        prompt_parts = [
            f"You are {business.name}, a professional voice agent.",
            "",
            "YOUR ROLE:",
            business.system_prompt,
            "",
            "IMPORTANT GUIDELINES:",
            "- Be conversational and natural, like a real phone call",
            "- If you don't have information the customer asks about, politely ask for it",
            "- NEVER make up information - if you don't know, ask or offer to look it up",
            "- If customer asks for something searchable (hours, locations, prices), use your search capability",
            "- Keep responses concise - this is a phone call, not an essay",
            "- If you have customer details, use them naturally",
            "",
        ]
        
        if customer_context:
            prompt_parts.extend([
                "CUSTOMER INFORMATION (from our records):",
                customer_context,
                "",
            ])
        else:
            prompt_parts.extend([
                "CUSTOMER INFORMATION: None on file yet.",
                "",
            ])
        
        if history:
            prompt_parts.extend([
                "CONVERSATION SO FAR:",
                history,
                "",
            ])
        
        prompt_parts.extend([
            "CUSTOMER SAYS:",
            user_message,
            "",
            "YOUR RESPONSE (be helpful, natural, and concise):",
        ])
        
        return "\n".join(prompt_parts)
    
    def _might_need_search(self, message: str) -> bool:
        """Determine if message might need web search."""
        search_indicators = [
            "hours", "open", "closed", "location", "address", "directions",
            "price", "cost", "how much", "available", "availability",
            "website", "phone number", "contact", "email",
            "reviews", "ratings", "nearby", "close to",
            "what is", "tell me about", "do you have",
            "latest", "current", "today", "now"
        ]
        msg_lower = message.lower()
        return any(indicator in msg_lower for indicator in search_indicators)
    
    def _async_ai_extraction(self, session_id: str, message: str, context: str):
        """Use AI to extract complex details from a message."""
        try:
            extracted = extract_details_with_ai(message, context)
            if extracted:
                print(f"[Conversation] AI extraction: {extracted}")
                smart_memory.update_customer_details(session_id, extracted)
        except Exception as e:
            print(f"[Conversation] AI extraction failed: {e}")
    
    def get_greeting(self, session_id: str, business_id: str) -> str:
        """Get the greeting for a business."""
        business = BUSINESSES.get(business_id)
        if not business:
            return "Hello! How can I help you today?"
        
        session = smart_memory.get_session(session_id, business_id)
        details = session.get("customer_details", {})
        
        if details.get("name"):
            return f"Welcome back! This is {business.name}, how can I help you today?"
        
        return business.greeting
    
    def reset_session(self, session_id: str):
        """Reset a conversation session."""
        smart_memory.clear_session(session_id)
        print(f"[Conversation] Reset session {session_id}")
    
    def get_customer_info(self, session_id: str) -> Dict:
        """Get all stored customer info for a session."""
        return smart_memory.get_customer_details(session_id)


# Global instance
conversation_manager = ConversationManager()
