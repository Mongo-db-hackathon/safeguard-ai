import os, json, requests
FIREWORKS_1 = "fw_3ZYWGYXM8p1Z4GQTZScCJCXy"
FIREWORKS_API_KEY = "fw_3ZYWGYXM8p1Z4GQTZScCJCXy"
MODEL = "accounts/fireworks/models/deepseek-v3p1-terminus"
URL = "https://api.fireworks.ai/inference/v1/chat/completions"

SYSTEM_PROMPT = (
    "Classify the user question into one of: "
    "FIND_AUDIO, FIND_FRAME, FIND_VIDEO_META, SUMMARIZE_WINDOW, COUNT. "
    "If the question includes time like 'at 05:10' or 'from 05:10 to 06:00', "
    "convert to seconds and output [start, end]. "
    "If only 'at' is given, use ±5 seconds. "
    "If no time given, return null for time_range. "
    "Respond ONLY as JSON: "
    "{\"intent\": <intent>, \"time_range\": [start, end] or null}"
)

def route_query(q: str):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q}
        ],
        "temperature": 0,
        "max_tokens": 80,
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(URL, headers=headers, json=payload, timeout=20)
    r.raise_for_status()
    msg = r.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(msg)
    except Exception:
        return {"raw": msg}

# Example
if __name__ == "__main__":
    q = "what did the subject say at 05:10?"
    print(route_query(q))


if __name__ == "__main__":
    q = "what did the subject say at 05:10?"
    print(route_query(q))
    # -> {"intent": "FIND_AUDIO", "time_range": [305.0, 315.0]}