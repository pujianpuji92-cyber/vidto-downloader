# Web Media Downloader

This is a Python tool that automates a headless browser to open a webpage, monitor network traffic, and capture media URLs (such as `.mp4` and `.m3u8`). Once a media URL is found, it automatically downloads it using `yt-dlp`.

## Prerequisites

- Python 3.7+
- `pip` (Python package manager)

## Installation

1. Clone or download this repository.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Install the Playwright browsers:

```bash
playwright install
```

## Usage

You can run the script from the terminal.

```bash
python downloader.py <URL> [OPTIONS]
```

### Examples

**Basic usage:**
Capture and download media from a target URL:
```bash
python downloader.py "https://example.com/video-page"
```

**Specify output filename:**
Save the downloaded video with a specific filename:
```bash
python downloader.py "https://example.com/video-page" -o my_video.mp4
```

**Increase the timeout:**
If a page loads slowly or requires user interaction before playing, you can increase the timeout (in seconds):
```bash
python downloader.py "https://example.com/video-page" --timeout 30
```

### Help

To view all available options, run:

```bash
python downloader.py -h
```
