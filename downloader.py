#!/usr/bin/env python3
import argparse
import sys
import time
import subprocess
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def download_media(media_url, output_name=None):
    """Downloads media using yt-dlp."""
    print(f"\n[+] Downloading media from: {media_url}")

    cmd = ["yt-dlp", media_url]
    if output_name:
        cmd.extend(["-o", output_name])

    try:
        subprocess.run(cmd, check=True)
        print("\n[+] Download completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n[-] Error downloading media: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Extract and download media (mp4, m3u8) from a webpage.")
    parser.add_argument("url", help="The URL of the webpage to analyze.")
    parser.add_argument("-o", "--output", help="Optional output filename template (e.g., video.mp4).")
    parser.add_argument("--timeout", type=int, default=15, help="Seconds to wait for a media request (default: 15).")

    args = parser.parse_args()

    target_url = args.url
    found_media_url = None

    print(f"[*] Navigating to {target_url}...")
    print(f"[*] Waiting up to {args.timeout} seconds for media URLs (.mp4, .m3u8) to appear...")

    with sync_playwright() as p:
        # We use Firefox or Chromium. Often Chromium headless might be detected, so sometimes we might need additional stealth, but let's stick to standard Chromium for now.
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def handle_request(request):
            nonlocal found_media_url
            if found_media_url:
                return # Already found one

            url = request.url.lower()
            if ".mp4" in url or ".m3u8" in url:
                found_media_url = request.url
                print(f"[+] Found media URL: {found_media_url}")

        page.on("request", handle_request)

        try:
            page.goto(target_url, wait_until="domcontentloaded")
            # We often need to trigger a 'play' event if there's an obvious video element,
            # but wait_for_timeout works as a generic approach if autoplay is on or if it loads streams immediately.

            # Let's also try to click on anything that looks like a play button just in case.
            # (Best effort approach)
            try:
                page.click("video", timeout=3000)
            except:
                pass

            try:
                page.click(".play-button", timeout=3000)
            except:
                pass

            start_time = time.time()
            while time.time() - start_time < args.timeout:
                if found_media_url:
                    break
                page.wait_for_timeout(500)  # Wait 500ms and check again

        except Exception as e:
            print(f"[-] Error navigating to page: {e}")
        finally:
            browser.close()

    if found_media_url:
        download_media(found_media_url, args.output)
    else:
        print(f"[-] No media URL (.mp4, .m3u8) was found within {args.timeout} seconds.")

if __name__ == "__main__":
    main()
