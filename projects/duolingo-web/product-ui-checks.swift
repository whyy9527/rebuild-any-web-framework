import Foundation
import AppKit
import ApplicationServices
import CoreGraphics

// Product checks drive only the child process created here, with isolated progress.
// They complement, and never change, the frozen shared v2 behavior assertions.
struct CheckFailure: Error { let message: String }
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let output = URL(fileURLWithPath: CommandLine.arguments[1], relativeTo: root).standardizedFileURL
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let progress = output.appendingPathComponent("progress.json")
guard !FileManager.default.fileExists(atPath: progress.path) else { throw CheckFailure(message: "Choose a fresh output directory; existing progress is preserved") }
var child: Process?
var app: AXUIElement?
var passed: [String] = []
var images: [String] = []
func attr(_ e: AXUIElement, _ name: String) -> AnyObject? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(e, name as CFString, &value) == .success else { return nil }
    return value
}
func text(_ e: AXUIElement, _ name: String) -> String { (attr(e, name) as? String) ?? "" }
func nodes(_ root: AXUIElement, _ depth: Int = 0) -> [AXUIElement] {
    guard depth < 24 else { return [] }
    return [root] + ((attr(root, kAXChildrenAttribute) as? [AXUIElement]) ?? []).flatMap { nodes($0, depth + 1) }
}
func windows() -> [AXUIElement] { app.flatMap { attr($0, kAXWindowsAttribute) as? [AXUIElement] } ?? [] }
func find(_ id: String) -> AXUIElement? { windows().flatMap { nodes($0) }.first { text($0, kAXIdentifierAttribute) == id } }
func value(_ id: String) -> String {
    guard let e = find(id), let raw = attr(e, kAXValueAttribute) else { return "" }
    return (raw as? String) ?? (raw as? NSNumber)?.stringValue ?? ""
}
func enabled(_ id: String) -> Bool { (find(id).flatMap { attr($0, kAXEnabledAttribute) } as? NSNumber)?.boolValue ?? false }
func wait(_ name: String, _ condition: () -> Bool) throws {
    let deadline = Date().addingTimeInterval(12)
    while Date() < deadline { if condition() { return }; Thread.sleep(forTimeInterval: 0.07) }
    throw CheckFailure(message: "Timed out: " + name)
}
func check(_ name: String, _ condition: @autoclosure () -> Bool) throws {
    guard condition() else { throw CheckFailure(message: name) }
    passed.append(name)
}
func press(_ id: String) throws {
    try wait(id) { enabled(id) }
    guard let e = find(id), AXUIElementPerformAction(e, kAXPressAction as CFString) == .success else { throw CheckFailure(message: "Cannot press " + id) }
    Thread.sleep(forTimeInterval: 0.12)
}
func stop() {
    guard let child, child.isRunning else { return }
    child.terminate()
    let deadline = Date().addingTimeInterval(2)
    while child.isRunning && Date() < deadline { Thread.sleep(forTimeInterval: 0.05) }
    if child.isRunning { kill(child.processIdentifier, SIGKILL) }
    child.waitUntilExit()
}
func launch() throws {
    let p = Process()
    p.executableURL = root.appendingPathComponent("projects/education-swift/.build/debug/LingoSeed")
    p.arguments = ["--fixture", root.appendingPathComponent("projects/duolingo-web/fixture-v2.json").path, "--progress", progress.path]
    p.standardOutput = FileHandle.nullDevice; p.standardError = FileHandle.nullDevice
    try p.run(); child = p; app = AXUIElementCreateApplication(p.processIdentifier)
    try wait("home startup") { p.isRunning && find("course-entry") != nil }
}
func resize(_ width: Double, _ height: Double) throws {
    guard let w = windows().first else { throw CheckFailure(message: "No owned window") }
    var size = CGSize(width: width, height: height)
    guard AXUIElementSetAttributeValue(w, kAXSizeAttribute as CFString, AXValueCreate(.cgSize, &size)!) == .success else { throw CheckFailure(message: "Resize failed") }
    Thread.sleep(forTimeInterval: 0.25)
}
func capture(_ name: String) throws {
    Thread.sleep(forTimeInterval: 0.65) // Let the visible progress/button transition settle before capture.
    guard let pid = child?.processIdentifier else { throw CheckFailure(message: "No owned PID") }
    let info = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    guard let window = info.first(where: { ($0[kCGWindowOwnerPID as String] as? Int) == Int(pid) && ($0[kCGWindowLayer as String] as? Int) == 0 }), let number = window[kCGWindowNumber as String] as? Int else { throw CheckFailure(message: "No owned visible window") }
    let p = Process(); p.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
    p.arguments = ["-x", "-l", String(number), output.appendingPathComponent(name + ".png").path]
    try p.run(); p.waitUntilExit()
    guard p.terminationStatus == 0 else { throw CheckFailure(message: "Capture failed") }
    images.append(name + ".png")
}
func next() throws {
    try press("continue")
    try wait("next activity") { find("lesson-complete") != nil || find("question-title") != nil && find("feedback") == nil }
}
func answer(_ id: String, expected: String = "correct") throws {
    try press("option-" + id); try press("check")
    try wait("answer feedback") { value("feedback") == expected }
}
func writeReceipt(_ status: String, _ failure: String? = nil) throws {
    var receipt: [String: Any] = ["kind": "native_product_ui", "status": status, "passed_checks": passed, "screenshots": images, "scope": "Owned child AX actions; real UI, isolated original course fixture and progress; screenshots require separate visual review", "limitations": ["Does not record acoustic output", "Does not establish reference visual similarity"]]
    if let failure { receipt["failure"] = failure }
    try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("result.json"))
}
defer { stop() }
do {
    try launch()
    if let window = windows().first, let raw = attr(window, kAXSizeAttribute) {
        var size = CGSize.zero
        AXValueGetValue(raw as! AXValue, .cgSize, &size)
        try check("Natural startup supports the three-column home", size.width >= 1120 && size.height >= 660)
    } else { throw CheckFailure(message: "No natural startup window size") }
    try resize(1200, 760)
    try check("Default home has course and locked second lesson", find("course-entry") != nil && enabled("start-lesson") && !enabled("start-lesson-1"))
    try check("Practice nodes are locked before lesson completion", !enabled("practice-lesson-0") && !enabled("practice-lesson-1"))
    try capture("home-wide")
    for name in ["Leaderboards", "Quests", "Shop", "Profile", "More"] {
        try press("nav-" + name.lowercased())
        try wait(name + " destination") { value("destination-title") == name }
        try check(name + " navigation opens its destination", value("destination-title") == name)
        try capture("navigation-" + name.lowercased())
        if ["Leaderboards", "Quests", "Shop"].contains(name) {
            try press("destination-practice"); try wait("destination starts real lesson") { find("question-title") != nil }
            try check(name + " starts an actual lesson", find("question-title") != nil)
            try press("quit"); try press("confirm-quit"); try wait("return to same destination") { value("destination-title") == name }
        }
        if name == "More" {
            try press("settings-sound"); try check("Settings turns sound off", value("sound-toggle") == "muted")
            try press("settings-sound"); try check("Settings restores sound", value("sound-toggle") == "on")
        }
        try press("return-learn"); try wait("navigation return") { find("course-entry") != nil }
    }
    try press("open-guide"); try wait("guide sheet") { find("guide-title") != nil }; try capture("guidebook")
    try press("close-guide"); try wait("guide closed") { find("guide-title") == nil }
    try check("Guidebook opens and closes", find("course-entry") != nil)
    for (id, destination) in [("view-quests", "Quests"), ("view-profile", "Profile")] {
        try press(id); try wait("card destination") { value("destination-title") == destination }
        try check(id + " opens " + destination, value("destination-title") == destination)
        try press("return-learn"); try wait("card return") { find("course-entry") != nil }
    }
    try resize(820, 700); try capture("home-narrow")
    try check("Narrow home keeps start and named navigation", enabled("start-lesson") && find("nav-profile").map { text($0, kAXDescriptionAttribute) == "Profile" } == true)
    try resize(1200, 760)
    try press("sound-toggle"); try wait("muted") { value("sound-toggle") == "muted" }
    stop(); try launch(); try resize(1200, 760)
    try check("Mute survives an actual process restart", value("sound-toggle") == "muted")
    try press("sound-toggle"); try wait("unmuted") { value("sound-toggle") == "on" }
    try check("Sound can be restored", value("sound-toggle") == "on")
    try press("start-lesson"); try wait("choice") { find("question-title") != nil }; try capture("choice")
    try press("pronounce")
    try answer("night", expected: "incorrect"); try check("Wrong answer updates hearts", value("hearts") == "4"); try capture("incorrect")
    try next(); try answer("thanks"); try capture("correct"); try next()
    try wait("matching") { find("pair-left-morning") != nil }; try capture("matching")
    for id in ["morning", "thanks", "bye"] { try press("pair-left-" + id); try press("pair-right-" + id) }
    try wait("automatic matching feedback") { value("feedback") == "correct" }
    try check("Completing all pairs advances to correct feedback without Check", value("feedback") == "correct" && find("check") == nil)
    try capture("matching-correct"); try next()
    try check("Mistake returns for review", find("review-label") != nil)
    try capture("mistake-review"); try answer("morning"); try next(); try wait("completion") { find("lesson-complete") != nil }; try check("Completion progress is full after mistake review", value("lesson-progress") == "1"); try capture("completion")
    try press("return-path"); try wait("path") { find("course-entry") != nil }
    try check("Completion updates home and unlocks lesson two", value("completed-count") == "1" && enabled("start-lesson-1")); try capture("unlocked-home")
    stop(); try launch(); try resize(1200, 760)
    try check("Completion and unlock survive restart", value("completed-count") == "1" && enabled("start-lesson-1") && value("sound-toggle") == "on")
    try press("start-lesson-1"); try wait("second lesson") { find("option-hello") != nil }; try answer("hello"); try next()
    try wait("word tiles") { find("word-bank-good") != nil }; try check("Word instruction speech entry is available", enabled("pronounce")); try press("pronounce"); try capture("word-tiles")
    try resize(820, 700); try capture("word-tiles-narrow"); try check("Narrow word tiles keep Check", find("check") != nil && find("word-bank-good") != nil); try resize(1200, 760)
    try press("word-bank-good"); try press("word-bank-night"); try press("check"); try wait("wrong word order") { value("feedback") == "incorrect" }; try capture("word-incorrect"); try next()
    try press("word-bank-thank"); try press("word-bank-you"); try press("check"); try wait("correct phrase") { value("feedback") == "correct" }; try capture("word-correct"); try next()
    try check("Wrong phrase returns to review", find("review-label") != nil && find("word-bank-good") != nil)
    try press("word-bank-good"); try press("word-bank-morning"); try press("check"); try wait("review corrected") { value("feedback") == "correct" }; try next()
    try wait("second completion") { find("lesson-complete") != nil }; try press("return-path"); try wait("completed path") { value("completed-count") == "2" }
    try check("Both lessons complete with persistent learning state", value("completed-count") == "2"); try capture("completed-home")
    try press("start-lesson"); try wait("practice again") { find("question-title") != nil }; try press("quit"); try wait("exit confirmation") { find("exit-title") != nil }; try capture("exit")
    try press("cancel-quit"); try wait("exit canceled") { find("exit-title") == nil && find("question-title") != nil }
    try press("quit"); try wait("exit again") { find("exit-title") != nil }; try press("confirm-quit"); try wait("exit to home") { find("course-entry") != nil }
    try check("Exit cancel and confirm preserve completed lessons", value("completed-count") == "2")
    stop(); try launch(); try resize(1200, 760)
    try check("Two completed lessons reopen after actual restart", value("completed-count") == "2")
    for index in 0..<2 {
        try check("Completed lesson unlocks practice \(index)", enabled("practice-lesson-\(index)"))
        try press("practice-lesson-\(index)"); try wait("practice node opens real lesson") { find("question-title") != nil }
        try press("quit"); try wait("practice exit") { find("exit-title") != nil }; try press("confirm-quit"); try wait("practice return") { find("course-entry") != nil }
        try check("Practice \(index) return preserves completions", value("completed-count") == "2")
    }
    try writeReceipt("pass"); print("PASS \(passed.count) native product checks; \(images.count) owned-window screenshots")
} catch {
    try? writeReceipt("fail", String(describing: error)); print("FAIL: \(error)"); stop(); exit(1)
}
