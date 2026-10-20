import SwiftUI
import Lottie

private struct ShoppingGuideSource: Decodable {
    struct Token: Decodable { let label: String; let rect: [CGFloat] }
    struct Phrase: Decodable, Identifiable {
        let id: String
        let english: String
        let translation: String
        let audioResource: String
        let card: [CGFloat]
        let speaker: [CGFloat]
        let englishRect: [CGFloat]
        let translationRect: [CGFloat]
        let tokens: [Token]
    }
    let title: String
    let subtitle: String
    let keyTitle: String
    let titleRect: [CGFloat]
    let subtitleRect: [CGFloat]
    let keyRect: [CGFloat]
    let characterResource: String
    let characterRect: [CGFloat]
    let backResource: String
    let phrases: [Phrase]
    let height: CGFloat
    static let observed: Self? = read("shopping-guide")
    static let unit12: Self? = read("unit12-guide")
    private static func read(_ name:String)->Self? {
        guard let url=Bundle.module.url(forResource:name,withExtension:"json",subdirectory:"Reference"),let data=try? Data(contentsOf:url) else {return nil}
        return try? JSONDecoder().decode(Self.self,from:data)
    }
}

/// Original en/11 and en/12 guides. Source coordinates include actual token bounds;
/// Unit12 token hover produced no immediate popup; click/Enter outcomes remain unknown.
struct ReferenceShoppingGuide: View {
    @Bindable var model: LearningModel
    @State private var speaking: String?
    @State private var playbackID=UUID()
    var body: some View {
        if let source=model.placementOutcome?.activeUnit == 12 ? ShoppingGuideSource.unit12 : ShoppingGuideSource.observed {
            LazyVStack(spacing:0,pinnedViews:[.sectionHeaders]) {
                Section {
                    content(source)
                } header: {
                    back(source)
                }
            }.frame(width:480)
        } else { Text("原版指南未能载入。") }
    }
    private func back(_ source:ShoppingGuideSource)->some View {
        ZStack(alignment:.topLeading) {
            ReferencePracticeControl(label:"返回",identifier:"close-guide",enabled:true,action:{model.destination="Learn"},face:AnyView(
                HStack(spacing:16) {
                    ReferenceStyle.image(source.backResource).resizable().frame(width:16,height:16)
                    Text("返回").font(ReferenceStyle.font(22,bold:true))
                }.foregroundStyle(ReferenceStyle.disclosureInk).frame(width:76,height:27)
            ),role:.link,fixedFaceSize:true).frame(width:76,height:27).offset(y:35)
            Rectangle().fill(ReferenceStyle.border).frame(width:480,height:2).offset(y:78)
        }.frame(width:480,height:80,alignment:.topLeading).background(.white)
    }
    private func content(_ source:ShoppingGuideSource)->some View {
        ZStack(alignment:.topLeading) {
            ReferenceStyle.image(source.characterResource).resizable()
                .frame(width:source.characterRect[2],height:source.characterRect[3])
                .offset(x:source.characterRect[0],y:source.characterRect[1])
            Text(source.title).font(ReferenceStyle.font(25,bold:true))
                .frame(width:318,height:30,alignment:.leading).offset(x:138,y:source.titleRect[1])
                .accessibilityIdentifier("guide-title")
            Text(source.subtitle).font(.custom("PingFangSC-Medium",size:19)).foregroundStyle(ReferenceStyle.secondaryInk)
                .lineSpacing(4).frame(width:318,alignment:.leading).fixedSize(horizontal:false,vertical:true)
                .offset(x:138,y:source.subtitleRect[1])
            Rectangle().fill(ReferenceStyle.border).frame(width:480,height:2).offset(y:208.21875)
            Text(source.keyTitle).font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.blue)
                .frame(width:68,height:20,alignment:.leading).offset(x:source.keyRect[0],y:source.keyRect[1])
            ForEach(source.phrases) { phrase in
                RoundedRectangle(cornerRadius:15).fill(.white)
                    .overlay(RoundedRectangle(cornerRadius:15).strokeBorder(ReferenceStyle.border,lineWidth:2))
                    .frame(width:phrase.card[2],height:phrase.card[3]).offset(x:phrase.card[0],y:phrase.card[1])
                GuideBubbleTail().fill(.white).overlay(GuideBubbleTail().stroke(ReferenceStyle.border,lineWidth:2))
                    .frame(width:8,height:16).offset(x:phrase.card[0]-6,y:phrase.card[1]+22)
                ReferencePracticeControl(label:"",identifier:"guide-speech-"+String(source.phrases.firstIndex(where:{$0.id==phrase.id})!),enabled:true,action:{
                    speaking=phrase.id;playbackID=UUID()
                    model.audio.speak(phrase.english,language:"en",resource:phrase.audioResource)
                },face:AnyView(ShoppingSpeaker(playing:speaking==phrase.id,completed:{speaking=nil}).id(speaking==phrase.id ? playbackID.uuidString : phrase.id)),fixedFaceSize:true)
                    .frame(width:phrase.speaker[2],height:phrase.speaker[3]).offset(x:phrase.speaker[0],y:phrase.speaker[1])
                Text(phrase.english).font(ReferenceStyle.font(17,weight:400)).fixedSize()
                    .frame(width:phrase.englishRect[2],height:20,alignment:.leading)
                    .offset(x:phrase.englishRect[0],y:phrase.englishRect[1]).accessibilityIdentifier(phrase.id+"-english")
                ForEach(Array(phrase.tokens.enumerated()),id:\.offset) { _, token in
                    Path { p in p.move(to:.zero);p.addLine(to:CGPoint(x:token.rect[2],y:0)) }
                        .stroke(ReferenceStyle.disclosureInk,style:StrokeStyle(lineWidth:2,dash:[3,3]))
                        .frame(width:token.rect[2],height:2).offset(x:token.rect[0],y:token.rect[1]+23)
                }
                Text(phrase.translation).font(.custom("PingFangSC-Regular",size:17)).foregroundStyle(ReferenceStyle.disclosureInk)
                    .fixedSize().frame(width:phrase.translationRect[2],height:24,alignment:.leading)
                    .offset(x:phrase.translationRect[0],y:phrase.translationRect[1]).accessibilityIdentifier(phrase.id+"-translation")
            }
        }.frame(width:480,height:source.height,alignment:.topLeading)
    }
}
private struct GuideBubbleTail: Shape {
    func path(in r:CGRect)->Path { Path {p in p.move(to:CGPoint(x:r.maxX,y:r.minY));p.addLine(to:CGPoint(x:r.minX,y:r.midY));p.addLine(to:CGPoint(x:r.maxX,y:r.maxY))} }
}
private struct ShoppingSpeaker: View {
    let playing: Bool
    let completed: ()->Void
    private static let animation:LottieAnimation? = {
        guard let url=Bundle.module.url(forResource:"en-guide-speaker-animation",withExtension:"json",subdirectory:"Reference"),let data=try? Data(contentsOf:url) else {return nil}
        return try? LottieAnimation.from(data:data)
    }()
    var body:some View {
        if !playing { ReferenceStyle.image("en-shopping-guide-speaker-idle").resizable() }
        else if let animation=Self.animation {
            LottieView(animation:animation).resizable()
                .valueProvider(ColorValueProvider(LottieColor(r:28.0/255,g:176.0/255,b:246.0/255,a:1)),for:AnimationKeypath(keypath:"**.Color"))
                .playing(.fromProgress(0,toProgress:1,loopMode:.playOnce))
                .animationDidFinish { finished in if finished {completed()} }
        }
    }
}
