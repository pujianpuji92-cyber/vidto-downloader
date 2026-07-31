#!/usr/bin/env python3
import argparse
import sys
import time
import subprocess
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright

def download_media(media_url, referer=None, output_name=None):
    """Downloads media using yt-dlp."""
    print(f"\n[+] Downloading media from: {media_url}")

    cmd = ["yt-dlp", media_url]
    if referer:
        cmd.extend(["--add-header", f"Referer:{referer}"])
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
    parser.add_argument("--timeout", type=int, default=30, help="Seconds to wait for a media request (default: 30).")

    args = parser.parse_args()

    target_url = args.url
    found_media_url = None
    found_referer = None

    print(f"[*] Navigating to {target_url}...")
    print(f"[*] Waiting up to {args.timeout} seconds for media URLs (.mp4, .m3u8) to appear...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def handle_request(request):
            nonlocal found_media_url, found_referer
            if found_media_url:
                return # Already found one

            url = request.url.lower()
            if ".mp4" in url or ".m3u8" in url:
                found_media_url = request.url
                found_referer = request.headers.get("referer", target_url)
                print(f"[+] Found media URL: {found_media_url}")

        page.on("request", handle_request)

        try:
            page.goto(target_url, wait_until="domcontentloaded")

            # 1. First, check if there is an iframe. Some video hosts hide the player inside an iframe.
            try:
                # Wait briefly to see if an iframe appears
                iframe_element = page.wait_for_selector("iframe", state="attached", timeout=3000)
                if iframe_element:
                    iframe_src = iframe_element.get_attribute("src")
                    if iframe_src:
                        full_iframe_url = urljoin(target_url, iframe_src)
                        print(f"[*] Found iframe, navigating directly to player: {full_iframe_url}")
                        page.goto(full_iframe_url, wait_until="domcontentloaded")
            except Exception:
                # No iframe found within timeout, proceed with current page
                pass

            # 2. Wait a bit for the player to initialize
            page.wait_for_timeout(2000)

            # 3. Try clicking on common video elements
            try:
                page.click("video", timeout=2000)
            except:
                pass

            try:
                page.click(".play-button", timeout=2000)
            except:
                pass

            # 4. If nothing else works, try clicking the center of the screen multiple times.
            # This is specifically useful for bypassing popunders that require a click before video plays.
            start_time = time.time()
            click_attempts = 0

            while time.time() - start_time < args.timeout:
                if found_media_url:
                    break

                # Attempt to click the center of the viewport every second for the first 5 seconds
                if click_attempts < 5:
                    try:
                        page.mouse.click(page.viewport_size['width'] / 2, page.viewport_size['height'] / 2)
                        click_attempts += 1
                    except:
                        pass

                page.wait_for_timeout(1000)  # Wait 1s and check again

        except Exception as e:
            print(f"[-] Error navigating to page: {e}")
        finally:
            browser.close()

    if found_media_url:
        download_media(found_media_url, found_referer, args.output)
    else:
        print(f"[-] No media URL (.mp4, .m3u8) was found within {args.timeout} seconds.")

if __name__ == "__main__":
    main()
