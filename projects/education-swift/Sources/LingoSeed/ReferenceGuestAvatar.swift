import AppKit
import SwiftUI

/// Source categories, choice values, geometry and composable Rive inputs.
struct ReferenceGuestAvatar: View {
    @Binding var savedState: [String:Int]?
    @Binding var savedSkin: Int?
    let leave: () -> Void
    let sidebarWidth: CGFloat
    let animations: Bool
    @State private var draft: [String:Int]
    @State private var category = 0
    @State private var cardHeight: CGFloat = 356
    @State private var touched = false
    @State private var confirming = false
    init(savedState:Binding<[String:Int]?>,savedSkin:Binding<Int?>,sidebarWidth:CGFloat,animations:Bool,leave:@escaping ()->Void) {
        _savedState=savedState;_savedSkin=savedSkin;self.sidebarWidth=sidebarWidth;self.animations=animations;self.leave=leave
        var state=savedState.wrappedValue ?? SourceAvatarPlayer.initial
        if savedState.wrappedValue == nil {state["SkinTone"]=15-(savedSkin.wrappedValue ?? 0)}
        _draft=State(initialValue:state)
    }
    private func select(_ option:SourceAvatarCatalog.Option) {draft[option.state]=option.value;touched=true}
    private func discard() {
        draft=savedState ?? SourceAvatarPlayer.initial
        if savedState == nil {draft["SkinTone"]=15-(savedSkin ?? 0)}
        touched=false;confirming=false;leave()
    }
    var body: some View {
        GeometryReader { g in
            ScrollView {
                ZStack(alignment:.topLeading) {
                    ReferencePracticeControl(label:"",identifier:"avatar-back",enabled:true,action:{if touched {confirming=true} else {leave()}},face:AnyView(ReferenceStyle.image("en-avatar-icon-0").resizable().frame(width:24,height:32)),fixedFaceSize:true).frame(width:24,height:32).offset(x:24,y:24)
                    Text(savedSkin == nil ? "创建虚拟头像" : "修改虚拟头像").font(ReferenceStyle.font(24,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).frame(height:32).offset(x:64,y:24)
                    ZStack(alignment:.topLeading) {
                        RoundedRectangle(cornerRadius:16).fill(.white).overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2))
                        ReferenceAvatarRenderer(states:draft,animations:animations).frame(width:372,height:cardHeight-4).offset(x:2,y:2)
                        Rectangle().fill(ReferenceStyle.border).frame(width:2,height:cardHeight-2).offset(x:374)
                        ForEach(0..<SourceAvatarCatalog.source.stateChooserTabs.count,id:\.self) { i in
                            ReferencePracticeControl(label:"",identifier:"avatar-category-\(i)",enabled:true,action:{category=i;cardHeight=max(cardHeight,CGFloat(SourceAvatarCatalog.layouts[i].region.rect[3]+68))},face:AnyView(ReferenceStyle.image("en-avatar-tab-\(i)-"+(category == i ? "selected":"unselected")).resizable().scaledToFit().frame(width:42,height:32)),fixedFaceSize:true).frame(width:58,height:64).offset(x:392+CGFloat(i)*58,y:2)
                        }
                        Rectangle().fill(ReferenceStyle.border).frame(width:520,height:2).offset(x:376,y:64)
                        Rectangle().fill(ReferenceStyle.blue).frame(width:category == 0 ? 74:58,height:2).offset(x:category == 0 ? 376:392+CGFloat(category)*58,y:64)
                        ReferenceAvatarOptions(category:category,states:draft,select:select).id(category).offset(x:376,y:66)
                    }.frame(width:896,height:cardHeight).clipShape(RoundedRectangle(cornerRadius:16)).offset(x:24,y:80)
                    ReferencePracticeControl(label:"完成",identifier:"avatar-done",enabled:touched,action:{savedState=draft;savedSkin=15-(draft["SkinTone"] ?? 15);confirming=true},face:AnyView(Text("完成").font(ReferenceStyle.font(16,bold:true)).tracking(0.64).foregroundStyle(touched ? .white:ReferenceStyle.disclosureInk).frame(width:136,height:44).background(touched ? ReferenceStyle.blue:ReferenceStyle.border,in:RoundedRectangle(cornerRadius:12)).compositingGroup().shadow(color:touched ? Color(red:24/255,green:153/255,blue:214/255):.clear,radius:0,y:4).frame(height:48,alignment:.top)),fixedFaceSize:true).frame(width:136,height:48).offset(x:784,y:cardHeight+116)
                }.frame(width:g.size.width,height:max(g.size.height,cardHeight+184),alignment:.topLeading)
            }.scrollIndicators(.never)
        }.overlay {GeometryReader {g in if confirming {ReferenceAvatarExit(keep:{confirming=false},discard:discard).frame(width:g.size.width+sidebarWidth,height:g.size.height).offset(x:-sidebarWidth)}}}
    }
}

private struct ReferenceAvatarOptions: View {
    let category:Int
    let states:[String:Int]
    let select:(SourceAvatarCatalog.Option)->Void
    var body: some View {
        let tab=SourceAvatarCatalog.source.stateChooserTabs[category]
        let layout=SourceAvatarCatalog.layouts[category]
        ScrollView {
            ZStack(alignment:.topLeading) {
                ForEach(tab.sections.indices,id:\.self) { group in
                    let section=tab.sections[group],geometry=layout.groups[group]
                    Text(section.header).font(ReferenceStyle.font(20,bold:true)).frame(width:geometry.header_rect[2],height:geometry.header_rect[3],alignment:.leading).offset(x:geometry.header_rect[0],y:geometry.header_rect[1])
                    ForEach(section.options.indices,id:\.self) { index in
                        let option=section.options[index],rect=geometry.options[index].rect
                        AvatarChoiceRadio(identifier:SourceAvatarCatalog.identifier(option),selected:states[option.state]==option.value,size:rect[2],content:content(option),action:{select(option)}).frame(width:rect[2],height:rect[3]).offset(x:rect[0],y:rect[1])
                    }
                }
            }.frame(width:518,height:layout.region.scrollHeight,alignment:.topLeading)
        }.frame(width:518,height:layout.region.rect[3]).scrollIndicators(.never).accessibilityIdentifier("avatar-options")
    }
    private func content(_ option:SourceAvatarCatalog.Option) -> AnyView {
        if let color=option.color {return AnyView(RoundedRectangle(cornerRadius:8).fill(SourceAvatarCatalog.color(color)).frame(width:40,height:40))}
        return AnyView(ReferenceAvatarThumbnail(states:states.merging(option.statesToOverride ?? [option.state:option.value],uniquingKeysWith:{_,new in new})).frame(width:126,height:126))
    }
}

struct ReferenceAvatarExit: View {
    let keep: () -> Void
    let discard: () -> Void
    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
            VStack(spacing:0) {
                Text("确定要退出吗？").font(ReferenceStyle.font(24,bold:true)).frame(height:32).padding(.top,32)
                Text("现在退出的话，刚完成的部分都会丢失哦").font(ReferenceStyle.font(16)).foregroundStyle(ReferenceStyle.secondaryInk).frame(height:24).padding(.top,12)
                ReferencePracticeControl(label:"继续编辑虚拟头像",identifier:"avatar-keep",enabled:true,action:keep,face:AnyView(Text("继续编辑虚拟头像").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(.white).frame(width:336,height:46).background(ReferenceStyle.blue,in:RoundedRectangle(cornerRadius:16)).compositingGroup().shadow(color:Color(red:24/255,green:153/255,blue:214/255),radius:0,y:4).frame(height:50,alignment:.top)),fixedFaceSize:true).frame(width:336,height:50).padding(.top,32)
                ReferencePracticeControl(label:"放弃编辑虚拟头像",identifier:"avatar-discard",enabled:true,action:discard,face:AnyView(Text("放弃编辑虚拟头像").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(Color(red:1,green:75/255,blue:75/255))),fixedFaceSize:true).frame(width:336,height:32).padding(.top,16)
                Spacer(minLength:0)
            }.frame(width:384,height:258).background(.white,in:RoundedRectangle(cornerRadius:16))
        }
    }
}

private struct AvatarChoiceRadio: NSViewRepresentable {
    let identifier: String
    let selected: Bool
    let size: Double
    let content: AnyView
    let action: () -> Void
    final class Coordinator: NSObject {
        var action: () -> Void
        init(_ action:@escaping () -> Void) {self.action=action}
        @objc func choose(_ sender:NSButton) {action()}
    }
    final class Radio: NSButton {
        let face=ReferenceAudioRadio.PassiveHost(rootView:AnyView(EmptyView()))
        override func accessibilityRole() -> NSAccessibility.Role? {.radioButton}
        override func accessibilityValue() -> Any? {state == .on ? 1 : 0}
        override var alignmentRectInsets:NSEdgeInsets {NSEdgeInsets(top:0,left:0,bottom:0,right:0)}
        override var intrinsicContentSize:NSSize {NSSize(width:NSView.noIntrinsicMetric,height:NSView.noIntrinsicMetric)}
        override func draw(_ dirtyRect:NSRect) {}
        override func accessibilityFrame() -> NSRect {guard let window else {return super.accessibilityFrame()};return window.convertToScreen(convert(bounds,to:nil))}
    }
    final class Container:NSView {
        let button=Radio(frame:.zero)
        override var intrinsicContentSize:NSSize {NSSize(width:NSView.noIntrinsicMetric,height:NSView.noIntrinsicMetric)}
    }
    func makeCoordinator() -> Coordinator {Coordinator(action)}
    func makeNSView(context:Context) -> Container {
        let container=Container(frame:.zero);let view=container.button;container.addSubview(view);view.translatesAutoresizingMaskIntoConstraints=false
        NSLayoutConstraint.activate([view.leadingAnchor.constraint(equalTo:container.leadingAnchor),view.trailingAnchor.constraint(equalTo:container.trailingAnchor),view.topAnchor.constraint(equalTo:container.topAnchor),view.bottomAnchor.constraint(equalTo:container.bottomAnchor)])
        container.setAccessibilityElement(false);container.setAccessibilityChildren([view])
        view.setButtonType(.radio);view.isBordered=false;view.target=context.coordinator;view.action=#selector(Coordinator.choose(_:));view.setAccessibilityElement(true);view.setAccessibilityChildren([])
        // The explicit source-sized outer control owns geometry. Letting the
        // nested SwiftUI face publish min/max constraints feeds layout back
        // into the scrolling representable.
        view.face.sizingOptions=[]
        view.addSubview(view.face);view.face.translatesAutoresizingMaskIntoConstraints=false
        NSLayoutConstraint.activate([view.face.leadingAnchor.constraint(equalTo:view.leadingAnchor),view.face.trailingAnchor.constraint(equalTo:view.trailingAnchor),view.face.topAnchor.constraint(equalTo:view.topAnchor),view.face.bottomAnchor.constraint(equalTo:view.bottomAnchor)])
        return container
    }
    func sizeThatFits(_ proposal:ProposedViewSize,nsView:Container,context:Context) -> CGSize? {
        guard let width=proposal.width,let height=proposal.height,width.isFinite,height.isFinite else {return nil};return CGSize(width:width,height:height)
    }
    func updateNSView(_ container:Container,context:Context) {
        let view=container.button
        context.coordinator.action=action;view.state=selected ? .on : .off;view.setAccessibilityIdentifier(identifier);view.setAccessibilityLabel("")
        let edge=selected ? Color(red:132/255,green:216/255,blue:1) : ReferenceStyle.border
        view.face.rootView=AnyView(RoundedRectangle(cornerRadius:12).fill(selected ? Color(red:221/255,green:244/255,blue:1) : .white).overlay(RoundedRectangle(cornerRadius:12).strokeBorder(edge,lineWidth:2)).overlay(content).compositingGroup().shadow(color:edge,radius:0,y:2).frame(height:size-2,alignment:.top).accessibilityHidden(true))
    }
}
