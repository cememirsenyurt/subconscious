"""
Smart Memory Service - AI-Powered Information Extraction

Uses a SECOND Subconscious AI call to intelligently extract customer information.
No hardcoding - the AI understands context and extracts what matters.
"""

import json
import re
import threading
from typing import Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .customer_db import customer_db


class SmartMemory:
    """
    AI-powered memory that extracts and stores ANY relevant customer information.
    Uses Subconscious AI for intelligent extraction - no hardcoded patterns.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def get_session(self, session_id: str, business_id: str) -> Dict:
        """Get or create a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "business_id": business_id,
                "customer_details": {},
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
            self.sessions[session_id]["messages"] = self.sessions[session_id]["messages"][-20:]
    
    def update_customer_details(self, session_id: str, details: Dict):
        """Update customer details with new information."""
        if session_id not in self.sessions:
            return
        
        current = self.sessions[session_id]["customer_details"]
        
        for key, value in details.items():
            if value and str(value).strip() and str(value).lower() not in ['none', 'null', 'n/a', 'unknown']:
                normalized_key = key.lower().replace(" ", "_").replace("-", "_")
                current[normalized_key] = value
                print(f"[SmartMemory] Stored: {normalized_key} = {value}")
        
        self._save_to_db(session_id)
    
    def get_customer_details(self, session_id: str) -> Dict:
        """Get all stored customer details."""
        if session_id in self.sessions:
            return self.sessions[session_id]["customer_details"].copy()
        return {}
    
    def lookup_customer(self, session_id: str, name: str):
        """Look up customer in database and restore their info."""
        if session_id not in self.sessions or not name:
            return False
        
        business_id = self.sessions[session_id]["business_id"]
        stored = customer_db.find_customer(name, business_id)
        
        if stored:
            print(f"[SmartMemory] Found returning customer: {name}")
            current = self.sessions[session_id]["customer_details"]
            for key, value in stored.items():
                if value and key not in current:
                    current[key] = value
                    print(f"[SmartMemory] Restored: {key} = {value}")
            current["is_returning_customer"] = True
            return True
        return False
    
    def _save_to_db(self, session_id: str):
        """Save customer details to persistent database."""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        details = session["customer_details"]
        business_id = session["business_id"]
        
        name = details.get("name") or details.get("customer_name") or details.get("full_name")
        if not name:
            return
        
        save_data = {k: v for k, v in details.items() 
                    if not k.startswith("_") and k != "is_returning_customer"}
        
        if len(save_data) > 1:
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
        
        for key, value in details.items():
            if key.startswith("_") or key == "is_returning_customer":
                continue
            display_key = key.replace("_", " ").title()
            parts.append(f"• {display_key}: {value}")
        
        if parts:
            parts.append("\n[Use this information in your response. If asked about these details, provide them.]")
        
        return "\n".join(parts)
    
    def clear_session(self, session_id: str):
        """Clear a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]


# =============================================================================
# AI-POWERED EXTRACTION (using Subconscious as second layer)
# =============================================================================

def extract_with_ai(message: str, context: str = "") -> Dict:
    """
    Use Subconscious AI to intelligently extract customer information.
    This runs as a SECOND parallel call - no hardcoding!
    """
    from .subconscious_api import call_subconscious_api
    
    prompt = f"""You are an information extraction assistant. Extract ALL customer details from this message.

IMPORTANT RULES:
1. Extract the customer's FULL NAME correctly. "My name is Cem and last name is Senyurt" means name is "Cem Senyurt"
2. Extract dates, times, budgets, preferences, locations - ANYTHING relevant
3. If info was previously known and customer confirms it, include it
4. Return ONLY a valid JSON object with extracted fields
5. Use clear field names: name, phone, email, date, time, budget, location, etc.
6. If nothing to extract, return empty {{}}

CONVERSATION CONTEXT:
{context if context else "No previous context"}

CURRENT MESSAGE TO EXTRACT FROM:
"{message}"

Return ONLY valid JSON (no markdown, no explanation):"""
    
    try:
        result = call_subconscious_api(
            instructions=prompt,
            enable_tools=False  # Pure extraction, no tools needed
        )
        
        if result["success"]:
            answer = result["answer"].strip()
            
            # Clean up markdown if present
            if "```json" in answer:
                answer = answer.split("```json")[1].split("```")[0]
            elif "```" in answer:
                answer = answer.split("```")[1].split("```")[0]
            
            # Parse JSON
            extracted = json.loads(answer.strip())
            if isinstance(extracted, dict):
                print(f"[AI Extraction] Extracted: {extracted}")
                return extracted
    except json.JSONDecodeError as e:
        print(f"[AI Extraction] JSON parse error: {e}")
    except Exception as e:
        print(f"[AI Extraction] Error: {e}")
    
    return {}


def process_message_parallel(
    session_id: str,
    business_id: str, 
    message: str,
    response_generator,  # Function that generates the response
    smart_memory: SmartMemory
) -> str:
    """
    Process message with smart sequencing:
    1. FIRST: Quick extraction to get customer name
    2. THEN: Lookup returning customer if name found
    3. FINALLY: Generate response with full context
    
    This ensures the agent knows who they're talking to!
    """
    session = smart_memory.get_session(session_id, business_id)
    
    # Get conversation history
    messages = session.get("messages", [])[-6:]
    history = "\n".join([
        f"{'Customer' if m['role'] == 'user' else 'Agent'}: {m['content']}"
        for m in messages
    ])
    
    # STEP 1: Run extraction FIRST to identify customer
    print("[Parallel] Step 1: Running extraction...")
    try:
        current_context = smart_memory.get_context_for_ai(session_id)
        full_context = f"{current_context}\n\nRecent conversation:\n{history}" if history else current_context
        
        extracted = extract_with_ai(message, full_context)
        if extracted:
            # Check if we got a name - try to look up returning customer
            name = extracted.get("name") or extracted.get("full_name") or extracted.get("customer_name")
            if name:
                print(f"[Parallel] Found name: {name}")
                # Lookup BEFORE updating (so we get existing data)
                if not session["customer_details"].get("is_returning_customer"):
                    smart_memory.lookup_customer(session_id, name)
            
            # Update with extracted info
            smart_memory.update_customer_details(session_id, extracted)
    except Exception as e:
        print(f"[Parallel] Extraction error: {e}")
    
    # STEP 2: Build context WITH the extracted/looked-up info
    print("[Parallel] Step 2: Building context with customer info...")
    updated_context = smart_memory.get_context_for_ai(session_id)
    
    # STEP 3: Generate response with full context
    print("[Parallel] Step 3: Generating response...")
    try:
        response = response_generator(message, updated_context, history)
    except Exception as e:
        print(f"[Parallel] Response error: {e}")
        response = "I'm sorry, I'm having trouble processing that. Could you try again?"
    
    # Add messages to history
    smart_memory.add_message(session_id, "user", message)
    smart_memory.add_message(session_id, "assistant", response)
    
    return response


# Global instance
smart_memory = SmartMemory()
