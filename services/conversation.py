"""
Conversation Service - Smart Discovery Agents

All agents use Subconscious web search to find REAL businesses,
then help users make mock bookings/reservations.
"""

from typing import Dict
from models.business import BUSINESSES
from .memory import smart_memory, process_message_parallel
from .subconscious_api import call_subconscious_api


class ConversationManager:
    """Manages conversations with web-search-powered discovery agents."""
    
    def __init__(self):
        pass
    
    def create_session(self, session_id: str, business_id: str):
        """Create a new conversation session."""
        smart_memory.get_session(session_id, business_id)
        print(f"[Conversation] Created session {session_id} for {business_id}")
    
    def process_message(self, session_id: str, business_id: str, user_message: str, use_search: bool = True) -> str:
        """
        Process a user message with smart discovery.
        
        Web search is ALWAYS enabled by default for finding real businesses.
        """
        business = BUSINESSES.get(business_id)
        if not business:
            return "Sorry, this service is not available."
        
        # Define the response generator - ALWAYS uses web search
        def generate_response(message: str, customer_context: str, history: str) -> str:
            prompt = self._build_prompt(business, message, customer_context, history)
            
            # ALWAYS enable web search tools for real business discovery
            tools = [
                {"type": "platform", "id": "web_search"},
                {"type": "platform", "id": "parallel_search"},
            ]
            
            result = call_subconscious_api(
                instructions=prompt,
                tools=tools
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
        """Build the prompt with discovery-focused instructions."""
        prompt_parts = [
            f"You are {business.name}, a smart discovery assistant.",
            "",
            "YOUR ROLE:",
            business.system_prompt,
            "",
            "KEY BEHAVIORS:",
            "- USE WEB SEARCH to find REAL businesses when asked about {category}".format(category=business.category),
            "- Present real options with names, ratings, prices when available",
            "- Help the user choose and 'book' with their selection",
            "- Remember everything they tell you",
            "- Be conversational - this is a phone call",
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
                "CUSTOMER INFORMATION: New customer - get their name and location first.",
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
            "YOUR RESPONSE (search if needed, be helpful and natural):",
        ])
        
        return "\n".join(prompt_parts)
    
    def get_greeting(self, session_id: str, business_id: str) -> str:
        """Get the greeting for an agent."""
        business = BUSINESSES.get(business_id)
        if not business:
            return "Hello! How can I help you today?"
        
        session = smart_memory.get_session(session_id, business_id)
        details = session.get("customer_details", {})
        
        if details.get("name"):
            return f"Welcome back, {details['name']}! I'm {business.name}. How can I help you today?"
        
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
