import Foundation
import SwiftUI

struct SourceAvatarCatalog: Decodable {
    struct Option: Decodable { let state: String; let value: Int; let color: String?; let statesToOverride: [String:Int]? }
    struct Section: Decodable {
        let header: String
        let buttonType: String
        let imageButtons: [Option]
        let featureButtons: [Option]
        var options: [Option] { buttonType == "IMAGE" ? imageButtons : featureButtons }
    }
    struct Tab: Decodable { let tabName: String; let sections: [Section] }
    struct ProfileDisplay: Decodable {let backgroundColor: String}
    let avatarOnProfileDisplayOptions: [String:ProfileDisplay]
    let stateChooserTabs: [Tab]
    static let source: SourceAvatarCatalog = load("avatar-builder")
    static let layouts: [SourceAvatarLayout] = load("avatar-layouts")
    private static func load<T:Decodable>(_ name:String) -> T {
        guard let url=Bundle.module.url(forResource:name,withExtension:"json",subdirectory:"Reference"),
              let bytes=try? Data(contentsOf:url),let value=try? JSONDecoder().decode(T.self,from:bytes) else {
            preconditionFailure("Missing original avatar data: " + name)
        }
        return value
    }
    static func color(_ hex:String) -> Color {
        let value=UInt32(hex.dropFirst(),radix:16)!
        return Color(red:Double((value>>16)&255)/255,green:Double((value>>8)&255)/255,blue:Double(value&255)/255)
    }
    static func identifier(_ option:Option) -> String {
        option.state == "SkinTone" ? "avatar-skin-\(15-option.value)" : "avatar-choice-\(option.state)-\(option.value)"
    }
}
struct SourceAvatarLayout: Decodable {
    struct Option: Decodable {let rect:[Double]}
    struct Group: Decodable {let header_rect:[Double];let options:[Option]}
    struct Region: Decodable {let rect:[Double];let scrollHeight:Double}
    let groups:[Group]
    let region:Region
}
