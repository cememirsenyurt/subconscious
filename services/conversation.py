"""
Conversation Service - Smart Discovery Agents

Uses web search ONLY when needed for finding real businesses.
Simple conversational messages don't need web search.
"""

from typing import Dict
from models.business import BUSINESSES
from .memory import smart_memory, process_message_parallel
from .subconscious_api import call_subconscious_api


class ConversationManager:
    """Manages conversations with smart search detection."""
    
    def __init__(self):
        pass
    
    def create_session(self, session_id: str, business_id: str):
        """Create a new conversation session."""
        smart_memory.get_session(session_id, business_id)
        print(f"[Conversation] Created session {session_id} for {business_id}")
    
    def process_message(self, session_id: str, business_id: str, user_message: str, use_search: bool = True) -> str:
        """
        Process a user message with smart search detection.
        
        Web search is used ONLY when the message asks about:
        - Finding businesses, restaurants, gyms, hotels, etc.
        - Locations, prices, reviews, availability
        
        NOT for simple conversation like "my name is..." or "yes please"
        """
        business = BUSINESSES.get(business_id)
        if not business:
            return "Sorry, this service is not available."
        
        # Check if this message actually NEEDS web search
        needs_search = self._needs_web_search(user_message)
        print(f"[Conversation] Message needs search: {needs_search}")
        
        # Define the response generator
        def generate_response(message: str, customer_context: str, history: str) -> str:
            prompt = self._build_prompt(business, message, customer_context, history, needs_search)
            
            # Only use tools if we actually need to search
            tools = None
            if needs_search:
                tools = [
                    {"type": "platform", "id": "web_search"},
                    {"type": "platform", "id": "parallel_search"},
                ]
                print("[Conversation] 🔍 Using web search tools...")
            else:
                print("[Conversation] 💬 Simple response, no search needed")
            
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
    
    def _needs_web_search(self, message: str) -> bool:
        """
        Determine if a message needs web search.
        
        Returns True for queries about finding businesses, locations, etc.
        Returns False for simple conversational responses.
        """
        msg_lower = message.lower()
        
        # Keywords that indicate we need to SEARCH
        search_triggers = [
            # Finding businesses
            "find", "search", "look for", "looking for", "show me",
            "what are", "where can i", "recommend", "suggestions",
            "best", "top rated", "popular", "nearby", "near me", "around",
            
            # Specific business types
            "restaurant", "gym", "fitness", "hotel", "property", "house",
            "clinic", "doctor", "salon", "spa", "barber",
            
            # Comparison/research
            "prices", "membership", "cost", "how much", "reviews",
            "ratings", "compare", "options", "available",
            
            # Location queries
            "in san", "in los", "in new", "in the", "downtown", "area",
        ]
        
        # Keywords that indicate simple conversation (NO search needed)
        simple_triggers = [
            "my name is", "i am", "i'm", "yes", "no", "okay", "ok",
            "sure", "please", "thank", "hi", "hello", "hey",
            "that sounds", "i want", "i'd like", "i would like",
            "book", "reserve", "sign up", "schedule", "confirm",
            "call me", "my phone", "my email", "contact",
        ]
        
        # If it's clearly a simple response, don't search
        for trigger in simple_triggers:
            if msg_lower.startswith(trigger) or trigger in msg_lower[:30]:
                # But check if they're ALSO asking to find something
                has_search = any(s in msg_lower for s in ["find", "search", "show", "what", "where"])
                if not has_search:
                    return False
        
        # Check if any search triggers are present
        for trigger in search_triggers:
            if trigger in msg_lower:
                return True
        
        # Default: don't search for short messages
        if len(message.split()) < 5:
            return False
        
        return False
    
    def _build_prompt(self, business, user_message: str, customer_context: str, history: str, searching: bool) -> str:
        """Build the prompt with appropriate instructions."""
        prompt_parts = [
            f"You are {business.name}, a helpful discovery assistant.",
            "",
            "YOUR ROLE:",
            business.system_prompt,
            "",
        ]
        
        if searching:
            prompt_parts.extend([
                "INSTRUCTION: The user wants to find real businesses. USE YOUR WEB SEARCH to find actual options.",
                "Present 3-5 real results with names, brief descriptions, and ratings if available.",
                "",
            ])
        else:
            prompt_parts.extend([
                "INSTRUCTION: This is a conversational response. Be helpful and natural.",
                "Ask clarifying questions if needed. Keep it brief - this is a phone call.",
                "",
            ])
        
        if customer_context:
            prompt_parts.extend([
                "CUSTOMER INFO:",
                customer_context,
                "",
            ])
        
        if history:
            prompt_parts.extend([
                "CONVERSATION:",
                history,
                "",
            ])
        
        prompt_parts.extend([
            "CUSTOMER:",
            user_message,
            "",
            "YOUR RESPONSE:",
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
