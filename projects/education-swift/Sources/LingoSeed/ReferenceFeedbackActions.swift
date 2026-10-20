import SwiftUI

struct ReferenceFeedbackActions: View {
    @Bindable var model: LearningModel
    let color: Color
    var body: some View {
        HStack(spacing: 24) {
            difficulty("太简单", value: "easy")
            difficulty("太难", value: "hard")
            Button { model.openQuestionReport() } label: {
                HStack(spacing: 5) {
                    ReferenceStyle.image("feedback-report").resizable().scaledToFit().frame(width: 20, height: 20)
                    Text("报错")
                }
            }.accessibilityIdentifier("feedback-report")
        }.font(ReferenceStyle.font(17)).foregroundStyle(color).buttonStyle(.plain)
    }
    private func difficulty(_ label: String, value: String) -> some View {
        Button { model.rateDifficulty(value) } label: {
            HStack(spacing: 5) {
                SourceDifficultyGlyph(easy: value == "easy").stroke(style: StrokeStyle(lineWidth: 2 * 20 / 24, lineCap: .round, lineJoin: .round)).frame(width: 20, height: 20)
                Text(label).underline(model.feedbackDifficulty == value).font(ReferenceStyle.font(17, bold: model.feedbackDifficulty == value))
            }
        }.accessibilityIdentifier("feedback-" + value)
            .accessibilityValue(model.feedbackDifficulty == value ? "selected" : "unselected")
    }
}

/// Paths from the actually observed 24x24 source SVG, using its currentColor.
private struct SourceDifficultyGlyph: Shape {
    let easy: Bool
    func path(in rect: CGRect) -> Path {
        var p = Path()
        if easy {
            p.move(to: CGPoint(x: 5, y: 8));p.addLines([CGPoint(x: 11, y: 8),CGPoint(x: 5, y: 16),CGPoint(x: 11, y: 16)])
            p.move(to: CGPoint(x: 15, y: 13));p.addLines([CGPoint(x: 19, y: 13),CGPoint(x: 15, y: 18),CGPoint(x: 19, y: 18)])
        } else {
            p.move(to: CGPoint(x: 8, y: 3));p.addLines([CGPoint(x: 12, y: 11),CGPoint(x: 17, y: 6),CGPoint(x: 22, y: 21),CGPoint(x: 2, y: 21)]);p.closeSubpath()
        }
        return p.applying(CGAffineTransform(scaleX: rect.width / 24, y: rect.height / 24))
    }
}

struct ReferenceQuestionReport: View {
    @Bindable var model: LearningModel
    var body: some View {
        ZStack {
            Color.black.opacity(0.4).ignoresSafeArea().onTapGesture { model.closeQuestionReport() }
            VStack(alignment: .leading, spacing: 0) {
                if let reasons = model.lesson?.question.feedbackReportReasons {
                    VStack(alignment: .leading, spacing: 10) {
                        ForEach(Array(reasons.enumerated()), id: \.offset) { index, reason in
                            Toggle(reason, isOn: Binding(get: { model.selectedReportReasons.contains(index) }, set: { selected in
                                if selected { model.selectedReportReasons.insert(index) } else { model.selectedReportReasons.remove(index) }
                            })).toggleStyle(SourceReportCheckboxStyle()).font(ReferenceStyle.font(17, bold: true)).frame(height: 24.5, alignment: .leading)
                                .accessibilityIdentifier("report-reason-\(index)")
                        }
                    }
                } else {
                    Text("当前题目的报错选项尚不可用。").font(ReferenceStyle.font(17))
                }
                Spacer(minLength: 24)
                Button("提交") { model.error = "报错提交服务尚未接入。" }
                    .buttonStyle(SourceReportSubmitStyle()).frame(width: 64, height: 50).disabled(model.selectedReportReasons.isEmpty)
                    .accessibilityIdentifier("report-submit")
            }.padding(30).frame(width: 243, height: 327, alignment: .topLeading)
                .background(ReferenceStyle.background, in: RoundedRectangle(cornerRadius: 16))
                .accessibilityElement(children: .contain)
                .accessibilityIdentifier("question-report")
                .overlay(alignment: .topTrailing) {
                    Button { model.closeQuestionReport() } label: {
                        Image(systemName: "xmark").font(.system(size: 18, weight: .bold)).foregroundStyle(.gray)
                            .frame(width: 32, height: 32).background(.white, in: Circle()).overlay(Circle().stroke(ReferenceStyle.border, lineWidth: 2))
                    }.buttonStyle(.plain).offset(x: 16, y: -16).accessibilityLabel("关闭").accessibilityIdentifier("report-close")
                }
        }.onExitCommand { model.closeQuestionReport() }
    }
}

private struct SourceReportSubmitStyle: ButtonStyle {
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(ReferenceStyle.font(15, bold: true))
            .frame(maxWidth: .infinity).frame(height: 46)
            .foregroundStyle(enabled ? Color.white : Color(white: 175/255))
            .background(enabled ? ReferenceStyle.blue : Color(white: 229/255), in: RoundedRectangle(cornerRadius: 16))
            .shadow(color: enabled ? Color(red: 24/255, green: 153/255, blue: 214/255) : .clear, radius: 0, y: 4)
            .padding(.bottom, 4)
            .offset(y: configuration.isPressed ? 4 : 0)
    }
}

private struct SourceReportCheckboxStyle: ToggleStyle {
    func makeBody(configuration: Configuration) -> some View {
        Button { configuration.isOn.toggle() } label: {
            HStack(spacing: 10) {
                RoundedRectangle(cornerRadius: 5).stroke(configuration.isOn ? ReferenceStyle.blue : ReferenceStyle.border, lineWidth: 2)
                    .background(.white, in: RoundedRectangle(cornerRadius: 5)).frame(width: 20, height: 20)
                    .overlay {
                        if configuration.isOn {
                            Path { p in p.move(to: CGPoint(x: 5.5, y: 10));p.addLine(to: CGPoint(x: 8.5, y: 13));p.addLine(to: CGPoint(x: 14.5, y: 7)) }
                                .stroke(ReferenceStyle.blue, style: StrokeStyle(lineWidth: 2, lineCap: .round, lineJoin: .round))
                        }
                    }
                configuration.label
            }
        }.buttonStyle(.plain)
            .accessibilityRepresentation { Toggle(isOn: configuration.$isOn) { configuration.label } }
    }
}
