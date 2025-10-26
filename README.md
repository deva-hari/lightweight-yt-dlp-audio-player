
# 🎵 YT Audio Player: The Ultimate Lightweight YouTube Audio Experience

## 🤩 Why settle for less? Behold, the Most Ridiculously Lightweight YouTube Audio Player Ever

Are you a gamer who wants to blast your favorite YouTube playlist while fragging noobs, but your browser eats more RAM than Chrome on a caffeine binge? Tired of apps that turn your potato PC into a baked potato? Want to listen to music while running a game, a video call, AND 37 Chrome tabs? **This script LAUGHS at your resource limits!**

**YT Audio Player** is so light, you’ll wonder if it’s even running. It’s like the ninja of audio players—silent, invisible, and deadly (to bloatware). No temp files, no drama, no nonsense. Just pure, instant music, even on a 10-year-old laptop that wheezes when you open Notepad.

## 🚀 What is this?

**YT Audio Player** is the *fastest*, *lightest*, and *most reliable* YouTube audio player for Windows (and beyond)! It lets you search, browse, and stream YouTube audio with near-zero CPU/RAM usage. No temp files, no bloat, no drama—just pure, instant music and talk, even on ancient laptops!

## ✨ Features That Will Make You Question Reality

- **Blazing Fast Search:** Type a query, get the top 10 results with titles, channels, and durations before you can say "yt-dlp"! (Not Really!😉)
- **Playlist Power:** Paste a playlist link and play every track, skipping with a single keypress. See what’s playing, always! (Your friends will think you’re a wizard.)
- **Direct Link Streaming:** Paste any YouTube link and it just works. No questions asked. No judgment.
- **Interactive Selection:** Pick your favorite from search results—no more guessing! (No more "wrong song" disasters.)
- **Skip & Control:** Press `n` to skip to the next song, or `Ctrl+C` to instantly return to the main menu. (Because you’re in control, always.)
- **Cookies.txt Support:** Got region-locked or age-restricted content? Drop your `cookies.txt` in the folder and you’re in! (Like a VIP pass for YouTube.)
- **Zero Temp Files:** Streams audio directly—no disk clutter, ever. (Marie Kondo would be proud.)
- **Minimal Logging:** Only what you want—toggle debug/info logs for easy troubleshooting. (Or just ignore them, we won’t tell.)
- **Rock-Solid Stability:** Handles errors, bad links, and weird YouTube quirks with grace. (It’s basically unbreakable.)
- **Runs on Potatoes:** Designed for low-resource systems. 8GB RAM? Old CPU? No problem! (Heck, it probably runs on a toaster.)

## 🛠️ Requirements (Spoiler: You Already Have Them)

- **Python 3.x** (Windows-focused, but works on other platforms with minor tweaks)
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) (must be in your PATH)
- [`ffplay`](https://ffmpeg.org/ffplay.html) (from FFmpeg, must be in your PATH)
- *(Optional)* `cookies.txt` for restricted content

## 🏁 How to Use (So Easy, Your Grandma Could Do It)

1. **Install Python 3.x** if you don’t have it.
2. **Install yt-dlp:**

   ```sh
   pip install -U yt-dlp
   ```

3. **Install FFmpeg:**
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your PATH.
4. *(Optional)* Place your `cookies.txt` in the same folder as the script.
5. **Run the script:**

   ```sh
   python yt_audio_player.py
   ```

6. **Enjoy!**

7. **Marvel at how little RAM and CPU you’re using.**

## 🎹 Usage Examples

### Search and pick interactively

```sh
python yt_audio_player.py
YouTube> lo-fi beats
```

### Play a single video

```sh
python yt_audio_player.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Play an entire playlist

```sh
python yt_audio_player.py "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
```

### Debug mode (verbose logs + ffplay output)

```sh
python yt_audio_player.py --debug "chill vibes"
```

#### Controls

- **Playlist:** `[n]ext`, `[r]eplay`, `[q]uit`
- **Single video:** `[q]uit`

### Interactive commands & features (detailed)

While running the script in interactive mode (`python yt_audio_player.py`) you can use the following commands and features:

- Playback controls:
  - `n` / `r` / `q` during playback
  - Playlist: press `n` to skip to the next track, `r` to replay the current track, or `q` to return to the main menu.
  - Single video: press `r` to replay or `q` to quit playback.

- `history` (hidden interactive command): opens the paginated history viewer
  - Defaults: 10 entries per page, numbered 0–9 on each page.
  - Display fields: serial (0–9), type, date/time, truncated title, URL, persistent play count.

- History viewer commands
  - `n` / `p` — next / previous page
  - `v<num>` — view raw JSON for the entry at index `<num>` on the page (e.g. `v3`)
  - `f type=<type>` — filter by entry type (e.g. `f type=single`, `f type=playlist_entry`)
  - `s <term>` — search/filter by title substring (case-insensitive)
  - `export csv` / `export json` — export the currently filtered list to `logs/history_export.csv` or `logs/history_export.json`
  - `clear` — delete all history (prompted confirmation required; type `YES` to proceed)
  - `help` — show the viewer commands

- `offline` (hidden): play cached audio files in your cache directory in shuffled order
  - Usage: type `offline` at the `YouTube>` prompt.
  - Behavior: scans `CacheDir` (default `cache`) for downloaded audio files, shuffles them, and plays them one-by-one.
  - Controls while playing: `n` = next, `p` = pause/resume (best-effort), `q` = quit offline playback.
  - Notes: this works only when you have cached tracks (i.e., `PlaybackMethod` = `cache` or you've previously downloaded tracks). Pause/resume uses ffplay's `p` toggle when available; on POSIX systems a fallback suspend/resume is used if needed.

- What is stored in history
  - Each history entry is a JSON object with fields including: `type` (single|playlist_entry), `track_url`, `playlist_url` (when applicable), `title`, `timestamp` (unix epoch), and `play_count` (persistent counter incremented per-track URL).
  - Files: `logs/history.json` (entries) and `logs/history_index.json` (persistent play count index).

### Playback behavior

- Piped streaming
  - The player streams audio by piping `yt-dlp` output directly into `ffplay`, matching this command-line pattern:

      ```sh
      yt-dlp -f bestaudio -o - "<query-or-url>" | ffplay -i - -nodisp -autoexit
      ```

- Elapsed / total time display
  - While a track is playing the script displays elapsed seconds in the terminal and, when available, the track's total duration (queried via `yt-dlp` metadata).
  - When running with `--debug`, ffplay and debug logs are shown and may interleave with the elapsed-time line.

### Playback modes (new)

Yes, we added options — because sometimes the internet is a diva.

- pipe (default): streams directly from `yt-dlp` into `ffplay` (no disk writes). Fast, lean, glorious.
- cache: downloads tracks into a local cache directory first, then plays from disk. Useful when your network is flaky or your ISP is mood-swinging.

Config and CLI options you might care about:

- `PlaybackMethod` in `config.json`: set to `pipe` or `cache`.
- `CacheDir` in `config.json`: directory used for cached tracks (default: `cache`).
- `CacheMaxFiles` in `config.json`: how many cached items to keep before pruning.
- `--force-cache-refresh` CLI flag: re-download a track even if a cached copy exists (great for when YouTube updates a video or your cache is possessed).

When using `cache` mode the script will:

- download into `CacheDir` with retries and exponential backoff
- prune the oldest cached files when `CacheMaxFiles` is exceeded
- write informative logs about cache hits and downloads (see logs/player.log)

Use cache mode when your internet acts like it’s on dial-up again. Use pipe mode when you want minimal disk activity and the network behaves.

### Debugging and logs

- Run with `--debug` to enable verbose logging (to console and `logs/player.log`) and to allow ffplay output to appear for troubleshooting:

```sh
python yt_audio_player.py --debug "chill vibes"
```

- Log locations
  - Player log: `logs/player.log`
  - History entries: `logs/history.json`
  - History index (play counts): `logs/history_index.json`
  - History exports: `logs/history_export.csv` / `logs/history_export.json`

Note on console vs file logging

- By default the script shows INFO-level messages on the console and writes INFO+ to the log file. This means normal operational events (what's playing, playlist boundaries, cache hits, etc.) are visible on your terminal without enabling debug mode.
- If you need full diagnostic output (stack traces, verbose yt-dlp details, ffplay interleaved output), run with `--debug` which raises both console and file verbosity to DEBUG.

### Files & configuration

- `config.json` — small config file (SearchLimit, Debug, CookiesFile). Defaults are created automatically when missing.
- `cookies.txt` — optional cookies file you can drop into the script folder for age/region-restricted content.

### Exporting & clearing history

- Export: from the history viewer use `export csv` or `export json` to write the currently filtered entries to `logs/history_export.csv` or `logs/history_export.json`.
- Clear: `clear` in the history viewer wipes `logs/history.json` and `logs/history_index.json` after typing `YES` to confirm.

#### Configuration

- The number of search results is set by `SearchLimit` in `config.json` (default: 10).
- Log file: `logs/player.log`
- Place `cookies.txt` in the folder for restricted content support.

#### Dependencies

- The script will auto-install `yt-dlp` and `ffmpeg` if missing (Windows: via winget, Linux: via apt/pip).

## 🧠 Why is this the best? (Let’s Get Real)

- **No GUI, no bloat, no waiting.**
- **Handles playlists, searches, and direct links with equal ease.**
- **Works even when your PC is running a game, a video call, AND a cryptocurrency miner.**
- **No temp files, no disk writes, no mess.**
- **Debugging is a breeze with toggleable logs.**
- **Code is clean, modular, and commented for easy hacking.**
- **So light, you’ll forget it’s running. (Seriously, check Task Manager. It’s barely there.)**

## 💡 Pro Tips (Because You’re a Power User Now)

- Use `cookies.txt` for private, region-locked, or age-restricted content.
- If you get errors, check `yt_audio_player.log` (if logging is enabled) for full debug info.
- You can change the number of search results by editing `SEARCH_RESULTS` in the script.
- Works great in a terminal multiplexer or as a background music tool while you work or play!
- If you don't want the hassle of keeping this script, you can directly start the player by executing the following commands:

### ▶️ Search and play the first result

```sh
yt-dlp -f bestaudio -o - "ytsearch1:lofi hip hop" | ffplay -i - -nodisp -autoexit
```

### ▶️ Stream a single YouTube video (replace the URL with your video)

```sh
yt-dlp -f bestaudio -o - "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" | ffplay -i - -nodisp -autoexit
```

### 🎶 Stream a YouTube playlist (replace the URL with your playlist)

```sh
yt-dlp -f bestaudio -o - "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID" | ffplay -i - -nodisp -autoexit
```

## 🦾 Contributing (Join the Cool Kids)

Pull requests, issues, and feature ideas are welcome! This project is designed to be hacked, forked, and improved.

## 🏆 The Bottom Line (The Sales Pitch)

**YT Audio Player** is the *last* YouTube audio tool you’ll ever need. Fast, light, reliable, and fun. Try it—you’ll never go back!

---

*Disclaimer: All exaggerations are for fun! This project is real, but the hype is just to make you smile. Use responsibly, and don’t actually try to run it on a toaster. Or do, and let us know what happens!*

---

*Made with ❤️ and 🤖 for music lovers, productivity nerds, and anyone who hates bloatware.*
