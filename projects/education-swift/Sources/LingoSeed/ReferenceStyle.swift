import AppKit
import CoreText
import SwiftUI

enum ReferenceStyle {
    static let choiceImages: [String: String] = {
        guard let url = Bundle.module.url(forResource: "choice-images", withExtension: "json", subdirectory: "Reference"),
              let data = try? Data(contentsOf: url), let result = try? JSONDecoder().decode([String: String].self, from: data) else { return [:] }
        return result
    }()
    static let green = Color(red: 88/255, green: 204/255, blue: 0)
    static let blue = Color(red: 28/255, green: 176/255, blue: 246/255)
    private static func adaptive(_ light: UInt32, _ dark: UInt32) -> Color {
        Color(nsColor: NSColor(name: nil) { appearance in
            let value = appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua ? dark : light
            return NSColor(srgbRed: Double((value >> 16) & 255) / 255, green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255, alpha: 1)
        })
    }
    static let border = adaptive(0xe5e5e5, 0x37464f)
    static let ink = adaptive(0x4b4b4b, 0xf1f7fb)
    static let secondaryInk = adaptive(0x777777, 0xdce6ec)
    static let disclosureInk = adaptive(0xafafaf, 0x52656d)
    static let background = adaptive(0xffffff, 0x131f24)
    static func registerFonts() {
        for name in ["font-0", "font-1"] {
            if let url = Bundle.module.url(forResource: name, withExtension: "ttf", subdirectory: "Reference") {
                CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
            }
        }
    }
    static func font(_ size: CGFloat, bold: Bool = false, weight: Double? = nil) -> Font {
        Font(nativeFont(size, bold: bold, weight: weight))
    }
    @MainActor private static let errorDescriptors: [Bool:CTFontDescriptor] = {
        var result: [Bool:CTFontDescriptor] = [:]
        for bold in [false,true] {
            let name=bold ? "en-error-bold" : "en-error-regular"
            guard let url=Bundle.module.url(forResource:name,withExtension:"otf",subdirectory:"Reference") else {continue}
            CTFontManagerRegisterFontsForURL(url as CFURL,.process,nil)
            if let descriptors=CTFontManagerCreateFontDescriptorsFromURL(url as CFURL) as? [CTFontDescriptor],let descriptor=descriptors.first {result[bold]=descriptor}
        }
        return result
    }()
    @MainActor static func errorFont(_ size:CGFloat,bold:Bool=false) -> Font {
        guard let descriptor=errorDescriptors[bold] else {return .system(size:size)}
        let font=CTFontCreateWithFontDescriptor(descriptor,size,nil)
        if CommandLine.arguments.contains("--render-metadata") {
            FileHandle.standardError.write(Data(("error-runtime-font "+(CTFontCopyPostScriptName(font) as String)+"\n").utf8))
        }
        return Font(font as NSFont)
    }
    static func nativeFont(_ size: CGFloat, bold: Bool = false, weight: Double? = nil) -> NSFont {
        let descriptor = CTFontDescriptorCreateWithAttributes([
            kCTFontNameAttribute: "DuolingoSans-Thin",
            kCTFontVariationAttribute: [NSNumber(value: 0x77676874): NSNumber(value: weight ?? (bold ? 700 : 500))]
        ] as CFDictionary)
        return CTFontCreateWithFontDescriptor(descriptor, size, nil) as NSFont
    }
    static func image(_ name: String) -> Image {
        guard let url = Bundle.module.url(forResource: name, withExtension: "png", subdirectory: "Reference"),
              let image = NSImage(contentsOf: url) else { return Image(systemName: "questionmark.square") }
        return Image(nsImage: image)
    }
    @MainActor static func recordWindowGeometry() {
        guard let index = CommandLine.arguments.firstIndex(of: "--render-metadata"),
              index + 1 < CommandLine.arguments.count,
              let window = NSApp.windows.first(where: { $0.contentView != nil }) else { return }
        let frame = window.frame
        let content = window.contentLayoutRect
        let value: [String: Any] = ["window_points": [frame.width, frame.height],
            "content_rect_points": [content.minX, frame.height - content.maxY, content.width, content.height],
            "backing_scale": window.backingScaleFactor]
        if let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys, .prettyPrinted]) {
            try? data.write(to: URL(fileURLWithPath: CommandLine.arguments[index + 1]), options: .atomic)
        }
    }
}

struct ReferenceButton: ButtonStyle {
    var color = ReferenceStyle.green
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(ReferenceStyle.font(15, bold: true)).tracking(0.8)
            .frame(maxWidth: .infinity).frame(height: 46)
            .foregroundStyle(.white).background(color, in: RoundedRectangle(cornerRadius: 16))
            .compositingGroup()
            .shadow(color: color == ReferenceStyle.green ? Color(red: 70/255, green: 163/255, blue: 2/255) : Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: configuration.isPressed ? 0 : 4)
            .offset(y: configuration.isPressed ? 4 : 0)
    }
}

/// Source footer: 150×50, 46-point face plus 4-point bottom edge.
struct ReferenceCheckButton: ButtonStyle {
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        let pressed = configuration.isPressed || !enabled
        configuration.label.font(ReferenceStyle.font(17, bold: true))
            .frame(width: 150, height: 50)
            .foregroundStyle(enabled ? .white : ReferenceStyle.disclosureInk)
            .background(alignment: .top) {
                RoundedRectangle(cornerRadius: 16).fill(enabled ? ReferenceStyle.green : ReferenceStyle.border)
                    .frame(height: 46)
                    .shadow(color: enabled ? Color(red: 70/255, green: 163/255, blue: 2/255) : .clear, radius: 0, y: pressed ? 0 : 4)
            }
            .offset(y: pressed ? 4 : 0)
    }
}
