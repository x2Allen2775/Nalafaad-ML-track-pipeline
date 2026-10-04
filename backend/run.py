import os
import sys
#isko chalana hai guys


# Ensure root directory is on python path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Ensure cross-platform OCR engine is installed
try:
    import easyocr
except ImportError:
    print("\n[SplitSnap] Installing cross-platform OCR engine (easyocr)...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "easyocr", "--quiet"])
        print("[SplitSnap] OCR engine installed successfully!\n")
    except Exception as e:
        print(f"[SplitSnap] Warning: could not auto-install easyocr ({e}). Run: pip install easyocr")

import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 SplitSnap Backend Server Started")
    print("=" * 60)
    print("👉 SplitSnap Web App:      http://localhost:3000")
    print("👉 Backend API (Redirect): http://localhost:8000")
    print("👉 Interactive API Docs:   http://localhost:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)



#isi se jeetenge hum
