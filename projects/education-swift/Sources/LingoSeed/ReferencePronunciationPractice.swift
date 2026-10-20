import SwiftUI
import LearningCore

struct ReferencePronunciationPractice: View {
    @Bindable var model: LearningModel
    let lesson: Lesson
    var otherQuestion: AnyView? = nil
    var otherFooter: AnyView? = nil
    private var question: Question { lesson.question }
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                HStack(spacing: 24) {
                    Button {
                        if model.pronunciationExitNeedsConfirmation { model.confirmingExit = true }
                        else { model.discardAttempt() }
                    } label: { ReferenceStyle.image("practice-close-source").resizable().frame(width: 18, height: 18) }
                        .buttonStyle(.plain).accessibilityIdentifier("exit")
                    ProgressView(value: lesson.complete ? 1 : lesson.reviewing ? 0.9 : Double(lesson.position) / Double(lesson.definition.questions.count)).tint(ReferenceStyle.green).accessibilityIdentifier("lesson-progress")
                    if model.isObservedCourse {
                        HStack(spacing:8) {ReferenceStyle.image("en-home-088202fb75fb12b0eec8").resizable().frame(width:32,height:32);Text(String(lesson.hearts)).font(ReferenceStyle.font(17,bold:true)).foregroundStyle(Color(red:1,green:75/255,blue:75/255))}.accessibilityIdentifier("course-hearts").accessibilityValue(String(lesson.hearts))
                    } else if model.isPlacement {
                        HStack(spacing: 5) {
                            ForEach(0..<(model.isUnitPlacement ? 5 : 3), id: \.self) { i in
                                ReferenceStyle.image(i < lesson.hearts ? "en-placement-heart-filled" : "en-placement-heart").resizable().frame(width: 25, height: 22)
                                    .accessibilityIdentifier("placement-heart-\(i)")
                            }
                        }.accessibilityValue(String(lesson.hearts))
                    }
                }.frame(maxWidth: 1000).padding(.top, 50)
                if let interlude = lesson.interlude {
                    VStack(spacing: 28) {
                        ReferenceStyle.image("duo-observed-frame").resizable().scaledToFit().frame(width: 180, height: 190)
                        Text(interlude.text).font(ReferenceStyle.font(28, bold: true)).multilineTextAlignment(.center).accessibilityIdentifier("lesson-interlude").accessibilityValue(interlude.id)
                    }.frame(width: 600).padding(.top, 80)
                } else if let speech = lesson.deferredSpeech {
                    speechPanel(speech).padding(.top, 51)
                } else if lesson.complete {
                    VStack(spacing: 24) {
                        Text(model.settlement?.current?.title ?? "").font(ReferenceStyle.font(32, bold: true)).accessibilityIdentifier("practice-settlement-title")
                        if let body = model.settlement?.current?.body { Text(body).font(ReferenceStyle.font(19)) }
                    }.padding(.top, 80)
                } else if let otherQuestion, question.kind != .matching {
                    // Ordinary assist source: heading block117 +40 +175 character row => first radio332.
                    otherQuestion
                        .padding(.top, model.isObservedCourse ? (question.sourceType == "assist" ? 34.5 : question.sourceType == "translate" ? 25.5 : 47) : model.isPlacement ? 48.5 : 51)
                        // Source viewport reserves header82 and footer140. Intrinsic
                        // question height must not push the actual controls below it.
                        .frame(width: 600, height: max(0, geometry.size.height - 222), alignment: .top)
                } else {
                    VStack(alignment: .leading, spacing: 0) {
                        Text(question.prompt).font(ReferenceStyle.font(32, bold: true)).frame(height: 40).accessibilityIdentifier("question-prompt").accessibilityValue(question.id)
                        if question.kind == .matching {
                            matching.padding(.top, question.sourceType == "match" ? 67.390625 : 86)
                        } else if question.sourceType == "sameDifferent" {
                            VStack(alignment: .leading, spacing: 0) {
                                splitSpeaker.frame(maxWidth: .infinity)
                                Text("你听到的词是？").font(ReferenceStyle.font(19, bold: true)).frame(height: 27).padding(.top, 40.25).padding(.bottom, 8)
                                ForEach(Array(question.options.enumerated()), id: \.element.id) { index, option in radio(option, index: index).padding(.bottom, 8) }
                            }.padding(.top, 27.75)
                        } else {
                            VStack(spacing: 24) {
                                speaker(0, size: 140)
                                HStack(spacing: 8) { ForEach(Array(question.options.enumerated()), id: \.element.id) { index, option in radio(option, index: index) } }
                            }.padding(.top, 105)
                        }
                    }.frame(width: 600).padding(.top, question.sourceType == "match" ? 39 : 51)
                }
                Spacer(minLength: 0)
                if let otherFooter, lesson.deferredSpeech == nil { otherFooter.frame(height: 140) }
                else { footer.frame(height: 140) }
            }.frame(maxWidth: .infinity, maxHeight: .infinity)
                .foregroundStyle(ReferenceStyle.ink).background(ReferenceStyle.background)
                .overlay { if model.confirmingExit { exitConfirmation } }
        }
    }

    private var exitConfirmation: some View {
        ZStack {
            Color.black.opacity(0.4)
            ZStack(alignment: .topLeading) {
                ReferenceStyle.image("practice-quit-duo-source").resizable().frame(width: 120, height: 120)
                    .accessibilityLabel("Duo").accessibilityIdentifier("practice-quit-duo")
                    .offset(x: 132, y: 32)
                Text("等等，先别走！现在离开的话，你的进度就没了！")
                    .font(ReferenceStyle.font(24, bold: true)).lineSpacing(4).multilineTextAlignment(.center)
                    .frame(width: 336, height: 64).accessibilityIdentifier("practice-quit-title").offset(x: 24, y: 168.5)
                ReferencePracticeControl(label: "继续努力", identifier: "practice-quit-cancel", enabled: true,
                    action: { model.confirmingExit = false }, face: AnyView(Text("继续努力").font(ReferenceStyle.font(15, bold: true))
                        .foregroundStyle(.white).frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(RoundedRectangle(cornerRadius: 16).fill(ReferenceStyle.blue)
                            .shadow(color: Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: 4)).padding(.bottom, 4)))
                    .frame(width: 336, height: 50).offset(x: 24, y: 264.5)
                ReferencePracticeControl(label: "退出", identifier: "practice-quit-confirm", enabled: true,
                    action: { model.discardAttempt() }, face: AnyView(Text("退出").font(ReferenceStyle.font(15, bold: true))
                        .foregroundStyle(Color(red: 1, green: 75/255, blue: 75/255)).frame(maxWidth: .infinity, maxHeight: .infinity)))
                    .frame(width: 336, height: 32).offset(x: 24, y: 330.5)
            }.frame(width: 384, height: 386.5, alignment: .topLeading).background(.white, in: RoundedRectangle(cornerRadius: 16))
        }
    }

    private func speechPanel(_ speech: DeferredSpeech) -> some View {
        ZStack(alignment: .topLeading) {
            if let resource=speech.characterResource {
                ReferenceCharacter(resource:resource,feedback:nil).frame(width:118,height:175).offset(x:0,y:105)
            }
            Text(speech.title).font(ReferenceStyle.font(32, bold: true)).frame(width: 600, height: 40, alignment: .leading)
                .accessibilityIdentifier("speech-title").accessibilityValue(speech.id)
            HStack(spacing: 8) {
                ReferencePracticeControl(label: "", identifier: "speech-play", enabled: true,
                    action: { model.playQuestion() }, face: AnyView(ReferenceStyle.image("practice-speaker-source").resizable().frame(width: 29, height: 22)))
                    .frame(width: 29, height: 22)
                Text(speech.phrase).font(ReferenceStyle.font(20))
            }.padding(.horizontal, 15).frame(height: 54)
                .background(RoundedRectangle(cornerRadius: 12).fill(ReferenceStyle.background).overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(ReferenceStyle.border, lineWidth: 2)))
                .offset(x: 135, y: 185)
            ReferencePracticeControl(label: "点击并开始录音", identifier: "speech-record", enabled: !lesson.speechDeclined && model.speechCapture.state != .recognizing,
                action: { model.startSpeech() }, face: AnyView(HStack(spacing: 12) {
                    ReferenceStyle.image("practice-microphone-source").resizable().frame(width: 18.75, height: 25)
                    Text("点击并开始录音").font(ReferenceStyle.font(15, bold: true))
                }.foregroundStyle(ReferenceStyle.blue).frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(RoundedRectangle(cornerRadius: 16).fill(ReferenceStyle.background).shadow(color: ReferenceStyle.border, radius: 0, y: 2)
                        .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2)))))
                .frame(width: 600, height: 70).offset(y: 295.5)
        }.frame(width: 600, height: 365.5, alignment: .topLeading)
    }

    private var matching: some View {
        let right = question.rightOrder?.compactMap { id in question.pairs.first { $0.id == id } } ?? question.pairs
        return HStack(spacing: 30) {
            VStack(spacing: 10) {
                ForEach(Array(question.pairs.enumerated()), id: \.element.id) { index, pair in
                    pairButton(pair, number: index + 1, left: true)
                }
            }
            VStack(spacing: 10) {
                ForEach(Array(right.enumerated()), id: \.element.id) { index, pair in
                    pairButton(pair, number: question.sourceType == "match" ? (index + 6) % 10 : index + 5, left: false)
                }
            }
        }.frame(maxWidth: .infinity)
    }
    private func pairButton(_ pair: WordPair, number: Int, left: Bool) -> some View {
        let matched = lesson.matchedPairs.contains(pair.id)
        let selected = (left ? lesson.selectedLeft : lesson.selectedRight) == pair.id
        let edge = selected ? ReferenceStyle.blue : ReferenceStyle.border
        let ink = matched ? ReferenceStyle.disclosureInk : selected ? ReferenceStyle.blue : ReferenceStyle.ink
        let face = HStack(spacing: left ? 14 : 0) {
            Text(String(number)).font(ReferenceStyle.font(14, bold: true)).foregroundStyle(matched ? ReferenceStyle.border : selected ? ReferenceStyle.blue : ReferenceStyle.disclosureInk)
                .frame(width: 28, height: 28).overlay(RoundedRectangle(cornerRadius: 6).strokeBorder(edge, lineWidth: 2))
            if left && question.sourceType == "match" {
                Text(pair.left).font(ReferenceStyle.font(19)).foregroundStyle(ink).frame(maxWidth: .infinity)
            } else if left {
                ReferenceStyle.image("en-match-speaker-source-frame").renderingMode(.template).resizable().frame(width: 24, height: 19).foregroundStyle(matched ? ReferenceStyle.border : ReferenceStyle.blue)
                ReferenceStyle.image("en-match-waveform-source-frame").renderingMode(.template).resizable().frame(width: 81, height: 24).foregroundStyle(matched ? ReferenceStyle.border : ReferenceStyle.blue)
                Spacer(minLength: 0)
            } else {
                Text(pair.right).font(ReferenceStyle.font(19)).foregroundStyle(ink).frame(maxWidth: .infinity)
            }
        }.padding(.horizontal, 18).frame(width: 255, height: question.sourceType == "match" ? 49.84375 : 56)
            .background(RoundedRectangle(cornerRadius: 12).fill(selected ? Color(red: 221/255, green: 244/255, blue: 1) : .white).shadow(color: edge, radius: 0, y: 2))
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(edge, lineWidth: 2)).frame(height: question.sourceType == "match" ? 51.84375 : 58, alignment: .top)
        return ReferencePracticeControl(label: left ? (question.sourceType == "match" ? "\(number) \(pair.left)" : String(number)) : "\(number) \(pair.right)", identifier: (left ? "pair-left-" : "pair-right-") + pair.id,
            enabled: lesson.feedback == nil && !matched, action: { model.match(pair.id, left: left) }, face: AnyView(face))
            .frame(width: 255, height: question.sourceType == "match" ? 51.84375 : 58)
    }

    private var splitSpeaker: some View {
        VStack(spacing: 0) {
            ForEach(0..<2) { part in
                let labels = question.practiceAudioLabels ?? []
                let label = lesson.feedback != nil && labels.indices.contains(part) ? labels[part] : ""
                ReferencePracticeAudioButton(label: label, identifier: "practice-play-" + String(part), enabled: lesson.feedback == nil,
                    action: { model.playQuestion(practicePart: part) })
                    .frame(width: 165, height: part == 0 ? 85.5 : 89.5)
            }
        }.frame(width: 165, height: 175)
            .background {
                RoundedRectangle(cornerRadius: 41.25).fill(.white)
                    .shadow(color: ReferenceStyle.border, radius: 0, y: 2)
                    .overlay(RoundedRectangle(cornerRadius: 41.25).strokeBorder(ReferenceStyle.border, lineWidth: 2))
            }
            .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2).offset(y: 85.5).allowsHitTesting(false) }
    }

    private func speaker(_ part: Int, size: Double) -> some View {
        Button { model.playQuestion(practicePart: part) } label: {
            ReferenceStyle.image("practice-speaker-source").resizable().scaledToFit().frame(width: size * 0.67, height: size * 0.52)
                .frame(width: size, height: size).background(alignment: .top) {
                    RoundedRectangle(cornerRadius: 32).fill(ReferenceStyle.blue).frame(height: size - 4)
                        .shadow(color: Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: 4)
                }
        }.buttonStyle(.plain).frame(maxWidth: .infinity).accessibilityIdentifier("practice-play-" + String(part))
    }
    private func radio(_ option: Choice, index: Int) -> some View {
        ReferenceAudioRadio(label: "\(index + 1) \(option.text)", identifier: "option-" + option.id, waveform: nil,
            correct: lesson.feedback == true, selected: lesson.selected == option.id, enabled: lesson.feedback == nil,
            action: { model.choose(option.id) }, textChoice: true).frame(width: question.sourceType == "sameDifferent" ? 600 : 296, height: 60)
    }
    private var footer: some View {
        HStack {
            if let speech = lesson.deferredSpeech {
                if lesson.speechDeclined {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(speech.closedTitle).font(ReferenceStyle.font(22, bold: true)).accessibilityIdentifier("speech-closed")
                        if !speech.closedBody.isEmpty { Text(speech.closedBody).font(ReferenceStyle.font(18)) }
                    }; Spacer()
                    Button("继续") { model.advance() }.buttonStyle(ReferenceCheckButton()).accessibilityIdentifier("speech-continue")
                } else {
                    ReferencePracticeControl(label: "现在不做口语题", identifier: "speech-decline", enabled: true, action: { model.declineSpeech() },
                        face: AnyView(Text("现在不做口语题").font(ReferenceStyle.font(17, bold: true)).foregroundStyle(Color(red: 175/255, green: 175/255, blue: 175/255))
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                            .background(RoundedRectangle(cornerRadius: 16).fill(ReferenceStyle.background).shadow(color: ReferenceStyle.border, radius: 0, y: 2)
                                .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2)))))
                        .frame(width: 160.6015625, height: 50).offset(y: 2)
                    Spacer(); Button("检查") {}.buttonStyle(ReferenceCheckButton()).disabled(true)
                }
            } else if lesson.complete {
                Spacer(); Button(model.settlement?.current?.continueLabel ?? "继续") { model.advanceSettlement() }.buttonStyle(ReferenceCheckButton()).accessibilityIdentifier("settlement-continue")
            } else if let feedback = lesson.feedback {
                VStack(alignment: .leading, spacing: 8) {
                    Text(feedback ? (question.correctFeedback ?? "你练得一副好听力，厉害呀！") : "还不太准确，再多听几次吧！").font(ReferenceStyle.font(22, bold: true)).accessibilityIdentifier("feedback")
                    if question.sourceType == "sameDifferent" { Text(question.explanation).font(ReferenceStyle.font(18)) }
                    ReferenceFeedbackActions(model: model, color: feedback ? ReferenceStyle.green : .red)
                }
                Spacer(); Button("继续") { model.advance() }.buttonStyle(ReferenceCheckButton()).accessibilityIdentifier("continue")
            } else {
                Button("跳过") { model.skip() }.buttonStyle(ReferenceSkipButton()).accessibilityIdentifier("skip")
                Spacer(); Button("检查") { model.submit() }.buttonStyle(ReferenceCheckButton()).disabled(!lesson.canSubmit).accessibilityIdentifier("check")
            }
        }.padding(.horizontal, 140).frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(lesson.feedback == nil && !lesson.speechDeclined ? ReferenceStyle.background : lesson.feedback == false ? Color(red: 1, green: 223/255, blue: 224/255) : Color(red: 215/255, green: 1, blue: 184/255))
            .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
    }
}

// The source's two halves have distinct hit rectangles, disabled states and labels.
// NSButton supplies those semantics without SwiftUI's decorative focus inset.
private struct ReferencePracticeAudioButton: View {
    let label: String
    let identifier: String
    let enabled: Bool
    let action: () -> Void
    var body: some View {
        ReferencePracticeControl(label: label, identifier: identifier, enabled: enabled, action: action, face: AnyView(HStack(spacing: 8) {
            ReferenceStyle.image("practice-speaker-source").renderingMode(.template).resizable().frame(width: 24, height: 19).foregroundStyle(ReferenceStyle.blue)
            Text(label.isEmpty ? " " : label).font(ReferenceStyle.font(19, bold: true)).foregroundStyle(ReferenceStyle.ink)
                .frame(width: 42, height: 27).overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
        }.offset(y: -2).frame(maxWidth: .infinity, maxHeight: .infinity)))
    }
}

struct ReferencePracticeControl: NSViewRepresentable {
    let label: String
    let identifier: String
    let enabled: Bool
    let action: () -> Void
    let face: AnyView
    var role: NSAccessibility.Role = .button
    var fixedFaceSize = false
    final class Coordinator: NSObject {
        var action: () -> Void
        init(_ action: @escaping () -> Void) { self.action = action }
        @objc func play(_ sender: NSButton) { action() }
    }
    final class Button: NSButton {
        let face = ReferenceAudioRadio.PassiveHost(rootView: AnyView(EmptyView()))
        var reportedRole: NSAccessibility.Role = .button
        override func accessibilityRole() -> NSAccessibility.Role? { reportedRole }
        override var intrinsicContentSize: NSSize { NSSize(width: NSView.noIntrinsicMetric, height: NSView.noIntrinsicMetric) }
        override func draw(_ dirtyRect: NSRect) {}
        override func keyDown(with event: NSEvent) {
            // Source HTML controls activate on Return; NSButton defaults to Space.
            if isEnabled && [36,76].contains(Int(event.keyCode)) {performClick(nil)}
            else {super.keyDown(with:event)}
        }
        override func accessibilityFrame() -> NSRect {
            guard let window else { return super.accessibilityFrame() }
            return window.convertToScreen(convert(bounds, to: nil))
        }
    }
    final class Container: NSView {
        let button = Button(frame: .zero)
    }
    func makeCoordinator() -> Coordinator { Coordinator(action) }
    func makeNSView(context: Context) -> Container {
        let container = Container(frame: .zero)
        let button = container.button
        container.addSubview(button)
        button.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            button.leadingAnchor.constraint(equalTo: container.leadingAnchor), button.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            button.topAnchor.constraint(equalTo: container.topAnchor), button.bottomAnchor.constraint(equalTo: container.bottomAnchor)
        ])
        button.reportedRole = role
        button.setAccessibilityElement(true)
        container.setAccessibilityElement(false)
        container.setAccessibilityChildren([button])
        button.isBordered = false
        button.setButtonType(.momentaryPushIn)
        button.target = context.coordinator
        button.action = #selector(Coordinator.play(_:))
        if fixedFaceSize { button.face.sizingOptions = [] }
        button.addSubview(button.face)
        button.face.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            button.face.leadingAnchor.constraint(equalTo: button.leadingAnchor), button.face.trailingAnchor.constraint(equalTo: button.trailingAnchor),
            button.face.topAnchor.constraint(equalTo: button.topAnchor), button.face.bottomAnchor.constraint(equalTo: button.bottomAnchor)
        ])
        button.setAccessibilityChildren([])
        return container
    }
    func updateNSView(_ container: Container, context: Context) {
        let button = container.button
        context.coordinator.action = action
        button.isEnabled = enabled
        button.title = label
        button.setAccessibilityLabel(label)
        button.setAccessibilityIdentifier(identifier)
        button.face.rootView = AnyView(face.accessibilityHidden(true))
    }
}
