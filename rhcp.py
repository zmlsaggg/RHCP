#!/usr/bin/env python3
"""
RHCP Randomizer — random Red Hot Chili Peppers track + an original rock line.

The catalog contains music metadata only. It does not download or store lyrics.
Run:
    python rhcp.py
    python rhcp.py --update
    python rhcp.py --list
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

APP_NAME = "RHCP Randomizer"
VERSION = "1.0.0"
API = "https://musicbrainz.org/ws/2"
CACHE = Path(__file__).with_name("rhcp_discography.json")
USER_AGENT = f"RHCP-Randomizer/{VERSION} (https://github.com/zmlsaggg/RHCP)"

# Original lines written for this utility; these are not song lyrics.
ORIGINAL_LINES = [
    "Neon hearts keep beating long after the city sleeps.",
    "We left our shadows dancing underneath the overpass.",
    "A little bit of chaos makes the silence feel alive.",
    "The moon was out of tune, so we sang against the night.",
    "Barefoot on the skyline, chasing sparks we couldn't name.",
    "Somewhere between the noise and love, we found our way.",
    "Let the streetlights testify: we were never standing still.",
    "Wildflowers in the concrete, summer running through our veins.",
    "Turn the midnight up until the whole world starts to move.",
    "Every broken compass points to somewhere worth the trip.",
    "The city has a pulse, and tonight it's keeping time.",
    "We are just passing comets with our windows open wide.",
    "Dust on our jackets, electricity in our bones.",
    "If the road forgets our names, the sunrise won't.",
    "No map, no plan — just another beautiful wrong turn.",
]

class MusicBrainzError(RuntimeError):
    pass


def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 503:
            raise MusicBrainzError("MusicBrainz rate limit/server busy. Wait a little and retry --update.") from exc
        raise MusicBrainzError(f"MusicBrainz returned HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise MusicBrainzError(f"Network error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise MusicBrainzError("MusicBrainz returned invalid JSON.") from exc


def fetch_discography() -> list[dict]:
    query = urllib.parse.urlencode({
        "query": 'artist:"Red Hot Chili Peppers"',
        "fmt": "json",
        "limit": 10,
    })
    data = request_json(f"{API}/artist/?{query}")
    artists = data.get("artists", [])
    artist = next((a for a in artists if a.get("name", "").casefold() == "red hot chili peppers"), None)
    if not artist:
        raise MusicBrainzError("Couldn't find Red Hot Chili Peppers in MusicBrainz.")

    artist_id = artist["id"]
    recordings: list[dict] = []
    offset = 0
    total = None

    while total is None or offset < total:
        params = urllib.parse.urlencode({
            "artist": artist_id,
            "fmt": "json",
            "limit": 100,
            "offset": offset,
        })
        page = request_json(f"{API}/recording/?{params}")
        batch = page.get("recordings", [])
        total = page.get("recording-count", len(batch))
        if not batch:
            break

        for item in batch:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            credits = item.get("artist-credit", [])
            artist_names = []
            for credit in credits:
                if isinstance(credit, dict) and isinstance(credit.get("artist"), dict):
                    artist_names.append(credit["artist"].get("name", ""))
            recordings.append({
                "title": title,
                "artist": " / ".join(n for n in artist_names if n) or "Red Hot Chili Peppers",
                "length_ms": item.get("length"),
                "id": item.get("id"),
            })

        offset += len(batch)
        if offset < total:
            time.sleep(1.1)  # MusicBrainz asks clients to stay at or below 1 request/second.

    # De-duplicate identical recording IDs while preserving order.
    unique = {track["id"]: track for track in recordings if track.get("id")}
    return sorted(unique.values(), key=lambda x: x["title"].casefold())


def load_tracks() -> list[dict]:
    if not CACHE.exists():
        print("No local catalog yet — downloading RHCP track metadata…")
        tracks = fetch_discography()
        save_tracks(tracks)
        return tracks
    try:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
        tracks = data.get("tracks", [])
        if not tracks:
            raise ValueError("empty catalog")
        return tracks
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise MusicBrainzError(f"Local catalog is unreadable: {exc}. Run with --update.") from exc


def save_tracks(tracks: list[dict]) -> None:
    payload = {
        "artist": "Red Hot Chili Peppers",
        "source": "MusicBrainz",
        "updated_at": time.strftime("%Y-%m-%d"),
        "tracks": tracks,
    }
    CACHE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def color(text: str, code: str, enabled: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enabled else text


def main() -> int:
    parser = argparse.ArgumentParser(description="A tiny randomizer for the RHCP discography.")
    parser.add_argument("--update", action="store_true", help="refresh the local track catalog")
    parser.add_argument("--list", action="store_true", help="print tracks instead of choosing one")
    parser.add_argument("--no-color", action="store_true", help="disable terminal colors")
    args = parser.parse_args()
    use_color = not args.no_color and sys.stdout.isatty()

    try:
        if args.update:
            print("Refreshing the RHCP catalog from MusicBrainz…")
            tracks = fetch_discography()
            save_tracks(tracks)
            print(f"Saved {len(tracks):,} recordings to {CACHE.name}.")
            return 0

        tracks = load_tracks()
        if args.list:
            for track in tracks:
                print(track["title"])
            print(f"\n{len(tracks):,} recordings")
            return 0

        track = random.choice(tracks)
        line = random.choice(ORIGINAL_LINES)
        print()
        print(color("  R H C P   /   RANDOMIZER", "1;31", use_color))
        print(color("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "31", use_color))
        print()
        print(color("  RANDOM TRACK", "2;33", use_color))
        print(f"  {color(track['title'], '1;37', use_color)}")
        print(f"  {color(track['artist'], '2;37', use_color)}")
        print()
        print(color("  A LITTLE EXTRA", "2;33", use_color))
        print(f"  “{line}”")
        print()
        print(color(f"  {len(tracks):,} recordings in your local catalog", "2;90", use_color))
        print(color("  Data: MusicBrainz  •  Lyrics are not included", "2;90", use_color))
        print()
        return 0
    except (MusicBrainzError, OSError) as exc:
        print(f"\n[RHCP] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
