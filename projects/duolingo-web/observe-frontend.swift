// Collect actual text from an isolated child, without encoding expected copy.
import AppKit
import ApplicationServices
import Foundation
import CryptoKit
import Carbon
import ImageIO

enum ObservationStop: Error { case afterQuestion(String) }
func main() throws {
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let output = URL(fileURLWithPath: CommandLine.arguments[1], relativeTo: root).standardizedFileURL
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let progress = output.appendingPathComponent("progress.json")
precondition(!FileManager.default.fileExists(atPath: progress.path), "Use a fresh output directory")
if let seedIndex = CommandLine.arguments.firstIndex(of: "--seed-progress"), seedIndex + 1 < CommandLine.arguments.count {
    try Data(contentsOf: root.appendingPathComponent(CommandLine.arguments[seedIndex + 1])).write(to: progress, options: .withoutOverwriting)
}
var seedPreferencesSHA: String?
if let index = CommandLine.arguments.firstIndex(of:"--seed-preferences"), index+1 < CommandLine.arguments.count {
    let data = try Data(contentsOf:root.appendingPathComponent(CommandLine.arguments[index+1]))
    try data.write(to:URL(fileURLWithPath:progress.path+".preferences.json"),options:.withoutOverwriting)
    seedPreferencesSHA=SHA256.hash(data:data).map{String(format:"%02x",$0)}.joined()
}
let eighthReview = CommandLine.arguments.contains("--exercise-eighth-review")
let errorReview = CommandLine.arguments.contains("--exercise-error-review")
let explicitReview = CommandLine.arguments.firstIndex(of: "--review-instance").map { CommandLine.arguments[$0 + 1] }
let reviewInstance = explicitReview ?? (eighthReview ? "level-review" : errorReview ? "error-review" : "current-review")
if explicitReview != nil && !CommandLine.arguments.contains("--exercise-current-review") { throw NSError(domain:"Explicit review requires exercise-current-review",code:1) }
let childLog = output.appendingPathComponent("child.log")
FileManager.default.createFile(atPath: childLog.path, contents: nil)
let fixture = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "projects/duolingo-web/fixture-reference-en-zh-v14.json"
let candidateURL = root.appendingPathComponent("projects/education-swift/.build/debug/LingoSeed")
let candidateSHA = SHA256.hash(data: try Data(contentsOf: candidateURL)).map { String(format: "%02x", $0) }.joined()
let fixtureSHA = SHA256.hash(data: try Data(contentsOf: root.appendingPathComponent(fixture))).map { String(format: "%02x", $0) }.joined()
var clockScenario: [String: Any]?
var referenceClockMilliseconds: NSNumber?
if let index = CommandLine.arguments.firstIndex(of: "--exercise-home-clock"), index + 1 < CommandLine.arguments.count {
    clockScenario = try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent(CommandLine.arguments[index + 1]))) as? [String: Any]
    guard let rows = clockScenario?["states"] as? [[String: Any]], !rows.isEmpty,
          let epoch = rows[0]["epoch_milliseconds"] as? NSNumber else { throw NSError(domain:"Clock scenario missing states",code:1) }
    referenceClockMilliseconds = epoch
}
func launchChild() throws -> Process {
    let process = Process()
    process.executableURL = candidateURL
    process.arguments = ["--fixture", root.appendingPathComponent(fixture).path, "--progress", progress.path, "--render-metadata", output.appendingPathComponent("window.json").path]
    if let epoch = referenceClockMilliseconds { process.arguments! += ["--reference-clock-milliseconds", epoch.stringValue] }
    if let index = CommandLine.arguments.firstIndex(of: "--reference-color-scheme"), index + 1 < CommandLine.arguments.count {
        process.arguments! += ["--reference-color-scheme", CommandLine.arguments[index + 1]]
    }
    if CommandLine.arguments.contains("--exercise-general-listening-decline") {
        process.arguments! += ["--general-practice-fixture", root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-general-listening-decline-v1.json").path]
    }
    if CommandLine.arguments.contains("--exercise-current-review") || errorReview {
        process.arguments! += ["--general-practice-fixture", root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-" + reviewInstance + "-v1.json").path]
    }
    if CommandLine.arguments.contains("--exercise-speech-denied") { process.arguments! += ["--verify-speech-denied"] }
    process.standardOutput = FileHandle.nullDevice
    let log = try FileHandle(forWritingTo: childLog); try log.seekToEnd()
    process.standardError = log
    try process.run()
    return process
}
var child = try launchChild()
defer { if child.isRunning { child.terminate(); child.waitUntilExit() } }
var app = AXUIElementCreateApplication(child.processIdentifier)
func attr(_ element: AXUIElement, _ name: String) -> AnyObject? {
    var result: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, name as CFString, &result) == .success else { return nil }
    return result
}
func nodes(_ element: AXUIElement, _ depth: Int = 0) -> [AXUIElement] {
    guard depth < 24 else { return [] }
    return [element] + ((attr(element, kAXChildrenAttribute) as? [AXUIElement]) ?? []).flatMap { nodes($0, depth + 1) }
}
func current() -> [AXUIElement] {
    ((attr(app, kAXWindowsAttribute) as? [AXUIElement]) ?? []).flatMap { nodes($0) }
}
let deadline = Date().addingTimeInterval(12)
while Date() < deadline && !current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "course-entry" }) {
    Thread.sleep(forTimeInterval: 0.1)
}
guard current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "course-entry" }) else { throw ProbeError(message: "No child home observed") }
func configureWindow() {
if let window = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.first {
    let metadata = try? Data(contentsOf: output.appendingPathComponent("window.json"))
    let value = metadata.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] }
    let frame = value?["window_points"] as? [Double]
    let rect = value?["content_rect_points"] as? [Double]
    let decoration = (frame?.last ?? 0) - (rect?.last ?? 0)
    let requested = CommandLine.arguments.firstIndex(of: "--source-viewport").map { index -> [Double] in
        guard index + 2 < CommandLine.arguments.count,
              let width=Double(CommandLine.arguments[index+1]),let height=Double(CommandLine.arguments[index+2]),width>0,height>0 else { preconditionFailure("Explicit measured source viewport required") }
        return [width,height]
    } ?? [1200,732]
    var size = CGSize(width: requested[0], height: requested[1] + decoration)
    AXUIElementSetAttributeValue(window, kAXSizeAttribute as CFString, AXValueCreate(.cgSize, &size)!)
}
Thread.sleep(forTimeInterval: 0.6)
AXUIElementSetAttributeValue(app, kAXFrontmostAttribute as CFString, kCFBooleanTrue)
if let window = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.first { AXUIElementPerformAction(window, kAXRaiseAction as CFString) }
Thread.sleep(forTimeInterval: 0.2)
}
configureWindow()
func capture(_ name: String) throws {
    try activateOwnedInputTarget()
    var number: Int?
    let deadline = Date().addingTimeInterval(10)
    repeat {
        let info = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        number = info.first(where: { ($0[kCGWindowOwnerPID as String] as? Int) == Int(child.processIdentifier) && ($0[kCGWindowLayer as String] as? Int) == 0 })?[kCGWindowNumber as String] as? Int
        if number == nil { Thread.sleep(forTimeInterval: 0.1) }
    } while number == nil && child.isRunning && Date() < deadline
    guard let number else { throw ProbeError(message: "No owned visible window") }
    let process = Process(); process.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
    process.arguments = ["-x", "-o", "-l", String(number), output.appendingPathComponent(name + ".png").path]
    try process.run(); process.waitUntilExit()
    guard process.terminationStatus == 0 else { throw ProbeError(message: "Owned window capture failed, exit \(process.terminationStatus)") }
}
func observe() -> [String: Any] {
    let strings = Set(current().flatMap { node in
        [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute].compactMap { attr(node, $0) as? String }.filter { !$0.isEmpty }
    })
    var elements: [String: Any] = [:]
    var controls: [[String:Any]] = []
    let metadata = (try? Data(contentsOf: output.appendingPathComponent("window.json"))).flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] }
    let content = metadata?["content_rect_points"] as? [Double]
    var origin = CGPoint.zero
    if let window = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.first, let position = attr(window, kAXPositionAttribute) { AXValueGetValue(position as! AXValue, .cgPoint, &origin) }
    for node in current() {
        let identifier=attr(node,kAXIdentifierAttribute) as? String
        var element: [String: Any] = ["enabled": attr(node, kAXEnabledAttribute) as? Bool ?? false, "role": attr(node, kAXRoleAttribute) as? String ?? "", "value": attr(node, kAXValueAttribute) as? String ?? ""]
        // NSButton radios expose NSNumber, not text. Keep unknown values absent.
        if element["role"] as? String == "AXRadioButton",
           let value = attr(node, kAXValueAttribute) as? NSNumber,
           [0, 1].contains(value.intValue) {
            element["checked"] = value.intValue == 1
            element["numeric_value"] = value
        }
        if let position = attr(node, kAXPositionAttribute), let size = attr(node, kAXSizeAttribute), let content {
            var point = CGPoint.zero; var dimensions = CGSize.zero
            AXValueGetValue(position as! AXValue, .cgPoint, &point); AXValueGetValue(size as! AXValue, .cgSize, &dimensions)
            element["rect"] = [point.x - origin.x - content[0], point.y - origin.y - content[1], dimensions.width, dimensions.height]
        }
        if let id=identifier {elements[id]=element}
        if ["AXButton","AXLink","AXRadioButton","AXTextField","AXCheckBox","AXPopUpButton"].contains(element["role"] as? String ?? "") {
            var row=element
            row["identifier"]=identifier as Any
            row["name"]=[kAXTitleAttribute,kAXDescriptionAttribute,kAXValueAttribute].compactMap{attr(node,$0) as? String}.first(where:{!$0.isEmpty}) ?? ""
            controls.append(row)
        }
    }
    return ["accessible_text": strings.sorted(), "elements": elements,"control_inventory":controls,"control_inventory_limitations":["Actual AX controls include nodes without developer identifiers; no invocation or hit-test coverage inferred"]]
}
func bindCaptures(_ states: inout [String: [String: Any]], names: [String: String] = [:]) throws {
    if output.path.hasPrefix(root.path + "/"),
       let metadata = try JSONSerialization.jsonObject(with: Data(contentsOf: output.appendingPathComponent("window.json"))) as? [String: Any] {
        for stateName in Array(states.keys) {
            let filename = (names[stateName] ?? stateName) + ".png"
            let file = output.appendingPathComponent(filename)
            if FileManager.default.fileExists(atPath: file.path) {
                states[stateName]?["capture"] = ["path": String(file.path.dropFirst(root.path.count + 1)),
                    "content_rect_points": metadata["content_rect_points"]!, "backing_scale": metadata["backing_scale"]!,
                    "window_points": metadata["window_points"]!]
            }
        }
    }
}
var pointerActions: [[String: Any]] = []
func movePointer(to id: String) -> Bool {
    guard let node = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == id }),
          let position = attr(node, kAXPositionAttribute), let size = attr(node, kAXSizeAttribute) else { return false }
    var point = CGPoint.zero; var dimensions = CGSize.zero
    AXValueGetValue(position as! AXValue, .cgPoint, &point); AXValueGetValue(size as! AXValue, .cgSize, &dimensions)
    let center = CGPoint(x: point.x + dimensions.width / 2, y: point.y + dimensions.height / 2)
    pointerActions.append(["control": id, "position": [point.x, point.y], "size": [dimensions.width, dimensions.height], "center": [center.x, center.y]])
    CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: center, mouseButton: .left)?.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.4)
    let ready = Date().addingTimeInterval(8)
    while current().isEmpty && child.isRunning && Date() < ready { Thread.sleep(forTimeInterval: 0.1) }
    pointerActions[pointerActions.count - 1]["child_running"] = child.isRunning
    pointerActions[pointerActions.count - 1]["window_count"] = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.count ?? -1
    let running = NSRunningApplication(processIdentifier: child.processIdentifier)
    pointerActions[pointerActions.count - 1]["active"] = running?.isActive
    pointerActions[pointerActions.count - 1]["hidden"] = running?.isHidden
    pointerActions[pointerActions.count - 1]["all_owned_windows"] = ((CGWindowListCopyWindowInfo(.optionAll, kCGNullWindowID) as? [[String: Any]]) ?? []).filter { ($0[kCGWindowOwnerPID as String] as? Int) == Int(child.processIdentifier) }.map { ["layer": $0[kCGWindowLayer as String] as Any, "bounds": $0[kCGWindowBounds as String] as Any, "onscreen": $0[kCGWindowIsOnscreen as String] as Any] }
    try? JSONSerialization.data(withJSONObject: pointerActions, options: [.prettyPrinted]).write(to: output.appendingPathComponent("pointer.json"))
    return true
}
func activateOwnedInputTarget() throws {
    guard child.isRunning, let running = NSRunningApplication(processIdentifier: child.processIdentifier) else { throw ProbeError(message: "Owned input process missing") }
    running.activate(options: [.activateAllWindows])
    AXUIElementSetAttributeValue(app, kAXFrontmostAttribute as CFString, kCFBooleanTrue)
    if let window = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.first { AXUIElementPerformAction(window, kAXRaiseAction as CFString) }
    let deadline = Date().addingTimeInterval(3)
    while !running.isActive && Date() < deadline { Thread.sleep(forTimeInterval: 0.05) }
    guard running.isActive else { throw ProbeError(message: "Owned input process not active") }
}
func fillInput(_ value: String, identifier: String = "answer-input", verifyValue: Bool = true) throws {
    try waitFor(identifier)
    try activateOwnedInputTarget()
    let input = current().first { (attr($0, kAXIdentifierAttribute) as? String) == identifier }!
    guard AXUIElementSetAttributeValue(input, kAXFocusedAttribute as CFString, kCFBooleanTrue) == .success else { throw ProbeError(message: "Cannot focus actual input") }
    let previousSource = TISCopyCurrentKeyboardInputSource().takeRetainedValue()
    let sourceID: (TISInputSource) -> String = { source in
        guard let value = TISGetInputSourceProperty(source, kTISPropertyInputSourceID) else { return "unknown" }
        return Unmanaged<CFString>.fromOpaque(value).takeUnretainedValue() as String
    }
    let layouts = TISCreateInputSourceList([kTISPropertyInputSourceType: kTISTypeKeyboardLayout!, kTISPropertyInputSourceIsASCIICapable: true, kTISPropertyInputSourceIsEnabled: true] as CFDictionary, false).takeRetainedValue() as! [TISInputSource]
    guard let latin = layouts.first, TISSelectInputSource(latin) == noErr else { throw ProbeError(message: "No enabled ASCII test keyboard layout selected") }
    defer {
        let status = TISSelectInputSource(previousSource)
        let receipt: [String: Any] = ["control":identifier,"previous":sourceID(previousSource),"temporary":sourceID(latin),"restore_status":status,"current_after_restore":sourceID(TISCopyCurrentKeyboardInputSource().takeRetainedValue()),"product_keyboard_rules_changed":false]
        let file = output.appendingPathComponent("input-source.json")
        var rows = (try? Data(contentsOf:file)).flatMap { try? JSONSerialization.jsonObject(with:$0) as? [[String:Any]] } ?? []
        rows.append(receipt); try? JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]).write(to:file)
    }
    Thread.sleep(forTimeInterval:0.15)
    // AX value assignment changes the field but can bypass SwiftUI's editing binding.
    // Send actual keyboard events to our isolated child instead.
    for down in [true, false] {
        let selectAll = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: down)!
        selectAll.flags = .maskCommand; selectAll.postToPid(child.processIdentifier)
    }
    for down in [true, false] { CGEvent(keyboardEventSource: nil, virtualKey: 51, keyDown: down)!.postToPid(child.processIdentifier) }
    if !value.isEmpty {
        let chars = Array(value.utf16)
        for down in [true, false] {
            let event = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: down)!
            chars.withUnsafeBufferPointer { event.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: $0.baseAddress!) }
            event.postToPid(child.processIdentifier)
        }
    }
    if verifyValue { try waitFor(identifier, value: value) } else { try waitFor(identifier) }
    Thread.sleep(forTimeInterval: 0.15)
}

func captureGeneralCharacterFrames(_ key: String, _ stage: String, _ question: [String: Any]) throws {
    guard CommandLine.arguments.contains("--capture-character-frames"),
          let index = CommandLine.arguments.firstIndex(of: "--character-frame-resource"), index + 1 < CommandLine.arguments.count,
          question["characterResource"] as? String == CommandLine.arguments[index + 1],
          current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "question-character" }) else { return }
    for frame in 0..<12 { try capture(key + "-character-" + stage + "-\(frame)"); Thread.sleep(forTimeInterval: 0.15) }
}

if let index = CommandLine.arguments.firstIndex(of: "--exercise-home-journey"), index + 1 < CommandLine.arguments.count {
    let scenarioURL = root.appendingPathComponent(CommandLine.arguments[index + 1])
    let scenario = try JSONSerialization.jsonObject(with: Data(contentsOf: scenarioURL)) as! [String: Any]
    let journeys = scenario["journeys"] as! [[String: Any]]
    var states: [String: [String: Any]] = [:]; var attempts: [[String: Any]] = []
    for (index, journey) in journeys.enumerated() {
        if index > 0 { child.terminate(); child.waitUntilExit(); child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier) }
        try waitFor("path-chest"); configureWindow()
        let id = journey["id"] as! String
        do {
            let steps = journey["steps"] as? [[String: Any]] ?? [
                ["native_action":journey["native_action"]!, "operation":journey["operation"] ?? "click", "state":"journey-" + id],
                ["native_action":journey["native_return"]!, "state":"journey-" + id + "-return"]]
            for step in steps {
                if step["operation"] as? String == "restart" {
                    child.terminate(); child.waitUntilExit(); child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
                    try waitFor("path-chest"); configureWindow()
                }
                try activateOwnedInputTarget()
                let control = step["native_action"] as! String
                if step["operation"] as? String == "escape" {
                    for down in [true,false] {CGEvent(keyboardEventSource:nil,virtualKey:53,keyDown:down)?.postToPid(child.processIdentifier)}
                }
                else if step["operation"] as? String == "fill" {
                    guard let text=step["text"] as? String else {throw ProbeError(message:"Owned input text required")}
                    try fillInput(text, identifier:control)
                }
                else if step["operation"] as? String == "scroll" {
                    let anchor = step["scroll_anchor"] as! String
                    let amount = (step["scroll_pixels"] as! NSNumber).int32Value
                    let before = ((observe()["elements"] as? [String:Any])?[anchor] as? [String:Any])?["rect"] as? [Double]
                    guard movePointer(to:control), NSRunningApplication(processIdentifier:child.processIdentifier)?.isActive == true,
                          let event = CGEvent(scrollWheelEvent2Source:nil,units:.pixel,wheelCount:1,wheel1:amount,wheel2:0,wheel3:0),
                          let point = CGEvent(source:nil)?.location else {throw ProbeError(message:"No active owned scroll target")}
                    event.location=point;event.post(tap:.cghidEventTap)
                    Thread.sleep(forTimeInterval:0.7)
                    var after: [Double]?
                    let scrollDeadline=Date().addingTimeInterval(8)
                    var samples=0
                    repeat {
                        after=((observe()["elements"] as? [String:Any])?[anchor] as? [String:Any])?["rect"] as? [Double]
                        samples += 1
                        if let before,let after,before != after {break}
                        if !child.isRunning {break}
                        Thread.sleep(forTimeInterval:0.1)
                    } while Date() < scrollDeadline
                    let file=output.appendingPathComponent("scroll.json")
                    var rows=(try? Data(contentsOf:file)).flatMap {try? JSONSerialization.jsonObject(with:$0) as? [[String:Any]]} ?? []
                    rows.append(["target":control,"anchor":anchor,"pixels":amount,"before":before as Any,"after":after as Any,"samples":samples,"child_running":child.isRunning])
                    try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted]).write(to:file)
                    guard let before,let after else {throw ProbeError(message:"Owned scroll anchor unavailable after bounded live re-observation")}
                    guard before != after else {throw ProbeError(message:"Owned scroll did not move measured anchor")}
                }
                else if step["operation"] as? String == "record_audio" {
                    guard let index=CommandLine.arguments.firstIndex(of:"--audio-recorder"),index+1<CommandLine.arguments.count,
                          let name=step["recording"] as? String,name.range(of:"^[a-z0-9-]+$",options:.regularExpression) != nil,
                          let duration=step["duration_seconds"] as? Int,duration>0 && duration<=30 else {throw ProbeError(message:"Owned recorder, local filename and bounded duration required")}
                    let actions=output.appendingPathComponent(name+"-actions.json")
                    try JSONSerialization.data(withJSONObject:[control]).write(to:actions,options:.withoutOverwriting)
                    let recorder=Process();recorder.executableURL=root.appendingPathComponent(CommandLine.arguments[index+1])
                    recorder.arguments=[String(child.processIdentifier),output.appendingPathComponent(name+".wav").path,String(duration),actions.path]
                    let log=output.appendingPathComponent(name+".log");FileManager.default.createFile(atPath:log.path,contents:nil)
                    let handle=try FileHandle(forWritingTo:log);recorder.standardOutput=handle;recorder.standardError=handle
                    try recorder.run();recorder.waitUntilExit()
                    guard recorder.terminationStatus==0 else {throw ProbeError(message:"Owned application recording failed; preserve actual log")}
                }
                else if step["operation"] as? String == "focus_key" {
                    try waitFor(control);try activateOwnedInputTarget()
                    let target=current().first { (attr($0,kAXIdentifierAttribute) as? String)==control }!
                    let focused=AXUIElementSetAttributeValue(target,kAXFocusedAttribute as CFString,kCFBooleanTrue)
                    guard focused == .success else {throw ProbeError(message:"Actual AX keyboard focus failed: \(focused.rawValue)")}
                    guard let key=step["key_code"] as? Int,[36,49,76].contains(key) else {throw ProbeError(message:"Registered Return/Space key required")}
                    CGEvent(keyboardEventSource:nil,virtualKey:CGKeyCode(key),keyDown:true)?.post(tap:.cghidEventTap)
                    CGEvent(keyboardEventSource:nil,virtualKey:CGKeyCode(key),keyDown:false)?.post(tap:.cghidEventTap)
                    let file=output.appendingPathComponent("focus-key.json")
                    var rows=(try? Data(contentsOf:file)).flatMap {try? JSONSerialization.jsonObject(with:$0) as? [[String:Any]]} ?? []
                    rows.append(["control":control,"key_code":key,"ax_focus_status":focused.rawValue,"source":"Actual focused owned AX control and hardware key event"])
                    try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]).write(to:file)
                }
                else if step["operation"] as? String == "observe" { /* Capture the already reached state without another action. */ }
                else if step["operation"] as? String == "pointer_click" {try clickOwnedControl(control,xFraction:step["x_fraction"] as? Double ?? 0.5)}
                else if step["operation"] as? String == "hover" { guard movePointer(to:control) else { throw ProbeError(message:"Missing hover target") } }
                else { try press(control) }
                Thread.sleep(forTimeInterval:0.7)
                if let state = step["state"] as? String {
                    var facts = observe()
                    if let aliases = step["element_aliases"] as? [String:String] {
                        var measured = facts["elements"] as? [String:Any] ?? [:]
                        for (sourceID,nativeID) in aliases {
                            if var value = measured[nativeID] as? [String:Any] {
                                value["native_identifier"] = nativeID
                                measured[sourceID] = value
                            }
                        }
                        facts["elements"] = measured
                    }
                    let elements = facts["elements"] as? [String: Any] ?? [:]
                    let profile = elements["path-profile-later"] != nil
                    let legendary = !profile && elements["legendary-quit"] != nil
                    facts["interactions"] = ["profile_present":profile, "legendary_present":legendary,
                        "completed_popover_present": !profile && !legendary && elements["completed-practice"] != nil,
                        "guest_profile_present":elements["guest-profile-joined"] != nil, "guest_introduction_present":elements["guest-profile-later"] != nil, "guest_error_present":elements["guest-profile-error"] != nil,
                        "status_selected":elements["leaderboard-selected-status"] != nil, "footer_status_visible":elements["leaderboard-footer-status"] != nil, "status_clear_visible":elements["leaderboard-clear"] != nil,
                        "guest_languages_present":elements["guest-profile-languages-close"] != nil,"home_course_present":elements["course-entry"] != nil,"practice_present":elements["pair-left-0"] != nil, "learn_present":elements["start-lesson"] != nil, "exit_confirmation_present":elements["practice-quit-confirm"] != nil]
                    var captureAttempts: [[String: Any]] = []
                    var validCapture = false
                    let metadata = try JSONSerialization.jsonObject(with:Data(contentsOf:output.appendingPathComponent("window.json"))) as! [String: Any]
                    let points = metadata["window_points"] as! [Double]; let scale = metadata["backing_scale"] as! Double
                    let expected = points.map { Int(($0 * scale).rounded()) }
                    for attempt in 1...8 {
                        let name = state + "-capture-" + String(attempt); try capture(name)
                        let url = output.appendingPathComponent(name + ".png")
                        let source = CGImageSourceCreateWithURL(url as CFURL,nil)!
                        let properties = CGImageSourceCopyPropertiesAtIndex(source,0,nil)! as NSDictionary
                        let actual = [(properties[kCGImagePropertyPixelWidth] as! NSNumber).intValue,(properties[kCGImagePropertyPixelHeight] as! NSNumber).intValue]
                        captureAttempts.append(["attempt":attempt,"pixels":actual,"expected":expected,"path":url.lastPathComponent])
                        if actual == expected { try FileManager.default.copyItem(at:url,to:output.appendingPathComponent(state + ".png"));validCapture = true;break }
                        Thread.sleep(forTimeInterval:0.5)
                    }
                    facts["capture_attempts"] = captureAttempts
                    states[state] = facts
                    guard validCapture else { throw ProbeError(message:"Owned capture never matched measured viewport: " + state) }
                }
            }
            attempts.append(["id":id,"failure":NSNull()])
        } catch { attempts.append(["id":id,"failure":String(describing:error)]) }
    }
    try bindCaptures(&states)
    let failures = attempts.filter { !($0["failure"] is NSNull) }
    let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,"attempts":attempts,
        "seed_preferences_sha256":seedPreferencesSHA as Any,"candidate_binary_sha256":candidateSHA,"fixture_sha256":fixtureSHA,"scenario_sha256":SHA256.hash(data:try Data(contentsOf:scenarioURL)).map{String(format:"%02x",$0)}.joined(),
        "failure":failures.isEmpty ? NSNull() : String(describing:failures),"limitations":["No acoustic equality claim; actual images retain clock and animation phase differences"]]
    try JSONSerialization.data(withJSONObject:receipt,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"),options:.withoutOverwriting)
    print("Collected \(states.count) actual home journey states, \(failures.count) failed journeys")
    if !failures.isEmpty { throw ProbeError(message:"Home journey execution failed; inspect observed.json attempts") }
    return
}
if let scenario = clockScenario, let rows = scenario["states"] as? [[String: Any]] {
    var states: [String: [String: Any]] = [:]; var failure: String?
    do {
        for (index, row) in rows.enumerated() {
            guard let key = row["id"] as? String, let epoch = row["epoch_milliseconds"] as? NSNumber else { throw ProbeError(message:"Invalid clock state") }
            if index > 0 {
                child.terminate(); child.waitUntilExit(); referenceClockMilliseconds = epoch
                child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
            }
            try waitFor("path-chest"); configureWindow(); try waitFor("home-league-countdown")
            states[key] = observe(); try capture(key)
        }
    } catch { failure = String(describing:error) }
    try bindCaptures(&states)
    let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states, "scenario":scenario,
        "candidate_binary_sha256":candidateSHA,"fixture_sha256":fixtureSHA,"failure":failure as Any? ?? NSNull(),
        "limitations":["Clock fixture controls label epoch, not source/native animation phase"]]
    try JSONSerialization.data(withJSONObject:receipt,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"),options:.withoutOverwriting)
    print("Collected \(states.count) actual home clock states")
    if let failure { throw ProbeError(message:failure) }; return
}
if let index = CommandLine.arguments.firstIndex(of:"--exercise-matching-audio"), index+1 < CommandLine.arguments.count {
    try press("nav-quests"); try waitFor("quests-practice"); try press("quests-practice"); try waitFor("pair-left-0")
    try press("pair-left-0"); Thread.sleep(forTimeInterval:1.5)
    let actions = output.appendingPathComponent("audio-actions.json")
    try JSONSerialization.data(withJSONObject:["pair-right-1"]).write(to:actions)
    let recorder=Process();recorder.executableURL=URL(fileURLWithPath:CommandLine.arguments[index+1])
    recorder.arguments=[String(child.processIdentifier),output.appendingPathComponent("matching-error.wav").path,"5",actions.path]
    let log=output.appendingPathComponent("recorder.log");FileManager.default.createFile(atPath:log.path,contents:nil)
    recorder.standardOutput=try FileHandle(forWritingTo:log);recorder.standardError=recorder.standardOutput
    try recorder.run();recorder.waitUntilExit()
    guard recorder.terminationStatus==0 else { throw ProbeError(message:"Owned matching error audio recorder failed") }
    var states=["matching-error":observe()];try capture("matching-error");try bindCaptures(&states)
    let receipt:[String:Any] = ["kind":"owned_native_ax_observation","states":states,"failure":NSNull(),"candidate_binary_sha256":candidateSHA,"fixture_sha256":fixtureSHA,"general_fixture_sha256":SHA256.hash(data:try Data(contentsOf:root.appendingPathComponent("projects/education-swift/Sources/LingoSeed/Resources/Reference/general-practice.json"))).map{String(format:"%02x",$0)}.joined(),"limitations":["Original browser loopback unavailable; candidate output vs original resource is diagnostic only"]]
    try JSONSerialization.data(withJSONObject:receipt,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"));return
}
if CommandLine.arguments.contains("--exercise-home-motion") || CommandLine.arguments.contains("--exercise-path-chest") { try waitFor("path-chest") }
let initialHomeState = CommandLine.arguments.contains("--seed-progress") ? "seeded-home" : "home"
var states = [initialHomeState: observe()]
try capture("home-window")
if CommandLine.arguments.contains("--exercise-home-motion") {
    // A seeded eight-lesson home is not the historical first-lesson home reference.
    states["home-motion-initial"] = states.removeValue(forKey:initialHomeState)
    var frames: [[String:Any]] = []; var failure: String?
    do {
        for index in 0..<6 {
            let key = "home-motion-frame-\(index)"; let at = Date().timeIntervalSince1970
            states[key] = observe(); try capture(key)
            frames.append(["state":key,"at":at]); Thread.sleep(forTimeInterval:0.3)
        }
    } catch { failure = String(describing:error) }
    try bindCaptures(&states, names:["home-motion-initial":"home-window"])
    let receipt: [String:Any] = ["kind":"owned_native_ax_observation","states":states,"frames":frames,"failure":failure as Any? ?? NSNull(),"candidate_binary_sha256":candidateSHA,"fixture_sha256":fixtureSHA,"limitations":["Unaligned live animation captures do not prove phase/timing equality"]]
    try JSONSerialization.data(withJSONObject:receipt,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"),options:.withoutOverwriting)
    print("Collected \(frames.count) actual home motion frames")
    if failure != nil { throw ProbeError(message:failure!) }; return
}
if CommandLine.arguments.contains("--exercise-path-chest") {
    var failure: String?
    func saveChest(_ key: String) throws { states[key] = observe(); try capture(key) }
    do {
        try waitFor("path-chest"); try saveChest("chest-dismissed")
        try press("path-chest"); Thread.sleep(forTimeInterval: 0.5); try saveChest("chest-after-click")
        try Data(contentsOf: progress).write(to: output.appendingPathComponent("progress-after.json"))
        child.terminate(); child.waitUntilExit(); child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
        try waitFor("path-chest"); configureWindow(); try saveChest("chest-reloaded")
        try press("start-lesson-3"); Thread.sleep(forTimeInterval: 0.4); try saveChest("chest-practice-entry"); Thread.sleep(forTimeInterval: 0.5); try saveChest("chest-practice-entry-settled")
        if CommandLine.arguments.contains("--exercise-path-profile") {
            try press("start-lesson-confirm"); try waitFor("path-profile-later"); try saveChest("chest-practice-start-profile")
            try press("path-profile-later"); Thread.sleep(forTimeInterval: 0.4)
            var returned = observe(); let elements = returned["elements"] as! [String: Any]
            returned["interactions"] = ["profile_closed":elements["path-profile-later"] == nil]
            states["chest-practice-profile-dismissed"] = returned; try capture("chest-practice-profile-dismissed")
            if CommandLine.arguments.contains("--exercise-registration") {
                try press("start-lesson-confirm"); try waitFor("path-profile-create"); try press("path-profile-create")
                try waitFor("path-age-input"); try saveChest("path-age-form")
                try fillInput("28", identifier: "path-age-input")
                try fillInput("", identifier: "path-age-input")
                let disabled = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "path-age-next" }.flatMap { attr($0,kAXEnabledAttribute) as? Bool } == false
                try fillInput("28", identifier: "path-age-input")
                var filled = observe(); let value = current().first { (attr($0,kAXIdentifierAttribute) as? String) == "path-age-input" }.flatMap { attr($0,kAXValueAttribute) as? String }
                filled["interactions"] = ["cleared_disabled":disabled,"age_value_correct":value == "28"]
                states["registration-filled"] = filled; try capture("registration-filled")
                if CommandLine.arguments.contains("--exercise-registration-controls") {
                    try saveChest("registration-clear-before"); try press("registration-age-clear")
                    try waitFor("path-age-input", value: "")
                    var cleared = observe(); let next = current().first { (attr($0,kAXIdentifierAttribute) as? String) == "path-age-next" }
                    cleared["interactions"] = ["clear_button_empties_age":current().first { (attr($0,kAXIdentifierAttribute) as? String) == "path-age-input" }.flatMap { attr($0,kAXValueAttribute) as? String } == "", "clear_button_disables_next":next.flatMap { attr($0,kAXEnabledAttribute) as? Bool } == false]
                    states["registration-cleared"] = cleared; try capture("registration-cleared")
                    try fillInput("28", identifier: "path-age-input")
                }
                try press("path-age-next"); try waitFor("registration-email"); try saveChest("registration-methods")
                try press("registration-email"); try waitFor("registration-address"); try saveChest("registration-email")
                if CommandLine.arguments.contains("--exercise-registration-controls") {
                    try fillInput("abc", identifier: "registration-password", verifyValue: false); Thread.sleep(forTimeInterval:0.3); try saveChest("registration-password-hidden")
                    try press("registration-password-reveal"); try waitFor("registration-password", value: "abc")
                    var visible = observe(); let shown = current().first { (attr($0,kAXIdentifierAttribute) as? String) == "registration-password" }
                    let preserved = shown.flatMap { attr($0,kAXValueAttribute) as? String } == "abc"
                    let plaintext = shown.flatMap { attr($0,kAXSubroleAttribute) as? String } != "AXSecureTextField"
                    try capture("registration-password-visible")
                    try press("registration-password-reveal"); Thread.sleep(forTimeInterval:0.3)
                    let hidden = current().first { (attr($0,kAXIdentifierAttribute) as? String) == "registration-password" }.flatMap { attr($0,kAXSubroleAttribute) as? String } == "AXSecureTextField"
                    visible["interactions"] = ["reveal_preserves_value":preserved,"reveal_shows_text":plaintext,"rehide_restores_secure":hidden]
                    states["registration-password-visible"] = visible
                    try fillInput("", identifier: "registration-password")
                }
                try press("registration-submit"); Thread.sleep(forTimeInterval:0.4); try saveChest("registration-email-invalid")
                try press("registration-back"); try waitFor("registration-email"); try saveChest("registration-back-methods")
                try press("registration-back"); try waitFor("path-age-input"); try saveChest("registration-back-age")
                try press("registration-back"); Thread.sleep(forTimeInterval:0.4); try saveChest("registration-closed")
            }
        }
    } catch { failure = String(describing: error); states["failure-boundary"] = observe(); try? capture("failure-boundary") }
    try bindCaptures(&states, names: ["home":"home-window", "seeded-home":"home-window"])
    let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states, "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
        "observed_at":ISO8601DateFormatter().string(from:Date()), "failure":failure as Any,
        "action":"Actual path chest click, persisted ledger, real process restart, next Practice popover",
        "limitations":["Leaderboard interruption not implemented; next Practice Start opens observed profile prompt; OAuth, successful registration and subsequent practice challenges unimplemented; no acoustic or animation equivalence claim"]]
    try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"))
    if let failure { throw ProbeError(message:failure) }
    return
}
if CommandLine.arguments.contains("--observe-quests") || CommandLine.arguments.contains("--exercise-current-review") || errorReview || eighthReview {
    try press("nav-quests"); Thread.sleep(forTimeInterval: 0.5)
    states["quests"] = observe(); try capture("quests")
    if CommandLine.arguments.contains("--exercise-current-review") || errorReview || eighthReview {
        let practiceURL = root.appendingPathComponent(eighthReview ? fixture : "projects/duolingo-web/fixture-reference-en-zh-" + reviewInstance + "-v1.json")
        let data = try JSONSerialization.jsonObject(with: Data(contentsOf: practiceURL)) as! [String: Any]
        let course = (data["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let definitions = course["lessons"] as! [[String: Any]]
        let definition = eighthReview ? definitions.last! : definitions[0]
        let questions = definition["questions"] as! [[String: Any]]
        let speech = (definition["deferredSpeech"] as! [[String: Any]])[0]
        var failure: String?
        func saveReviewState(_ key: String) throws { states[key] = observe(); try capture(key) }
        do {
            if eighthReview {
                try press("nav-learn"); try waitFor("start-lesson-1")
                try press("start-lesson-1"); try waitFor("start-lesson-confirm"); try press("start-lesson-confirm")
                try waitFor("lesson-entry"); try saveReviewState("eighth-entry"); try press("lesson-entry-start")
            } else if explicitReview != nil {
                try press("nav-leaderboards"); try waitFor("leaderboard-practice"); try press("leaderboard-practice")
            } else { try press("quests-practice") }
            for q in questions {
                let key = q["id"] as! String
                if key == speech["beforeQuestionID"] as? String {
                    try waitFor("speech-title", value: speech["id"] as? String)
                    try saveReviewState(reviewInstance+"-speech")
                    try press("speech-decline"); try waitFor("speech-closed"); try saveReviewState(reviewInstance+"-speech-declined")
                    try press("speech-continue")
                }
                try waitFor(q["kind"] as? String == "matching" ? "question-prompt" : "question-title",
                            value: q["kind"] as? String == "matching" ? key : q["prompt"] as? String)
                try saveReviewState(key)
                switch q["kind"] as? String {
                case "matching":
                    for p in q["pairs"] as! [[String: Any]] { try press("pair-left-" + (p["id"] as! String)); try press("pair-right-" + (p["id"] as! String)) }
                case "word_tiles":
                    for id in q["answer_words"] as! [String] { try press("word-bank-"+id) }
                    if eighthReview && key == "level-review-q3", let index = CommandLine.arguments.firstIndex(of: "--eighth-feedback-audio-recorder"), index + 1 < CommandLine.arguments.count {
                        let actions = output.appendingPathComponent("audio-actions.json")
                        try JSONSerialization.data(withJSONObject: ["check"]).write(to: actions, options: .withoutOverwriting)
                        let recorder = Process(); recorder.executableURL = URL(fileURLWithPath: CommandLine.arguments[index+1])
                        recorder.arguments = [String(child.processIdentifier), output.appendingPathComponent("eighth-feedback.wav").path, "7", actions.path]
                        let log = output.appendingPathComponent("audio-recorder.log"); FileManager.default.createFile(atPath: log.path, contents: nil)
                        let handle = try FileHandle(forWritingTo: log); recorder.standardOutput = handle; recorder.standardError = handle
                        try recorder.run(); recorder.waitUntilExit()
                        guard recorder.terminationStatus == 0 else { throw ProbeError(message: "Owned eighth feedback recording failed") }
                    } else { try press("check") }
                case "text_entry": try fillInput(q["answer"] as! String); try press("check")
                default: try press("option-" + (errorReview && key == "error-review-q1" ? "1" : (q["answer"] as! String))); try press("check")
                }
                try waitFor("continue"); try saveReviewState(key+"-feedback"); try press("continue")
                if let intro = (definition["interludes"] as? [[String: Any]])?.first(where: { $0["afterQuestionID"] as? String == key }) {
                    let id = intro["id"] as! String
                    try waitFor("lesson-interlude", value: id); try saveReviewState(id); try press("interlude-continue")
                }
            }
            if errorReview {
                let intro = definition["reviewInterlude"] as! [String: Any]
                try waitFor("lesson-interlude", value: intro["id"] as? String)
                try saveReviewState("error-review-correction-intro"); try press("interlude-continue")
                let q = questions.first { $0["id"] as? String == "error-review-q1" }!
                try waitFor("question-title", value: q["prompt"] as? String)
                try saveReviewState("error-review-correction")
                try press("option-" + (q["answer"] as! String)); try press("check")
                try waitFor("continue"); try saveReviewState("error-review-correction-feedback"); try press("continue")
            }
            try waitFor("lesson-complete", value: errorReview ? "你莫不是特工？" : "完美！"); try saveReviewState(reviewInstance+"-result")
            try press("settlement-secondary"); try waitFor("result-review-title")
            try saveReviewState((explicitReview ?? (eighthReview ? "level" : errorReview ? "error" : "current"))+"-practice-review-open")
            let expandedCard = explicitReview != nil ? (definition["reviewSpeechCard"] as! Int) : eighthReview ? 7 : errorReview ? 1 : 8
            try press("review-card-"+String(expandedCard)); try waitFor("result-review-answer")
            try saveReviewState(explicitReview.map { $0+"-practice-review-speech-expanded" } ?? (eighthReview ? "level-practice-review-long-expanded" : errorReview ? "error-practice-review-wrong-expanded" : "current-practice-review-speech-expanded"))
            func scrollReview(_ amount: Int32, returned: Bool) throws {
                try activateOwnedInputTarget()
                guard movePointer(to: "review-card-8") else { throw ProbeError(message: "Cannot target active owned review scroll") }
                guard let event = CGEvent(scrollWheelEvent2Source: nil, units: .pixel, wheelCount: 1, wheel1: amount, wheel2: 0, wheel3: 0),
                      let point = CGEvent(source: nil)?.location,
                      NSRunningApplication(processIdentifier: child.processIdentifier)?.isActive == true else {
                    throw ProbeError(message: "No active owned review scroll target")
                }
                event.location = point; event.post(tap: .cghidEventTap)
                let deadline = Date().addingTimeInterval(8)
                while Date() < deadline {
                    let elements = observe()["elements"] as! [String: Any]
                    let rect = (elements["review-card-0"] as? [String: Any])?["rect"] as? [Double]
                    if let y = rect?[1], returned ? abs(y - 194) < 0.01 : y < 94 {
                        Thread.sleep(forTimeInterval: 0.5); return
                    }
                    Thread.sleep(forTimeInterval: 0.1)
                }
                throw ProbeError(message: "Actual review geometry did not change after scroll")
            }
            try scrollReview(-600, returned: false)
            try saveReviewState(reviewInstance+"-scrolled")
            if errorReview {
                try press("review-card-17"); try waitFor("result-review-answer")
                try saveReviewState("error-practice-review-correction-expanded")
            }
            try scrollReview(600, returned: true)
            try saveReviewState(reviewInstance+"-scroll-returned")
            if errorReview {
                for down in [true, false] {
                    CGEvent(keyboardEventSource: nil, virtualKey: 53, keyDown: down)?.postToPid(child.processIdentifier)
                }
                Thread.sleep(forTimeInterval: 0.5)
                var escaped = observe()
                let elements = escaped["elements"] as! [String: Any]
                let closed = elements["result-review-title"] == nil
                escaped["interactions"] = ["review_closed":closed]
                states["error-practice-review-escape"] = escaped
                try capture("error-practice-review-escape")
                if !closed { try press("result-review-close") }
            } else { try press("result-review-close") }
            try waitFor("lesson-complete")
            try saveReviewState(reviewInstance+"-closed")
            if eighthReview {
                for (key, title) in [("eighth-score-progress","离提升你的英语分数又近了一步！"),("eighth-boost-reward","到手一个经验宝！"),("eighth-legendary-offer","来向我们展示你的传奇实力吧"),("eighth-profile","来创建你的个人档案吧！")] {
                    try press("settlement-continue"); try waitFor("settlement-title", value: title); try saveReviewState(key)
                }
                try press("settlement-continue"); try waitFor("course-entry"); try saveReviewState("eighth-home")
                try Data(contentsOf:progress).write(to:output.appendingPathComponent("progress-after.json"))
                child.terminate(); child.waitUntilExit(); child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
                try waitFor("course-entry"); configureWindow(); try saveReviewState("eighth-home-restart")
            } else {
                try press("settlement-retry"); try waitFor("question-prompt", value: reviewInstance+"-q0")
                try saveReviewState(reviewInstance+"-retried")
            }
        } catch {
            failure = String(describing: error); states["failure-boundary"] = observe(); try? capture("failure-boundary")
        }
        try bindCaptures(&states, names: ["home":"home-window", "seeded-home":"home-window"])
        let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,
            "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
            "general_fixture_sha256":SHA256.hash(data:try Data(contentsOf:practiceURL)).map{String(format:"%02x",$0)}.joined(),
            "observed_at":ISO8601DateFormatter().string(from:Date()), "failure":failure as Any,
            "action":eighthReview ? "Actual default eighth lesson, entry, speech decline, twelve accepted, thirteen cards, long answer, post-result pages, home and real restart" : errorReview ? "Actual first wrong coffee, corrected hot, distinct 18 cards, scroll, close and retry" : "Actual 16-question instance, speech decline, 17-card review, expanded speech, close and retry",
            "limitations":["Explicit observed instance; retry uses that instance, not verified adaptive selection; no acoustic equality proof"]]
        try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"))
        if let failure { throw ProbeError(message: failure) }
        return
    }
    if CommandLine.arguments.contains("--exercise-general-listening-decline") {
        let practiceURL = root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-general-listening-decline-v1.json")
        let fixtureData = try JSONSerialization.jsonObject(with: Data(contentsOf: practiceURL)) as! [String: Any]
        let practice = (fixtureData["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let definition = (practice["lessons"] as! [[String: Any]])[0]
        let replacements = definition["listeningDeclineReplacements"] as! [String: [String: Any]]
        var failure: String?
        let before = try Data(contentsOf: progress)
        func saveState(_ name: String) throws { states[name] = observe(); try capture(name) }
        do {
            try press("quests-practice")
            for original in definition["questions"] as! [[String: Any]] {
                var question = original
                if let replacement = replacements[original["id"] as! String] {
                    try waitFor("listening-decline")
                    try saveState("general-listening-decline-tap-before")
                    try press("listening-decline"); try waitFor("listening-declined", value: "听力题已跳过")
                    try saveState("general-listening-decline-tap-declined")
                    try press("listening-continue")
                    question = replacement
                    try waitFor("question-title", value: replacement["prompt"] as? String)
                    try saveState("general-listening-decline-after-tap")
                }
                if question["id"] as? String == "general-listening-decline-water-tea" {
                    try waitFor("speech-title", value: "general-listening-decline-speech")
                    try saveState("general-listening-decline-after-inserted")
                    try press("speech-decline"); try waitFor("speech-closed")
                    try saveState("general-listening-decline-speech-declined-with-text")
                    try press("speech-continue")
                }
                let key = question["id"] as! String
                try waitFor(question["kind"] as? String == "matching" ? "question-prompt" : "question-title", value: question["kind"] as? String == "matching" ? key : question["prompt"] as? String)
                try saveState(key)
                switch question["kind"] as? String {
                case "matching":
                    for pair in question["pairs"] as! [[String: Any]] { try press("pair-left-" + (pair["id"] as! String)); try press("pair-right-" + (pair["id"] as! String)) }
                case "word_tiles":
                    for word in question["answer_words"] as! [String] { try press("word-bank-" + word) }
                    try press("check")
                case "text_entry":
                    try fillInput(question["answer"] as! String); try press("check")
                default:
                    try press("option-" + (question["answer"] as! String)); try press("check")
                }
                try waitFor("continue")
                try saveState(key + "-feedback")
                if key == "general-listening-decline-coffee-milk" { try saveState("general-listening-decline-coffee-milk-feedback-detail") }
                try press("continue")
                if key == "general-listening-decline-goodbye" {
                    try waitFor("lesson-interlude", value: "general-listening-decline-challenge")
                    try saveState("general-listening-decline-challenge-interlude"); try press("interlude-continue")
                }
            }
            for (state, page) in zip(["general-listening-decline-result", "general-listening-decline-profile"], definition["settlement"] as! [[String: Any]]) {
                try waitFor(page["kind"] as? String == "result" ? "lesson-complete" : "settlement-title", value: page["title"] as? String)
                try saveState(state); try press("settlement-continue")
            }
            try waitFor("course-entry"); try saveState("general-listening-decline-home-return")
            try before.write(to: output.appendingPathComponent("progress-before.json"), options: .withoutOverwriting)
            try Data(contentsOf: progress).write(to: output.appendingPathComponent("progress-after.json"), options: .withoutOverwriting)
            child.terminate(); child.waitUntilExit(); child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
            try waitFor("course-entry"); configureWindow(); try saveState("general-listening-decline-home-restart")
            try Data(contentsOf: progress).write(to: output.appendingPathComponent("progress-after-restart.json"), options: .withoutOverwriting)
        } catch {
            failure = String(describing: error); states["failure-boundary"] = observe(); try? capture("failure-boundary")
        }
        try bindCaptures(&states, names: ["home":"home-window", "seeded-home":"home-window"])
        let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,
            "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
            "general_fixture_sha256":SHA256.hash(data:try Data(contentsOf:practiceURL)).map{String(format:"%02x",$0)}.joined(),
            "observed_at":ISO8601DateFormatter().string(from:Date()), "failure":failure as Any,
            "action":"Actual Quests entry, listening decline and replacement, speech decline, sixteen graded questions, result/profile/home and actual child restart",
            "limitations":["Fixed observed instance; adaptive selection and non-decline future remain unverified", "AX/PNG collection does not prove acoustic equality"]]
        try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"), options:.withoutOverwriting)
        print("Collected listening-decline native states: \(states.count); failure=\(failure ?? "none")")
        if failure != nil { exit(1) }
        return
    }
    if CommandLine.arguments.contains("--exercise-general-practice") {
        let practiceURL = root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-general-practice-v4.json")
        let practiceFixture = try JSONSerialization.jsonObject(with: Data(contentsOf: practiceURL)) as! [String: Any]
        let practice = (practiceFixture["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let definition = (practice["lessons"] as! [[String: Any]])[0]
        let questions = definition["questions"] as! [[String: Any]]
        let initialProgress = try Data(contentsOf: progress)
        var failure: String?
        do {
            try press("quests-practice")
            for question in questions {
                let key = question["id"] as! String
                if key == "general-practice-inserted" {
                    try waitFor("speech-title", value: "general-practice-speech")
                    states["general-practice-speech"] = observe(); try capture("general-practice-speech")
                    try press("speech-decline"); try waitFor("speech-closed")
                    states["general-practice-speech-declined"] = observe(); try capture("general-practice-speech-declined")
                    try press("speech-continue")
                }
                if key == "general-practice-q6" {
                    try waitFor("question-title", value: question["keyboardPrompt"] as? String)
                    states["general-practice-keyboard"] = observe(); try capture("general-practice-keyboard")
                    try clickOwnedControl("toggle-input-mode")
                }
                try waitFor(question["kind"] as? String == "matching" ? "question-prompt" : "question-title", value: question["kind"] as? String == "matching" ? key : question["prompt"] as? String)
                states[key] = observe(); try capture(key)
                if key == "general-practice-q0" { states["quests-practice-entry"] = states[key]; try capture("quests-practice-entry") }
                try captureGeneralCharacterFrames(key, "idle", question)
                switch question["kind"] as? String {
                case "matching":
                    let pairs = question["pairs"] as! [[String: Any]]
                    if key == "general-practice-q0", let index = CommandLine.arguments.firstIndex(of: "--general-practice-audio-recorder"), index + 1 < CommandLine.arguments.count {
                        let actions = output.appendingPathComponent("audio-actions.json")
                        try JSONSerialization.data(withJSONObject: pairs.flatMap { ["pair-left-" + ($0["id"] as! String), "pair-right-" + ($0["id"] as! String)] }).write(to: actions, options: .withoutOverwriting)
                        let recorder = Process()
                        recorder.executableURL = URL(fileURLWithPath: CommandLine.arguments[index + 1])
                        recorder.arguments = [String(child.processIdentifier), output.appendingPathComponent("general-practice.wav").path, "14", actions.path, "1.1"]
                        let log = output.appendingPathComponent("audio-recorder.log")
                        FileManager.default.createFile(atPath: log.path, contents: nil)
                        let handle = try FileHandle(forWritingTo: log)
                        recorder.standardOutput = handle; recorder.standardError = handle
                        try recorder.run(); recorder.waitUntilExit()
                        guard recorder.terminationStatus == 0 else { throw ProbeError(message: "Owned practice output recording failed; preserve log") }
                    } else {
                        for pair in pairs { try press("pair-left-" + (pair["id"] as! String)); try press("pair-right-" + (pair["id"] as! String)) }
                    }
                case "word_tiles":
                    for word in question["answer_words"] as! [String] { try press("word-bank-" + word) }
                    try press("check")
                case "text_entry":
                    try fillInput(key == "general-practice-replacement15" ? "water" : question["answer"] as! String)
                    try press("check")
                default:
                    try press("option-" + (question["answer"] as! String)); try press("check")
                }
                try waitFor("continue")
                states[key + "-feedback"] = observe(); try capture(key + "-feedback")
                try captureGeneralCharacterFrames(key, "feedback", question)
                if key == "general-practice-replacement15" {
                    try Data(contentsOf: progress).write(to: output.appendingPathComponent("progress-after-wrong.json"), options: .withoutOverwriting)
                }
                try press("continue")
                if key == "general-practice-q12" {
                    try waitFor("lesson-interlude", value: "general-practice-challenge-intro")
                    states["general-practice-challenge-intro"] = observe(); try capture("general-practice-challenge-intro")
                    try press("interlude-continue")
                }
            }
            try waitFor("lesson-interlude", value: "general-practice-review-intro")
            states["general-practice-review-intro"] = observe(); try capture("general-practice-review-intro")
            try press("interlude-continue"); try waitFor("review-label")
            states["general-practice-review"] = observe(); try capture("general-practice-review")
            try fillInput(questions.last!["answer"] as! String); try press("check"); try waitFor("continue")
            states["general-practice-review-feedback"] = observe(); try capture("general-practice-review-feedback")
            try press("continue")
            for (state, page) in zip(["general-practice-result", "general-practice-heart-reward", "general-practice-profile"], definition["settlement"] as! [[String: Any]]) {
                try waitFor(page["kind"] as? String == "result" ? "lesson-complete" : "settlement-title", value: page["title"] as? String)
                states[state] = observe(); try capture(state)
                try Data(contentsOf: progress).write(to: output.appendingPathComponent(state + "-progress.json"), options: .withoutOverwriting)
                try press("settlement-continue")
            }
            try waitFor("course-entry")
            states["general-practice-home-return"] = observe(); try capture("general-practice-home-return")
            child.terminate(); child.waitUntilExit()
            child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
            try waitFor("course-entry"); configureWindow()
            states["general-practice-home-restart"] = observe(); try capture("general-practice-home-restart")
            try initialProgress.write(to: output.appendingPathComponent("progress-before.json"), options: .withoutOverwriting)
        } catch {
            failure = String(describing: error)
            states["failure-boundary"] = observe(); try? capture("failure-boundary")
        }
        try bindCaptures(&states, names: ["home":"home-window", "seeded-home":"home-window"])
        let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,
            "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
            "general_fixture_sha256":SHA256.hash(data:try Data(contentsOf:practiceURL)).map{String(format:"%02x",$0)}.joined(),
            "observed_at":ISO8601DateFormatter().string(from:Date()), "failure":failure as Any,
            "action":"Actual Quests entry, independent practice, one wrong, correction, result/reward/profile and real child restart",
            "limitations":["Observed finite source instance; adaptive selection, complete pixels and acoustic equality remain unproven"]]
        try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"))
        if let failure { throw ProbeError(message: failure) }
        return
    }
    if CommandLine.arguments.contains("--exercise-quests-practice") {
        try press("quests-practice"); try waitFor("question-prompt", value: "general-practice-q0")
        states["quests-practice-entry"] = observe(); try capture("quests-practice-entry")
        try press("exit"); try waitFor("course-entry")
        states["quests-practice-exited"] = observe(); try capture("quests-practice-exited")
    }
    try bindCaptures(&states, names: ["home":"home-window", "seeded-home":"home-window"])
    let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,
        "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
        "observed_at":ISO8601DateFormatter().string(from:Date()),
        "action":"Actual quests navigation and optional practice entry; no driver pass flags",
        "limitations":["Actual AX and owned captures; this entry-only run does not verify the full independent practice"]]
    try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"))
    return
}
if CommandLine.arguments.contains("--observe-pronunciation") {
    try press("nav-pronunciation")
    Thread.sleep(forTimeInterval: 0.5)
    states["en-zh-pronunciation"] = observe()
    try capture("pronunciation-window")
    if CommandLine.arguments.contains("--exercise-pronunciation-card-press") {
        guard movePointer(to: "pronunciation-sound-1"),
              NSRunningApplication(processIdentifier: child.processIdentifier)?.isActive == true,
              let center = pointerActions.last?["center"] as? [CGFloat] else {
            throw ProbeError(message: "Cannot target owned pronunciation card")
        }
        let point = CGPoint(x: center[0], y: center[1])
        guard let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point, mouseButton: .left),
              let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point, mouseButton: .left) else {
            throw ProbeError(message: "Cannot create owned card pointer events")
        }
        var held = false
        defer { if held { up.post(tap: .cghidEventTap) } }
        states["pronunciation-card-hover"] = observe(); try capture("pronunciation-card-hover")
        down.post(tap: .cghidEventTap); held = true
        Thread.sleep(forTimeInterval: 0.2)
        states["pronunciation-card-pressed"] = observe(); try capture("pronunciation-card-pressed")
        up.post(tap: .cghidEventTap); held = false
        Thread.sleep(forTimeInterval: 0.2)
        states["pronunciation-card-released"] = observe(); try capture("pronunciation-card-released")
    }
    if let index = CommandLine.arguments.firstIndex(of: "--pronunciation-audio-recorder"), index + 1 < CommandLine.arguments.count {
        let actions = output.appendingPathComponent("audio-actions.json")
        try JSONSerialization.data(withJSONObject: ["pronunciation-sound-0"]).write(to: actions)
        let recorder = Process()
        recorder.executableURL = URL(fileURLWithPath: CommandLine.arguments[index + 1])
        recorder.arguments = [String(child.processIdentifier), output.appendingPathComponent("phoneme.wav").path, "6", actions.path]
        let audioLog = output.appendingPathComponent("audio-recorder.log")
        FileManager.default.createFile(atPath: audioLog.path, contents: nil)
        let handle = try FileHandle(forWritingTo: audioLog)
        recorder.standardOutput = handle; recorder.standardError = handle
        try recorder.run(); recorder.waitUntilExit()
        precondition(recorder.terminationStatus == 0, "Owned pronunciation audio recording failed; preserve log")
    }
    if CommandLine.arguments.contains("--walk-pronunciation-practice") {
        try press("pronunciation-start"); try waitFor("question-prompt", value: "p0")
        var visits: [String: Int] = [:]
        let practiceURL = root.appendingPathComponent("projects/education-swift/Sources/LingoSeed/Resources/Reference/pronunciation-practice.json")
        let practice = try JSONSerialization.jsonObject(with: Data(contentsOf: practiceURL)) as! [String: Any]
        let definitions = practice["lessons"] as! [[String: Any]]
        let saved = try JSONSerialization.jsonObject(with: Data(contentsOf: progress)) as! [String: Any]
        let completed = ((saved["completedLessons"] as? [String: [String]])?[practice["id"] as! String]) ?? []
        guard let lessonDefinition = definitions.first(where: { !completed.contains($0["id"] as! String) }) else { throw ProbeError(message: "No compiled uncompleted practice") }
        let questions = lessonDefinition["questions"] as! [[String: Any]]
        for _ in 0..<30 {
            if current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "practice-settlement-title" }) { break }
            if current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "speech-decline" }) {
                states["pronunciation-speech-before"] = observe(); try capture("practice-speech-before")
                if CommandLine.arguments.contains("--exercise-speech-denied") {
                    try press("speech-record"); Thread.sleep(forTimeInterval: 0.3)
                    try JSONSerialization.data(withJSONObject: observe(), options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("speech-denial-probe.json"))
                    try capture("speech-denial-probe"); try waitFor("speech-denied-title")
                    states["pronunciation-speech-denied"] = observe(); try capture("practice-speech-denied")
                    try press("speech-denied-close"); try waitFor("speech-record")
                    states["pronunciation-speech-denied-closed"] = observe(); try capture("practice-speech-denied-closed")
                }
                try press("speech-decline"); states["pronunciation-speech-declined"] = observe()
                try press("speech-continue"); continue
            }
            guard let prompt = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == "question-prompt" }),
                  let id = attr(prompt, kAXValueAttribute) as? String,
                  let question = questions.first(where: { $0["id"] as? String == id }) else { throw ProbeError(message: "No actual practice question") }
            let repeatCount = visits[id, default: 0]; visits[id] = repeatCount + 1
            let state = "pronunciation-" + id + (repeatCount > 0 ? "-review" : "")
            var before = observe()
            let check = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "check" }
            before["interactions"] = ["check_enabled": check.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false]
            states[state + "-before"] = before; try capture(state + "-before")
            if question["sourceType"] as? String == "sameDifferent" {
                try press("practice-play-0"); try press("practice-play-1")
            }
            if question["kind"] as? String == "matching" {
                if CommandLine.arguments.contains("--exercise-practice-quit"), repeatCount == 0 {
                    let preserved = try JSONSerialization.data(withJSONObject: observe(), options: [.sortedKeys])
                    try press("exit"); try waitFor("practice-quit-title")
                    states["pronunciation-practice-exit-confirm"] = observe(); try capture("practice-quit-confirm")
                    try press("practice-quit-cancel"); try waitFor("question-prompt", value: id)
                    let resumed = observe()
                    guard try JSONSerialization.data(withJSONObject: resumed, options: [.sortedKeys]) == preserved else { throw ProbeError(message: "Practice cancellation changed actual AX question/control state") }
                    states["pronunciation-practice-exit-cancelled"] = resumed; try capture("practice-quit-cancelled")
                }
                for pair in question["pairs"] as! [[String: Any]] {
                    let pairID = pair["id"] as! String
                    try press("pair-left-" + pairID); try press("pair-right-" + pairID)
                }
            } else {
                let options = question["options"] as! [[String: Any]]
                let answer = repeatCount > 0 ? question["answer"] as! String : options[0]["id"] as! String
                try press("option-" + answer)
                states[state + "-selected"] = observe(); try capture(state + "-selected")
                try press("check")
            }
            states[state + "-feedback"] = observe(); try capture(state + "-feedback")
            try press("continue")
        }
        states["pronunciation-settlement"] = observe(); try capture("practice-settlement")
        try press("settlement-continue"); states["pronunciation-profile"] = observe(); try capture("practice-profile")
        try press("settlement-continue"); states["pronunciation-returned"] = observe(); try capture("practice-returned")
        if CommandLine.arguments.contains("--verify-pronunciation-restart") {
            let savedAfter = try JSONSerialization.jsonObject(with: Data(contentsOf: progress)) as! [String: Any]
            let completedAfter = ((savedAfter["completedLessons"] as? [String: [String]])?[practice["id"] as! String]) ?? []
            guard completedAfter.contains(lessonDefinition["id"] as! String),
                  let next = definitions.first(where: { !completedAfter.contains($0["id"] as! String) }),
                  let nextQuestion = (next["questions"] as? [[String: Any]])?.first else { throw ProbeError(message: "Practice completion not persisted or next unavailable") }
            child.terminate(); child.waitUntilExit(); child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
            try waitFor("course-entry"); configureWindow(); try press("nav-pronunciation"); try press("pronunciation-start")
            try waitFor("question-prompt", value: (nextQuestion["id"] as! String))
            let nextState = observe()
            let strings = nextState["accessible_text"] as? [String] ?? []
            // The real controls must expose the next source options, rather than merely another p0 identifier.
            for (optionIndex, option) in (nextQuestion["options"] as! [[String: Any]]).enumerated() {
                try waitFor("option-" + (option["id"] as! String))
                guard current().contains(where: { node in
                    [kAXTitleAttribute,kAXValueAttribute,kAXDescriptionAttribute].contains { name in (attr(node,name) as? String) == "\(optionIndex + 1) \(option["text"] as! String)" }
                }) else { throw ProbeError(message: "Next practice option text missing after restart") }
            }
            states["pronunciation-restarted-next"] = nextState; try capture("practice-restarted-next")
            try JSONSerialization.data(withJSONObject: ["completed":completedAfter,"next_lesson":next["id"]!,"observed_text_count":strings.count], options: [.prettyPrinted,.sortedKeys]).write(to: output.appendingPathComponent("restart.json"), options:.withoutOverwriting)
        } else { try press("pronunciation-start"); try waitFor("question-prompt", value: "p0") }
        if CommandLine.arguments.contains("--exercise-practice-quit") {
            // An option selected but not graded must still leave directly, as observed.
            guard let option = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String)?.hasPrefix("option-") == true }),
                  let optionID = attr(option, kAXIdentifierAttribute) as? String else { throw ProbeError(message: "No actual fresh practice option") }
            try press(optionID)
        }
        try press("exit"); try waitFor("pronunciation-start")
        states["pronunciation-exit-returned"] = observe(); try capture("practice-exit-returned")
        if CommandLine.arguments.contains("--exercise-practice-quit") {
            let savedBefore = try Data(contentsOf: progress)
            let savedValue = try JSONSerialization.jsonObject(with: savedBefore) as! [String: Any]
            let finished = ((savedValue["completedLessons"] as? [String: [String]])?[practice["id"] as! String]) ?? []
            guard let remaining = definitions.first(where: { !finished.contains($0["id"] as! String) }),
                  let pending = remaining["questions"] as? [[String: Any]], pending.count >= 3,
                  let firstWrong = (pending[0]["options"] as? [[String: Any]])?.first(where: { $0["id"] as? String != pending[0]["answer"] as? String }),
                  let secondWrong = (pending[1]["options"] as? [[String: Any]])?.first(where: { $0["id"] as? String != pending[1]["answer"] as? String }) else { throw ProbeError(message: "Observed next practice choices unavailable") }
            try press("pronunciation-start"); try waitFor("question-prompt", value: "p0")
            try press("option-" + (firstWrong["id"] as! String)); try press("check"); try waitFor("continue"); try press("continue")
            try press("option-" + (secondWrong["id"] as! String)); try press("check"); try waitFor("continue"); try press("continue")
            try press("exit"); try waitFor("pronunciation-start")
            states["pronunciation-practice-wrong-exit-returned"] = observe(); try capture("practice-wrong-exit-returned")
            guard try Data(contentsOf: progress) == savedBefore else { throw ProbeError(message: "Wrong-only abandoned practice changed saved progress") }
            try press("pronunciation-start"); try waitFor("question-prompt", value: "p0")
            try press("option-" + (pending[0]["answer"] as! String)); try press("check"); try waitFor("continue"); try press("continue")
            try press("option-" + (secondWrong["id"] as! String)); try press("check"); try waitFor("continue"); try press("continue")
            try press("exit"); try waitFor("practice-quit-title")
            states["pronunciation-practice-abandon-confirm"] = observe(); try capture("practice-abandon-confirm")
            try press("practice-quit-confirm"); try waitFor("pronunciation-start")
            states["pronunciation-practice-abandoned"] = observe(); try capture("practice-abandoned")
            guard try Data(contentsOf: progress) == savedBefore else { throw ProbeError(message: "Abandoned practice changed saved completion or main progress") }
            try press("pronunciation-start"); try waitFor("question-prompt", value: "p0")
            states["pronunciation-practice-abandoned-restarted"] = observe(); try capture("practice-abandoned-restarted")
            try press("exit"); try waitFor("pronunciation-start")
        }
    }
    try bindCaptures(&states, names: ["home":"home-window", "seeded-home":"home-window", "en-zh-pronunciation":"pronunciation-window",
        "pronunciation-speech-before":"practice-speech-before", "pronunciation-speech-denied":"practice-speech-denied",
        "pronunciation-speech-denied-closed":"practice-speech-denied-closed"])
    let receipt: [String: Any] = ["kind": "owned_native_ax_observation", "states": states,
        "candidate_binary_sha256": candidateSHA, "fixture_sha256": fixtureSHA,
        "observed_at": ISO8601DateFormatter().string(from: Date()),
        "action": "Actual native pronunciation navigation click; collect page without supplying pass flags",
        "limitations": ["AX and owned capture; no audio or visual equivalence"]]
    try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("observed.json"), options: .withoutOverwriting)
    if child.isRunning { child.terminate(); child.waitUntilExit() }
    return
}
if CommandLine.arguments.contains("--observe-home-popover") {
    try press("start-lesson"); try waitFor("start-lesson-confirm")
    var popover = observe()
    let start = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "start-lesson-confirm" }
    popover["interactions"] = ["start_enabled": start.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false]
    states["en-zh-home-popover"] = popover; try capture("home-popover-window")
    try press("start-lesson")
}

// A hover must include an outside-to-inside transition, including when the cursor
// starts over the same row left by a previous owned probe.
_ = movePointer(to: "course-entry")
let moved = movePointer(to: "nav-more")
let opened = current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "more-settings" }
states["more-open"] = observe()
try capture("more-window")
let movedOut = movePointer(to: "course-entry")
let dismissed = opened && !current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "more-settings" }
states["home"]?["interactions"] = ["more_hover_opened": moved && opened, "more_hover_dismissed": movedOut && dismissed]
struct ProbeError: Error { let message: String }
func waitFor(_ id: String, value: String? = nil) throws {
    let end = Date().addingTimeInterval(10)
    while Date() < end {
        if let node = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == id }),
           value == nil || (attr(node, kAXValueAttribute) as? String) == value { return }
        Thread.sleep(forTimeInterval: 0.05)
    }
    throw ProbeError(message: "No observed control: " + id)
}
func press(_ id: String) throws {
    try waitFor(id)
    guard let node = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == id }),
          AXUIElementPerformAction(node, kAXPressAction as CFString) == .success else { throw ProbeError(message: "Cannot press " + id) }
    Thread.sleep(forTimeInterval: 0.08)
}
func clickOwnedControl(_ id: String,xFraction:Double=0.5) throws {
    guard xFraction >= 0 && xFraction <= 1 else {throw ProbeError(message:"Invalid owned pointer fraction")}
    // Preserve failed AXPress attempts separately. Use one real screen click
    // for TextEditor transitions, and verify the resulting state without retry.
    try waitFor(id)
    guard child.isRunning, let node = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == id }),
          attr(node, kAXEnabledAttribute) as? Bool == true,
          let position = attr(node, kAXPositionAttribute), let size = attr(node, kAXSizeAttribute) else { throw ProbeError(message: "No enabled owned control: " + id) }
    var point = CGPoint.zero; var dimensions = CGSize.zero
    AXValueGetValue(position as! AXValue, .cgPoint, &point); AXValueGetValue(size as! AXValue, .cgSize, &dimensions)
    let center = CGPoint(x: point.x + dimensions.width * xFraction, y: point.y + dimensions.height / 2)
    pointerActions.append(["control": id, "center": [center.x, center.y], "delivery": "single screen click in owned frontmost window"])
    for type in [CGEventType.leftMouseDown, .leftMouseUp] {
        CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: center, mouseButton: .left)?.post(tap: .cghidEventTap)
        Thread.sleep(forTimeInterval: 0.1)
    }
}

func selectAppearance(_ title: String) throws {
    guard movePointer(to: "dark-mode"), let center = pointerActions.last?["center"] as? [CGFloat] else { throw ProbeError(message: "No owned appearance control") }
    let point = CGPoint(x: center[0], y: center[1])
    for kind in [CGEventType.leftMouseDown, .leftMouseUp] {
        CGEvent(mouseEventSource: nil, mouseType: kind, mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
        Thread.sleep(forTimeInterval: 0.1)
    }
    let end = Date().addingTimeInterval(5)
    while Date() < end {
        let focused = attr(app, kAXFocusedUIElementAttribute).map { nodes($0 as! AXUIElement) } ?? []
        if let item = (current() + focused).first(where: { node in (attr(node, kAXRoleAttribute) as? String) == "AXMenuItem" && [kAXTitleAttribute, kAXValueAttribute, kAXDescriptionAttribute].contains { name in (attr(node, name) as? String) == title } }) {
            guard AXUIElementPerformAction(item, kAXPressAction as CFString) == .success else { throw ProbeError(message: "Cannot select appearance " + title) }
            try waitFor("dark-mode", value: title)
            return
        }
        Thread.sleep(forTimeInterval: 0.05)
    }
    throw ProbeError(message: "No actual appearance menu item " + title)
}
if opened {
    _ = movePointer(to: "nav-more")
    try press("more-settings")
    try waitFor("preferences-title")
    states["preferences"] = observe()
    try capture("preferences-window")
    try JSONSerialization.data(withJSONObject: states["preferences"]!, options: .prettyPrinted).write(to: output.appendingPathComponent("preferences-initial.json"))
    let switches = ["sound-effects", "animations", "motivational-messages", "listening-exercises"]
    for id in switches { try waitFor(id, value: "on"); try press(id); try waitFor(id, value: "off") }
    states["preferences-off"] = observe()
    try selectAppearance("On")
    states["preferences-dark"] = observe()
    try capture("preferences-dark-window")
    child.terminate(); child.waitUntilExit()
    child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
    try waitFor("course-entry")
    configureWindow()
    if !current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "more-settings" }) { try press("nav-more") }
    try press("more-settings"); try waitFor("preferences-title")
    states["preferences-reopened"] = observe()
    var reloaded: [String: Bool] = [:]
    for id in switches {
        let value = current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXValueAttribute) as? String }
        reloaded[id + "-off-persisted"] = value == "off"
    }
    reloaded["dark-mode-on-persisted"] = current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "dark-mode" && (attr($0, kAXValueAttribute) as? String) == "On" }
    states["preferences-reopened"]?["interactions"] = reloaded
    try selectAppearance("Off")
    try selectAppearance("System Default")
    for id in switches { try press(id); try waitFor(id, value: "on") }
    try press("nav-learn")

}
var walkError: String?
var stoppedAtQuestion: String?
if CommandLine.arguments.contains("--walk-course") {
    do {
        try press("nav-learn")
        let data = try Data(contentsOf: root.appendingPathComponent(fixture))
        let json = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        let course = (json["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let lessons = course["lessons"] as! [[String: Any]]
        var capturedKinds = Set<String>()
        let startIndex = CommandLine.arguments.firstIndex(of: "--start-lesson-index").map { Int(CommandLine.arguments[$0 + 1])! } ?? 0
        precondition(lessons.indices.contains(startIndex), "Start lesson must exist in the explicit fixture")
        for (lessonIndex, definition) in lessons.enumerated().dropFirst(startIndex) {
            let path = course["pathNodes"] as? [[String: Any]]
            let nodeIndex = path?.firstIndex { ($0["lessonIDs"] as? [String])?.contains(definition["id"] as! String) == true } ?? lessonIndex
            try press(nodeIndex == 0 ? "start-lesson" : "start-lesson-\(nodeIndex)")
            if course["interfaceLanguage"] as? String == "zh" {
                if lessonIndex == 1 {
                    var popover = observe()
                    let start = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "start-lesson-confirm" }
                    popover["interactions"] = ["start_enabled": start.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false]
                    states["en-zh-home-popover"] = popover; try capture("after-first-popover-window")
                }
                try press("start-lesson-confirm")
            }
            if let entry = definition["entry"] as? [String: String] {
                try waitFor("lesson-entry", value: entry["id"])
                states[entry["id"]!] = observe(); try capture(entry["id"]! + "-window")
                try press("lesson-entry-start")
            }
            if let initial = definition["initialInterlude"] as? [String: String] {
                try waitFor("lesson-interlude", value: initial["id"])
                states[initial["id"]!] = observe(); try capture(initial["id"]! + "-window")
                try press("interlude-continue")
            }
            let questions = definition["questions"] as! [[String: Any]]
            let wrongFirst = CommandLine.arguments.contains("--english-first-wrong") && course["interfaceLanguage"] as? String == "zh" && lessonIndex == 0
            let fifthErrors = CommandLine.arguments.contains("--english-fifth-mixed-errors") && definition["id"] as? String == "lesson-5"
            for question in questions {
                if let speeches = definition["deferredSpeech"] as? [[String: String]], let speech = speeches.first(where: { $0["beforeQuestionID"] == question["id"] as? String }) {
                    let id = speech["id"]!
                    try waitFor("speech-title", value: id)
                    states[id] = observe(); try capture(id + "-before")
                    try press("speech-decline"); try waitFor("speech-closed")
                    states[id + "-closed"] = observe(); states[id + "-declined"] = observe(); try capture(id + "-closed")
                    if id.hasSuffix("-speech") { states[String(id.dropLast(7)) + "-declined"] = observe() }
                    try press("speech-continue")
                }
                let modeProbe = CommandLine.arguments.contains("--exercise-input-modes") && question["keyboardAnswer"] != nil
                if modeProbe {
                    if let hint = question["hint"] as? String { try waitFor("question-hint", value: hint) }
                    let full = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }.flatMap { attr($0, kAXRoleAttribute) as? String } == "AXTextArea"
                    try waitFor("question-title", value: (full ? question["keyboardPrompt"] : question["prompt"]) as? String)
                    try waitFor("check")
                } else { try waitFor("question-title", value: question["prompt"] as? String) }
                let key = question["id"] as! String
                var initialObservation = observe()
                if modeProbe {
                    let input = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }
                    let full = input.flatMap { attr($0, kAXRoleAttribute) as? String } == "AXTextArea"
                    let empty = input == nil ? question["kind"] as? String == "word_tiles" : input.flatMap { attr($0, kAXValueAttribute) as? String } == ""
                    let enabled = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "check" }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false
                    initialObservation["interactions"] = ["keyboard_mode": full, "empty_input": empty, "check_enabled": enabled]
                }
                states[key] = initialObservation
                states[key + "-initial"] = initialObservation
                if CommandLine.arguments.contains("--capture-character-frames"), current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "question-character" }) {
                    for frame in 0..<12 { try capture(key + "-character-idle-\(frame)"); Thread.sleep(forTimeInterval: 0.15) }
                }
                if let kind = (question["sourceType"] ?? question["kind"]) as? String, capturedKinds.insert(kind).inserted { try capture("question-" + kind) }
                if course["interfaceLanguage"] as? String == "zh" { try capture(key + "-before") }
                let skipProbe = CommandLine.arguments.contains("--exercise-source-skip") && key == "en-zh-l7-q0"
                if skipProbe {
                    let oldHearts = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "hearts" }.flatMap { attr($0, kAXValueAttribute) as? String }
                    try press("skip"); try waitFor("continue")
                    let newHearts = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "hearts" }.flatMap { attr($0, kAXValueAttribute) as? String }
                    var skipped = observe()
                    skipped["interactions"] = ["hearts_unchanged": oldHearts != nil && oldHearts == newHearts]
                    states[key + "-skipped"] = skipped; try capture(key + "-skipped")
                } else if CommandLine.arguments.contains("--exercise-input-modes"), let answer = question["keyboardAnswer"] as? String {
                    func enabled(_ id: String) -> Bool {
                        current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false
                    }
                    func recordMode(_ phase: String, expectedInput: String) throws {
                        var value = observe()
                        let actual = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }.flatMap { attr($0, kAXValueAttribute) as? String }
                        let inputMatches = phase == "returned" && question["kind"] as? String == "word_tiles" ? actual == nil : actual == expectedInput
                        value["interactions"] = ["check_enabled": enabled("check"), "input_matches": inputMatches]
                        states[key + "-" + phase] = value; try capture(key + "-" + phase)
                        if question["sourceObservationPhase"] as? String == phase { states[key] = value }
                    }
                    let full = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }.flatMap { attr($0, kAXRoleAttribute) as? String } == "AXTextArea"
                    if full {
                        try fillInput(answer)
                    } else {
                        try clickOwnedControl("toggle-input-mode"); try recordMode("empty", expectedInput: "")
                        try fillInput(answer); try recordMode("filled", expectedInput: answer)
                        try clickOwnedControl("toggle-input-mode"); try recordMode("returned", expectedInput: "")
                        try clickOwnedControl("toggle-input-mode"); try recordMode("reopened", expectedInput: answer)
                    }
                    try clickOwnedControl("check")
                } else {
                switch question["kind"] as? String {
                case "text_entry":
                    func enabled(_ id: String) -> Bool {
                        current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false
                    }
                    var interactions = ["empty_check_disabled": !enabled("check")]
                    try fillInput("Te"); interactions["nonempty_check_enabled"] = enabled("check")
                    try fillInput(""); interactions["cleared_check_disabled"] = !enabled("check")
                    if CommandLine.arguments.contains("--exercise-typed-review") {
                        let heartsBefore = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "hearts" }.flatMap { attr($0, kAXValueAttribute) as? String }.flatMap(Int.init)
                        try fillInput("cold"); try press("check"); try waitFor("continue")
                        let heartsAfter = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "hearts" }.flatMap { attr($0, kAXValueAttribute) as? String }.flatMap(Int.init)
                        var wrong = observe(); wrong["interactions"] = ["heart_decremented_once": heartsBefore != nil && heartsAfter == heartsBefore! - 1, "submitted_input_locked": !enabled("answer-input")]
                        states[key + "-wrong"] = wrong; try capture(key + "-wrong")
                        try press("continue"); try waitFor("review-label")
                        var review = observe()
                        review["interactions"] = ["review_input_empty": current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }.flatMap { attr($0, kAXValueAttribute) as? String } == ""]
                        states[key + "-review"] = review; try capture(key + "-review")
                        try fillInput("HOT")
                    } else { try fillInput(fifthErrors && key == "en-zh-l5-q7" ? "cold" : question["answer"] as! String) }
                    var observed = observe(); observed["interactions"] = interactions
                    states[key + "-filled"] = observed; try capture(key + "-filled")
                    try press("check"); try waitFor("continue")
                    observed = observe(); observed["interactions"] = ["submitted_input_locked": !enabled("answer-input")]
                    states[key + "-submitted"] = observed
                case "matching":
                    let pairs = question["pairs"] as! [[String: Any]]
                    func value(_ id: String) -> String? { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXValueAttribute) as? String } }
                    func enabled(_ id: String) -> Bool { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false }
                    let declineLesson = CommandLine.arguments.firstIndex(of: "--decline-lesson-id").map { CommandLine.arguments[$0 + 1] }
                    if CommandLine.arguments.contains("--exercise-listening-decline"), question["listeningDecline"] != nil, declineLesson == nil || declineLesson == definition["id"] as? String {
                        let before = value("hearts")
                        try press("listening-decline"); try waitFor("listening-declined")
                        var observed = observe()
                        observed["interactions"] = ["hearts_unchanged": before != nil && value("hearts") == before,
                            "all_pairs_disabled": pairs.allSatisfy { pair in
                                let id = pair["id"] as! String
                                return !enabled("pair-left-" + id) && !enabled("pair-right-" + id)
                            }]
                        states[key + "-declined"] = observed; try capture(key + "-declined")
                        try press("listening-continue")
                        continue
                    }
                    if (CommandLine.arguments.contains("--exercise-wrong-audio-pair") || (fifthErrors && key == "en-zh-l5-q8")), question["sourceType"] as? String == "listenMatch", pairs.count > 1 {
                        let a = pairs[0]["id"] as! String, b = pairs[1]["id"] as! String
                        let before = Int(value("hearts") ?? "")
                        try press("pair-left-" + a); try press("pair-right-" + b)
                        var observed = observe()
                        observed["interactions"] = ["heart_decremented_once": before != nil && Int(value("hearts") ?? "") == before! - 1,
                            "unmatched_remains_available": enabled("pair-left-" + a) && enabled("pair-right-" + b),
                            "wrong_pair_marked_incorrect": value("pair-left-" + a) == "incorrect" && value("pair-right-" + b) == "incorrect"]
                        states[key + "-wrong"] = observed; try capture(key + "-wrong")
                    }
                    for (index, pair) in pairs.enumerated() {
                        let id = pair["id"] as! String
                        try press("pair-left-" + id); try press("pair-right-" + id)
                        if index == 0 {
                            var observed = observe(); observed["interactions"] = ["matched_pair_disabled": !enabled("pair-left-" + id) && !enabled("pair-right-" + id)]
                            states[key + "-paired-first"] = observed; try capture(key + "-paired-first")
                        }
                    }
                case "word_tiles":
                    if CommandLine.arguments.contains("--exercise-duplicate-words") {
                        let words = question["words"] as! [[String: Any]]
                        let grouped = Dictionary(grouping: words, by: { $0["text"] as! String })
                        if let duplicates = grouped.values.first(where: { $0.count > 1 }) {
                            let first = duplicates[0]["id"] as! String, second = duplicates[1]["id"] as! String
                            func enabled(_ id: String) -> Bool? {
                                current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool }
                            }
                            try press("word-bank-" + first)
                            var observed = observe()
                            observed["interactions"] = ["used_occurrence_disabled": enabled("word-bank-" + first) == false,
                                "other_occurrence_available": enabled("word-bank-" + second) == true]
                            states[key + "-duplicate-first"] = observed
                            try press("word-bank-" + second); try press("selected-word-" + first)
                            observed = observe()
                            observed["interactions"] = ["removed_occurrence_available": enabled("word-bank-" + first) == true,
                                "other_occurrence_still_selected": enabled("word-bank-" + second) == false]
                            states[key + "-duplicate-undo-one"] = observed; try capture(key + "-duplicate-undo-one")
                            try press("selected-word-" + second)
                            observed = observe()
                            observed["interactions"] = ["empty_answer_disabled": enabled("check") == false,
                                "both_occurrences_available": enabled("word-bank-" + first) == true && enabled("word-bank-" + second) == true]
                            states[key + "-duplicate-empty"] = observed
                        }
                    }
                    for word in question["answer_words"] as! [String] { try press("word-bank-" + word) }
                    try press("check")
                default:
                    if wrongFirst && question["id"] as? String == "en-zh-q0" {
                        let options = question["options"] as! [[String: Any]]
                        let wrong = options.first { $0["text"] as? String == "sugar" }!["id"] as! String
                        try press("option-" + wrong)
                    } else { try press("option-" + (question["answer"] as! String)) }
                    try press("check")
                }
                }
                try waitFor("continue")
                var feedbackObservation = observe()
                if CommandLine.arguments.contains("--exercise-input-modes"), question["keyboardAnswer"] != nil {
                    let actual = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "feedback" }.flatMap { attr($0, kAXValueAttribute) as? String }
                    feedbackObservation["interactions"] = ["accepted": actual == "correct"]
                }
                states[key + "-feedback"] = feedbackObservation
                if CommandLine.arguments.contains("--capture-character-frames"), current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "question-character" }) {
                    for frame in 0..<12 { try capture(key + "-character-feedback-\(frame)"); Thread.sleep(forTimeInterval: 0.15) }
                }
                if course["interfaceLanguage"] as? String == "zh" { try capture(key + "-feedback") }
                if CommandLine.arguments.contains("--exercise-feedback-actions") {
                    func value(_ id: String) -> String? { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXValueAttribute) as? String } }
                    func enabled(_ id: String) -> Bool { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false }
                    func checked(_ id: String) -> Bool { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXValueAttribute) as? NSNumber }?.intValue == 1 }
                    for (action, name) in [("easy", "easy"), ("hard", "hard"), ("hard", "deselected")] {
                        try press("feedback-" + action)
                        var facts = observe(); facts["interactions"] = ["easy_selected": value("feedback-easy") == "selected", "hard_selected": value("feedback-hard") == "selected"]
                        states[key + "-" + name] = facts; try capture(key + "-" + name)
                    }
                    try press("feedback-report"); try waitFor("report-submit")
                    var facts = observe(); facts["interactions"] = ["submit_disabled": !enabled("report-submit")]
                    states[key + "-report-open"] = facts; try capture(key + "-report-open")
                    try press("report-reason-5")
                    facts = observe(); facts["interactions"] = ["other_checked": checked("report-reason-5"), "submit_enabled": enabled("report-submit")]
                    states[key + "-report-other"] = facts; try capture(key + "-report-other")
                    try press("report-reason-0")
                    facts = observe(); facts["interactions"] = ["both_checked": checked("report-reason-5") && checked("report-reason-0")]
                    states[key + "-report-two"] = facts; try capture(key + "-report-two")
                    try press("report-close")
                    facts = observe(); facts["interactions"] = ["report_closed": !current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "report-submit" }]
                    states[key + "-report-closed"] = facts; try capture(key + "-report-closed")
                    try press("feedback-report"); try waitFor("report-submit")
                    facts = observe(); facts["interactions"] = ["submit_disabled": !enabled("report-submit"), "all_unchecked": (0..<6).allSatisfy { !checked("report-reason-\($0)") }]
                    states[key + "-report-reopened"] = facts; try capture(key + "-report-reopened")
                    try press("report-close")
                }
                if let i = CommandLine.arguments.firstIndex(of: "--stop-after-question-id"), i + 1 < CommandLine.arguments.count,
                   CommandLine.arguments[i + 1] == key { throw ObservationStop.afterQuestion(key) }
                if CommandLine.arguments.contains("--exercise-input-modes"), question["keyboardAnswer"] != nil {
                    try clickOwnedControl("continue")
                } else { try press("continue") }
                if let interludes = definition["interludes"] as? [[String: String]], let interlude = interludes.first(where: { $0["afterQuestionID"] == key }) {
                    try waitFor("lesson-interlude", value: interlude["id"])
                    states[interlude["id"]!] = observe(); try capture(interlude["id"]! + "-window")
                    try press("interlude-continue")
                }
            }
            if CommandLine.arguments.contains("--exercise-source-skip"), let first = questions.first, first["id"] as? String == "en-zh-l7-q0" {
                let intro = definition["reviewInterlude"] as! [String: String]
                try waitFor("lesson-interlude", value: intro["id"])
                states[intro["id"]!] = observe(); try capture(intro["id"]! + "-window")
                try press("interlude-continue"); try waitFor("review-label")
                try waitFor("question-title", value: first["prompt"] as? String)
                if let hint = first["hint"] as? String {
                    guard current().contains(where: { node in [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute].contains { attr(node, $0) as? String == hint } }) else { throw ProbeError(message: "Review original hint not observed") }
                }
                states["en-zh-l7-review-q0"] = observe(); try capture("en-zh-l7-review-q0")
                var skipped = states["en-zh-l7-q0-skipped"]!
                var facts = skipped["interactions"] as! [String: Bool]
                facts["original_question_reviewed"] = current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "review-label" }
                skipped["interactions"] = facts; states["en-zh-l7-q0-skipped"] = skipped
                for word in first["answer_words"] as! [String] { try press("word-bank-" + word) }
                try press("check"); try waitFor("continue")
                states["en-zh-l7-review-q0-feedback"] = observe(); try capture("en-zh-l7-review-q0-feedback")
                try press("continue")
            }
            if fifthErrors {
                let intro = definition["reviewInterlude"] as! [String: String]
                try waitFor("lesson-interlude", value: intro["id"])
                states[intro["id"]!] = observe(); try capture(intro["id"]! + "-window")
                try press("interlude-continue"); try waitFor("review-label")
                states["en-zh-l5-q7-review"] = observe(); try capture("en-zh-l5-q7-review")
                try fillInput("HOT"); try press("check"); try waitFor("continue")
                states["en-zh-l5-q7-review-feedback"] = observe(); try capture("en-zh-l5-q7-review-feedback")
                try press("continue")
            }
            if wrongFirst {
                let first = questions[0]
                try waitFor("question-title", value: first["prompt"] as? String)
                states["en-zh-review-question"] = observe(); try capture("en-zh-review-question")
                try press("option-" + (first["answer"] as! String)); try press("check"); try waitFor("continue")
                states["en-zh-review-feedback"] = observe(); try capture("en-zh-review-feedback"); try press("continue")
            }
            try waitFor("lesson-complete")
            states["lesson-\(lessonIndex + 1)-complete"] = observe()
            if course["interfaceLanguage"] as? String == "zh" { states["en-zh-l\(lessonIndex + 1)-complete"] = observe() }
            if let pages = definition["settlement"] as? [[String: Any]] {
                for (pageIndex, page) in pages.enumerated() {
                    let id = page["id"] as! String
                    try waitFor(page["kind"] as? String == "result" ? "lesson-complete" : "settlement-title", value: page["title"] as? String)
                    var observed = observe()
                    let secondary = page["secondaryLabel"] as? String
                    let actionAvailable = secondary.map { label in current().contains { node in
                        let role = attr(node, kAXRoleAttribute) as? String
                        let text = [kAXTitleAttribute, kAXValueAttribute, kAXDescriptionAttribute].compactMap { attr(node, $0) as? String }
                        return [kAXButtonRole, "AXLink"].contains(role ?? "") && text.contains(label) && (attr(node, kAXEnabledAttribute) as? Bool != false)
                    } } ?? false
                    observed["interactions"] = ["secondary_action_available": actionAvailable]
                    states[id] = observed; try capture(id + "-window")
                    try press("settlement-continue")
                    if pageIndex + 1 < pages.count { try waitFor("settlement-title", value: pages[pageIndex + 1]["title"] as? String) }
                    else { try waitFor("course-entry") }
                    observed["interactions"] = ["secondary_action_available": actionAvailable, "next_state_reached": true]
                    states[id] = observed
                }
            } else { try press("return-path") }
            try waitFor("course-entry")
            states["home-after-lesson-\(lessonIndex + 1)"] = observe()
            if course["interfaceLanguage"] as? String == "zh" { states["en-zh-l\(lessonIndex + 1)-home"] = observe() }
            try capture("home-after-lesson-\(lessonIndex + 1)-window")
            if lessonIndex == 3 && definition["settlement"] != nil {
                try press("start-lesson")
                var observed = observe()
                observed["interactions"] = ["practice_action_available": current().contains { (attr($0, kAXRoleAttribute) as? String) == kAXButtonRole && (attr($0, kAXTitleAttribute) as? String) == "练习 +5 经验" },
                    "legendary_action_available": current().contains { (attr($0, kAXRoleAttribute) as? String) == kAXButtonRole && (attr($0, kAXTitleAttribute) as? String) == "晋升传奇 +40 经验" }]
                states["en-zh-completed-popover"] = observed; try capture("en-zh-completed-popover-window")
                try press("start-lesson"); try press("start-lesson-1")
                observed = observe()
                let start = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "start-lesson-confirm" }
                observed["interactions"] = ["start_enabled": start.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false]
                states["en-zh-next-popover"] = observed; try capture("en-zh-next-popover-window")
                try press("start-lesson-1")
            }
            if lessonIndex == 0 && course["interfaceLanguage"] as? String == "zh" {
                // The frozen English home reference follows the first lesson.
                // Keep initial facts; compare the same state from this run.
                states["home-initial"] = states["home"]
                states["home"] = observe(); try capture("after-first-home-window")
            }
        }
        // Reference Guidebook was observed after the first node's three lessons.
        try press("open-guide"); try waitFor("guide-title")
        states["guidebook"] = observe(); try capture("guidebook-window")
        try press("close-guide"); try waitFor("course-entry")
    } catch ObservationStop.afterQuestion(let id) { stoppedAtQuestion = id }
    catch {
        walkError = String(describing: error)
        states["walk-failure"] = observe()
        try? capture("walk-failure-window")
    }
}
// Read the actual rendered seventh result, not a core-state prediction or score formula.
if var skipped = states["en-zh-l7-q0-skipped"],
   let result = states["en-zh-l7-result"]?["accessible_text"] as? [String],
   result.contains("100%"), result.contains("你练习全对，无错完成本单元") {
    var facts = skipped["interactions"] as? [String: Bool] ?? [:]
    facts["settlement_mistake"] = false
    skipped["interactions"] = facts; states["en-zh-l7-q0-skipped"] = skipped
}
let receipt: [String: Any] = ["kind": "owned_native_ax_observation", "states": states,
    "candidate_binary_sha256": candidateSHA, "fixture_sha256": fixtureSHA,
    "observed_at": ISO8601DateFormatter().string(from: Date()),
    "action": "Start isolated child, collect home, move pointer into More then out, optionally walk the observed course",
    "walk_error": walkError as Any? ?? NSNull(),
    "stopped_at_question": stoppedAtQuestion as Any? ?? NSNull(),
    "pointer_actions": pointerActions,
    "limitations": ["AX text and owned pointer actions; no visual/audio equivalence"]]
let data = try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
try data.write(to: output.appendingPathComponent("observed.json"), options: .withoutOverwriting)
print("Collected actual home and More text from owned child")
if child.isRunning { child.terminate(); child.waitUntilExit() }
if walkError != nil { exit(1) }

}
do { try main() } catch {
    FileHandle.standardError.write(Data(("Native observation failed: \(error)\n").utf8))
    exit(1)
}
