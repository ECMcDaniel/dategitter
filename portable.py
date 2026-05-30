import io
import re
import os
import subprocess
import argparse
import csv
from pathlib import Path
from google.cloud import vision
from google.oauth2 import service_account

def get_vision_client():
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    # 1. Use an explicit credentials path when provided.
    if credentials_path:
        if os.path.exists(credentials_path):
            print("Using GOOGLE_APPLICATION_CREDENTIALS environment variable.")
            creds = service_account.Credentials.from_service_account_file(credentials_path)
            return vision.ImageAnnotatorClient(credentials=creds)
        raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS was set but the file was not found: {credentials_path}")

    # 2. Fall back to a local JSON file in the working directory.
    local_key = "google_key.json"
    if os.path.exists(local_key):
        print("Using local google_key.json for authentication.")
        creds = service_account.Credentials.from_service_account_file(local_key)
        return vision.ImageAnnotatorClient(credentials=creds)

    raise RuntimeError("No Google Cloud authentication found. Set GOOGLE_APPLICATION_CREDENTIALS or place google_key.json in the working directory.")

def detect_date_and_stamp(image_path, dry_run=False):
    try:
        client = get_vision_client()
    except Exception as e:
        print(e)
        return

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        print(f"No text found in {image_path}")
        return

    full_text = texts[0].description
    print(f"Detected Text: {full_text.strip()}")
    date_pattern = re.compile(r'\b(\d{2,4})[-/ ](\d{2})[-/ ](\d{2,4})\b')
    match = date_pattern.search(full_text)

    if match:
        p1, p2, p3 = match.groups()

        def fix_year(y):
            if len(y) == 2:
                return f"19{y}" if int(y) > 70 else f"20{y}"
            return y

        groups = [p1, p2, p3]

        # Prefer a 4-digit group as the year if present
        year = None
        year_idx = None
        for i, g in enumerate(groups):
            if len(g) == 4:
                year = g
                year_idx = i
                break

        if year is None:
            # No explicit 4-digit year — assume the first group is the year (legacy behavior)
            year = fix_year(p1)
            month = p2
            day = p3
        else:
            # Remove the year and decide month/day from the remaining two groups
            rem = [g for i, g in enumerate(groups) if i != year_idx]
            a, b = rem

            def is_month(s):
                try:
                    v = int(s)
                    return 1 <= v <= 12
                except ValueError:
                    return False

            if is_month(a) and not is_month(b):
                month, day = a, b
            elif is_month(b) and not is_month(a):
                month, day = b, a
            else:
                # Ambiguous (both look like months or neither does) — keep original order
                month, day = rem[0], rem[1]

            # Ensure year is 4 digits (if it was 2-digit, normalize)
            if len(year) == 2:
                year = fix_year(year)

        # Zero-pad month/day
        month = str(int(month)).zfill(2)
        day = str(int(day)).zfill(2)

        exif_date = f"{year}:{month}:{day} 12:00:00"
        print(f"Parsed Date for EXIF: {exif_date}")

        # Prepare ExifTool command
        exif_cmd = [
            'exiftool',
            f'-DateTimeOriginal={exif_date}',
            f'-CreateDate={exif_date}',
            '-overwrite_original',
            image_path,
        ]

        if dry_run:
            # Write a CSV row with proposed change instead of invoking exiftool
            csv_path = Path("dry_run_proposed_changes.csv")
            write_header = not csv_path.exists()
            try:
                with csv_path.open("a", newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    if write_header:
                        writer.writerow(["image_path", "detected_text", "exif_date", "exiftool_command"])
                    writer.writerow([image_path, full_text.strip(), exif_date, ' '.join(exif_cmd)])
                print(f"Dry run: wrote proposal to {csv_path}")
            except Exception as e:
                print(f"Failed to write dry-run CSV: {e}")
            return

        try:
            # Running exiftool inside the container
            subprocess.run(exif_cmd, check=True)
            print(f"Successfully updated {image_path} to {exif_date}")
        except subprocess.CalledProcessError as e:
            print(f"ExifTool failed: {e}")
    else:
        print(f"No valid date found in {image_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect dates in images and write EXIF DateTimeOriginal/CreateDate")
    parser.add_argument("--photos", default=os.getenv("PHOTOS_DIR", "/photos"), help="Directory containing photos (defaults to PHOTOS_DIR or /photos)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write EXIF, just print the exiftool command")
    args = parser.parse_args()

    photo_dir = args.photos
    if os.path.exists(photo_dir):
        for root, dirs, files in os.walk(photo_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    full_path = os.path.join(root, file)
                    detect_date_and_stamp(full_path, dry_run=args.dry_run)
    else:
        print(f"{photo_dir} directory not found. Did you mount your volume or provide the correct path?")