import SwiftUI
import LearningCore

private enum UnitPlacementArt {
    static let resources: [String:String] = {
        guard let url=Bundle.module.url(forResource:"unit-placement-presentation",withExtension:"json",subdirectory:"Reference"),let data=try? Data(contentsOf:url) else {return [:]}
        return (try? JSONDecoder().decode([String:String].self,from:data)) ?? [:]
    }()
}

struct ReferenceUnitPlacementIntro: View {
    let later:()->Void
    let start:()->Void
    var body:some View {
        GeometryReader { g in
            ZStack(alignment:.topLeading) {
                ReferenceStyle.image(UnitPlacementArt.resources["intro"] ?? "").resizable().frame(width:214,height:233)
                    .offset(x:(g.size.width-214)/2,y:144.25+(g.size.height-732)/2)
                Text("挑战通关测试，跳级到第 2 部分！").font(ReferenceStyle.font(24,bold:true))
                    .foregroundStyle(ReferenceStyle.ink).frame(width:600,height:28)
                    .offset(x:(g.size.width-600)/2,y:404.75+(g.size.height-732)/2).accessibilityIdentifier("unit-placement-intro")
                Rectangle().fill(ReferenceStyle.border).frame(height:2).offset(y:g.size.height-140)
                unitControl("下次再说",id:"unit-placement-later",color:nil,action:later).frame(width:103.203125,height:48).offset(x:(g.size.width-920)/2,y:g.size.height-92)
                unitControl("立即开始",id:"unit-placement-start",color:ReferenceStyle.blue,action:start).frame(width:150,height:50).offset(x:(g.size.width+920)/2-150.0078125,y:g.size.height-93)
            }.frame(width:g.size.width,height:g.size.height,alignment:.topLeading).background(.white)
        }
    }
}

/// Original observed unit-12 sequence. Result SVG is one captured animation frame;
/// score-page canvas animation and exact progress width remain unverified gaps.
struct ReferenceUnitPlacementPage: View {
    let page:SettlementPage
    let advance:()->Void
    let review:()->Void
    var body:some View {
        GeometryReader {g in
            ZStack(alignment:.topLeading) {
                if page.kind == "result" {
                    ReferenceStyle.image(UnitPlacementArt.resources["result"] ?? "").resizable().frame(width:310.359375,height:329.3984375)
                        .offset(x:(g.size.width-310.359375)/2,y:52.046875+(g.size.height-732)/2)
                    title(color:Color(red:1,green:200/255,blue:0),size:32).frame(width:600,height:40).offset(x:(g.size.width-600)/2,y:395.6953125+(g.size.height-732)/2)
                    HStack(spacing:20) {
                        stat("总经验",value:"50",color:Color(red:1,green:200/255,blue:0))
                        stat("超级棒",value:"100%",color:ReferenceStyle.green)
                    }.offset(x:(g.size.width-340)/2,y:441.9453125+(g.size.height-732)/2)
                } else if page.kind == "unit_unlock" {
                    ReferenceStyle.image(UnitPlacementArt.resources["unlock"] ?? "").resizable().frame(width:250.828125,height:220)
                        .offset(x:(g.size.width-250.828125)/2,y:145.5+(g.size.height-732)/2)
                    title(size:24).frame(width:600,height:28).offset(x:(g.size.width-600)/2,y:394.5+(g.size.height-732)/2)
                } else if page.kind == "score_progress" {
                    // Source canvas artwork has not yet been recovered as an animated resource.
                    HStack(spacing:28) {
                        ReferenceStyle.image("flag-home").resizable().frame(width:72,height:55)
                        Text(String(page.scoreValue ?? 10)).font(ReferenceStyle.font(64,bold:true))
                    }.frame(width:300,height:76).offset(x:(g.size.width-300)/2,y:265+(g.size.height-732)/2)
                    title(size:28).frame(width:600,height:34).offset(x:(g.size.width-600)/2,y:367.3046875+(g.size.height-732)/2)
                    HStack(spacing:16) {
                        Text("10"); RoundedRectangle(cornerRadius:8).fill(ReferenceStyle.border).frame(height:16); Text("11")
                    }.font(ReferenceStyle.font(24,bold:true)).frame(width:842).offset(x:(g.size.width-842)/2,y:435+(g.size.height-732)/2)
                }
                Rectangle().fill(ReferenceStyle.border).frame(height:2).offset(y:g.size.height-140)
                if let label=page.secondaryLabel {
                    unitControl(label,id:"settlement-secondary",color:nil,action:review).frame(width:150,height:50)
                        .overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2))
                        .offset(x:(g.size.width-920)/2,y:g.size.height-94)
                }
                unitControl(page.continueLabel,id:"settlement-continue",color:page.kind=="score_progress" ? ReferenceStyle.blue : ReferenceStyle.green,action:advance).frame(width:150,height:50)
                    .offset(x:(g.size.width+920)/2-150,y:g.size.height-94)
            }.frame(width:g.size.width,height:g.size.height,alignment:.topLeading).background(.white)
        }
    }
    private func title(color:Color=ReferenceStyle.ink,size:CGFloat)->some View {
        Text(page.title).font(ReferenceStyle.font(size,bold:true)).foregroundStyle(color)
            .accessibilityIdentifier(page.kind=="result" ? "lesson-complete" : "settlement-title").accessibilityValue(page.title)
    }
    private func stat(_ label:String,value:String,color:Color)->some View {
        VStack(spacing:0) {
            Text(label).font(ReferenceStyle.font(13,bold:true)).foregroundStyle(.white).frame(width:160,height:30).background(color)
            Text(value).font(ReferenceStyle.font(20,bold:true)).foregroundStyle(color).frame(width:156,height:58).background(.white,in:RoundedRectangle(cornerRadius:14))
        }.frame(width:160,height:90).background(color,in:RoundedRectangle(cornerRadius:16)).clipShape(RoundedRectangle(cornerRadius:16))
    }
}

@MainActor private func unitControl(_ label:String,id:String,color:Color?,action:@escaping ()->Void)->some View {
    ReferencePracticeControl(label:label,identifier:id,enabled:true,action:action,face:AnyView(
        Text(label).font(ReferenceStyle.font(17,bold:true)).tracking(0.8).foregroundStyle(color == nil ? ReferenceStyle.blue : .white)
            .frame(maxWidth:.infinity).frame(height:color == nil ? 48 : 46)
            .background(color ?? .clear,in:RoundedRectangle(cornerRadius:16))
            .shadow(color:color == nil ? .clear : color==ReferenceStyle.green ? Color(red:70/255,green:163/255,blue:2/255) : Color(red:24/255,green:153/255,blue:214/255),radius:0,y:4)
            .frame(height:50,alignment:.top)
    ),fixedFaceSize:true)
}
