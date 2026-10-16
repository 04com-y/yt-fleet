import os
import json
import xml.etree.ElementTree as ET
import requests
from typing import Dict, Any

def fetch_live_tech_radar() -> str:
    """Scrapes breaking hardware announcements, upcoming leaks, and silicon news."""
    feeds = [
        "https://www.theverge.com/rss/index.xml",
        "https://techcrunch.com/feed/",
        "https://videocardz.com/feed",
        "https://9to5mac.com/feed/"
    ]
    headlines = []
    headers = {"User-Agent": "Mozilla/5.0"}
    radar_keywords = ["leak", "unveil", "launch", "specs", "benchmark", "reveal", "upcoming", "next-gen", "chip", "gpu", "m4", "rtx"]

    for url in feeds:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:5]:
                    title_elem = item.find("title")
                    if title_elem is not None and title_elem.text:
                        text = title_elem.text.strip()
                        if any(kw in text.lower() for kw in radar_keywords):
                            headlines.insert(0, text)
                        else:
                            headlines.append(text)
        except Exception as e:
            print(f"[scriptwriter] Feed error from {url}: {e}")

    if not headlines:
        headlines = [
            "Next-gen GPU leak reveals 32GB GDDR7 architecture jump",
            "Apple M4 Ultra benchmark tests surface with dual-die packaging",
            "Qualcomm announces Snapdragon X2 extreme efficiency compute node"
        ]
    return "\n- ".join(headlines[:6])

def generate_script(channel_config: dict, language: str = "en") -> dict:
    """Generates a 30s technical breakdown with scene-by-scene image directives and viral SEO."""
    channel_name = channel_config.get("name", "Texh News")
    live_news = fetch_live_tech_radar()
    print(f"[scriptwriter] Live tech headlines gathered:\n{live_news}")

    system_prompt = f"""You are a senior tech journalist writing an authoritative, rapid 30-second YouTube Short for '{channel_name}'.
Pick ONE high-impact breaking story or upcoming hardware leak from these headlines:
{live_news}

CRITICAL RULES:
- Language: {language}
- Total spoken script MUST be strictly between 60 and 70 words (exactly 28-32 seconds of speech).
- NO fluff, NO greetings ("Hey guys"), NO clickbait ("earn money", "make passive income").
- Include at least TWO concrete technical measurements (e.g., nanometers, GHz, GB, watts, or release dates).
- Return STRICT JSON matching this schema:

{{
  "title": "High-CTR title under 50 characters with 1 emoji and #TexhNews",
  "seo_description": "Search-optimized 2-sentence summary followed by 4 hashtags and a pinned discussion question",
  "tags": ["Exact Model", "Brand", "Hardware", "Texh News", "Shorts"],
  "scenes": [
    {{
      "spoken_line": "Opening sentence hook introducing the upcoming device or breakthrough.",
      "image_query": "Exact product name leak render or press photo"
    }},
    {{
      "spoken_line": "Technical specs, architecture details, and compute node breakdown.",
      "image_query": "Silicon die shot or hardware component circuit close up"
    }},
    {{
      "spoken_line": "Cooling redesign, memory bandwidth, or power consumption specs.",
      "image_query": "Device teardown or heatsink vapor chamber hardware"
    }},
    {{
      "spoken_line": "Release timeline, expected MSRP, and call to follow {channel_name} for updates.",
      "image_query": "Brand official event keynote presentation stage"
    }}
  ]
}}"""

    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    content = None

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": system_prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                content = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[scriptwriter] Gemini failed, falling back: {e}")

    if not content and groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": system_prompt}],
                "response_format": {"type": "json_object"}
            }
            res = requests.post(url, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[scriptwriter] Groq failed: {e}")

    try:
        data = json.loads(content)
    except Exception:
        data = {
            "title": "Nvidia Just Leaked the RTX 5090? ⚡ #TexhNews",
            "seo_description": f"Leaked benchmarks reveal the upcoming Nvidia flagship GPU architecture with 32GB GDDR7 memory.\n\nAre you upgrading this year? Drop your thoughts below 👇\n\n#TexhNews #Nvidia #Hardware #Shorts",
            "tags": ["RTX 5090", "Nvidia", "GPU Leak", "Texh News", "Shorts"],
            "scenes": [
                {
                    "spoken_line": "Leaked engineering benchmarks for Nvidia's next-gen flagship GPU just surfaced online.",
                    "image_query": "Nvidia RTX graphics card hardware render"
                },
                {
                    "spoken_line": "Built on a custom three nanometer node, the die features over twenty-four thousand CUDA cores.",
                    "image_query": "silicon microchip wafer die shot macro"
                },
                {
                    "spoken_line": "Early leaks confirm thirty-two gigabytes of GDDR7 memory with a massive dual-slot vapor chamber.",
                    "image_query": "GPU vapor chamber heatsink cooler"
                },
                {
                    "spoken_line": f"Official retail launch is scheduled for early next quarter. Follow {channel_name} for daily hardware updates.",
                    "image_query": "Jensen Huang Nvidia keynote presentation"
                }
            ]
        }

    full_voice = " ".join([s["spoken_line"] for s in data["scenes"]])

    return {
        "title": data["title"],
        "body": full_voice,
        "seo_description": data.get("seo_description", ""),
        "tags": data.get("tags", ["Texh News", "Hardware"]),
        "scenes": data.get("scenes", []),
        "shorts_segments": [
            {
                "title": data["title"],
                "text": full_voice,
                "scenes": data.get("scenes", [])
            }
        ]
    }
