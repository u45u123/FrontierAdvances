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

let arguments = CommandLine.arguments
guard arguments.count == 3,
      let image = NSImage(contentsOfFile: arguments[1]),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fatalError("Usage: extract_ko_ocr.swift input.png output.json")
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["ko-KR"]
request.usesLanguageCorrection = true
let handler = VNImageRequestHandler(cgImage: cgImage)
try handler.perform([request])

let lines = (request.results ?? []).compactMap { result -> OCRLine? in
    guard let candidate = result.topCandidates(1).first else { return nil }
    let box = result.boundingBox
    return OCRLine(text: candidate.string, x: box.minX, y: box.minY, width: box.width, height: box.height)
}.sorted { lhs, rhs in
    abs(lhs.y - rhs.y) > 0.005 ? lhs.y > rhs.y : lhs.x < rhs.x
}
let output = try JSONEncoder().encode(lines)
try output.write(to: URL(fileURLWithPath: arguments[2]))
