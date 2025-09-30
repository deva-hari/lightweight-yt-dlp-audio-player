#!/usr/bin/env python3
"""
Lightweight YouTube Audio Player with Search and Streaming
Cross-platform, no temp files, auto-installs deps, debug logging, playlist support.
"""

import argparse
import json
import logging
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

CONFIG_FILE = "config.json"
LOG_FILE = "logs/player.log"
COOKIES_FILE = "cookies.txt"


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
def init_logger(debug: bool):
    Path("logs").mkdir(exist_ok=True)
    level = logging.DEBUG if debug else logging.WARNING
    root_logger = logging.getLogger()
    # Remove all handlers associated with the root logger object
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    logging.debug("Logger initialized. Debug mode: %s", debug)


# ------------------------------------------------------------------
# Dependency manager
# ------------------------------------------------------------------
def is_windows() -> bool:
    return platform.system() == "Windows"


def installed(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run_elevated(cmd: List[str], shell=False):
    """Run command and return True on success."""
    try:
        subprocess.check_call(
            cmd, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def ensure_dependencies():
    logging.debug("Checking dependencies …")
    logging.debug("Checking if ffmpeg is installed …")
    try:
        import yt_dlp as _yt_dlp

        logging.debug("yt_dlp import successful.")
    except ImportError:
        _yt_dlp = None
        logging.debug("yt_dlp not found.")
    need_ffmpeg = not installed("ffmpeg")
    logging.debug("ffmpeg needed: %s", need_ffmpeg)
    need_yt_dlp = _yt_dlp is None
    logging.debug("yt_dlp needed: %s", need_yt_dlp)

    if not need_ffmpeg and not need_yt_dlp:
        logging.debug("All dependencies satisfied.")
        return

    print("Installing missing dependencies …")
    logging.debug("Attempting to install missing dependencies …")
    logging.debug("Platform: %s", platform.system())
    if is_windows():
        if need_ffmpeg and installed("winget"):
            logging.debug("Installing ffmpeg via winget …")
            print("Installing ffmpeg via winget …")
            run_elevated(
                [
                    "winget",
                    "install",
                    "--id=Gyan.FFmpeg",
                    "-e",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ]
            )
        if need_yt_dlp and installed("winget"):
            logging.debug("Installing yt-dlp via winget …")
            print("Installing yt-dlp via winget …")
            run_elevated(
                [
                    "winget",
                    "install",
                    "--id=yt-dlp.yt-dlp",
                    "-e",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ]
            )
    else:  # Linux
        if need_ffmpeg:
            logging.debug("Installing ffmpeg via apt …")
            print("Installing ffmpeg via apt …")
            run_elevated(["sudo", "apt", "update"])
            run_elevated(["sudo", "apt", "install", "ffmpeg", "-y"])
        if need_yt_dlp:
            logging.debug("Installing yt-dlp via pip …")
            print("Installing yt-dlp via pip …")
            run_elevated([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])

    # Re-check
    logging.debug("Re-checking ffmpeg and yt-dlp after attempted install …")
    if not installed("ffmpeg"):
        logging.error("ffmpeg still missing after attempted install.")
        sys.exit("ffmpeg still missing – please install manually.")
    try:
        import yt_dlp as _yt_dlp

        logging.debug("yt_dlp import successful after install.")
    except ImportError:
        logging.error("yt-dlp still missing after attempted install.")
        sys.exit("yt-dlp still missing – please install manually.")
    global yt_dlp
    yt_dlp = _yt_dlp


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
def load_config() -> dict:
    defaults = {"SearchLimit": 10, "Debug": False, "CookiesFile": COOKIES_FILE}
    logging.debug("Loading config from %s", CONFIG_FILE)
    if Path(CONFIG_FILE).exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                loaded = json.load(f)
                logging.debug("Loaded config: %s", loaded)
                defaults.update(loaded)
        except Exception as e:
            logging.warning("Could not load config.json – %s", e)
    else:
        logging.debug("Config file not found, using defaults.")
    return defaults


# ------------------------------------------------------------------
# yt-dlp helpers
# ------------------------------------------------------------------
def ydl_opts(cfg: dict, audio_only=True) -> dict:
    logging.debug("Building yt-dlp options. audio_only=%s", audio_only)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "format": "bestaudio/best",
    }
    if audio_only:
        opts["format"] = "bestaudio/best"
    cookies = cfg.get("CookiesFile", COOKIES_FILE)
    if Path(cookies).exists():
        opts["cookiefile"] = cookies
        logging.debug("Using cookies file: %s", cookies)
    else:
        logging.debug("Cookies file not found, using defaults.")
    logging.debug("yt-dlp options: %s", opts)
    return opts


def search_yt(query: str, limit: int) -> List[dict]:
    cfg = load_config()
    logging.debug("search_yt called with query='%s', limit=%d", query, limit)
    opts = {**ydl_opts(cfg), "default_search": f"ytsearch{limit}"}
    logging.debug("yt-dlp search options: %s", opts)
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            logging.debug("yt-dlp search result: %s", info)
        except Exception as e:
            logging.error("Search failed – %s", e)
            return []
    entries = info.get("entries") or []
    logging.debug("Found %d entries", len(entries))
    return entries


def extract_stream_url(video_url: str) -> Optional[str]:
    cfg = load_config()
    logging.debug("extract_stream_url called for: %s", video_url)
    with yt_dlp.YoutubeDL(ydl_opts(cfg)) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            logging.debug("yt-dlp extract_info result: %s", info)
            return info["url"]
        except Exception as e:
            logging.error("Could not extract URL – %s", e)
            return None


# ------------------------------------------------------------------
# Playback
# ------------------------------------------------------------------
def play_stream(url: str, silent=True) -> subprocess.Popen:
    """
    Pipe yt-dlp output directly to ffplay, matching the command-line example.
    url: can be a search string, video URL, or playlist URL.
    """
    logging.debug("play_stream (pipe) called with url=%s, silent=%s", url, silent)
    ytdlp_cmd = [
        "yt-dlp",
        "-f",
        "bestaudio",
        "-o",
        "-",
        url,
    ]
    cfg = load_config()
    cookies = cfg.get("CookiesFile", COOKIES_FILE)
    if Path(cookies).exists():
        ytdlp_cmd += ["--cookies", cookies]
    ffplay_cmd = [
        "ffplay",
        "-i",
        "-",
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "info" if not silent else "quiet",
    ]
    logging.debug("yt-dlp cmd: %s", " ".join(ytdlp_cmd))
    logging.debug("ffplay cmd: %s", " ".join(ffplay_cmd))
    try:
        ytdlp_proc = subprocess.Popen(
            ytdlp_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        ffplay_proc = subprocess.Popen(
            ffplay_cmd, stdin=ytdlp_proc.stdout, stdout=subprocess.DEVNULL, stderr=None
        )
        logging.debug("yt-dlp pid=%s, ffplay pid=%s", ytdlp_proc.pid, ffplay_proc.pid)
        return ffplay_proc
    except Exception as e:
        logging.error("Failed to start yt-dlp|ffplay pipeline: %s", e)
        return None


def interactive_play(entries: List[dict], cfg: dict):
    logging.debug("interactive_play called with %d entries", len(entries))
    idx = 0
    retry = 3
    while 0 <= idx < len(entries):
        logging.debug("Playlist index: %d", idx)
        e = entries[idx]
        title = e.get("title") or "Unknown"
        webpage_url = e.get("webpage_url") or e.get("url")
        logging.debug("Now playing entry: %s, url: %s", title, webpage_url)
        print(f"\nNow playing: [{idx+1}/{len(entries)}] {title}")
        retry_count = 0
        while retry_count < 3:
            player = play_stream(webpage_url, silent=not cfg.get("Debug", False))
            if player is None:
                print("  Failed to start player.")
                idx += 1
                break
            print("  Controls: [n]ext, [r]eplay, [q]uit")
            logging.debug("Player started for entry: %s", title)
            user_action = None
            try:
                while player.poll() is None:
                    if platform.system() == "Windows":
                        import msvcrt

                        if msvcrt.kbhit():
                            ch = msvcrt.getch().decode().lower()
                            logging.debug("User pressed key: %s", ch)
                            if ch == "n":
                                logging.debug("User requested next track.")
                                player.terminate()
                                user_action = "next"
                                break
                            elif ch == "r":
                                logging.debug("User requested replay.")
                                player.terminate()
                                user_action = "replay"
                                break
                            elif ch == "q":
                                logging.debug("User requested quit.")
                                player.terminate()
                                return
                    else:
                        import select

                        if select.select([sys.stdin], [], [], 0)[0]:
                            ch = sys.stdin.read(1).lower()
                            logging.debug("User pressed key: %s", ch)
                            if ch == "n":
                                logging.debug("User requested next track.")
                                player.terminate()
                                user_action = "next"
                                break
                            elif ch == "r":
                                logging.debug("User requested replay.")
                                player.terminate()
                                user_action = "replay"
                                break
                            elif ch == "q":
                                logging.debug("User requested quit.")
                                player.terminate()
                                return
                    time.sleep(0.2)
            except KeyboardInterrupt:
                logging.debug("KeyboardInterrupt: terminating player.")
                player.terminate()
                return
            exit_code = player.wait()
            logging.debug("ffplay exited with code: %s", exit_code)
            # If abnormal exit, retry up to 2 more times
            if exit_code != 0 and user_action is None:
                retry_count += 1
                print(
                    f"  ffplay exited abnormally (code {exit_code}), retrying ({retry_count}/3)..."
                )
                logging.warning(
                    "ffplay exited abnormally (code %s), retrying (%d/3)...",
                    exit_code,
                    retry_count,
                )
                continue
            # If user requested replay, loop again
            if user_action == "replay":
                retry_count = 0
                continue
            # If user requested next, advance
            if user_action == "next":
                idx += 1
                break
            # If track ended naturally, prompt user for 3 seconds
            print("Track ended. [n]ext, [r]eplay, [q]uit? (auto-next in 3s)")
            logging.debug("Track ended, waiting for user action (3s timeout).")
            import threading

            user_input = {"ch": None}

            def get_input():
                user_input["ch"] = input().strip().lower()

            t = threading.Thread(target=get_input)
            t.daemon = True
            t.start()
            t.join(3)
            ch = user_input["ch"]
            if ch is None:
                print("No input, auto-advancing to next track.")
                idx += 1
                break
            if ch == "n":
                idx += 1
                break
            elif ch == "r":
                retry_count = 0
                continue
            elif ch == "q":
                return
            else:
                print("Invalid input. [n]ext, [r]eplay, [q]uit?")
                # fallback: auto-advance
                idx += 1
                break
    print("End of playlist.")


# ------------------------------------------------------------------
# Input handler
# ------------------------------------------------------------------
def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")


def is_playlist(url: str) -> bool:
    return "playlist" in url or "list=" in url


def handle_input(raw: str, cfg: dict):
    logging.debug("handle_input called with raw='%s'", raw)
    raw = raw.strip()
    if not raw:
        return
    if is_url(raw):
        logging.debug("Input detected as URL.")
        if is_playlist(raw):
            logging.debug("URL detected as playlist.")
            print("Playlist URL detected – fetching all entries …")
            entries = playlist_to_entries(raw)
            if entries:
                logging.debug("Playlist has %d entries.", len(entries))
                # Use current debug setting for playlist playback
                interactive_play(entries, cfg)
            else:
                logging.debug("Playlist empty or unavailable.")
                print("Empty or unavailable playlist.")
        else:
            logging.debug("URL detected as single video.")
            # single video: stream directly using yt-dlp | ffplay pipe
            print("Now playing: [1/1] (single video)")
            while True:
                player = play_stream(raw, silent=not cfg.get("Debug", False))
                print("  Controls: [r]eplay, [q]uit")
                if player is None:
                    print("  Failed to start player.")
                    return
                user_action = None
                try:
                    while player.poll() is None:
                        if platform.system() == "Windows":
                            import msvcrt

                            if msvcrt.kbhit():
                                ch = msvcrt.getch().decode().lower()
                                logging.debug("User pressed key: %s", ch)
                                if ch == "r":
                                    logging.debug("User requested replay.")
                                    player.terminate()
                                    user_action = "replay"
                                    break
                                elif ch == "q":
                                    logging.debug("User requested quit.")
                                    player.terminate()
                                    return
                        else:
                            import select

                            if select.select([sys.stdin], [], [], 0)[0]:
                                ch = sys.stdin.read(1).lower()
                                logging.debug("User pressed key: %s", ch)
                                if ch == "r":
                                    logging.debug("User requested replay.")
                                    player.terminate()
                                    user_action = "replay"
                                    break
                                elif ch == "q":
                                    logging.debug("User requested quit.")
                                    player.terminate()
                                    return
                        time.sleep(0.2)
                except KeyboardInterrupt:
                    logging.debug("KeyboardInterrupt: terminating player.")
                    player.terminate()
                    return
                # If user requested replay, loop again
                if user_action == "replay":
                    continue
                # If track ended naturally, prompt user
                print("Track ended. [r]eplay, [q]uit?")
                logging.debug("Track ended, waiting for user action.")
                while True:
                    ch = input().strip().lower()
                    if ch == "r":
                        break
                    elif ch == "q":
                        return
                    else:
                        print("Invalid input. [r]eplay, [q]uit?")
                if ch == "r":
                    continue
                else:
                    break
    else:
        logging.debug("Input detected as search query.")
        # treat as search
        limit = cfg.get("SearchLimit", 10)
        logging.debug("Search limit: %d", limit)
        results = search_yt(raw, limit)
        if not results:
            logging.debug("No search results for query: %s", raw)
            print("No results.")
            return
        print("\nSearch results:")
        for i, v in enumerate(results, 1):
            title = v.get("title") or "Unknown"
            channel = v.get("channel") or v.get("uploader") or "Unknown"
            duration = v.get("duration_string") or "?"
            logging.debug("Result %d: %s | %s | %s", i, title, channel, duration)
            print(f"[{i}] {title} | {channel} | {duration}")
        try:
            chosen = input(
                "\nSelect by number (space for multiple), or 0 to cancel: "
            ).strip()
            logging.debug("User selection: %s", chosen)
            if chosen == "0":
                return
            indices = [int(x) - 1 for x in chosen.split()]
            selected = [results[i] for i in indices if 0 <= i < len(results)]
            logging.debug("Selected indices: %s", indices)
            if selected:
                logging.debug("Selected entries: %s", selected)
                interactive_play(selected, cfg)
        except (ValueError, IndexError):
            logging.debug("Invalid selection input.")
            print("Invalid selection.")


def playlist_to_entries(playlist_url: str) -> List[dict]:
    cfg = load_config()
    logging.debug("playlist_to_entries called for: %s", playlist_url)
    with yt_dlp.YoutubeDL({**ydl_opts(cfg), "extract_flat": "in_playlist"}) as ydl:
        try:
            info = ydl.extract_info(playlist_url, download=False)
            logging.debug("Playlist extract_info result: %s", info)
            return info.get("entries") or []
        except Exception as e:
            logging.error("Playlist fetch failed – %s", e)
            return []


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Lightweight YouTube audio player")
    parser.add_argument(
        "input", nargs="?", help="Search query, video URL, or playlist URL"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.debug("main() called")
    cfg = load_config()
    if args.debug:
        cfg["Debug"] = True
    logging.debug("Debug mode: %s", cfg["Debug"])
    init_logger(cfg["Debug"])

    ensure_dependencies()

    if args.input:
        logging.debug("Input argument provided: %s", args.input)
        handle_input(args.input, cfg)
    else:
        # interactive session
        logging.debug("Entering interactive session loop.")
        while True:
            try:
                raw = input("\nYouTube> ").strip()
                logging.debug("User input: %s", raw)
            except (EOFError, KeyboardInterrupt):
                logging.debug("Session ended by user.")
                print("\nBye.")
                break
            if raw.lower() in {"exit", "quit", "q"}:
                logging.debug("User requested exit.")
                break
            handle_input(raw, cfg)


if __name__ == "__main__":
    try:
        import shutil
    except ImportError:
        import shutil
    main()
