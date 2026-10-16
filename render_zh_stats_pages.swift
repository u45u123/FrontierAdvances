import AppKit
import Foundation
import PDFKit

let arguments = CommandLine.arguments
guard arguments.count == 3,
      let document = PDFDocument(url: URL(fileURLWithPath: arguments[1])) else {
    fatalError("Usage: render_zh_stats_pages.swift input.pdf output-directory")
}
let output = URL(fileURLWithPath: arguments[2], isDirectory: true)
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let pages = [14, 16, 18, 22, 24, 26, 28, 30, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 64, 68, 70, 72, 74, 76, 78, 80, 82]
for number in pages {
    guard let page = document.page(at: number - 1) else { continue }
    let bounds = page.bounds(for: .mediaBox)
    let scale: CGFloat = 2
    let size = NSSize(width: bounds.width * scale, height: bounds.height * scale)
    let image = NSImage(size: size)
    image.lockFocus()
    NSColor.white.set(); NSBezierPath(rect: NSRect(origin: .zero, size: size)).fill()
    let context = NSGraphicsContext.current!.cgContext
    context.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: context)
    image.unlockFocus()
    guard let data = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: data),
          let png = bitmap.representation(using: .png, properties: [:]) else { continue }
    try png.write(to: output.appendingPathComponent("page-\(number).png"))
}
