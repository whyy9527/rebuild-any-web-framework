import AppKit
import SwiftUI

/// Actual country control opens a full-window language list; its enrollment
/// link returns to the actual observed English/Chinese learning path.
struct ReferenceGuestLanguages: View {
    let close: () -> Void
    let enroll: () -> Void
    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
            ZStack(alignment:.topLeading) {
                RoundedRectangle(cornerRadius:16).fill(.white)
                Text("所有语言").font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).frame(width:480,height:64)
                Rectangle().fill(ReferenceStyle.border).frame(width:480,height:2).offset(y:64)
                ReferencePracticeControl(label:"",identifier:"guest-profile-languages-close",enabled:true,action:close,face:AnyView(ReferenceStyle.image("en-profile-language-close").resizable().frame(width:16,height:16)),fixedFaceSize:true).frame(width:32,height:32).offset(x:20,y:16)
                RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2).frame(width:432,height:90).offset(x:24,y:90)
                ReferencePracticeControl(label:"英语（中文（简体）） 204 经验",identifier:"guest-profile-language-en-zh",enabled:true,action:enroll,face:AnyView(
                    ZStack(alignment:.topLeading) {
                        Color.clear
                        ReferenceStyle.image("en-home-56c79be7b1d61ed14ae1").resizable().frame(width:48,height:37.0234375).offset(x:16,y:22.234375)
                        ReferenceStyle.image("en-profile-language-zh").resizable().frame(width:30,height:23.140625).offset(x:42,y:46.6171875)
                        Text("英语（中文（简体））").font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.ink).offset(x:80,y:31)
                        Text("204 经验").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.disclosureInk).offset(x:286.8359375,y:31)
                        ReferenceStyle.image("en-profile-language-arrow").resizable().frame(width:10,height:20).offset(x:402,y:34)
                    }.frame(width:428,height:86)
                ),role:.link,fixedFaceSize:true).frame(width:428,height:86).offset(x:26,y:92)
            }.frame(width:480,height:204)
        }
    }
}
