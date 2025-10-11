import os, json, requests
from router import route_query as router_model_call

FIREWORKS_1 = "fw_3ZYWGYXM8p1Z4GQTZScCJCXy"
FIREWORKS_API_KEY = "fw_3ZYWGYXM8p1Z4GQTZScCJCXy"
MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"
URL = "https://api.fireworks.ai/inference/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a factual video analysis assistant. "
    "Use ONLY the data retrieved from MongoDB collections "
    "'video_intelligence.video_intelligence' (frames) and "
    "'video_intelligence.video_intelligence_transcripts' (transcripts). "
    "Summarize what happens in that evidence window clearly and concisely. "
    "Include timestamp references like [mm:ss] when possible. "
    "Never invent or assume details outside the data provided. "
    "If there is no meaningful activity, say 'insufficient evidence'. "
    "Return your response STRICTLY as JSON in this format:\n"
    "{\n"
    "  \"summary\": \"<one-paragraph natural-language summary for the user>\",\n"
    "  \"video_name\": \"<video name from MongoDB or 'unknown'>\",\n"
    "  \"citations\": [\"<frame_ids or transcript_ids used>\"]\n"
    "}\n"
    "Do not output anything else."
)

def reasoner_query(q: str):
    # --- Call router model first (small LLM) ---
    router_output = router_model_call(q)
    print("Router output:", router_output)

    # Stub data for now (replace with Mongo fetch)
    video_id = "vid_001"
    video_name = "Training Scenario 1"
    frames_data = [{"id": "frame_01", "t_sec": 310.2, "caption": "Subject raises hands."}]
    transcript_data = [{"id": "utt_02", "t_start": 309.9, "t_end": 311.5, "speaker": "Officer", "text": "Stay still."}]


    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q},
            {
            "role": "user",
            "content": json.dumps({
                "question": q,
                "video_id": video_id,
                "video_name": video_name,
                "intent": router_output.get("intent"),
                "time_range": router_output.get("time_range"),
                "evidence": {
                    "frames": frames_data,         # from Mongo video_intelligence.video_intelligence
                    "transcripts": transcript_data # from Mongo video_intelligence.video_intelligence_transcripts
                }
            }, indent=2)
        }
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
    print(reasoner_query(q))


if __name__ == "__main__":
    q = "what did the subject say at 05:10?"
    print(reasoner_query(q))
    # -> {"intent": "FIND_AUDIO", "time_range": [305.0, 315.0]}