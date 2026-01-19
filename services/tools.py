"""
Subconscious Tools Integration

Provides:
1. Platform tools (web_search, parallel_search, etc.)
2. Custom function tools (our own endpoints)
3. Tool configurations for different use cases
"""

from typing import List, Dict, Any

# =============================================================================
# PLATFORM TOOLS - Built into Subconscious
# =============================================================================

PLATFORM_TOOLS = {
    "web_search": {
        "type": "platform",
        "id": "web_search",
        "description": "Search the web for current information"
    },
    "parallel_search": {
        "type": "platform",
        "id": "parallel_search",
        "description": "Precision search for facts from authoritative sources"
    },
    "webpage_understanding": {
        "type": "platform",
        "id": "webpage_understanding",
        "description": "Extract and summarize webpage content"
    },
    "exa_search": {
        "type": "platform",
        "id": "exa_search",
        "description": "Semantic search for high-quality content"
    },
}


# =============================================================================
# CUSTOM FUNCTION TOOLS - Our endpoints that Subconscious can call
# =============================================================================

def get_custom_tools(base_url: str) -> List[Dict[str, Any]]:
    """
    Get custom function tools that point to our API endpoints.
    
    These let Subconscious call back to our server to:
    - Look up customer information
    - Check availability
    - Make bookings
    """
    return [
        {
            "type": "function",
            "name": "lookup_customer",
            "description": "Look up a customer's information by name. Use this when a customer identifies themselves to find their booking history, preferences, and past interactions.",
            "url": f"{base_url}/api/tools/lookup_customer",
            "method": "POST",
            "timeout": 10,
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "The customer's name to look up"
                    },
                    "business_id": {
                        "type": "string",
                        "description": "The business identifier (hotel, restaurant, gym, etc.)"
                    }
                },
                "required": ["customer_name", "business_id"]
            }
        },
        {
            "type": "function",
            "name": "save_booking",
            "description": "Save or update a customer's booking/appointment. Use this when a customer confirms they want to make a reservation.",
            "url": f"{base_url}/api/tools/save_booking",
            "method": "POST",
            "timeout": 10,
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's full name"
                    },
                    "business_id": {
                        "type": "string",
                        "description": "Business identifier"
                    },
                    "booking_details": {
                        "type": "object",
                        "description": "Booking details (date, time, party_size, room_type, etc.)"
                    }
                },
                "required": ["customer_name", "business_id", "booking_details"]
            }
        },
        {
            "type": "function",
            "name": "check_availability",
            "description": "Check availability for a specific date/time. Use this when customer asks about availability.",
            "url": f"{base_url}/api/tools/check_availability",
            "method": "POST",
            "timeout": 10,
            "parameters": {
                "type": "object",
                "properties": {
                    "business_id": {
                        "type": "string",
                        "description": "Business identifier"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date to check"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time to check (optional)"
                    },
                    "service_type": {
                        "type": "string",
                        "description": "Type of service/room/table requested"
                    }
                },
                "required": ["business_id", "date"]
            }
        }
    ]


# =============================================================================
# TOOL SETS - Preconfigured combinations for different scenarios
# =============================================================================

def get_research_tools() -> List[Dict]:
    """Tools for answering questions that need real-world data."""
    return [
        {"type": "platform", "id": "web_search"},
        {"type": "platform", "id": "parallel_search"},
    ]


def get_full_tools(base_url: str = None) -> List[Dict]:
    """Full tool set including web search and custom functions."""
    tools = [
        {"type": "platform", "id": "web_search"},
        {"type": "platform", "id": "parallel_search"},
    ]
    
    if base_url:
        tools.extend(get_custom_tools(base_url))
    
    return tools


def should_use_tools(message: str) -> tuple[bool, List[str]]:
    """
    Determine if a message needs tools and which ones.
    
    Returns: (should_use, list_of_tool_ids)
    """
    msg_lower = message.lower()
    
    # Research indicators - need web search
    research_keywords = [
        "what is", "tell me about", "how do i get to", "directions",
        "where is", "nearby", "close to", "around here",
        "weather", "traffic", "news", "latest",
        "reviews", "ratings", "best", "recommended",
        "hours", "open", "closed", "website", "phone number",
        "price of", "cost of", "how much is"
    ]
    
    needs_research = any(kw in msg_lower for kw in research_keywords)
    
    # Booking indicators - need custom tools
    booking_keywords = [
        "book", "reserve", "appointment", "schedule",
        "available", "availability", "can i get",
        "sign up", "register", "membership"
    ]
    
    needs_booking = any(kw in msg_lower for kw in booking_keywords)
    
    tools = []
    if needs_research:
        tools.extend(["web_search", "parallel_search"])
    
    return (needs_research or needs_booking, tools)
