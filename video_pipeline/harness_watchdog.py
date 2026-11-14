"""
video_pipeline/harness_watchdog.py
Harness² deterministic validation hook for Connections video generation.
Enforces hard structural rules before FFmpeg rendering or YouTube API calls.
"""
import sys

def verify_puzzle_payload(topic_data: dict) -> bool:
    """Deterministic watchdog hook: Replaces LLM self-checking with strict logic."""
    required_keys = ["title", "hook", "categories", "related_url"]
    for key in required_keys:
        if key not in topic_data:
            print(f"[WATCHDOG FAIL] Missing payload key: {key}")
            return False

    categories = topic_data.get("categories", [])
    if len(categories) != 4:
        print(f"[WATCHDOG FAIL] Expected exactly 4 categories, found {len(categories)}")
        return False

    all_words = []
    expected_tiers = {"YELLOW", "GREEN", "BLUE", "PURPLE"}
    found_tiers = set()

    for cat in categories:
        tier = cat.get("tier", "").upper()
        words = [w.strip().upper() for w in cat.get("words", [])]
        found_tiers.add(tier)

        if len(words) != 4:
            print(f"[WATCHDOG FAIL] Tier {tier} has {len(words)} words instead of 4.")
            return False

        all_words.extend(words)

    if found_tiers != expected_tiers:
        print(f"[WATCHDOG FAIL] Tiers do not match required spectrum: {found_tiers}")
        return False

    if len(set(all_words)) != 16:
        print(f"[WATCHDOG FAIL] Grid contains duplicate words! Unique count: {len(set(all_words))}/16")
        return False

    print("[WATCHDOG PASS] Grid structure, unique word counts, and color tiers verified.")
    return True

if __name__ == "__main__":
    test_grid = {
        "title": "The BAT Trap",
        "hook": "Can you spot the overlapping animal traps?",
        "related_url": "https://connectionsassistant.com/nyt-connections-guide.html",
        "categories": [
            {"tier": "YELLOW", "name": "Direct Synonyms", "words": ["LEAP", "JUMP", "BOUND", "SPRING"]},
            {"tier": "GREEN", "name": "Nautical Terms", "words": ["CAPTAIN", "CREW", "SAILOR", "SKIPPER"]},
            {"tier": "BLUE", "name": "Words ending in 'BOARD'", "words": ["KEY", "DASH", "SNOW", "SURF"]},
            {"tier": "PURPLE", "name": "Homophones", "words": ["BEAR", "HARE", "DEAR", "FAIR"]}
        ]
    }
    passed = verify_puzzle_payload(test_grid)
    if not passed:
        sys.exit(1)