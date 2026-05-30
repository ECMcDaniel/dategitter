import io
import re
import subprocess
from google.cloud import vision

def detect_date_and_stamp(image_path):
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    
    # We use TEXT_DETECTION (optimized for dense text) or DOCUMENT_TEXT_DETECTION
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        print(f"No text found in {image_path}")
        return

    # The first element in texts contains the entire block of found text
    full_text = texts[0].description
    print(f"Detected Text: {full_text.strip()}")

    # Regex to match common camera date formats (e.g., '98 10 24, 10/24/98, 1998-10-24)
    # This specific regex looks for 2 or 4 digit blocks separated by spaces, slashes, or dashes
    date_pattern = re.compile(r'\b(\d{2,4})[-/ ](\d{2})[-/ ](\d{2,4})\b')
    match = date_pattern.search(full_text)

    if match:
        # Extract the pieces (e.g., Year, Month, Day)
        p1, p2, p3 = match.groups()
        
        # Standardize 2-digit years (Assume 1900s if > 70, otherwise 2000s)
        def fix_year(y):
            if len(y) == 2:
                return f"19{y}" if int(y) > 70 else f"20{y}"
            return y

        # Customize this logic depending on how YOUR camera ordered them (e.g., YY MM DD)
        year = fix_year(p1)
        month = p2
        day = p3

        exif_date = f"{year}:{month}:{day} 12:00:00"
        print(f"Parsed Date for EXIF: {exif_date}")

        # Use ExifTool to write the metadata
        try:
            subprocess.run([
                'exiftool', 
                f'-DateTimeOriginal={exif_date}', 
                f'-CreateDate={exif_date}',
                '-overwrite_original', # Prevents creating .jpg_original backups
                image_path
            ], check=True)
            print(f"Successfully updated metadata for {image_path}")
        except subprocess.CalledProcessError as e:
            print(f"ExifTool failed: {e}")
            
    else:
        print(f"No valid date pattern matched in the text for {image_path}")

# Example usage
detect_date_and_stamp('path/to/your/old_photo.jpg')