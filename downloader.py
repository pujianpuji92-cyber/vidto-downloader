#!/usr/bin/env python3
import sys
import time
import os
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright, TimeoutError

def extract_media_url(target_url, timeout=30):
    """
    Automates a browser to extract the underlying media URL (.mp4, .m3u8, etc) from a webpage.
    """
    print(f"[*] Analyzing: {target_url} (Timeout: {timeout}s)")
    found_media_url = None

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
            nonlocal found_media_url
            if found_media_url: return

            url = request.url.lower()
            if is_analytics_url(url): return

            if ".mp4" in url or ".m3u8" in url or ("overfetch.video" in url and "http" in url):
                found_media_url = request.url
                print(f"[+] Found media URL via Request: {found_media_url}")

        def handle_response(response):
            nonlocal found_media_url
            if found_media_url: return

            try:
                url = response.url.lower()
                if is_analytics_url(url): return

                content_type = response.headers.get("content-type", "").lower()
                if "video/" in content_type or "application/x-mpegurl" in content_type:
                    found_media_url = response.url
                    print(f"[+] Found media URL via Content-Type ({content_type}): {found_media_url}")
            except Exception:
                pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
            except TimeoutError:
                pass # Continue even if it times out

            iframe_element = None
            try:
                iframe_element = page.wait_for_selector("iframe", state="attached", timeout=5000)
            except:
                pass

            if iframe_element:
                iframe_src = iframe_element.get_attribute("src")
                if iframe_src:
                    full_iframe_url = urljoin(target_url, iframe_src)

                    page.set_extra_http_headers({"Referer": target_url})
                    try:
                        page.goto(full_iframe_url, wait_until="domcontentloaded", timeout=15000)
                    except TimeoutError:
                        pass

            start_time = time.time()
            click_attempts = 0

            while time.time() - start_time < timeout:
                if found_media_url:
                    break

                if click_attempts < 15:
                    try:
                        page.mouse.click(page.viewport_size['width'] / 2, page.viewport_size['height'] / 2)

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

    return found_media_url

def main():
    print("========================================")
    print("       Media URL Extractor Tool         ")
    print("========================================")
    print("1. Single URL")
    print("2. Bulk URL (dari file)")
    print("0. Keluar")
    print("========================================")

    try:
        pilihan = input("Pilih menu (0-2): ").strip()
    except KeyboardInterrupt:
        print("\nKeluar...")
        sys.exit(0)

    output_file = "extracted_urls.txt"

    if pilihan == '1':
        url = input("Masukkan URL target: ").strip()
        if not url:
            print("URL tidak valid.")
            return

        result = extract_media_url(url)
        if result:
            print(f"\n[HASIL] {result}")
            with open(output_file, 'a') as out_f:
                out_f.write(f"{result}\n")
            print(f"[*] Hasil telah ditambahkan ke dalam file '{output_file}'\n")
        else:
            print(f"\n[-] {url} -> GAGAL\n")
            with open(output_file, 'a') as out_f:
                out_f.write(f"{url} -> GAGAL\n")

    elif pilihan == '2':
        filepath = input("Masukkan path ke file teks (contoh: list_url.txt): ").strip()
        if not os.path.exists(filepath):
            print(f"File '{filepath}' tidak ditemukan.")
            return

        with open(filepath, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]

        if not urls:
            print("File kosong atau tidak berisi URL yang valid.")
            return

        print(f"Ditemukan {len(urls)} URL untuk diproses.")
        print(f"Hasil ekstraksi akan disimpan ke: {output_file}\n")

        with open(output_file, 'a') as out_f:
            for i, url in enumerate(urls, 1):
                print(f"\n--- Memproses URL {i}/{len(urls)} ---")
                result = extract_media_url(url)
                if result:
                    out_f.write(f"{result}\n")
                    print(f"[HASIL] {result}")
                else:
                    out_f.write(f"{url} -> GAGAL\n")
                    print(f"[-] {url} -> GAGAL")

        print(f"\nProses selesai. Hasil tersimpan di '{output_file}'\n")

    elif pilihan == '0':
        print("Keluar...")
        sys.exit(0)
    else:
        print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()
