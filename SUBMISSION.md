# Subconscious Interview Submission

**Candidate**: Cem Emir Senyurt  
**Position**: Founding Engineer - New Grad  
**Date**: January 2026

---

## 📦 What I Built

**A Voice Agent Platform for Businesses** - Users can "call" various businesses (hotel, restaurant, clinic, etc.) and have natural voice conversations. The agent remembers context within a call AND across sessions.

**Repository**: https://github.com/cememirsenyurt/subconscious

**Live Demo**: Run locally with `python app.py` → http://localhost:5001

---

## 🔑 Key Features Demonstrating Subconscious Capabilities

### 1. Long-Context Reasoning
- Full conversation history sent to `tim-large`
- 6 different business personas with 50+ line system prompts
- Agent maintains character throughout extended conversations

### 2. Cross-Session Memory (Long-Term)
- Customer makes reservation → stored in database
- Customer "hangs up", calls back later
- Says their name → agent instantly retrieves their reservation
- **This is what Subconscious is known for**

### 3. Production-Ready Architecture
```
app.py (65 lines) → routes/ → services/ → models/
```
- Flask Blueprints for modularity
- Official Subconscious SDK integration
- Graceful fallback to HTTP if SDK unavailable

---

## 🎯 My Experience Summary

### What Worked Great
| Aspect | Rating | Notes |
|--------|--------|-------|
| API Design | ⭐⭐⭐⭐⭐ | Clean, predictable REST endpoints |
| tim-large Quality | ⭐⭐⭐⭐⭐ | Excellent persona maintenance |
| Dashboard UX | ⭐⭐⭐⭐ | Easy key management, clear usage |
| Quickstart Docs | ⭐⭐⭐⭐ | Got running in 5 minutes |

### Friction I Encountered
| Issue | Severity | My Solution |
|-------|----------|-------------|
| 202 async response not obvious | Medium | Built polling loop |
| No built-in conversation memory | High | Built `CustomerDatabase` class |
| Tool payload format unclear | Low | Trial and error |

---

## 💡 Top 5 Improvement Suggestions

### 1. **Built-in Conversation Memory**
```python
# Current: I manually build context each time
# Suggested:
client.run(memory={"session_id": "user-123", "persist": True})
```

### 2. **Entity Extraction Tool**
```python
# Current: I regex-parse names, dates, times
# Suggested: Built-in NER tool
tools=[{"type": "platform", "id": "entity_extraction"}]
```

### 3. **Async/Await SDK Support**
```python
# Current: Blocking await_completion or manual polling
# Suggested:
run = await client.run_async(...)
```

### 4. **Webhook Examples in Docs**
Currently: Webhooks mentioned but no examples
Suggested: Full tutorial with Express/Flask setup

### 5. **Conversation API**
```
POST /conversations/{id}/messages  # Stateful!
GET /conversations/{id}/history
```

---

## 📊 Technical Details

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11, Flask 2.3 |
| AI | Subconscious SDK, tim-large |
| Speech | Web Speech API + Google STT |
| Audio | pydub + ffmpeg |
| Frontend | Vanilla JS, CSS Variables |

**Lines of Code**:
- Python: ~800 lines across 12 files
- JavaScript: ~400 lines
- CSS: ~300 lines

---

## 🏃 How to Run

```bash
git clone https://github.com/[YOUR_USERNAME]/subconscious.git
cd subconscious
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "SUBCONSCIOUS_API_KEY=your-key" > .env
python app.py
# Open http://localhost:5001
```

---

## 🎬 Demo Scenario

**Call 1** (Session A):
```
User: "Hi, my name is Jason Statham. I want to make a reservation for tonight."
Agent: "Buonasera, Mr. Statham! I'd be happy to help. What time works for you?"
User: "7pm, terrace, party of two"
Agent: "Perfect! I have you down for tonight at 7pm on our outdoor terrace for 2 guests."
```

**Call 2** (Session B - NEW session!):
```
User: "Hi, my name is Jason. What's my reservation info?"
Agent: "Yes, I have your reservation right here! Tonight at 7:00 p.m. on our outdoor terrace for 2 guests. We can't wait to welcome you!"
```

**The agent remembered Jason across sessions.** That's the Subconscious difference.

---

## 📞 Contact

Ready to discuss the project, dive into the code, or talk about the role!

- Email: cememirsenyurt99@gmail.com
- GitHub: github.com/cememirsenyurt

---

*Thank you for the opportunity to build with Subconscious!*
