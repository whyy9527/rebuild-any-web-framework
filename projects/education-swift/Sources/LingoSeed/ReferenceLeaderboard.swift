import AppKit
import SwiftUI

/// Observed guest bronze page. Ranking membership and remote status persistence remain unverified.
struct ReferenceLeaderboard: View {
    @Binding var selectedStatus: Int?
    let practice: () -> Void
    let profile: () -> Void
    var body: some View {
        ZStack(alignment:.topLeading) {
            HStack(alignment:.center,spacing:28) {
                ReferenceStyle.image("en-leaderboard-bronze").resizable().frame(width:80,height:91)
                ForEach(0..<9) { _ in ReferenceStyle.image("en-leaderboard-locked").resizable().frame(width:52,height:58) }
            }.offset(x:200)
            Text("青铜等级").font(ReferenceStyle.font(25,bold:true)).foregroundStyle(Color(white:60/255)).frame(width:480,height:30).offset(y:110)
            Text("只要一息尚存，就要坚持到底。来学个单元，挑战本周排行榜！").font(ReferenceStyle.font(19)).foregroundStyle(ReferenceStyle.secondaryInk).multilineTextAlignment(.center).padding(.horizontal,12).fixedSize(horizontal:false,vertical:true).frame(width:480,height:43).offset(y:153.5)
            ReferencePracticeControl(label:"去学个单元",identifier:"leaderboard-practice",enabled:true,action:practice,face:AnyView(Text("去学个单元").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(ReferenceStyle.blue).frame(width:256,height:44).background { RoundedRectangle(cornerRadius:16).fill(.white).overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)).shadow(color:ReferenceStyle.border,radius:0,y:2) }.frame(height:48,alignment:.top)),role:.link)
                .frame(width:256,height:48).offset(x:112,y:215)
            ZStack(alignment:.topLeading) {
                ReferenceStyle.image("en-leaderboard-ghost-rank").resizable().frame(width:16,height:464).offset(x:28)
                ReferenceStyle.image("en-leaderboard-ghost-users").resizable().frame(width:208,height:480).offset(x:68)
                ReferenceStyle.image("en-leaderboard-ghost-xp").resizable().frame(width:48,height:462).offset(x:408)
            }.frame(width:480,height:290,alignment:.topLeading).clipped().mask(LinearGradient(colors:[.white,.white,.clear],startPoint:.top,endPoint:.bottom)).offset(y:311)
            HStack(spacing:21) {
                Text("-").frame(width:24)
                ReferenceLeaderboardAvatar(selectedStatus:$selectedStatus,size:48)
                Spacer();Text("0 经验").font(ReferenceStyle.font(17)).padding(.trailing,34)
            }.font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).padding(.leading,38).frame(width:480,height:72).background(Color(white:247/255),in:RoundedRectangle(cornerRadius:16)).overlay { ReferencePracticeControl(label:"- U 0 经验",identifier:"leaderboard-guest-profile",enabled:true,action:profile,face:AnyView(Color.clear),role:.link).frame(width:480,height:72) }.offset(y:612)
        }.frame(width:480,height:684,alignment:.topLeading).clipped()
    }
}
struct ReferenceLeaderboardStatus: View {
    @Binding var selectedStatus: Int?
    @State private var hovered = false
    @State private var hoveredStatus: Int?
    var body: some View {
        ZStack(alignment:.topLeading) {
            RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)
            Text("设置状态").font(ReferenceStyle.font(19,bold:true)).offset(x:22,y:24.5)
            if hovered {
                ReferencePracticeControl(label:"清除",identifier:"leaderboard-clear",enabled:true,action:{ selectedStatus = nil },face:AnyView(Text("清除").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(ReferenceStyle.blue).frame(width:31.6015625,height:18)))
                    .frame(width:31.6015625,height:18).offset(x:318.3984375,y:27)
            }
            ReferenceLeaderboardAvatar(selectedStatus:$selectedStatus,size:80).offset(x:146,y:75)
            if let selectedStatus {
                ReferenceLeaderboardBadge(index:selectedStatus,size:46,imageSize:40,imageOffset:CGPoint(x:2,y:4),border:ReferenceStyle.border,identifier:"leaderboard-selected-status").offset(x:212,y:63)
            } else {
                ReferenceLeaderboardBadge(index:nil,size:46,imageSize:36,imageOffset:CGPoint(x:5,y:5),border:ReferenceStyle.border,identifier:"leaderboard-default-status").offset(x:212,y:63)
            }
            ForEach(0..<12) { index in
                ReferencePracticeControl(label:"",identifier:"leaderboard-status-\(index)",enabled:true,action:{ selectedStatus=index },face:AnyView(
                    ReferenceStyle.image("en-leaderboard-status-\(index)").resizable().scaledToFit().frame(width:index==5 ? 32 : 44,height:index==5 ? 24.6796875 : 42).frame(width:48,height:46)
                        .background(index==0 || index==6 ? ReferenceLeaderboardBadge.green : .white,in:RoundedRectangle(cornerRadius:12))
                        .overlay(RoundedRectangle(cornerRadius:12).strokeBorder(selectedStatus==index ? Color(red:132/255,green:216/255,blue:255/255) : ReferenceStyle.border,lineWidth:2))
                        .shadow(color:selectedStatus==index ? Color(red:132/255,green:216/255,blue:255/255) : ReferenceStyle.border,radius:0,y:2)
                        .frame(width:48,height:48,alignment:.top).compositingGroup().colorMultiply(hoveredStatus==index ? Color(white:0.9) : .white)))
                    .frame(width:48,height:48).onHover { hoveredStatus = $0 ? index : (hoveredStatus==index ? nil : hoveredStatus) }.offset(x:22+CGFloat(index%6)*56,y:187+CGFloat(index/6)*58)
            }
        }.frame(width:368,height:315).onHover { hovered = $0 }
    }
}
struct ReferenceLeaderboardAvatar: View {
    @Binding var selectedStatus: Int?
    let size: CGFloat
    var body: some View {
        ZStack {
            Circle().stroke(ReferenceStyle.disclosureInk,style:StrokeStyle(lineWidth:2,dash:[3,2]))
            Text("U").font(ReferenceStyle.font(size*0.46,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk)
        }.frame(width:size,height:size).overlay(alignment:.bottomTrailing) { Circle().fill(ReferenceLeaderboardBadge.green).frame(width:size*0.2,height:size*0.2).overlay(Circle().stroke(.white,lineWidth:2)) }
            .overlay(alignment:.topLeading) {
                if size==48, let selectedStatus {
                    ReferenceLeaderboardBadge(index:selectedStatus,size:28,imageSize:24,imageOffset:CGPoint(x:1,y:3),border:Color(white:247/255),identifier:"leaderboard-footer-status").offset(x:36,y:-6)
                }
            }
    }
}

/// Source CSS badge, including its asymmetric bottom-left corner and SVG aspect fit.
struct ReferenceLeaderboardBadge: View {
    static let green = Color(red:88/255,green:204/255,blue:2/255)
    let index: Int?
    let size: CGFloat
    let imageSize: CGFloat
    let imageOffset: CGPoint
    let border: Color
    let identifier: String
    var body: some View {
        ZStack(alignment:.topLeading) {
            UnevenRoundedRectangle(topLeadingRadius:size/2,bottomLeadingRadius:size*0.16,bottomTrailingRadius:size/2,topTrailingRadius:size/2)
                .fill(index==0 || index==6 ? Self.green : .white)
                .overlay(UnevenRoundedRectangle(topLeadingRadius:size/2,bottomLeadingRadius:size*0.16,bottomTrailingRadius:size/2,topTrailingRadius:size/2).strokeBorder(border,lineWidth:2))
            ReferenceLeaderboardBadgeImage(resource:index.map { "en-leaderboard-status-\($0)" } ?? "en-leaderboard-smile",identifier:identifier)
                .frame(width:imageSize,height:imageSize).offset(x:imageOffset.x,y:imageOffset.y)
        }.frame(width:size,height:size)
    }
}

/// Aspect-fit the source image inside an explicit layout box.
/// Strict AX geometry still differs from the source and remains a failed check.
private struct ReferenceLeaderboardBadgeImage: NSViewRepresentable {
    let resource: String
    let identifier: String
    func makeNSView(context: Context) -> NSImageView {
        let view = NSImageView()
        view.imageScaling = .scaleProportionallyUpOrDown
        view.imageAlignment = .alignCenter
        view.imageFrameStyle = .none
        view.focusRingType = .none
        view.setContentCompressionResistancePriority(.defaultLow,for:.horizontal)
        view.setContentCompressionResistancePriority(.defaultLow,for:.vertical)
        view.setAccessibilityElement(true)
        return view
    }
    func sizeThatFits(_ proposal: ProposedViewSize, nsView: NSImageView, context: Context) -> CGSize? {
        guard let width=proposal.width,let height=proposal.height,width.isFinite,height.isFinite else { return nil }
        return CGSize(width:width,height:height)
    }
    func updateNSView(_ view: NSImageView, context: Context) {
        view.image = Bundle.module.url(forResource:resource,withExtension:"png",subdirectory:"Reference").flatMap { NSImage(contentsOf:$0) }
        view.setAccessibilityIdentifier(identifier)
    }
}
