import SwiftUI
import LearningCore

/// Frozen fourth-lesson profile prompt; geometry from the original 1192x705 viewport.
struct ReferenceObservedProfile: View {
    let page: SettlementPage
    let advance: () -> Void
    @State private var registration = false
    var body: some View {
        GeometryReader { g in
            let left = (g.size.width - 300) / 2
            let dy = (g.size.height - 705) / 2
            ZStack(alignment: .topLeading) {
                ReferenceStyle.image("en-path-profile-duo").resizable().frame(width: 115, height: 200)
                    .offset(x: (g.size.width - 115) / 2, y: 145 + dy).accessibilityIdentifier("settlement-profile-art")
                Text(page.title).font(ReferenceStyle.font(32, bold: true)).foregroundStyle(Color(white: 60/255))
                    .frame(width: 600, height: 40).offset(x: (g.size.width - 600) / 2, y: 374.5 + dy)
                    .accessibilityIdentifier("settlement-title").accessibilityValue(page.title)
                Text(page.body ?? "").font(ReferenceStyle.font(18)).foregroundStyle(Color(white: 153/255))
                    .frame(width: 600, height: 21).offset(x: (g.size.width - 600) / 2, y: 444.5 + dy)
                control(page.secondaryLabel ?? "创建档案", id: "settlement-secondary", blue: true, action: { registration = true })
                    .offset(x: left, y: 495 + dy)
                control(page.continueLabel, id: "settlement-continue", blue: false, action: advance)
                    .offset(x: left, y: 560 + dy)
            }.frame(width: g.size.width, height: g.size.height, alignment: .topLeading).background(.white)
                .accessibilityHidden(registration)
                .overlay { if registration { ReferenceRegistration(close: { registration = false }) } }
        }
    }
    private func control(_ label: String, id: String, blue: Bool, action: @escaping () -> Void) -> some View {
        ReferencePracticeControl(label: label, identifier: id, enabled: true, action: action, face: AnyView(
            Text(label).font(ReferenceStyle.font(15, bold: true)).tracking(0.8)
                .foregroundStyle(blue ? .white : ReferenceStyle.disclosureInk)
                .frame(width: 300, height: 46)
                .background(blue ? ReferenceStyle.blue : .white, in: RoundedRectangle(cornerRadius: 16))
                .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(blue ? .clear : ReferenceStyle.border, lineWidth: 2))
                .shadow(color: blue ? Color(red: 24/255, green: 153/255, blue: 214/255) : ReferenceStyle.border, radius: 0, y: 4)
                .frame(height: 50, alignment: .top)))
            .frame(width: 300, height: 50)
    }
}
