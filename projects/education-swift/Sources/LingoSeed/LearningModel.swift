import Foundation
import Observation
import LearningCore

@MainActor @Observable final class LearningModel {
    let course: Course
    let store: ProgressStore
    var progress: LearningProgress
    var lesson: Lesson?
    enum SessionKind { case course, pronunciation, generalPractice, sectionPlacement, unitPlacement, observedCourse }
    var sessionKind = SessionKind.course
    var isPronunciationPractice: Bool { sessionKind == .pronunciation }
    var sectionPlacementStage:Int?
    var sectionPlacementEntry=false
    var isSectionPlacement:Bool {sessionKind == .sectionPlacement}
    var unitPlacementNumber:Int?
    var unitPlacementEntry=false
    var isUnitPlacement:Bool {sessionKind == .unitPlacement}
    var isPlacement:Bool {isSectionPlacement || isUnitPlacement}
    var isObservedCourse:Bool {sessionKind == .observedCourse}
    var isReferenceSession:Bool {isGeneralPractice || isPlacement || isObservedCourse}
    var placementOutcome: ObservedPlacementOutcome? { progress.placementOutcomes[course.id] }
    var isGeneralPractice: Bool { sessionKind == .generalPractice }
    var pronunciationExitNeedsConfirmation: Bool {
        guard sessionKind != .course, let lesson else { return false }
        // Source probes: all-wrong exits directly; one correct then a wrong
        // still confirms. Use earned answers, not attempts or current streak.
        if lesson.reviewing || lesson.complete { return lesson.definition.questions.count > lesson.review.count }
        return lesson.feedback == true || lesson.position > lesson.review.filter { $0 < lesson.position }.count
    }
    var confirmingExit = false
    var feedbackDifficulty: String?
    var reportingQuestion = false
    var selectedReportReasons = Set<Int>()
    func rateDifficulty(_ value: String) {
        guard lesson?.feedback != nil || lesson?.listeningDeclined == true || lesson?.speechDeclined == true else { return }
        feedbackDifficulty = feedbackDifficulty == value ? nil : value
    }
    func openQuestionReport() { selectedReportReasons = []; reportingQuestion = true }
    func closeQuestionReport() { reportingQuestion = false; selectedReportReasons = [] }
    var entryPending = false
    var settlement: SettlementFlow?
    var error: String?
    var destination = "Learn"
    var preferences = LearningPreferences()
    private var preferencesURL: URL { store.url.appendingPathExtension("preferences.json") }
    func savePreferences() {
        audio.effectsEnabled = preferences.soundEffects
        do {
            try FileManager.default.createDirectory(at: preferencesURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            try JSONEncoder().encode(preferences).write(to: preferencesURL, options: .atomic)
        } catch { self.error = "Preferences could not be saved." }
    }
    let audio = LearningAudio(resourceURL: { Bundle.module.url(forResource: $0, withExtension: nil, subdirectory: "Reference") })
    let speechCapture = LearningSpeech()
    func startSpeech() { guard lesson?.deferredSpeech != nil, lesson?.speechDeclined == false else { return }; Task { await speechCapture.start() } }
    var muted = false
    private var audioPreferencesURL: URL { store.url.appendingPathExtension("audio.json") }
    func toggleMute() {
        muted.toggle(); audio.muted = muted
        do {
            try FileManager.default.createDirectory(at: audioPreferencesURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            try JSONEncoder().encode(muted).write(to: audioPreferencesURL, options: .atomic)
        } catch { self.error = "Sound preference could not be saved." }
    }
    func choose(_ id: String) {
        guard let lesson, lesson.feedback == nil, let option = lesson.question.options.first(where: { $0.id == id }) else { return }
        self.lesson?.choose(id)
        if (!isReferenceSession || lesson.question.sourceType != "assist"), course.interfaceLanguage != "zh" || option.audioResource != nil {
            audio.speak(option.text, language: course.speechLanguage, resource: option.audioResource)
        }
    }
    func addWord(_ id: String) {
        guard let word = lesson?.question.words.first(where: { $0.id == id }) else { return }
        lesson?.addWord(id)
        if let resource = word.audioResource { audio.speak(word.text, language: course.speechLanguage, resource: resource) }
        else if !isReferenceSession { audio.play(.tap) }
    }
    func toggleInputMode() { lesson?.toggleInputMode() }
    func enterText(_ text: String) { lesson?.enterText(text) }
    func removeWord(_ id: String) { lesson?.removeWord(id); if !isReferenceSession { audio.play(.tap) } }
    func match(_ id: String, left: Bool) {
        let previous = lesson?.feedback
        let matchedBefore = lesson?.matchedPairs.count ?? 0
        let mistakesBefore = lesson?.mistakesMade ?? 0
        if left { lesson?.matchLeft(id) } else { lesson?.matchRight(id) }
        if isGeneralPractice, let lesson {
            if left, let pair = lesson.question.pairs.first(where: { $0.id == id }), let resource = pair.audioResource {
                audio.speak(pair.right, language: course.speechLanguage, resource: resource)
            }
            if lesson.matchedPairs.count > matchedBefore, let resources = lesson.question.matchedAudioResources, resources.indices.contains(matchedBefore) {
                audio.playReferenceEffect(resources[matchedBefore])
            }
            if previous == nil && lesson.feedback == true { audio.playReferenceEffect(lesson.question.correctFeedbackAudioResource) }
            if lesson.mistakesMade > mistakesBefore { audio.playReferenceEffect(lesson.question.incorrectFeedbackAudioResource) }
        } else if isReferenceSession, let lesson {
            let playSpeech = lesson.question.sourceType == "listenMatch" ? left : !left
            if playSpeech, let pair = lesson.question.pairs.first(where: { $0.id == id }), let resource = pair.audioResource {
                audio.speak(pair.right, language: course.speechLanguage, resource: resource)
            }
            if lesson.matchedPairs.count > matchedBefore, let resources = lesson.question.matchedAudioResources, resources.indices.contains(matchedBefore) {
                audio.playReferenceEffect(resources[matchedBefore])
            }
            if previous == nil && lesson.feedback == true {
                audio.playReferenceEffect(lesson.question.correctFeedbackAudioResource, volume: lesson.question.correctFeedbackAudioVolume ?? 1)
            }
            if lesson.mistakesMade > mistakesBefore {
                audio.playReferenceEffect(lesson.question.incorrectFeedbackAudioResource, volume: lesson.question.incorrectFeedbackAudioVolume ?? 1)
            }
        } else if isPronunciationPractice {
            if left, let pair = lesson?.question.pairs.first(where: { $0.id == id }), let resource = pair.audioResource {
                audio.speak(pair.right, language: course.speechLanguage, resource: resource)
            }
            // Missing original speech is left unavailable, never replaced by a synthetic tap or voice.
        } else if (lesson?.question.sourceType == "listenMatch" ? left : !left), let pair = lesson?.question.pairs.first(where: { $0.id == id }), let resource = pair.audioResource {
            audio.speak(pair.right, language: course.speechLanguage, resource: resource)
        } else {
            audio.play(previous == nil && lesson?.feedback == true ? .correct : (lesson?.matchingHint != nil || lesson?.incorrectMatch != nil) ? .incorrect : .tap)
        }
        if (sessionKind == .course || isObservedCourse), let hearts = lesson?.hearts, hearts != progress.hearts { progress.hearts = hearts; save() }
    }
    func playQuestion(slow: Bool = false, practicePart: Int = 0) {
        if let speech = lesson?.deferredSpeech {
            audio.speak(speech.phrase, language: course.speechLanguage, resource: speech.audioResource)
            return
        }
        guard let question = lesson?.question else { return }
        if let resources = question.practiceAudioResources, resources.indices.contains(practicePart) {
            audio.speak(question.prompt, resource: resources[practicePart]); return
        }
        audio.speak(question.hint ?? question.prompt, language: question.sourceLanguage ?? course.speechLanguage, resource: slow ? question.slowAudioResource : question.audioResource)
    }
    func playExample() {
        guard let question = lesson?.question, let example = question.example, let resource = question.exampleAudioResource else { return }
        audio.speak(example, language: course.speechLanguage, resource: resource)
    }
    func pronounce() {
        guard let lesson else { return }
        let option = lesson.question.options.first { $0.id == lesson.selected }
        let selected = option?.text
        let phrase = selected ?? lesson.question.hint ?? lesson.question.prompt
        audio.speak(phrase, language: selected != nil ? course.speechLanguage : (lesson.question.sourceLanguage ?? (lesson.question.kind == .wordTiles ? course.speechLanguage : "en-US")), resource: option?.audioResource ?? lesson.question.audioResource)
    }
    init(course: Course, store: ProgressStore) throws {
        self.course = course; self.store = store; progress = try store.load()
        if let data = try? Data(contentsOf: preferencesURL), let saved = try? JSONDecoder().decode(LearningPreferences.self, from: data) { preferences = saved }
        audio.effectsEnabled = preferences.soundEffects
        if let data = try? Data(contentsOf: audioPreferencesURL), let saved = try? JSONDecoder().decode(Bool.self, from: data) { muted = saved; audio.muted = saved }
    }
    func beginPronunciation() {
        guard let url = Bundle.module.url(forResource: "pronunciation-practice", withExtension: "json", subdirectory: "Reference"),
              let data = try? Data(contentsOf: url) else { error = "无法打开练习。"; return }
        let practice: Course
        do { practice = try JSONDecoder().decode(Course.self, from: data) }
        catch { self.error = "无法打开练习。"; NSLog("Practice definition decode failed: %@", String(describing: error)); return }
        let index = progress.completedCount(practice)
        guard practice.lessons.indices.contains(index) else { error = "无法加载下一次练习。"; return }
        sessionKind = .pronunciation
        lesson = Lesson(course: practice, lessonIndex: index, hearts: progress.hearts)
        settlement = nil; entryPending = false; confirmingExit = false
        feedbackDifficulty = nil; closeQuestionReport(); playQuestion()
    }
    func begin(_ index: Int) {
        sessionKind = .course
        guard progress.isUnlocked(course, index: index) else { return }
        lesson = Lesson(course: course, lessonIndex: index, hearts: progress.hearts)
        settlement = nil
        feedbackDifficulty = nil; closeQuestionReport()
        confirmingExit = false
        entryPending = course.lessons[index].entry != nil
        audio.play(.tap)
        playAutomaticPrompt()
    }
    func prepareSectionPlacement(_ stage:Int) {
        sectionPlacementStage=stage;sectionPlacementEntry=true;error=nil
    }
    func beginSectionPlacement() {
        guard let stage=sectionPlacementStage,
              let url=Bundle.module.url(forResource:"section-placement-\(stage)",withExtension:"json",subdirectory:"Reference") else {error="无法载入阶段测试。";return}
        do {
            let test=try Course.readFixture(url)
            sessionKind = .sectionPlacement;sectionPlacementEntry=false
            lesson=Lesson(course:test,hearts:3)
            settlement=nil;entryPending=false;confirmingExit=false
            feedbackDifficulty=nil;closeQuestionReport();playAutomaticPrompt()
        } catch {self.error="无法载入阶段测试。"}
    }
    func prepareUnitPlacement(_ unit:Int) {
        unitPlacementNumber=unit;unitPlacementEntry=true;error=nil
    }
    func beginUnitPlacement() {
        guard let unit=unitPlacementNumber,
              let url=Bundle.module.url(forResource:"unit-placement-\(unit)",withExtension:"json",subdirectory:"Reference") else {error="无法载入单元测试。";return}
        do {
            let test=try Course.readFixture(url)
            sessionKind = .unitPlacement;unitPlacementEntry=false
            lesson=Lesson(course:test,hearts:5)
            settlement=nil;entryPending=false;confirmingExit=false
            feedbackDifficulty=nil;closeQuestionReport();playAutomaticPrompt()
        } catch {self.error="无法载入单元测试。"}
    }
    var unitTwelveCompletedLessons:Int {
        (progress.completedLessons["duolingo-en-zh-unit12-home-instance",default:[]].contains("unit12-home-1") ? 1 : 0) +
        (progress.completedLessons["duolingo-en-zh-unit12-home2-instance",default:[]].contains("unit12-home-2") ? 1 : 0) +
        (progress.completedLessons["duolingo-en-zh-unit12-home3-instance",default:[]].contains("unit12-home-3") ? 1 : 0) +
        (progress.completedLessons["duolingo-en-zh-unit12-home4-instance",default:[]].contains("unit12-home-4") ? 1 : 0)
    }
    func dismissPronunciationCoach() { preferences.pronunciationCoach="dismissed";savePreferences() }
    func beginStageTwoLesson() {
        guard let url=Bundle.module.url(forResource:placementOutcome?.activeUnit == 12 ? "unit12-home-\(unitTwelveCompletedLessons+1)" : "stage2-grocery-1",withExtension:"json",subdirectory:"Reference") else {
            error="无法载入这个单元。";return
        }
        do {
            let observed=try Course.readFixture(url)
            sessionKind = .observedCourse
            lesson=Lesson(course:observed,hearts:progress.hearts)
            settlement=nil;entryPending=false;confirmingExit=false
            feedbackDifficulty=nil;closeQuestionReport();playAutomaticPrompt()
        } catch {self.error="无法载入这个单元。"}
    }
    func beginGeneralPractice() {
        let explicit = CommandLine.arguments.firstIndex(of: "--general-practice-fixture").flatMap { index in
            index + 1 < CommandLine.arguments.count ? URL(fileURLWithPath: CommandLine.arguments[index + 1]) : nil
        }
        guard let url = explicit ?? Bundle.module.url(forResource: "general-practice", withExtension: "json", subdirectory: "Reference") else { error = "无法打开练习。"; return }
        do {
            let practice = try Course.readFixture(url)
            sessionKind = .generalPractice
            lesson = Lesson(course: practice, hearts: progress.hearts)
            settlement = nil; entryPending = false; confirmingExit = false
            feedbackDifficulty = nil; closeQuestionReport(); playAutomaticPrompt()
        } catch { self.error = "无法打开练习。"; NSLog("General practice decode failed: %@", String(describing: error)) }
    }
    func acceptEntry() { entryPending = false; playAutomaticPrompt() }
    func declineSpeech() { speechCapture.cancel(); lesson?.declineSpeech() }
    func declineListening() { lesson?.declineListening() }
    private func playAutomaticPrompt() {
        guard !entryPending, lesson?.interlude == nil, lesson?.deferredSpeech == nil, let question = lesson?.question,
              ["translate", "listenTap", "dialogue", "orderTapComplete", "selectPronunciation", "sameDifferent"].contains(question.sourceType ?? "") || isReferenceSession && ["listen", "listenComplete", "listenIsolation"].contains(question.sourceType ?? ""),
              course.interfaceLanguage != "zh" || question.audioResource != nil else { return }
        playQuestion()
    }
    func skip() {
        lesson?.skip()
        // No source evidence yet for a skip effect; do not substitute incorrect audio.
    }
    func submit() {
        guard lesson?.canSubmit == true, lesson?.feedback == nil else { return }
        lesson?.submit()
        if let lesson, isReferenceSession || (lesson.feedback == true ? lesson.question.correctFeedbackAudioResource : lesson.question.incorrectFeedbackAudioResource) != nil {
            audio.playReferenceEffect(lesson.feedback == true ? lesson.question.correctFeedbackAudioResource : lesson.question.incorrectFeedbackAudioResource,volume:lesson.feedback == true ? lesson.question.correctFeedbackAudioVolume : lesson.question.incorrectFeedbackAudioVolume)
            if isReferenceSession && lesson.question.sourceType == "assist", let correct = lesson.question.options.first(where: { $0.id == lesson.question.answer }), let resource = correct.audioResource {
                audio.speak(correct.text, language: course.speechLanguage, resource: resource)
            }
        } else { audio.play(lesson?.feedback == true ? .correct : .incorrect) }
        if (sessionKind == .course || isObservedCourse), let hearts = lesson?.hearts, hearts != progress.hearts {
            progress.hearts = hearts
            save()
        }
    }
    func advance() {
        guard lesson?.feedback != nil || lesson?.interlude != nil || lesson?.speechDeclined == true || lesson?.listeningDeclined == true else { return }
        let previousQuestion = lesson?.question.id
        let wasInterlude = lesson?.interlude != nil
        let wasDeferred = lesson?.deferredSpeech != nil
        lesson?.advance()
        if lesson?.question.id != previousQuestion { feedbackDifficulty = nil; closeQuestionReport() }
        if let lesson, !lesson.complete, lesson.interlude == nil, (wasInterlude || wasDeferred || lesson.question.id != previousQuestion) { playAutomaticPrompt() }
        if let lesson, lesson.complete {
            if let resource=lesson.definition.completionAudioResource {
                audio.playReferenceEffect(resource,volume:lesson.definition.completionAudioVolume)
            } else if !isReferenceSession { audio.play(.complete) }
            if let pages = lesson.definition.settlement { settlement = SettlementFlow(pages: pages) }
            if sessionKind != .course {
                // Track observed sessions separately; this finite evidence set is not the full pronunciation course.
                progress.completedLessons[lesson.course.id, default: []].insert(lesson.definition.id)
                save()
            } else { progress.markCompleted(course, index: lesson.lessonIndex); save() }
        }
    }
    func advanceSettlement() {
        if isReferenceSession, settlement?.current?.kind == "practice_heart" {
            progress.hearts += 1; save()
        }
        settlement?.advance()
        if settlement?.current == nil {
            if isPlacement, let lesson, lesson.complete,
               let outcome=lesson.definition.placementOutcome,
               lesson.mistakesMade == outcome.observedMistakes {
                progress.placementOutcomes[course.id]=outcome
                save()
            }
            if let lesson, lesson.complete, lesson.mistakesMade == 0,
               let snapshot=lesson.definition.observedHomeSnapshot,
               var outcome=progress.placementOutcomes[course.id] {
                outcome.homeSnapshot=snapshot
                progress.placementOutcomes[course.id]=outcome
                save()
            }
            if lesson?.definition.postHomeCoach == "pronunciation", preferences.pronunciationCoach != "dismissed" {
                preferences.pronunciationCoach="pending";savePreferences()
            }
            discardAttempt()
        }
    }
    var homeGems: Int {
        let completed=progress.completedCount(course)
        let snapshot=placementOutcome?.homeSnapshot ?? course.home?.progressSnapshots?.first {$0.completedLessons == completed}
        let base=placementOutcome?.homeSnapshot.gems ?? (progress.isPathChestOpened(course) ? course.home?.pathChest?.afterGems ?? 0 : snapshot?.gems ?? (500+completed*5))
        return base-progress.spentGems
    }
    func refillHearts() {
        if progress.purchaseHeartRefill(availableGems:homeGems) {save()}
    }
    func openPathChest() {
        if progress.openPathChest(course) { save() }
    }
    func save() {
        do { try store.save(progress); error = nil }
        catch { self.error = "Progress could not be saved. Please try again." }
    }
    func discardAttempt() { speechCapture.cancel(); if isSectionPlacement {destination="Sections"}; sectionPlacementEntry=false; unitPlacementEntry=false; if isUnitPlacement {destination="Learn"}; if isPronunciationPractice { destination = "Pronunciation" }; if isGeneralPractice || isObservedCourse { destination = "Learn" }; sessionKind = .course; lesson = nil; confirmingExit = false; entryPending = false; settlement = nil }
}
