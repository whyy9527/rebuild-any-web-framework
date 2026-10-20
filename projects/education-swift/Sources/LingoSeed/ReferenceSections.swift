import SwiftUI

private struct SourceSections: Decodable, Sendable {
    struct TextBox: Decodable, Sendable {let text:String;let rect:[CGFloat]}
    struct Artwork: Decodable, Sendable {let resource:String;let rect:[CGFloat]}
    struct Caption: Decodable, Sendable {let text:String;let rect:[CGFloat];let bubbleRect:[CGFloat];let bordered:Bool}
    struct Card: Decodable, Identifiable, Sendable {
        let stage:Int;var id:Int {stage}
        let active:Bool?
        let completed:Bool?
        let heading:String;let height:CGFloat;let headingRect:[CGFloat]
        let images:[Artwork];let caption:Caption?;let button:TextBox?;let paragraph:TextBox?;let dailyText:TextBox?
    }
    let cards:[Card]
    static let unlocked:SourceSections? = {
        guard let url=Bundle.module.url(forResource:"sections-unlocked-presentation",withExtension:"json",subdirectory:"Reference"),let data=try? Data(contentsOf:url) else {return nil}
        return try? JSONDecoder().decode(SourceSections.self,from:data)
    }()
    static let observed:SourceSections? = {
        guard let url=Bundle.module.url(forResource:"sections-presentation",withExtension:"json",subdirectory:"Reference"),let data=try? Data(contentsOf:url) else {return nil}
        return try? JSONDecoder().decode(SourceSections.self,from:data)
    }()
}

/// Original section inventory and source card geometry; it does not infer test questions.
struct ReferenceSections: View {
    let activeStage:Int
    let completedStages:Set<Int>
    var review:(Int)->Void = {_ in}
    let leave:()->Void
    let jump:(Int)->Void
    var body:some View {
        VStack(alignment:.leading,spacing:0) {
            ReferencePracticeControl(label:"返回",identifier:"sections-return",enabled:true,action:leave,face:AnyView(HStack(spacing:16) {
                ReferenceStyle.image("en-registration-back").resizable().frame(width:16,height:16)
                Text("返回").font(ReferenceStyle.font(22,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk)
            }.frame(width:76,height:27)),role:.link,fixedFaceSize:true).frame(width:76,height:27).padding(.top,59)
            Rectangle().fill(ReferenceStyle.border).frame(height:2).padding(.top,16).padding(.bottom,16)
            if let source=activeStage==2 ? SourceSections.unlocked : SourceSections.observed {
                VStack(spacing:16) {ForEach(source.cards) {card in sectionCard(card)}}
            } else {Text("原版阶段数据无法加载").accessibilityIdentifier("sections-load-error")}
        }.frame(width:516,alignment:.topLeading).padding(.bottom,24)
    }
    private func sectionCard(_ card:SourceSections.Card)->some View {
        ZStack(alignment:.topLeading) {
            RoundedRectangle(cornerRadius:16).fill((card.active ?? (card.stage==1)) ? Color(red:221/255,green:244/255,blue:1) : completedStages.contains(card.stage) ? .white : Color(white:247/255))
            Text(card.heading).font(ReferenceStyle.font(25,bold:true)).foregroundStyle((card.active ?? (card.stage==1)) ? Color(white:60/255) : ReferenceStyle.secondaryInk)
                .frame(width:card.headingRect[2],height:card.headingRect[3],alignment:.leading).offset(x:card.headingRect[0],y:card.headingRect[1])
                .accessibilityIdentifier("sections-heading-\(card.stage)")
            if (card.active ?? (card.stage==1)) {
                Capsule().fill(.white).frame(width:178,height:18).offset(x:24,y:70)
                Capsule().fill(Color(red:88/255,green:204/255,blue:2/255)).frame(width:18,height:18).offset(x:24,y:70)
                Capsule().fill(.white.opacity(0.3)).frame(width:8.796875,height:3).offset(x:28.5,y:74.5)
                Text("0%").font(ReferenceStyle.font(14,bold:true)).tracking(0.56).foregroundStyle(ReferenceStyle.disclosureInk).frame(width:178,height:18).offset(x:24,y:70)
            }
            if let paragraph=card.paragraph {
                Text(paragraph.text).font(ReferenceStyle.font(15,bold:true)).tracking(0.6).foregroundStyle(ReferenceStyle.secondaryInk)
                    .frame(width:paragraph.rect[2],height:paragraph.rect[3],alignment:.leading).offset(x:paragraph.rect[0],y:paragraph.rect[1])
            }
            if let text=card.dailyText {
                Text(text.text).font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.secondaryInk)
                    .frame(width:text.rect[2],height:text.rect[3],alignment:.topLeading).offset(x:text.rect[0],y:text.rect[1])
            }
            if let caption=card.caption {
                RoundedRectangle(cornerRadius:16).fill(.white).overlay {if caption.bordered {RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)}}
                    .frame(width:caption.bubbleRect[2],height:caption.bubbleRect[3]).offset(x:caption.bubbleRect[0],y:caption.bubbleRect[1])
                Text(caption.text).font(ReferenceStyle.font(20)).lineSpacing(4).foregroundStyle(ReferenceStyle.ink)
                    .frame(width:caption.rect[2]-32,alignment:.leading).padding(16).frame(width:caption.rect[2],height:caption.rect[3],alignment:.topLeading).offset(x:caption.rect[0],y:caption.rect[1])
            }
            ForEach(Array(card.images.enumerated()),id:\.offset) {_,image in
                ReferenceStyle.image(image.resource).resizable().frame(width:image.rect[2],height:image.rect[3]).offset(x:image.rect[0],y:image.rect[1])
            }
            if let button=card.button {
                ReferencePracticeControl(label:button.text,identifier:completedStages.contains(card.stage) ? "sections-review-\(card.stage)" : (card.active ?? (card.stage==1)) ? (card.stage==1 ? "sections-continue" : "sections-continue-\(card.stage)") : "sections-jump-\(card.stage)",enabled:true,action:{if completedStages.contains(card.stage) {review(card.stage)} else if card.active ?? (card.stage==1) {leave()} else {jump(card.stage)}},face:AnyView(
                    Text(button.text).font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle((card.active ?? (card.stage==1)) ? .white : ReferenceStyle.blue)
                        .frame(width:button.rect[2],height:button.rect[3]-4).background((card.active ?? (card.stage==1)) ? ReferenceStyle.blue : .white,in:RoundedRectangle(cornerRadius:12))
                        .overlay {if !(card.active ?? (card.stage==1)) {RoundedRectangle(cornerRadius:12).strokeBorder(ReferenceStyle.border,lineWidth:2)}}
                        .compositingGroup().shadow(color:(card.active ?? (card.stage==1)) ? Color(red:24/255,green:153/255,blue:214/255) : ReferenceStyle.border,radius:0,y:4)
                        .frame(width:button.rect[2],height:button.rect[3],alignment:.top)
                ),fixedFaceSize:true).frame(width:button.rect[2],height:button.rect[3]).offset(x:button.rect[0],y:button.rect[1])
            }
        }.frame(width:516,height:card.height).accessibilityElement(children: .contain).accessibilityIdentifier("sections-card-\(card.stage)")
    }
}
