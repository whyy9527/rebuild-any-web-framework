import AppKit
import CoreText
import Foundation
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
for n in ["font-0", "font-1"] {
 let u=root.appendingPathComponent("projects/education-swift/Sources/LingoSeed/Resources/Reference/"+n+".ttf")
 CTFontManagerRegisterFontsForURL(u as CFURL, .process,nil)
}
let text="来复习一下这个等级，完成后有惊喜哦！"
let descriptor=CTFontDescriptorCreateWithAttributes([kCTFontNameAttribute:"DuolingoSans-Thin", kCTFontVariationAttribute:[NSNumber(value:0x77676874):NSNumber(value:700)]] as CFDictionary)
let font=CTFontCreateWithFontDescriptor(descriptor,28,nil)
let string=NSAttributedString(string:text,attributes:[.font:font])
let line=CTLineCreateWithAttributedString(string)
let runs=CTLineGetGlyphRuns(line) as! [CTRun]
let fonts=runs.map { run -> [String:Any] in
 let attr=CTRunGetAttributes(run) as NSDictionary;let f=attr[kCTFontAttributeName] as! CTFont
 return ["postscript":CTFontCopyPostScriptName(f) as String,"family":CTFontCopyFamilyName(f) as String,"size":CTFontGetSize(f),"glyph_count":CTRunGetGlyphCount(run)]
}
let result:[String:Any]=["text":text,"measurement":"CoreText shaping of same native font descriptor; not inspection of rendered SwiftUI glyph runs","fonts":fonts]
print(String(data:try JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys]),encoding:.utf8)!)
