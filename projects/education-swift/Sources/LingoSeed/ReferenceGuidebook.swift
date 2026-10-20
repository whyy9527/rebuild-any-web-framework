import SwiftUI

struct GuidebookContent: Decodable {
    struct Phrase: Decodable { let spanish: String; let english: String; let audioResource: String }
    let title: String
    let subtitle: String
    let phrases: [Phrase]
    let tipTitle: String
    let tipDescription: String
    let examples: [Phrase]
    static let unitOne: Self? = {
        guard let url = Bundle.module.url(forResource: "guidebook-unit-1", withExtension: "json", subdirectory: "Reference"), let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(Self.self, from: data)
    }()
}

struct ReferenceGuidebook: View {
    @Bindable var model: LearningModel
    var body: some View {
        if let content = GuidebookContent.unitOne {
            VStack(alignment: .leading, spacing: 0) {
                Button { model.destination = "Learn" } label: {
                    HStack(spacing: 16) { ReferenceStyle.image("back").renderingMode(.template).resizable().frame(width: 16, height: 16); Text("Back").font(ReferenceStyle.font(20, bold: true)) }
                        .foregroundStyle(ReferenceStyle.disclosureInk).frame(height: 24)
                }.buttonStyle(.plain).accessibilityIdentifier("close-guide").padding(.bottom, 30)
                rule
                HStack(alignment: .top, spacing: 30) {
                    ReferenceStyle.image("duo-observed-frame").resizable().scaledToFit().frame(width: 108, height: 116)
                    VStack(alignment: .leading, spacing: 8) {
                        Text(content.title).font(ReferenceStyle.font(25, bold: true)).frame(maxWidth: .infinity, alignment: .leading).accessibilityIdentifier("guide-title")
                        Text(content.subtitle).font(ReferenceStyle.font(19)).foregroundStyle(ReferenceStyle.secondaryInk).lineSpacing(5).fixedSize(horizontal: false, vertical: true)
                    }.padding(.top, 24).padding(.trailing, 24)
                }.padding(.top, 24).padding(.bottom, 48)
                rule
                Text("KEY PHRASES").font(ReferenceStyle.font(16, bold: true)).foregroundStyle(ReferenceStyle.blue).padding(.top, 34).padding(.bottom, 12)
                VStack(alignment: .leading, spacing: 22) {
                    ForEach(Array(content.phrases.enumerated()), id: \.offset) { index, phrase in phraseRow(phrase, index: index) }
                }
                Text("TIP").font(ReferenceStyle.font(16, bold: true)).foregroundStyle(ReferenceStyle.blue).padding(.top, 36)
                Text(content.tipTitle).font(ReferenceStyle.font(24, bold: true)).padding(.top, 12)
                Text(content.tipDescription).font(ReferenceStyle.font(19)).fixedSize(horizontal: false, vertical: true).padding(.top, 16)
                VStack(spacing: 0) {
                    tableRow("Spanish", "English", heading: true)
                    tableRow("y", "and")
                    tableRow("o", "or")
                }.overlay(RoundedRectangle(cornerRadius: 12).stroke(ReferenceStyle.border, lineWidth: 2)).padding(.vertical, 24)
                VStack(alignment: .leading, spacing: 22) {
                    ForEach(Array(content.examples.enumerated()), id: \.offset) { index, phrase in phraseRow(phrase, index: index + content.phrases.count) }
                }
            }.frame(maxWidth: 528, alignment: .leading).padding(.bottom, 48)
        } else { Text("Guidebook content could not be loaded.") }
    }
    private var rule: some View { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
    private func phraseRow(_ phrase: GuidebookContent.Phrase, index: Int) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Button { model.audio.speak(phrase.spanish, language: "es", resource: phrase.audioResource) } label: {
                ReferenceStyle.image("guide-speaker").resizable().frame(width: 29, height: 22)
            }.buttonStyle(.plain).accessibilityLabel("Listen: " + phrase.spanish).accessibilityIdentifier("guide-speech-\(index)")
            VStack(alignment: .leading, spacing: 12) {
                Text(phrase.spanish).font(ReferenceStyle.font(17)).fixedSize(horizontal: false, vertical: true)
                Text(phrase.english).font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.disclosureInk).fixedSize(horizontal: false, vertical: true)
            }
        }.padding(18).overlay(RoundedRectangle(cornerRadius: 16).stroke(ReferenceStyle.border, lineWidth: 2)).padding(.leading, 8)
    }
    private func tableRow(_ spanish: String, _ english: String, heading: Bool = false) -> some View {
        HStack { Text(spanish).frame(maxWidth: .infinity); Text(english).frame(maxWidth: .infinity) }
            .font(ReferenceStyle.font(17, bold: heading)).padding(16).background(heading ? ReferenceStyle.border.opacity(0.35) : .clear)
            .overlay(alignment: .bottom) { rule }
    }
}
