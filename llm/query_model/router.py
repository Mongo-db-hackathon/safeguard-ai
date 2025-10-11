import os, json, requests
from typing import Literal, Optional, Tuple, Dict, Any

FIREWORKS_API_KEY = os.environ["FIREWORKS_1"]

# small + fast
ROUTER_MODEL = os.getenv(
    "ROUTER_MODEL",
    "accounts/fireworks/models/llama-v3p2-1b-instruct"
)

FIREWORKS_CHAT_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

# schema for strict JSON via function-calling
ROUTER_FUNCTION = {
    "type": "function",
    "function": {
        "name": "route",
        "description": "Classify query intent and extract mm:ss time ranges if any",
        "parameters": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [
                        "FIND_AUDIO",
                        "FIND_FRAME",
                        "FIND_VIDEO_META",
                        "SUMMARIZE_WINDOW",
                        "COUNT"
                    ]
                },
                "time_range": {
                    "type": ["array", "null"],
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2,
                    "description": "Seconds [start, end] if user gave mm:ss; else null"
                }
            },
            "required": ["intent", "time_range"]
        }
    }
}

SYSTEM_PROMPT = (
    "Classify the user question into one of: "
    "FIND_AUDIO, FIND_FRAME, FIND_VIDEO_META, SUMMARIZE_WINDOW, COUNT. "
    "If the question contains time in mm:ss (optionally with 'from mm:ss to mm:ss' "
    "or 'at mm:ss'), convert to seconds and return [start, end]. "
    "If only 'at mm:ss' is given, use a ±5s window. "
    "If no time given, return null for time_range. "
    "Call the function 'route' with the result."
)

def _call_fireworks_router(user_query: str) -> Dict[str, Any]:
    payload = {
        "model": ROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ],
        "tools": [ROUTER_FUNCTION],
        "temperature": 0,
        "max_tokens": 64,
        "top_p": 1,
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json"
    }
    r = requests.post(FIREWORKS_CHAT_URL, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def route_query(user_query: str) -> Dict[str, Any]:
    """
    Returns: {"intent": "...", "time_range": [start_sec, end_sec] | None}
    Includes a regex fallback if tool_call is absent.
    """
    out = _call_fireworks_router(user_query)
    choice = out["choices"][0]

    # function/tool call path (preferred)
    tool_calls = choice["message"].get("tool_calls") or []
    for tc in tool_calls:
        if tc.get("type") == "function" and tc["function"]["name"] == "route":
            args = tc["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            intent = args["intent"]
            time_range = args.get("time_range")
            return {"intent": intent, "time_range": time_range}

    # fallback: quick regex if the model didn't call the function
    import re
    s = user_query.lower()

    def _mmss_to_sec(mm: str, ss: str) -> float:
        return int(mm) * 60 + int(ss)

    t0 = t1 = None
    m = re.search(r"from\s+(\d+):(\d+)\s+to\s+(\d+):(\d+)", s)
    if m:
        t0 = _mmss_to_sec(m.group(1), m.group(2))
        t1 = _mmss_to_sec(m.group(3), m.group(4))
    else:
        m = re.search(r"at\s+(\d+):(\d+)", s)
        if m:
            mid = _mmss_to_sec(m.group(1), m.group(2))
            t0, t1 = mid - 5.0, mid + 5.0

    if any(k in s for k in ["say","said","audio","transcript","spoken","hear"]):
        intent = "FIND_AUDIO"
    elif any(k in s for k in ["frame","image","what does it look","show me frame"]):
        intent = "FIND_FRAME"
    elif any(k in s for k in ["title","camera id","duration","video info","metadata"]):
        intent = "FIND_VIDEO_META"
    elif any(k in s for k in ["how many","count","number of"]):
        intent = "COUNT"
    elif any(k in s for k in ["summary","summarize","recap","between"]):
        intent = "SUMMARIZE_WINDOW"
    else:
        intent = "FIND_AUDIO"

    return {"intent": intent, "time_range": [t0, t1] if (t0 is not None and t1 is not None) else None}


if __name__ == "__main__":
    q = "what did the subject say at 05:10?"
    print(route_query(q))
    # -> {"intent": "FIND_AUDIO", "time_range": [305.0, 315.0]}