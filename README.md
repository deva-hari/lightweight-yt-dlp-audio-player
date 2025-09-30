
# 🎵 YT Audio Player: The Ultimate Lightweight YouTube Audio Experience

## 🤩 Why settle for less? Behold, the Most Ridiculously Lightweight YouTube Audio Player Ever

Are you a gamer who wants to blast your favorite YouTube playlist while fragging noobs, but your browser eats more RAM than Chrome on a caffeine binge? Tired of apps that turn your potato PC into a baked potato? Want to listen to music while running a game, a video call, AND 37 Chrome tabs? **This script LAUGHS at your resource limits!**

**YT Audio Player** is so light, you’ll wonder if it’s even running. It’s like the ninja of audio players—silent, invisible, and deadly (to bloatware). No temp files, no drama, no nonsense. Just pure, instant music, even on a 10-year-old laptop that wheezes when you open Notepad.

## 🚀 What is this?

**YT Audio Player** is the *fastest*, *lightest*, and *most reliable* YouTube audio player for Windows (and beyond)! It lets you search, browse, and stream YouTube audio with near-zero CPU/RAM usage. No temp files, no bloat, no drama—just pure, instant music and talk, even on ancient laptops!

## ✨ Features That Will Make You Question Reality

- **Blazing Fast Search:** Type a query, get the top 10 results with titles, channels, and durations before you can say "yt-dlp"!
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
