# Email to Send

**To:** hongyin@subconscious.dev, jack@subconscious.dev  
**Subject:** Subconscious Agent Submission - Voice-Enabled Business Discovery Platform

---

Hi Hongyin and Jack,

Thanks for the opportunity to experiment with Subconscious. I built a voice-enabled agent platform that helps users discover and book real businesses - restaurants, gyms, hotels, clinics, and more.

**Repository:** https://github.com/cememirsenyurt/subconscious

**What it does:**
- Six specialized discovery agents (Restaurant Finder, Fitness Finder, etc.)
- Uses web_search and parallel_search to find actual businesses with real prices and reviews
- Voice input via browser + text-to-speech responses
- AI-powered information extraction (not regex) that persists across sessions
- Smart detection to only trigger web search when needed

**Example:** A user asks "Find gyms in San Mateo" and gets back Equinox ($330/mo), Crunch ($15-30/mo), 24 Hour Fitness ($30-55/mo) with real details. They can then "sign up" and the system remembers them on future calls.

**Technical notes:**
- Built with Python/Flask + Subconscious SDK
- Uses tim-large engine with platform tools
- Prepared custom function tools for database callbacks (though not deployed publicly yet)

I documented my experience and some platform feedback in SUBMISSION.md in the repo. A few things that would have helped: structured JSON output mode, webhooks for long-running searches, and better streaming + tools integration.

Happy to walk through the code or demo it live if useful.

Best,  
Cem Emir Senyurt  
cememirsenyurt99@gmail.com
