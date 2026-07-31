# Web Media Extractor

This is a Python tool that automates a headless browser to open a webpage, monitor network traffic, and capture the raw media URLs (such as `.mp4`, `.m3u8`, or other video streams) from video players. It handles complicated video hosts that require clicking, use iframes, or don't explicitly show file extensions.

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

You can run the script from the terminal. It features an interactive menu allowing you to choose between processing a single URL or processing a bulk list of URLs from a text file.

```bash
python downloader.py
```

### Menu Options

**1. Single URL**
- The script will ask you to input a single webpage URL.
- It will open the page, attempt to trigger the video, and print the raw media URL to your terminal.

**2. Bulk URL (dari file)**
- The script will ask for the path to a text file (e.g., `list_url.txt`).
- Your text file should contain one URL per line.
- The script will process each URL sequentially and save the results into a file named `extracted_urls.txt` in the same directory.
