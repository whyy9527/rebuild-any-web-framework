import SwiftUI
import AppKit
import LearningCore

@MainActor final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        if let index = CommandLine.arguments.firstIndex(of: "--reference-color-scheme"), index + 1 < CommandLine.arguments.count {
            let scheme = CommandLine.arguments[index + 1]
            if scheme == "light" { NSApp.appearance = NSAppearance(named: .aqua) }
            else if scheme == "dark" { NSApp.appearance = NSAppearance(named: .darkAqua) }
        }
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main struct LingoSeedApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var delegate
    @State private var model: LearningModel?
    @State private var startupError: String?
    init() {
        ReferenceStyle.registerFonts()
        func argument(_ name: String) -> String? {
            guard let index = CommandLine.arguments.firstIndex(of: name), index + 1 < CommandLine.arguments.count else { return nil }
            return CommandLine.arguments[index + 1]
        }
        let fixture = URL(fileURLWithPath: argument("--fixture") ?? "projects/duolingo-web/fixture-reference-en-zh-v14.json")
        let progress = argument("--progress").map { URL(fileURLWithPath: $0) }
            ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("LingoSeed/\(fixture.deletingPathExtension().lastPathComponent)/progress.json")
        do { _model = State(initialValue: try LearningModel(course: Course.readFixture(fixture), store: ProgressStore(url: progress))) }
        catch { _startupError = State(initialValue: "Unable to open the course or saved progress. Check the supplied files before restarting.") }
    }
    var body: some Scene {
        WindowGroup("LingoSeed") {
            if let model { LearningView(model: model)
                    .onAppear { DispatchQueue.main.async { ReferenceStyle.recordWindowGeometry() } }
                    .onReceive(NotificationCenter.default.publisher(for: NSWindow.didResizeNotification)) { _ in ReferenceStyle.recordWindowGeometry() }
            }
            else { ContentUnavailableView("Course unavailable", systemImage: "book.closed", description: Text(startupError ?? "Unknown error")) }
        }
        .defaultSize(width: 1200, height: 760)
    }
}
