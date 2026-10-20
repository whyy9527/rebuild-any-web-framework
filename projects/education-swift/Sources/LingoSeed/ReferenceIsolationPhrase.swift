import AppKit
import SwiftUI
import LearningCore

struct ReferenceIsolationPhrase: View {
    let tokens: [IsolationPromptToken]
    let correct: Bool
    private var widths: [CGFloat] {
        let font = ReferenceStyle.nativeFont(20, weight: 400)
        return tokens.map { ($0.text as NSString).size(withAttributes: [.font: font]).width }
    }
    var body: some View {
        let widths = widths
        Canvas { context, _ in
            var x: CGFloat = 0
            for (index, token) in tokens.enumerated() {
                let color = token.isBlank && correct ? ReferenceStyle.green : ReferenceStyle.ink
                if !token.isBlank || correct {
                    context.draw(Text(token.text).font(ReferenceStyle.font(20, weight: 400)).foregroundStyle(color),
                                 at: CGPoint(x: x, y: 16), anchor: .leading)
                }
                if token.underlined || token.isBlank {
                    var line = Path()
                    line.move(to: CGPoint(x: x, y: 30))
                    line.addLine(to: CGPoint(x: x + widths[index], y: 30))
                    context.stroke(line, with: .color(token.isBlank && correct ? ReferenceStyle.green : ReferenceStyle.disclosureInk),
                                   style: StrokeStyle(lineWidth: 2, dash: token.isBlank && !correct ? [] : [2, 3]))
                }
                x += widths[index]
            }
        }.frame(width: widths.reduce(0, +), height: 32)
            .accessibilityLabel(tokens.map { $0.isBlank && !correct ? "__" : $0.text }.joined())
    }
}

struct ReferenceIsolationBubble: Shape {
    func path(in r: CGRect) -> Path {
        let radius: CGFloat = 12
        var p = Path()
        p.move(to: CGPoint(x: radius, y: 0))
        p.addLine(to: CGPoint(x: r.width - radius, y: 0))
        p.addQuadCurve(to: CGPoint(x: r.width, y: radius), control: CGPoint(x: r.width, y: 0))
        p.addLine(to: CGPoint(x: r.width, y: r.height - radius))
        p.addQuadCurve(to: CGPoint(x: r.width - radius, y: r.height), control: CGPoint(x: r.width, y: r.height))
        p.addLine(to: CGPoint(x: radius, y: r.height))
        p.addQuadCurve(to: CGPoint(x: 0, y: r.height - radius), control: CGPoint(x: 0, y: r.height))
        p.addLine(to: CGPoint(x: 0, y: r.midY + 2))
        p.addLine(to: CGPoint(x: -15, y: r.midY + 2))
        p.addLine(to: CGPoint(x: 0, y: r.midY - 13))
        p.addLine(to: CGPoint(x: 0, y: radius))
        p.addQuadCurve(to: CGPoint(x: radius, y: 0), control: .zero)
        p.closeSubpath()
        return p
    }
}
