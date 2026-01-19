"""
Custom Tool Endpoints for Subconscious Function Calling

These endpoints are called BY Subconscious during agent execution.
They provide real-time access to our customer database and booking system.
"""

from flask import Blueprint, request, jsonify
from services import customer_db

tools_bp = Blueprint('tools', __name__)


@tools_bp.route("/api/tools/lookup_customer", methods=["POST"])
def lookup_customer():
    """
    Tool: Look up customer information.
    Called by Subconscious when agent needs to find a customer.
    """
    data = request.get_json() or {}
    
    customer_name = data.get("customer_name", "").strip()
    business_id = data.get("business_id", "")
    
    if not customer_name:
        return jsonify({
            "found": False,
            "message": "No customer name provided"
        })
    
    # Look up in our database
    customer_info = customer_db.find_customer(customer_name, business_id)
    
    if customer_info:
        return jsonify({
            "found": True,
            "customer": customer_info,
            "message": f"Found customer {customer_name} in our records"
        })
    else:
        return jsonify({
            "found": False,
            "message": f"No record found for {customer_name}. They may be a new customer."
        })


@tools_bp.route("/api/tools/save_booking", methods=["POST"])
def save_booking():
    """
    Tool: Save a booking/reservation.
    Called by Subconscious when agent confirms a booking.
    """
    data = request.get_json() or {}
    
    customer_name = data.get("customer_name", "").strip()
    business_id = data.get("business_id", "")
    booking_details = data.get("booking_details", {})
    
    if not customer_name:
        return jsonify({
            "success": False,
            "message": "Customer name is required"
        })
    
    # Save to database
    save_data = {
        "name": customer_name,
        **booking_details,
        "booking_confirmed": True
    }
    
    customer_db.save_customer(customer_name, business_id, save_data)
    
    return jsonify({
        "success": True,
        "message": f"Booking saved for {customer_name}",
        "booking": save_data
    })


@tools_bp.route("/api/tools/check_availability", methods=["POST"])
def check_availability():
    """
    Tool: Check availability for a date/time.
    Called by Subconscious when customer asks about availability.
    
    Note: This is a mock - in production, connect to real booking system.
    """
    data = request.get_json() or {}
    
    business_id = data.get("business_id", "")
    date = data.get("date", "")
    time = data.get("time", "")
    service_type = data.get("service_type", "")
    
    # Mock availability responses based on business
    availability_responses = {
        "restaurant": {
            "available": True,
            "message": f"We have availability on {date}" + (f" at {time}" if time else "") + ". Would you like to book?",
            "options": ["Indoor seating", "Outdoor terrace", "Private room"]
        },
        "hotel": {
            "available": True,
            "message": f"We have rooms available for {date}.",
            "options": ["Standard Room ($199)", "Deluxe Room ($299)", "Suite ($499)"]
        },
        "salon": {
            "available": True,
            "message": f"We have openings on {date}" + (f" around {time}" if time else "") + ".",
            "stylists": ["Maria (Master Stylist)", "Jake (Color Specialist)", "Sofia"]
        },
        "gym": {
            "available": True,
            "message": f"You can start your membership anytime! We're open 5am-11pm weekdays.",
            "options": ["Basic ($39/mo)", "Plus ($59/mo)", "Premium ($89/mo)"]
        },
        "clinic": {
            "available": True,
            "message": f"We have appointment slots on {date}.",
            "doctors": ["Dr. Smith", "Dr. Chen", "Dr. Patel"]
        },
        "realestate": {
            "available": True,
            "message": f"We can schedule property viewings for {date}.",
            "agents": ["Available agents ready to help"]
        }
    }
    
    response = availability_responses.get(business_id, {
        "available": True,
        "message": f"Checking availability for {date}..."
    })
    
    return jsonify(response)


@tools_bp.route("/api/tools/get_business_info", methods=["POST"])
def get_business_info():
    """
    Tool: Get detailed business information.
    Provides hours, location, services, etc.
    """
    data = request.get_json() or {}
    business_id = data.get("business_id", "")
    
    from models import BUSINESSES
    
    if business_id in BUSINESSES:
        business = BUSINESSES[business_id]
        return jsonify({
            "name": business.name,
            "greeting": business.greeting,
            "sample_services": business.sample_queries
        })
    
    return jsonify({"error": "Business not found"})
