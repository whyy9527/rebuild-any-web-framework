import SwiftUI
import Lottie

private struct StageTwoPath: Decodable {
    struct Node: Decodable, Identifiable {
        let id: String
        let label: String
        let test: String
        let rect: [CGFloat]
        let imageRect: [CGFloat]
        let resource: String
        let active: Bool
        let role: String
    }
    struct Artwork: Decodable { let rect: [CGFloat]; let resource: String; let animationResource: String? }
    struct Heading: Decodable { let text: String; let rect: [CGFloat] }
    struct Chest: Decodable, Identifiable { let id: String; let rect: [CGFloat]; let imageRect: [CGFloat]; let resource: String; let enabled: Bool }
    let nodes: [Node]
    let headerBack: String
    let chests: [Chest]
    let artwork: [Artwork]
    let headings: [Heading]
    let height: CGFloat
    static let observed: Self? = load("stage2-path-presentation")
    static let unit12: Self? = load("unit12-path-presentation")
    private static func load(_ name:String)->Self? {
        guard let url=Bundle.module.url(forResource:name,withExtension:"json",subdirectory:"Reference"),
              let data=try? Data(contentsOf:url) else {return nil}
        return try? JSONDecoder().decode(Self.self,from:data)
    }
}

/// Coordinates and artwork from the actual rendered source path. Later virtualized
/// units and still-unobserved action outcomes remain in the exploration frontier.
struct ReferenceStageTwoPath: View {
    static var backResource: String { StageTwoPath.observed?.headerBack ?? "back" }
    let start: () -> Void
    var activeUnit:Int? = nil
    var unitLessonNumber:Int = 1
    let jump: () -> Void
    let firstLessonCompleted: Bool
    @Binding var selected: String?
    private var blue:Color {activeUnit==12 ? Color(red:204/255,green:52/255,blue:141/255) : ReferenceStyle.blue}
    var body: some View {
        if let source=activeUnit==12 ? StageTwoPath.unit12 : StageTwoPath.observed {
            ZStack(alignment:.topLeading) {
                ForEach(Array(source.artwork.enumerated()),id:\.offset) { _, art in
                    Group {
                        if let resource=art.animationResource { ReferenceStageCharacter(resource:resource) }
                        else { ReferenceStyle.image(art.resource).resizable() }
                    }.frame(width:art.rect[2],height:art.rect[3])
                        .offset(x:art.rect[0],y:art.rect[1]).accessibilityIdentifier("stage2-character-animation")
                }
                ForEach(source.chests) { chest in
                    ReferencePracticeControl(label:"宝箱",identifier:chest.id,enabled:chest.enabled,action:{},face:AnyView(
                        ReferenceStyle.image(chest.resource).resizable().frame(width:chest.imageRect[2],height:chest.imageRect[3])
                            .offset(y:chest.imageRect[1]-chest.rect[1])
                    ),fixedFaceSize:true).frame(width:chest.rect[2],height:chest.rect[3]).offset(x:chest.rect[0],y:chest.rect[1])
                }
                ForEach(Array(source.headings.enumerated()),id:\.offset) { _, h in
                    HStack(spacing:16) { Rectangle().fill(ReferenceStyle.border).frame(height:2);Text(h.text).font(ReferenceStyle.font(19,bold:true)).fixedSize();Rectangle().fill(ReferenceStyle.border).frame(height:2) }
                        .foregroundStyle(ReferenceStyle.disclosureInk).frame(width:480,height:h.rect[3]).offset(y:h.rect[1])
                }
                ForEach(source.nodes) { node in
                    if node.active {
                        if activeUnit == 12 && unitLessonNumber == 5 {
                            ReferenceStyle.image("en-unit12-ring-5").resizable().frame(width:98,height:92.7080078125)
                                .offset(x:node.rect[0]-14,y:node.rect[1]-13.85400390625)
                        } else {
                            Ellipse().stroke(ReferenceStyle.border,lineWidth:8).frame(width:90,height:85)
                                .offset(x:node.rect[0]-10,y:node.rect[1]-10)
                        }
                    }
                    ReferencePracticeControl(label:node.active && activeUnit == 12 ? "Lesson \(unitLessonNumber) of 6" : node.active && firstLessonCompleted ? "Lesson 2 of 5" : node.label,identifier:node.id,enabled:true,
                        action:{if node.id=="stage2-path-7" && node.role=="link" {jump()} else {selected=selected==node.id ? nil : node.id}},face:AnyView(
                            ZStack(alignment:.topLeading) {
                                Ellipse().fill(node.active ? blue : ReferenceStyle.border).overlay(Ellipse().fill(.black.opacity(0.2)))
                                    .frame(width:70,height:57).offset(y:8)
                                Ellipse().fill(node.active ? blue : ReferenceStyle.border).frame(width:70,height:57)
                                ReferenceStyle.image(node.resource).resizable().frame(width:42,height:34).offset(x:14,y:11.5)
                            }.frame(width:70,height:65).contentShape(Rectangle())
                        ),role:node.role=="link" ? .link : .button,fixedFaceSize:true)
                        .frame(width:node.rect[2],height:node.rect[3]).offset(x:node.rect[0],y:node.rect[1])
                }
                if let active=source.nodes.first(where:{$0.active}),selected != active.id {
                    Text("开始").font(ReferenceStyle.font(17,bold:true)).tracking(0.51).foregroundStyle(blue)
                        .frame(width:78,height:42).background(.white,in:RoundedRectangle(cornerRadius:10))
                        .overlay(RoundedRectangle(cornerRadius:10).strokeBorder(ReferenceStyle.border,lineWidth:2))
                        .offset(x:201,y:activeUnit==12 ? active.rect[1]-46 : 31).accessibilityIdentifier("stage2-path-start-label")
                }
                if selected=="stage2-path-0" || selected=="unit12-path-0" { lessonPopup.offset(x:92.5,y:activeUnit == 12 ? 270.1484375 : 170) }
                if selected=="stage2-path-1" { lockedPopup("篮球运动员",id:"stage2-story-locked").offset(x:92.5,y:248.8515625) }
                if selected=="unit12-path-2" {lockedPopup("公寓参观",id:"unit12-radio-locked").offset(x:92.5,y:434.375)}
            }.frame(width:480,height:source.height,alignment:.topLeading)
        } else { Text("原版阶段路径未能载入。") }
    }
    private var lessonPopup: some View {
        VStack(alignment:.leading,spacing:0) {
            Text(activeUnit == 12 ? "描述你的家居布局" : "购买食品杂货").font(ReferenceStyle.font(19,bold:true)).frame(height:26.6)
            Text(activeUnit == 12 ? "第 \(unitLessonNumber)/6 单元" : (firstLessonCompleted ? "第 2/5 单元" : "第 1/5 单元")).font(ReferenceStyle.font(17)).frame(height:26.6)
            ReferencePracticeControl(label:"开始 +10 经验",identifier:"stage2-lesson-confirm",enabled:true,action:start,face:AnyView(
                Text("开始 +10 经验").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(blue)
                    .frame(width:263,height:46).background(.white,in:RoundedRectangle(cornerRadius:16))
                    .shadow(color:ReferenceStyle.border,radius:0,y:4).frame(height:50,alignment:.top)
            ),role:.link,fixedFaceSize:true).frame(width:263,height:50).padding(.top,16)
        }.foregroundStyle(.white).padding(16).frame(width:295).background(blue,in:RoundedRectangle(cornerRadius:15))
    }
    private func lockedPopup(_ title:String,id:String)->some View {
        VStack(alignment:.leading,spacing:8) {
            Text(title).font(ReferenceStyle.font(19,bold:true))
            Text("完成以上全部等级才可以解锁哦！").font(ReferenceStyle.font(19)).lineSpacing(4).fixedSize(horizontal:false,vertical:true)
            ReferencePracticeControl(label:"未解锁",identifier:id,enabled:false,action:{},face:AnyView(
                Text("未解锁").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).frame(width:259,height:50)
                    .background(ReferenceStyle.border,in:RoundedRectangle(cornerRadius:16))
            ),fixedFaceSize:true).frame(width:259,height:50).padding(.top,4)
        }.foregroundStyle(ReferenceStyle.disclosureInk).padding(18).frame(width:295,height:181.8046875)
            .background(Color(white:247/255),in:RoundedRectangle(cornerRadius:15))
            .overlay(RoundedRectangle(cornerRadius:15).strokeBorder(ReferenceStyle.border,lineWidth:2))
    }
}

private struct ReferenceStageBea: View {
    private static let animation: LottieAnimation? = {
        guard let url=Bundle.module.url(forResource:"en-stage2-bea-smores",withExtension:"json",subdirectory:"Reference"),
              let data=try? Data(contentsOf:url) else {return nil}
        return try? LottieAnimation.from(data:data)
    }()
    var body: some View {
        if let animation=Self.animation { LottieView(animation:animation).resizable().looping() }
        else { Text("原版角色动画未能载入。") }
    }
}

private struct ReferenceStageCharacter: View {
    private let animation:LottieAnimation?
    init(resource:String) {
        if let url=Bundle.module.url(forResource:resource,withExtension:"json",subdirectory:"Reference"),let data=try? Data(contentsOf:url) {
            animation=try? LottieAnimation.from(data:data)
        } else {animation=nil}
    }
    var body:some View {
        if let animation {LottieView(animation:animation).resizable().looping()}
        else {Text("原版角色动画未能载入。")}
    }
}
