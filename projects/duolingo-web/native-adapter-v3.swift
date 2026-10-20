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
let fixtureData = ((request["fixture"] as? [String: Any])?["data"] as? [String: Any]) ?? [:]
let course = fixtureData["candidate_course"] as? [String: Any] ?? [:]
let lessonDefinitions = course["lessons"] as? [[String: Any]] ?? [["questions": course["questions"] ?? []]]
let allQuestions = lessonDefinitions.flatMap { $0["questions"] as? [[String: Any]] ?? [] }
var process: Process?
var app: AXUIElement?
var directory: URL?
var fixtureURL: URL?
var progressURL: URL?
var firstPrompt = ""
var currentLesson = 0
var response: [String: Any] = ["operation": operation]
var learningTrace = [[String: Any]]()

func windowElements() -> [AXUIElement] {
    guard let app else { return [] }
    let windows = attribute(app, kAXWindowsAttribute) as? [AXUIElement] ?? []
    return windows.flatMap { elements($0) }
}
func find(_ id: String) -> AXUIElement? { windowElements().first { text($0, kAXIdentifierAttribute) == id } }
func value(_ id: String) -> String { find(id).map { text($0, kAXValueAttribute) } ?? "" }
func press(_ id: String) throws {
    try wait { find(id).map(enabled) ?? false }
    guard let element = find(id), AXUIElementPerformAction(element, kAXPressAction as CFString) == .success else {
        throw DriverError.unavailable("Cannot press native control: " + id)
    }
}
func kind() -> String? {
    let ids = windowElements().map { text($0, kAXIdentifierAttribute) }
    if ids.contains(where: { $0.hasPrefix("option-") }) { return "choice" }
    if ids.contains(where: { $0.hasPrefix("word-bank-") }) { return "word_tiles" }
    if ids.contains(where: { $0.hasPrefix("pair-left-") }) { return "matching" }
    return nil
}
func question() throws -> [String: Any] {
    guard let q = allQuestions.first(where: { $0["prompt"] as? String == value("question-title") }) else {
        throw DriverError.unavailable("Visible native question does not map to the explicit fixture")
    }
    return q
}
func terminateChild() {
    guard let process, process.isRunning else { return }
    process.terminate()
    let deadline = Date().addingTimeInterval(2)
    while process.isRunning && Date() < deadline { Thread.sleep(forTimeInterval: 0.05) }
    if process.isRunning { kill(process.processIdentifier, SIGKILL) }
    process.waitUntilExit()
}
func launch() throws {
    guard let fixtureURL, let progressURL else { throw DriverError.unavailable("No isolated fixture paths") }
    let child = Process()
    child.executableURL = binary
    child.arguments = ["--fixture", fixtureURL.path, "--progress", progressURL.path]
    child.standardOutput = FileHandle.nullDevice
    child.standardError = FileHandle.nullDevice
    try child.run()
    process = child
    app = AXUIElementCreateApplication(child.processIdentifier)
    try wait { child.isRunning && find("course-entry") != nil }
}
func next() throws {
    try press("continue")
    try wait { find("lesson-complete") != nil || find("question-title") != nil && find("feedback") == nil }
}
func select(_ intent: String) throws {
    let q = try question()
    guard let correct = q["answer"] as? String, let options = q["options"] as? [[String: Any]], intent == "correct" || intent == "wrong" else {
        throw DriverError.unavailable("Unknown semantic choice")
    }
    let id = intent == "correct" ? correct : options.compactMap { $0["id"] as? String }.first { $0 != correct }
    guard let id else { throw DriverError.unavailable("No distinct wrong option") }
    try press("option-" + id)
    try wait { find("check").map(enabled) ?? false }
}
func submit() throws { try press("check"); try wait { find("feedback") != nil } }
func wordID(_ index: Int) throws -> String {
    let q = try question()
    guard let answer = q["answer_words"] as? [String], answer.indices.contains(index) else {
        throw DriverError.unavailable("Unknown semantic token index")
    }
    return answer[index]
}
func addWord(_ index: Int) throws {
    let id = try wordID(index)
    try press("word-bank-" + id)
    try wait { find("selected-word-" + id) != nil }
}
func removeWord(_ index: Int) throws {
    let id = try wordID(index)
    try press("selected-word-" + id)
    try wait { find("selected-word-" + id) == nil && (find("word-bank-" + id).map(enabled) ?? false) }
}
func matchAll() throws {
    let q = try question()
    guard let pairs = q["pairs"] as? [[String: String]] else { throw DriverError.unavailable("No matching fixture") }
    for pair in pairs {
        guard let id = pair["id"] else { throw DriverError.unavailable("Missing pair identity") }
        if find("pair-left-" + id).map(enabled) ?? false {
            try press("pair-left-" + id); try press("pair-right-" + id)
            try wait { !(find("pair-left-" + id).map(enabled) ?? true) }
        }
    }
    try wait { find("feedback") != nil }
}
func answerCurrent() throws {
    learningTrace.append(["kind": kind() ?? "unknown", "prompt": value("question-title")])
    switch kind() {
    case "choice": try select("correct"); try submit()
    case "word_tiles":
        let q = try question()
        guard let answer = q["answer_words"] as? [String] else { throw DriverError.unavailable("No word order fixture") }
        for index in answer.indices { try addWord(index) }
        try submit()
    case "matching": try matchAll()
    default: throw DriverError.unavailable("Unknown native question type")
    }
}
func finishLesson(stopAtReview: Bool = false) throws {
    for _ in 0..<45 {
        if find("lesson-complete") != nil { return }
        if stopAtReview && find("review-label") != nil { return }
        if find("feedback") == nil { try answerCurrent() }
        try next()
    }
    throw DriverError.unavailable("Native lesson action budget exhausted")
}
func returnPath() throws {
    try press("return-path")
    try wait { find("course-entry") != nil }
}
func openLesson(_ index: Int) throws {
    guard lessonDefinitions.indices.contains(index) else { throw DriverError.unavailable("No further native lesson fixture") }
    try press(index == 0 ? "start-lesson" : "start-lesson-" + String(index))
    currentLesson = index
    try wait { find("question-title") != nil }
}
func prepare(_ precondition: [String: Any]) throws {
    try openLesson(0)
    if precondition["lesson_index"] as? Int == 1 { try finishLesson();try returnPath();try openLesson(1) }
    if let requested = precondition["question_kind"] as? String {
        for index in 0..<60 {
            if kind() == requested { break }
            if find("lesson-complete") != nil { try returnPath();try openLesson(currentLesson + 1) }
            else { try answerCurrent();try next() }
            if index == 59 { throw DriverError.unavailable("Requested native question type not reached") }
        }
    }
    firstPrompt = value("question-title")
}
func observe() -> [String: Any] {
    let nodes = windowElements()
    let choices = nodes.filter { text($0, kAXIdentifierAttribute).hasPrefix("option-") }
    let words = nodes.filter { text($0, kAXIdentifierAttribute).hasPrefix("selected-word-") }
    let bank = nodes.filter { text($0, kAXIdentifierAttribute).hasPrefix("word-bank-") }
    let pairs = nodes.filter { text($0, kAXIdentifierAttribute).hasPrefix("pair-left-") || text($0, kAXIdentifierAttribute).hasPrefix("pair-right-") }
    let completed = Int(value("completed-count")) ?? 0
    let isPath = find("course-entry") != nil
    let screen = find("exit-title") != nil ? "exit_confirmation" : find("lesson-complete") != nil ? "lesson_complete" : find("question-title") != nil ? "question" : isPath ? completed > 0 ? "course_path" : "course_entry" : "other"
    let snapshot: [[String: Any]] = nodes.map {
        ["role":text($0,kAXRoleAttribute),"id":text($0,kAXIdentifierAttribute),"value":text($0,kAXValueAttribute),"description":text($0,kAXDescriptionAttribute),"enabled":enabled($0)]
    }
    let matched = !pairs.isEmpty && pairs.allSatisfy { !enabled($0) }
    var nextEnabled = false
    if isPath && lessonDefinitions.indices.contains(completed) { nextEnabled = find(completed == 0 ? "start-lesson" : "start-lesson-" + String(completed)).map(enabled) ?? false }
    return ["screen":screen,"authenticated":false,"question_kind":kind() as Any? ?? NSNull(),"lesson_index":currentLesson,
            "answer_selected":choices.contains { text($0,kAXValueAttribute)=="selected" } || !words.isEmpty,
            "check_enabled":find("check").map(enabled) ?? false,
            "options_locked":!choices.isEmpty && choices.allSatisfy { !enabled($0) } || !bank.isEmpty && bank.allSatisfy { !enabled($0) } || matched,
            "feedback":find("feedback").map { text($0,kAXValueAttribute) } ?? "none","continue_enabled":find("continue").map(enabled) ?? false,
            "hearts":Int(value("hearts")) as Any? ?? NSNull(),"selected_word_count":words.count,"matching_complete":matched,
            "reviewing":find("review-label") != nil,"initial_question_revisited":find("question-title") != nil && value("question-title")==firstPrompt,
            "question_changed":find("question-title") != nil && value("question-title") != firstPrompt,
            "completed_lessons":isPath ? completed as Any : NSNull(),"current_lesson_index":isPath ? completed as Any : NSNull(),"next_lesson_enabled":nextEnabled,"ui_snapshot":snapshot]
}
func act(_ action: [String: Any]) throws {
    switch action["type"] as? String {
    case "inspect": break
    case "select": try select(action["answer"] as? String ?? "")
    case "submit": try submit()
    case "continue": try next()
    case "quit": try press("quit");try wait { find("exit-title") != nil }
    case "cancel_quit": try press("cancel-quit");try wait { find("exit-title") == nil }
    case "confirm_quit": try press("confirm-quit");try wait { find("course-entry") != nil }
    case "reopen_lesson": try openLesson(currentLesson)
    case "add_word": try addWord(action["index"] as? Int ?? -1)
    case "remove_word": try removeWord(action["index"] as? Int ?? -1)
    case "fill_words":
        let q = try question()
        guard let answer = q["answer_words"] as? [String] else { throw DriverError.unavailable("No token order fixture") }
        var indices = Array(answer.indices)
        if action["order"] as? String == "reversed" { indices.reverse() }
        else if action["order"] as? String != "correct" { throw DriverError.unavailable("Unknown word order") }
        for index in indices { try addWord(index) }
    case "match_all": try matchAll()
    case "finish_main_questions": try finishLesson(stopAtReview: true)
    case "finish_lesson": try finishLesson()
    case "return_to_path": try returnPath()
    case "reload": terminateChild();try launch()
    default: throw DriverError.unavailable("Unsupported native action")
    }
}
do {
    if operation == "stop" { response["resources"] = [] }
    else {
        guard AXIsProcessTrusted() else { throw DriverError.unavailable("Accessibility permission unavailable") }
        guard FileManager.default.isExecutableFile(atPath: binary.path) else { throw DriverError.unavailable("Candidate executable missing after build") }
        let temp = FileManager.default.temporaryDirectory.appendingPathComponent("app-rebuild-native-" + UUID().uuidString)
        directory = temp
        try FileManager.default.createDirectory(at: temp,withIntermediateDirectories:true)
        fixtureURL = temp.appendingPathComponent("fixture.json");progressURL = temp.appendingPathComponent("progress.json")
        try JSONSerialization.data(withJSONObject:request["fixture"] ?? [:],options:[.sortedKeys]).write(to:fixtureURL!)
        try launch()
        if operation == "scenario" {
            try prepare(request["precondition"] as? [String:Any] ?? [:])
            response["scenario_id"] = request["scenario_id"];response["precondition_state"] = observe()
            var observations = [[String:Any]]()
            for (step,action) in (request["actions"] as? [[String:Any]] ?? []).enumerated() {try act(action);observations.append(["step":step,"state":observe()])}
            response["observations"] = observations;response["preparation"] = learningTrace
        }else if operation == "start" || operation == "reset" { response["state"] = observe() }
        else {throw DriverError.unavailable("Unsupported operation")}
    }
}catch {
    response["status"] = "unavailable"
    if case DriverError.unavailable(let reason) = error {response["reason"] = reason}
    else {response["reason"] = "Native driver error: " + String(describing:type(of:error))}
    response["ui_observation"] = observe();response["preparation"] = learningTrace
}
terminateChild()
if let directory {try? FileManager.default.removeItem(at:directory)}
let result = try JSONSerialization.data(withJSONObject:response,options:[.sortedKeys])
print("APP_REBUILD_RESULT " + String(decoding:result,as:UTF8.self))
