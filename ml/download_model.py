"""
SplitSnap Donut Model Downloader.
Downloads the fine-tuned Donut vision model weights from Google Drive and unpacks
them into ml/models/donut_splitsnap for local GPU/CPU inference.
"""
import os
import sys
import zipfile
import shutil
import urllib.request
import re

# Default Google Drive File ID or Direct Download URL for donut_splitsnap.zip
# Replace with the user's uploaded Drive file ID or public link
DEFAULT_DRIVE_FILE_ID = os.getenv("DONUT_DRIVE_FILE_ID", "")
DEFAULT_DRIVE_URL = os.getenv("DONUT_DRIVE_URL", "")

DEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models", "donut_splitsnap"))
ZIP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "models", "donut_splitsnap.zip"))

def download_from_gdrive(file_id_or_url: str, output_path: str):
    """
    Downloads file from Google Drive handling large file confirmation tokens.
    """
    # Extract file id if full URL provided
    file_id = file_id_or_url
    match = re.search(r"[-_\w]{25,}", file_id_or_url)
    if match and "http" in file_id_or_url:
        file_id = match.group(0)

    print(f"Connecting to Google Drive (ID: {file_id})...")

    # Try using gdown if installed
    try:
        import gdown
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output_path, quiet=False)
        return True
    except ImportError:
        pass

    # Fallback to requests / urllib
    try:
        import requests
        url = "https://docs.google.com/uc?export=download"
        session = requests.Session()
        response = session.get(url, params={"id": file_id}, stream=True)

        token = None
        for key, value in response.cookies.items():
            if key.startswith("download_warning"):
                token = value
                break

        if token:
            params = {"id": file_id, "confirm": token}
            response = session.get(url, params=params, stream=True)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        sys.stdout.write(f"\rDownloading: {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB ({percent:.1f}%)")
                    else:
                        sys.stdout.write(f"\rDownloading: {downloaded / (1024*1024):.1f}MB")
                    sys.stdout.flush()
        print("\nDownload complete!")
        return True
    except Exception as e:
        print(f"Direct download failed: {e}")
        return False

def main():
    target_id = sys.argv[1] if len(sys.argv) > 1 else (DEFAULT_DRIVE_FILE_ID or DEFAULT_DRIVE_URL)

    if not target_id:
        print("\n=======================================================")
        print("SplitSnap Trained Donut Model Downloader")
        print("=======================================================")
        print("Usage:")
        print("  python ml/download_model.py <GOOGLE_DRIVE_LINK_OR_ID>")
        print("\nExample:")
        print("  python ml/download_model.py https://drive.google.com/file/d/1A2B3C4D5E.../view")
        print("=======================================================\n")
        sys.exit(1)

    os.makedirs(os.path.dirname(DEST_DIR), exist_ok=True)

    print(f"Downloading fine-tuned Donut weights to {ZIP_PATH}...")
    success = download_from_gdrive(target_id, ZIP_PATH)

    if not success or not os.path.exists(ZIP_PATH):
        print("Error: Could not download the model archive.")
        sys.exit(1)

    print(f"Unpacking {ZIP_PATH} into {DEST_DIR}...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        # Check if contents are nested inside 'donut_splitsnap'
        extract_tmp = os.path.join(os.path.dirname(DEST_DIR), "tmp_extract")
        zip_ref.extractall(extract_tmp)

        extracted_sub = os.path.join(extract_tmp, "donut_splitsnap")
        if os.path.exists(extracted_sub):
            if os.path.exists(DEST_DIR):
                shutil.rmtree(DEST_DIR)
            shutil.move(extracted_sub, DEST_DIR)
            shutil.rmtree(extract_tmp)
        else:
            if os.path.exists(DEST_DIR):
                shutil.rmtree(DEST_DIR)
            shutil.move(extract_tmp, DEST_DIR)

    # Clean up zip
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    print(f"\nModel successfully installed in: {DEST_DIR}")
    print("Files present:")
    for f in os.listdir(DEST_DIR):
        print(f"  - {f}")
    print("\nYou can now launch the backend:")
    print("  python backend/run.py")

if __name__ == "__main__":
    main()
