"""
Smart Memory Service - AI-Powered Information Extraction

Instead of hardcoding patterns, we let Subconscious AI extract important details.
This captures ANY information the customer provides, not just predefined fields.
"""

import json
import re
from typing import Dict, Optional, Any
from .customer_db import customer_db


class SmartMemory:
    """
    AI-powered memory that extracts and stores ANY relevant customer information.
    No hardcoded fields - just stores what the AI identifies as important.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_session(self, session_id: str, business_id: str) -> Dict:
        """Get or create a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "business_id": business_id,
                "customer_details": {},  # Flexible dictionary - stores ANYTHING
                "conversation_summary": "",
                "messages": []
            }
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to session history."""
        if session_id in self.sessions:
            self.sessions[session_id]["messages"].append({
                "role": role,
                "content": content
            })
            # Keep last 20 messages for context
            self.sessions[session_id]["messages"] = self.sessions[session_id]["messages"][-20:]
    
    def update_customer_details(self, session_id: str, details: Dict):
        """
        Update customer details with new information.
        Merges new details with existing ones.
        """
        if session_id not in self.sessions:
            return
        
        current = self.sessions[session_id]["customer_details"]
        
        # Merge new details (new values override old ones if not empty)
        for key, value in details.items():
            if value and str(value).strip():
                # Normalize key to lowercase with underscores
                normalized_key = key.lower().replace(" ", "_").replace("-", "_")
                current[normalized_key] = value
                print(f"[SmartMemory] Stored: {normalized_key} = {value}")
        
        # Save to persistent database if we have a name
        self._save_to_db(session_id)
    
    def get_customer_details(self, session_id: str) -> Dict:
        """Get all stored customer details."""
        if session_id in self.sessions:
            return self.sessions[session_id]["customer_details"].copy()
        return {}
    
    def lookup_customer(self, session_id: str, name: str):
        """Look up customer in database and restore their info."""
        if session_id not in self.sessions:
            return
        
        business_id = self.sessions[session_id]["business_id"]
        stored = customer_db.find_customer(name, business_id)
        
        if stored:
            print(f"[SmartMemory] Found returning customer: {name}")
            # Merge stored data into current session
            current = self.sessions[session_id]["customer_details"]
            for key, value in stored.items():
                if value and key not in current:
                    current[key] = value
                    print(f"[SmartMemory] Restored: {key} = {value}")
            current["is_returning_customer"] = True
    
    def _save_to_db(self, session_id: str):
        """Save customer details to persistent database."""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        details = session["customer_details"]
        business_id = session["business_id"]
        
        # Need a name to save
        name = details.get("name") or details.get("customer_name")
        if not name:
            return
        
        # Save all details (excluding internal flags)
        save_data = {k: v for k, v in details.items() 
                    if not k.startswith("_") and k != "is_returning_customer"}
        
        if len(save_data) > 1:  # More than just the name
            customer_db.save_customer(name, business_id, save_data)
    
    def get_context_for_ai(self, session_id: str) -> str:
        """Build context string with all known customer details."""
        if session_id not in self.sessions:
            return ""
        
        session = self.sessions[session_id]
        details = session["customer_details"]
        
        if not details:
            return ""
        
        parts = []
        
        if details.get("is_returning_customer"):
            parts.append("[RETURNING CUSTOMER - Found in our records!]")
        else:
            parts.append("[CUSTOMER INFORMATION]")
        
        # List all stored details
        for key, value in details.items():
            if key.startswith("_") or key == "is_returning_customer":
                continue
            # Make key human readable
            display_key = key.replace("_", " ").title()
            parts.append(f"• {display_key}: {value}")
        
        if parts:
            parts.append("\n[Use this information in your response. If asked about these details, provide them.]")
        
        return "\n".join(parts)
    
    def clear_session(self, session_id: str):
        """Clear a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Build the extraction prompt for Subconscious
EXTRACTION_PROMPT = """Analyze this customer message and extract ALL important details.

Return a JSON object with any relevant information found. Use descriptive keys.
Examples of what to extract:
- name, phone, email
- dates, times, duration
- budget, price range, cost preferences  
- location, address, area, neighborhood, city
- quantities (party size, number of people, rooms, etc.)
- preferences (seating, style, type, features)
- product/service details (membership type, room type, property specs, etc.)
- any specific requirements or requests

ONLY include fields that were explicitly mentioned. Do not invent or assume.
Return empty {} if no extractable information found.

Customer message: "{message}"

Return ONLY valid JSON, nothing else:"""


def extract_details_from_message(message: str) -> Dict:
    """
    Basic extraction for common patterns.
    This is a fallback - the main extraction happens via Subconscious AI.
    """
    details = {}
    msg_lower = message.lower()
    
    # Extract name (multiple patterns, more flexible)
    name_patterns = [
        r"(?:my name is|i'm|im|i am|this is|it's|its|call me|hey,?\s*(?:this is)?)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
        r"^(?:hi|hello|hey),?\s*(?:this is|i'm|im|i am)?\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)",
    ]
    stop_words = ['the', 'a', 'an', 'here', 'there', 'calling', 'looking', 'interested', 
                  'wondering', 'trying', 'need', 'want', 'have', 'would', 'could', 'can',
                  'hi', 'hello', 'hey', 'thanks', 'thank', 'please', 'just', 'actually']
    for pattern in name_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Filter out common false positives and title case the name
            if name.lower() not in stop_words and len(name) > 1:
                details["name"] = name.title()
                print(f"[Memory] Extracted name: {details['name']}")
                break
    
    # Extract phone
    phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', message)
    if phone_match:
        details["phone"] = phone_match.group(1)
    
    # Extract email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
    if email_match:
        details["email"] = email_match.group(0)
    
    # Extract money/budget amounts
    money_patterns = [
        (r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|m)', lambda m: f"${float(m.replace(',',''))*1000000:,.0f}"),
        (r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:k|thousand)', lambda m: f"${float(m.replace(',',''))*1000:,.0f}"),
        (r'\$\s*([\d,]+(?:\.\d{2})?)', lambda m: f"${m}"),
        (r'(\d+(?:\.\d+)?)\s*(?:million|m)\s*(?:dollars?)?', lambda m: f"${float(m)*1000000:,.0f}"),
        (r'(\d+)\s*(?:k|thousand)\s*(?:dollars?)?', lambda m: f"${float(m)*1000:,.0f}"),
    ]
    for pattern, formatter in money_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            try:
                details["budget"] = formatter(match.group(1))
                break
            except:
                pass
    
    # Extract dates
    date_match = re.search(
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?',
        msg_lower
    )
    if date_match:
        month = date_match.group(1).title()
        day = date_match.group(2)
        year = date_match.group(3) or "2026"
        details["date"] = f"{month} {day}, {year}"
    
    # Extract time
    time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))', message)
    if time_match:
        details["time"] = time_match.group(1)
    
    # Extract numbers with context (party size, bedrooms, etc.)
    number_contexts = [
        (r'(\d+)\s*(?:people|persons|guests|of us)', 'party_size'),
        (r'party of\s*(\d+)', 'party_size'),
        (r'(\d+)\s*(?:bed(?:room)?s?)', 'bedrooms'),
        (r'(\d+)\s*(?:bath(?:room)?s?)', 'bathrooms'),
        (r'for\s*(\d+)\s*(?:night|day)s?', 'duration'),
    ]
    for pattern, key in number_contexts:
        match = re.search(pattern, msg_lower)
        if match:
            details[key] = match.group(1)
    
    return details


# Global instance
smart_memory = SmartMemory()
