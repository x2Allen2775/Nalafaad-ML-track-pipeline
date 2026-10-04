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
DEFAULT_DRIVE_FILE_ID = os.getenv("DONUT_DRIVE_FILE_ID", "1sHSRn1ZrJNXJT7UktvLne7f5ntaTzHgP")
DEFAULT_DRIVE_URL = os.getenv("DONUT_DRIVE_URL", "https://drive.google.com/file/d/1sHSRn1ZrJNXJT7UktvLne7f5ntaTzHgP/view?usp=sharing")

DEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models", "donut_splitsnap"))
ZIP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "models", "donut_splitsnap.zip"))

import subprocess

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
    direct_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Fast curl download if available
    curl_path = shutil.which("curl")
    if curl_path:
        ret = subprocess.run([curl_path, "-L", "--progress-bar", "-o", output_path, direct_url])
        if ret.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000000:
            print("Download complete!")
            return True

    # Fallback to requests
    try:
        import requests
        res = requests.get(direct_url, stream=True)
        if res.status_code == 200:
            total_size = int(res.headers.get("content-length", 0))
            downloaded = 0
            with open(output_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=1048576):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            sys.stdout.write(f"\rDownloading: {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB ({(downloaded/total_size)*100:.1f}%)")
                        else:
                            sys.stdout.write(f"\rDownloading: {downloaded / (1024*1024):.1f}MB")
                        sys.stdout.flush()
            print("\nDownload complete!")
            return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False
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
