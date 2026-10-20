import SwiftUI
import LearningCore

/// Geometry and artwork from the executed unit12 result. The captured frame is
/// original artwork; it does not stand in for the still-unverified animation.
struct ReferenceObservedCourseResult:View {
    let page:SettlementPage
    let mistakes:Int
    let advance:()->Void
    let review:()->Void
    private let yellow=Color(red:1,green:200/255,blue:0)
    var body:some View {
        GeometryReader {g in
            ZStack(alignment:.topLeading) {
                ReferenceStyle.image(page.artResource ?? "").resizable().frame(width:310.359375,height:329.3984375)
                    .offset(x:(g.size.width-310.359375)/2,y:30.046875+(g.size.height-732)/2)
                Text(page.title).font(ReferenceStyle.font(32,bold:true)).foregroundStyle(yellow)
                    .frame(width:600,height:40).offset(x:(g.size.width-600)/2,y:373.6953125+(g.size.height-732)/2)
                    .accessibilityIdentifier("lesson-complete").accessibilityValue(page.title)
                Text(page.body ?? "").font(ReferenceStyle.font(19)).foregroundStyle(ReferenceStyle.secondaryInk)
                    .frame(width:600,height:24).offset(x:(g.size.width-600)/2,y:425.6953125+(g.size.height-732)/2)
                HStack(spacing:16) {
                    stat("总经验",value:mistakes == page.observedMistakes ? String(page.experience ?? 0) : "—",color:yellow,icon:page.experienceIconResource ?? "")
                    stat(page.accuracyLabel ?? "",value:mistakes == page.observedMistakes ? "\(page.observedAccuracy ?? 0)%" : "—",color:ReferenceStyle.green,icon:page.accuracyIconResource ?? "")
                }.offset(x:(g.size.width-342)/2,y:467.9453125+(g.size.height-732)/2)
                Rectangle().fill(ReferenceStyle.border).frame(height:2).offset(y:g.size.height-140)
                Button(page.secondaryLabel ?? "",action:review).buttonStyle(.plain)
                    .font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.secondaryInk)
                    .frame(width:150,height:48).background(.white,in:RoundedRectangle(cornerRadius:16))
                    .overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2))
                    .shadow(color:ReferenceStyle.border,radius:0,y:2)
                    .offset(x:(g.size.width-920)/2,y:g.size.height-94).accessibilityIdentifier("settlement-secondary")
                Button(page.continueLabel,action:advance).buttonStyle(ReferenceButton(color:ReferenceStyle.green)).frame(width:150,height:50)
                    .offset(x:(g.size.width+920)/2-150,y:g.size.height-94).accessibilityIdentifier("settlement-continue")
            }.frame(width:g.size.width,height:g.size.height,alignment:.topLeading).background(.white)
        }
    }
    private func stat(_ label:String,value:String,color:Color,icon:String)->some View {
        VStack(spacing:0) {
            Text(label).font(ReferenceStyle.font(13,bold:true)).foregroundStyle(.white).frame(width:160,height:26).background(color)
            HStack(spacing:8) {
                ReferenceStyle.image(icon).resizable().scaledToFit().frame(width:22,height:25)
                Text(value).font(ReferenceStyle.font(20,bold:true)).foregroundStyle(color)
            }.frame(width:160,height:66).background(.white,in:RoundedRectangle(cornerRadius:16))
        }.frame(width:163,height:94).clipShape(RoundedRectangle(cornerRadius:16))
            .overlay(RoundedRectangle(cornerRadius:16).strokeBorder(color,lineWidth:2))
    }
}
