import SwiftUI

struct ReferenceSectionPlacementEntry: View {
    let stage:Int
    let later:()->Void
    let start:()->Void
    var body:some View {
        GeometryReader {g in
            ZStack(alignment:.topLeading) {
                ReferenceStyle.image("en-placement-entry-duo").resizable().frame(width:270,height:270).offset(x:(g.size.width-270)/2,y:125.75+(g.size.height-732)/2)
                Text("挑战通关测试，跳级到第  \(stage)  阶段！").font(ReferenceStyle.font(24,bold:true)).foregroundStyle(Color(white:60/255))
                    .frame(width:600,height:28).offset(x:(g.size.width-600)/2,y:423.25+(g.size.height-732)/2).accessibilityIdentifier("section-placement-intro")
                ReferencePracticeControl(label:"下次再说",identifier:"section-placement-later",enabled:true,action:later,face:AnyView(Text("下次再说").font(ReferenceStyle.font(17,bold:true)).tracking(0.8).foregroundStyle(ReferenceStyle.blue)),fixedFaceSize:true).frame(width:103.203125,height:48).offset(x:(g.size.width-920)/2,y:g.size.height-92)
                ReferencePracticeControl(label:"继续",identifier:"section-placement-start",enabled:true,action:start,face:AnyView(Text("继续").font(ReferenceStyle.font(17,bold:true)).foregroundStyle(.white).frame(width:150,height:46).background(ReferenceStyle.blue,in:RoundedRectangle(cornerRadius:16)).compositingGroup().shadow(color:Color(red:24/255,green:153/255,blue:214/255),radius:0,y:4).frame(width:150,height:50,alignment:.top)),fixedFaceSize:true).frame(width:150,height:50).offset(x:g.size.width-(g.size.width-920)/2-150.0078125,y:g.size.height-93)
            }.frame(maxWidth:.infinity,maxHeight:.infinity).background(.white)
        }
    }
}
