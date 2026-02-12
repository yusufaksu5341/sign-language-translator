import argparse
import html
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.parse import urljoin

import requests

BASE_URL = "https://tidsozluk.aile.gov.tr"
ALPHABET = [
    "A", "B", "C", "Ç", "D", "E", "F", "G", "Ğ", "H", "I", "İ",
    "J", "K", "L", "M", "N", "O", "Ö", "P", "R", "S", "Ş", "T",
    "U", "Ü", "V", "Y", "Z"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/tr/Alfabetik/Arama/A",
}

CHUNK_SIZE = 512 * 1024
MIN_FILE_SIZE = 4 * 1024


@dataclass
class VideoEntry:
    word: str
    vid_id: str
    url: str


def sanitize_filename(filename: str) -> str:
    invalid_chars = r'<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    filename = " ".join(filename.split())
    return filename.strip(" .") or "untitled"


def decode_text(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", text)
    cleaned = html.unescape(cleaned)
    return " ".join(cleaned.split()).strip()


def extract_total_pages(page_html: str) -> int:
    matches = re.findall(r'data-p="(\d+)"', page_html)
    if not matches:
        return 1
    return max(int(value) for value in matches)


def parse_entries_from_html(page_html: str) -> list[VideoEntry]:
    item_pattern = re.compile(
        r'<div class="rezult_item row".*?</a></div>',
        re.DOTALL | re.IGNORECASE,
    )
    h3_pattern = re.compile(r"<h3[^>]*>(.*?)</h3>", re.DOTALL | re.IGNORECASE)
    src_pattern = re.compile(
        r'<source[^>]+src="([^"]+/degiske/[^"]+_cr_0\.1\.mp4)"',
        re.IGNORECASE,
    )

    entries: list[VideoEntry] = []
    for block in item_pattern.findall(page_html):
        h3_match = h3_pattern.search(block)
        if not h3_match:
            continue

        word = decode_text(h3_match.group(1))
        if not word:
            continue

        sources = src_pattern.findall(block)
        for src in sources:
            full_url = urljoin(BASE_URL, src)
            vid_match = re.search(r"/degiske/([^/_]+)_cr_0\.1\.mp4$", full_url)
            if not vid_match:
                continue
            vid_id = vid_match.group(1)
            entries.append(VideoEntry(word=word, vid_id=vid_id, url=full_url))

    return entries


def fetch_html(session: requests.Session, url: str, timeout: int, retries: int) -> str:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as error:
            last_error = error
            if attempt < retries:
                time.sleep(1.0)
    raise RuntimeError(f"HTML fetch failed: {url} ({last_error})")


def scrape_all_entries(timeout: int, retries: int) -> list[VideoEntry]:
    session = requests.Session()
    session.headers.update(HEADERS)

    seen_vid: dict[str, VideoEntry] = {}

    for index, letter in enumerate(ALPHABET, start=1):
        first_page_url = f"{BASE_URL}/tr/Alfabetik/Arama/{letter}"
        print(f"[{index}/{len(ALPHABET)}] Taraniyor: {letter}")

        first_html = fetch_html(session, first_page_url, timeout, retries)
        total_pages = extract_total_pages(first_html)
        print(f"  Sayfa sayisi: {total_pages}")

        letter_count = 0
        for page_num in range(1, total_pages + 1):
            page_url = first_page_url if page_num == 1 else f"{first_page_url}?p={page_num}"
            page_html = first_html if page_num == 1 else fetch_html(session, page_url, timeout, retries)
            page_entries = parse_entries_from_html(page_html)

            for entry in page_entries:
                if entry.vid_id not in seen_vid:
                    seen_vid[entry.vid_id] = entry
                    letter_count += 1

        print(f"  Yeni video: {letter_count}")

    session.close()
    all_entries = list(seen_vid.values())
    print(f"\nToplam benzersiz video: {len(all_entries)}")
    return all_entries


def download_one(entry: VideoEntry, output_folder: str, timeout: int, retries: int) -> tuple[bool, str, int]:
    safe_word = sanitize_filename(entry.word)
    filename = f"{safe_word}_{entry.vid_id}.mp4"
    output_path = os.path.join(output_folder, filename)
    temp_path = f"{output_path}.part"

    if os.path.exists(output_path) and os.path.getsize(output_path) >= MIN_FILE_SIZE:
        return True, filename, os.path.getsize(output_path)

    headers = dict(HEADERS)
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            with requests.get(entry.url, headers=headers, timeout=timeout, stream=True) as response:
                response.raise_for_status()

                downloaded = 0
                with open(temp_path, "wb") as file_obj:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if not chunk:
                            continue
                        file_obj.write(chunk)
                        downloaded += len(chunk)

            if downloaded < MIN_FILE_SIZE:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                last_error = RuntimeError("file too small")
                if attempt < retries:
                    time.sleep(0.8)
                    continue
                return False, filename, 0

            os.replace(temp_path, output_path)
            return True, filename, downloaded
        except Exception as error:
            last_error = error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if attempt < retries:
                time.sleep(1.0)

    print(f"  Hata ({entry.vid_id}): {last_error}")
    return False, filename, 0


def download_all(entries: list[VideoEntry], output_folder: str, workers: int, timeout: int, retries: int) -> None:
    os.makedirs(output_folder, exist_ok=True)

    success = 0
    failed = 0
    total_bytes = 0

    print(f"\nIndirme basliyor: {len(entries)} video | worker={workers}\n")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(download_one, entry, output_folder, timeout, retries): entry
            for entry in entries
        }

        for index, future in enumerate(as_completed(future_map), start=1):
            ok, filename, size = future.result()
            if ok:
                success += 1
                total_bytes += size
                print(f"[{index}/{len(entries)}] OK   {filename}")
            else:
                failed += 1
                print(f"[{index}/{len(entries)}] FAIL {filename}")

    print("\n" + "=" * 70)
    print("INDIRME OZETI")
    print("=" * 70)
    print(f"Basarili : {success}")
    print(f"Hatali   : {failed}")
    print(f"Toplam   : {len(entries)}")
    print(f"Boyut    : {total_bytes / (1024 * 1024):.2f} MB")
    print(f"Klasor   : {os.path.abspath(output_folder)}")
    print("=" * 70)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TID sozlugunden tum kelime-videolari dogrudan scrape edip indirir (mapping dosyasi kullanmaz)."
    )
    parser.add_argument("--output", default="tid_dataset", help="Indirme klasoru")
    parser.add_argument("--workers", type=int, default=8, help="Paralel indirme sayisi")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout (sn)")
    parser.add_argument("--retries", type=int, default=4, help="Yeniden deneme")
    parser.add_argument("--max-downloads", type=int, default=0, help="Test icin ilk N videoyu indir (0=tumu)")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()

    print("=" * 70)
    print("TID TAM ARSIV SCRAPER + DOWNLOADER")
    print("(kelime_mapping.json kullanilmaz)")
    print("=" * 70)

    entries = scrape_all_entries(timeout=args.timeout, retries=args.retries)
    if not entries:
        print("Hic video bulunamadi.")
        return

    if args.max_downloads > 0:
        entries = entries[:args.max_downloads]
        print(f"Test modu: {len(entries)} video indirilecek")

    download_all(
        entries=entries,
        output_folder=args.output,
        workers=max(1, args.workers),
        timeout=args.timeout,
        retries=max(1, args.retries),
    )


if __name__ == "__main__":
    main()