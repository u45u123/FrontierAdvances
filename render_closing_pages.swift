import AppKit
import Foundation
import PDFKit

let arguments = CommandLine.arguments
guard arguments.count == 4,
      let document = PDFDocument(url: URL(fileURLWithPath: arguments[1])),
      let page = document.page(at: document.pageCount - 1) else {
    fatalError("Usage: render_closing_pages.swift input.pdf output.png scale")
}

let scale = CGFloat(Double(arguments[3]) ?? 2)
let bounds = page.bounds(for: .mediaBox)
let size = NSSize(width: bounds.width * scale, height: bounds.height * scale)
let image = NSImage(size: size)
image.lockFocus()
NSColor.white.set()
NSBezierPath(rect: NSRect(origin: .zero, size: size)).fill()
let context = NSGraphicsContext.current!.cgContext
context.scaleBy(x: scale, y: scale)
page.draw(with: .mediaBox, to: context)
image.unlockFocus()

guard let data = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: data),
      let png = bitmap.representation(using: .png, properties: [:]) else {
    fatalError("Could not encode PNG")
}
try png.write(to: URL(fileURLWithPath: arguments[2]))
