# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv          # ← NEW

# ----------------- load .env first -----------------
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")              # searches .env and populates os.environ
# ---------------------------------------------------

# ----- EDIT ME IF YOU LIKE -----
DECK_NAME = "Russian"
MODEL_NAME = "Russian Basic"
AUDIO_DIR = ROOT / "audio"
VOCAB_FILE = ROOT / "vocab.txt"
OPENAI_MODEL = "gpt-4o-mini"
TTS_MODEL = "tts-1"
TTS_VOICE = "alloy"
MAX_CONCURRENT_REQUESTS = 3
# --------------------------------

AUDIO_DIR.mkdir(exist_ok=True)

# now pulled from the .env that was just loaded
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing – add it to .env or your shell environment."
    )