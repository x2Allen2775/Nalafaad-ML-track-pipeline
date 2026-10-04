import os
import sys
#isko chalana hai guys


# Ensure root directory is on python path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import uvicorn

if __name__ == "__main__":
    print("Starting SplitSnap Backend on http://0.0.0.0:8000 ...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)



#isi se jeetenge hum
