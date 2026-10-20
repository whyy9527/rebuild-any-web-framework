import SwiftUI

/// Observed path-start interruption; Later preserves the underlying path popover.
struct ReferencePathProfile: View {
    let close: () -> Void
    @State private var registration = false
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .topLeading) {
                Color.black.opacity(0.4).ignoresSafeArea()
                ZStack(alignment: .topLeading) {
                    RoundedRectangle(cornerRadius: 16).fill(.white)
                    ReferenceStyle.image("en-path-profile-duo").resizable().frame(width: 144, height: 250)
                        .accessibilityLabel("Duo").accessibilityIdentifier("path-profile-art").offset(x: 153, y: 30)
                    Text("来创建你的个人档案吧！").font(ReferenceStyle.font(32, bold: true)).foregroundStyle(ReferenceStyle.ink)
                        .frame(width: 390, height: 40).offset(x: 30, y: 314.5)
                    Text("创建档案就能保存学习进度，随时都可以继续免费学习后续内容。")
                        .font(ReferenceStyle.font(18, weight: 500)).foregroundStyle(ReferenceStyle.disclosureInk).multilineTextAlignment(.center)
                        .frame(width: 390, height: 40).offset(x: 30, y: 384.5)
                    ReferencePracticeControl(label: "创建档案", identifier: "path-profile-create", enabled: true, action: { registration = true }, face: AnyView(
                        Text("创建档案").font(ReferenceStyle.font(15, bold: true)).foregroundStyle(.white)
                            .frame(width: 300, height: 46).background(ReferenceStyle.blue, in: RoundedRectangle(cornerRadius: 16))
                            .shadow(color: Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: 4).frame(height: 50, alignment: .top)))
                        .frame(width: 300, height: 50).offset(x: 75, y: 454.5)
                    ReferencePracticeControl(label: "稍后创建帐户", identifier: "path-profile-later", enabled: true, action: close, face: AnyView(
                        Text("稍后创建帐户").font(ReferenceStyle.font(15, bold: true)).tracking(0.8).foregroundStyle(ReferenceStyle.disclosureInk)))
                        .frame(width: 94.8046875, height: 18).offset(x: 177.59375, y: 521)
                }.frame(width: 450, height: 569.5)
                    .overlay(alignment: .topTrailing) {
                        Button(action: close) { ReferenceStyle.image("en-path-profile-close").resizable().frame(width: 16, height: 16)
                            .frame(width: 35, height: 35).background(.white, in: Circle()).overlay(Circle().strokeBorder(ReferenceStyle.border, lineWidth: 2)) }
                            .buttonStyle(.plain).accessibilityLabel("关闭").accessibilityIdentifier("path-profile-close").offset(x: 17.5, y: -17.5)
                    }.offset(x: (geometry.size.width - 450) / 2, y: (geometry.size.height - 569.5) / 2)
            }.accessibilityHidden(registration)
                .overlay { if registration { ReferenceRegistration(close: close) } }
        }
    }
}
