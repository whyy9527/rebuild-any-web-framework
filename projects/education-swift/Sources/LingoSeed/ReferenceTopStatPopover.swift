import SwiftUI

/// Actual en/zh hover panels. Enrollment remains incomplete.
struct ReferenceTopStatPopover: View {
    let kind: String
    let gems: Int
    let hearts: Int
    let refill: () -> Void
    let practice: () -> Void
    let superSignup: () -> Void
    let flagResource: String
    let selectEnglish: () -> Void
    let visitShop: () -> Void
    var body: some View {
        ZStack(alignment:.topLeading) {
            if kind == "hearts" {
                heartPanel
            } else if kind == "gems" {
                face(width:384,height:152)
                ReferenceStyle.image("en-stats-0de4611fd4d7c682803e").resizable().frame(width:100,height:100).offset(x:14,y:21)
                Text("宝石").font(ReferenceStyle.font(24,bold:true)).frame(width:118,height:28,alignment:.leading).offset(x:126,y:31.75)
                Text("你有 \(gems) 颗宝石").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk).fixedSize().offset(x:126,y:68.75)
                ReferencePracticeControl(label:"访问宝石小店",identifier:"stat-gems-shop",enabled:true,action:visitShop,face:AnyView(Text("访问宝石小店").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(ReferenceStyle.blue)),role:.link,fixedFaceSize:true)
                    .frame(width:94.8046875,height:18).offset(x:126,y:100.75)
                arrow(x:261.9296875,y:-5.0703125)
            } else {
                face(width:244,height:163.3515625)
                Text("我的课程").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).frame(width:90,height:20,alignment:.leading).offset(x:22,y:14)
                Rectangle().fill(ReferenceStyle.border).frame(width:240,height:2).offset(x:2,y:48)
                ReferencePracticeControl(label:"英语",identifier:"stat-course-english",enabled:true,action:selectEnglish,face:AnyView(ZStack(alignment:.topLeading) {
                    Rectangle().fill(Color(red:221/255,green:244/255,blue:1))
                    ReferenceStyle.image(flagResource).resizable().frame(width:32,height:24.6812438965).offset(x:20,y:13.0851593018)
                    Text("英语").font(ReferenceStyle.font(17,bold:true)).foregroundStyle(Color(red:24/255,green:153/255,blue:214/255)).frame(width:34,height:20).offset(x:72,y:17.671875)
                }),role:.menuItem,fixedFaceSize:true).frame(width:240,height:55.3515625).offset(x:2,y:50)
                Rectangle().fill(ReferenceStyle.border).frame(width:240,height:2).offset(x:2,y:105.3515625)
                ReferenceStyle.image("en-stats-96c4427d97cc128e7a1f").resizable().frame(width:44,height:30).offset(x:16,y:119.3515625)
                Text("添加新课程").font(ReferenceStyle.font(17,bold:true)).frame(width:85,height:20).offset(x:75,y:124.3515625)
                    .accessibilityIdentifier("stat-course-add-label")
                arrow(x:114.9296875,y:-5.0703125)
            }
        }.foregroundStyle(ReferenceStyle.ink)
        .frame(width:kind == "gems" ? 384 : kind == "hearts" ? 404 : 244,height:kind == "gems" ? 152 : kind == "hearts" ? (hearts >= 5 ? 398.5 : 402.5) : 163.3515625,alignment:.topLeading)
    }
    private var heartPanel: some View {
        let full=hearts >= 5
        let shift:CGFloat=full ? -4 : 0
        return ZStack(alignment:.topLeading) {
            face(width:404,height:full ? 398.5 : 402.5)
            Text("红心").font(ReferenceStyle.font(25,bold:true)).frame(width:50,height:29.5).offset(x:177,y:27)
            ForEach(0..<5,id:\.self) { i in
                ReferenceStyle.image(i < hearts ? "en-heartmenu-088202fb75fb12b0" : "en-heartmenu-empty").resizable().frame(width:i < hearts ? 32 : 36,height:i < hearts ? 32 : 36).offset(x:104+CGFloat(i)*40,y:i < hearts ? 74 : 72)
            }
            if full {
                Text("红心满满").font(ReferenceStyle.font(19,bold:true)).frame(width:76,height:22.5).offset(x:164,y:119)
            } else {
                HStack(spacing:0) {Text("获取下一颗红心还要等");Text("2 小时").foregroundStyle(Color(red:1,green:75/255,blue:75/255))}.font(ReferenceStyle.font(19,bold:true)).fixedSize().offset(x:79.8359375,y:123)
            }
            Text(full ? "继续加油吧！" : "你还有红心呢！接着练吧！").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk).fixedSize().offset(x:full ? 151 : 100,y:158.5+shift)
            heartAction("无限红心 订购 Super",id:"stat-hearts-super",enabled:true,icon:"en-heartmenu-9e00c8c23d5e6c5b",title:"无限红心",suffix:AnyView(Text("订购 SUPER").foregroundStyle(Color(red:207/255,green:23/255,blue:200/255))),action:superSignup).offset(x:22,y:196.5+shift)
            heartAction("补心 350",id:"stat-hearts-refill",enabled:!full && gems >= 350,icon:"en-heartmenu-e93dc7a895769639",title:"补心",suffix:AnyView(HStack(spacing:0) {ReferenceStyle.image("en-heartmenu-010dc0f82e89bc22").resizable().frame(width:24,height:24);Text("350").foregroundStyle(ReferenceStyle.blue)}),action:refill).offset(x:22,y:258.5+(full ? -2 : 0))
            heartAction("做练习获取红心",id:"stat-hearts-practice",enabled:!full,icon:"en-heartmenu-088202fb75fb12b0",title:"做练习获取红心",suffix:AnyView(EmptyView()),action:practice).offset(x:22,y:320.5+(full ? -2 : 0))
            arrow(x:352.9296875,y:-5.0703125)
        }
    }
    private func heartAction(_ label:String,id:String,enabled:Bool,icon:String,title:String,suffix:AnyView,action:@escaping ()->Void)->some View {
        ReferencePracticeControl(label:label,identifier:id,enabled:enabled,action:action,face:AnyView(
            HStack(spacing:8) {ReferenceStyle.image(icon).resizable().frame(width:36,height:36);Text(title);Spacer(minLength:0);suffix}.font(ReferenceStyle.font(15,bold:true)).padding(.horizontal,18).frame(width:360,height:50)
                .background(.white,in:RoundedRectangle(cornerRadius:16,style:.circular)).overlay(RoundedRectangle(cornerRadius:16,style:.circular).strokeBorder(ReferenceStyle.border,lineWidth:2)).shadow(color:ReferenceStyle.border,radius:0,y:4).frame(height:54,alignment:.top).opacity(enabled ? 1 : 0.5)
        ),fixedFaceSize:true).frame(width:360,height:54)
    }
    private func face(width:CGFloat,height:CGFloat)->some View {
        RoundedRectangle(cornerRadius:15,style:.circular).fill(.white)
            .overlay(RoundedRectangle(cornerRadius:15,style:.circular).strokeBorder(ReferenceStyle.border,lineWidth:2)).frame(width:width,height:height)
    }
    private func arrow(x:CGFloat,y:CGFloat)->some View {
        RoundedRectangle(cornerRadius:2,style:.circular).fill(.white).overlay(RoundedRectangle(cornerRadius:2,style:.circular).strokeBorder(ReferenceStyle.border,lineWidth:2)).frame(width:14.140625,height:14.140625).rotationEffect(.degrees(45)).offset(x:x,y:y)
            .overlay(Rectangle().fill(.white).frame(width:20,height:8).offset(x:x-4,y:2))
    }
}
