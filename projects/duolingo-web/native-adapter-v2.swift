import Foundation
import AppKit
import ApplicationServices

// Drives only the child application launched below; never inspects another app.
enum DriverError: Error { case unavailable(String) }
func attribute(_ element: AXUIElement, _ name: String) -> AnyObject? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success else { return nil }
    return value
}
func text(_ element: AXUIElement, _ name: String) -> String {
    (attribute(element, name) as? String) ?? ""
}
func enabled(_ element: AXUIElement) -> Bool {
    (attribute(element, kAXEnabledAttribute) as? NSNumber)?.boolValue ?? false
}
func elements(_ root: AXUIElement, depth: Int = 0) -> [AXUIElement] {
    if depth > 20 { return [] }
    let children = attribute(root, kAXChildrenAttribute) as? [AXUIElement] ?? []
    return [root] + children.flatMap { elements($0, depth: depth + 1) }
}
func wait(_ condition: () -> Bool) throws {
    let deadline = Date().addingTimeInterval(12)
    while Date() < deadline {
        if condition() { return }
        Thread.sleep(forTimeInterval: 0.08)
    }
    throw DriverError.unavailable("Native UI transition timed out")
}

let request = try JSONSerialization.jsonObject(with: FileHandle.standardInput.readDataToEndOfFile()) as! [String: Any]
let operation = request["operation"] as? String ?? "invalid"
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let binary = root.appendingPathComponent("projects/education-swift/.build/debug/LingoSeed")
var process: Process?
var app: AXUIElement?
var directory: URL?
var response: [String: Any] = ["operation": operation]

func windowElements() -> [AXUIElement] {
    guard let app else { return [] }
    let windows = attribute(app, kAXWindowsAttribute) as? [AXUIElement] ?? []
    return windows.flatMap { elements($0) }
}
func find(_ id: String) -> AXUIElement? {
    return windowElements().first { text($0, kAXIdentifierAttribute) == id }
}
func press(_ id: String) throws {
    try wait { find(id).map(enabled) ?? false }
    guard let element = find(id), AXUIElementPerformAction(element, kAXPressAction as CFString) == .success else {
        throw DriverError.unavailable("Cannot press native control: " + id)
    }
}
func observe() -> [String: Any] {
    let nodes = windowElements()
    let choices = nodes.filter { text($0, kAXIdentifierAttribute).hasPrefix("option-") }
    let feedback = find("feedback").map { text($0, kAXValueAttribute) } ?? "none"
    let heartsText = find("hearts").map { text($0, kAXValueAttribute) } ?? ""
    let screen = find("exit-title") != nil ? "exit_confirmation" : find("question-title") != nil ? "question" : find("course-entry") != nil ? "course_entry" : "other"
    let snapshot: [[String: Any]] = nodes.map {
        ["role": text($0, kAXRoleAttribute), "id": text($0, kAXIdentifierAttribute),
         "title": text($0, kAXTitleAttribute), "value": text($0, kAXValueAttribute),
         "description": text($0, kAXDescriptionAttribute), "enabled": enabled($0)]
    }
    return ["screen": screen, "authenticated": false,
            "answer_selected": choices.contains { text($0, kAXValueAttribute) == "selected" },
            "check_enabled": find("check").map(enabled) ?? false,
            "options_locked": !choices.isEmpty && choices.allSatisfy { !enabled($0) },
            "feedback": feedback, "continue_enabled": find("continue").map(enabled) ?? false,
            "hearts": Int(heartsText) as Any? ?? NSNull(), "ui_snapshot": snapshot]
}

do {
    if operation == "stop" {
        response["resources"] = [] // Every earlier command terminates its own registered child.
    } else {
        guard AXIsProcessTrusted() else { throw DriverError.unavailable("Accessibility permission unavailable for native UI driver") }
        guard FileManager.default.isExecutableFile(atPath: binary.path) else { throw DriverError.unavailable("Build LingoSeed before candidate UI verification") }
        let temp = FileManager.default.temporaryDirectory.appendingPathComponent("app-rebuild-native-" + UUID().uuidString)
        directory = temp
        try FileManager.default.createDirectory(at: temp, withIntermediateDirectories: true)
        let fixture = temp.appendingPathComponent("fixture.json")
        try JSONSerialization.data(withJSONObject: request["fixture"] ?? [:], options: [.sortedKeys]).write(to: fixture)
        let child = Process()
        child.executableURL = binary
        child.arguments = ["--fixture", fixture.path, "--progress", temp.appendingPathComponent("progress.json").path]
        child.standardOutput = FileHandle.nullDevice
        child.standardError = FileHandle.nullDevice
        try child.run()
        process = child
        app = AXUIElementCreateApplication(child.processIdentifier)
        try wait { child.isRunning && find("course-entry") != nil }
        if operation == "scenario" {
            try press("start-lesson")
            try wait { find("question-title") != nil }
            response["scenario_id"] = request["scenario_id"]
            response["precondition_state"] = observe()
            guard let data = (request["fixture"] as? [String: Any])?["data"] as? [String: Any],
                  let course = data["candidate_course"] as? [String: Any],
                  let questions = course["questions"] as? [[String: Any]], let first = questions.first,
                  let correctID = first["answer"] as? String,
                  let options = first["options"] as? [[String: Any]] else {
                throw DriverError.unavailable("Explicit original candidate curriculum fixture required")
            }
            var observations: [[String: Any]] = []
            for (index, action) in (request["actions"] as? [[String: Any]] ?? []).enumerated() {
                switch action["type"] as? String {
                case "inspect": break
                case "select":
                    let intent = action["answer"] as? String
                    guard intent == "correct" || intent == "wrong" else { throw DriverError.unavailable("Unknown semantic answer") }
                    let id = intent == "correct" ? correctID : options.compactMap { $0["id"] as? String }.first { $0 != correctID }
                    guard let id else { throw DriverError.unavailable("No distinct wrong option in fixture") }
                    try press("option-" + id)
                    try wait { find("check").map(enabled) ?? false }
                case "submit": try press("check"); try wait { find("feedback") != nil }
                case "quit": try press("quit"); try wait { find("exit-title") != nil }
                case "cancel_quit": try press("cancel-quit"); try wait { find("exit-title") == nil }
                default: throw DriverError.unavailable("Unsupported native action")
                }
                observations.append(["step": index, "state": observe()])
            }
            response["observations"] = observations
        } else if operation == "start" || operation == "reset" {
            response["state"] = observe()
            response["reset_scope"] = "Fresh temporary progress store; real native application launched"
        } else { throw DriverError.unavailable("Unsupported operation") }
    }
} catch {
    response["status"] = "unavailable"
    if case DriverError.unavailable(let reason) = error { response["reason"] = reason }
    else { response["reason"] = "Native driver error: " + String(describing: type(of: error)) }
    response["ui_observation"] = observe()
}
if let process, process.isRunning {
    process.terminate()
    let deadline = Date().addingTimeInterval(2)
    while process.isRunning && Date() < deadline { Thread.sleep(forTimeInterval: 0.05) }
    if process.isRunning { kill(process.processIdentifier, SIGKILL) }
    process.waitUntilExit()
}
if let directory { try? FileManager.default.removeItem(at: directory) }
let result = try JSONSerialization.data(withJSONObject: response, options: [.sortedKeys])
print("APP_REBUILD_RESULT " + String(decoding: result, as: UTF8.self))
