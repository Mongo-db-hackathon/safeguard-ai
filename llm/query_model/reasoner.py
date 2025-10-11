import os, json, requests
from pprint import pprint

from llm.inference import hybrid_search_with_transcripts
from llm.query_model.router import route_query as router_model_call

FIREWORKS_1 = "fw_3ZYWGYXM8p1Z4GQTZScCJCXy"
FIREWORKS_API_KEY = "fw_3ZYWGYXM8p1Z4GQTZScCJCXy"
MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"
URL = "https://api.fireworks.ai/inference/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a factual video analysis assistant. Use ONLY the evidence provided in the user message. "
    "You must do three things:\n"
    "1) Determine which video the evidence belongs to by inspecting evidence fields "
    "(e.g., frames[].video_id, transcripts[].video_id, or any provided candidate_videos). "
    "If multiple videos appear, pick the one with the majority of cited items; if still ambiguous, output 'unknown'.\n"
    "2) Write a concise, factual summary of what happens, grounded ONLY in the provided evidence.\n"
    "3) Derive timestamps ONLY from the evidence you cite. Compute a canonical_time_window as "
    "[start,end] where start = min of cited times (frame.t_sec or transcript.t_start) and "
    "end = max of cited times (frame.t_sec or transcript.t_end). Also return key_timestamps as a sorted "
    "list of unique [mm:ss] strings taken from the cited items. Never invent times.\n"
    "\n"
    "Rules:\n"
    "- Do not use outside knowledge. Do not speculate.\n"
    "- If evidence is insufficient or empty, set summary to 'insufficient evidence' and return "
    "video_id='unknown', video_name='unknown', canonical_time_window=null, key_timestamps=[].\n"
    "- Keep the summary to 1–2 sentences. Include inline [mm:ss] references only if present in the evidence.\n"
    "- Cite the exact item IDs you relied on (frames[].id or transcripts[].id) in the citations array.\n"
    "\n"
    "Return your response STRICTLY as compact JSON with this schema:\n"
    "{\n"
    "  \"summary\": \"<1–2 sentence factual summary>\",\n"
    "  \"video_id\": \"<chosen video_id or 'unknown'>\",\n"
    "  \"video_name\": \"<chosen video_name or 'unknown'>\",\n"
    "  \"canonical_time_window\": [<start_seconds>, <end_seconds>] or null,\n"
    "  \"key_timestamps\": [\"mm:ss\", ...],\n"
    "  \"citations\": [\"<ids used>\"]\n"
    "}\n"
    "Output ONLY JSON. No additional text."
)

def reasoner_query(q: str, data, video_id=None, video_name=None):
    # # --- Call router model first (small LLM) ---
    # router_output = router_model_call(q)
    # print("Router output:", router_output)
    

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
                # "intent": router_output.get("intent"), #router model (small LLM) result (Optional)
                # "time_range": router_output.get("time_range"), #router model (small LLM) result (Optional)
                "evidence": data
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
    q = "Was there a guy in a blue jersey?"


    merged_hybrid_results = hybrid_search_with_transcripts(
        user_query="blue jersey",
        top_n=5,
        vector_weight=0.7,
        text_weight=0.3,
        transcript_weight=0.3,
        search_type="text",
    )

    pprint(merged_hybrid_results)

    print(reasoner_query(q, merged_hybrid_results))

