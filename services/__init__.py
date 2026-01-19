"""
Services Package

Contains business logic and external integrations:
- conversation: Manages AI conversations with smart memory
- customer_db: Persistent customer database
- memory: Smart AI-powered memory system
- subconscious_api: Subconscious AI integration with tools
"""

from .conversation import conversation_manager
from .customer_db import customer_db
from .memory import smart_memory
from .subconscious_api import call_subconscious_api, search_for_info, stream_subconscious_response

__all__ = [
    'conversation_manager',
    'customer_db', 
    'smart_memory',
    'call_subconscious_api',
    'search_for_info',
    'stream_subconscious_response',
]
