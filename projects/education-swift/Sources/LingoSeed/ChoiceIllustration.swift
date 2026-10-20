import SwiftUI

/// Presentation-only vocabulary artwork. It never reads the question's answer.
struct ChoiceIllustration: View {
    let phrase: String
    var resource: String? = nil
    private var symbol: String {
        switch phrase.lowercased() {
        case "good morning": "sun.max.fill"
        case "good night": "moon.stars.fill"
        case "thank you": "gift.fill"
        case "hello": "hand.wave.fill"
        case "goodbye": "paperplane.fill"
        default: "bubble.left.and.text.bubble.right.fill"
        }
    }
    private var colors: [Color] {
        switch phrase.lowercased() {
        case "good morning": [.orange, .yellow]
        case "good night": [.indigo, .purple]
        case "thank you": [.pink, .orange]
        case "hello": [.orange, .yellow]
        default: [.cyan, .blue]
        }
    }
    var body: some View {
        Group {
            if let name = resource ?? ReferenceStyle.choiceImages[phrase.lowercased()] {
                ReferenceStyle.image(name).resizable().scaledToFit().frame(width: 143, height: 160)
            } else { ZStack {
            Circle().fill(colors[0].opacity(0.1)).frame(width: 110, height: 110)
            Image(systemName: symbol).font(.system(size: 68, weight: .semibold)).symbolRenderingMode(.palette).foregroundStyle(colors[0], colors[1])
            }.frame(height: 135) }
        }.accessibilityHidden(true)
    }
}
struct SeedChoiceStyle: ButtonStyle {
    let selected: Bool
    let feedback: Bool?
    private var color: Color { feedback == false ? .red : feedback == true ? Color(red: 0.345, green: 0.8, blue: 0) : .cyan }
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.padding(14).frame(maxWidth: .infinity)
            .foregroundStyle(selected ? color : Color(white: 0.3))
            .background {
                RoundedRectangle(cornerRadius: 14).fill(selected ? color.opacity(0.15) : .white)
                    .shadow(color: selected ? color.opacity(0.4) : Color.black.opacity(0.15), radius: 0, y: configuration.isPressed ? 0 : 3)
            }
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(selected ? color.opacity(0.6) : Color.gray.opacity(0.25), lineWidth: 2))
            .offset(y: configuration.isPressed ? 3 : 0)
    }
}
