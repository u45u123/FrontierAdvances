import AppKit
import Foundation
import Vision

struct OCRLine: Encodable {
  let text: String
  let x: Double
  let y: Double
  let width: Double
  let height: Double
}

guard CommandLine.arguments.count == 3 else {
  fatalError("Usage: extract_es_ocr.swift IMAGE OUTPUT_JSON")
}

let imagePath = CommandLine.arguments[1]
let outputPath = CommandLine.arguments[2]
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
  fatalError("Could not open image: \(imagePath)")
}

var lines: [OCRLine] = []
let request = VNRecognizeTextRequest { request, _ in
  for observation in request.results as? [VNRecognizedTextObservation] ?? [] {
    guard let candidate = observation.topCandidates(1).first else { continue }
    let box = observation.boundingBox
    lines.append(OCRLine(text: candidate.string, x: box.origin.x, y: box.origin.y, width: box.width, height: box.height))
  }
}
request.recognitionLevel = .accurate
request.recognitionLanguages = ["es-ES"]
request.usesLanguageCorrection = true

try VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])
let data = try JSONEncoder().encode(lines)
try data.write(to: URL(fileURLWithPath: outputPath))
