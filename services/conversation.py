"""
Conversation Management Service.

Manages conversation history, memory extraction, and context building
for multi-turn voice agent interactions.
"""

import re
from typing import Dict

from models import BUSINESSES
from .customer_db import customer_db


class ConversationManager:
    """
    Manages conversation history for multi-turn interactions.
    
    Features:
    - Maintains full conversation context
    - Extracts and remembers key customer facts (name, phone, reservation details)
    - Integrates with CustomerDatabase for cross-session memory
    - Builds comprehensive prompts for the AI
    """
    
    def __init__(self):
        self.conversations: Dict[str, Dict] = {}
    
    def get_or_create(self, session_id: str, business_id: str) -> Dict:
        """
        Get existing conversation or create new one with system prompt.
        
        Args:
            session_id: Unique identifier for the conversation session
            business_id: The business type (hotel, restaurant, etc.)
            
        Returns:
            The conversation dictionary
        """
        if session_id not in self.conversations:
            business = BUSINESSES.get(business_id, BUSINESSES["hotel"])
            self.conversations[session_id] = {
                "business_id": business_id,
                "business_name": business.name,
                "system_prompt": business.system_prompt,
                "messages": [],  # List of (role, content) tuples
                "customer_info": {},  # Extracted customer details
            }
        return self.conversations[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to the conversation history.
        
        Args:
            session_id: The conversation session ID
            role: Message role ("user" or "assistant")
            content: The message content
        """
        if session_id in self.conversations:
            self.conversations[session_id]["messages"].append({
                "role": role,
                "content": content
            })
            
            # Extract and remember customer information from user messages
            if role == "user":
                self._extract_customer_info(session_id, content)
                
                # Check if customer gave their name - look up in global database
                self._lookup_customer_in_db(session_id)
                
                # Save customer to database if we have meaningful info
                self._save_customer_to_db(session_id)
            
            # Also extract confirmed details from agent responses
            if role == "assistant":
                self._extract_from_confirmation(session_id, content)
                
                # Save customer to global database for future sessions
                self._save_customer_to_db(session_id)
    
    def _extract_customer_info(self, session_id: str, message: str):
        """
        Extract key customer information from messages for memory.
        
        Extracts: names, phone numbers, emails, party sizes, dates, times, seating preferences
        """
        conv = self.conversations[session_id]
        info = conv["customer_info"]
        msg_lower = message.lower()
        
        # Extract name patterns - also check for standalone names (just a name as response)
        name_patterns = [
            "my name is ", "i'm ", "i am ", "this is ", "call me ",
            "name's ", "it's ", "the name is ", "name is "
        ]
        
        # Words that should NOT be part of a name
        stop_words = {'what', 'whats', "what's", 'when', 'where', 'how', 'why', 'which', 'who', 
                      'can', 'could', 'would', 'will', 'do', 'does', 'did', 'is', 'are', 'was', 
                      'were', 'the', 'and', 'or', 'but', 'for', 'to', 'at', 'on', 'in', 'i', 
                      'my', 'me', 'want', 'need', 'have', 'had', 'reservation', 'appointment', 
                      'booking', 'book', 'table', 'dinner', 'lunch', 'breakfast', 'please', 
                      'thanks', 'make', 'call', 'calling', 'check', 'looking', 'like', 'just',
                      'give', 'tell', 'show', 'info', 'information', 'details', 'about'}
        
        # Check if message looks like just a name (1-3 capitalized words)
        words = message.strip().split()
        if len(words) <= 3 and all(w[0].isupper() for w in words if w):
            # Likely just a name response - but filter stop words
            potential_name = []
            for w in words:
                clean = w.strip('.,!?')
                if clean.lower() not in stop_words:
                    potential_name.append(clean)
            if potential_name and len(" ".join(potential_name)) > 1:
                info["name"] = " ".join(potential_name)
                print(f"[Memory] Remembered customer name: {info['name']}")
        else:
            # Try pattern matching
            for pattern in name_patterns:
                if pattern in msg_lower:
                    idx = msg_lower.find(pattern) + len(pattern)
                    remaining = message[idx:].strip()
                    words = remaining.split()
                    if words:
                        potential_name = []
                        for word in words[:3]:
                            clean_word = word.strip('.,!?')
                            # Stop at punctuation or stop words
                            if not clean_word or clean_word.lower() in stop_words:
                                break
                            if clean_word[0].isupper():
                                potential_name.append(clean_word)
                            else:
                                break
                        if potential_name:
                            info["name"] = " ".join(potential_name)
                            print(f"[Memory] Remembered customer name: {info['name']}")
                            break

        # Extract phone number patterns
        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})', message)
        if phone_match:
            info["phone"] = phone_match.group(1)
            print(f"[Memory] Remembered phone: {info['phone']}")

        # Extract email patterns
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
        if email_match:
            info["email"] = email_match.group(0)
            print(f"[Memory] Remembered email: {info['email']}")
        
        # Extract party size
        party_patterns = [
            r'(\d+)\s*(?:people|persons|guests|of us)',
            r'party of (\d+)',
            r'table for (\d+)',
            r'room for (\d+)',
            r'for (\d+)\b',
            r'(\d+)\s*(?:adults?|kids?|children)',
        ]
        for pattern in party_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                info["party_size"] = match.group(1)
                print(f"[Memory] Remembered party size: {info['party_size']}")
                break
        
        # Only extract dates if there's booking/reservation context
        booking_context_words = ['book', 'reserv', 'appointment', 'schedule', 'table for', 
                                  'room for', 'want to', 'like to', 'need to', 'can i', 
                                  'available', 'opening', 'slot']
        has_booking_context = any(word in msg_lower for word in booking_context_words)
        
        # Extract full date mentions (only if booking context exists)
        if has_booking_context:
            # Month + day patterns
            month_day = re.search(
                r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?',
                msg_lower
            )
            if month_day:
                month = month_day.group(1).title()
                day = month_day.group(2)
                year = month_day.group(3) or "2025"
                info["reservation_date"] = f"{month} {day}, {year}"
                print(f"[Memory] Remembered reservation date: {info['reservation_date']}")
            else:
                # Try other date patterns
                date_patterns = [
                    (r'(today|tonight)', "today"),
                    (r'(tomorrow)', "tomorrow"),
                    (r'(this weekend)', "this weekend"),
                    (r'(next week)', "next week"),
                    (r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', None),
                    (r'(\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)', None),
                ]
                for pattern, replacement in date_patterns:
                    match = re.search(pattern, msg_lower)
                    if match:
                        info["reservation_date"] = replacement or match.group(1).title()
                        print(f"[Memory] Remembered reservation date: {info['reservation_date']}")
                        break
        
        # Extract time mentions - must have am/pm or be followed by "o'clock"
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm|a\.m\.|p\.m\.))',  # 8:00pm
            r'(\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.))',  # 8pm
            r'(\d{1,2}\s*o\'?clock)',  # 8 o'clock
            r'at\s+(\d{1,2})\b(?!\s*(?:st|nd|rd|th|people|guests|person))',  # at 8 (not "at 25th")
        ]
        for pattern in time_patterns:
            time_match = re.search(pattern, msg_lower)
            if time_match:
                info["reservation_time"] = time_match.group(1)
                print(f"[Memory] Remembered reservation time: {info['reservation_time']}")
                break

        # Extract location/seating preference
        location_patterns = [
            (r'\b(terrace|patio|outdoor|outside)\b', "outdoor terrace"),
            (r'\b(indoor|inside)\b', "indoor"),
            (r'\b(private room|private dining)\b', "private room"),
            (r'\b(bar|counter)\b', "bar area"),
            (r'\b(window|by the window)\b', "window seat"),
        ]
        for pattern, location in location_patterns:
            if re.search(pattern, msg_lower):
                info["seating_preference"] = location
                print(f"[Memory] Remembered seating preference: {info['seating_preference']}")
                break
        
        # Distinguish between CREATING a new reservation vs LOOKING UP an existing one
        
        # Phrases that mean they WANT TO CREATE a new booking
        creating_phrases = ['want to book', 'want to make', 'want to reserve', 'like to book', 
                           'like to make', 'like to reserve', 'need to book', 'need to make',
                           'can i book', 'can i make', 'can i reserve', 'make a reservation',
                           'book a table', 'book a room', 'schedule an appointment', 'need an appointment']
        
        # Phrases that mean they ALREADY HAVE a booking
        has_existing_phrases = ['my reservation', 'my appointment', 'my booking', 'i have a reservation', 
                               'i have an appointment', 'i have a booking', 'i booked', 'i reserved', 
                               'i made a reservation', 'check my', 'look up my', 'find my']
        
        if any(phrase in msg_lower for phrase in creating_phrases):
            info["wants_to_book"] = True
            print(f"[Memory] Noted: Customer WANTS TO CREATE a new reservation")
        
        if any(phrase in msg_lower for phrase in has_existing_phrases):
            info["claims_existing_reservation"] = True
            print(f"[Memory] Noted: Customer claims to ALREADY HAVE a reservation")
    
    def _lookup_customer_in_db(self, session_id: str):
        """Look up customer in global database if we have their name."""
        if session_id not in self.conversations:
            return
        
        info = self.conversations[session_id]["customer_info"]
        name = info.get("name")
        
        if not name:
            return
        
        # Look up in global database
        stored = customer_db.find_customer(name)
        if stored:
            print(f"[Memory] Found {name} in database! Restoring their info...")
            # Merge stored data into current session (don't overwrite existing non-empty values)
            for key, value in stored.items():
                if value and (key not in info or not info.get(key)):
                    info[key] = value
                    print(f"[Memory] Restored: {key} = {value}")
            
            # Mark that we found them
            info["found_in_database"] = True
    
    def _save_customer_to_db(self, session_id: str):
        """Save customer info to global database for future sessions."""
        if session_id not in self.conversations:
            return
        
        info = self.conversations[session_id]["customer_info"]
        name = info.get("name")
        
        if not name:
            return
        
        # Save if we have ANY meaningful data (name + anything else)
        has_data = (info.get("reservation_date") or info.get("reservation_time") or 
                    info.get("party_size") or info.get("has_reservation") or
                    info.get("seating_preference") or info.get("phone") or info.get("email"))
        
        if has_data:
            print(f"[Memory] Saving {name} to database with: {info}")
            customer_db.save_customer(name, info)
    
    def _extract_from_confirmation(self, session_id: str, message: str):
        """Extract booking details from agent confirmation messages."""
        conv = self.conversations[session_id]
        info = conv["customer_info"]
        msg_lower = message.lower()
        
        # Check if this is a confirmation message
        confirmation_keywords = ['reserved', 'booked', 'confirmed', 'all set', 'appointment is']
        if not any(kw in msg_lower for kw in confirmation_keywords):
            return
        
        info["has_reservation"] = True
        
        # Extract date from confirmation if not already captured
        if "reservation_date" not in info:
            month_day = re.search(
                r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?',
                msg_lower
            )
            if month_day:
                info["reservation_date"] = f"{month_day.group(1).title()} {month_day.group(2)}"
                print(f"[Memory] Extracted confirmed date: {info['reservation_date']}")
            else:
                # Try simpler patterns
                simple_date = re.search(r'(tonight|today|tomorrow|this evening)', msg_lower)
                if simple_date:
                    info["reservation_date"] = simple_date.group(1)
                    print(f"[Memory] Extracted confirmed date: {info['reservation_date']}")
        
        # Extract time from confirmation if not already captured
        if "reservation_time" not in info:
            time_match = re.search(r'at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|p\.m\.|a\.m\.)?)', msg_lower)
            if time_match:
                info["reservation_time"] = time_match.group(1)
                print(f"[Memory] Extracted confirmed time: {info['reservation_time']}")
        
        # Extract party size from confirmation if not already captured
        if "party_size" not in info:
            party_match = re.search(r'(?:for|party of)\s+(\d+)|(\d+)\s+(?:people|guests)', msg_lower)
            if party_match:
                info["party_size"] = party_match.group(1) or party_match.group(2)
                print(f"[Memory] Extracted confirmed party size: {info['party_size']}")
    
    def clear(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_memory_summary(self, session_id: str) -> str:
        """Get a summary of remembered customer information."""
        if session_id not in self.conversations:
            return ""
        
        info = self.conversations[session_id]["customer_info"]
        if not info:
            return ""
        
        found_in_db = info.get("found_in_database", False)
        if found_in_db:
            parts = ["[RETURNING CUSTOMER - We found their information from a previous visit! Use this data:]"]
        else:
            parts = ["[CUSTOMER INFORMATION - Use this in your responses]"]
        
        if "name" in info:
            parts.append(f"- Customer's name: {info['name']} (Address them by name!)")
        
        # Build reservation summary if we have any booking details
        reservation_parts = []
        if info.get("has_reservation") or info.get("reservation_date") or info.get("reservation_time"):
            reservation_parts.append("- RESERVATION DETAILS (Customer made this booking in this conversation):")
            if "reservation_date" in info:
                reservation_parts.append(f"  * Date: {info['reservation_date']}")
            if "reservation_time" in info:
                reservation_parts.append(f"  * Time: {info['reservation_time']}")
            if "party_size" in info:
                reservation_parts.append(f"  * Party size: {info['party_size']} people")
            if "seating_preference" in info:
                reservation_parts.append(f"  * Seating: {info['seating_preference']}")
            parts.extend(reservation_parts)
        elif "party_size" in info:
            parts.append(f"- Party size mentioned: {info['party_size']} people")
        
        if "phone" in info:
            parts.append(f"- Phone number: {info['phone']}")
        if "email" in info:
            parts.append(f"- Email: {info['email']}")
        
        if len(parts) > 1:
            parts.append("\nIMPORTANT: When the customer asks about their reservation/appointment, tell them the EXACT details from above. You already have this information from their previous visit - use it!")
            parts.append("Say something like 'Yes, I have your reservation right here!' and give them the specific details.")
        
        return "\n".join(parts) if len(parts) > 1 else ""
    
    def has_complete_reservation(self, session_id: str) -> bool:
        """Check if we have COMPLETE reservation details (not just partial)."""
        if session_id not in self.conversations:
            return False
        info = self.conversations[session_id]["customer_info"]
        
        # Only consider it a "complete" reservation if we have enough details
        # Need at least: name + (date or time)
        has_name = bool(info.get("name"))
        has_date = bool(info.get("reservation_date"))
        has_time = bool(info.get("reservation_time"))
        
        # If they found in database, we have their info
        if info.get("found_in_database") and has_name:
            return True
        
        # Otherwise need name plus at least date or time that was explicitly given
        return has_name and (has_date or has_time)
    
    def build_full_context(self, session_id: str, current_message: str) -> str:
        """Build the complete context string for the API call."""
        if session_id not in self.conversations:
            return current_message
        
        conv = self.conversations[session_id]
        parts = []
        
        # System prompt / Role definition
        parts.append(f"[YOUR ROLE AND INSTRUCTIONS]\n{conv['system_prompt']}")
        
        # Memory summary (key customer facts)
        memory = self.get_memory_summary(session_id)
        if memory:
            parts.append(f"\n{memory}")
        
        # Conversation history
        if conv["messages"]:
            parts.append("\n[CONVERSATION HISTORY]")
            for msg in conv["messages"]:
                if msg["role"] == "user":
                    parts.append(f"Customer: {msg['content']}")
                elif msg["role"] == "assistant":
                    parts.append(f"You (Agent): {msg['content']}")
        
        # Current message
        parts.append(f"\n[CURRENT MESSAGE FROM CUSTOMER]")
        parts.append(f"Customer: {current_message}")
        
        # Check reservation status
        has_complete_reservation = self.has_complete_reservation(session_id)
        info = conv.get("customer_info", {})
        wants_to_book = info.get("wants_to_book", False)
        claims_existing = info.get("claims_existing_reservation", False)
        has_name = bool(info.get("name"))
        
        # Instructions for response
        parts.append(f"""
[RESPONSE INSTRUCTIONS]
1. LISTEN FIRST: Don't assume you know what the customer wants. Ask clarifying questions if needed.
2. DON'T ASSUME: Never claim to have information you don't have. If unsure, ASK.
3. Be conversational and warm - you're on a phone call
4. Keep responses concise (2-3 sentences)
5. Use the customer's name if you know it
6. If the customer mentions a problem or concern, acknowledge it with empathy FIRST, then ask how you can help
7. Do not include role labels like "Agent:" - just speak directly

[HANDLING RESERVATIONS]
{f"RETURNING CUSTOMER: You have their complete reservation details above - confirm them!" if has_complete_reservation else f'''{"CUSTOMER WANTS TO BOOK: They want to CREATE a new reservation. You MUST ask for missing information BEFORE confirming anything:" if wants_to_book else ""}
{"- Ask for their NAME first if you don't have it" if not has_name else ""}
{"- Ask what DATE/TIME they prefer" if not info.get("reservation_date") and not info.get("reservation_time") else ""}
{"- Ask how many GUESTS/PEOPLE" if not info.get("party_size") else ""}
{"- Only CONFIRM the booking once you have: name, date/time, and party size" if wants_to_book else ""}

{"CUSTOMER CLAIMS EXISTING RESERVATION: Ask for their NAME to look it up." if claims_existing and not has_name else ""}

CRITICAL RULES:
- NEVER say "I have your reservation right here" unless you actually have their name + date + time above
- If they say "I want to make a reservation" - that means they DON'T have one yet, ASK for details!
- Always gather: NAME, DATE/TIME, PARTY SIZE before confirming any booking
- Be helpful and conversational while collecting this information'''
}""")

        return "\n".join(parts)


# Global conversation manager instance
conversation_manager = ConversationManager()
