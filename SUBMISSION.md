# Subconscious Voice Agent - Technical Submission

**Author:** Cem Emir Senyurt  
**Email:** cememirsenyurt99@gmail.com  
**Repository:** https://github.com/cememirsenyurt/subconscious  

---

## Overview

This project demonstrates a voice-enabled AI agent platform built on the Subconscious API. The system allows users to interact with specialized discovery agents through voice or text, finding real businesses and completing mock bookings. Each agent leverages Subconscious's web search capabilities to return actual business data including names, prices, reviews, and availability.

The core insight driving this project: Subconscious excels at long-horizon reasoning and tool use. Rather than building a simple chatbot, I created agents that actively search the web, extract structured information, and maintain persistent memory across sessions.

---

## Architecture

### Stack
- **Backend:** Python/Flask
- **AI Engine:** Subconscious API (tim-large)
- **Voice:** Browser MediaRecorder + Server-side Speech Recognition + Web Speech Synthesis
- **Frontend:** Vanilla HTML/CSS/JavaScript

### Key Components

**1. Smart Memory System**

The platform uses a two-layer approach for information extraction:
- Primary extraction via Subconscious AI (not regex patterns)
- Persistent customer database that survives session restarts

When a user says "My name is Kevin and I'm looking for a 3 bedroom house in San Mateo with a budget around 800k," the system extracts: name, property type, bedrooms, location, and budget - all through AI understanding, not hardcoded patterns.

**2. Intelligent Search Detection**

Not every message needs web search. The system analyzes each message to determine if it requires real-time data:
- "Hi my name is Kelly" → No search, instant response
- "Find gyms in San Francisco with prices" → Web search, returns real gyms

This prevents unnecessary API calls and keeps conversational exchanges fast.

**3. Discovery Agents**

Six specialized agents, each configured to find real businesses:
- Restaurant Finder - Search restaurants, make reservations
- Fitness Finder - Compare gyms and membership prices
- Hotel Finder - Find hotels, book rooms
- Property Finder - Search real estate listings
- Healthcare Finder - Locate doctors and clinics
- Salon Finder - Find salons and spas

Each agent uses the same underlying architecture but with domain-specific prompts and extraction logic.

---

## Subconscious Features Used

**Platform Tools**
- `web_search` - Real-time Google search for current business data
- `parallel_search` - Authoritative source verification

**SDK Integration**
- Async run creation with polling
- Streaming endpoint support (SSE)
- Tool configuration and management

**Custom Function Tools (Prepared)**
- `/api/tools/lookup_customer` - Agent can query our database
- `/api/tools/save_booking` - Agent can create reservations
- `/api/tools/check_availability` - Real-time availability checks

---

## Sample Interaction

**User:** "Find Italian restaurants in San Mateo"

**Agent Response:**
> I found these Italian restaurants in San Mateo:
> 1. Pausa Bar & Cookery - Contemporary Italian, Michelin recognized, upscale
> 2. Sapore Express - Fresh handmade pasta, casual, family-friendly
> 3. La Lanterna - Traditional Italian, family-run, medium-priced
> 4. Vespucci Ristorante Italiano - Classic menu, great for dinner
>
> Would you like to make a reservation at any of these?

**User:** "Book Pausa Bar for 4 people Saturday at 7pm. My name is Kevin, phone 555-1234"

**System extracts and stores:**
```
restaurant: Pausa Bar & Cookery
party_size: 4
date: Saturday
time: 7pm
name: Kevin
phone: 555-1234
```

On the next call, when Kevin identifies himself, the system retrieves his reservation details.

---

## Running the Project

```bash
git clone https://github.com/cememirsenyurt/subconscious.git
cd subconscious
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file with your API key
echo "SUBCONSCIOUS_API_KEY=your_key_here" > .env

python app.py
# Open http://localhost:5001
```

---

## Suggested Improvements for Subconscious Platform

Based on my development experience:

1. **Structured Output Mode** - Option to return JSON alongside natural language would simplify extraction pipelines

2. **Webhook Support for Long Runs** - Web searches can take 15-30 seconds; webhooks would be cleaner than polling

3. **Tool Result Visibility** - Exposing which tools were called and their raw results would help with debugging

4. **Streaming + Tools** - Currently streaming doesn't work well with tool calls; combining them would improve UX

5. **Rate Limit Headers** - Including rate limit info in response headers would help with throttling

6. **Cached Search Results** - Option to cache recent search results would reduce latency for common queries

---

## Conclusion

This project demonstrates that Subconscious is well-suited for building agents that need to take real-world actions - not just chat. The combination of web search tools, long-horizon reasoning, and the clean SDK made it possible to build a functional business discovery platform in a short timeframe.

The voice interface adds accessibility, but the core value is in the agent architecture: smart search detection, AI-powered extraction, and persistent memory. These patterns could extend to any domain where users need to discover, compare, and transact with real businesses.
