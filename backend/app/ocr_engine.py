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

import tempfile
import numpy as np

class OCREngine:
    def __init__(self):
        self.is_mac = sys.platform == "darwin"
        self.swift_path = shutil.which("swift")
        self.has_swift = self.is_mac and (self.swift_path is not None)
        self.script_file = os.path.join(os.path.dirname(__file__), "_vision_ocr.swift")
        if self.has_swift and not os.path.exists(self.script_file):
            try:
                with open(self.script_file, "w") as f:
                    f.write(SWIFT_OCR_SCRIPT)
            except Exception:
                self.has_swift = False

        self._easyocr_reader = None

    def _get_easyocr_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                import torch
                use_gpu = torch.cuda.is_available()
                self._easyocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
            except Exception as e:
                print(f"[OCREngine] EasyOCR reader initialization: {e}")
                self._easyocr_reader = False
        return self._easyocr_reader if self._easyocr_reader is not False else None

    def extract_text_tokens(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Extracts list of text tokens with bounding boxes and confidence:
        [{"text": "...", "confidence": 0.99, "x": 0.1, "y": 0.2, "w": 0.4, "h": 0.05}, ...]
        Uses macOS native Vision when available, and universal PyTorch EasyOCR across Windows/Linux/Mac.
        """
        w_total, h_total = image.size

        # Tier 1 (macOS native fast Swift Apple Vision):
        if self.has_swift:
            temp_path = os.path.join(tempfile.gettempdir(), f"splitsnap_ocr_{os.getpid()}.png")
            try:
                image.save(temp_path, "PNG")
                tokens = self._extract_with_apple_vision(temp_path)
                if tokens and len(tokens) > 2:
                    return tokens
            except Exception as e:
                print(f"[OCREngine] Apple Vision OCR note: {e}")
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

        # Tier 2 (Universal PyTorch EasyOCR - Windows, Linux, macOS):
        reader = self._get_easyocr_reader()
        if reader:
            try:
                img_rgb = image.convert("RGB")
                img_np = np.array(img_rgb)
                results = reader.readtext(img_np)
                tokens = []
                for bbox, text, conf in results:
                    txt = text.strip()
                    if not txt:
                        continue
                    xs = [pt[0] for pt in bbox]
                    ys = [pt[1] for pt in bbox]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
                    tokens.append({
                        "text": txt,
                        "confidence": float(conf),
                        "x": max(0.0, min(1.0, x_min / w_total)),
                        "y": max(0.0, min(1.0, y_min / h_total)),
                        "w": max(0.001, min(1.0, (x_max - x_min) / w_total)),
                        "h": max(0.001, min(1.0, (y_max - y_min) / h_total))
                    })
                if tokens:
                    tokens.sort(key=lambda t: t.get("y", 0.0))
                    return tokens
            except Exception as e:
                print(f"[OCREngine] EasyOCR extraction error: {e}")

        # Tier 3 (Pytesseract fallback if installed on system):
        temp_path = os.path.join(tempfile.gettempdir(), f"splitsnap_ocr_{os.getpid()}.png")
        try:
            image.save(temp_path, "PNG")
            tokens = self._extract_with_tesseract(temp_path)
            if tokens:
                return tokens
        except Exception:
            pass
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
