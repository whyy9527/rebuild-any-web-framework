import Foundation
import ApplicationServices
let pid = pid_t(CommandLine.arguments[1])!
let app = AXUIElementCreateApplication(pid)
func attr(_ e: AXUIElement, _ name: String) -> AnyObject? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(e, name as CFString, &value) == .success else { return nil }
    return value
}
func nodes(_ e: AXUIElement) -> [AXUIElement] {
    [e] + ((attr(e, kAXChildrenAttribute) as? [AXUIElement]) ?? []).flatMap(nodes)
}
guard AXIsProcessTrusted() else { print("unavailable: accessibility permission"); exit(2) }
let deadline = Date().addingTimeInterval(15)
while Date() < deadline {
    let own = ((attr(app, kAXWindowsAttribute) as? [AXUIElement]) ?? []).flatMap(nodes)
    if own.contains(where: { attr($0, kAXIdentifierAttribute) as? String == "course-entry" }) {
        print("course_path"); exit(0)
    }
    if own.contains(where: { e in
        [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute].contains { attr(e, $0) as? String == "Course unavailable" }
    }) { print("course_unavailable"); exit(0) }
    Thread.sleep(forTimeInterval: 0.1)
}
print("unavailable: owned app did not show a known startup screen"); exit(2)
