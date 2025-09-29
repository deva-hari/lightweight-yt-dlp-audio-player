import os
import re
import subprocess
import sys
import shlex
import msvcrt

# ========== CONFIGURATION ==========
SEARCH_RESULTS = 10  # Default number of search results
COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.txt")
YT_DLP = "yt-dlp"
FFPLAY = "ffplay"
LOG_ENABLED = True  # Set to False to disable logging
LOG_FILE = os.path.join(os.path.dirname(__file__), "yt_audio_player.log")


# ========== LOGGING (TOGGLABLE) ==========
def log(msg):
    """Write a message to the log file if logging is enabled."""
    if LOG_ENABLED:
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(msg + "\n")


# ========== UTILITY FUNCTIONS ==========
def has_cookies():
    present = os.path.isfile(COOKIES_FILE)
    log(f"[INFO] Checking for cookies.txt: {'FOUND' if present else 'NOT FOUND'}")
    return present


def is_url(text):
    result = re.match(r"^https?://", text.strip()) is not None
    log(f"[DEBUG] is_url('{text}') -> {result}")
    return result


def run_cmd(cmd, silent=True):
    log(f"[DEBUG] run_cmd: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    if silent:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            encoding="utf-8",
        )
    else:
        return subprocess.run(cmd, shell=True)


# ========== SEARCH & METADATA ==========
def search_yt(query, n=SEARCH_RESULTS, cookies=None):
    cmd = [YT_DLP]
    if cookies:
        cmd += ["--cookies", cookies]
    cmd += [
        f"ytsearch{n}:{query}",
        "--print",
        "%(id)s\t%(title)s\t%(channel)s\t%(duration_string)s",
        "--skip-download",
        "--no-warnings",
        "--quiet",
    ]
    log(f"[INFO] Searching YouTube for: {query}")
    log(f"[DEBUG] Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    log(f"[DEBUG] yt-dlp stdout: {result.stdout}")
    log(f"[DEBUG] yt-dlp stderr: {result.stderr}")
    if not result.stdout:
        if result.stderr:
            log(f"[ERROR] yt-dlp error: {result.stderr.strip()}")
        return []
    lines = result.stdout.strip().splitlines()
    videos = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) == 4:
            videos.append(
                {
                    "id": parts[0],
                    "title": parts[1],
                    "channel": parts[2],
                    "duration": parts[3],
                }
            )
    log(f"[INFO] Found {len(videos)} search results.")
    return videos


def get_playlist_video_ids(playlist_url, cookies=None):
    """
    Returns a list of dicts: [{id, title, channel, duration}], or [] if not a playlist.
    Logs all output for debugging.
    """
    cmd = [
        YT_DLP,
        "--flat-playlist",
        "--print",
        "%(id)s\t%(title)s\t%(channel)s\t%(duration_string)s",
        playlist_url,
    ]
    if cookies:
        cmd += ["--cookies", cookies]
    log(f"[INFO] Checking playlist: {playlist_url}")
    log(f"[DEBUG] Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    log(f"[DEBUG] yt-dlp stdout: {result.stdout}")
    log(f"[DEBUG] yt-dlp stderr: {result.stderr}")
    videos = []
    if not result.stdout:
        log("[ERROR] No playlist output from yt-dlp.")
        return []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 1 and parts[0]:
            video = {"id": parts[0]}
            if len(parts) > 1:
                video["title"] = parts[1]
            if len(parts) > 2:
                video["channel"] = parts[2]
            if len(parts) > 3:
                video["duration"] = parts[3]
            videos.append(video)
    log(f"[INFO] Playlist contains {len(videos)} videos.")
    return videos


def get_video_title(video_id, cookies=None):
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [YT_DLP, "--print", "%(title)s", "--skip-download", url]
    if cookies:
        cmd += ["--cookies", cookies]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout:
        return result.stdout.strip().splitlines()[0]
    return video_id


def get_single_video_metadata(video_url, cookies=None):
    cmd = [
        YT_DLP,
        "--print",
        "%(id)s\t%(title)s\t%(channel)s\t%(duration_string)s",
        "--skip-download",
        video_url,
    ]
    if cookies:
        cmd += ["--cookies", cookies]
    log(f"[INFO] Checking single video: {video_url}")
    log(f"[DEBUG] Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    log(f"[DEBUG] yt-dlp stdout: {result.stdout}")
    log(f"[DEBUG] yt-dlp stderr: {result.stderr}")
    if not result.stdout:
        log("[ERROR] No video output from yt-dlp.")
        return None
    parts = result.stdout.strip().split("\t")
    if len(parts) >= 1 and parts[0]:
        video = {"id": parts[0]}
        if len(parts) > 1:
            video["title"] = parts[1]
        if len(parts) > 2:
            video["channel"] = parts[2]
        if len(parts) > 3:
            video["duration"] = parts[3]
        log(f"[INFO] Single video metadata: {video}")
        return video
    return None


# ========== PLAYBACK ==========
def play_audio(video_id, cookies=None):
    title = get_video_title(video_id, cookies)
    log(f"[INFO] Now playing: {title} (id={video_id})")
    print(f"[PLAYING] {title}")
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [YT_DLP, "-f", "bestaudio", "-o", "-", url]
    if cookies:
        cmd += ["--cookies", cookies]
    ffplay_cmd = [FFPLAY, "-nodisp", "-autoexit", "-loglevel", "quiet", "-i", "-"]
    log(f"[DEBUG] Running: {' '.join(cmd)} | {' '.join(ffplay_cmd)}")
    try:
        ytdlp_proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        ffplay_proc = subprocess.Popen(
            ffplay_cmd,
            stdin=ytdlp_proc.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ytdlp_proc.stdout.close()
        print("[INFO] Press 'n' to skip/next, Ctrl+C to return to main menu.")
        while True:
            if ffplay_proc.poll() is not None:
                return "done"
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b"n", b"N"):
                    print("\n[INFO] Skipped.")
                    log(f"[INFO] Skipped: {title} (id={video_id})")
                    ytdlp_proc.terminate()
                    ffplay_proc.terminate()
                    return "skip"
            import time

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[INFO] Returning to main menu.")
        log(f"[INFO] KeyboardInterrupt during playback: {title} (id={video_id})")
        try:
            ytdlp_proc.terminate()
            ffplay_proc.terminate()
        except Exception:
            pass
        return "break"


# ========== DEPENDENCY CHECK & AUTO-INSTALL ==========
def check_and_install_dependencies():
    import shutil
    import platform

    # Check yt-dlp
    yt_dlp_path = shutil.which(YT_DLP)
    if not yt_dlp_path:
        print("[INFO] yt-dlp not found. Attempting to install via pip...")
        log("[INFO] yt-dlp not found. Attempting to install via pip...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"]
            )
            print("[INFO] yt-dlp installed successfully.")
            log("[INFO] yt-dlp installed successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to install yt-dlp: {e}")
            log(f"[ERROR] Failed to install yt-dlp: {e}")
            sys.exit(1)
    # Check ffplay
    ffplay_path = shutil.which(FFPLAY)
    if not ffplay_path:
        print(
            "[ERROR] ffplay not found in PATH. Attempting to install FFmpeg using winget..."
        )
        log(
            "[ERROR] ffplay not found in PATH. Attempting to install FFmpeg using winget..."
        )
        if platform.system() == "Windows":
            try:
                subprocess.check_call(
                    ["winget", "install", "-e", "--id", "Gyan.FFmpeg"], shell=True
                )
                print(
                    "[INFO] FFmpeg installation attempted. Please restart your terminal or add ffplay to PATH if needed."
                )
                log("[INFO] FFmpeg installation attempted via winget.")
            except Exception as e:
                print(f"[ERROR] Failed to install FFmpeg using winget: {e}")
                log(f"[ERROR] Failed to install FFmpeg using winget: {e}")
            # Re-check ffplay after attempted install
            ffplay_path = shutil.which(FFPLAY)
            if not ffplay_path:
                print(
                    "[ERROR] ffplay still not found in PATH. Please install FFmpeg from https://ffmpeg.org/download.html and add ffplay to your PATH."
                )
                log("[ERROR] ffplay still not found in PATH after winget attempt.")
                sys.exit(1)
        else:
            print(
                "[ERROR] ffplay not found in PATH. Please install FFmpeg and add ffplay to your PATH."
            )
            log(
                "[ERROR] ffplay not found in PATH. Please install FFmpeg and add ffplay to your PATH."
            )
            sys.exit(1)


# ========== MAIN LOOP ==========
def main():
    cookies = COOKIES_FILE if has_cookies() else None
    print("Lightweight YouTube Audio Player (Python)")
    print("Type a YouTube link, playlist, or search query. Type EXIT to quit.")
    while True:
        try:
            user_input = input("\nInput: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)
        if not user_input:
            continue
        if user_input.lower() == "exit":
            break
        if is_url(user_input):
            print("[INFO] Checking if input is a playlist...")
            playlist_videos = get_playlist_video_ids(user_input, cookies)
            if not playlist_videos:
                # Try as single video
                single_video = get_single_video_metadata(user_input, cookies)
                if not single_video:
                    print("[ERROR] Could not retrieve video. Please check the link.")
                    continue
                title = single_video.get("title", single_video["id"])
                print(
                    f"[INFO] Single video detected: {title}. Streaming audio... (Press 'n' for next, Ctrl+C to exit)"
                )
                play_audio(single_video["id"], cookies)
                continue
            if len(playlist_videos) > 1:
                print(
                    f"[INFO] Playlist detected with {len(playlist_videos)} videos. (Press 'n' for next, Ctrl+C to return to main menu)"
                )
                for idx, vid in enumerate(playlist_videos, 1):
                    title = vid.get("title", vid["id"])
                    print(
                        f"[INFO] Playing {idx}/{len(playlist_videos)}: {title} (Press 'n' for next, Ctrl+C to return to main menu)"
                    )
                    result = play_audio(vid["id"], cookies)
                    if result == "break":
                        break
                continue
            else:
                # Only one video in playlist (not a real playlist)
                vid = playlist_videos[0]
                title = vid.get("title", vid["id"])
                print(
                    f"[INFO] Single video detected: {title}. Streaming audio... (Press 'n' for next, Ctrl+C to exit)"
                )
                play_audio(vid["id"], cookies)
                continue
        # Search query
        print(f"[INFO] Searching YouTube for: {user_input}")
        results = search_yt(user_input, SEARCH_RESULTS, cookies)
        if not results:
            print("No results found. Try a different query.")
            continue
        print("\nResults:")
        for idx, vid in enumerate(results, 1):
            print(f'{idx}. {vid["title"]} | {vid["channel"]} | {vid["duration"]}')
        while True:
            sel = input(
                "Select a video number to play (or press Enter to cancel): "
            ).strip()
            if not sel:
                break
            if sel.isdigit() and 1 <= int(sel) <= len(results):
                video_id = results[int(sel) - 1]["id"]
                print(
                    f'[INFO] Streaming: {results[int(sel)-1]["title"]} (Ctrl+C to skip)'
                )
                play_audio(video_id, cookies)
                break
            else:
                print("Invalid selection. Try again.")


if __name__ == "__main__":
    check_and_install_dependencies()
    main()
