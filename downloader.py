#!/usr/bin/env python3
import argparse
import sys
import time
import subprocess
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright, TimeoutError

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
    parser = argparse.ArgumentParser(description="Extract and download media from a webpage.")
    parser.add_argument("url", help="The URL of the webpage to analyze.")
    parser.add_argument("-o", "--output", help="Optional output filename template (e.g., video.mp4).")
    parser.add_argument("--timeout", type=int, default=30, help="Seconds to wait for a media request (default: 30).")

    args = parser.parse_args()

    target_url = args.url
    found_media_url = None
    found_referer = None

    print(f"[*] Navigating to {target_url}...")
    print(f"[*] Waiting up to {args.timeout} seconds for media URLs to appear...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Using a mobile UA avoids many complex anti-bot systems on streaming sites
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
            viewport={"width": 390, "height": 844},
            is_mobile=True
        )
        page = context.new_page()

        def is_analytics_url(url):
            return "google-analytics" in url or "doubleclick" in url or "google" in url or "googletagmanager" in url

        def handle_request(request):
            nonlocal found_media_url, found_referer
            if found_media_url: return

            url = request.url.lower()
            if is_analytics_url(url): return

            # Look for common video extensions or known video host domains
            if ".mp4" in url or ".m3u8" in url or ("overfetch.video" in url and "http" in url):
                found_media_url = request.url
                found_referer = request.headers.get("referer", target_url)
                print(f"[+] Found media URL via Request: {found_media_url}")

        def handle_response(response):
            nonlocal found_media_url, found_referer
            if found_media_url: return

            try:
                url = response.url.lower()
                if is_analytics_url(url): return

                content_type = response.headers.get("content-type", "").lower()
                # Check headers for video if url has no extension
                if "video/" in content_type or "application/x-mpegurl" in content_type:
                    found_media_url = response.url
                    found_referer = response.request.headers.get("referer", target_url)
                    print(f"[+] Found media URL via Content-Type ({content_type}): {found_media_url}")
            except Exception:
                pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
            except TimeoutError:
                print("[*] Main page load timed out. Continuing...")

            # Step 1: Detect iframe and navigate to it explicitly, keeping the same context
            iframe_element = None
            try:
                iframe_element = page.wait_for_selector("iframe", state="attached", timeout=5000)
            except:
                pass

            if iframe_element:
                iframe_src = iframe_element.get_attribute("src")
                if iframe_src:
                    full_iframe_url = urljoin(target_url, iframe_src)
                    print(f"[*] Found iframe, navigating directly to player: {full_iframe_url}")

                    page.set_extra_http_headers({"Referer": target_url})
                    try:
                        page.goto(full_iframe_url, wait_until="domcontentloaded", timeout=15000)
                    except TimeoutError:
                        print("[*] Iframe load timed out. Continuing...")

            # Step 2: Continuously attempt to click the player
            start_time = time.time()
            click_attempts = 0

            while time.time() - start_time < args.timeout:
                if found_media_url:
                    break

                if click_attempts < 15:
                    try:
                        # Click the center of the viewport to bypass overlays
                        page.mouse.click(page.viewport_size['width'] / 2, page.viewport_size['height'] / 2)

                        # Use Javascript to forcefully trigger playback
                        for frame in page.frames:
                            try:
                                frame.evaluate('''() => {
                                    let v = document.querySelector('video');
                                    if (v) { v.play().catch(e => {}); v.click(); }
                                    let p = document.querySelector('.play-button');
                                    if (p) p.click();
                                }''')
                            except:
                                pass

                        click_attempts += 1
                    except:
                        pass

                page.wait_for_timeout(1000)

        except Exception as e:
            print(f"[-] Error navigating to page: {e}")
        finally:
            browser.close()

    if found_media_url:
        download_media(found_media_url, found_referer, args.output)
    else:
        print(f"[-] No media URL was found within {args.timeout} seconds.")

if __name__ == "__main__":
    main()
