# src/main.py
import asyncio, base64, json, logging, re
from pathlib import Path
import httpx, openai
from config import *

# ---------- logging ----------
logging.basicConfig(
    format="%(levelname)s:%(name)s:%(message)s", level=logging.INFO
)
log = logging.getLogger("anki-creator")

# ---------- OpenAI clients ----------
oai = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
http = httpx.AsyncClient(timeout=60.0)            # for AnkiConnect

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    PROMPT_HEADER = f.read()

# ---------- helpers ----------
DASH = re.compile(r"\s*[-–—]\s*")    # any kind of dash

def parse_vocab_line(line: str) -> tuple[str, str] | None:
    if not line.strip():
        return None
    rus, eng = DASH.split(line.strip(), maxsplit=1)
    return eng.strip(), rus.strip()        # we want (eng, rus)

async def enrich_worker(in_q: asyncio.Queue, out_q: asyncio.Queue):
    while True:
        eng, rus = await in_q.get()
        try:
            completion = await oai.chat.completions.create(
                model=OPENAI_MODEL,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": PROMPT_HEADER},
                    {"role": "user", "content": f"{rus} – {eng}"},
                ],
            )
            js = json.loads(completion.choices[0].message.content)
            js["eng"] = eng
            js["rus"] = rus
            await out_q.put(js)
            log.info("Enriched: %s", eng)
        except Exception as e:
            log.error("Enrich failed for %s – %s: %s", rus, eng, e)
        finally:
            in_q.task_done()

async def tts_worker(in_q: asyncio.Queue, out_q: asyncio.Queue):
    while True:
        card = await in_q.get()
        try:
            resp = await oai.audio.speech.create(
                model=TTS_MODEL,
                voice=TTS_VOICE,
                input=card["pure_russian"],
                response_format="mp3",
            )
            mp3_bytes = await resp.aread()
            fname = re.sub(r"\W+", "_", card["rus"]) + ".mp3"
            fpath = AUDIO_DIR / fname
            fpath.write_bytes(mp3_bytes)
            card["audio_path"] = fpath
            await out_q.put(card)
            log.info("TTS done: %s", fname)
        except Exception as e:
            log.error("TTS failed for %s: %s", card.get("rus"), e)
        finally:
            in_q.task_done()

def build_anki_note(card: dict) -> dict:
    with card["audio_path"].open("rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return {
        "deckName": DECK_NAME,
        "modelName": MODEL_NAME,
        "fields": {
            "Front": card["front"],
            "Back": card["back"].replace("\n", "<br>"),
        },
        "audio": [{
            "filename": card["audio_path"].name,
            "data": b64,
            "fields": ["Back"]      # play on back
        }],
        "tags": ["auto"],
    }

async def anki_worker(in_q: asyncio.Queue):
    while True:
        card = await in_q.get()
        try:
            note = build_anki_note(card)
            resp = await http.post(
                "http://127.0.0.1:8765",
                json={"action": "addNote", "version": 6, "params": {"note": note}},
            )
            res = resp.json()
            if res.get("error") is None:
                log.info("Anki ✓ %s (note id %s)", card["eng"], res["result"])
            else:
                log.error("Anki error: %s", res["error"])
        except Exception as e:
            log.error("Anki request failed: %s", e)
        finally:
            in_q.task_done()

# ---------- orchestrator ----------
async def main():
    vocab_q   = asyncio.Queue()
    enrich_q  = asyncio.Queue()
    tts_q     = asyncio.Queue()

    # feed vocab
    with open(VOCAB_FILE, encoding="utf-8") as f:
        for line in f:
            pair = parse_vocab_line(line)
            if pair:
                await vocab_q.put(pair)

    # launch workers
    workers = []
    for _ in range(MAX_CONCURRENT_REQUESTS):
        workers.append(asyncio.create_task(enrich_worker(vocab_q, enrich_q)))
        workers.append(asyncio.create_task(tts_worker(enrich_q, tts_q)))
        workers.append(asyncio.create_task(anki_worker(tts_q)))

    # wait until first queue empties → then wait down the chain
    await vocab_q.join()
    await enrich_q.join()
    await tts_q.join()

    for w in workers:
        w.cancel()
    await http.aclose()

if __name__ == "__main__":
    asyncio.run(main())