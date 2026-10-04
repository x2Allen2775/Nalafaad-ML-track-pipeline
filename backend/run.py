import os
import sys
#isko chalana hai guys


# Ensure root directory is on python path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 SplitSnap Backend Server Starting...")
    print("=" * 60)
    print("👉 Backend API Root:       http://localhost:8000")
    print("👉 Interactive API Docs:   http://localhost:8000/docs")
    print("👉 Health Status:          http://localhost:8000/api/health")
    print("👉 Frontend Web App:       http://localhost:3000")
    print("=" * 60 + "\n")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)



#isi se jeetenge hum
