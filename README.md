# 🎵 YT CMD Player: The Ultimate Lightweight YouTube Player

## 🤩 Why settle for less? Behold, the Most Ridiculously Lightweight YouTube Player Ever

Are you a gamer who wants to blast your favorite YouTube playlist while fragging noobs, but your browser eats more RAM than Chrome on a caffeine binge? Tired of apps that turn your potato PC into a baked potato? Want to listen to music (or watch a video) while running a game, a video call, AND 37 Chrome tabs? **This script LAUGHS at your resource limits!**

**YT CMD Player** is so light, you’ll wonder if it’s even running. It’s like the ninja of media players—silent, invisible, and deadly (to bloatware). No temp files, no drama, no nonsense. Just pure, instant media, even on a 10-year-old laptop that wheezes when you open Notepad.

## 🚀 What is this?

**YT CMD Player** is the *fastest*, *lightest*, and *most reliable* YouTube audio and video player for your command line! It lets you search, browse, and stream YouTube content with near-zero CPU/RAM usage. No temp files, no bloat, no drama—just pure, instant music and video, even on ancient laptops!

## ✨ Core Features

- **Audio & Video on Demand:** Stream audio-only with `ffplay` for minimal footprint, or launch a full video window with `mpv` using the `--video` flag.
- **Blazing Fast Search:** Type a query and get the top 10 results with titles, channels, and durations before you can say "yt-dlp"!
- **Powerful Playback Modes:**
  - **Pipe Mode (Default):** Streams media directly from YouTube to your player. Zero disk writes, maximum efficiency.
  - **Cache Mode:** Downloads tracks before playing. Perfect for flaky networks and building an offline library.
- **Total Playback Control:** Interactive controls for playlists and single tracks. Skip, replay, or quit with a single keypress.
- **Offline Mode:** Type `offline` to shuffle and play everything in your cache. No internet required!
- **Full History:** Automatically logs every track you play. View, search, filter, and export your listening history with the `history` command.
- **Smart Configuration:** Tweaks are stored in a simple `config.json`. The script creates it with sensible defaults on first run.
- **Cookies Support:** Just drop your `cookies.txt` in the folder to play age-restricted or region-locked content.
- **Self-Updating & Dependency Management:** The script checks for new `yt-dlp` versions and can even auto-install `ffmpeg` and `mpv` for you!
- **Windows Sleep Prevention:** On Windows, the script prevents your PC from sleeping while playing media. Perfect for gaming sessions or long listening sessions!
- **Crash Recovery:** If the script exits ungracefully, it automatically detects and cleans up the previous state on next run, ensuring reliable resumption.
- **Graceful Shutdown:** Signal handling for `Ctrl+C` and termination signals ensures proper cleanup before exit—no stray processes left behind.

## 🛠️ Zero-Fuss Installation

This script is smart. If you're missing dependencies, it will try to install them for you!

1. **Install Python 3.x** if you don't have it.
2. **Run the script:**

    ```sh
    python yt_audio_player.py
    ```

3. The script will check for `yt-dlp`, `ffmpeg`, and `mpv`. If they are missing, it will attempt to install them using `winget` (on Windows) or `apt`/`pip` (on Linux).
4. If the automatic install fails, you may need to install them manually:
    - **yt-dlp:** `pip install -U yt-dlp`
    - **FFmpeg:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your system's PATH.
    - **mpv:** Download from [mpv.io](https://mpv.io/installation/) and add to your system's PATH.

## 🎹 How to Use

### Interactive Mode

For the full experience, run the script without arguments. You can choose between audio or video mode.

**Audio Mode:**

```sh
python yt_audio_player.py
YouTube> lofi hip hop radio
```

**Video Mode:**

```sh
python yt_audio_player.py --video
YouTube(video)> how to cook a perfect steak
```

### Direct Playback (from Command Line)

Pass a search query, video URL, or playlist URL directly as an argument.

```sh
# Search and play audio
python yt_audio_player.py "80s synthwave mix"

# Watch a single video
python yt_audio_player.py --video "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Play an entire playlist (audio-only)
python yt_audio_player.py "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
```

### Playlist Files (`--list`)

The `--list` flag allows you to play from local playlist files. These are simple text files with one YouTube URL per line (comments starting with `#` are ignored). You can create these files in the `playlists` directory.

**How to use:**

1. Create a `playlists` folder in the same directory as the script.
2. Add `.txt` or `.m3u` files with one URL per line:

   ```txt
   # My Favorite Songs
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
   https://youtu.be/jNQXAC9IVRw
   ```

3. Run the script:

   ```sh
   python yt_audio_player.py --list
   ```

4. Select a file from the menu.

**Playlist Features:**

- **Sequential playback:** URLs are played in order (or shuffled if you use `--shuffle` or `--shuffle-all`).
- **Playlist expansion:** If a line contains a playlist URL, it expands into all its videos and plays them in sequence.
- **User controls (unless `--auto` is used):** During playback, press `n` for next, `r` to replay, `q` to quit.
- **Respects cache/pipe mode:** Uses your configured `PlaybackMethod` from `config.json`.

**Advanced shuffle options:**

- `--shuffle`: Shuffles only the top-level file lines (preserves playlist order within each expanded playlist).

  ```sh
  python yt_audio_player.py --list --shuffle
  ```

- `--shuffle-all`: Expands ALL playlists first, then shuffles the entire flattened list of videos.

  ```sh
  python yt_audio_player.py --list --shuffle-all
  ```

**Auto-advance mode:**

- `--auto`: Non-interactive mode—auto-advances through all tracks without prompting for input. Perfect for unattended playback or scripting.

  ```sh
  python yt_audio_player.py --list --auto
  ```

**Combined examples:**

```sh
# Shuffle all videos across all playlists, then auto-advance
python yt_audio_player.py --list --shuffle-all --auto

# Video mode with shuffled playlists
python yt_audio_player.py --list --shuffle-all --video
```

## 🚀 Power-User Guide

### Reliability & System Integration

**Windows Sleep Prevention:**

- On Windows systems, the script automatically prevents your PC from entering sleep mode while media is playing.
- This is especially useful during long gaming sessions or overnight listening sessions.
- The script gracefully restores sleep settings when it exits.

**Crash Detection & Recovery:**

- If the script exits unexpectedly (power loss, crash, force-kill), it stores the active playback state in `logs/player_state.json`.
- On the next run, the script automatically detects this state, cleans up any lingering player processes, and resumes normally.
- This ensures no stray `ffplay` or `mpv` processes are left behind.

**Graceful Shutdown:**

- The script handles `Ctrl+C` and system termination signals (`SIGTERM`) properly.
- All player processes are terminated cleanly, state is cleared, and system settings (like sleep mode) are restored.
- Uses `atexit` hooks to ensure cleanup happens even in unexpected exit scenarios.

### Command-Line Flags

- `--video`: Enables video mode, which uses `mpv` for playback.
- `--debug`: Enables verbose logging to the console and `logs/player.log`.
- `--force-cache-refresh`: Forces re-download of a track, even if it exists in the cache.
- `--update-yt-dlp`: Checks for and attempts to install the latest version of `yt-dlp`.
- `--offline`: Immediately starts playing all tracks from the local cache in shuffle mode.
- `--list`: Show and play from playlist files stored in `./playlists` (one URL per line).
- `--shuffle`: Shuffle the top-level lines of a playlist file (only works with `--list`).
- `--shuffle-all`: Expand all playlists and shuffle the entire flattened list of videos (only works with `--list`).
- `--auto`: Non-interactive auto-advance mode; skips all user prompts (only works with `--list`).

### Interactive Commands

At the `YouTube>` prompt, you can use these special commands:

- `history`: Opens the interactive history viewer.
- `offline`: Starts offline playback from your cache.
- `config`: Displays the current configuration from `config.json` and prompts to edit it.
- `exit` or `quit`: Exits the player.

### Playback Controls

- **Playlist/Offline Mode:** `[n]`ext, `[r]`eplay, `[p]`ause/resume (offline only), `[q]`uit to main menu.
- **Single Track:** `[r]`eplay, `[q]`uit to main menu.

### History Viewer Commands

- `n` / `p`: Next / previous page.
- `v<num>`: View the raw JSON data for an entry (e.g., `v3`).
- `f type=<type>`: Filter by type (`single`, `playlist_entry`).
- `s <term>`: Search titles for a specific term.
- `export [csv|json]`: Export the current view to a file.
- `clear`: Deletes all history (requires confirmation).
- `help`: Shows available commands.

## ⚙️ Configuration (`config.json`)

The script automatically creates `config.json` on first run. You can edit it directly or use the `config` interactive command.

- `PlaybackMethod`: `"pipe"` or `"cache"`. Determines if you stream directly or download first.
- `CacheDir`: The folder where cached tracks are stored (default: `"cache"`).
- `CacheMaxFiles`: The maximum number of files to keep in the cache before deleting the oldest.
- `SearchLimit`: Number of results to show in search (default: 10).
- `ForceCacheRefresh`: If `true`, will always re-download files instead of using the cache.
- `Debug`: Set to `true` for verbose logging.

## 💡 Pro Tips

- Use `cookies.txt` for private, region-locked, or age-restricted content.
- If you get errors, check `logs/player.log` for full debug info (especially after running with `--debug`).
- For quick, one-off plays without the script's features, you can use `yt-dlp` and `ffplay` directly:

  ```sh
  # Stream a single YouTube video
  yt-dlp -f bestaudio -o - "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" | ffplay -i - -nodisp -autoexit
  ```

## 🦾 Contributing

Pull requests, issues, and feature ideas are welcome! This project is designed to be hacked, forked, and improved.

## 🏆 The Bottom Line

**YT CMD Player** is the *last* YouTube tool you’ll ever need. Fast, light, reliable, and fun. Try it—you’ll never go back!

---

*Disclaimer: All exaggerations are for fun! This project is real, but the hype is just to make you smile. Use responsibly, and don’t actually try to run it on a toaster. Or do, and let us know what happens!*

*Made with ❤️ and 🤖 for music lovers, productivity nerds, and anyone who hates bloatware.
