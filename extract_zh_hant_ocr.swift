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
    fatalError("Usage: extract_zh_hant_ocr.swift input.png output.json")
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hant"]
request.usesLanguageCorrection = true
try VNImageRequestHandler(cgImage: cgImage).perform([request])
let lines = (request.results ?? []).compactMap { result -> OCRLine? in
    guard let candidate = result.topCandidates(1).first else { return nil }
    let box = result.boundingBox
    return OCRLine(text: candidate.string, x: box.minX, y: box.minY, width: box.width, height: box.height)
}.sorted { abs($0.y - $1.y) > 0.005 ? $0.y > $1.y : $0.x < $1.x }
try JSONEncoder().encode(lines).write(to: URL(fileURLWithPath: arguments[2]))
