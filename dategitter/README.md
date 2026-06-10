# dategitter

Scans a folder of photos, reads any printed date visible in each image using Google Cloud Vision OCR, then writes the detected date into the image's EXIF metadata (`DateTimeOriginal` / `CreateDate`) using ExifTool.

Useful for digitized physical photos (e.g. scanned prints or film) where the date is stamped on the photo itself but absent from the file metadata.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A **Google Cloud service account key** ([what's this?](https://cloud.google.com/iam/docs/service-account-overview)) with the [Cloud Vision API](https://cloud.google.com/vision) enabled

## Setup

1. **Clone the repo**

   ```bash
   git clone <repo-url>
   cd dategitter
   ```

2. **Add your Google Cloud key**

   Place your service account JSON file in the project root as `google_key.json`, or set the `GOOGLE_KEY_HOST_PATH` environment variable to point to its location on your machine.

3. **Set your photos directory**

   Set the `PHOTOS_DIR_HOST_PATH` environment variable to the folder containing your photos, or edit `compose.yaml` directly.

## Usage

### Run with Docker Compose (recommended)

```bash
PHOTOS_DIR_HOST_PATH=/path/to/your/photos docker compose up
```

Or with a key at a custom path:

```bash
GOOGLE_KEY_HOST_PATH=/path/to/key.json PHOTOS_DIR_HOST_PATH=/path/to/photos docker compose up
```

The container will walk the photos directory recursively and process every `.jpg`, `.jpeg`, and `.png` file it finds.

### Dry run (preview changes without writing EXIF)

Pass `--dry-run` via the `command` override to see what would be written without modifying any files. A `dry_run_proposed_changes.csv` will be written with the detected dates and proposed ExifTool commands.

```bash
docker compose run --rm dategitter python portable.py --dry-run
```

### Run directly (without Docker)

Install dependencies and ExifTool, then:

```bash
pip install -r requirements.txt
# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
python portable.py --photos /path/to/photos
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_KEY_HOST_PATH` | `./google_key.json` | Host path to GCP service account key (Docker only) |
| `PHOTOS_DIR_HOST_PATH` | `/path/to/photos` | Host path to photo directory (Docker only) |
| `GOOGLE_APPLICATION_CREDENTIALS` | — | Path to GCP key inside the container or on the host |
| `PHOTOS_DIR` | `/photos` | Photo directory inside the container |

## How it works

1. Each image is sent to the Google Cloud Vision text detection API.
2. The returned text is scanned for a date pattern (`YYYY-MM-DD`, `MM/DD/YY`, etc.).
3. The parsed date is written to the image's EXIF fields using ExifTool (`-overwrite_original`).

## Contributing

Contributions are welcome! Open an issue or submit a pull request.

One area of interest is refactoring the OCR step to run on local hardware (e.g. Tesseract) instead of Google Cloud Vision — removing the external dependency entirely. This is planned for a future version.

## Notes

- Files are modified in place. Back up your photos before running.
- Only `.jpg`, `.jpeg`, and `.png` files are processed.
- If no date is detected in an image it is skipped without modification.
