import SwiftUI
import LearningCore

/// Original achievement art and measured fourth-lesson viewport positions.
struct ReferenceObservedAchievement: View {
    let page: SettlementPage
    let advance: () -> Void
    let review: () -> Void
    var body: some View {
        GeometryReader { g in
            ZStack(alignment: .topLeading) {
                ReferenceStyle.image(page.artResource ?? "").resizable().frame(width:150,height:186.75)
                    .offset(x:(g.size.width-150)/2,y:117.9296875+(g.size.height-705)/2)
                Text(page.levelLabel ?? "").font(ReferenceStyle.font(20,bold:true)).foregroundStyle(.white)
                    .frame(width:150,height:24).offset(x:(g.size.width-150)/2,y:258.40625+(g.size.height-705)/2)
                Text(page.title).font(ReferenceStyle.font(24,bold:true)).foregroundStyle(ReferenceStyle.ink)
                    .frame(width:600,height:28).offset(x:(g.size.width-600)/2,y:334.6796875+(g.size.height-705)/2)
                    .accessibilityIdentifier("settlement-title").accessibilityValue(page.title)
                Text(page.body ?? "").font(ReferenceStyle.font(19)).foregroundStyle(ReferenceStyle.secondaryInk)
                    .frame(width:600,height:23).offset(x:(g.size.width-600)/2,y:406.4765625+(g.size.height-705)/2)
                Rectangle().fill(ReferenceStyle.border).frame(height:2).offset(y:g.size.height-140)
                Button(page.secondaryLabel ?? "",action:review).buttonStyle(.plain)
                    .font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.secondaryInk)
                    .frame(width:150,height:48).background(.white,in:RoundedRectangle(cornerRadius:16))
                    .overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2))
                    .shadow(color:ReferenceStyle.border,radius:0,y:2)
                    .offset(x:(g.size.width-920)/2,y:g.size.height-95).accessibilityIdentifier("settlement-secondary")
                Button(page.continueLabel,action:advance).buttonStyle(ReferenceButton(color:ReferenceStyle.green)).frame(width:150,height:50)
                    .offset(x:(g.size.width+920)/2-150,y:g.size.height-95).accessibilityIdentifier("settlement-continue")
            }.frame(width:g.size.width,height:g.size.height,alignment:.topLeading).background(.white)
        }
    }
}
