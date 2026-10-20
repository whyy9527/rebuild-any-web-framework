import SwiftUI
import RiveRuntime

/// Actual source avatar-builder asset and state-machine inputs, observed through
/// loaded public resources. These inputs compose the avatar, rather than swap photos.
@MainActor final class SourceAvatarPlayer: ObservableObject {
    let model: RiveViewModel?
    let error: String?
    private let defaultAnimation: Double
    private let defaultZoom: Double
    @Published private(set) var inputSnapshot = "unavailable"
    static let initial: [String:Int] = {
        guard let url = Bundle.module.url(forResource:"avatar-initial-state",withExtension:"json",subdirectory:"Reference"),
              let bytes = try? Data(contentsOf:url),
              let values = try? JSONDecoder().decode([String:Int].self,from:bytes) else { return [:] }
        return values
    }()
    private static let file: Result<RiveFile, Error> = Result {
        guard let url=Bundle.module.url(forResource:"en-avatar-builder",withExtension:"riv",subdirectory:"Reference") else {throw CocoaError(.fileNoSuchFile)}
        return try RiveFile(data:Data(contentsOf:url),loadCdn:false)
    }
    let machine: String
    init(machine: String = "SMAvatar") {
        self.machine = machine
        do {
            let file = try Self.file.get()
            model = RiveViewModel(RiveModel(riveFile:file),stateMachineName:machine,fit:.cover,alignment:.center,autoPlay:true)
            defaultZoom = Double(model?.numberInput(named:"ENG_ONLY_Zoom")?.value() ?? 0)
            defaultAnimation = Double(model?.numberInput(named:"ENG_ONLY_Animation")?.value() ?? 0)
            error = nil
        } catch {
            model = nil
            defaultZoom = 0
            defaultAnimation = 0
            self.error = "原版头像动画载入失败"
        }
    }
    func update(states: [String:Int], animations: Bool, zoom: Double? = 3) {
        var values = Self.initial.merging(states,uniquingKeysWith: {_,new in new})
        values["ENG_ONLY_Zoom"] = states["ENG_ONLY_Zoom"] ?? Int(machine == "SMAvatar" ? (zoom ?? defaultZoom) : 1)
        for (name,value) in values { model?.setInput(name,value:Double(value)) }
        model?.setInput("ENG_ONLY_Animation",value:animations ? defaultAnimation : 0)
        inputSnapshot = measuredInputs
        if machine == "SMAvatar" && CommandLine.arguments.contains("--render-metadata") {
            // Read the runtime numbers after applying inputs; never emit pass flags.
            let line = "avatar-runtime-inputs " + inputSnapshot + "\n"
            FileHandle.standardError.write(Data(line.utf8))
        }
    }
    var measuredInputs: String {
        var values: [String:Double] = [:]
        for name in Array(Self.initial.keys)+["ENG_ONLY_Zoom","ENG_ONLY_Animation"] {
            if let value = model?.numberInput(named:name) { values[name] = Double(value.value()) }
        }
        guard let data = try? JSONSerialization.data(withJSONObject:values,options:[.sortedKeys]),
              let string = String(data:data,encoding:.utf8) else { return "unavailable" }
        return string
    }
}

struct ReferenceAvatarRenderer: View {
    let states: [String:Int]
    let animations: Bool
    var zoom: Double? = 3
    var identifier = "avatar-preview"
    @StateObject private var player = SourceAvatarPlayer()
    var body: some View {
        Group {
            if let model = player.model { RiveViewRepresentable(viewModel:model) }
            else { Text(player.error ?? "原版头像动画不可用") }
        }
        .onAppear { player.update(states:states,animations:animations,zoom:zoom) }
        .onChange(of:states) { _,_ in player.update(states:states,animations:animations,zoom:zoom) }
        .onChange(of:animations) { _,_ in player.update(states:states,animations:animations,zoom:zoom) }
        .accessibilityElement(children:.ignore)
        .accessibilityLabel(player.model == nil ? "unavailable" : "SMAvatar")
        .accessibilityValue(player.inputSnapshot)
        .accessibilityIdentifier(identifier)
    }
}

/// Original feature-button overrides use SMButtons and disable motion. Each
/// instance has its own artboard, while sharing the immutable parsed source file.
struct ReferenceAvatarThumbnail: View {
    let states: [String:Int]
    @StateObject private var player = SourceAvatarPlayer(machine:"SMButtons")
    private func update() {
        player.update(states:states,animations:false)
        player.model?.riveView?.advance(delta:0)
        player.model?.riveView?.advance(delta:0)
        player.model?.pause()
    }
    var body: some View {
        Group {
            if let model=player.model {RiveViewRepresentable(viewModel:model)}
            else {Text(player.error ?? "原版缩略图不可用")}
        }.onAppear {update()}.onChange(of:states) {_,_ in update()}.accessibilityHidden(true)
    }
}
