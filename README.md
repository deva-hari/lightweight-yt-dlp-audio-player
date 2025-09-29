# 🎵 YT Audio Player: The Ultimate Lightweight YouTube Audio Experience

## 🚀 What is this?

**YT Audio Player** is the *fastest*, *lightest*, and *most reliable* YouTube audio player for Windows (and beyond)! It lets you search, browse, and stream YouTube audio with near-zero CPU/RAM usage. No temp files, no bloat, no drama—just pure, instant music and talk, even on ancient laptops!

## ✨ Features That Will Blow Your Mind

- **Blazing Fast Search:** Type a query, get the top 10 results with titles, channels, and durations in a flash!
- **Playlist Power:** Paste a playlist link and play every track, skipping with a single keypress. See what’s playing, always!
- **Direct Link Streaming:** Paste any YouTube link and it just works. No questions asked.
- **Interactive Selection:** Pick your favorite from search results—no more guessing!
- **Skip & Control:** Press `n` to skip to the next song, or `Ctrl+C` to instantly return to the main menu.
- **Cookies.txt Support:** Got region-locked or age-restricted content? Drop your `cookies.txt` in the folder and you’re in!
- **Zero Temp Files:** Streams audio directly—no disk clutter, ever.
- **Minimal Logging:** Only what you want—toggle debug/info logs for easy troubleshooting.
- **Rock-Solid Stability:** Handles errors, bad links, and weird YouTube quirks with grace.
- **Runs on Potatoes:** Designed for low-resource systems. 8GB RAM? Old CPU? No problem!

## 🛠️ Requirements

- **Python 3.x** (Windows-focused, but works on other platforms with minor tweaks)
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) (must be in your PATH)
- [`ffplay`](https://ffmpeg.org/ffplay.html) (from FFmpeg, must be in your PATH)
- *(Optional)* `cookies.txt` for restricted content

## 🏁 How to Use

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

## 🎹 Usage

- **Search:** Type a search query, see results, pick a number, and listen!
- **Playlist:** Paste a playlist link, play all tracks, skip with `n`, exit with `Ctrl+C`.
- **Direct Link:** Paste a YouTube video link, and it streams instantly.
- **Debugging:** Set `LOG_ENABLED = True` in the script for detailed logs in `yt_audio_player.log`.

## 🧠 Why is this the best?

- **No GUI, no bloat, no waiting.**
- **Handles playlists, searches, and direct links with equal ease.**
- **Works even when your PC is running a game or heavy software.**
- **No temp files, no disk writes, no mess.**
- **Debugging is a breeze with toggleable logs.**
- **Code is clean, modular, and commented for easy hacking.**

## 💡 Pro Tips

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

## 🦾 Contributing

Pull requests, issues, and feature ideas are welcome! This project is designed to be hacked, forked, and improved.

## 🏆 The Bottom Line

**YT Audio Player** is the *last* YouTube audio tool you’ll ever need. Fast, light, reliable, and fun. Try it—you’ll never go back!

---

*Made with ❤️ for music lovers, productivity nerds, and anyone who hates bloatware.*
