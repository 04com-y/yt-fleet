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
            print(f"[research] Feed error from {url}: {e}")

    if not headlines:
        headlines = [
            "Nvidia RTX 5090 leak reveals power draw can heat your entire living room",
            "Apple announces new base storage that still insults your bank account",
            "Intel claims new architectural efficiency node will save your electricity bill"
        ]
    return "\n- ".join(headlines[:6])

def generate_script(channel_config: dict, language: str = "en") -> dict:
    """Generates a funny, sarcastic, high-retention 30s tech short."""
    channel_name = channel_config.get("name", "Texh News")
    live_news = fetch_live_tech_radar()
    print(f"[scriptwriter] Live tech headlines gathered:\n{live_news}")

    system_prompt = f"""You are a sarcastic, witty tech journalist writing a funny 30-second YouTube Short for '{channel_name}' (think Fireship meets TechLinked humor).
Roast ONE breaking hardware leak or tech story from these headlines:
{live_news}

TONE & STYLE:
- Fast, punchy, self-aware, and funny. Roast the insane pricing, absurd wattage, or ridiculous product decisions.
- Language: {language}
- Length: STRICTLY 60 to 70 words total (timed for 28-30 seconds).
- NO boring intro, NO "Hey guys", NO generic advice. Jump straight into the joke and the leak.
- Include real specs, but compare them to funny real-world things (e.g. wattage that cooks toast, VRAM you will never fill, pricing requiring a kidney).

Return STRICT JSON matching this exact structure:
{{
  "title": "Funny high-CTR title under 50 characters with 1 emoji and #TexhNews",
  "seo_description": "Hilarious 2-sentence breakdown of why this tech is absurd.\n\nWould you sell your kidney for this? Drop your comments below 👇\n\n#TexhNews #TechRoast #Hardware #Shorts",
  "tags": ["Tech Roast", "Hardware", "Funny Tech", "Texh News", "Shorts"],
  "scenes": [
    {{
      "spoken_line": "Opening joke or sarcastic observation about the new device.",
      "image_query": "gpu graphics card"
    }},
    {{
      "spoken_line": "The ridiculous spec reveal with a funny comparison.",
      "image_query": "computer microchip silicon"
    }},
    {{
      "spoken_line": "Roasting the power draw, thermal meltdown, or price tag.",
      "image_query": "computer cooling heatsink fan"
    }},
    {{
      "spoken_line": "Final punchline urging viewers to subscribe to Texh News before their wallet dies.",
      "image_query": "technology data server motherboard"
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
            "title": "Nvidia Wants Your Entire Bank Account? 💀 #TexhNews",
            "seo_description": "Nvidia's new leak proves GPUs are no longer gaming cards, they are personal home space heaters.\n\nAre you trading your car for this? Comment below 👇\n\n#TexhNews #Nvidia #Hardware #Shorts",
            "tags": ["RTX 5090", "Nvidia", "Hardware Roast", "Texh News", "Shorts"],
            "scenes": [
                {
                    "spoken_line": "Nvidia just looked at your monthly electric bill and decided it was way too low.",
                    "image_query": "graphics card gpu computer"
                },
                {
                    "spoken_line": "Leaked specs show the new flagship draws six hundred watts, officially doubling as a high-end pizza oven.",
                    "image_query": "computer microchip motherboard"
                },
                {
                    "spoken_line": "With thirty-two gigabytes of VRAM, you can finally run Minecraft shaders without setting your carpet on fire.",
                    "image_query": "computer heatsink cooler fan"
                },
                {
                    "spoken_line": f"Expected price? One kidney and your car keys. Subscribe to {channel_name} so you can cry with us daily.",
                    "image_query": "technology hardware computer server"
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
