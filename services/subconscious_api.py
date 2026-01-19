"""
Subconscious API Integration Service.

Uses the official Subconscious Python SDK for:
- Long-horizon agent reasoning
- Built-in tools (parallel_search, web_search, etc.)
- Async run management with await_completion
"""

import json
import time
import requests
from typing import Dict, Any, List, Optional

from config import SUBCONSCIOUS_API_KEY, SUBCONSCIOUS_BASE_URL, DEFAULT_ENGINE

# Try to use official SDK, fall back to HTTP if not available
try:
    from subconscious import Subconscious
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("[Subconscious] SDK not available, using HTTP fallback")


def call_subconscious_api(
    instructions: str, 
    engine: str = None,
    use_tools: bool = False,
    tools: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Call the Subconscious API using the official SDK.
    
    Leverages Subconscious's unique features:
    - Long-context reasoning engine (tim-large)
    - Built-in tools for web search, parallel extraction
    - Await completion for synchronous response
    
    Args:
        instructions: The full prompt/instructions to send to the API
        engine: The engine to use (defaults to DEFAULT_ENGINE from config)
        use_tools: Whether to enable Subconscious platform tools
        tools: Optional list of custom tools to attach
        
    Returns:
        Dictionary with success status, answer, and any error information
    """
    if not SUBCONSCIOUS_API_KEY:
        return {
            "success": False,
            "error": "API key not configured. Set SUBCONSCIOUS_API_KEY environment variable.",
            "answer": "I apologize, but I'm having technical difficulties. Please try again later."
        }
    
    engine = engine or DEFAULT_ENGINE
    
    # Use SDK if available for cleaner integration
    if SDK_AVAILABLE:
        return _call_with_sdk(instructions, engine, use_tools, tools)
    else:
        return _call_with_http(instructions, engine, use_tools, tools)


def _call_with_sdk(
    instructions: str,
    engine: str,
    use_tools: bool,
    tools: Optional[List[Dict]]
) -> Dict[str, Any]:
    """Call API using the official Subconscious SDK."""
    try:
        client = Subconscious(api_key=SUBCONSCIOUS_API_KEY)
        
        # Build the input payload
        input_data = {"instructions": instructions}
        
        # Add platform tools if requested
        # Subconscious provides: parallel_search, parallel_extract, web_search, webpage_understanding
        if use_tools:
            input_data["tools"] = tools or [
                {"type": "platform", "id": "parallel_search"},
            ]
        
        print(f"[Subconscious SDK] Creating run with engine={engine}, tools={use_tools}")
        
        # Use await_completion for synchronous response
        run = client.run(
            engine=engine,
            input=input_data,
            options={"await_completion": True}
        )
        
        # Extract answer from result
        if run.result and hasattr(run.result, 'answer') and run.result.answer:
            print(f"[Subconscious SDK] Success! Answer: {run.result.answer[:100]}...")
            return {
                "success": True,
                "answer": run.result.answer,
                "raw": {
                    "run_id": run.id if hasattr(run, 'id') else None,
                    "status": run.status if hasattr(run, 'status') else None,
                }
            }
        else:
            return {
                "success": False,
                "error": "No answer in response",
                "answer": "I received your message but couldn't generate a response. Please try again."
            }
            
    except Exception as e:
        print(f"[Subconscious SDK] Error: {e}")
        # Fall back to HTTP method
        return _call_with_http(instructions, engine, use_tools, tools)


def _call_with_http(
    instructions: str,
    engine: str,
    use_tools: bool,
    tools: Optional[List[Dict]]
) -> Dict[str, Any]:
    """
    Call API using HTTP (fallback method).
    
    Handles the async nature of Subconscious API:
    1. POST /v1/runs creates a run (returns 202 with runId)
    2. GET /v1/runs/{runId} polls for result
    """
    headers = {
        "Authorization": f"Bearer {SUBCONSCIOUS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build payload with optional tools
    input_data = {"instructions": instructions}
    if use_tools:
        input_data["tools"] = tools or [
            {"type": "platform", "id": "parallel_search"},
        ]
    
    payload = {
        "engine": engine,
        "input": input_data
    }
    
    try:
        # Step 1: Create the run
        print(f"[Subconscious HTTP] Creating run with engine={engine}...")
        response = requests.post(
            f"{SUBCONSCIOUS_BASE_URL}/runs",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201, 202]:
            error_msg = f"API returned status {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get("message", error_data.get("error", error_msg))
            except:
                error_msg = response.text[:200]
            print(f"[Subconscious HTTP] Error creating run: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "answer": "I apologize, but I'm experiencing some difficulties. Could you please repeat that?"
            }
        
        data = response.json()
        run_id = data.get("runId")
        
        if not run_id:
            # Maybe the API returned the result directly
            if data.get("result") and data["result"].get("answer"):
                return {
                    "success": True,
                    "answer": data["result"]["answer"],
                    "raw": data
                }
            print(f"[Subconscious HTTP] No runId in response: {data}")
            return {
                "success": False,
                "error": "No runId returned",
                "answer": "I apologize, but something went wrong. Please try again."
            }
        
        print(f"[Subconscious HTTP] Run created: {run_id}")
        
        # Step 2: Poll for completion
        max_polls = 30  # Max 60 seconds (30 * 2s)
        for i in range(max_polls):
            time.sleep(2)  # Wait 2 seconds between polls
            
            status_response = requests.get(
                f"{SUBCONSCIOUS_BASE_URL}/runs/{run_id}",
                headers=headers,
                timeout=30
            )
            
            if status_response.status_code != 200:
                print(f"[Subconscious HTTP] Poll error: {status_response.status_code}")
                continue
            
            status_data = status_response.json()
            status = status_data.get("status", "unknown")
            print(f"[Subconscious HTTP] Poll {i+1}: status={status}")
            
            if status == "succeeded":
                result = status_data.get("result", {})
                answer = result.get("answer", "")
                
                if answer:
                    print(f"[Subconscious HTTP] Success! Answer: {answer[:100]}...")
                    return {
                        "success": True,
                        "answer": answer,
                        "raw": status_data
                    }
                else:
                    print(f"[Subconscious HTTP] No answer in result: {result}")
                    return {
                        "success": False,
                        "error": "No answer in response",
                        "answer": "I received your message but couldn't generate a response. Please try again."
                    }
            
            elif status in ["failed", "error", "cancelled"]:
                error = status_data.get("error", "Unknown error")
                print(f"[Subconscious HTTP] Run failed: {error}")
                return {
                    "success": False,
                    "error": error,
                    "answer": "I apologize, but I couldn't process that request. Please try again."
                }
        
        # Timeout
        print(f"[Subconscious HTTP] Polling timeout for run {run_id}")
        return {
            "success": False,
            "error": "Request timed out waiting for response",
            "answer": "I'm sorry, that's taking longer than expected. Please try again."
        }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out",
            "answer": "I'm sorry, that took too long. Could you try asking again?"
        }
    except requests.exceptions.RequestException as e:
        print(f"[Subconscious HTTP] Request error: {e}")
        return {
            "success": False,
            "error": str(e),
            "answer": "I'm having trouble connecting. Please try again in a moment."
        }
    except Exception as e:
        print(f"[Subconscious HTTP] Unexpected error: {e}")
        return {
            "success": False,
            "error": str(e),
            "answer": "Something unexpected happened. Please try again."
        }


def call_with_tools(
    instructions: str,
    tool_ids: List[str] = None,
    engine: str = None
) -> Dict[str, Any]:
    """
    Call Subconscious API with specific platform tools enabled.
    
    Available Subconscious platform tools:
    - parallel_search: Search multiple sources in parallel
    - parallel_extract: Extract structured data from multiple pages
    - web_search: Traditional web search (Google)
    - webpage_understanding: Deep page analysis with Jina
    
    Args:
        instructions: The prompt/task for the agent
        tool_ids: List of tool IDs to enable (e.g., ["parallel_search", "web_search"])
        engine: The engine to use
        
    Returns:
        API response dictionary
    """
    tool_ids = tool_ids or ["parallel_search"]
    tools = [{"type": "platform", "id": tid} for tid in tool_ids]
    
    return call_subconscious_api(
        instructions=instructions,
        engine=engine,
        use_tools=True,
        tools=tools
    )


def extract_answer(response_data: Dict) -> str:
    """
    Extract the answer text from various possible API response structures.
    
    Args:
        response_data: The raw API response dictionary
        
    Returns:
        The extracted answer string
    """
    # Try common paths based on documented structure
    paths_to_try = [
        ["result", "answer"],
        ["result", "output"],
        ["result", "text"],
        ["answer"],
        ["output"],
        ["text"],
        ["data", "result", "answer"],
        ["data", "answer"],
    ]
    
    for path in paths_to_try:
        value = response_data
        for key in path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                value = None
                break
        if value and isinstance(value, str):
            return value.strip()
    
    # If we have a result object, try to get any string content
    if "result" in response_data and response_data["result"]:
        result = response_data["result"]
        if isinstance(result, str):
            return result.strip()
        if isinstance(result, dict):
            for key in ["answer", "output", "text", "content", "response"]:
                if key in result and result[key]:
                    return str(result[key]).strip()
    
    # Last resort: stringify the response
    return str(response_data)


def stream_subconscious_response(instructions: str, engine: str = None):
    """
    Stream responses from Subconscious API using SSE.
    
    Based on docs: POST /v1/runs/stream
    
    Args:
        instructions: The full prompt/instructions to send to the API
        engine: The engine to use (defaults to DEFAULT_ENGINE from config)
        
    Yields:
        SSE formatted strings with the streaming response
    """
    if not SUBCONSCIOUS_API_KEY:
        yield "data: " + json.dumps({"error": "API key not configured"}) + "\n\n"
        return
    
    engine = engine or DEFAULT_ENGINE
    
    headers = {
        "Authorization": f"Bearer {SUBCONSCIOUS_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "engine": engine,
        "input": {
            "instructions": instructions
        }
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
                    decoded = line.decode('utf-8')
                    yield f"{decoded}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
