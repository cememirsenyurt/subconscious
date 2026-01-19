"""
Conversation Service - Manages AI conversations with PARALLEL processing.

Two Subconscious AI calls run concurrently:
1. Response Generation - The main agent response
2. Information Extraction - Extracts customer details

This ensures we capture ALL info while keeping response time fast.
"""

from typing import Dict
from models.business import BUSINESSES
from .memory import smart_memory, process_message_parallel
from .subconscious_api import call_subconscious_api


class ConversationManager:
    """Manages conversations with parallel AI processing."""
    
    def __init__(self):
        pass
    
    def create_session(self, session_id: str, business_id: str):
        """Create a new conversation session."""
        smart_memory.get_session(session_id, business_id)
        print(f"[Conversation] Created session {session_id} for {business_id}")
    
    def process_message(self, session_id: str, business_id: str, user_message: str) -> str:
        """
        Process a user message with PARALLEL AI calls:
        - Response AI: Generates the agent's answer
        - Extraction AI: Extracts customer information
        
        Both run concurrently to save time!
        """
        business = BUSINESSES.get(business_id)
        if not business:
            return "Sorry, this business is not available."
        
        # Define the response generator function
        def generate_response(message: str, customer_context: str, history: str) -> str:
            prompt = self._build_prompt(business, message, customer_context, history)
            
            # Enable tools for questions that might need real info
            needs_search = self._might_need_search(message)
            
            result = call_subconscious_api(
                instructions=prompt,
                enable_tools=needs_search
            )
            
            return result.get("answer", "I'm sorry, could you repeat that?")
        
        # Process with parallel extraction
        response = process_message_parallel(
            session_id=session_id,
            business_id=business_id,
            message=user_message,
            response_generator=generate_response,
            smart_memory=smart_memory
        )
        
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
            "- If you don't have information, politely ask for it - don't make things up",
            "- If customer provides info, acknowledge it and use it",
            "- Keep responses concise (2-3 sentences) - this is a phone call",
            "- If you have customer details from records, use them naturally",
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
    
    def get_greeting(self, session_id: str, business_id: str) -> str:
        """Get the greeting for a business."""
        business = BUSINESSES.get(business_id)
        if not business:
            return "Hello! How can I help you today?"
        
        session = smart_memory.get_session(session_id, business_id)
        details = session.get("customer_details", {})
        
        if details.get("name"):
            return f"Welcome back, {details['name']}! This is {business.name}, how can I help you today?"
        
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
