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
import urllib.request
import shutil
import random
import signal


def _is_version_greater(v_new: str, v_old: str) -> bool:
    """Return True if v_new > v_old. Prefer packaging when available, fallback to simple token compare."""
    try:
        from packaging.version import Version

        return Version(v_new) > Version(v_old)
    except Exception:
        # fallback: split on non-alphanum and compare token-wise
        def to_tokens(s: str):
            parts = re.split(r"[\.\-]", s)
            toks = []
            for p in parts:
                if p.isdigit():
                    toks.append(int(p))
                else:
                    toks.append(p)
            return toks

        return to_tokens(v_new) > to_tokens(v_old)


try:
    import yt_dlp
except ImportError:
    yt_dlp = None

CONFIG_FILE = "config.json"
LOG_FILE = "logs/player.log"
COOKIES_FILE = "cookies.txt"
HISTORY_FILE = "logs/history.json"
HISTORY_INDEX_FILE = "logs/history_index.json"


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
def init_logger(debug: bool):
    Path("logs").mkdir(exist_ok=True)
    # Always allow DEBUG events at the logger level; handlers will filter
    root_logger = logging.getLogger()
    # Remove all handlers associated with the root logger object
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    # Keep most verbose logging available internally; handlers decide what
    # to show. Console should show INFO by default, DEBUG when debug=True.
    root_logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    stream_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    logging.debug("Logger initialized. Debug mode: %s", debug)
    logging.info(
        "Logger configured. Console level=%s, File level=%s",
        logging.getLevelName(stream_handler.level),
        logging.getLevelName(file_handler.level),
    )


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


def ensure_dependencies(check_mpv=False):
    logging.debug("Checking dependencies …")
    try:
        import yt_dlp as _yt_dlp

        logging.debug("yt_dlp import successful.")
    except ImportError:
        _yt_dlp = None
        logging.debug("yt_dlp not found.")

    need_ffmpeg = not installed("ffmpeg")
    need_yt_dlp = _yt_dlp is None
    need_mpv = check_mpv and not installed("mpv")

    logging.debug("ffmpeg needed: %s", need_ffmpeg)
    logging.debug("yt_dlp needed: %s", need_yt_dlp)
    logging.debug("mpv needed: %s", need_mpv)

    if not any([need_ffmpeg, need_yt_dlp, need_mpv]):
        logging.debug("All dependencies satisfied.")
        return True

    print("Installing missing dependencies …")
    logging.info("Installing missing dependencies …")
    logging.debug("Platform: %s", platform.system())

    if is_windows():
        if installed("winget"):
            if need_ffmpeg:
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
            if need_yt_dlp:
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
            if need_mpv:
                logging.debug("Installing mpv via winget …")
                print("Installing mpv via winget …")
                run_elevated(
                    [
                        "winget",
                        "install",
                        "--id=mpv.mpv",
                        "-e",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                    ]
                )
    else:  # Linux
        if need_ffmpeg or need_mpv:
            logging.debug("Installing ffmpeg/mpv via apt …")
            print("Installing ffmpeg/mpv via apt …")
            run_elevated(["sudo", "apt", "update"])
            pkgs = []
            if need_ffmpeg:
                pkgs.append("ffmpeg")
            if need_mpv:
                pkgs.append("mpv")
            if pkgs:
                run_elevated(["sudo", "apt", "install"] + pkgs + ["-y"])

        if need_yt_dlp:
            logging.debug("Installing yt-dlp via pip …")
            print("Installing yt-dlp via pip …")
            run_elevated([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])

    # Re-check
    logging.debug("Re-checking dependencies after attempted install …")
    if need_ffmpeg and not installed("ffmpeg"):
        logging.error("ffmpeg still missing after attempted install.")
        sys.exit("ffmpeg still missing – please install manually.")
    if need_mpv and not installed("mpv"):
        logging.error("mpv still missing after attempted install.")
        if check_mpv:  # Only exit if mpv was actually required
            sys.exit("mpv still missing – please install manually.")
        return False

    try:
        import yt_dlp as _yt_dlp

        logging.debug("yt_dlp import successful after install.")
    except ImportError:
        logging.error("yt-dlp still missing after attempted install.")
        sys.exit("yt-dlp still missing – please install manually.")

    global yt_dlp
    yt_dlp = _yt_dlp
    return True


# ------------------------------------------------------------------
# yt-dlp update helpers
# ------------------------------------------------------------------
def _get_installed_yt_dlp_version() -> Optional[str]:
    try:
        import yt_dlp as _yt

        return getattr(_yt, "__version__", None)
    except Exception:
        return None


def _get_latest_yt_dlp_version_pypi(timeout: float = 5.0) -> Optional[str]:
    url = "https://pypi.org/pypi/yt-dlp/json"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.load(resp)
            return data.get("info", {}).get("version")
    except Exception as e:
        logging.debug("Could not fetch latest yt-dlp version from PyPI: %s", e)
        return None


def _detect_install_method() -> str:
    """Try to guess how yt-dlp was installed: 'pip', 'winget', 'pipx', 'self' (binary), or 'unknown'."""
    exe = shutil.which("yt-dlp")
    try:
        import yt_dlp as _yt

        module_file = getattr(_yt, "__file__", "") or ""
    except Exception:
        module_file = ""
    if module_file and "site-packages" in module_file:
        return "pip"
    if exe:
        low = exe.lower()
        if "program files" in low or "windowsapps" in low:
            return "winget"
        if "pipx" in low:
            return "pipx"
        # default to 'self' if binary appears on PATH
        return "self"
    return "unknown"


def _suggest_update_commands(method: str) -> List[str]:
    cmds = []
    # safe generic suggestions
    cmds.append(
        "yt-dlp -U  # yt-dlp's built-in self-update (may work for exe installs)"
    )
    cmds.append(f"{sys.executable} -m pip install -U yt-dlp  # pip upgrade")
    cmds.append("pipx upgrade yt-dlp  # if installed via pipx")
    cmds.append("winget upgrade --id yt-dlp.yt-dlp -e  # on Windows with winget")
    # prioritize method-specific
    if method == "pip":
        return [f"{sys.executable} -m pip install -U yt-dlp"]
    if method == "pipx":
        return ["pipx upgrade yt-dlp"]
    if method == "winget":
        return ["winget upgrade --id yt-dlp.yt-dlp -e"]
    if method == "self":
        return ["yt-dlp -U"]
    return cmds


def _attempt_runtime_update(method: str) -> bool:
    """Attempt to update yt-dlp using the detected method. Returns True on success."""
    try:
        if method == "pip":
            cmd = [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"]
            logging.info("Attempting to update yt-dlp via pip: %s", " ".join(cmd))
            subprocess.check_call(cmd)
            return True
        if method == "self":
            cmd = [shutil.which("yt-dlp") or "yt-dlp", "-U"]
            logging.info("Attempting to self-update yt-dlp: %s", " ".join(cmd))
            subprocess.check_call(cmd)
            return True
        if method == "winget":
            cmd = ["winget", "upgrade", "--id", "yt-dlp.yt-dlp", "-e"]
            logging.info("Attempting to update yt-dlp via winget: %s", " ".join(cmd))
            subprocess.check_call(cmd)
            return True
        if method == "pipx":
            cmd = ["pipx", "upgrade", "yt-dlp"]
            logging.info("Attempting to update yt-dlp via pipx: %s", " ".join(cmd))
            subprocess.check_call(cmd)
            return True
    except Exception as e:
        logging.warning("Runtime update attempt failed: %s", e)
        return False
    return False


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
def load_config() -> dict:
    defaults = {
        "SearchLimit": 10,
        "Debug": False,
        "CookiesFile": COOKIES_FILE,
        "PlaybackMethod": "pipe",
        "CacheDir": "cache",
        "CacheMaxFiles": 50,
        "CacheRetryCount": 3,
        "CacheRetryBaseDelay": 1.0,
        "CacheRetryOnNetworkOnly": True,
        "CacheDownloadTimeout": 30,
        "ForceCacheRefresh": False,
    }
    logging.debug("Loading config from %s", CONFIG_FILE)
    if Path(CONFIG_FILE).exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                loaded = json.load(f)
                logging.debug("Loaded config: %s", loaded)
                # Coerce loaded values to match types in defaults
                for k, v in loaded.items():
                    if k in defaults:
                        default_val = defaults[k]
                        # handle booleans represented as strings
                        if isinstance(default_val, bool) and isinstance(v, str):
                            lv = v.strip().lower()
                            if lv in ("true", "1", "yes", "y"):
                                defaults[k] = True
                            elif lv in ("false", "0", "no", "n"):
                                defaults[k] = False
                            else:
                                # fall back to python truthiness
                                defaults[k] = bool(v)
                        # handle numeric coercion
                        elif isinstance(default_val, int) and not isinstance(v, bool):
                            try:
                                defaults[k] = int(v)
                            except Exception:
                                defaults[k] = v
                        elif isinstance(default_val, float) and not isinstance(v, bool):
                            try:
                                defaults[k] = float(v)
                            except Exception:
                                defaults[k] = v
                        else:
                            defaults[k] = v
                    else:
                        # unknown keys, keep as-is
                        defaults[k] = v
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
        "format": "bestaudio/best" if audio_only else "best",
    }
    cookies = cfg.get("CookiesFile", COOKIES_FILE)
    if Path(cookies).exists():
        opts["cookiefile"] = cookies
        logging.debug("Using cookies file: %s", cookies)
    else:
        logging.debug("Cookies file not found, using defaults.")
    logging.debug("yt-dlp options: %s", opts)
    return opts


# ------------------------------------------------------------------
# History (simple JSON log)
# ------------------------------------------------------------------
def init_history():
    Path("logs").mkdir(exist_ok=True)
    if not Path(HISTORY_FILE).exists():
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    # ensure index file exists
    if not Path(HISTORY_INDEX_FILE).exists():
        with open(HISTORY_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def load_history() -> List[dict]:
    init_history()
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _load_index() -> dict:
    init_history()
    try:
        with open(HISTORY_INDEX_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_index(idx: dict):
    try:
        with open(HISTORY_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.debug("Could not write history index: %s", e)


def append_history(entry: dict):
    # update persistent play count index and attach play_count to entry
    idx = _load_index()
    key = entry.get("track_url") or entry.get("playlist_url") or ""
    count = idx.get(key, 0) + 1
    idx[key] = count
    entry["play_count"] = count
    _save_index(idx)

    h = load_history()
    h.append(entry)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(h, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.debug("Could not write history: %s", e)


def _format_date(ts: Optional[int]) -> str:
    if not ts:
        return "-"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    except Exception:
        return str(ts)


def show_history_paged(page_size: int = 10):
    h = load_history()
    if not h:
        print("No history entries.")
        logging.info("History empty")
        return
    # use persistent play_count if present

    def _truncate(s: str, w: int) -> str:
        s = s or ""
        if len(s) <= w:
            return s
        return s[: w - 1] + "…"

    filtered = h
    total_pages = (len(filtered) + page_size - 1) // page_size if filtered else 1
    page = 0
    # active filters
    active_type = None
    active_search = None
    while True:
        start = page * page_size
        end = start + page_size
        # re-evaluate filtered list
        filtered = h
        if active_type:
            filtered = [x for x in filtered if (x.get("type") or "") == active_type]
        if active_search:
            filtered = [
                x
                for x in filtered
                if active_search.lower() in (x.get("title") or "").lower()
            ]
        total_pages = (len(filtered) + page_size - 1) // page_size if filtered else 1
        start = page * page_size
        end = start + page_size
        slice_ = filtered[start:end]
        print(
            f"History — page {page+1}/{total_pages} (entries {start+1}-{min(end,len(filtered))} of {len(filtered)})"
        )
        print(
            "Idx Type         Date                    Title                               URL                                      Plays"
        )
        print(
            "--- -------------- -------------------- ------------------------------------ ---------------------------------------- -----"
        )
        for i, item in enumerate(slice_):
            idx = i % 10  # 0-9 per page
            t = (item.get("type") or "?")[:14]
            date = _format_date(item.get("timestamp"))
            title = _truncate(item.get("title") or "", 36)
            url = _truncate(item.get("track_url") or item.get("playlist_url") or "", 40)
            plays = item.get("play_count") or 1
            print(f"[{idx}] {t:14} {date:20} {title:36} {url:40} {plays:5}")
        print(
            "\nCommands: n=next, p=prev, q=quit, v<num>=view raw (v3), f type=<single|playlist|playlist_entry|...>, s <term>=search title, export [csv|json], clear, help"
        )
        cmd = input("history> ").strip().lower()
        if cmd == "n":
            if page + 1 < total_pages:
                page += 1
            else:
                print("Already last page.")
        elif cmd == "p":
            if page > 0:
                page -= 1
            else:
                print("Already first page.")
        elif cmd == "q":
            break
        elif cmd.startswith("v"):
            try:
                n = int(cmd[1:])
                if 0 <= n < len(slice_):
                    print(json.dumps(slice_[n], ensure_ascii=False, indent=2))
                else:
                    print("Invalid index on page.")
            except Exception:
                print("Invalid v command. Use v0..v9")
        elif cmd.startswith("f"):
            # filter by type, syntax: f type=single
            parts = cmd.split()
            if len(parts) >= 2 and "=" in parts[1]:
                k, v = parts[1].split("=", 1)
                if k == "type":
                    active_type = v
                    page = 0
                else:
                    print("Unknown filter key.")
            else:
                print("Filter syntax: f type=single")
        elif cmd.startswith("s "):
            # search by title
            term = cmd[2:].strip()
            if term:
                active_search = term
                page = 0
            else:
                active_search = None
                print("Search cleared.")
        elif cmd.startswith("export"):
            parts = cmd.split()
            fmt = "csv" if len(parts) == 1 else parts[1]
            try:
                if fmt == "csv":
                    _export_history_csv(filtered)
                else:
                    _export_history_json(filtered)
                print(f"Exported history as {fmt}.")
            except Exception as e:
                print("Export failed:", e)
        elif cmd == "clear":
            confirm = input("Clear all history? Type YES to confirm: ")
            if confirm == "YES":
                try:
                    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                        json.dump([], f)
                    _save_index({})
                    h = []
                    filtered = []
                    page = 0
                    print("History cleared.")
                except Exception as e:
                    print("Failed to clear:", e)
            else:
                print("Clear cancelled.")
        elif cmd == "help":
            print(
                "Commands: n, p, q, v<num>, f type=<type>, s <term>, export [csv|json], clear, help"
            )
        else:
            print("Unknown command.")


def _export_history_json(items: List[dict], path: str = "logs/history_export.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _export_history_csv(items: List[dict], path: str = "logs/history_export.csv"):
    import csv

    keys = ["timestamp", "type", "title", "track_url", "playlist_url", "play_count"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for it in items:
            row = {k: it.get(k) for k in keys}
            w.writerow(row)


# ------------------------------------------------------------------
# Metadata helpers
# ------------------------------------------------------------------
def get_video_info(url: str) -> Optional[dict]:
    cfg = load_config()
    try:
        with yt_dlp.YoutubeDL({**ydl_opts(cfg)}) as ydl:
            info = ydl.extract_info(url, download=False)
            logging.debug("get_video_info: %s", info)
            return info
    except Exception as e:
        logging.debug("get_video_info failed: %s", e)
        return None


# ------------------------------------------------------------------
# Cache helpers
# ------------------------------------------------------------------
def ensure_cache_dir(cfg: dict) -> Path:
    cache_dir = Path(cfg.get("CacheDir", "cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _url_to_filename(url: str) -> str:
    # produce a short safe filename for a URL
    import hashlib

    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return h + ".webm"


def get_cached_file_for_url(url: str, cfg: dict) -> Optional[Path]:
    cache_dir = ensure_cache_dir(cfg)
    fname = _url_to_filename(url)
    p = cache_dir / fname
    if p.exists():
        return p
    return None


def prune_cache(cfg: dict):
    cache_dir = ensure_cache_dir(cfg)
    max_files = int(cfg.get("CacheMaxFiles", 50))
    files = sorted(cache_dir.iterdir(), key=lambda p: p.stat().st_atime)
    while len(files) > max_files:
        try:
            files[0].unlink()
            files.pop(0)
        except Exception:
            break


def download_to_cache(url: str, cfg: dict, video_mode: bool = False) -> Optional[Path]:
    # If already cached, return path
    existing = get_cached_file_for_url(url, cfg)
    force = bool(cfg.get("ForceCacheRefresh", False))
    if existing and not force:
        logging.debug("Cache hit for %s -> %s", url, existing)
        logging.info(
            "Using cached %s for %s -> %s",
            "video" if video_mode else "track",
            url,
            existing,
        )
        return existing
    if existing and force:
        logging.debug(
            "ForceCacheRefresh enabled, removing existing cache file: %s", existing
        )
        try:
            existing.unlink()
        except Exception as e:
            logging.debug("Failed to remove cached file %s: %s", existing, e)
    cache_dir = ensure_cache_dir(cfg)
    fname = _url_to_filename(url)
    out_path = cache_dir / fname
    # build yt-dlp options for downloading: ensure skip_download is False
    ydl_opts_local = {**ydl_opts(cfg, audio_only=not video_mode)}
    ydl_opts_local.pop("skip_download", None)
    # let yt-dlp choose extension; use template with %(ext)s
    stem = out_path.stem
    out_template = str(cache_dir / (stem + ".%(ext)s"))
    ydl_opts_local.update(
        {"outtmpl": out_template, "format": "best" if video_mode else "bestaudio/best"}
    )
    # Use yt_dlp to download directly to the cache path
    # Retry loop with exponential backoff and jitter
    max_retries = int(cfg.get("CacheRetryCount", 3))
    base_delay = float(cfg.get("CacheRetryBaseDelay", 1.0))
    attempt = 0
    real_path = None
    while attempt <= max_retries:
        try:
            with yt_dlp.YoutubeDL(ydl_opts_local) as ydl:
                logging.debug(
                    "Downloading %s to cache as template %s (attempt %d)",
                    url,
                    out_template,
                    attempt + 1,
                )
                ydl.download([url])
            matches = list(cache_dir.glob(stem + ".*"))
            if matches:
                matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                real_path = matches[0]
            prune_cache(cfg)
            if real_path and real_path.exists():
                logging.info("Downloaded and cached %s -> %s", url, real_path)
                return real_path
            # if no file found, fallthrough to retry
        except Exception as e:
            logging.debug("download_to_cache attempt %d failed: %s", attempt + 1, e)
        # backoff
        attempt += 1
        if attempt > max_retries:
            break
        import random

        delay = base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0, delay * 0.2)
        wait = delay + jitter
        logging.debug(
            "Retrying download in %.2fs (attempt %d/%d)",
            wait,
            attempt + 1,
            max_retries + 1,
        )
        time.sleep(wait)
    return None


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
def play_stream(url: str, silent=True, video_mode=False) -> subprocess.Popen:
    """
    Play content based on mode and method:
    - Audio mode:
      - pipe: yt-dlp -> ffplay
      - cache: download first, then ffplay
    - Video mode:
      - pipe: pass URL directly to mpv (full features)
      - cache: download first, then mpv
    """
    cfg = load_config()
    method = cfg.get("PlaybackMethod", "pipe")
    logging.debug(
        "play_stream called with url=%s, silent=%s, method=%s, video_mode=%s",
        url,
        silent,
        method,
        video_mode,
    )

    # If the caller already provided a local cached file path, play it directly
    # instead of treating it as a URL (which would cause yt-dlp to error).
    try:
        p = Path(url)
    except Exception:
        p = None
    if p and p.exists():
        local_path = str(p)
        logging.debug(
            "play_stream: detected local file path, playing directly: %s", local_path
        )
        if video_mode:
            # Play local video file with mpv
            mpv_cmd = [
                "mpv",
                local_path,
                "--force-window",
                "--no-terminal" if silent else None,
                "--msg-level=all=no" if silent else None,
            ]
            mpv_cmd = [c for c in mpv_cmd if c is not None]
            logging.debug("mpv cmd (local file): %s", " ".join(mpv_cmd))
            try:
                proc = subprocess.Popen(
                    mpv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                logging.info("Playing local video file: %s", local_path)
                return proc
            except Exception as e:
                logging.error(
                    "Failed to start mpv for local file %s: %s", local_path, e
                )
                return None
        else:
            # Play local audio file with ffplay
            ffplay_cmd = [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "info" if not silent else "quiet",
                local_path,
            ]
            logging.debug("ffplay cmd (local file): %s", " ".join(ffplay_cmd))
            try:
                proc = subprocess.Popen(ffplay_cmd, stdin=subprocess.DEVNULL)
                logging.info("Playing local audio file: %s", local_path)
                return proc
            except Exception as e:
                logging.error(
                    "Failed to start ffplay for local file %s: %s", local_path, e
                )
                return None

    if video_mode:
        # Get the correct path/url to play
        play_path = url
        if method == "cache":
            # For cached files, we already have the file path
            if Path(url).exists():  # If url is actually a local file path
                play_path = url
            else:
                # Otherwise download to cache
                filepath = download_to_cache(url, cfg, video_mode=True)
                if not filepath:
                    logging.error("Cache download failed for %s", url)
                    return None
                play_path = str(filepath)

        # Construct mpv command
        mpv_cmd = [
            "mpv",
            play_path,
            "--force-window",
            "--no-terminal" if silent else None,
            "--msg-level=all=no" if silent else None,
        ]
        # Add cookies only for URLs, not local files
        if not Path(play_path).exists():
            cookies = cfg.get("CookiesFile", COOKIES_FILE)
            if Path(cookies).exists():
                mpv_cmd.append(f"--cookies-file={cookies}")

        mpv_cmd = [c for c in mpv_cmd if c is not None]
        logging.debug("mpv cmd: %s", " ".join(mpv_cmd))

        try:
            proc = subprocess.Popen(
                mpv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            logging.debug("mpv process started, pid=%s", proc.pid)
            if Path(play_path).exists():
                logging.info("Playing video from cache: %s", play_path)
            else:
                logging.info("Playing video via mpv: %s", play_path)
            return proc
        except Exception as e:
            logging.error("Failed to start mpv: %s", e)
            return None
        else:
            # Pipe mode: Let mpv handle everything - pass URL directly
            cookies = cfg.get("CookiesFile", COOKIES_FILE)
            mpv_cmd = [
                "mpv",
                url,
                "--force-window",
                "--no-terminal" if silent else None,
                "--msg-level=all=no" if silent else None,
                f"--cookies-file={cookies}" if Path(cookies).exists() else None,
            ]
            mpv_cmd = [c for c in mpv_cmd if c is not None]

            logging.debug("mpv cmd (direct): %s", " ".join(mpv_cmd))
            try:
                proc = subprocess.Popen(
                    mpv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                logging.debug("mpv process started (direct), pid=%s", proc.pid)
                logging.info("Playing video via mpv: %s", url)
                return proc
            except Exception as e:
                logging.error("Failed to start mpv: %s", e)
                return None

    # Audio playback modes
    elif method == "cache":
        # download to cache first
        try:
            filepath = download_to_cache(url, cfg)
            if not filepath:
                logging.error("Cache download failed for %s", url)
                return None
            ffplay_cmd = [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "info" if not silent else "quiet",
                str(filepath),
            ]
            logging.debug("ffplay cmd (cache): %s", " ".join(ffplay_cmd))
            proc = subprocess.Popen(ffplay_cmd, stdin=subprocess.DEVNULL)
            logging.debug("ffplay process started from cache, pid=%s", proc.pid)
            logging.info("Playing from cache: %s", filepath)
            return proc
        except Exception as e:
            logging.error("Failed to start ffplay from cache: %s", e)
            return None
    else:
        # audio pipe method
        ytdlp_cmd = [
            "yt-dlp",
            "-f",
            "bestaudio",
            "-o",
            "-",
            url,
        ]
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
                ffplay_cmd,
                stdin=ytdlp_proc.stdout,
                stdout=subprocess.DEVNULL,
                stderr=None,
            )
            logging.debug(
                "yt-dlp pid=%s, ffplay pid=%s", ytdlp_proc.pid, ffplay_proc.pid
            )
            logging.info("Playing via pipe: %s", url)
            return ffplay_proc
        except Exception as e:
            logging.error("Failed to start yt-dlp|ffplay pipeline: %s", e)
            return None


def interactive_play(
    entries: List[dict], cfg: dict, playlist_url: Optional[str] = None, video_mode=False
):
    logging.debug(
        "interactive_play called with %d entries, video_mode=%s",
        len(entries),
        video_mode,
    )
    idx = 0
    retry = 3
    while 0 <= idx < len(entries):
        logging.debug("Playlist index: %d", idx)
        e = entries[idx]
        title = e.get("title") or "Unknown"
        webpage_url = e.get("webpage_url") or e.get("url")
        logging.debug("Now playing entry: %s, url: %s", title, webpage_url)
        print(f"\nNow playing: [{idx+1}/{len(entries)}] {title}")
        logging.info(
            "Now playing playlist entry %d/%d: %s", idx + 1, len(entries), title
        )
        retry_count = 0
        # Record playlist entry in history (playlist-level)
        try:
            append_history(
                {
                    "type": "playlist_entry",
                    "playlist_url": playlist_url,
                    "track_url": webpage_url,
                    "title": title,
                    "timestamp": int(time.time()),
                }
            )
        except Exception:
            pass
        while retry_count < 3:
            # try to get duration from metadata and try cache first
            info = get_video_info(webpage_url)
            duration = None
            if info:
                duration = info.get("duration")
            # Determine if we should use cache or direct streaming
            play_url = webpage_url
            if cfg.get("PlaybackMethod") == "cache":
                filepath = download_to_cache(webpage_url, cfg, video_mode=video_mode)
                if not filepath:
                    print("  Failed to download to cache.")
                    logging.info("Cache download failed for %s", title)
                    idx += 1
                    break
                play_url = str(filepath)  # Use the cached file path
            player = play_stream(
                play_url, silent=not cfg.get("Debug", False), video_mode=video_mode
            )
            if player is None:
                print("  Failed to start player.")
                logging.info("Player failed to start for %s", title)
                idx += 1
                break
            print("  Controls: [n]ext, [r]eplay, [q]uit")
            logging.debug("Displayed controls to user")
            logging.debug("Player started for entry: %s", title)
            user_action = None
            start_ts = time.time()
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
                    # Only show elapsed time in audio mode
                    if not video_mode:
                        elapsed = int(time.time() - start_ts)
                        if duration:
                            total = int(duration)
                            sys.stdout.write(f"\rElapsed: {elapsed}s / {total}s ")
                        else:
                            sys.stdout.write(f"\rElapsed: {elapsed}s")
                        sys.stdout.flush()
                    time.sleep(0.1)  # More responsive controls
            except KeyboardInterrupt:
                logging.debug("KeyboardInterrupt: terminating player.")
                player.terminate()
                return
            exit_code = player.wait()
            # clear elapsed line in audio mode
            if not video_mode:
                try:
                    sys.stdout.write("\r" + " " * 60 + "\r")
                except Exception:
                    pass
            logging.debug("Player exited with code: %s", exit_code)
            # If abnormal exit, retry up to 2 more times
            if exit_code != 0 and user_action is None:
                retry_count += 1
                print(
                    f"  Player exited abnormally (code {exit_code}), retrying ({retry_count}/3)..."
                )
                logging.warning(
                    "Player exited abnormally (code %s), retrying (%d/3)...",
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
    logging.info("End of playlist")


# ------------------------------------------------------------------
# Input handler
# ------------------------------------------------------------------
def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")


def is_playlist(url: str) -> bool:
    return "playlist" in url or "list=" in url


def handle_input(raw: str, cfg: dict, video_mode=False):
    logging.debug("handle_input called with raw='%s', video_mode=%s", raw, video_mode)
    raw = raw.strip()
    if not raw:
        return
    if is_url(raw):
        logging.debug("Input detected as URL.")
        if is_playlist(raw):
            logging.debug("URL detected as playlist.")
            print("Playlist URL detected – fetching all entries …")
            logging.info("Playlist URL detected: %s", raw)
            entries = playlist_to_entries(raw)
            if entries:
                logging.debug("Playlist has %d entries.", len(entries))
                # Use current debug setting for playlist playback
                interactive_play(entries, cfg, playlist_url=raw, video_mode=video_mode)
            else:
                logging.debug("Playlist empty or unavailable.")
                print("Empty or unavailable playlist.")
                logging.info("Playlist empty or unavailable: %s", raw)
        else:
            logging.debug("URL detected as single video.")
            # single video: stream directly
            print("Now playing: [1/1] (single video)")
            logging.info(
                "Now playing single %s: %s", "video" if video_mode else "audio", raw
            )
            # record history (include title from metadata when available)
            try:
                info = get_video_info(raw)
                title = info.get("title") if info else None
                append_history(
                    {
                        "type": "single",
                        "playlist_url": None,
                        "track_url": raw,
                        "title": title,
                        "timestamp": int(time.time()),
                    }
                )
            except Exception:
                pass
            while True:
                # ensure we have metadata for duration display
                info = info if "info" in locals() else get_video_info(raw)
                duration = info.get("duration") if info else None
                # Determine if we should use cache or direct streaming
                play_url = raw
                if cfg.get("PlaybackMethod") == "cache":
                    filepath = download_to_cache(raw, cfg, video_mode=video_mode)
                    if not filepath:
                        print("  Failed to download to cache.")
                        logging.info("Cache download failed for single video: %s", raw)
                        return
                    play_url = str(filepath)  # Use the cached file path
                player = play_stream(
                    play_url, silent=not cfg.get("Debug", False), video_mode=video_mode
                )
                print("  Controls: [r]eplay, [q]uit")
                if player is None:
                    print("  Failed to start player.")
                    return
                user_action = None
                try:
                    start_ts = time.time()
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
                        # In video mode, don't show elapsed time since mpv has its own OSD
                        if not video_mode:
                            elapsed = int(time.time() - start_ts)
                            if duration:
                                total = int(duration)
                                sys.stdout.write(f"\rElapsed: {elapsed}s / {total}s ")
                            else:
                                sys.stdout.write(f"\rElapsed: {elapsed}s")
                            sys.stdout.flush()
                        time.sleep(0.1)  # Shorter sleep for more responsive controls
                except KeyboardInterrupt:
                    logging.debug("KeyboardInterrupt: terminating player.")
                    player.terminate()
                    return
                # Clear elapsed line in audio mode
                if not video_mode:
                    try:
                        sys.stdout.write("\r" + " " * 60 + "\r")
                    except Exception:
                        pass
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
                interactive_play(selected, cfg, playlist_url=None)
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


def list_playlist_files(folder: str = "playlists") -> List[Path]:
    """Return a list of Path objects for playlist files in the given folder.
    Creates the folder if it does not exist.
    """
    p = Path(folder)
    p.mkdir(parents=True, exist_ok=True)
    files = [
        f
        for f in sorted(p.iterdir())
        if f.is_file() and f.suffix.lower() in (".txt", ".list", ".m3u")
    ]
    logging.debug("Found %d playlist files in %s", len(files), folder)
    return files


def play_from_list_file(
    path: Path,
    cfg: dict,
    video_mode: bool = False,
    shuffle: bool = False,
    shuffle_all: bool = False,
    auto_mode: bool = False,
):
    """Play URLs listed (one per line) in the given file.

    Each line may be a single video URL or a playlist URL. For playlist URLs,
    expand entries and play them sequentially. After a playlist finishes, move
    to the next line in the file. Respects global PlaybackMethod and video_mode.

    Args:
      shuffle: Shuffle top-level lines only
      shuffle_all: Flatten all entries (expand playlists) and shuffle the result
      auto_mode: Auto-advance without user prompts (no n/r/q controls)
    """
    logging.info("Playing list file: %s", path)
    try:
        with open(path, encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines()]
    except Exception as e:
        logging.error("Failed to read list file %s: %s", path, e)
        print("Failed to read list file:", e)
        return

    entries = [l for l in lines if l and not l.startswith("#")]
    if not entries:
        print("No URLs found in", path)
        return

    # If shuffle_all, flatten all entries (expand playlists) and shuffle the result
    if shuffle_all:
        logging.info("Expanding all playlists for shuffle_all mode")
        flattened = []
        for raw in entries:
            if is_url(raw) and is_playlist(raw):
                pl_entries = playlist_to_entries(raw)
                for pe in pl_entries or []:
                    flattened.append(pe.get("webpage_url") or pe.get("url"))
            elif is_url(raw):
                flattened.append(raw)
        entries = flattened
        random.shuffle(entries)
        logging.info("After shuffle_all: %d total entries", len(entries))
    # Optionally shuffle the top-level entries from the file (only if shuffle_all not used)
    elif shuffle:
        random.shuffle(entries)

    for i, raw in enumerate(entries, 1):
        print(f"\n== List item {i}/{len(entries)}: {raw}")
        logging.info(
            "List file %s: playing entry %d/%d: %s", path, i, len(entries), raw
        )
        # If it's a playlist URL, expand and play entries
        if is_url(raw) and is_playlist(raw):
            print("Playlist URL detected – fetching all entries …")
            logging.info("Playlist URL detected in list file: %s", raw)
            pl_entries = playlist_to_entries(raw)
            if pl_entries:
                interactive_play(
                    pl_entries, cfg, playlist_url=raw, video_mode=video_mode
                )
            else:
                print("Empty or unavailable playlist.")
            # after playlist finished, continue to next list file line
            continue

        # If it's a URL (single video), play it similarly to interactive single play
        if is_url(raw):
            title = None
            try:
                info = get_video_info(raw)
                title = info.get("title") if info else None
            except Exception:
                info = None

            print(f"Now playing: {title or raw}")
            # record history
            try:
                append_history(
                    {
                        "type": "list_item",
                        "playlist_url": str(path),
                        "track_url": raw,
                        "title": title,
                        "timestamp": int(time.time()),
                    }
                )
            except Exception:
                pass

            # Use cache if configured
            play_target = raw
            if cfg.get("PlaybackMethod") == "cache":
                filepath = download_to_cache(raw, cfg, video_mode=video_mode)
                if not filepath:
                    print("  Failed to download to cache.")
                    logging.info("Cache download failed for %s", raw)
                    continue
                play_target = str(filepath)

            # Start player and allow user controls similar to interactive_play
            player = play_stream(
                play_target, silent=not cfg.get("Debug", False), video_mode=video_mode
            )
            if player is None:
                print("  Failed to start player.")
                logging.info("Player failed to start for %s", raw)
                continue

            user_action = None
            start_ts = time.time()
            try:
                while player.poll() is None:
                    # In auto_mode, skip all user input checks
                    if not auto_mode:
                        if platform.system() == "Windows":
                            import msvcrt

                            if msvcrt.kbhit():
                                ch = msvcrt.getch().decode().lower()
                                logging.debug("User pressed key: %s", ch)
                                if ch == "n":
                                    logging.debug("User requested next item in list.")
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
                                    logging.debug("User requested next item in list.")
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

                    # show elapsed in audio mode
                    if not video_mode:
                        elapsed = int(time.time() - start_ts)
                        if info and info.get("duration"):
                            total = int(info.get("duration"))
                            sys.stdout.write(f"\rElapsed: {elapsed}s / {total}s ")
                        else:
                            sys.stdout.write(f"\rElapsed: {elapsed}s")
                        sys.stdout.flush()
                    time.sleep(0.1)
            except KeyboardInterrupt:
                logging.debug("KeyboardInterrupt: terminating player.")
                player.terminate()
                return

            # Clear elapsed line in audio mode
            if not video_mode:
                try:
                    sys.stdout.write("\r" + " " * 60 + "\r")
                except Exception:
                    pass

            # In auto_mode, skip all post-play prompts and just continue
            if auto_mode:
                logging.info("auto_mode: continuing to next item")
                continue

            # Replay handling
            if user_action == "replay":
                # replay same item
                try:
                    continue
                except Exception:
                    pass
            # If next was requested, continue to next URL in file
            if user_action == "next":
                continue

            # natural end: continue to next file entry
            continue
        else:
            logging.debug("Skipping non-URL line in list file: %s", raw)
            continue


# ------------------------------------------------------------------
# Cached playback helpers (start, send key, pause/resume)
# ------------------------------------------------------------------
def _start_ffplay_for_file(filepath: str, cfg: dict, silent: bool) -> subprocess.Popen:
    ffplay_cmd = [
        "ffplay",
        "-i",
        str(filepath),
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "info" if not silent else "quiet",
    ]
    logging.debug("ffplay cmd (cache, controllable stdin): %s", " ".join(ffplay_cmd))
    try:
        proc = subprocess.Popen(
            ffplay_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logging.info(
            "ffplay started for cached file %s (pid=%s)",
            filepath,
            getattr(proc, "pid", None),
        )
        return proc
    except Exception as e:
        logging.error("Failed to start ffplay for cached file %s: %s", filepath, e)
        return None


def _ffplay_send_key(proc: subprocess.Popen, key: bytes = b"p") -> bool:
    if not proc or proc.poll() is not None:
        logging.debug("_ffplay_send_key: process not running or exited")
        return False
    try:
        if proc.stdin:
            proc.stdin.write(key)
            proc.stdin.flush()
            logging.debug("Wrote key %r to ffplay stdin (pid=%s)", key, proc.pid)
            return True
    except Exception as e:
        logging.debug("Failed to write to ffplay stdin: %s", e)
    return False


def _suspend_process_posix(proc: subprocess.Popen) -> bool:
    try:
        os.kill(proc.pid, signal.SIGSTOP)
        logging.debug("Sent SIGSTOP to pid %s", proc.pid)
        return True
    except Exception as e:
        logging.debug("SIGSTOP failed: %s", e)
        return False


def _resume_process_posix(proc: subprocess.Popen) -> bool:
    try:
        os.kill(proc.pid, signal.SIGCONT)
        logging.debug("Sent SIGCONT to pid %s", proc.pid)
        return True
    except Exception as e:
        logging.debug("SIGCONT failed: %s", e)
        return False


def pause_cached_playback(proc: subprocess.Popen) -> bool:
    if _ffplay_send_key(proc, b"p"):
        logging.info(
            "Toggled pause via ffplay stdin (pid=%s)", getattr(proc, "pid", None)
        )
        return True
    if os.name == "posix":
        ok = _suspend_process_posix(proc)
        if ok:
            logging.info(
                "Paused ffplay via SIGSTOP (pid=%s)", getattr(proc, "pid", None)
            )
        return ok
    logging.warning("Unable to pause ffplay process on this platform.")
    return False


def resume_cached_playback(proc: subprocess.Popen) -> bool:
    if _ffplay_send_key(proc, b"p"):
        logging.info(
            "Toggled resume via ffplay stdin (pid=%s)", getattr(proc, "pid", None)
        )
        return True
    if os.name == "posix":
        ok = _resume_process_posix(proc)
        if ok:
            logging.info(
                "Resumed ffplay via SIGCONT (pid=%s)", getattr(proc, "pid", None)
            )
        return ok
    logging.warning("Unable to resume ffplay process on this platform.")
    return False


def offline_play(cfg: dict):
    """Hidden command: play cached audio files in shuffle order.
    Controls while playing: n=next, p=toggle pause, q=quit
    """
    cache_dir = ensure_cache_dir(cfg)
    files = [
        p
        for p in cache_dir.iterdir()
        if p.is_file() and p.suffix.lower() not in (".json",)
    ]
    if not files:
        print("No cached audio files found in", str(cache_dir))
        logging.info("offline: no cached files in %s", cache_dir)
        return
    random.shuffle(files)
    logging.info("offline: playing %d cached files (shuffled)", len(files))
    idx = 0
    while 0 <= idx < len(files):
        f = files[idx]
        title = f.name
        # try sidecar metadata
        sidecar = f.with_suffix(".json")
        if sidecar.exists():
            try:
                with open(sidecar, encoding="utf-8") as sf:
                    meta = json.load(sf)
                    title = meta.get("title") or title
            except Exception:
                pass
        print(f"\nOffline play [{idx+1}/{len(files)}]: {title}")
        logging.info("offline now playing: %s", f)
        # start ffplay with controllable stdin
        player = _start_ffplay_for_file(str(f), cfg, silent=not cfg.get("Debug", False))
        if player is None:
            logging.warning("offline: failed to start player for %s", f)
            idx += 1
            continue
        try:
            while player.poll() is None:
                # check for keypress
                if platform.system() == "Windows":
                    import msvcrt

                    if msvcrt.kbhit():
                        ch = msvcrt.getch().decode().lower()
                        logging.debug("offline: user pressed key: %s", ch)
                        if ch == "n":
                            player.terminate()
                            break
                        elif ch == "p":
                            _ffplay_send_key(player, b"p")
                        elif ch == "q":
                            player.terminate()
                            return
                else:
                    import select

                    if select.select([sys.stdin], [], [], 0)[0]:
                        ch = sys.stdin.read(1).lower()
                        logging.debug("offline: user pressed key: %s", ch)
                        if ch == "n":
                            player.terminate()
                            break
                        elif ch == "p":
                            _ffplay_send_key(player, b"p")
                        elif ch == "q":
                            player.terminate()
                            return
                time.sleep(0.1)
        except KeyboardInterrupt:
            logging.debug("offline: KeyboardInterrupt, terminating player.")
            try:
                player.terminate()
            except Exception:
                pass
            return
        idx += 1
    print("Offline playback finished.")
    logging.info("offline: finished playing cached files")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Lightweight YouTube player")
    parser.add_argument(
        "input", nargs="?", help="Search query, video URL, or playlist URL"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--force-cache-refresh",
        action="store_true",
        help="Force re-download of cached tracks (overrides existing cache)",
    )
    parser.add_argument(
        "--update-yt-dlp",
        action="store_true",
        help="Check for a newer yt-dlp and attempt to update it using the detected method",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Start playback from cached files in shuffle mode (hidden)",
    )
    parser.add_argument(
        "--video",
        action="store_true",
        help="Enable video playback mode using mpv player",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Show and play from playlist files stored in ./playlists (one URL per line)",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle the order of URLs when using --list (shuffles top-level file lines only)",
    )
    parser.add_argument(
        "--shuffle-all",
        action="store_true",
        help="Shuffle all tracks when using --list (expands playlists and shuffles all resulting entries)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-advance through --list without user prompts (non-interactive mode)",
    )
    args = parser.parse_args()

    logging.debug("main() called")
    cfg = load_config()
    if args.debug:
        cfg["Debug"] = True
    if getattr(args, "force_cache_refresh", False):
        cfg["ForceCacheRefresh"] = True
    logging.debug("Debug mode: %s", cfg["Debug"])
    init_logger(cfg["Debug"])
    logging.info("Player starting. Debug=%s", cfg["Debug"])

    # Check for mpv if video mode enabled
    if args.video:
        logging.info("Video mode enabled, checking for mpv player")
        if not ensure_dependencies(check_mpv=True):
            sys.exit("mpv player required for video mode")

    ensure_dependencies()

    # Check yt-dlp version and notify if update available. Optionally attempt update.
    try:
        installed_v = _get_installed_yt_dlp_version()
        latest_v = _get_latest_yt_dlp_version_pypi()
        if installed_v and latest_v:
            logging.debug(
                "yt-dlp installed version=%s latest=%s", installed_v, latest_v
            )
            try:
                if _is_version_greater(latest_v, installed_v):
                    msg = f"A newer yt-dlp is available: {installed_v} -> {latest_v}."
                    print(msg)
                    logging.info(msg)
                    method = _detect_install_method()
                    cmds = _suggest_update_commands(method)
                    print(
                        "Suggested update commands (choose the one matching your install method):"
                    )
                    for c in cmds:
                        print("  ", c)
                    # If user passed the flag, attempt update non-interactively
                    if args.update_yt_dlp:
                        print(
                            "Attempting runtime update using detected method:", method
                        )
                        ok = _attempt_runtime_update(method)
                        if ok:
                            print(
                                "yt-dlp updated successfully. You may need to restart the script."
                            )
                            logging.info("yt-dlp updated successfully via %s", method)
                        else:
                            print(
                                "Automatic update failed. See logs for details and try one of the suggested commands."
                            )
                    # Otherwise, if running interactively, ask the user
                    elif sys.stdin is not None and sys.stdin.isatty():
                        try:
                            resp = input("Update yt-dlp now? [Y/n]: ").strip().lower()
                        except (EOFError, KeyboardInterrupt):
                            resp = "n"
                        if resp in ("", "y", "yes"):
                            print(
                                "Attempting runtime update using detected method:",
                                method,
                            )
                            ok = _attempt_runtime_update(method)
                            if ok:
                                print(
                                    "yt-dlp updated successfully. You may need to restart the script."
                                )
                                logging.info(
                                    "yt-dlp updated successfully via %s", method
                                )
                            else:
                                print(
                                    "Automatic update failed. See logs for details and try one of the suggested commands."
                                )
                        else:
                            print(
                                "Skipping automatic update. You can update later using one of the suggested commands."
                            )
                    else:
                        print(
                            "Non-interactive session: run with --update-yt-dlp to attempt an automatic update or run one of the suggested commands manually."
                        )
                else:
                    logging.debug("yt-dlp is up-to-date (%s)", installed_v)
            except Exception as e:
                logging.debug("Version comparison failed: %s", e)
        else:
            logging.debug(
                "Could not determine installed or latest yt-dlp version (installed=%s latest=%s)",
                installed_v,
                latest_v,
            )
    except Exception as e:
        logging.debug("yt-dlp update check failed: %s", e)

    # If offline flag passed, start offline playback and exit
    if getattr(args, "offline", False):
        logging.info("Starting offline playback (cache) via --offline flag")
        try:
            offline_play(cfg)
        except Exception as e:
            logging.error("Offline playback failed: %s", e)
        return

    # If --list flag passed, show playlist files and let user pick one to play
    if getattr(args, "list", False):
        files = list_playlist_files()
        if not files:
            print(
                "No playlist files found in ./playlists. Add .txt files with one URL per line."
            )
            return
        print("Available playlist files:")
        for i, f in enumerate(files, 1):
            print(f"[{i}] {f.name}")
        try:
            sel = input("Select file by number (or 0 to cancel): ").strip()
            if not sel or sel == "0":
                print("Cancelled.")
                return
            idx = int(sel) - 1
            if not (0 <= idx < len(files)):
                print("Invalid selection.")
                return
        except Exception:
            print("Invalid selection.")
            return
        chosen = files[idx]
        logging.info("User selected playlist file: %s", chosen)
        play_from_list_file(
            chosen,
            cfg,
            video_mode=args.video,
            shuffle=args.shuffle,
            shuffle_all=args.shuffle_all,
            auto_mode=args.auto,
        )
        return

    if args.input:
        logging.debug("Input argument provided: %s", args.input)
        handle_input(args.input, cfg, video_mode=args.video)
    else:
        # interactive session
        logging.debug("Entering interactive session loop. Video mode: %s", args.video)
        while True:
            try:
                prompt = "YouTube(video)> " if args.video else "YouTube> "
                raw = input(f"\n{prompt}").strip()
                logging.debug("User input: %s", raw)
            except (EOFError, KeyboardInterrupt):
                logging.debug("Session ended by user.")
                print("\nBye.")
                break
            if raw.lower() in {"exit", "quit", "q"}:
                logging.debug("User requested exit.")
                break
            if raw.lower() == "history":
                # hidden command: show paginated history
                try:
                    show_history_paged()
                except Exception as e:
                    print("Could not load history:", e)
                continue
            if raw.lower() == "config":
                # hidden command: view/edit config
                try:
                    cfg_current = load_config()
                    print(json.dumps(cfg_current, indent=2, ensure_ascii=False))
                except Exception as e:
                    print("Could not load config:", e)
                    continue
                edit = input("Edit config? (y/N): ").strip().lower()
                if edit == "y":
                    print(
                        "Enter key=value lines. Empty line to finish. Current values shown above."
                    )
                    while True:
                        try:
                            line = input("config> ").strip()
                        except (EOFError, KeyboardInterrupt):
                            print()
                            break
                        if not line:
                            break
                        if "=" not in line:
                            print("Invalid format. Use key=value")
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        # simple type coercion
                        if v.lower() in ("true", "false"):
                            parsed = v.lower() == "true"
                        else:
                            try:
                                parsed = int(v)
                            except Exception:
                                try:
                                    parsed = float(v)
                                except Exception:
                                    parsed = v
                        cfg_current[k] = parsed
                    try:
                        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                            json.dump(cfg_current, f, ensure_ascii=False, indent=2)
                        print("Config saved to", CONFIG_FILE)
                        logging.info("Config saved to %s", CONFIG_FILE)
                        # update live cfg used by the session
                        cfg.update(cfg_current)
                    except Exception as e:
                        print("Failed to save config:", e)
                continue
            handle_input(raw, cfg, video_mode=args.video)


if __name__ == "__main__":
    try:
        import shutil
    except ImportError:
        import shutil
    main()
