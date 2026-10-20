import AppKit
import SwiftUI

/// Plain multiline input: preserve literal lesson text, without macOS smart quotes.
struct ReferenceAnswerEditor: NSViewRepresentable {
    @Binding var text: String
    let enabled: Bool
    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeNSView(context: Context) -> NSScrollView {
        let scroll = NSScrollView()
        scroll.borderType = .noBorder
        scroll.drawsBackground = false
        scroll.hasVerticalScroller = false
        let editor = NSTextView(frame: NSRect(x: 0, y: 0, width: 600, height: 170))
        editor.autoresizingMask = [.width]
        editor.minSize = NSSize(width: 0, height: 170)
        editor.maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        editor.isVerticallyResizable = true
        editor.isHorizontallyResizable = false
        editor.textContainer?.widthTracksTextView = true
        editor.textContainer?.lineFragmentPadding = 0
        editor.textContainerInset = NSSize(width: 14, height: 12)
        editor.font = ReferenceStyle.nativeFont(19, weight: 400)
        editor.backgroundColor = NSColor(white: 247/255, alpha: 1)
        editor.isRichText = false
        editor.isAutomaticQuoteSubstitutionEnabled = false
        editor.isAutomaticDashSubstitutionEnabled = false
        editor.isAutomaticTextReplacementEnabled = false
        editor.isAutomaticSpellingCorrectionEnabled = false
        editor.isContinuousSpellCheckingEnabled = false
        editor.setAccessibilityIdentifier("answer-input")
        editor.setAccessibilityLabel("使用英语键入")
        editor.delegate = context.coordinator
        scroll.documentView = editor
        return scroll
    }
    func updateNSView(_ scroll: NSScrollView, context: Context) {
        context.coordinator.parent = self
        guard let editor = scroll.documentView as? NSTextView else { return }
        if editor.string != text { editor.string = text }
        editor.isEditable = enabled
    }
    final class Coordinator: NSObject, NSTextViewDelegate {
        var parent: ReferenceAnswerEditor
        init(_ parent: ReferenceAnswerEditor) { self.parent = parent }
        func textDidChange(_ notification: Notification) {
            guard let editor = notification.object as? NSTextView else { return }
            parent.text = editor.string
        }
    }
}
