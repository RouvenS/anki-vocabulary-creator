import asyncio
import httpx
import logging
from config import DECK_NAME

# ---------- logging ----------
logging.basicConfig(
    format="%(levelname)s:%(name)s:%(message)s", level=logging.INFO
)
log = logging.getLogger("anki-wipe")

async def main():
    http = httpx.AsyncClient(timeout=60.0)
    try:
        log.info(f"Attempting to wipe all cards from deck: '{DECK_NAME}'")

        # --- Pre-wipe check (for target deck) ---
        log.info(f"Checking card count in '{DECK_NAME}' before wipe...")
        pre_wipe_target_payload = {
            "action": "findNotes",
            "version": 6,
            "params": {
                "query": f"deck:'{DECK_NAME}'"
            }
        }
        pre_wipe_target_response = await http.post("http://127.0.0.1:8765", json=pre_wipe_target_payload)
        pre_wipe_target_response.raise_for_status()
        pre_wipe_target_note_ids = pre_wipe_target_response.json().get("result")
        log.info(f"Found {len(pre_wipe_target_note_ids)} cards in deck '{DECK_NAME}' before wipe.")

        # Find all notes in the collection
        find_all_notes_payload = {
            "action": "findNotes",
            "version": 6,
            "params": {
                "query": ""
            }
        }
        log.info("Sending broad findNotes payload to get all notes...")
        all_notes_response = await http.post("http://127.0.0.1:8765", json=find_all_notes_payload)
        all_notes_response.raise_for_status()
        all_note_ids = all_notes_response.json().get("result")
        log.info(f"Found {len(all_note_ids)} total notes in collection.")

        if not all_note_ids:
            log.info("No notes found in your Anki collection. Nothing to wipe.")
            return

        # Get detailed info for all notes and filter by target deck
        notes_to_delete_ids = []
        chunk_size = 1000
        for i in range(0, len(all_note_ids), chunk_size):
            chunk_note_ids = all_note_ids[i:i + chunk_size]
            notes_info_payload = {
                "action": "notesInfo",
                "version": 6,
                "params": {
                    "notes": chunk_note_ids
                }
            }
            notes_info_response = await http.post("http://127.0.0.1:8765", json=notes_info_payload)
            notes_info_response.raise_for_status()
            notes_details = notes_info_response.json().get("result")
            
            for detail in notes_details:
                try:
                    if detail['deckName'] == DECK_NAME:
                        notes_to_delete_ids.append(detail['noteId'])
                except KeyError:
                    log.error(f"Note details missing 'deckName' key: {detail}")
                    continue

        if not notes_to_delete_ids:
            log.info(f"No cards found belonging to deck '{DECK_NAME}' after detailed check. Nothing to wipe.")
            return

        log.info(f"Found {len(notes_to_delete_ids)} notes belonging to deck '{DECK_NAME}'. Deleting...")

        # Delete the identified notes
        delete_notes_payload = {
            "action": "deleteNotes",
            "version": 6,
            "params": {
                "notes": notes_to_delete_ids
            }
        }
        log.info(f"Sending deleteNotes payload for {len(notes_to_delete_ids)} notes.")
        response = await http.post("http://127.0.0.1:8765", json=delete_notes_payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        result = response.json().get("result")

        if result is None:
            log.info(f"Successfully wiped {len(notes_to_delete_ids)} notes from deck '{DECK_NAME}'.")
        else:
            log.error(f"Failed to wipe notes: {response.json().get('error')}")

        # --- Post-wipe check (for target deck) ---
        log.info(f"Checking card count in '{DECK_NAME}' after wipe...")
        post_wipe_target_payload = {
            "action": "findNotes",
            "version": 6,
            "params": {
                "query": f"deck:'{DECK_NAME}'"
            }
        }
        post_wipe_target_response = await http.post("http://127.0.0.1:8765", json=post_wipe_target_payload)
        post_wipe_target_response.raise_for_status()
        post_wipe_target_note_ids = post_wipe_target_response.json().get("result")
        log.info(f"Found {len(post_wipe_target_note_ids)} cards in deck '{DECK_NAME}' after wipe.")

    except httpx.RequestError as e:
        log.error(f"AnkiConnect request failed: {e}")
    except httpx.HTTPStatusError as e:
        log.error(f"AnkiConnect returned an error status: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")
    finally:
        await http.aclose()

if __name__ == "__main__":
    asyncio.run(main())