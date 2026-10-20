import SwiftUI
import RiveRuntime

struct SourceCharacterAnimation: Decodable {
    let resource: String
    let name: String
    let artboard: String
    let stateMachine: String
    let correctTrigger: String
    let incorrectTrigger: String
    let resetTrigger: String
    let darkModeInput: String
    let rtlInput: String
    let scale: Double
    let xOffsetPercentage: Double
    let yOffsetPercentage: Double
    static let configurations: [String: SourceCharacterAnimation] = {
        guard let url = Bundle.module.url(forResource: "character-animations", withExtension: "json", subdirectory: "Reference"),
              let data = try? Data(contentsOf: url),
              let result = try? JSONDecoder().decode([String: SourceCharacterAnimation].self, from: data) else { return [:] }
        return result
    }()
}

@MainActor final class SourceCharacterPlayer: ObservableObject {
    let model: RiveViewModel?
    let error: String?
    init(configuration: SourceCharacterAnimation) {
        do {
            guard let url = Bundle.module.url(forResource: configuration.resource, withExtension: nil, subdirectory: "Reference") else {
                throw CocoaError(.fileNoSuchFile)
            }
            let file = try RiveFile(data: Data(contentsOf: url), loadCdn: false)
            model = RiveViewModel(RiveModel(riveFile: file), stateMachineName: configuration.stateMachine,
                                  fit: .contain, alignment: .center, autoPlay: true, artboardName: configuration.artboard)
            error = nil
        } catch {
            model = nil
            self.error = "角色动画未能载入。"
        }
    }
    func feedback(_ correct: Bool?, configuration: SourceCharacterAnimation) {
        model?.triggerInput(correct == nil ? configuration.resetTrigger : correct == true ? configuration.correctTrigger : configuration.incorrectTrigger)
    }
}

/// Original source Rive file and state-machine names, not a reconstructed mascot.
struct ReferenceCharacter: View {
    let resource: String
    let feedback: Bool?
    static func size(for resource: String?) -> CGSize {
        guard let resource, SourceCharacterAnimation.configurations[resource] != nil else { return CGSize(width: 120, height: 150) }
        return CGSize(width: 118, height: 175)
    }
    static func hasAnimation(for resource: String?) -> Bool {
        guard let resource else { return false }
        return SourceCharacterAnimation.configurations[resource] != nil
    }
    var body: some View {
        if let configuration = SourceCharacterAnimation.configurations[resource] {
            AnimatedSourceCharacter(configuration: configuration, feedback: feedback)
        } else {
            ReferenceStyle.image(resource).resizable().scaledToFit()
        }
    }
}

private struct AnimatedSourceCharacter: View {
    let configuration: SourceCharacterAnimation
    let feedback: Bool?
    @Environment(\.colorScheme) private var colorScheme
    @StateObject private var player: SourceCharacterPlayer
    init(configuration: SourceCharacterAnimation, feedback: Bool?) {
        self.configuration = configuration
        self.feedback = feedback
        _player = StateObject(wrappedValue: SourceCharacterPlayer(configuration: configuration))
    }
    private var state: String {
        guard player.model != nil else { return "unavailable" }
        guard let feedback else { return "idle" }
        return feedback ? "correct" : "incorrect"
    }
    private var rendered: AnyView {
        if let model = player.model { return AnyView(RiveViewRepresentable(viewModel: model)) }
        return AnyView(Text(player.error ?? "角色动画不可用"))
    }
    private func appearance(_ scheme: ColorScheme) {
        player.model?.setInput(configuration.darkModeInput, value: scheme == .dark)
    }
    var body: some View {
        rendered
        .onAppear {
            appearance(colorScheme)
            player.model?.setInput(configuration.rtlInput, value: false)
            player.feedback(feedback, configuration: configuration)
        }
        .onChange(of: feedback) { _, value in player.feedback(value, configuration: configuration) }
        .onChange(of: colorScheme) { _, value in appearance(value) }
        .scaleEffect(configuration.scale)
        .offset(x: 118 * configuration.xOffsetPercentage * configuration.scale / 100,
                y: -175 * configuration.yOffsetPercentage * configuration.scale / 100)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(configuration.name)
        .accessibilityIdentifier("question-character")
        .accessibilityValue(state)
    }
}
