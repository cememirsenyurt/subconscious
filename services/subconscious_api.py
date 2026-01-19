"""
Subconscious API Integration Service.

Uses the official Subconscious SDK with TOOLS enabled for:
- Web search for real-time information
- Parallel search for comprehensive lookups
- Long-horizon agent reasoning
"""

import json
import time
import requests
from typing import Dict, Any, List, Optional

from config import SUBCONSCIOUS_API_KEY, SUBCONSCIOUS_BASE_URL, DEFAULT_ENGINE

# Try to use official SDK
try:
    from subconscious import Subconscious
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("[Subconscious] SDK not available, using HTTP")


# Available Subconscious platform tools
PLATFORM_TOOLS = {
    "web_search": {"type": "platform", "id": "web_search"},
    "parallel_search": {"type": "platform", "id": "parallel_search"},
    "parallel_extract": {"type": "platform", "id": "parallel_extract"},
    "webpage_understanding": {"type": "platform", "id": "webpage_understanding"},
}


def call_subconscious_api(
    instructions: str, 
    engine: str = None,
    enable_tools: bool = True,
    tools: List[str] = None
) -> Dict[str, Any]:
    """
    Call the Subconscious API with optional tool usage.
    
    Args:
        instructions: The prompt to send
        engine: Engine to use (default: tim-large)
        enable_tools: Whether to enable platform tools
        tools: List of tool IDs to enable (default: web_search, parallel_search)
    
    Returns:
        Dict with success, answer, and metadata
    """
    if not SUBCONSCIOUS_API_KEY:
        return {
            "success": False,
            "error": "API key not configured",
            "answer": "I apologize, but I'm having technical difficulties. Please try again."
        }
    
    engine = engine or DEFAULT_ENGINE
    
    # Build tools list
    tool_list = None
    if enable_tools:
        tool_ids = tools or ["web_search", "parallel_search"]
        tool_list = [PLATFORM_TOOLS[tid] for tid in tool_ids if tid in PLATFORM_TOOLS]
    
    # Try SDK first, fall back to HTTP
    if SDK_AVAILABLE:
        return _call_with_sdk(instructions, engine, tool_list)
    else:
        return _call_with_http(instructions, engine, tool_list)


def _call_with_sdk(instructions: str, engine: str, tools: List[Dict]) -> Dict[str, Any]:
    """Call using official SDK."""
    try:
        client = Subconscious(api_key=SUBCONSCIOUS_API_KEY)
        
        input_data = {"instructions": instructions}
        if tools:
            input_data["tools"] = tools
        
        print(f"[Subconscious SDK] Running with engine={engine}, tools={bool(tools)}")
        
        run = client.run(
            engine=engine,
            input=input_data,
            options={"await_completion": True}
        )
        
        if run.result and hasattr(run.result, 'answer') and run.result.answer:
            return {
                "success": True,
                "answer": run.result.answer,
                "tool_calls": getattr(run.result, 'tool_calls', None),
                "sources": getattr(run.result, 'sources', None),
            }
        else:
            return _call_with_http(instructions, engine, tools)  # Fallback
            
    except Exception as e:
        print(f"[Subconscious SDK] Error: {e}")
        return _call_with_http(instructions, engine, tools)


def _call_with_http(instructions: str, engine: str, tools: List[Dict]) -> Dict[str, Any]:
    """Call using HTTP (fallback)."""
    headers = {
        "Authorization": f"Bearer {SUBCONSCIOUS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    input_data = {"instructions": instructions}
    if tools:
        input_data["tools"] = tools
    
    payload = {
        "engine": engine,
        "input": input_data
    }
    
    try:
        print(f"[Subconscious HTTP] Creating run...")
        response = requests.post(
            f"{SUBCONSCIOUS_BASE_URL}/runs",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201, 202]:
            return {
                "success": False,
                "error": f"API error: {response.status_code}",
                "answer": "I'm having trouble connecting. Please try again."
            }
        
        data = response.json()
        run_id = data.get("runId")
        
        if not run_id:
            if data.get("result", {}).get("answer"):
                return {"success": True, "answer": data["result"]["answer"]}
            return {
                "success": False,
                "error": "No runId",
                "answer": "Something went wrong. Please try again."
            }
        
        # Poll for completion
        for i in range(30):
            time.sleep(2)
            
            status_resp = requests.get(
                f"{SUBCONSCIOUS_BASE_URL}/runs/{run_id}",
                headers=headers,
                timeout=30
            )
            
            if status_resp.status_code != 200:
                continue
            
            status_data = status_resp.json()
            status = status_data.get("status")
            
            if status == "succeeded":
                result = status_data.get("result", {})
                answer = result.get("answer", "")
                if answer:
                    return {
                        "success": True,
                        "answer": answer,
                        "tool_calls": result.get("tool_calls"),
                        "sources": result.get("sources"),
                    }
            elif status in ["failed", "error", "cancelled"]:
                return {
                    "success": False,
                    "error": status_data.get("error", "Run failed"),
                    "answer": "I couldn't process that. Please try again."
                }
        
        return {
            "success": False,
            "error": "Timeout",
            "answer": "That's taking too long. Please try again."
        }
        
    except Exception as e:
        print(f"[Subconscious HTTP] Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "answer": "I'm having connection issues. Please try again."
        }


def extract_details_with_ai(message: str, context: str = "") -> Dict[str, Any]:
    """
    Use Subconscious to extract important details from a message.
    Returns a dictionary of extracted information.
    """
    prompt = f"""Extract ALL important details from this customer message.
Return a JSON object with relevant information found.

Use descriptive, lowercase keys with underscores (e.g., "party_size", "preferred_date").
ONLY include fields explicitly mentioned. Do not assume or invent data.

{f"Previous context: {context}" if context else ""}

Customer message: "{message}"

Return ONLY a valid JSON object:"""

    result = call_subconscious_api(
        instructions=prompt,
        enable_tools=False  # No tools needed for extraction
    )
    
    if result["success"]:
        try:
            # Try to parse JSON from the response
            answer = result["answer"].strip()
            # Handle markdown code blocks
            if "```json" in answer:
                answer = answer.split("```json")[1].split("```")[0]
            elif "```" in answer:
                answer = answer.split("```")[1].split("```")[0]
            
            extracted = json.loads(answer)
            if isinstance(extracted, dict):
                return extracted
        except json.JSONDecodeError:
            pass
    
    return {}


def search_for_info(query: str) -> Dict[str, Any]:
    """
    Use Subconscious with web search to find real information.
    """
    prompt = f"""Search for and provide accurate information about: {query}

Include relevant links/sources if available.
Be concise but helpful."""

    return call_subconscious_api(
        instructions=prompt,
        enable_tools=True,
        tools=["web_search", "parallel_search"]
    )


# For backward compatibility
def stream_subconscious_response(instructions: str, engine: str = None):
    """Stream responses (SSE)."""
    if not SUBCONSCIOUS_API_KEY:
        yield f"data: {json.dumps({'error': 'API key not configured'})}\n\n"
        return
    
    engine = engine or DEFAULT_ENGINE
    
    headers = {
        "Authorization": f"Bearer {SUBCONSCIOUS_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "engine": engine,
        "input": {"instructions": instructions}
    }
    
    try:
        with requests.post(
            f"{SUBCONSCIOUS_BASE_URL}/runs/stream",
            headers=headers,
            json=payload,
            stream=True,
            timeout=120
        ) as response:
            if response.status_code != 200:
                yield f"data: {json.dumps({'error': f'API error: {response.status_code}'})}\n\n"
                return
            
            for line in response.iter_lines():
                if line:
                    yield f"{line.decode('utf-8')}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


def extract_answer(response_data: Dict) -> str:
    """Extract answer from API response."""
    paths = [["result", "answer"], ["answer"], ["output"], ["text"]]
    for path in paths:
        value = response_data
        for key in path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                value = None
                break
        if value and isinstance(value, str):
            return value.strip()
    return str(response_data)
