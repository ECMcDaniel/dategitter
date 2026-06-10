![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

# dategitter

A containerized utility for adding timestamps to scanned photo collections. Uses Google Cloud Vision OCR to detect printed dates on old photographs and writes the parsed date directly into each image's EXIF DateTimeOriginal and CreateDate fields via ExifTool.

## What it does

- Recursively scans a directory for .jpg, .jpeg, and .png files
- Detects text in each image using the Google Cloud Vision API
- Parses detected text into a valid EXIF timestamp (YYYY:MM:DD 12:00:00), handling ambiguous date formats and two-digit years
- Writes timestamps directly to EXIF metadata via ExifTool, or in --dry-run mode, logs proposed changes to dry_run_proposed_changes.csv without modifying any files

## Requirements

- Docker + Docker Compose
- Google Cloud project with the Vision API enabled
- A Google Cloud service account key (JSON).

More info about Gcloud service accounts can be found [here](https://docs.cloud.google.com/iam/docs/keys-list-get) on Google's website. I believe there is a free tier.

> [!NOTE]
> Cloud Vision API can be swapped for local ML inference if you have capable hardware. The containerized architecture makes this straightforward to refactor. If you do, please submit a PR because this is a feature I hope to add ASAP.

> [!NOTE]
> If you would like to try out this tool, you don't have Cloud Vision API, and you don't wish to refactor the code, please get in contact with me! I want to test this tool further, I will work to find a way to get your photos dated!

## Quick start (Docker Compose)

1. Clone the repo
2. Copy .env.example to .env and fill in your values:
   - GOOGLE_KEY_HOST_PATH — path/to/serviceaccount/keys.json 
   - PHOTOS_DIR_HOST_PATH — path/to/your/photos
3. Run:

```bash
docker compose up --build
```

## Authentication

The script resolves credentials in this order:
  1. GOOGLE_APPLICATION_CREDENTIALS environment variable (path to service account JSON)
  2. A google_key.json file in the working directory

## Dry Run Mode

To preview changes without modifying any EXIF data, add the --dry-run flag:

```bash
   docker compose run dategitter --dry-run
```

Proposed changes are written to **dry_run_proposed_changes.csv**.

## Roadmap / Known Limitations

- Date format detection is heuristic-based; highly unusual formats may not parse correctly
- All metadata date changes will include 12:00:00 as the time. Some photos contain timestamps, but this utility can't parse them yet.
- No GPU/local inference path yet — currently requires Google Cloud Vision API

## Contributing

If anyone wishes to contribute, feel free to fork and submit a PR.
