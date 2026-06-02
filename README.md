# Lyrica — 3D Vinyl Lyrics Display
......
A dark, cinematic desktop lyrics display app built in Python.

## Features
- Spinning 3D vinyl disc with groove rings and specular highlight
- Auto-fetched synced lyrics from lrclib.net (free, no API key)
- Cinematic lyrics typography — active line is huge, past/future lines fade
- Live waveform bar at the bottom
- Album art extracted from MP3/FLAC metadata
- Dark editorial theme — red accent on black

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## Dependencies
- PyQt6 — window and UI
- pygame — audio playback
- mutagen — MP3/FLAC metadata + album art
- requests — fetch lyrics from lrclib.net

## Usage
1. Click the folder icon in the sidebar
2. Select any MP3, FLAC, WAV, or OGG file
3. Lyrics are fetched automatically
4. Vinyl spins while playing, slows to a stop on pause

## Notes
- Lyrics sync accuracy depends on lrclib.net having the track
- For best results use MP3 files with proper ID3 tags (title + artist)
- Works on Windows, macOS, Linux
