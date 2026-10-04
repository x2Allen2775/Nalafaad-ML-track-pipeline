
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
