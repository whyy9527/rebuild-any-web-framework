import SwiftUI

struct ReferenceSpeechPermissionOverlay: View {
    let speech: LearningSpeech
    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
            VStack(alignment: .leading, spacing: 8) {
                Text("未授权使用麦克风").font(ReferenceStyle.font(18, bold: true))
                    .accessibilityIdentifier("speech-denied-title")
                Text(try! AttributedString(markdown: "为了更好地锻炼口语，请允许多邻国访问你的麦克风。你可以点击浏览器地址栏中的录音图标，或点击[这里](https://support.duolingo.com/hc/zh-cn/articles/204642264)寻求帮助。"))
                    .font(ReferenceStyle.font(18)).tint(ReferenceStyle.blue).fixedSize(horizontal: false, vertical: true)
                    .accessibilityChildren {
                        Link("这里", destination: URL(string: "https://support.duolingo.com/hc/zh-cn/articles/204642264")!)
                            .accessibilityIdentifier("speech-denied-help")
                    }
            }.foregroundStyle(ReferenceStyle.ink).padding(30).frame(width: 400)
                .background(.white, in: RoundedRectangle(cornerRadius: 16))
                .overlay(alignment: .topTrailing) {
                    Button { speech.dismissDenial() } label: {
                        ReferenceStyle.image("practice-permission-close-source").resizable().frame(width: 16, height: 16)
                            .frame(width: 36, height: 36).background(.white, in: Circle())
                            .overlay(Circle().strokeBorder(ReferenceStyle.border, lineWidth: 2))
                    }.buttonStyle(.plain).offset(x: 18, y: -18).accessibilityIdentifier("speech-denied-close")
                }
        }
    }
}
