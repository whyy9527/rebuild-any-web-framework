import SwiftUI
import LearningCore

struct LearningView: View {
    @State private var showingResultReview = false
    @Bindable var model: LearningModel
    private var chinese: Bool { model.course.interfaceLanguage == "zh" }
    private func copy(_ english: String, _ zh: String) -> String { chinese ? zh : english }
    private let ink = Color(white: 0.28)
    private let accent = Color(red: 0.345, green: 0.8, blue: 0)
    private let columns = [GridItem(.adaptive(minimum: 110), spacing: 12)]
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                if let lesson = model.lesson {
                    if model.isPronunciationPractice { ReferencePronunciationPractice(model: model, lesson: lesson) }
                    else if model.isReferenceSession {
                        if lesson.complete, let page = model.settlement?.current {
                            if model.isObservedCourse && page.kind == "result", page.artResource != nil {
                                ReferenceObservedCourseResult(page:page,mistakes:lesson.mistakesMade,advance:model.advanceSettlement,review:{showingResultReview=true})
                            } else if model.isObservedCourse && page.kind == "achievement", page.artResource != nil {
                                ReferenceObservedAchievement(page:page,advance:model.advanceSettlement,review:{showingResultReview=true})
                            } else if model.isObservedCourse && page.kind == "profile" {
                                ReferenceObservedProfile(page: page, advance: model.advanceSettlement)
                            } else if model.isUnitPlacement && page.kind != "profile" {
                                ReferenceUnitPlacementPage(page:page,advance:model.advanceSettlement,review:{showingResultReview=true})
                            } else {
                            ReferenceSettlement(page: page, mistakesMade: lesson.mistakesMade, advance: model.advanceSettlement, retry: model.beginGeneralPractice,
                                                review: lesson.resultReviewEntries.isEmpty ? nil : { showingResultReview = true })
                            }
                        } else {
                            ReferencePronunciationPractice(model: model, lesson: lesson, otherQuestion: AnyView(question(lesson)), otherFooter: AnyView(generalPracticeFooter(lesson)))
                        }
                    }
                    else { lessonPage(lesson) }
                } else if model.unitPlacementEntry {
                    ReferenceUnitPlacementIntro(later:{model.unitPlacementEntry=false},start:model.beginUnitPlacement)
                } else if model.sectionPlacementEntry,let stage=model.sectionPlacementStage {
                    ReferenceSectionPlacementEntry(stage:stage,later:{model.sectionPlacementEntry=false;model.destination="Sections"},start:model.beginSectionPlacement)
                } else if model.destination == "Guest achievements error" {
                    ReferenceGuestAchievementsError(home:{model.destination="Learn"})
                } else if ["Learn", "Sections", "Settings", "Guidebook", "Pronunciation", "Shop", "Forgot password", "Leaderboards", "Guest profile", "Guest avatar"].contains(model.destination)
                    || (model.destination == "Quests" && model.course.interfaceLanguage == "zh") {
                    ReferenceHome(model: model)
                } else {
                    HStack(spacing: 0) {
                        sidebar(compact: geometry.size.width < 1180)
                        Divider()
                        ScrollView {
                            destinationPage
                        }.frame(maxWidth: .infinity)
                        if geometry.size.width >= 1120 {
                            ScrollView { dashboard }.frame(width: 350).padding(.trailing, 24)
                        }
                    }
                }
                if let error = model.error {
                    HStack { Text(error).foregroundStyle(.red); Button("Retry saving") { model.save() } }.padding(8)
                }
            }
        }
        .frame(minWidth: 780, minHeight: 660)
        .foregroundStyle(ink).background(ReferenceStyle.background)
        .overlay { if model.reportingQuestion { ReferenceQuestionReport(model: model) } }
        .overlay {
            if showingResultReview, let lesson = model.lesson {
                ReferenceResultReview(entries: lesson.resultReviewEntries,
                    play: { model.audio.speak("", language: "en", resource: $0) }, close: { showingResultReview = false })
            }
        }
        .overlay { if model.speechCapture.state == .denied { ReferenceSpeechPermissionOverlay(speech: model.speechCapture) } }
        .preferredColorScheme(model.preferences.darkMode == "On" ? .dark : model.preferences.darkMode == "Off" ? .light : nil)

    }
    @ViewBuilder private func generalPracticeFooter(_ lesson: Lesson) -> some View {
        if lesson.interlude != nil {
            HStack {
                Spacer()
                Button("继续") { model.advance() }.buttonStyle(ReferenceCheckButton()).accessibilityIdentifier("interlude-continue")
            }.padding(.horizontal, 140).frame(maxWidth: .infinity, maxHeight: .infinity)
                .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
        } else if lesson.listeningDeclined, let decline = lesson.question.listeningDecline {
            GeometryReader { geometry in
                let left = (geometry.size.width - 920) / 2
                let brown = Color(red: 205/255, green: 121/255, blue: 0)
                ZStack(alignment: .topLeading) {
                    Color(red: 1, green: 0.961, blue: 0.827)
                    if let image = decline.imageResource {
                        ReferenceStyle.image(image).resizable().frame(width: 41, height: 31)
                            .frame(width: 80, height: 80).background(.white, in: Circle()).offset(x: left, y: 30)
                    }
                    Text(decline.title).font(ReferenceStyle.font(24, bold: true)).foregroundStyle(brown)
                        .frame(width: 320, height: 30, alignment: .leading).offset(x: left + 96, y: 23.25)
                        .accessibilityIdentifier("listening-declined")
                    Text(decline.body).font(ReferenceStyle.font(17)).foregroundStyle(brown)
                        .offset(x: left + 96, y: 55)
                    ReferenceFeedbackActions(model: model, color: brown).offset(x: left + 96, y: 96)
                    ReferencePracticeControl(label: "继续", identifier: "listening-continue", enabled: true,
                        action: { model.advance() }, face: AnyView(Text("继续").font(ReferenceStyle.font(17, bold: true)).foregroundStyle(.white)
                            .frame(width: 150, height: 46).background(RoundedRectangle(cornerRadius: 16).fill(Color(red: 1, green: 0.784, blue: 0)))
                            .shadow(color: Color(red: 229/255, green: 163/255, blue: 0), radius: 0, y: 4)
                            .frame(height: 50, alignment: .top)))
                        .frame(width: 150, height: 50).offset(x: geometry.size.width - left - 150, y: 45)
                }
            }
        } else if model.isObservedCourse && lesson.feedback == true {
            ReferenceObservedCorrectFooter(model: model, lesson: lesson)
        } else { answerBar(lesson) }
    }
    private func sidebar(compact: Bool) -> some View {
        VStack(alignment: .leading, spacing: 15) {
            Text(compact ? "ls" : "lingoseed").font(.system(size: 34, weight: .heavy)).foregroundStyle(accent).padding(.bottom, 25)
            ForEach(["Learn", "Leaderboards", "Quests", "Shop", "Profile", "More"], id: \.self) { item in
                Button { model.destination = item } label: {
                    HStack(spacing: 12) {
                        Image(systemName: icon(item)).font(.system(size: 25, weight: .bold)).foregroundStyle(item == "Learn" ? accent : .orange).frame(width: 34)
                        if !compact { Text(item.uppercased()).font(.system(size: 13, weight: .bold)).tracking(0.2).fixedSize(horizontal: true, vertical: false) }
                        Spacer(minLength: 0)
                    }.padding(15).background(model.destination == item ? Color.cyan.opacity(0.12) : .clear, in: RoundedRectangle(cornerRadius: 13))
                        .overlay(RoundedRectangle(cornerRadius: 13).stroke(model.destination == item ? Color.cyan.opacity(0.45) : .clear, lineWidth: 2))
                }.buttonStyle(.plain).accessibilityLabel(item).accessibilityIdentifier("nav-" + item.lowercased())
            }
            Spacer()
            Button { model.toggleMute() } label: { Label(model.muted ? "Sound off" : "Sound on", systemImage: model.muted ? "speaker.slash.fill" : "speaker.wave.2.fill") }
                .buttonStyle(.plain).accessibilityLabel(model.muted ? "Sound off" : "Sound on").accessibilityIdentifier("sound-toggle").accessibilityValue(model.muted ? "muted" : "on").padding(15)
        }.padding(24).frame(width: compact ? 92 : 252)
    }
    private func icon(_ name: String) -> String {
        switch name { case "Learn": "house.fill"; case "Leaderboards": "shield.fill"; case "Quests": "shippingbox.fill"; case "Shop": "storefront.fill"; case "Profile": "person.crop.circle.fill"; default: "ellipsis.circle.fill" }
    }
    private var dashboard: some View {
        VStack(alignment: .leading, spacing: 22) {
            HStack { Label("EN", systemImage: "globe"); Spacer(); Label("\(model.progress.completedCount(model.course) * 10)", systemImage: "bolt.fill").foregroundStyle(.orange); Spacer(); Label("\(model.progress.hearts)", systemImage: "heart.fill").foregroundStyle(.red) }.font(.headline).padding(.vertical, 20)
            card("Your learning milestones") {
                Label("\(model.progress.completedCount(model.course)) lessons complete", systemImage: "shield.lefthalf.filled").font(.title3.bold())
                Text("Learn at your own pace. Every completed lesson is saved on this device.").foregroundStyle(.secondary)
            }
            card("Course goal") {
                Label("Complete a lesson", systemImage: "bolt.fill").font(.headline)
                ProgressView(value: Double(min(model.progress.completedCount(model.course), 1)), total: 1).tint(.yellow)
                Button("VIEW QUESTS") { model.destination = "Quests" }.buttonStyle(.plain).foregroundStyle(.cyan).accessibilityIdentifier("view-quests")
            }
            card("Your progress stays with you") {
                Text("Your local profile works offline. Online accounts and competitive rankings are not connected.").foregroundStyle(.secondary)
                Button("VIEW PROFILE") { model.destination = "Profile" }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("view-profile")
            }
        }.padding(.top, 20)
    }
    private func card<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 23) { Text(title).font(.title3.bold()); content() }.padding(23).frame(maxWidth: .infinity, alignment: .leading)
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.gray.opacity(0.22), lineWidth: 2))
    }
    private var destinationPage: some View {
        VStack(alignment: .leading, spacing: 26) {
            HStack(spacing: 16) {
                Image(systemName: icon(model.destination)).font(.system(size: 36, weight: .bold)).foregroundStyle(model.destination == "Profile" ? .purple : .orange)
                Text(model.destination).font(.largeTitle.bold()).accessibilityIdentifier("destination-title").accessibilityValue(model.destination)
            }
            switch model.destination {
            case "Quests":
                card("Your course goal") {
                    Label("Complete a lesson", systemImage: "bolt.fill").font(.title3.bold()).foregroundStyle(.orange)
                    Text("\(min(model.progress.completedCount(model.course), 1)) / 1 complete in this course")
                    ProgressView(value: Double(min(model.progress.completedCount(model.course), 1)), total: 1).tint(.yellow)
                    Text("Every lesson is a step forward.").foregroundStyle(.secondary)
                    practiceButton
                }
            case "Profile":
                HStack(spacing: 24) { SeedMascot(); VStack(alignment: .leading, spacing: 8) { Text("Local learner").font(.title2.bold()); Text("Everyday practice, at your pace.").foregroundStyle(.secondary) } }
                card("Your learning") {
                    Label("\(model.progress.completedCount(model.course)) completed lessons", systemImage: "checkmark.seal.fill").font(.title3.bold()).foregroundStyle(accent)
                    Label("\(model.progress.hearts) hearts", systemImage: "heart.fill").foregroundStyle(.red)
                    Text("Progress is saved on this device. Account synchronization is not connected.").foregroundStyle(.secondary)
                }
            case "Leaderboards":
                card("Learn. Practice. Make progress.") {
                    HStack { Image(systemName: "shield.lefthalf.filled").font(.system(size: 56)).foregroundStyle(.cyan); Text("Keep learning at your own pace.").font(.title2.bold()) }
                    Text("Online competitions are not connected in this local education base.").foregroundStyle(.secondary)
                    practiceButton
                }
            case "Shop":
                card("Hearts") {
                    Label("\(model.progress.hearts) hearts", systemImage: "heart.fill").font(.title2.bold()).foregroundStyle(.red)
                    Text("Everything here is free to practice.")
                    Text("Purchases and subscriptions are not connected.").foregroundStyle(.secondary)
                }
                card("Practice is always open") { Text("Return to your course whenever you are ready."); practiceButton }
            default:
                card("Learning sounds") {
                    Label(model.muted ? "Sound off" : "Sound on", systemImage: model.muted ? "speaker.slash.fill" : "speaker.wave.2.fill").font(.title2.bold()).foregroundStyle(.cyan)
                    Text("Hear words and feedback as you learn. Your preference is saved on this device.").foregroundStyle(.secondary)
                    Button(model.muted ? "Turn sound on" : "Turn sound off") { model.toggleMute() }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("settings-sound")
                }
                Text("LingoSeed · original lessons and sounds, inspired by the reference learning flow.").foregroundStyle(.secondary)
            }
            Button("Back to learning") { model.destination = "Learn" }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("return-learn")
        }.padding(30).frame(maxWidth: 680, alignment: .leading)
    }
    private var practiceButton: some View {
        Button("START A LESSON") {
            let next = model.course.lessons.indices.first { !model.progress.isCompleted(model.course, index: $0) && model.progress.isUnlocked(model.course, index: $0) } ?? 0
            model.begin(next)
        }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("destination-practice")
    }
    @ViewBuilder private func lessonPage(_ lesson: Lesson) -> some View {
        if lesson.complete, let page = model.settlement?.current {
            ReferenceSettlement(page: page, mistakesMade: lesson.mistakesMade, advance: model.advanceSettlement,
                                review: lesson.resultReviewEntries.isEmpty ? nil : { showingResultReview = true })
        } else if model.entryPending, let entry = lesson.definition.entry {
            VStack(spacing: 32) {
                Spacer()
                Text(entry.title).font(ReferenceStyle.font(28, bold: true)).multilineTextAlignment(.center).frame(maxWidth: 560).accessibilityIdentifier("lesson-entry").accessibilityValue(entry.id)
                Spacer()
                HStack {
                    Button(entry.declineLabel) { model.discardAttempt() }.buttonStyle(ReferenceButton(color: .gray)).accessibilityIdentifier("lesson-entry-decline")
                    Spacer()
                    Button(entry.startLabel) { model.acceptEntry() }.buttonStyle(ReferenceButton()).accessibilityIdentifier("lesson-entry-start")
                }.padding(40)
            }
        } else {
        VStack(spacing: 0) {
            HStack(spacing: 24) {
                if !lesson.complete { Button { model.confirmingExit = true } label: { Image(systemName: "xmark").font(.title2.bold()).foregroundStyle(.gray) }.buttonStyle(.plain).accessibilityIdentifier("quit") }
                ProgressView(value: lesson.complete ? 1 : lesson.reviewing ? 0.9 : Double(lesson.position) / Double(lesson.definition.questions.count)).tint(accent).scaleEffect(y: 2).accessibilityIdentifier("lesson-progress").accessibilityValue(lesson.complete ? "complete" : lesson.reviewing ? "review" : String(lesson.position))
                    .overlay(alignment: .top) {
                        if chinese && lesson.feedback == true && lesson.correctStreak >= 2 {
                            Text("连对 \(lesson.correctStreak) 题").font(ReferenceStyle.font(17, bold: true)).foregroundStyle(.orange).offset(y: -24)
                                .accessibilityIdentifier("correct-streak")
                        }
                    }
                Text("♥ \(lesson.hearts)").font(.title2.bold()).foregroundStyle(.red).accessibilityIdentifier("hearts").accessibilityValue(String(lesson.hearts))
                Button { model.toggleMute() } label: { Image(systemName: model.muted ? "speaker.slash.fill" : "speaker.wave.2.fill") }.buttonStyle(.plain).accessibilityLabel(model.muted ? "Sound off" : "Sound on").accessibilityIdentifier("sound-toggle").accessibilityValue(model.muted ? "muted" : "on")
            }.padding(.horizontal, 60).padding(.vertical, 35)
            Spacer(minLength: 0)
            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    if lesson.complete { completion }
                    else if let interlude = lesson.interlude {
                        VStack(spacing: 28) {
                            ReferenceStyle.image("duo-observed-frame").resizable().scaledToFit().frame(width: 180, height: 190)
                            Text(interlude.text).font(ReferenceStyle.font(28, bold: true)).multilineTextAlignment(.center).accessibilityIdentifier("lesson-interlude").accessibilityValue(interlude.id)
                        }.frame(maxWidth: .infinity)
                    }
                    else if let speech = lesson.deferredSpeech {
                        VStack(alignment: .leading, spacing: 32) {
                            Text(speech.title).font(ReferenceStyle.font(32, bold: true)).frame(height: 40).accessibilityIdentifier("speech-title").accessibilityValue(speech.id)
                            Button { model.playQuestion() } label: { Label(speech.phrase, systemImage: "speaker.wave.2.fill") }.font(ReferenceStyle.font(22)).accessibilityIdentifier("speech-play")
                            Button("点击并开始录音") { model.startSpeech() }
                                .buttonStyle(ReferenceButton(color: ReferenceStyle.blue)).disabled(lesson.speechDeclined).accessibilityIdentifier("speech-record")
                        }
                    }
                    else { question(lesson) }
                }.padding(30).frame(maxWidth: 660).frame(maxWidth: .infinity)
            }
            Spacer(minLength: 0)
            if lesson.interlude != nil {
                HStack { Spacer(); Button(copy("CONTINUE", "继续")) { model.advance() }.buttonStyle(ReferenceButton()).frame(width: 150).accessibilityIdentifier("interlude-continue") }
                    .padding(.horizontal, 60).padding(.vertical, 28).frame(minHeight: 115)
                    .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
            } else if let speech = lesson.deferredSpeech {
                HStack {
                    if lesson.speechDeclined {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(speech.closedTitle).font(ReferenceStyle.font(22, bold: true)).accessibilityIdentifier("speech-closed")
                            Text(speech.closedBody).font(ReferenceStyle.font(18))
                            if chinese { ReferenceFeedbackActions(model: model, color: Color(red: 205/255, green: 121/255, blue: 0)) }
                        }
                        Spacer()
                        Button("继续") { model.advance() }.buttonStyle(ReferenceButton()).accessibilityIdentifier("speech-continue")
                    } else {
                        Button(speech.declineLabel) { model.declineSpeech() }.buttonStyle(.plain).accessibilityIdentifier("speech-decline")
                        Spacer()
                        Button("检查") {}.buttonStyle(ReferenceButton()).disabled(true)
                    }
                }.padding(.horizontal, 60).padding(.vertical, 28).frame(minHeight: 115)
                    .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
            } else if !lesson.complete { answerBar(lesson) }
        }
        .sheet(isPresented: $model.confirmingExit) { exitConfirmation }
        }
    }
    private func answerBar(_ lesson: Lesson) -> some View {
        HStack(spacing: 30) {
            if lesson.listeningDeclined, let decline = lesson.question.listeningDecline {
                Image(systemName: "checkmark.circle.fill").font(.system(size: 48)).foregroundStyle(Color(red: 0.80, green: 0.47, blue: 0))
                VStack(alignment: .leading, spacing: 8) {
                    Text(decline.title).font(ReferenceStyle.font(22, bold: true)).accessibilityIdentifier("listening-declined")
                    Text(decline.body).font(ReferenceStyle.font(18))
                    if chinese { ReferenceFeedbackActions(model: model, color: Color(red: 0.80, green: 0.47, blue: 0)) }
                }.foregroundStyle(Color(red: 0.80, green: 0.47, blue: 0))
                Spacer()
                Button("继续") { model.advance() }.buttonStyle(ReferenceButton(color: Color(red: 1, green: 0.78, blue: 0))).accessibilityIdentifier("listening-continue")
            } else if let correct = lesson.feedback {
                Image(systemName: correct ? "checkmark.circle.fill" : "xmark.circle.fill").font(.system(size: 48)).foregroundStyle(correct ? accent : .red)
                VStack(alignment: .leading, spacing: 8) {
                    Text(correct ? (lesson.question.correctFeedback ?? copy("Well done!", "好棒！")) : ((lesson.skipped || lesson.question.kind == .textEntry) ? copy("Correct answer:", "正确答案：") : copy("Correct answer: \(lesson.question.correctText)", "正确答案：\(lesson.question.correctText)"))).font(.title2.bold())
                        .foregroundStyle(correct ? Color(red: 0.28, green: 0.62, blue: 0) : Color.red).accessibilityIdentifier("feedback").accessibilityValue(correct ? "correct" : "incorrect")
                    if !correct && (lesson.skipped || lesson.question.kind == .textEntry) { Text(lesson.skipped ? (lesson.question.skipCorrectText ?? lesson.question.correctText) : lesson.question.correctText) }
                    Text(lesson.question.explanation)
                    if chinese { ReferenceFeedbackActions(model: model, color: correct ? Color(red: 88/255, green: 167/255, blue: 0) : .red) }
                }
                Spacer()
                Button(copy("CONTINUE", "继续")) { model.advance() }.buttonStyle(SeedButtonStyle(fill: correct ? accent : .red)).accessibilityIdentifier("continue")
            } else {
                if let label = lesson.question.skipLabel {
                    Button(label) { model.skip() }.buttonStyle(ReferenceSkipButton()).accessibilityIdentifier("skip").offset(y: 2)
                }
                if let decline = lesson.question.listeningDecline {
                    if model.isReferenceSession {
                        ReferencePracticeControl(label: decline.label, identifier: "listening-decline", enabled: true,
                            action: { model.declineListening() }, face: AnyView(Text(decline.label).font(ReferenceStyle.font(17, bold: true)).tracking(0.8)
                                .foregroundStyle(ReferenceStyle.disclosureInk).frame(width: 160.6015625, height: 46)
                                .background(RoundedRectangle(cornerRadius: 16).fill(.white))
                                .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                                .shadow(color: ReferenceStyle.border, radius: 0, y: 2).frame(height: 50, alignment: .top)))
                            .frame(width: 160.6015625, height: 50)
                    } else {
                    Button(decline.label) { model.declineListening() }.buttonStyle(.plain).accessibilityIdentifier("listening-decline")
                    }
                }
                if lesson.question.sourceType == nil { Text(lesson.question.kind == .matching ? "Match all pairs to continue" : "Take your time. You’ve got this.").foregroundStyle(.secondary) }
                Spacer()
                if lesson.question.kind != .matching || chinese {
                    if chinese {
                        Button("检查") { model.submit() }.buttonStyle(ReferenceCheckButton()).disabled(!lesson.canSubmit).accessibilityIdentifier("check").offset(y: 2)
                    } else {
                        Button("CHECK") { model.submit() }.buttonStyle(SeedButtonStyle(fill: accent)).disabled(!lesson.canSubmit).accessibilityIdentifier("check")
                    }
                }
            }
        }.frame(maxWidth: chinese ? 920 : .infinity).padding(.horizontal, chinese ? 24 : 60).frame(maxWidth: .infinity).padding(.vertical, 28).frame(minHeight: chinese ? 140 : 115)
            .overlay {
                if lesson.supportsInputMode && lesson.feedback == nil && !lesson.listeningDeclined {
                    Button(lesson.question.kind == .wordTiles ? (lesson.usingKeyboard ? "使用词库" : "使用键盘") : (lesson.usingKeyboard ? "减少难度" : "加大难度")) { model.toggleInputMode() }
                        .font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.disclosureInk)
                        .frame(width: 150, height: 19.546875).contentShape(Rectangle()).offset(y: 2)
                        .buttonStyle(.plain).accessibilityElement(children: .ignore).accessibilityAddTraits(.isButton).accessibilityLabel(lesson.question.kind == .wordTiles ? (lesson.usingKeyboard ? "使用词库" : "使用键盘") : (lesson.usingKeyboard ? "减少难度" : "加大难度")).accessibilityIdentifier("toggle-input-mode")
                }
            }
            .background(lesson.listeningDeclined ? Color(red: 1, green: 0.961, blue: 0.827) : lesson.feedback == nil ? Color.white : lesson.feedback == true ? Color(red: 0.843, green: 1, blue: 0.722) : Color(red: 1, green: 0.875, blue: 0.875))
            .overlay(alignment: .top) { Rectangle().fill(Color.gray.opacity(0.15)).frame(height: 2) }
    }
    private var exitConfirmation: some View {
        VStack(spacing: 22) {
            SeedMascot()
            Text("Leave this lesson?").font(.largeTitle.bold()).accessibilityIdentifier("exit-title")
            Text("Your finished lessons are safe. This unfinished attempt will be discarded.").foregroundStyle(.secondary)
            Button("Keep learning") { model.confirmingExit = false }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("cancel-quit")
            Button("End session") { model.discardAttempt() }.buttonStyle(SeedButtonStyle(fill: .red)).accessibilityIdentifier("confirm-quit")
        }.padding(36).frame(width: 440).multilineTextAlignment(.center)
    }
    private var completion: some View {
        VStack(alignment: .leading, spacing: 20) {
            SeedMascot()
            Text("Lesson complete").font(.largeTitle.bold()).accessibilityIdentifier("lesson-complete")
            Text("You made time for your next step.").foregroundStyle(.secondary)
            Button("Back to your path") { model.discardAttempt() }
                .buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("return-path")
        }.padding(.vertical, 32)
    }
    @ViewBuilder private func question(_ lesson: Lesson) -> some View {
        if lesson.question.contextExamples != nil {
            VStack(alignment: .leading, spacing: 0) {
                HStack(spacing: 4) {
                    ReferenceStyle.image("en-pattern-context-indicator").resizable().frame(width: 32, height: 32)
                    Text(lesson.question.indicator ?? "").font(ReferenceStyle.font(17, bold: true))
                        .foregroundStyle(Color(red: 206/255, green: 130/255, blue: 1))
                }.frame(height: 32).padding(.bottom, 8)
                Text(lesson.displayedPrompt).font(ReferenceStyle.font(32, bold: true))
                    .frame(maxWidth: .infinity, minHeight: 40, maxHeight: 40, alignment: .leading)
                    .accessibilityIdentifier("question-title").accessibilityValue(lesson.displayedPrompt)
                words(lesson).padding(.top, 24)
            }.offset(y: -8)
        } else {
        VStack(alignment: .leading, spacing: 8) {
        if lesson.reviewing {
            Text(copy("ONE MORE LOOK", "错题重练")).font(.caption.bold()).foregroundStyle(accent).accessibilityIdentifier("review-label")
        } else if let indicator = lesson.question.indicator {
            Text(indicator).font(ReferenceStyle.font(14, bold: true)).foregroundStyle(indicator == "挑战题" ? .red : .purple).accessibilityIdentifier("question-indicator")
        } else if lesson.question.newWord {
            HStack(spacing: 4) {
                ReferenceStyle.image("en-newword-source").resizable().frame(width: 32, height: 32)
                Text(copy("NEW WORD", "新单词")).font(ReferenceStyle.font(16, bold: true)).tracking(0.64)
                    .foregroundStyle(Color(red: 206/255, green: 130/255, blue: 1))
            }.frame(height: 32).accessibilityIdentifier("question-indicator")
        }
        // Source challenge-header: 32px/40px. Translation's character row follows
        // the heading directly; the old shared 28-point gap displaced it.
        VStack(alignment: .leading, spacing: (model.isReferenceSession && lesson.question.sourceType == "assist") || ["translate", "completeReverseTranslation"].contains(lesson.question.sourceType ?? "") || (model.isReferenceSession && lesson.question.sourceType == "listen") ? 0 : model.isReferenceSession && lesson.question.sourceType == "listenTap" ? 23.5 : model.isReferenceSession && lesson.question.sourceType == "listenIsolation" && lesson.question.isolationPromptTokens != nil ? 32 : 28) {
        Text(lesson.question.kind == .wordTiles && lesson.question.hint == nil && lesson.question.sourceType == nil ? "Build this phrase" : lesson.displayedPrompt).font(ReferenceStyle.font(32, bold: true))
            .frame(maxWidth: .infinity, minHeight: 40, maxHeight: 40, alignment: .leading)
            .accessibilityIdentifier("question-title").accessibilityValue(lesson.displayedPrompt)
        switch lesson.question.kind {
        case .choice: choices(lesson)
        case .wordTiles: if lesson.usingKeyboard { textEntry(lesson) } else { words(lesson) }
        case .matching: matching(lesson)
        case .textEntry: textEntry(lesson)
        }
        }.padding(.top, 0.5)
        if !model.isReferenceSession && lesson.question.kind == .choice && !["dialogue", "listenIsolation"].contains(lesson.question.sourceType ?? "") {
            Button { model.pronounce() } label: { Label(lesson.selected == nil ? "Read the instruction" : "Listen again", systemImage: "speaker.wave.2.fill") }.buttonStyle(.plain).foregroundStyle(.cyan).accessibilityIdentifier("pronounce")
        }
        }
        }
    }
    private var generalListeningControls: some View {
        HStack(alignment: .bottom, spacing: 16) {
            generalListeningButton(slow: false, size: 100, iconSize: CGSize(width: 50, height: 38.828125))
            generalListeningButton(slow: true, size: 70, iconSize: CGSize(width: 42, height: 23.046875))
        }.frame(maxWidth: .infinity).frame(height: 100)
    }
    private func generalListeningButton(slow: Bool, size: CGFloat, iconSize: CGSize) -> some View {
        ReferencePracticeControl(label: slow ? "播放慢速" : "播放正常语速", identifier: slow ? "pronounce-slow" : "pronounce", enabled: true,
            action: { model.playQuestion(slow: slow) }, face: AnyView(
                ReferenceStyle.image(slow ? "general-listen-slow-source-frame" : "general-listen-normal-source-frame")
                    .resizable().frame(width: iconSize.width, height: iconSize.height)
                    .frame(width: size, height: size - 4)
                    .background(RoundedRectangle(cornerRadius: size / 4).fill(ReferenceStyle.blue)
                        .shadow(color: Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: 4))
                    .frame(height: size, alignment: .top)))
            .frame(width: size, height: size)
    }
    private func splitListeningButton(slow: Bool, width: CGFloat) -> some View {
        ReferencePracticeControl(label: slow ? "播放慢速" : "播放正常语速", identifier: slow ? "pronounce-slow" : "pronounce", enabled: true,
            action: { model.playQuestion(slow: slow) }, face: AnyView(
                ReferenceStyle.image(slow ? "general-listen-slow-source-frame" : "general-listen-normal-source-frame")
                    .renderingMode(.template).resizable().frame(width: slow ? 42 : 29, height: slow ? 23.046875 : 22.5390625)
                    .foregroundStyle(ReferenceStyle.blue).frame(width: width, height: 66)))
            .frame(width: width, height: 66)
    }
    @ViewBuilder private func textEntry(_ lesson: Lesson) -> some View {
        if lesson.question.sourceType == "name", let image = lesson.question.promptImageResource {
            HStack(spacing: 24) {
                ReferenceStyle.image(image).resizable().scaledToFit().frame(width: 180, height: 180)
                    .accessibilityIdentifier("question-image")
                TextField("使用英语键入", text: Binding(get: { model.lesson?.displayedInput ?? "" }, set: { model.enterText($0) }))
                    .font(ReferenceStyle.font(19)).textFieldStyle(.plain).padding(.horizontal, 14)
                    .frame(width: 394, height: 46)
                    .background(Color(white: 247/255), in: RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(ReferenceStyle.border, lineWidth: 2))
                    .disabled(lesson.feedback != nil).accessibilityIdentifier("answer-input")
                    .accessibilityLabel("使用英语键入").padding(.leading, 1)
            }.frame(height: 350).offset(y: 14)
        } else {
        if let hint = lesson.question.hint {
            if chinese, let character = lesson.question.characterResource {
                HStack(spacing: 0) {
                    ReferenceCharacter(resource: character, feedback: lesson.feedback).id(lesson.question.id)
                        .frame(width: ReferenceCharacter.size(for: character).width, height: ReferenceCharacter.size(for: character).height)
                    phraseBubble(hint, speaker: false)
                    Spacer(minLength: 0)
                }.frame(height: 175).padding(.leading, 10)
            } else {
                Text(hint).font(ReferenceStyle.font(20)).accessibilityIdentifier("question-hint")
            }
        }
        if model.isReferenceSession && lesson.question.sourceType == "listen" {
            HStack(spacing: 0) {
                if let character = lesson.question.characterResource {
                    ReferenceCharacter(resource: character, feedback: lesson.feedback).id(lesson.question.id)
                        .frame(width: 118, height: 175)
                }
                HStack(spacing: 0) {
                    splitListeningButton(slow: false, width: 80)
                    Rectangle().fill(ReferenceStyle.border).frame(width: 2, height: 66)
                    splitListeningButton(slow: true, width: 88)
                }.frame(width: 170, height: 66)
                    .background(RoundedRectangle(cornerRadius: 16, style: .circular).fill(.white))
                    .overlay(RoundedRectangle(cornerRadius: 16, style: .circular).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                    .overlay(alignment: .leading) {
                        ZStack {
                            Path { p in p.move(to: CGPoint(x: 9, y: 0)); p.addLine(to: CGPoint(x: 1, y: 8)); p.addLine(to: CGPoint(x: 9, y: 16)); p.closeSubpath() }.fill(.white)
                            Path { p in p.move(to: CGPoint(x: 9, y: 0)); p.addLine(to: CGPoint(x: 1, y: 8)); p.addLine(to: CGPoint(x: 9, y: 16)) }.stroke(ReferenceStyle.border, lineWidth: 2)
                        }.frame(width: 10, height: 16).offset(x: -8).accessibilityHidden(true)
                    }
                Spacer(minLength: 0)
            }.frame(height: 175).padding(.leading, 10)
        } else if model.isReferenceSession && lesson.question.sourceType == "listenTap" {
            generalListeningControls.padding(.bottom, 46.5)
        } else if lesson.question.sourceType == "listenComplete" {
            HStack(spacing: 28) {
                Button { model.playQuestion() } label: { Image(systemName: "speaker.wave.2.fill").font(.system(size: 36)).frame(width: 90, height: 78) }
                    .buttonStyle(SeedButtonStyle(fill: .cyan)).accessibilityIdentifier("pronounce").accessibilityLabel("播放正常语速")
                Button { model.playQuestion(slow: true) } label: { Image(systemName: "tortoise.fill").font(.system(size: 26)).frame(width: 56, height: 58) }
                    .buttonStyle(SeedButtonStyle(fill: .cyan)).accessibilityIdentifier("pronounce-slow").accessibilityLabel("播放慢速")
            }
        }
        if lesson.usingKeyboard || (model.isReferenceSession && ["listen", "translate"].contains(lesson.question.sourceType ?? "")) {
            ReferenceAnswerEditor(text: Binding(get: { model.lesson?.displayedInput ?? "" }, set: { model.enterText($0) }), enabled: lesson.feedback == nil)
                .overlay(alignment: .topLeading) {
                    if model.isReferenceSession && lesson.displayedInput.isEmpty {
                        Text("使用英语键入").font(ReferenceStyle.font(19, weight: 400)).foregroundStyle(ReferenceStyle.disclosureInk)
                            .padding(.horizontal, 14).padding(.vertical, 12).allowsHitTesting(false).accessibilityHidden(true)
                    }
                }
                .frame(height: 170).background(Color(white: 247/255), in: RoundedRectangle(cornerRadius: 10))
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(ReferenceStyle.border, lineWidth: 2))
        } else {
        HStack(spacing: 6) {
            if let prefix = lesson.question.completionPrefix, !prefix.isEmpty, !lesson.usingKeyboard { Text(prefix).font(ReferenceStyle.font(20)).accessibilityIdentifier("completion-prefix") }
            TextField("", text: Binding(get: { model.lesson?.displayedInput ?? "" }, set: { model.enterText($0) }))
                .font(ReferenceStyle.font(chinese ? 17 : 20)).textFieldStyle(.plain).frame(maxWidth: lesson.usingKeyboard || lesson.question.completionPrefix == nil ? .infinity : 120)
                .padding(.vertical, 8).overlay(alignment: .bottom) { Rectangle().fill(Color.gray.opacity(0.4)).frame(height: 2) }
                .disabled(lesson.feedback != nil || lesson.listeningDeclined).accessibilityIdentifier("answer-input").accessibilityLabel(chinese ? (!lesson.usingKeyboard && lesson.question.completionPrefix != nil ? (lesson.question.completionPrefix ?? "") + (lesson.question.completionSuffix ?? "") : "使用英语键入") : "填写所缺单词")
            if let suffix = lesson.question.completionSuffix, !lesson.usingKeyboard { Text(suffix).font(ReferenceStyle.font(20)).accessibilityIdentifier("completion-suffix") }
        }.frame(maxWidth: .infinity, minHeight: chinese ? 146 : nil, maxHeight: chinese ? 146 : nil, alignment: .topLeading).padding(chinese ? 12 : 20)
            .background(chinese ? Color(white: 247/255) : .clear, in: RoundedRectangle(cornerRadius: chinese ? 8 : 12))
            .overlay(RoundedRectangle(cornerRadius: chinese ? 8 : 12).stroke(Color.gray.opacity(0.25), lineWidth: 2))
        }
    }
    }
    @ViewBuilder private func isolation(_ lesson: Lesson) -> some View {
        if model.isReferenceSession, let tokens = lesson.question.isolationPromptTokens {
            VStack(spacing: 0) {
                HStack(spacing: 0) {
                    if let character = lesson.question.characterResource {
                        ReferenceCharacter(resource: character, feedback: lesson.feedback).id(lesson.question.id)
                            .frame(width: 118, height: 175)
                    }
                    HStack(spacing: 8) {
                        ReferencePracticeControl(label: "播放音频", identifier: "isolation-prompt", enabled: true,
                            action: { model.playQuestion() }, face: AnyView(ReferenceStyle.image("en-match-speaker-source-frame")
                                .renderingMode(.template).resizable().frame(width: 29, height: 22).foregroundStyle(ReferenceStyle.blue)))
                            .frame(width: 29, height: 22)
                        ReferenceIsolationPhrase(tokens: tokens, correct: lesson.feedback == true)
                    }.padding(.horizontal, 16).frame(height: 56)
                        .background(ReferenceIsolationBubble().fill(ReferenceStyle.background))
                        .overlay(ReferenceIsolationBubble().stroke(ReferenceStyle.border, lineWidth: 2))
                    Spacer(minLength: 0)
                }.padding(.leading, 16).frame(height: 175)
                Rectangle().fill(ReferenceStyle.border).frame(height: 2).padding(.bottom, 36)
                isolationOptions(lesson)
            }
        } else {
        VStack(spacing: 42.5) {
            HStack(spacing: 16) {
                if let character = lesson.question.characterResource {
                    ReferenceCharacter(resource: character, feedback: lesson.feedback).id(lesson.question.id)
                        .frame(width: 118, height: 175)
                }
                Button { model.playQuestion() } label: {
                    HStack(spacing: 8) {
                        ReferenceStyle.image("en-match-speaker-source-frame").renderingMode(.template).resizable().frame(width: 24, height: 19).foregroundStyle(ReferenceStyle.blue)
                        Text(lesson.displayedHint ?? "").font(ReferenceStyle.font(19)).foregroundStyle(ReferenceStyle.ink)
                    }.padding(14).overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                }.buttonStyle(.plain).accessibilityIdentifier("isolation-prompt").accessibilityLabel(lesson.displayedHint ?? "")
                Spacer()
            }.frame(height: 175)
            isolationOptions(lesson)
        }
        }
    }
    private func isolationOptions(_ lesson: Lesson) -> some View {
        VStack(spacing: 8) {
                ForEach(lesson.question.options) { option in
                    ReferenceAudioRadio(label: option.text, identifier: "option-" + option.id,
                        waveform: lesson.feedback == true && lesson.selected == option.id ? option.correctImageResource ?? option.imageResource : option.imageResource,
                        correct: lesson.feedback == true, selected: lesson.selected == option.id,
                        enabled: lesson.feedback == nil, action: { model.choose(option.id) }).frame(height: 62)
                }
            }
    }
    @ViewBuilder private func choices(_ lesson: Lesson) -> some View {
        if lesson.question.sourceType == "listenIsolation" {
            isolation(lesson)
        } else if lesson.question.sourceType == "dialogue" {
            dialogue(lesson)
        } else if model.isUnitPlacement && lesson.question.sourceType == "gapFill" {
            VStack(alignment:.leading,spacing:0) {
                HStack(spacing:0) {
                    Text(lesson.question.completionPrefix ?? "")
                    Text(lesson.selected.flatMap { id in lesson.question.options.first(where:{$0.id==id})?.text } ?? "")
                        .frame(width:70,height:39).overlay(alignment:.bottom){Rectangle().fill(ReferenceStyle.border).frame(height:2)}
                    Text(lesson.question.completionSuffix ?? "")
                }.font(ReferenceStyle.font(19)).frame(height:39).padding(.top,3)
                    .accessibilityIdentifier("gap-fill-context")
                VStack(spacing:8) {
                    ForEach(Array(lesson.question.options.enumerated()),id:\.element.id) { index,option in
                        ReferenceAudioRadio(label:"\(index+1) \(option.text)",identifier:"option-"+option.id,waveform:nil,correct:lesson.feedback==true,selected:lesson.selected==option.id,enabled:lesson.feedback==nil,action:{model.choose(option.id)},textChoice:true).frame(width:600,height:60)
                    }
                }.padding(.top,80)
            }
        } else if model.isReferenceSession && lesson.question.sourceType == "assist" {
            HStack(spacing: 16) {
                if let character = lesson.question.characterResource {
                    ReferenceCharacter(resource: character, feedback: lesson.feedback).id(lesson.question.id)
                        .frame(width: 118, height: 175)
                }
                Text(lesson.question.hint ?? "").font(ReferenceStyle.font(20)).padding(16)
                    .overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                    .overlay(alignment: .leading) {
                        ZStack {
                            Path { p in p.move(to: CGPoint(x: 14, y: 0)); p.addLine(to: CGPoint(x: 0, y: 15)); p.addLine(to: CGPoint(x: 14, y: 15)); p.closeSubpath() }.fill(.white)
                            Path { p in p.move(to: CGPoint(x: 14, y: 0)); p.addLine(to: CGPoint(x: 0, y: 15)); p.addLine(to: CGPoint(x: 14, y: 15)) }.stroke(ReferenceStyle.border, lineWidth: 2)
                        }.frame(width: 15, height: 16).offset(x: -13).accessibilityHidden(true)
                    }.accessibilityIdentifier("question-hint")
                Spacer(minLength: 0)
            }.frame(height: 175)
            VStack(spacing: 8) {
                ForEach(Array(lesson.question.options.enumerated()), id: \.element.id) { index, option in
                    ReferenceAudioRadio(label: "\(index + 1) \(option.text)", identifier: "option-" + option.id,
                        waveform: nil, correct: lesson.feedback == true, selected: lesson.selected == option.id,
                        enabled: lesson.feedback == nil, action: { model.choose(option.id) }, textChoice: true)
                        .frame(width: 600, height: 60)
                }
            }
        } else if let hint = lesson.question.hint {
            HStack(spacing: 16) {
                if let character = lesson.question.characterResource { ReferenceCharacter(resource: character, feedback: lesson.feedback).id(lesson.question.id).frame(width: ReferenceCharacter.size(for: character).width, height: ReferenceCharacter.size(for: character).height) }
                Text(hint).font(ReferenceStyle.font(20)).accessibilityIdentifier("question-hint")
                    .padding(16).overlay(RoundedRectangle(cornerRadius: 14).stroke(ReferenceStyle.border, lineWidth: 2))
            }
            VStack(spacing: 12) {
                ForEach(Array(lesson.question.options.enumerated()), id: \.element.id) { index, option in
                    Button { model.choose(option.id) } label: {
                        HStack(spacing: 20) { Text("\(index + 1)").font(ReferenceStyle.font(14)).frame(width: 24, height: 24).overlay(RoundedRectangle(cornerRadius: 6).stroke(ReferenceStyle.border, lineWidth: 2)); Text(option.text).font(ReferenceStyle.font(19)); Spacer() }
                    }.buttonStyle(SeedTileStyle(selected: lesson.selected == option.id))
                        .disabled(lesson.feedback != nil).accessibilityIdentifier("option-" + option.id)
                        .accessibilityLabel(option.text).accessibilityValue(lesson.selected == option.id ? "selected" : "not selected")
                }
            }
        } else { LazyVGrid(columns: [GridItem(.adaptive(minimum: 150, maximum: 220), spacing: 12)], spacing: 12) {
            ForEach(Array(lesson.question.options.enumerated()), id: \.element.id) { index, option in
                Button { model.choose(option.id) } label: {
                    VStack(spacing: 18) {
                        ChoiceIllustration(phrase: option.text, resource: option.imageResource)
                        HStack {
                            Text(option.text).font(.system(size: 17, weight: .medium)).lineLimit(1).minimumScaleFactor(0.8)
                            Spacer(minLength: 3)
                            Text("\(index + 1)").font(.caption.bold()).padding(5)
                                .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.25), lineWidth: 1))
                        }
                    }
                }.buttonStyle(SeedChoiceStyle(selected: lesson.selected == option.id, feedback: lesson.feedback))
                    .disabled(lesson.feedback != nil).accessibilityIdentifier("option-" + option.id)
                    .accessibilityLabel(option.text).accessibilityValue(lesson.selected == option.id ? "selected" : "not selected")
            }
        } }
    }
    private func dialogue(_ lesson: Lesson) -> some View {
        VStack(spacing: 34) {
            HStack(spacing: 16) {
                if let avatar = lesson.question.dialogueAvatars?.first { ReferenceStyle.image(avatar).resizable().scaledToFit().frame(width: 64, height: 64) }
                Button { model.playQuestion() } label: {
                    HStack { Image(systemName: "speaker.wave.2.fill").foregroundStyle(ReferenceStyle.blue); Text(lesson.question.hint ?? "").foregroundStyle(ink) }
                        .font(ReferenceStyle.font(19)).padding(16).overlay(RoundedRectangle(cornerRadius: 12).stroke(ReferenceStyle.border, lineWidth: 2))
                }.buttonStyle(.plain).accessibilityIdentifier("pronounce")
                Spacer()
            }
            HStack(spacing: 20) {
                Spacer()
                Text(lesson.feedback == true ? lesson.question.correctText : "_______").font(ReferenceStyle.font(19)).padding(16)
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(ReferenceStyle.border, lineWidth: 2))
                if let avatar = lesson.question.dialogueAvatars?.last { ReferenceStyle.image(avatar).resizable().scaledToFit().frame(width: 64, height: 64) }
            }
            VStack(spacing: 12) {
                ForEach(Array(lesson.question.options.enumerated()), id: \.element.id) { index, option in
                    Button { model.choose(option.id) } label: {
                        HStack { Text("\(index + 1)").font(ReferenceStyle.font(14)).frame(width: 26, height: 26).overlay(RoundedRectangle(cornerRadius: 6).stroke(ReferenceStyle.border, lineWidth: 2)); Spacer(); Text(option.text); Spacer() }
                    }.buttonStyle(SeedTileStyle(selected: lesson.selected == option.id)).disabled(lesson.feedback != nil)
                        .accessibilityLabel(option.text).accessibilityIdentifier("option-" + option.id)
                }
            }.padding(.top, 12)
        }
    }
    private func generalListeningWords(_ lesson: Lesson) -> some View {
            VStack(spacing: 0) {
                generalListeningControls
                WordFlowLayout(centered: false) {
                    ForEach(lesson.selectedWords, id: \.self) { id in
                        Button(lesson.question.words.first { $0.id == id }!.text) { model.removeWord(id) }
                            .buttonStyle(ReferenceListeningTile()).fixedSize().disabled(lesson.feedback != nil || lesson.listeningDeclined)
                            .accessibilityIdentifier("selected-word-" + id)
                    }
                }.frame(maxWidth: .infinity, minHeight: 52, maxHeight: 52, alignment: .bottomLeading)
                    .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                WordFlowLayout(centered: true) {
                    ForEach(lesson.visibleWords) { word in
                        Button(word.text) { model.addWord(word.id) }.buttonStyle(ReferenceListeningTile()).fixedSize()
                            .disabled(lesson.feedback != nil || lesson.listeningDeclined || lesson.selectedWords.contains(word.id))
                            .accessibilityIdentifier("word-bank-" + word.id)
                    }
                }.padding(.top, 68)
            }
    }
    private func contextualExample(_ example: String, highlight: String) -> some View {
        let parts = highlight.isEmpty ? [example] : example.components(separatedBy: highlight)
        return (Text(parts[0]) + Text(highlight).foregroundColor(Color(red: 206/255, green: 130/255, blue: 1)).bold() + Text(parts.count > 1 ? parts[1] : ""))
            .font(ReferenceStyle.font(19))
            .overlay(alignment: .bottom) { GeometryReader { proxy in
                Path { path in path.move(to: CGPoint(x: 0, y: proxy.size.height + 4));path.addLine(to: CGPoint(x: proxy.size.width - 4, y: proxy.size.height + 4)) }
                    .stroke(Color(white: 0.69), style: StrokeStyle(lineWidth: 2, dash: [2, 2]))
            } }
    }
    @ViewBuilder private func words(_ lesson: Lesson) -> some View {
        if let examples = lesson.question.contextExamples {
            VStack(spacing: 36) {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(Array(examples.enumerated()), id: \.offset) { index, example in
                        contextualExample(example, highlight: lesson.question.contextHighlights?.indices.contains(index) == true ? lesson.question.contextHighlights![index] : "")
                            .frame(maxWidth: .infinity, minHeight: 80, alignment: .leading)
                            .padding(.horizontal, 16).accessibilityIdentifier("context-example-\(index)")
                            .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                    }
                    HStack(spacing: 4) {
                        Text(lesson.question.completionPrefix ?? "").accessibilityIdentifier("completion-prefix")
                        HStack(spacing: 4) {
                            ForEach(lesson.selectedWords, id: \.self) { id in
                                Button(lesson.question.words.first { $0.id == id }!.text) { model.removeWord(id) }
                                    .buttonStyle(SeedTileStyle(selected: true)).disabled(lesson.feedback != nil)
                                    .accessibilityIdentifier("selected-word-" + id)
                            }
                        }.frame(minWidth: 82, minHeight: 48)
                            .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                        Text(lesson.question.completionSuffix ?? "").accessibilityIdentifier("completion-suffix")
                    }.font(ReferenceStyle.font(19)).padding(.horizontal, 16)
                        .frame(maxWidth: .infinity, minHeight: 87.84375, alignment: .leading)
                }.overlay(RoundedRectangle(cornerRadius: 16).stroke(ReferenceStyle.border, lineWidth: 2))
                    .accessibilityIdentifier("context-table")
                WordFlowLayout(centered: true) {
                    ForEach(lesson.visibleWords) { word in
                        Button(word.text) { model.addWord(word.id) }.buttonStyle(SeedTileStyle()).fixedSize()
                            .disabled(lesson.feedback != nil || lesson.selectedWords.contains(word.id))
                            .accessibilityIdentifier("word-bank-" + word.id)
                    }
                }
            }
        } else if lesson.question.sourceType == "tapComplete", let image = lesson.question.promptImageResource {
            VStack(spacing: 90) {
                HStack(spacing: 24) {
                    ReferenceStyle.image(image).resizable().scaledToFit().frame(width: 180, height: 180)
                        .accessibilityIdentifier("question-image")
                    HStack(spacing: 4) {
                        Text(lesson.question.completionPrefix ?? "").accessibilityIdentifier("completion-prefix")
                        HStack(spacing: 4) {
                            ForEach(lesson.selectedWords, id: \.self) { id in
                                Button(lesson.question.words.first { $0.id == id }!.text) { model.removeWord(id) }
                                    .buttonStyle(SeedTileStyle(selected: true)).disabled(lesson.feedback != nil)
                                    .accessibilityIdentifier("selected-word-" + id)
                            }
                        }.frame(minWidth: 80, minHeight: 48)
                            .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                        Text(lesson.question.completionSuffix ?? "").accessibilityIdentifier("completion-suffix")
                    }.font(ReferenceStyle.font(20))
                    Spacer(minLength: 0)
                }.padding(.top, 20)
                WordFlowLayout(centered: true) {
                    ForEach(lesson.visibleWords) { word in
                        Button(word.text) { model.addWord(word.id) }.buttonStyle(SeedTileStyle()).fixedSize()
                            .disabled(lesson.feedback != nil || lesson.selectedWords.contains(word.id))
                            .accessibilityIdentifier("word-bank-" + word.id)
                    }
                }
            }
        } else if model.isReferenceSession && lesson.question.sourceType == "listenTap" {
            generalListeningWords(lesson)
        } else if model.isObservedCourse && lesson.question.sourceType == "translate" {
            observedTranslationWords(lesson)
        } else {
        VStack(alignment: .leading, spacing: 24) {
            if lesson.question.sourceType == "listenTap" {
                if model.isReferenceSession { generalListeningControls }
                else {
                HStack(spacing: 28) {
                    Button { model.playQuestion() } label: { Image(systemName: "speaker.wave.2.fill").font(.system(size: 54)).frame(width: 110, height: 110) }
                        .buttonStyle(ReferenceButton(color: ReferenceStyle.blue)).accessibilityLabel(copy("Listen", "播放")).accessibilityIdentifier("pronounce")
                    Button { model.playQuestion(slow: true) } label: { Image(systemName: "tortoise.fill").font(.system(size: 28)).frame(width: 64, height: 64) }
                        .buttonStyle(ReferenceButton(color: ReferenceStyle.blue)).accessibilityLabel(copy("Slow", "慢速播放")).accessibilityIdentifier("pronounce-slow")
                }.frame(maxWidth: .infinity)
                }
            } else {
                HStack(spacing: 16) {
                    Group {
                        if let character = lesson.question.characterResource { ReferenceCharacter(resource: character, feedback: lesson.feedback).id(lesson.question.id) }
                        else if !chinese { SeedMascot().scaleEffect(0.7) }
                        else { Color.clear }
                    }.frame(width: ReferenceCharacter.size(for: lesson.question.characterResource).width, height: ReferenceCharacter.size(for: lesson.question.characterResource).height)
                    if let example = lesson.question.example {
                        Button { model.playExample() } label: {
                            phraseBubble(example, speaker: true)
                        }.buttonStyle(.plain).accessibilityIdentifier("pronounce-example")
                    } else if lesson.question.audioResource != nil || !chinese {
                        Button { model.pronounce() } label: {
                            phraseBubble(lesson.question.hint ?? lesson.question.prompt, speaker: true)
                        }.buttonStyle(.plain).accessibilityIdentifier("pronounce")
                    } else {
                        phraseBubble(lesson.question.hint ?? lesson.question.prompt, speaker: false)
                    }
                }.padding(.leading, ReferenceCharacter.hasAnimation(for: lesson.question.characterResource) ? 10 : 0)
            }
            if let prefix = lesson.question.completionPrefix {
                HStack(spacing: 0) {
                    Text(prefix).accessibilityIdentifier("completion-prefix")
                    HStack(spacing: 8) {
                        ForEach(lesson.selectedWords, id: \.self) { id in
                            Button(lesson.question.words.first { $0.id == id }!.text) { model.removeWord(id) }
                                .buttonStyle(SeedTileStyle(selected: true)).disabled(lesson.feedback != nil || lesson.listeningDeclined)
                                .accessibilityIdentifier("selected-word-" + id)
                        }
                    }.frame(minWidth: 140, minHeight: 48)
                        .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                    Text(lesson.question.completionSuffix ?? "").accessibilityIdentifier("completion-suffix")
                }.font(ReferenceStyle.font(20)).frame(maxWidth: .infinity, minHeight: 108, alignment: .leading)
            } else {
                WordFlowLayout(centered: false) {
                    ForEach(lesson.selectedWords, id: \.self) { id in
                        Button(lesson.question.words.first { $0.id == id }!.text) { model.removeWord(id) }
                            .buttonStyle(SeedTileStyle(selected: true)).fixedSize().disabled(lesson.feedback != nil || lesson.listeningDeclined)
                            .accessibilityIdentifier("selected-word-" + id)
                    }
                }.padding(.vertical, 12).frame(maxWidth: .infinity, minHeight: 108, alignment: .topLeading)
                    .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                    .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
            }
            WordFlowLayout(centered: true) {
                ForEach(lesson.visibleWords) { word in
                    Button(word.text) { model.addWord(word.id) }.buttonStyle(SeedTileStyle()).fixedSize()
                        .disabled(lesson.feedback != nil || lesson.listeningDeclined || lesson.selectedWords.contains(word.id)).accessibilityIdentifier("word-bank-" + word.id)
                }
            }
            Text(chinese ? "" : "Tap a word in your phrase to put it back.").font(.callout).foregroundStyle(.secondary)
        }
        }
    }
    private func observedTranslationWords(_ lesson: Lesson) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 0) {
                Group {
                    if let resource = lesson.question.characterResource { ReferenceCharacter(resource: resource, feedback: lesson.feedback).id(lesson.question.id) }
                    else { Color.clear }
                }.frame(width: 118, height: 175)
                Button { model.pronounce() } label: {
                    phraseBubble(lesson.question.hint ?? "", speaker: lesson.question.audioResource != nil)
                }.buttonStyle(.plain).accessibilityIdentifier("pronounce")
                Spacer(minLength: 0)
            }.padding(.leading, 10).frame(height: 175)
            WordFlowLayout(centered: false) {
                ForEach(lesson.selectedWords, id: \.self) { id in
                    if let word = lesson.question.words.first(where: { $0.id == id }) {
                        observedTranslationTile(word.text, id: "selected-word-" + id, enabled: lesson.feedback == nil, action: { model.removeWord(id) })
                    }
                }
            }.padding(.horizontal, 4).padding(.top, 6.078125)
                .frame(width: 600, height: 60, alignment: .topLeading)
                .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
            WordFlowLayout(centered: true) {
                ForEach(lesson.visibleWords) { word in
                    observedTranslationTile(word.text, id: "word-bank-" + word.id,
                        enabled: lesson.feedback == nil && !lesson.selectedWords.contains(word.id), action: { model.addWord(word.id) })
                }
            }.padding(.top, lesson.question.sourceLanguage == "en" ? 38.078125 : 18)
        }
    }
    private func observedTranslationTile(_ text: String, id: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        let width = (text as NSString).size(withAttributes: [.font: ReferenceStyle.nativeFont(19)]).width + 36
        return ReferencePracticeControl(label: text, identifier: id, enabled: enabled, action: action, face: AnyView(
            Text(text).font(ReferenceStyle.font(19)).foregroundStyle(ReferenceStyle.ink)
                .frame(width: width, height: 47.84375).background(.white, in: RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                .shadow(color: ReferenceStyle.border, radius: 0, y: 4).frame(height: 51.84375, alignment: .top)))
            .frame(width: width, height: 51.84375)
    }
    private func phraseBubble(_ text: String, speaker: Bool) -> some View {
        HStack(spacing: 12) {
            if speaker { Image(systemName: "speaker.wave.2.fill").foregroundStyle(ReferenceStyle.blue) }
            Text(text).foregroundStyle(ink).multilineTextAlignment(.leading).accessibilityIdentifier("question-hint")
        }.font(ReferenceStyle.font(20)).padding(18)
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(ReferenceStyle.border, lineWidth: 2))
    }
    @ViewBuilder private func matching(_ lesson: Lesson) -> some View {
        if lesson.question.sourceType == "listenMatch" { audioMatching(lesson) } else {
        VStack(alignment: .leading, spacing: 14) {
            if let hint = lesson.matchingHint { Text(hint).foregroundStyle(.secondary) }
            else if !model.isReferenceSession { Text("Choose an expression, then its meaning.").foregroundStyle(.secondary) }
            HStack(alignment: .top, spacing: 20) {
                VStack(spacing: 12) {
                    ForEach(lesson.question.pairs) { pair in
                        Button(pair.left) { model.match(pair.id, left: true) }
                            .buttonStyle(SeedTileStyle(selected: lesson.selectedLeft == pair.id))
                            .disabled(lesson.listeningDeclined || lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-left-" + pair.id)
                    }
                }
                VStack(spacing: 12) {
                    ForEach(orderedRightPairs(lesson.question)) { pair in
                        Button(pair.right) { model.match(pair.id, left: false) }
                            .buttonStyle(SeedTileStyle(selected: lesson.selectedRight == pair.id))
                            .disabled(lesson.listeningDeclined || lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-right-" + pair.id)
                    }
                }
            }
        }
    }
    }
    private func audioMatching(_ lesson: Lesson) -> some View {
        HStack(spacing: 32) {
            VStack(spacing: 12) {
                ForEach(Array(lesson.question.pairs.enumerated()), id: \.element.id) { index, pair in
                    Button { model.match(pair.id, left: true) } label: {
                        HStack(spacing: 14) {
                            Text(String(index + 1)).font(ReferenceStyle.font(14, bold: true)).frame(width: 28, height: 28)
                                .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color.gray.opacity(0.25), lineWidth: 2))
                            ReferenceStyle.image("en-match-speaker-source-frame").renderingMode(.template).resizable().frame(width: 24, height: 19).foregroundStyle(lesson.incorrectMatch?.first == pair.id ? Color.red : lesson.matchedPairs.contains(pair.id) ? Color.green : ReferenceStyle.blue)
                            ReferenceStyle.image("en-match-waveform-source-frame").renderingMode(.template).resizable().frame(width: 81, height: 24).foregroundStyle(lesson.incorrectMatch?.first == pair.id ? Color.red : lesson.matchedPairs.contains(pair.id) ? Color.green : ReferenceStyle.blue)
                            Spacer(minLength: 0)
                        }.padding(.horizontal, 18).frame(width: 253, height: 56)
                    }.buttonStyle(AudioPairButtonStyle(matched: lesson.matchedPairs.contains(pair.id), selected: lesson.selectedLeft == pair.id, incorrect: lesson.incorrectMatch?.first == pair.id))
                        .disabled(lesson.listeningDeclined || lesson.feedback != nil || lesson.matchedPairs.contains(pair.id))
                        .accessibilityIdentifier("pair-left-" + pair.id).accessibilityLabel(String(index + 1))
                        .accessibilityValue(lesson.incorrectMatch?.first == pair.id ? "incorrect" : lesson.matchedPairs.contains(pair.id) ? "matched" : "available")
                }
            }
            VStack(spacing: 12) {
                ForEach(Array(orderedRightPairs(lesson.question).enumerated()), id: \.element.id) { index, pair in
                    audioRightPair(pair, index: index, lesson: lesson)
                }
            }
        }.frame(maxWidth: .infinity).padding(.top, 59)
    }
    private func audioRightPair(_ pair: WordPair, index: Int, lesson: Lesson) -> some View {
        let label = "\(index + 5) \(pair.right)"
        return Button { model.match(pair.id, left: false) } label: {
            HStack {
                Text(String(index + 5)).font(ReferenceStyle.font(14, bold: true)).frame(width: 28, height: 28)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color.gray.opacity(0.25), lineWidth: 2))
                Text(pair.right).font(ReferenceStyle.font(20)).frame(maxWidth: .infinity)
            }.padding(.horizontal, 18).frame(width: 253, height: 56)
                    }.buttonStyle(AudioPairButtonStyle(matched: lesson.matchedPairs.contains(pair.id), selected: lesson.selectedRight == pair.id, incorrect: lesson.incorrectMatch?.last == pair.id))
            .disabled(lesson.listeningDeclined || lesson.feedback != nil || lesson.matchedPairs.contains(pair.id))
            .accessibilityIdentifier("pair-right-" + pair.id).accessibilityLabel(label)
            .accessibilityValue(lesson.incorrectMatch?.last == pair.id ? "incorrect" : lesson.matchedPairs.contains(pair.id) ? "matched" : "available")
    }
    private func orderedRightPairs(_ question: Question) -> [WordPair] {
        question.rightOrder?.compactMap { id in question.pairs.first { $0.id == id } } ?? Array(question.pairs.reversed())
    }
}

struct SeedButtonStyle: ButtonStyle {
    var fill: Color
    var foreground: Color = .white
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.system(size: 16, weight: .bold, design: .rounded)).padding(.horizontal, 24).padding(.vertical, 16)
            .frame(minWidth: 110).foregroundStyle(enabled ? foreground : Color.gray)
            .background {
                RoundedRectangle(cornerRadius: 13).fill(enabled ? fill : Color(white: 0.9))
                    .shadow(color: Color.black.opacity(0.18), radius: 0, y: configuration.isPressed ? 0 : 4)
            }
            .overlay(RoundedRectangle(cornerRadius: 13).stroke(Color.black.opacity(0.12), lineWidth: 2))
            .offset(y: configuration.isPressed ? 4 : 0)
    }
}

struct ReferenceListeningTile: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(ReferenceStyle.font(19, weight: 400)).lineLimit(1)
            .padding(.horizontal, 16).frame(height: 47.84375)
            .foregroundStyle(ReferenceStyle.ink)
            .background(RoundedRectangle(cornerRadius: 12).fill(ReferenceStyle.background)
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(ReferenceStyle.border, lineWidth: 2)))
            .shadow(color: ReferenceStyle.border, radius: 0, y: configuration.isPressed ? 0 : 2)
            .frame(height: 51.84375, alignment: .top)
    }
}

struct SeedTileStyle: ButtonStyle {
    var selected = false
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.system(size: 17, weight: .medium, design: .rounded)).lineLimit(1).minimumScaleFactor(0.8)
            .padding(.horizontal, 12).padding(.vertical, 15).frame(maxWidth: .infinity)
            .foregroundStyle(enabled ? selected ? Color(red: 0, green: 0.6, blue: 0.8) : Color(white: 0.3) : Color.gray.opacity(0.6))
            .background {
                RoundedRectangle(cornerRadius: 12).fill(enabled ? selected ? Color.cyan.opacity(0.1) : .white : Color(white: 0.95))
                    .shadow(color: Color.black.opacity(0.15), radius: 0, y: configuration.isPressed ? 0 : 3)
            }
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(selected && enabled ? Color.cyan.opacity(0.5) : Color.gray.opacity(0.25), lineWidth: 2))
            .offset(y: configuration.isPressed ? 3 : 0)
    }
}

// Intrinsic word widths preserve the observed sentence order and wrap only
// when the available question width cannot hold the next tile.
private struct WordFlowLayout: Layout {
    var centered: Bool
    private func rows(_ subviews: Subviews, width: CGFloat) -> [[Int]] {
        var result: [[Int]] = [[]]; var used: CGFloat = 0
        for i in subviews.indices {
            let size = subviews[i].sizeThatFits(.unspecified)
            let gap: CGFloat = result.last!.isEmpty ? 0 : 8
            if used + gap + size.width > width && !result.last!.isEmpty { result.append([]); used = 0 }
            used += (result.last!.isEmpty ? 0 : 8) + size.width; result[result.count - 1].append(i)
        }
        return result.filter { !$0.isEmpty }
    }
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? 600
        let groups = rows(subviews, width: width)
        let heights = groups.map { row in row.map { subviews[$0].sizeThatFits(.unspecified).height }.max() ?? 0 }
        return CGSize(width: width, height: heights.reduce(0, +) + CGFloat(max(0, groups.count - 1)) * 8)
    }
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var y = bounds.minY
        for row in rows(subviews, width: bounds.width) {
            let sizes = row.map { subviews[$0].sizeThatFits(.unspecified) }
            let width = sizes.reduce(CGFloat(0)) { $0 + $1.width } + CGFloat(max(0, row.count - 1)) * 8
            var x = bounds.minX + (centered ? max(0, (bounds.width - width) / 2) : 0)
            for (i, size) in zip(row, sizes) {
                subviews[i].place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(size))
                x += size.width + 8
            }
            y += (sizes.map(\.height).max() ?? 0) + 8
        }
    }
}

struct AudioPairButtonStyle: ButtonStyle {
    var matched: Bool
    var selected: Bool
    var incorrect: Bool
    func makeBody(configuration: Configuration) -> some View {
        let color: Color = incorrect ? .red : matched ? Color(red: 0.35, green: 0.7, blue: 0) : selected ? ReferenceStyle.blue : Color.gray
        configuration.label.foregroundStyle(color)
            .background(RoundedRectangle(cornerRadius: 12).fill(incorrect ? Color.red.opacity(0.12) : matched ? Color.green.opacity(0.12) : selected ? Color.cyan.opacity(0.1) : .white))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(color.opacity(0.3), lineWidth: 2))
            .offset(y: configuration.isPressed ? 2 : 0)
    }
}

struct ReferenceSkipButton: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(ReferenceStyle.font(17, bold: true))
            .foregroundStyle(ReferenceStyle.disclosureInk)
            .frame(width: 150, height: 46)
            .background(RoundedRectangle(cornerRadius: 16).fill(.white)
                .shadow(color: ReferenceStyle.border, radius: 0, y: configuration.isPressed ? 0 : 4))
            .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2))
            .offset(y: configuration.isPressed ? 4 : 0)
            .frame(width: 150, height: 50, alignment: .top)
            .contentShape(Rectangle())
    }
}
