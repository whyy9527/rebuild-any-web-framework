import SwiftUI

struct ReferencePronunciation: View {
    @Bindable var model: LearningModel
    struct Phoneme: Decodable, Identifiable {
        let symbol: String
        let word: String
        let group: String
        let source_label: String
        let element: String
        let audio: String?
        var id: String { element }
    }
    private struct Catalog: Decodable { let phonemes: [Phoneme] }
    private static let phonemes: [Phoneme] = {
        guard let url = Bundle.module.url(forResource: "pronunciation", withExtension: "json", subdirectory: "Reference"),
              let data = try? Data(contentsOf: url), let catalog = try? JSONDecoder().decode(Catalog.self, from: data) else { return [] }
        return catalog.phonemes
    }()
    var body: some View {
        VStack(spacing: 0) {
            Text("一起来学英语发音！").font(ReferenceStyle.font(32, bold: true))
                .frame(maxWidth: .infinity).frame(height: 51.1953125)
            Text("磨耳朵，练就地道英语发音").font(ReferenceStyle.font(19))
                .foregroundStyle(ReferenceStyle.secondaryInk).frame(height: 26.59375).padding(.top, 10)
            ReferencePracticeControl(label:"开始 +10 经验",identifier:"pronunciation-start",enabled:true,action:{model.beginPronunciation()},face:AnyView(
                Text("开始 +10 经验").font(ReferenceStyle.font(16, bold: true)).tracking(0.64)
                    .foregroundStyle(.white).frame(width: 264, height: 44)
                    .background(ReferenceStyle.blue, in: RoundedRectangle(cornerRadius: 16, style: .circular))
                    .shadow(color: Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: 4)
                    .frame(width:264,height:48,alignment:.top)
            ),role:.link,fixedFaceSize:true).frame(width:264,height:48)
                .padding(.top, 20).padding(.bottom, 29)
            section("元音")
            section("辅音")
        }.foregroundStyle(ReferenceStyle.ink)
    }
    private func section(_ title: String) -> some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Rectangle().fill(ReferenceStyle.border).frame(height: 2)
                Text(title).font(ReferenceStyle.font(20, bold: true)).fixedSize()
                Rectangle().fill(ReferenceStyle.border).frame(height: 2)
            }.padding(.horizontal, 32).frame(height: 44)
            Grid(horizontalSpacing: 8, verticalSpacing: 8) {
                let phonemes = Self.phonemes.filter { $0.group == title }
                ForEach(0..<(phonemes.count / 3), id: \.self) { row in
                    GridRow { ForEach(0..<3, id: \.self) { column in
                    let phoneme = phonemes[row * 3 + column]
                    Button {
                        if let resource = phoneme.audio { model.audio.speak(phoneme.symbol, resource: resource) }
                    } label: {
                        VStack(spacing: 0) {
                            // Browser CSS 500 resolves to Latin axis 400; keep Chinese fallback weights elsewhere.
                            Text(phoneme.symbol).font(ReferenceStyle.font(19, weight: 400)).tracking(0.8).foregroundStyle(ReferenceStyle.ink).frame(height: 19)
                            Text(phoneme.word).font(ReferenceStyle.font(15, weight: 400)).tracking(0.8).foregroundStyle(ReferenceStyle.disclosureInk).frame(height: 15)
                            Capsule().fill(ReferenceStyle.border).frame(width: 40, height: 8).padding(.top, 5)
                        }.padding(.top, 12).frame(maxWidth: .infinity).frame(height: 68, alignment: .top)
                            .contentShape(Rectangle())
                    }.buttonStyle(ReferencePronunciationCardStyle()).accessibilityLabel(phoneme.source_label).accessibilityIdentifier(phoneme.element)
                    }}
                }
            }.padding(.top, 20)
        }
    }
}

private struct ReferencePronunciationCardStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .background(alignment: .top) {
                RoundedRectangle(cornerRadius: 16, style: .circular).fill(ReferenceStyle.background).frame(height: 66)
                    .shadow(color: ReferenceStyle.border, radius: 0, y: configuration.isPressed ? 0 : 2)
            }
            .overlay(alignment: .top) {
                RoundedRectangle(cornerRadius: 16, style: .circular).strokeBorder(ReferenceStyle.border, lineWidth: 2).frame(height: 66)
            }
            .offset(y: configuration.isPressed ? 2 : 0)
    }
}
