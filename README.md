# 🎙️ Subconscious Voice Agent Demo

**A production-ready voice agent platform showcasing Subconscious AI's long-context reasoning capabilities.**

Built by Cem Emir Senyurt as part of the Subconscious Founding Engineer interview process.

---

## 📋 Table of Contents

1. [What I Built](#what-i-built)
2. [Why Subconscious](#why-subconscious)
3. [Quick Start](#quick-start)
4. [Architecture](#architecture)
5. [Features Deep Dive](#features-deep-dive)
6. [My Experience with the Platform](#my-experience-with-the-platform)
7. [Suggested Improvements](#suggested-improvements)
8. [Demo Screenshots](#demo-screenshots)

---

## 🎯 What I Built

A **multi-business voice agent platform** that demonstrates Subconscious's key differentiators:

| Feature | Implementation |
|---------|----------------|
| **Long-context reasoning** | Full conversation history + extracted facts sent to `tim-large` |
| **Cross-session memory** | Customer database persists reservations across "phone calls" |
| **Real-time voice** | Browser speech recognition + text-to-speech |
| **Multiple personas** | 6 business types with unique personalities |
| **Production structure** | Flask blueprints, services layer, clean architecture |

### The Demo Flow

1. **User selects a business** (Hotel, Restaurant, Clinic, Salon, Real Estate, Gym)
2. **"Calls" the business** - Agent greets with business-specific personality
3. **Converses naturally** - Voice in, voice out
4. **Makes a reservation** - Agent remembers name, date, time, party size
5. **Ends call, calls back later** - Agent remembers everything from the database
6. **Asks "What's my reservation?"** - Agent instantly recalls all details

---

## 🔬 Why Subconscious (vs OpenAI/Claude directly)

I chose to build on Subconscious because the use case demands:

| Requirement | Why Subconscious Fits |
|-------------|----------------------|
| **Long conversations** | `tim-large` handles extended context without degradation |
| **Memory across sessions** | Platform designed for stateful, long-running agents |
| **Tool orchestration** | Built-in `parallel_search`, `web_search` for future enhancements |
| **Production-ready** | Async runs, webhooks, structured output - enterprise features |

### What I Used

```python
from subconscious import Subconscious

client = Subconscious(api_key=SUBCONSCIOUS_API_KEY)

run = client.run(
    engine="tim-large",
    input={
        "instructions": full_context_with_memory,
        "tools": [{"type": "platform", "id": "parallel_search"}]
    },
    options={"await_completion": True}
)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- ffmpeg (for audio conversion): `brew install ffmpeg`
- Subconscious API key from [subconscious.dev](https://subconscious.dev)

### Setup

```bash
# Clone the repository
git clone https://github.com/cememirsenyurt/subconscious.git
cd subconscious

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your SUBCONSCIOUS_API_KEY

# Run the application
python app.py
```

### Access

Open http://localhost:5001 in your browser.

---

## 🏗️ Architecture

```
subconscious/
├── app.py                    # Application factory (65 lines)
├── config.py                 # Configuration management
│
├── models/
│   ├── __init__.py
│   └── business.py           # 6 business templates with personalities
│
├── services/
│   ├── __init__.py
│   ├── customer_db.py        # Cross-session memory storage
│   ├── conversation.py       # Context building + fact extraction
│   └── subconscious_api.py   # Official SDK integration
│
├── routes/
│   ├── __init__.py
│   ├── main.py               # UI routes
│   ├── chat.py               # Subconscious API endpoint
│   ├── transcribe.py         # Speech-to-text
│   └── debug.py              # Development tools
│
├── templates/
│   └── index.html            # Phone-call UI
│
└── static/
    ├── css/style.css         # Dark theme styling
    └── js/app.js             # Voice handling + API calls
```

### Design Decisions

1. **Flask Blueprints**: Modular routing for scalability
2. **Service Layer**: Business logic separated from routes
3. **Factory Pattern**: `create_app()` for testing flexibility
4. **Graceful Fallback**: SDK → HTTP if SDK unavailable

---

## 🔍 Features Deep Dive

### 1. Contextual Memory System

The `ConversationManager` extracts and remembers:

```python
# Automatically extracted from conversation:
{
    "name": "Jason Statham",
    "reservation_date": "Tonight",
    "reservation_time": "7:00 p.m.",
    "party_size": "2",
    "seating_preference": "outdoor terrace",
    "found_in_database": True  # Retrieved from previous session!
}
```

### 2. Cross-Session Persistence

```
Session 1: "Hi, I'm Jason. Table for 2, tonight at 7pm on the terrace"
           → Saved to CustomerDatabase

Session 2: "Hi, my name is Jason. What's my reservation?"
           → Looked up → "Yes! Tonight at 7pm, terrace, party of 2"
```

### 3. Smart Name Extraction

Handles variations:
- "My name is Jason Statham"
- "I'm Jason"
- "This is Jason"
- Just "Jason" as a response

Avoids false positives:
- "My name is Jason. **What** time?" → Extracts "Jason", not "Jason What"

### 4. Business Personas

Each business has:
- Unique greeting
- Specific system prompt with personality
- Relevant information (menu, rates, hours)
- Sample queries for UI hints

---

## 📝 My Experience with the Platform

### What Worked Well ✅

| Aspect | Notes |
|--------|-------|
| **API Design** | Clean REST endpoints, predictable responses |
| **tim-large Quality** | Excellent at maintaining persona, natural responses |
| **Async Model** | `await_completion: True` simplifies integration |
| **Dashboard** | Clean UI, easy API key management |
| **Documentation** | Quickstart got me running in minutes |

### Friction Points / Learnings 📚

| Issue | How I Solved It |
|-------|-----------------|
| **202 Queued Response** | Had to implement polling loop (not obvious from docs) |
| **No built-in memory** | Built custom `CustomerDatabase` + `ConversationManager` |
| **Tool usage unclear** | Trial and error with `{"type": "platform", "id": "..."}` |
| **SDK vs HTTP** | SDK simpler but HTTP gives more control |

### API Response Handling

The async nature required this pattern:

```python
# 1. Create run
response = client.run(..., options={"await_completion": True})

# 2. If 202, poll for result
if response.status == "queued":
    while True:
        status = client.get_run(run_id)
        if status.status == "succeeded":
            return status.result.answer
        time.sleep(2)
```

---

## 💡 Suggested Improvements

### 1. SDK Enhancements

```python
# Current: Manual polling or await_completion blocks
run = client.run(..., options={"await_completion": True})

# Suggested: Async/await support
run = await client.run_async(...)

# Suggested: Callback support
client.run(..., on_complete=lambda r: print(r.answer))
```

### 2. Built-in Conversation Memory

```python
# Current: I build context manually
context = f"""
Previous messages: {history}
Customer info: {extracted_facts}
"""

# Suggested: Platform-level memory
run = client.run(
    ...,
    memory={
        "session_id": "customer-123",
        "persist": True,  # Save across runs
        "extract_entities": True  # Auto-extract names, dates, etc.
    }
)
```

### 3. Structured Output Mode

```python
# Suggested: Schema-enforced responses
run = client.run(
    ...,
    output_schema={
        "type": "object",
        "properties": {
            "response": {"type": "string"},
            "extracted_entities": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "reservation_date": {"type": "string"}
                }
            }
        }
    }
)
# Returns: {"response": "...", "extracted_entities": {...}}
```

### 4. Documentation Improvements

| Current | Suggested |
|---------|-----------|
| Quickstart shows basic run | Add multi-turn conversation example |
| Tools listed but not explained | Add tool-specific guides with use cases |
| No error handling examples | Add common errors + solutions |
| No webhook examples | Add webhook setup tutorial |

### 5. Platform Features Wishlist

- **Conversation API**: `POST /conversations/{id}/messages` for stateful chats
- **Entity extraction tool**: Built-in NER for names, dates, phone numbers
- **Voice mode**: Direct audio input → Subconscious → audio output
- **Playground history**: Save and replay conversations for debugging

---

## 📸 Demo Screenshots

### Business Selection
Dark-themed card grid with 6 business options, each with icon and sample queries.

### Voice Call Interface
Phone-call style UI with:
- Business name and avatar
- Message bubbles (user: purple, agent: dark gray)
- Voice controls (mic, call, speaker)
- "Try saying:" suggestions

### Memory in Action
```
Call 1: "I'm Jason Statham, reservation for tonight at 7pm, terrace, party of 2"
        → Agent confirms booking

Call 2: "Hi, my name is Jason. What's my reservation info?"
        → Agent: "Your reservation is for tonight at 7:00 p.m. on our outdoor terrace!"
```

---

## 🛠️ Technical Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, Flask, Blueprints |
| **AI** | Subconscious SDK, tim-large engine |
| **Speech** | Web Speech API (TTS), Google Speech Recognition (STT) |
| **Audio** | pydub, ffmpeg |
| **Frontend** | Vanilla JS, CSS Variables, MediaRecorder API |

---

## 📄 License

MIT License - Feel free to use this as a starting point for your own Subconscious projects.

---

## 🙏 Acknowledgments

- **Subconscious Team** - For building a platform that makes agent development enjoyable
- **Jack & Hongyin** - For the opportunity to explore and build

---

*Built with ☕ and curiosity by Cem Emir Senyurt*  
📧 cememirsenyurt99@gmail.com  
🔗 github.com/cememirsenyurt
