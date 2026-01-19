"""
Subconscious Voice Agent Demo
============================

A comprehensive voice agent for businesses using Subconscious AI.
Built for interview demonstration.

Features:
- Multiple business types with custom prompts
- Real-time voice interaction via Web Speech API
- Beautiful phone-call style UI
- Streaming responses from Subconscious API
- Long-term contextual memory across sessions

Project Structure:
- config.py          - Configuration settings
- models/            - Data models (Business templates)
- services/          - Business logic (API, Conversation, Database)
- routes/            - Flask route blueprints
- templates/         - HTML templates
- static/            - CSS and JavaScript
"""

from flask import Flask

from config import Config, SUBCONSCIOUS_API_KEY, DEFAULT_ENGINE
from models import BUSINESSES
from routes import main_bp, chat_bp, transcribe_bp, debug_bp


def create_app() -> Flask:
    """
    Application factory for creating the Flask app.
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(transcribe_bp)
    app.register_blueprint(debug_bp)
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎙️  SUBCONSCIOUS VOICE AGENT DEMO")
    print("="*60)
    print(f"\n📍 Server starting at: http://localhost:{Config.PORT}")
    print(f"🔑 API Key configured: {'Yes ✓' if SUBCONSCIOUS_API_KEY else 'No ✗ (set SUBCONSCIOUS_API_KEY)'}")
    print(f"🤖 Engine: {DEFAULT_ENGINE}")
    print(f"\n🏢 Available businesses: {', '.join(BUSINESSES.keys())}")
    print("\n" + "="*60 + "\n")
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
