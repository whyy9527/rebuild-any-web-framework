import SwiftUI
import LearningCore

/// Original correct-feedback positions, independent of the question's intrinsic height.
struct ReferenceObservedCorrectFooter: View {
    @Bindable var model: LearningModel
    let lesson: Lesson
    var body: some View {
        GeometryReader { g in
            let left = (g.size.width - 920) / 2
            let ink = Color(red: 88/255, green: 167/255, blue: 0)
            ZStack(alignment: .topLeading) {
                Color(red: 215/255, green: 1, blue: 184/255)
                ReferenceStyle.image("en-result-review-check").resizable().frame(width: 41, height: 31)
                    .frame(width: 80, height: 80).background(.white, in: Circle()).offset(x: left, y: 32.5)
                Text(lesson.question.correctFeedback ?? "好棒！").font(ReferenceStyle.font(24, bold: true)).foregroundStyle(ink)
                    .frame(width: 600, height: 30, alignment: .leading).offset(x: left + 96, y: 32.5)
                    .accessibilityIdentifier("feedback").accessibilityValue("correct")
                ReferenceFeedbackActions(model: model, color: ink).offset(x: left + 96, y: 85.375)
                ReferencePracticeControl(label: "继续", identifier: "continue", enabled: true, action: { model.advance() }, face: AnyView(
                    Text("继续").font(ReferenceStyle.font(17, bold: true)).foregroundStyle(.white)
                        .frame(width: 150, height: 46).background(ReferenceStyle.green, in: RoundedRectangle(cornerRadius: 16))
                        .shadow(color: Color(red: 70/255, green: 163/255, blue: 2/255), radius: 0, y: 4)
                        .frame(height: 50, alignment: .top)))
                    .frame(width: 150, height: 50).offset(x: g.size.width - left - 150, y: 45)
            }
        }
    }
}
