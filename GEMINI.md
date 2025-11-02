# Gemini Code Assistant Context

## Project Overview

This project is a command-line YouTube audio and video player written in Python. It is designed to be lightweight and resource-efficient, making it suitable for running in the background while gaming or performing other tasks.

The player is highly configurable and offers a rich set of features, including:

*   **Search and Playback:** Search for YouTube videos and play them directly from the command line.
*   **Playlist Support:** Play entire YouTube playlists.
*   **Multiple Playback Modes:**
    *   `pipe`: Stream audio/video directly from `yt-dlp` to the player, minimizing disk I/O.
    *   `cache`: Download videos to a local cache before playing, which is useful for flaky internet connections.
*   **Audio and Video:**
    *   Audio-only playback using `ffplay`.
    *   Video playback using `mpv`.
*   **Interactive Controls:** Control playback with simple keyboard commands (next, replay, quit).
*   **History:** Keeps a log of played tracks, which can be viewed and exported.
*   **Offline Playback:** Play all files from the local cache in a shuffled order.
*   **Dependency Management:** The script can automatically check for and install required dependencies (`yt-dlp`, `ffmpeg`, `mpv`) using `winget` (on Windows) or `apt` and `pip` (on Linux).

The main script is `yt_audio_player.py`, which is well-structured and uses the `argparse` library for command-line arguments, `logging` for detailed logs, and a `config.json` file for configuration. An alternative, older version of the script exists at `alt/yt_audio_player_alt.py`.

## Building and Running

### 1. Installation

The script is designed to automatically install its dependencies. However, you can also install them manually.

**Dependencies:**

*   Python 3.x
*   `yt-dlp`
*   `ffmpeg` (which includes `ffplay`)
*   `mpv` (for video playback)

To install dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### 2. Configuration

The player can be configured by editing the `config.json` file. Key options include:

*   `PlaybackMethod`: Set to `"pipe"` (default) or `"cache"`.
*   `SearchLimit`: The number of search results to display.
*   `CacheMaxFiles`: The maximum number of files to store in the cache.
*   `Debug`: Set to `true` for verbose logging.

### 3. Running the Player

**Interactive Mode (Audio):**

```bash
python yt_audio_player.py
```

Then, at the `YouTube>` prompt, you can type a search query, a YouTube URL, or a playlist URL.

**Interactive Mode (Video):**

```bash
python yt_audio_player.py --video
```

**Direct Playback:**

You can also pass a query or URL as a command-line argument:

```bash
# Search and play
python yt_audio_player.py "lo-fi hip hop radio"

# Play a single video
python yt_audio_player.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Play a playlist
python yt_audio_player.py "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"

# Play a video
python yt_audio_player.py --video "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Offline Playback:**

To play from the cache:

```bash
python yt_audio_player.py --offline
```

## Development Conventions

*   **Main Script:** All new development should be focused on `yt_audio_player.py`. The script in the `alt` directory is likely for reference or historical purposes.
*   **Logging:** The script uses the `logging` module. Use `logging.info` for user-facing messages and `logging.debug` for development/troubleshooting messages. Debug logging can be enabled with the `--debug` flag.
*   **Configuration:** New configuration options should be added to the `config.json` file with sensible defaults in the `load_config` function.
*   **Dependencies:** The script uses `yt-dlp` as a Python library and also calls `ffplay` and `mpv` as subprocesses.
*   **Code Style:** The code follows standard Python conventions (PEP 8). It is well-commented and includes type hints.
*   **Cross-Platform Support:** The script is designed to be cross-platform, with checks for `platform.system()` to handle differences between Windows and Linux.
