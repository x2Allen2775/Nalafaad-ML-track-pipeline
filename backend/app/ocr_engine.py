"""
Apple Vision & Cross-Platform Neural OCR Engine for SplitSnap.
Extracts raw text tokens, coordinates, and confidence levels from receipt images.
"""
import os
import sys
import json
import subprocess
import shutil
from typing import List, Dict, Any, Optional
from PIL import Image

SWIFT_OCR_SCRIPT = """
import Foundation
import Vision
import AppKit

func runOCR(imagePath: String) {
    guard let img = NSImage(contentsOfFile: imagePath),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("[]")
        return
    }
    
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do {
        try handler.perform([req])
    } catch {
        print("[]")
        return
    }
    
    guard let results = req.results else {
        print("[]")
        return
    }
    
    var output: [[String: Any]] = []
    for observation in results {
        if let topCandidate = observation.topCandidates(1).first {
            let box = observation.boundingBox
            output.append([
                "text": topCandidate.string,
                "confidence": Double(topCandidate.confidence),
                "x": Double(box.origin.x),
                "y": Double(1.0 - box.origin.y - box.size.height), // Convert to top-left origin
                "w": Double(box.size.width),
                "h": Double(box.size.height)
            ])
        }
    }
    
    if let data = try? JSONSerialization.data(withJSONObject: output, options: []),
       let str = String(data: data, encoding: .utf8) {
        print(str)
    } else {
        print("[]")
    }
}

let args = CommandLine.arguments
if args.count > 1 {
    runOCR(imagePath: args[1])
} else {
    print("[]")
}
"""

class OCREngine:
    def __init__(self):
        self.is_mac = sys.platform == "darwin"
        self.swift_path = shutil.which("swift")
        self.has_swift = self.is_mac and (self.swift_path is not None)
        self.script_file = os.path.join(os.path.dirname(__file__), "_vision_ocr.swift")
        if self.has_swift and not os.path.exists(self.script_file):
            with open(self.script_file, "w") as f:
                f.write(SWIFT_OCR_SCRIPT)

    def extract_text_tokens(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Extracts list of text tokens with bounding boxes and confidence:
        [{"text": "...", "confidence": 0.99, "x": 0.1, "y": 0.2, "w": 0.4, "h": 0.05}, ...]
        """
        # Save temp image for native OCR
        temp_path = f"/tmp/splitsnap_ocr_temp_{os.getpid()}.png"
        try:
            image.save(temp_path, "PNG")

            if self.has_swift:
                tokens = self._extract_with_apple_vision(temp_path)
                if tokens:
                    return tokens

            # Fallback to pytesseract if installed
            tokens = self._extract_with_tesseract(temp_path)
            if tokens:
                return tokens

        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

        return []

    def _extract_with_apple_vision(self, image_path: str) -> List[Dict[str, Any]]:
        try:
            cmd = ["swift", self.script_file, image_path]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, list):
                    # Sort top to bottom by y coordinate
                    data.sort(key=lambda t: t.get("y", 0.0))
                    return data
        except Exception as e:
            print(f"[OCR] Apple Vision OCR failed: {e}")
        return []

    def _extract_with_tesseract(self, image_path: str) -> List[Dict[str, Any]]:
        try:
            import pytesseract
            from pytesseract import Output
            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, output_type=Output.DICT)
            tokens = []
            n_boxes = len(data['text'])
            w_total, h_total = img.size
            for i in range(n_boxes):
                txt = data['text'][i].strip()
                if txt:
                    conf = float(data['conf'][i]) / 100.0 if float(data['conf'][i]) > 0 else 0.8
                    tokens.append({
                        "text": txt,
                        "confidence": conf,
                        "x": data['left'][i] / w_total,
                        "y": data['top'][i] / h_total,
                        "w": data['width'][i] / w_total,
                        "h": data['height'][i] / h_total
                    })
            tokens.sort(key=lambda t: t.get("y", 0.0))
            return tokens
        except Exception:
            return []

ocr_engine = OCREngine()
