# Simple Audio Visualizer Video Generator
A Python script that generates music videos with audio visualizations from MP3/WAV files and static images. Creates videos with animated waveforms or frequency spectrum bars overlayed on your cover art.

Requirements
Python 3.7+
FFmpeg installed and available in system PATH
Python packages: ffmpeg-python (optional, script uses subprocess)

Install standalone ffmpeg for you OS before script use

Windows 10\11:
```bat
winget install Gyan.FFmpeg
```
## File Naming Convention
For automatic image matching, use identical names:

input/
├── song-name.mp3
├── song-name.jpg      ← matches automatically
├── another-track.mp3
└── cover.jpg          ← fallback default image

### License
MIT License — feel free to use for personal or commercial projects.
