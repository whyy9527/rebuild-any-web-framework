import Foundation
import LearningCore

// Executable business checks for a CLT-only host without XCTest/Swift Testing.
enum CheckFailure: Error { case failed(String) }
func check(_ condition: @autoclosure () throws -> Bool, _ message: String) throws {
    if try !condition() { throw CheckFailure.failed(message) }
}
func course(fixture: String = "fixture-v1.json") throws -> Course {
    let projects = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    return try Course.readFixture(projects.appendingPathComponent("duolingo-web/" + fixture))
}
func mistakeReview() throws {
    let course = try course()
    var lesson = Lesson(course: course)
    lesson.submit()
    try check(lesson.feedback == nil, "Empty answer was submitted")
    lesson.choose(course.questions[0].options.first { $0.id != course.questions[0].answer }!.id)
    lesson.submit()
    try check(lesson.hearts == 4, "Wrong answer must consume one heart")
    lesson.advance()
    lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance()
    try check(!lesson.complete && lesson.reviewing, "Mistakes must be reviewed before completion")
    try check(lesson.question.id == course.questions[0].id, "Review must revisit missed question")
    lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance()
    try check(lesson.complete, "Corrected mistake must allow completion")
    print("PASS mistake review and empty-answer boundary")
}
func persistence() throws {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: directory) }
    let store = ProgressStore(url: directory.appendingPathComponent("progress.json"))
    var progress = try store.load()
    progress.completedCourses.insert("original-course")
    try store.save(progress)
    try check(try ProgressStore(url: store.url).load() == progress, "Completed progress lost on reopening")
    for content in ["broken", "{}", "{\"completedCourses\":null}", "{\"completedCourses\":[],\"hearts\":-1}"] {
        try Data(content.utf8).write(to: store.url)
        var rejected = false
        do { _ = try store.load() } catch { rejected = true }
        try check(rejected, "Corrupt progress was silently accepted: " + content)
        try check(try String(contentsOf: store.url, encoding: .utf8) == content, "Corrupt progress was overwritten")
    }
    print("PASS persistence and corrupt-data preservation")
}
func wordTilesAndReview() throws {
    let course = try course(fixture: "fixture-v2.json")
    var lesson = Lesson(course: course, lessonIndex: 1)
    lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance()
    let missed = lesson.question.id
    let words = lesson.question.answerWords
    lesson.addWord(words[0])
    try check(lesson.canSubmit, "A partial phrase must be submittable")
    lesson.removeWord(words[0])
    try check(!lesson.canSubmit && lesson.selectedWords.isEmpty, "Undo must restore the empty-answer boundary")
    for word in words.reversed() { lesson.addWord(word) }
    lesson.submit()
    try check(lesson.feedback == false && lesson.hearts == 4, "Reversed phrase must consume one heart")
    lesson.removeWord(words[0])
    try check(lesson.selectedWords.count == 2, "Submitted words must remain locked")
    lesson.advance()
    for word in lesson.question.answerWords { lesson.addWord(word) }
    lesson.submit(); lesson.advance()
    try check(lesson.reviewing && lesson.question.id == missed && lesson.selectedWords.isEmpty, "Review must restore the missed phrase without its old selection")
    for word in lesson.question.answerWords { lesson.addWord(word) }
    lesson.submit(); lesson.advance()
    try check(lesson.complete, "Corrected phrase must permit completion")
    print("PASS word order, undo, locking and mistake review")
}
func matching() throws {
    let course = try course(fixture: "fixture-v2.json")
    var lesson = Lesson(course: course)
    for _ in 0..<2 { lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance() }
    let pairs = lesson.question.pairs
    lesson.matchLeft(pairs[0].id); lesson.matchRight(pairs[1].id)
    try check(lesson.matchedPairs.isEmpty && lesson.hearts == 5 && lesson.matchingHint != nil, "Wrong-pair retry decision was not preserved")
    for pair in pairs.dropLast() { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
    try check(lesson.feedback == nil && !lesson.complete, "Matching finished before the last pair")
    lesson.matchLeft(pairs.last!.id); lesson.matchRight(pairs.last!.id)
    try check(lesson.feedback == true && lesson.matchedPairs.count == pairs.count, "All pairs must produce positive feedback")
    lesson.advance()
    try check(lesson.complete, "A completed matching activity must finish this lesson")
    print("PASS matching completion and explicit wrong-pair retry decision")
}
func unlocksAndLegacy() throws {
    let course = try course(fixture: "fixture-v2.json")
    var progress = LearningProgress()
    try check(!progress.isUnlocked(course, index: 1), "Later lesson started before its prerequisite")
    try check(!progress.markCompleted(course, index: 1), "Locked lesson was credited")
    try check(progress.markCompleted(course, index: 0), "First lesson could not be recorded")
    try check(progress.completedCount(course) == 1 && progress.isUnlocked(course, index: 1), "Completion did not unlock the next lesson")
    progress.hearts = 4
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: directory) }
    let store = ProgressStore(url: directory.appendingPathComponent("progress.json"))
    try store.save(progress)
    let reopened = try store.load()
    try check(reopened == progress && reopened.completedCount(course) == 1 && reopened.hearts == 4, "Lesson and heart progress did not survive reopening")
    let legacy = try JSONDecoder().decode(LearningProgress.self, from: Data("{\"completedCourses\":[\"everyday-english\"]}".utf8))
    try check(legacy.completedCount(try legacyCourse()) == 1, "Old single-lesson progress was lost")
    try check(legacy.completedCount(course) == 0, "Old course credit silently completed new lesson content")
    print("PASS prerequisite unlock, progress reopening and legacy-content boundary")
}
func observedInterludes() throws {
    let source = try course(fixture: "fixture-reference-v6.json")
    var lesson = Lesson(course: source, lessonIndex: 2)
    var seen = [String]()
    while !lesson.complete {
        if let interlude = lesson.interlude {
            seen.append(interlude.text)
            let questionID = lesson.question.id
            lesson.choose(lesson.question.answer); lesson.submit()
            try check(lesson.selected == nil && lesson.feedback == nil && !lesson.canSubmit, "Interlude allowed answering the hidden next question")
            lesson.advance()
            try check(lesson.interlude == nil && lesson.question.id == questionID, "Dismissing interlude skipped the next question")
            continue
        }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer); lesson.submit()
        case .wordTiles:
            for id in lesson.question.answerWords { lesson.addWord(id) }; lesson.submit()
        case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
        case .matching:
            for pair in lesson.question.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
        }
        try check(lesson.feedback == true, "Observed source answer failed")
        lesson.advance()
    }
    try check(seen == ["Cool! 5 in a row!", "Nice! Practice always pays off."], "Observed interludes missing or repeated")
    print("PASS observed interludes block hidden input and resume without losing a question; other trajectories unverified")
}
func actualEnglishTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v1.json")
    try check(source.speechLanguage == "en" && source.interfaceLanguage == "zh", "Real course language metadata lost")
    try check(source.questions.count == 15, "Actual English question count changed")
    let listening = source.questions.filter { $0.sourceType == "listenTap" }
    let dialogues = source.questions.filter { $0.sourceType == "dialogue" }
    try check(listening.count == 2 && listening.allSatisfy { $0.audioResource != nil && $0.slowAudioResource != nil }, "Observed listening clips missing")
    try check(dialogues.count == 2 && dialogues.allSatisfy { $0.dialogueAvatars?.count == 2 && $0.hint != nil && $0.audioResource != nil }, "Dialogue presentation data missing")
    try check(source.questions[0].options.allSatisfy { $0.imageResource != nil }, "Per-option source artwork lost")
    var lesson = Lesson(course: source)
    let first = lesson.question.id
    lesson.choose(lesson.question.options.first { $0.text == "sugar" }!.id); lesson.submit()
    try check(lesson.hearts == 4 && lesson.feedback == false, "Observed first mistake must consume one heart")
    lesson.advance()
    var accepted = 0
    while !lesson.reviewing && !lesson.complete {
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer); lesson.submit()
        case .wordTiles:
            for id in lesson.question.answerWords { lesson.addWord(id) }; lesson.submit()
        case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
        case .matching:
            for pair in lesson.question.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
        }
        try check(lesson.feedback == true, "Observed English answer rejected")
        accepted += 1; lesson.advance()
    }
    try check(accepted == 14 && lesson.reviewing && lesson.question.id == first && !lesson.complete, "Actual mistake review trajectory lost")
    lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance()
    try check(lesson.complete && lesson.hearts == 4, "Correct retry must complete without restoring lost heart")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "English presentation metadata failed Codable round-trip")
    print("PASS actual en/zh 15-question wrong-first/review trajectory and presentation metadata; frontend equivalence pending")
}
func actualEnglishSecondTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v2.json")
    try check(source.lessons.count == 2 && source.pathNodes?.first?.lessonIDs == ["lesson-1", "lesson-2"], "Second lesson lost its first-node membership")
    let questions = source.lessons[1].questions
    try check(questions.count == 15 && questions.suffix(3).allSatisfy { $0.sourceType == "translate" && $0.indicator == "挑战题" }, "Actual adaptive tail replaced by unvisited API tail")
    let fill = questions[4]
    try check(fill.sourceType == "orderTapComplete" && fill.example == "Tea with sugar." && fill.completionPrefix == "Coffee " && fill.completionSuffix == ".", "Observed fill-in context missing")
    var progress = LearningProgress()
    try check(!progress.isUnlocked(source, index: 1), "Second lesson unlocked before first completion")
    progress.markCompleted(source, index: 0)
    try check(progress.isUnlocked(source, index: 1), "First completion did not unlock actual second lesson")
    var lesson = Lesson(course: source, lessonIndex: 1, hearts: 4)
    var seen = [String](); var count = 0
    while !lesson.complete {
        if let interlude = lesson.interlude { seen.append(interlude.text); lesson.advance(); continue }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer); lesson.submit()
        case .wordTiles:
            if lesson.question.sourceType == "orderTapComplete" {
                let first = lesson.question.answerWords[0]
                lesson.addWord(first); lesson.removeWord(first)
                try check(lesson.selectedWords.isEmpty && !lesson.canSubmit, "Fill undo lost empty-answer boundary")
            }
            for id in lesson.question.answerWords { lesson.addWord(id) }; lesson.submit()
        case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
        case .matching: throw CheckFailure.failed("Unvisited API matching question entered actual second trajectory")
        }
        try check(lesson.feedback == true, "Source accepted second-lesson answer rejected")
        count += 1; lesson.advance()
    }
    try check(count == 15 && lesson.hearts == 4 && seen == ["你的辛勤付出得到了回报！", "你是最棒的！", "哎哟不错哦！要不要玩点刺激的？"], "Second trajectory or interludes lost")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Second-lesson presentation lost during round-trip")
    print("PASS actual second lesson, fill undo, adaptive tail, three interludes and first-node unlock; frontend equivalence pending")
}
func actualEnglishThirdTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v3.json")
    try check(source.lessons.count == 3 && source.pathNodes?.first?.lessonIDs == ["lesson-1", "lesson-2", "lesson-3"], "Actual third lesson not connected to first node")
    var progress = LearningProgress()
    progress.markCompleted(source, index: 0)
    try check(!progress.isUnlocked(source, index: 2), "Third lesson unlocked without second completion")
    progress.markCompleted(source, index: 1)
    try check(progress.isUnlocked(source, index: 2), "Third lesson unavailable after first two completions")
    var lesson = Lesson(course: source, lessonIndex: 2, hearts: 4)
    var count = 0; var interludes = [String]()
    while !lesson.complete {
        if let interlude = lesson.interlude { interludes.append(interlude.text); lesson.advance(); continue }
        if lesson.question.id == "en-zh-l3-q9" {
            let duplicates = lesson.question.words.filter { $0.text == "不要" }.map(\.id)
            try check(duplicates.count == 2 && Set(duplicates).count == 2, "Repeated visible words collapsed")
            lesson.addWord(duplicates[0]); lesson.addWord(duplicates[0])
            try check(lesson.selectedWords.count == 1, "A tile occurrence was reused")
            lesson.addWord(duplicates[1]); lesson.removeWord(duplicates[0])
            try check(lesson.selectedWords == [duplicates[1]], "Undo removed both equal-text tiles")
            lesson.removeWord(duplicates[1])
            try check(!lesson.canSubmit, "Removing both repeated tiles left a submittable answer")
            var missing = lesson
            for id in lesson.question.answerWords where id != duplicates[1] { missing.addWord(id) }
            missing.submit()
            try check(missing.feedback == false, "Missing a repeated word was accepted")
            for id in lesson.question.answerWords {
                lesson.addWord(id == duplicates[0] ? duplicates[1] : id == duplicates[1] ? duplicates[0] : id)
            }
            lesson.submit()
        } else {
            switch lesson.question.kind {
            case .choice: lesson.choose(lesson.question.answer); lesson.submit()
            case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }; lesson.submit()
            case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
            case .matching: throw CheckFailure.failed("Unobserved matching tail entered third actual trajectory")
            }
        }
        try check(lesson.feedback == true, "Source accepted third-lesson word sequence rejected")
        count += 1; lesson.advance()
    }
    try check(count == 15 && lesson.hearts == 4 && interludes.count == 3, "Third accepted trajectory or interludes lost")
    progress.completedCourses.insert(source.id) // Old partial-fixture credit must be repaired.
    progress.markCompleted(source, index: 2)
    try check(progress.completedCount(source) == 3 && !progress.completedCourses.contains(source.id), "Observed three-lesson subset incorrectly credited the whole uncompiled path")
    try check(source.lessons[2].questions.suffix(3).allSatisfy { $0.indicator == "挑战题" && $0.sourceLanguage == "zh" }, "Static API tail substituted for actual hard questions")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Third-course occurrence identities lost during round-trip")
    print("PASS actual third lesson, duplicate-tile independence/undo/multiplicity/equivalent sequence, three interludes and unlock; full source grader unverified")
}
func actualEnglishFourthTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v4.json")
    try check(source.lessons.map { $0.questions.count } == [15,15,15,12], "Fourth source length replaced with assumed 15 questions")
    try check(source.lessons[3].entry?.startLabel == "开始挑战 +20 经验", "Observed challenge entry lost")
    var progress = LearningProgress()
    for index in 0..<3 { progress.markCompleted(source, index: index) }
    try check(progress.isUnlocked(source, index: 3), "Fourth unavailable after actual first three")
    var lesson = Lesson(course: source, lessonIndex: 3, hearts: 4)
    try check(lesson.interlude?.id == "en-zh-l4-review-intro" && !lesson.canSubmit, "Initial review intro skipped")
    lesson.choose(lesson.question.answer)
    try check(lesson.selected == nil, "Hidden question accepted input during introduction")
    var count = 0; var interludes = [String]()
    while !lesson.complete {
        if let interlude = lesson.interlude { interludes.append(interlude.id); lesson.advance(); continue }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer)
        case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }
        case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
        case .matching: throw CheckFailure.failed("Fourth actual trajectory has no matching task")
        }
        lesson.submit(); try check(lesson.feedback == true, "Actual accepted fourth answer rejected")
        count += 1; lesson.advance()
    }
    try check(count == 12 && lesson.hearts == 4 && interludes == ["en-zh-l4-review-intro", "en-zh-l4-hard-intro"], "Fourth trajectory or introduction ordering changed")
    progress.markCompleted(source, index: 3)
    try check(!progress.completedCourses.contains(source.id), "Uncompiled next path falsely credited")
    let afterThird = source.home?.progressSnapshots?.first { $0.completedLessons == 3 }
    try check(afterThird?.gems == 505 && afterThird?.leagueTitle == "青铜等级", "Observed home snapshot lost")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Fourth presentation round-trip failed")
    print("PASS actual fourth 12-question trajectory, initial input boundary, hard interlude, home snapshot and partial path credit; frontend pending")
}
func actualEnglishSettlement() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v5.json")
    let pages = source.lessons[3].settlement!
    var flow = SettlementFlow(pages: pages)
    var ids = [String]()
    while let page = flow.current { ids.append(page.id); flow.advance() }
    try check(ids == ["en-zh-l4-complete", "en-zh-l4-score", "en-zh-l4-streak", "en-zh-l4-xp-boost", "en-zh-l4-legendary", "en-zh-l4-profile"], "Observed settlement ordering changed")
    flow.advance(); try check(flow.current == nil && flow.position == 6, "Finished settlement restarted")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Settlement metadata lost in round-trip")
    var lesson = Lesson(course: source, hearts: 4)
    lesson.choose(lesson.question.options.first { $0.id != lesson.question.answer }!.id); lesson.submit()
    try check(lesson.mistakesMade == 1, "Incorrect attempt lost, potentially rendering false 100 percent")
    print("PASS source six-stage settlement sequence, terminal behavior, metadata and incorrect-attempt accounting; frontend/secondary branches pending")
}
func actualEnglishInputStates() throws {
    let source = try course(fixture: "fixture-english-input-probe.json")
    var lesson = Lesson(course: source, hearts: 4)
    try check(!lesson.canSubmit, "Empty typed input submitted")
    lesson.enterText("Te"); try check(lesson.canSubmit, "Nonempty input cannot submit")
    lesson.enterText(""); try check(!lesson.canSubmit, "Clearing typed input leaves check enabled")
    lesson.enterText("Tea"); lesson.submit()
    try check(lesson.feedback == true && lesson.hearts == 4, "Source accepted Tea rejected")
    lesson.enterText("changed"); try check(lesson.enteredText == "Tea", "Submitted input edited")
    lesson.advance(); try check(lesson.enteredText.isEmpty && !lesson.canSubmit, "Input leaked into next state")
    try check(lesson.question.completionPrefix == "I'd like " && lesson.question.completionSuffix == ".", "Source fixed sentence lost")
    lesson.enterText("tea"); lesson.submit(); lesson.advance()
    try check(lesson.complete, "Source accepted reverse input rejected")
    var progress = LearningProgress(); progress.markCompleted(source, index: 0)
    try check(!progress.completedCourses.contains(source.id), "Component probe promoted to full original course completion")
    print("PASS observed input edit/clear/lock and two source accepted values; full grader and source mistake trajectory unverified")
}
func actualEnglishAudioPairing() throws {
    let source = try course(fixture: "fixture-english-pairing-probe.json")
    var lesson = Lesson(course: source, hearts: 3)
    let a = lesson.question.pairs[0].id, b = lesson.question.pairs[1].id
    lesson.matchLeft(a); lesson.matchRight(b)
    try check(lesson.hearts == 2 && lesson.mistakesMade == 1 && lesson.incorrectMatch == [a, b], "Source audio mismatch must consume one heart and mark both controls")
    try check(lesson.feedback == nil && lesson.matchedPairs.isEmpty, "Wrong pair ended the current task")
    lesson.matchLeft(a); lesson.matchRight(a)
    try check(lesson.hearts == 2 && lesson.matchedPairs.contains(a) && lesson.incorrectMatch == nil, "Source retry failed or cost another heart")
    lesson.matchLeft(a); lesson.matchRight(a)
    try check(lesson.hearts == 2 && lesson.matchedPairs.count == 1, "Disabled matched pair accepted new input")
    for pair in lesson.question.pairs.dropFirst() { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
    try check(lesson.feedback == true && lesson.hearts == 2, "All source audio pairs did not finish")
    let typed = try course(fixture: "fixture-english-input-probe.json").questions[1]
    try check(typed.correctText == "I'd like tea.", "Typed correction lost the source fixed sentence")
    print("PASS source audio matching wrong-heart, retry and disabled pairs; no extra pairing review observed in mixed-error source trajectory; acoustics unverified")
}
func actualEnglishTypedReview() throws {
    let source = try course(fixture: "fixture-english-hot-review-probe.json")
    var lesson = Lesson(course: source, hearts: 4)
    lesson.enterText("cold"); lesson.submit()
    try check(lesson.feedback == false && lesson.hearts == 3 && lesson.question.correctText == "hot tea", "Source cold rejection or full correction not reproduced")
    lesson.advance()
    try check(lesson.reviewing && lesson.enteredText.isEmpty && !lesson.canSubmit, "Typed error did not enter clean review")
    lesson.enterText("HOT"); lesson.submit()
    try check(lesson.feedback == true && lesson.hearts == 3, "Source accepted HOT rejected")
    lesson.advance(); try check(lesson.complete, "Corrected source typed error cannot finish")
    print("PASS source cold rejection, full hot tea correction, review and HOT acceptance; broader grader unverified")
}
func legacyCourse() throws -> Course { try course() }
func actualEnglishFifthTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v6.json")
    try check(source.lessons.map { $0.questions.count } == [15,15,15,12,15], "Captured five-course sequence changed")
    var lesson = Lesson(course: source, lessonIndex: 4, hearts: 4)
    var graded = 0, speeches = 0, introductions = 0
    while !lesson.complete {
        if let speech = lesson.deferredSpeech {
            speeches += 1
            try check(speech.phrase == "I'd like hot coffee." && lesson.question.id == "en-zh-l5-adaptive7", "Speech inserted at wrong source position")
            let position = lesson.position
            lesson.advance(); lesson.addWord(lesson.question.answerWords[0]); lesson.submit()
            try check(lesson.position == position && lesson.selectedWords.isEmpty && lesson.feedback == nil && !lesson.canSubmit, "Ungraded speech leaked into answering")
            lesson.declineSpeech(); lesson.advance()
            try check(lesson.hearts == 4 && lesson.mistakesMade == 0 && lesson.deferredSpeech == nil, "Declining speech was graded or consumed a heart")
            continue
        }
        if let interlude = lesson.interlude {
            introductions += 1
            try check(interlude.id == "en-zh-l5-review-intro" && lesson.reviewing && lesson.question.id == "en-zh-l5-q7", "Source review introduction or target wrong")
            try check(!lesson.canSubmit && lesson.enteredText.isEmpty, "Review introduction exposes stale answer")
            lesson.advance(); continue
        }
        let q = lesson.question
        switch q.kind {
        case .wordTiles: for id in q.answerWords { lesson.addWord(id) }; lesson.submit()
        case .textEntry:
            lesson.enterText(q.id == "en-zh-l5-q7" ? (lesson.reviewing ? "HOT" : "cold") : q.answer)
            lesson.submit()
        case .matching:
            if q.id == "en-zh-l5-q8" { lesson.matchLeft(q.pairs[0].id); lesson.matchRight(q.pairs[1].id) }
            for pair in q.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
        case .choice: throw CheckFailure.failed("Unexpected fifth choice task")
        }
        try check(lesson.feedback == (q.id != "en-zh-l5-q7" || lesson.reviewing), "Captured answer outcome changed")
        graded += 1; lesson.advance()
    }
    try check(graded == 16 && speeches == 1 && introductions == 1 && lesson.hearts == 2 && lesson.mistakesMade == 2, "Full mixed-error fifth trajectory diverged")
    var flow = SettlementFlow(pages: lesson.definition.settlement!)
    var kinds = [String]()
    while let page = flow.current { kinds.append(page.kind); flow.advance() }
    try check(kinds == ["result","daily_quests","gems","profile"], "Fifth settlement ordering changed")
    var progress = LearningProgress()
    for index in source.lessons.indices { progress.markCompleted(source, index: index) }
    try check(!progress.completedCourses.contains(source.id), "Remaining three uncompiled lessons credited")
    try check(source.pathNodes?[1].lessonIDs == ["lesson-5"] && source.pathNodes?[1].lessonCount == 4, "Second-node source progress lost")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Speech/review metadata lost in round-trip")
    print("PASS full fifth mixed-error trajectory: 15 graded questions + ungraded speech + one typed review; settlement/home metadata; frontend pending")
}
func actualListeningDeclinePrefix() throws {
    let source = try course(fixture: "fixture-listening-decline.json")
    var lesson = Lesson(course: source, hearts: 2)
    lesson.advance()
    try check(lesson.position == 0, "Unanswered pairing advanced before decline")
    lesson.declineListening()
    let pair = lesson.question.pairs[0].id
    lesson.matchLeft(pair); lesson.matchRight(pair); lesson.submit()
    try check(lesson.listeningDeclined && lesson.feedback == nil && lesson.matchedPairs.isEmpty && lesson.hearts == 2 && lesson.mistakesMade == 0 && lesson.review.isEmpty,
              "Declined listening was scored, accepted input, or consumed a heart")
    lesson.advance()
    try check(lesson.question.id == "en-zh-decline-adaptive" && !lesson.listeningDeclined, "Inserted source translation was skipped")
    lesson.declineListening()
    try check(!lesson.listeningDeclined, "Listening decline leaked into translation")
    for id in lesson.question.answerWords { lesson.addWord(id) }
    lesson.submit(); lesson.advance()
    try check(lesson.question.id == "en-zh-decline-fill", "Original typed challenge did not follow inserted translation")
    lesson.enterText("milk"); lesson.submit()
    try check(lesson.feedback == true && lesson.hearts == 2 && lesson.review.isEmpty, "Observed milk acceptance changed")
    print("PASS source listening decline locks pairs without grading, preserves hearts, enters inserted translation then original fill; later adaptation/timer unverified")
}
func actualEnglishSixthDoubleDecline() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v7.json")
    var lesson = Lesson(course: source, lessonIndex: 5, hearts: 2)
    var graded = 0, listening = 0, speech = 0, introductions = 0
    while !lesson.complete {
        if lesson.interlude != nil { introductions += 1; lesson.advance(); continue }
        if lesson.deferredSpeech != nil {
            speech += 1; lesson.declineSpeech(); lesson.advance(); continue
        }
        let q = lesson.question
        if q.listeningDecline != nil {
            listening += 1; lesson.declineListening()
            try check(lesson.feedback == nil && lesson.hearts == 2 && lesson.review.isEmpty, "Sixth listening decline was graded")
            lesson.advance(); continue
        }
        switch q.kind {
        case .wordTiles: for id in q.answerWords { lesson.addWord(id) }
        case .textEntry: lesson.enterText(q.answer)
        default: throw CheckFailure.failed("Unexpected sixth graded task")
        }
        lesson.submit()
        try check(lesson.feedback == true, "Actual sixth accepted answer rejected")
        graded += 1; try check(lesson.correctStreak == graded, "Ungraded sixth stage changed correct streak"); lesson.advance()
    }
    try check(graded == 15 && listening == 1 && speech == 1 && introductions == 1 && lesson.hearts == 2 && lesson.mistakesMade == 0 && lesson.review.isEmpty, "Sixth observed trajectory diverged")
    try check(lesson.definition.settlement?.map(\.kind) == ["result", "profile"], "Sixth incorrectly inherited fifth settlement")
    try check(source.pathNodes?[1].lessonIDs == ["lesson-5", "lesson-6"], "Sixth second-node placement lost")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Sixth metadata lost during round trip")
    print("PASS actual sixth double-decline: 15 graded + ungraded listening/speech, challenge entry and independent settlement; normal branch still unknown")
}

func actualSecondaryInputModes() throws {
    let source = try course(fixture: "fixture-reference-en-zh-secondary-v1.json")
    var lesson = Lesson(course: source, hearts: 2)
    for (index, answer) in ["Thank you.", "I'd like water and coffee, please."].enumerated() {
        try check(!lesson.canSubmit && lesson.supportsInputMode, "Observed initial action state missing")
        lesson.toggleInputMode()
        try check(lesson.usingKeyboard && !lesson.canSubmit && lesson.displayedPrompt == "用英语写出这句话", "Empty full answer must be disabled")
        lesson.enterText(answer)
        try check(lesson.canSubmit && lesson.displayedInput == answer, "Full answer not retained")
        lesson.toggleInputMode()
        try check(!lesson.canSubmit && lesson.displayedInput.isEmpty && lesson.selectedWords.isEmpty, "Alternative answer must stay independent")
        if index == 1 { try check(lesson.displayedPrompt == "输入所缺单词", "Reduced difficulty prompt missing") }
        lesson.toggleInputMode()
        try check(lesson.displayedInput == answer && lesson.canSubmit, "Reopened source answer lost")
        lesson.submit()
        try check(lesson.feedback == true && lesson.hearts == 2, "Actual accepted full answer rejected")
        lesson.toggleInputMode()
        try check(lesson.usingKeyboard, "Feedback input must remain locked")
        lesson.advance()
    }
    try check(lesson.complete && lesson.mistakesMade == 0, "Probe did not finish")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Input-mode metadata lost")
    print("PASS actual keyboard/harder independent buffers, source accepted full answers and feedback lock")
}

func actualCrossQuestionPreferences() throws {
    var lesson = Lesson(course: try course(fixture: "fixture-reference-en-zh-secondary-v3.json"), hearts: 2)
    try check(!lesson.usingKeyboard, "Initial word bank must remain the source default")
    lesson.toggleInputMode(); lesson.enterText("Thank you."); lesson.submit(); lesson.advance()
    try check(!lesson.usingKeyboard && lesson.displayedPrompt == "输入所缺单词", "Tile preference must not change the initial fill difficulty")
    lesson.toggleInputMode(); lesson.enterText("I'd like water and coffee, please."); lesson.submit(); lesson.advance()
    try check(lesson.usingKeyboard && lesson.displayedInput.isEmpty && !lesson.canSubmit, "Source q6 must reopen keyboard with a fresh buffer")
    lesson.enterText("No coffee, thank you."); lesson.submit(); lesson.advance()
    try check(lesson.usingKeyboard && lesson.displayedPrompt == "用英语写出这句话" && lesson.displayedInput.isEmpty && !lesson.canSubmit, "Source q7 must independently retain full-sentence difficulty")
    lesson.enterText("With ice?"); lesson.submit()
    try check(lesson.feedback == true && lesson.hearts == 2 && lesson.mistakesMade == 0, "Observed full answer rejected after preference restoration")
    lesson.advance(); try check(lesson.complete, "Preference trajectory did not finish")
    print("PASS observed independent cross-question keyboard/full-sentence preferences and fresh buffers")
}

func actualSkipReview() throws {
    let c = try course(fixture: "fixture-reference-en-zh-skip-v1.json")
    var lesson = Lesson(course: c, hearts: 2)
    try check(!lesson.canSubmit, "Empty source question unexpectedly submittable")
    lesson.skip(); lesson.skip()
    try check(lesson.skipped && lesson.feedback == false && lesson.review == [0], "Skip must queue original question once")
    try check(lesson.hearts == 2 && lesson.mistakesMade == 0, "Skip was incorrectly graded as a mistake")
    try check(lesson.question.skipCorrectText == "茶和咖啡", "Source correction lost Chinese spacing")
    lesson.advance()
    try check(lesson.reviewing && !lesson.complete && lesson.interlude != nil && !lesson.skipped, "Skip bypassed review intro")
    lesson.advance()
    for word in lesson.question.answerWords { lesson.addWord(word) }
    lesson.submit()
    try check(lesson.feedback == true, "Source review answer rejected")
    lesson.advance()
    try check(lesson.complete && lesson.hearts == 2 && lesson.mistakesMade == 0 && lesson.review.isEmpty, "Skip review altered hearts/errors or remained incomplete")
    print("PASS observed empty skip, no heart/error penalty, original-question review and correction")
}

func actualSeventhTrajectory() throws {
    let c = try course(fixture: "fixture-reference-en-zh-v9.json")
    var lesson = Lesson(course: c, lessonIndex: 6, hearts: 2)
    let original = lesson.question.id
    lesson.skip(); lesson.advance()
    for index in 1..<15 {
        try check(lesson.position == index, "Seventh actual order changed")
        if lesson.deferredSpeech != nil { lesson.declineSpeech(); lesson.advance() }
        if [1,4].contains(index) { lesson.toggleInputMode() }
        if [6,7,8,14].contains(index) { try check(lesson.usingKeyboard, "Source independent preference lost") }
        if index == 3 { try check(lesson.displayedHint == "No __, please.", "Isolation answer revealed before submit") }
        if lesson.usingKeyboard { lesson.enterText(lesson.question.keyboardAnswer!); lesson.submit() }
        else {
            switch lesson.question.kind {
            case .matching: for p in lesson.question.pairs { lesson.matchLeft(p.id); lesson.matchRight(p.id) }
            case .choice: lesson.choose(lesson.question.answer); lesson.submit()
            case .textEntry: lesson.enterText(lesson.question.answer); lesson.submit()
            case .wordTiles: for w in lesson.question.answerWords { lesson.addWord(w) }; lesson.submit()
            }
        }
        try check(lesson.feedback == true && lesson.hearts == 2 && lesson.mistakesMade == 0, "Seventh source accepted answer failed")
        if index == 3 { try check(lesson.displayedHint == "No ice, please.", "Isolation accepted answer not revealed") }
        lesson.advance()
    }
    try check(lesson.reviewing && lesson.interlude != nil && lesson.question.id == original, "Seventh skipped q0 not queued at actual end")
    lesson.advance()
    try check(lesson.visibleWords.map(\.text) == ["和","茶","咖啡","谢谢你"], "Review bank must follow observed reshuffle")
    for w in lesson.question.answerWords { lesson.addWord(w) }; lesson.submit()
    try check(lesson.correctStreak == 15, "Actual fifteen-correct streak lost")
    lesson.advance()
    try check(lesson.complete && lesson.mistakesMade == 0, "Seventh actual review did not complete")
    try check(lesson.definition.settlement?.map(\.kind) == ["result","achievement","profile"], "Source seventh settlement order lost")
    print("PASS full observed seventh skip/normal listening/radio2/preferences/speech decline/insertion/review/settlement; heart refresh and unknown radio1 audio unverified")
}

func actualPronunciationPractice() throws {
    let package = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let url = package.appendingPathComponent("Sources/LingoSeed/Resources/Reference/pronunciation-practice.json")
    let course = try JSONDecoder().decode(Course.self, from: Data(contentsOf: url))
    var lesson = Lesson(course: course, lessonIndex: 0, hearts: 3)
    var graded = 0, declined = 0, reviews = 0
    for _ in 0..<40 {
        if lesson.complete { break }
        if lesson.deferredSpeech != nil { lesson.declineSpeech(); declined += 1; lesson.advance(); continue }
        let question = lesson.question
        if question.kind == .matching {
            for pair in question.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
        } else {
            if lesson.reviewing { reviews += 1 }
            lesson.choose(lesson.reviewing ? question.answer : question.options[0].id)
            lesson.submit()
        }
        try check(lesson.feedback != nil, "Observed pronunciation answer must grade")
        graded += 1; lesson.advance()
    }
    try check(lesson.complete && declined == 1 && reviews == 4 && graded == 15, "Observed 10 choices, speech decline, matching and four reviews must finish")
    print("PASS pronunciation original 12-state base trajectory and four corrections; main progress isolation verified separately through native UI")
}

func laterPronunciationPractices() throws {
    let package = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let course = try JSONDecoder().decode(Course.self, from: Data(contentsOf: package.appendingPathComponent("Sources/LingoSeed/Resources/Reference/pronunciation-practice.json")))
    try check(course.lessons.count == 3, "All three observed practices must compile")
    for index in 1...2 {
        var lesson = Lesson(course: course, lessonIndex: index, hearts: 3)
        var reviewed = 0, speech = 0, graded = 0
        for _ in 0..<40 {
            if lesson.complete { break }
            if lesson.deferredSpeech != nil { speech += 1; lesson.declineSpeech(); lesson.advance(); continue }
            if lesson.question.kind == .matching {
                for pair in lesson.question.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
            } else {
                if lesson.reviewing { reviewed += 1 }
                lesson.choose(lesson.reviewing ? lesson.question.answer : lesson.question.options[0].id); lesson.submit()
            }
            try check(lesson.feedback != nil, "Later practice failed to grade")
            graded += 1; lesson.advance()
        }
        try check(lesson.complete && reviewed == (index == 1 ? 6 : 5) && speech == (index == 1 ? 0 : 1) && graded == (index == 1 ? 17 : 16), "Later practice source trajectory differs")
    }
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: directory) }
    let store = ProgressStore(url: directory.appendingPathComponent("progress.json"))
    var progress = LearningProgress(); progress.hearts = 3
    progress.completedLessons["duolingo-en-zh-unit-1"] = ["lesson-1"]
    let initialMain = progress.completedLessons["duolingo-en-zh-unit-1"]
    for index in 0...1 {
        progress.completedLessons[course.id, default: []].insert(course.lessons[index].id)
        try store.save(progress); progress = try store.load()
        try check(progress.completedCount(course) == index + 1 && progress.hearts == 3 && progress.completedLessons["duolingo-en-zh-unit-1"] == initialMain && !progress.completedCourses.contains(course.id), "Practice restart progression leaked into main course or invented course completion")
    }
    print("PASS second/third observed practices, optional speech, six/five corrections and isolated persisted session selection; adaptive source selection remains unknown")
}

func actualGeneralPractice() throws {
    let course = try course(fixture: "fixture-reference-en-zh-general-practice-v2.json")
    try check(course.lessons[0].questions.count == 16 && course.mistakeHeartCost == 0, "Independent practice source definition differs")
    var lesson = Lesson(course: course, hearts: 3)
    var graded = 0, speech = 0, interludes = 0, keyboard = 0
    for _ in 0..<64 {
        if lesson.complete { break }
        if lesson.interlude != nil { interludes += 1; lesson.advance(); continue }
        if let pending = lesson.deferredSpeech {
            try check(pending.phrase == "Tea, please.", "Wrong inserted speech identity")
            speech += 1; lesson.declineSpeech(); lesson.advance(); continue
        }
        if lesson.question.id == "general-practice-q6" {
            try check(lesson.usingKeyboard, "Observed initial keyboard mode lost")
            keyboard += 1; lesson.toggleInputMode()
        }
        let wrong = lesson.question.id == "general-practice-replacement15" && !lesson.reviewing
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer)
        case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }
        case .matching:
            for pair in lesson.question.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
        case .textEntry: lesson.enterText(wrong ? "water" : lesson.question.answer)
        }
        if lesson.question.kind != .matching { lesson.submit() }
        try check(lesson.feedback == !wrong && lesson.hearts == 3, "Practice feedback or no-heart-cost differs: \(lesson.question.id), feedback=\(String(describing: lesson.feedback)), keyboard=\(lesson.usingKeyboard), hearts=\(lesson.hearts)")
        graded += 1; lesson.advance()
    }
    try check(lesson.complete && graded == 17 && speech == 1 && interludes == 2 && keyboard == 1 && lesson.mistakesMade == 1, "Actual practice adaptive/decline/review trajectory differs")
    try check(lesson.definition.settlement?.map(\.kind) == ["result", "practice_heart", "profile"], "Observed result/reward/profile sequence differs")
    print("PASS independent general practice, initial keyboard/bank, speech insertion, challenge replacements, non-penalizing wrong and correction")
}

func actualListeningDeclineReplacement() throws {
    let source = try course(fixture: "fixture-reference-en-zh-general-listening-decline-v1.json")
    for injectWrong in [false, true] {
        var lesson = Lesson(course: source, hearts: 5)
        var graded = 0, declines = 0, speeches = 0
        for _ in 0..<48 {
            if lesson.complete { break }
            if lesson.interlude != nil { lesson.advance(); continue }
            if let speech = lesson.deferredSpeech {
                try check(speech.phrase == "Good morning, hot coffee or with ice?", "Source speech changed")
                speeches += 1; lesson.declineSpeech(); lesson.advance(); continue
            }
            if lesson.question.id == "general-listening-prefix-6" {
                let before = lesson
                lesson.declineListening(); lesson.addWord(lesson.question.answerWords[0]); lesson.submit()
                try check(lesson.listeningDeclined && !lesson.canSubmit && lesson.selectedWords.isEmpty && lesson.feedback == nil, "Declined listening still accepts input")
                try check(lesson.hearts == before.hearts && lesson.correctStreak == before.correctStreak && lesson.position == before.position, "Decline was graded or advanced")
                lesson.advance(); declines += 1
                try check(lesson.question.id == "general-listening-decline-inserted" && lesson.position == before.position && !lesson.listeningDeclined, "Observed translation was skipped")
            }
            let wrong = injectWrong && lesson.question.id == "general-listening-decline-inserted" && !lesson.reviewing
            if lesson.reviewing { try check(lesson.question.id == "general-listening-decline-inserted", "Review restored skipped listening instead of translation") }
            switch lesson.question.kind {
            case .matching: for pair in lesson.question.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
            case .choice: lesson.choose(lesson.question.answer); lesson.submit()
            case .wordTiles:
                for id in wrong ? Array(lesson.question.answerWords.prefix(1)) : lesson.question.answerWords { lesson.addWord(id) }
                lesson.submit()
            case .textEntry: lesson.enterText(lesson.question.answer); lesson.submit()
            }
            try check(lesson.feedback == !wrong && lesson.hearts == 5, "Replacement grading or zero heart cost changed")
            graded += 1; lesson.advance()
        }
        try check(lesson.complete && declines == 1 && speeches == 1 && graded == (injectWrong ? 17 : 16), "Listening replacement trajectory incomplete")
    }
    print("PASS actual listening replacement trajectory and separate wrong-review state invariant")
}

func actualCurrentResultHistory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-current-review-v1.json")
    var lesson = Lesson(course: source)
    while !lesson.complete {
        if lesson.interlude != nil { lesson.advance(); continue }
        if let speech = lesson.deferredSpeech {
            let count = lesson.resultReviewEntries.count
            lesson.advance()
            try check(lesson.resultReviewEntries.count == count, "Unanswered speech entered result history")
            lesson.declineSpeech(); lesson.advance()
            let entry = lesson.resultReviewEntries.last!
            try check(entry.questionID == speech.id && entry.accepted == nil && entry.declined, "Decline falsely recorded as graded correct")
            try check(entry.answer == "Hot, please.", "Observed declined-speech display lost")
            continue
        }
        let q = lesson.question
        switch q.kind {
        case .choice: lesson.choose(q.answer); lesson.submit()
        case .wordTiles: for id in q.answerWords { lesson.addWord(id) }; lesson.submit()
        case .textEntry: lesson.enterText(q.answer); lesson.submit()
        case .matching: for p in q.pairs { lesson.matchLeft(p.id); lesson.matchRight(p.id) }
        }
        try check(lesson.feedback == true, "Actual current question not accepted")
        lesson.advance()
    }
    let entries = lesson.resultReviewEntries
    try check(entries.count == 17 && entries.filter { $0.accepted == true }.count == 16, "Actual review lost graded or deferred card")
    try check(entries[8].declined && entries[9].presentation.prompt == "tea with sugar", "Inserted translation reordered before speech")
    try check(entries[14].answer == "tea with sugar", "Keyboard answer not retained after clearing input")
    let fresh = Lesson(course: source)
    try check(fresh.resultReviewEntries.isEmpty, "Retry inherited prior result history")
    print("PASS actual 17-card history; declined display is not a correct grade; keyboard answer and retry isolation")
}

func actualErrorResultHistory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-error-review-v1.json")
    var lesson = Lesson(course: source)
    var steps = 0
    while !lesson.complete && steps < 48 {
        steps += 1
        if lesson.interlude != nil { lesson.advance(); continue }
        if lesson.deferredSpeech != nil { lesson.declineSpeech(); lesson.advance(); continue }
        let q = lesson.question
        let wrong = q.id == "error-review-q1" && !lesson.reviewing
        switch q.kind {
        case .choice: lesson.choose(wrong ? "1" : q.answer); lesson.submit()
        case .wordTiles: for id in q.answerWords { lesson.addWord(id) }; lesson.submit()
        case .textEntry: lesson.enterText(q.answer); lesson.submit()
        case .matching: for p in q.pairs { lesson.matchLeft(p.id); lesson.matchRight(p.id) }
        }
        try check(lesson.feedback == !wrong, "Observed first error or correction was misgraded")
        lesson.advance()
    }
    let entries = lesson.resultReviewEntries
    try check(lesson.complete && entries.count == 18, "Error instance lost an attempt")
    try check(entries[1].answer == "coffee" && entries[1].accepted == false, "First wrong answer overwritten")
    try check(entries[17].answer == "hot" && entries[17].accepted == true && entries[1].questionID == entries[17].questionID && entries[1].id != entries[17].id, "Corrected attempt was deduplicated")
    try check(entries[6].declined && entries[6].accepted == nil, "Deferred speech became graded")
    try check(Lesson(course: source).resultReviewEntries.isEmpty, "Retry retained error history")
    print("PASS actual 18-card history preserves wrong coffee and corrected hot separately")
}

func actualEighthCourse() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v12.json")
    let old = try course(fixture: "fixture-reference-en-zh-v11.json")
    try check(Array(source.lessons.prefix(7)) == old.lessons, "New default rewrote old seven lessons")
    var lesson = Lesson(course: source, lessonIndex: 7, hearts: 5)
    var graded = 0
    while !lesson.complete && graded < 20 {
        if lesson.deferredSpeech != nil { lesson.declineSpeech(); lesson.advance(); continue }
        let q = lesson.question
        switch q.kind {
        case .choice: lesson.choose(q.answer); lesson.submit()
        case .wordTiles: for id in q.answerWords { lesson.addWord(id) }; lesson.submit()
        case .textEntry: lesson.enterText(q.answer); lesson.submit()
        case .matching: for p in q.pairs { lesson.matchLeft(p.id); lesson.matchRight(p.id) }
        }
        try check(lesson.feedback == true, "Actual eighth answer rejected")
        graded += 1; lesson.advance()
    }
    let entries = lesson.resultReviewEntries
    try check(lesson.complete && graded == 12 && entries.count == 13 && lesson.hearts == 5, "Actual eighth trajectory changed")
    try check(entries[1].declined && entries[1].accepted == nil && entries[7].answer == "I'd like coffee with milk and sugar.", "Speech or full reverse answer lost")
    try check(lesson.definition.settlement?.map(\.kind) == ["result","score_progress","boost","legendary","profile"], "Observed post-result sequence lost")
    print("PASS default eighth course retains seven lessons, twelve accepted, deferred speech and thirteen-card history")
}

func observedPathChest() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v13.json")
    var progress = LearningProgress()
    try check(!progress.openPathChest(source), "Locked chest granted a reward")
    for i in source.lessons.indices { progress.markCompleted(source, index: i) }
    try check(progress.isPathChestReady(source) && !progress.isPathChestOpened(source), "Completed two levels failed to unlock chest")
    try check(progress.openPathChest(source) && !progress.openPathChest(source), "Chest opening must be idempotent")
    let restored = try JSONDecoder().decode(LearningProgress.self, from: JSONEncoder().encode(progress))
    try check(restored.isPathChestOpened(source) && restored.completedCourses.isEmpty, "Chest persistence or incomplete path semantics lost")
    let old = try JSONDecoder().decode(LearningProgress.self, from: Data("{\"completedLessons\":{},\"hearts\":5}".utf8))
    try check(old.openedPathChests.isEmpty, "Old saved progress must remain readable")
    try check(source.home?.pathChest?.beforeGems == 510 && source.home?.pathChest?.afterGems == 525, "Observed gem endpoints changed")
    print("PASS actual path chest prerequisites, one-time opening, persisted state and old progress compatibility")
}

func observedHomeClock() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v14.json")
    guard let snapshot = source.home?.progressSnapshots?.first(where: { $0.completedLessons == 8 }) else { throw CheckFailure.failed("Missing eight-completion home") }
    let projects = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let scenario = try JSONSerialization.jsonObject(with: Data(contentsOf: projects.appendingPathComponent("duolingo-web/home-clock-scenario-v1.json"))) as! [String: Any]
    for row in scenario["states"] as! [[String: Any]] {
        let date = Date(timeIntervalSince1970: (row["epoch_milliseconds"] as! Double) / 1000)
        try check(snapshot.leagueCountdownText(at:date) == row["expected_text"] as? String, "Countdown differs from actual original mutation epoch")
    }
    let legacy = try course(fixture: "fixture-reference-en-zh-v13.json").home?.progressSnapshots?.first(where: { $0.completedLessons == 8 })
    try check(legacy?.leagueCountdownText(at: .distantFuture) == legacy?.leagueCountdown, "Legacy frozen reference changed")
    print("PASS actual original countdown epochs and legacy fixture compatibility")
}

func observedPlacementPersistence() throws {
    let test=try course(fixture:"fixture-reference-en-zh-section-placement-v2.json")
    guard let outcome=test.lessons[0].placementOutcome else {throw CheckFailure.failed("Observed placement outcome missing")}
    try check(outcome.activeStage==2 && outcome.completedStages==[1] && outcome.englishScore==10,"Actual stage unlock/score lost")
    try check(outcome.homeSnapshot.gems==530 && outcome.homeSnapshot.questTarget==50,"Actual source result snapshot lost")
    let old=Data("{\"completedCourses\":[],\"completedLessons\":{},\"hearts\":5}".utf8)
    var progress=try JSONDecoder().decode(LearningProgress.self,from:old)
    try check(progress.placementOutcomes.isEmpty,"Old progress invented a stage result")
    progress.placementOutcomes["main-course"]=outcome
    let restored=try JSONDecoder().decode(LearningProgress.self,from:JSONEncoder().encode(progress))
    try check(restored==progress && restored.hearts==5,"Placement persistence changed global hearts or result")
    let original=try course(fixture:"fixture-reference-en-zh-section-placement-v1.json")
    try check(original.lessons[0].placementOutcome==nil,"Historical fixture changed")
    print("PASS observed placement outcome persistence and legacy progress/fixture compatibility")
}


func actualStageTwoGrocery() throws {
    let course = try course(fixture:"fixture-reference-en-zh-stage2-grocery-v1.json")
    var lesson=Lesson(course:course)
    var graded=0, speech=0, interludes=0
    for _ in 0..<32 {
        if lesson.complete { break }
        if lesson.interlude != nil { interludes += 1;lesson.advance();continue }
        if let pending=lesson.deferredSpeech {
            try check(pending.phrase == "Is this store expensive?", "Grocery oral identity lost")
            speech += 1;lesson.declineSpeech();lesson.advance();continue
        }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer)
        case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }
        case .textEntry: lesson.enterText(lesson.question.answer)
        case .matching: throw CheckFailure.failed("Unexpected grocery matching")
        }
        lesson.submit();try check(lesson.feedback == true,"Grocery accepted source answer rejected")
        graded += 1;lesson.advance()
    }
    try check(lesson.complete && graded == 10 && speech == 1 && interludes == 2,"Grocery full observed trajectory differs")
    try check(lesson.resultReviewEntries.count == 11,"Declined oral missing from grocery result history")
    try check(lesson.definition.settlement?.map(\.kind) == ["result","profile"],"Grocery settlement sequence differs")
    try check(lesson.definition.observedHomeSnapshot?.leagueTitle == "青铜等级" && lesson.definition.observedHomeSnapshot?.gems == 505,"Actual post-grocery home state differs")
    print("PASS grocery 10 accepted, oral decline, two encouragements, 11 result cards and observed home outcome")
}

func actualUnitPlacement() throws {
    let c=try course(fixture:"fixture-reference-en-zh-unit-placement-v1.json")
    var lesson=Lesson(course:c,hearts:5)
    var answered=0,encouragements=0
    while !lesson.complete && answered<30 {
        if lesson.interlude != nil {encouragements += 1;lesson.advance();continue}
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer)
        case .wordTiles: for id in lesson.question.answerWords {lesson.addWord(id)}
        case .textEntry: lesson.enterText(lesson.question.answer)
        case .matching: throw CheckFailure.failed("Unexpected unit test matching")
        }
        lesson.submit();try check(lesson.feedback==true,"Accepted unit test answer rejected")
        answered += 1;lesson.advance()
    }
    try check(lesson.complete && answered==18 && encouragements==4 && lesson.hearts==5,"Unit-12 trajectory differs")
    try check(lesson.resultReviewEntries.count==18,"Actual 18 review cards missing")
    try check(lesson.definition.settlement?.map(\.kind)==["result","score_progress","unit_unlock","profile"],"Unit settlement confused with section settlement")
    let outcome=lesson.definition.placementOutcome!
    try check(outcome.activeUnit==12 && outcome.activeStage==2 && outcome.englishScore==10,"Unit jump must not promote English score")
    var progress=LearningProgress();progress.hearts=4;progress.placementOutcomes["main"]=outcome
    let decoded=try JSONDecoder().decode(LearningProgress.self,from:JSONEncoder().encode(progress))
    try check(decoded.hearts==4 && decoded.placementOutcomes["main"]?.activeUnit==12,"Independent unit hearts or unit unlock not preserved")
    let legacy=try course(fixture:"fixture-reference-en-zh-section-placement-v1.json")
    try check(legacy.lessons[0].placementOutcome?.activeUnit==nil,"Legacy stage outcome must decode without invented unit")
    print("PASS actual unit-12 18 accepted, four encouragements, five independent hearts, 18 review cards and unpromoted score")
}

func actualUnit12HomeCourse() throws {
    let course = try course(fixture:"fixture-reference-en-zh-unit12-content-v1.json")
    var lesson=Lesson(course:course,hearts:4)
    var graded=0, speech=0, interludes=0
    for _ in 0..<32 {
        if lesson.complete { break }
        if lesson.interlude != nil { interludes += 1;lesson.advance();continue }
        if let pending=lesson.deferredSpeech {
            try check(pending.phrase == "Welcome, Lisa, how are you?", "Unit12 oral identity lost")
            speech += 1;lesson.declineSpeech();lesson.advance();continue
        }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer)
        case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }
        case .textEntry: lesson.enterText(lesson.question.answer)
        case .matching: throw CheckFailure.failed("Unexpected unit12 matching")
        }
        lesson.submit();try check(lesson.feedback == true,"Unit12 accepted source answer rejected")
        graded += 1;lesson.advance()
    }
    try check(lesson.complete && graded == 17 && speech == 1 && interludes == 2,"Unit12 full observed trajectory differs")
    try check(lesson.resultReviewEntries.count == 18,"Declined oral missing from unit12 result history")
    try check(lesson.definition.settlement?.map(\.kind) == ["result","profile"],"Unit12 settlement sequence differs")
    try check(lesson.definition.observedHomeSnapshot?.leagueTitle == "青铜等级" && lesson.definition.observedHomeSnapshot?.gems == 505,"Actual post-unit12 home state differs")
    try check(lesson.hearts == 4,"Ordinary course must not use placement heart rewards")
    try check(lesson.definition.completionAudioVolume == 0.5 && lesson.definition.completionAudioResource != nil,"Observed completion resource/gain missing")
    try check(lesson.definition.questions.filter{$0.correctFeedbackAudioVolume != nil}.count == 6,"Preserve incomplete source feedback windows rather than invent every event")
    let roundtrip=try JSONDecoder().decode(Course.self,from:JSONEncoder().encode(course))
    try check(roundtrip.lessons[0].completionAudioVolume == 0.5,"Audio contract dropped during roundtrip")
    print("PASS unit12 17 accepted, oral decline, two encouragements, 18 result cards and observed home outcome")
}

func actualUnit12SecondHomeCourse() throws {
    let course = try course(fixture:"fixture-reference-en-zh-unit12-lesson2-v1.json")
    var lesson=Lesson(course:course,hearts:4)
    var graded=0, speech=0, interludes=0
    for _ in 0..<32 {
        if lesson.complete { break }
        if lesson.interlude != nil { interludes += 1;lesson.advance();continue }
        if let pending=lesson.deferredSpeech {
            try check(pending.phrase == "a beautiful house", "Unit12 oral identity lost")
            speech += 1;lesson.declineSpeech();lesson.advance();continue
        }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer)
        case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }
        case .textEntry: lesson.enterText(lesson.question.answer)
        case .matching: throw CheckFailure.failed("Unexpected unit12 matching")
        }
        lesson.submit();try check(lesson.feedback == true,"Unit12 accepted source answer rejected")
        graded += 1;lesson.advance()
    }
    try check(lesson.complete && graded == 12 && speech == 1 && interludes == 2,"Unit12 full observed trajectory differs")
    try check(lesson.resultReviewEntries.count == 13,"Declined oral missing from unit12 result history")
    try check(lesson.definition.settlement?.map(\.kind) == ["result","profile"],"Unit12 settlement sequence differs")
    try check(lesson.definition.observedHomeSnapshot?.leagueTitle == "青铜等级" && lesson.definition.observedHomeSnapshot?.gems == 505,"Actual post-unit12 home state differs")
    try check(lesson.hearts == 4,"Ordinary course must not use placement heart rewards")
    try check(lesson.definition.questions.filter{$0.sourceType == "orderTapComplete"}.count == 2,"Two observed pattern exercises missing")
    let pattern=lesson.resultReviewEntries.first{$0.questionID=="unit12-q3"}
    try check(pattern?.answer == "Oh, the house is small.","Pattern result history lost prefills or spacing")
    try check(lesson.definition.completionAudioResource == nil,"Do not invent an unprobed second-course completion cue")
    print("PASS unit12 second 12 accepted, oral decline, two encouragements, 13 result cards and observed home outcome")
}

func actualUnit12ThirdHomeCourse() throws {
    let course = try course(fixture:"fixture-reference-en-zh-unit12-lesson3-v1.json")
    var lesson=Lesson(course:course,hearts:4)
    lesson.skip();try check(lesson.hearts == 4 && lesson.skipped,"Observed skip spent a heart")
    lesson.advance()
    var graded=0, speech=0, interludes=0
    for _ in 0..<32 {
        if lesson.complete { break }
        if lesson.interlude != nil { interludes += 1;lesson.advance();continue }
        if let pending=lesson.deferredSpeech {
            try check(pending.phrase == "Oh, the kitchen is clean!", "Third oral identity lost")
            speech += 1;lesson.declineSpeech();lesson.advance();continue
        }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer)
        case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }
        case .textEntry: lesson.enterText(lesson.question.answer)
        case .matching: for pair in lesson.question.pairs { lesson.matchLeft(pair.id);lesson.matchRight(pair.id) }
        }
        lesson.submit();try check(lesson.feedback == true,"Third accepted answer rejected")
        graded += 1;lesson.advance()
    }
    try check(lesson.complete && graded == 15 && speech == 1 && interludes == 1,"Third skip/review trajectory differs")
    try check(lesson.resultReviewEntries.count == 17,"Skipped and reattempted cards must both remain")
    let tables=lesson.definition.questions.filter{$0.contextExamples != nil}
    try check(tables.count == 2 && tables[0].contextExamples == ["I am from France.","My jacket is on the table."] && tables[1].contextExamples == ["I am from Tokyo.","Your bag is on the couch."],"Table context omitted")
    try check(lesson.definition.questions.filter{$0.kind == .matching}.allSatisfy{$0.matchedAudioResources?.count == 5},"Five real match cues per instance missing")
    try check(lesson.definition.settlement?.map(\.kind) == ["result","practice_heart","profile"],"Actual heart reward page missing")
    try check(lesson.hearts == 4 && lesson.definition.observedHomeSnapshot?.completedLessons == 5,"Course core must leave actual reward to settlement")
    print("PASS third course: two context tables, two match instances, skip/review, oral and heart reward sequence")
}

func actualUnit12FourthHomeCourse() throws {
    let course=try course(fixture:"fixture-reference-en-zh-unit12-lesson4-v1.json")
    var lesson=Lesson(course:course,hearts:5)
    var graded=0,oral=0,intros=0
    for _ in 0..<32 {
        if lesson.complete {break}
        if lesson.interlude != nil {intros += 1;lesson.advance();continue}
        if let pending=lesson.deferredSpeech {
            try check(pending.phrase == "Have a seat here." && pending.characterResource != nil,"Observed oral actor missing")
            oral += 1;lesson.declineSpeech();lesson.advance();continue
        }
        if lesson.question.id == "unit12-q14" {
            try check(!lesson.usingKeyboard && !lesson.canSubmit,"Listening initial state differs")
            lesson.toggleInputMode()
            try check(lesson.usingKeyboard && lesson.displayedPrompt == "键入你听到的内容" && !lesson.canSubmit,"Empty keyboard transition differs")
            lesson.enterText("two bathrooms")
            try check(lesson.canSubmit,"Typed answer did not enable check")
        } else {
            if lesson.question.id == "unit12-q15" {
                try check(lesson.usingKeyboard,"Observed keyboard preference lost between questions")
                lesson.toggleInputMode()
            }
            switch lesson.question.kind {
            case .choice:lesson.choose(lesson.question.answer)
            case .wordTiles:for id in lesson.question.answerWords {lesson.addWord(id)}
            case .textEntry:lesson.enterText(lesson.question.answer)
            case .matching:throw CheckFailure.failed("Unobserved fourth matching")
            }
        }
        lesson.submit();try check(lesson.feedback == true,"Executed fourth answer rejected")
        graded += 1;lesson.advance()
    }
    try check(lesson.complete && graded == 17 && oral == 1 && intros == 1,"Fourth trajectory differs")
    try check(lesson.hearts == 5 && lesson.resultReviewEntries.count == 18,"Fourth hearts/review history differs")
    try check(lesson.definition.settlement?.map(\.kind) == ["result","achievement","profile"],"Actual achievement page omitted")
    try check(lesson.definition.observedHomeSnapshot?.gems == 155,"Fourth source cohort mixed with old 505 gems")
    print("PASS fourth:17 accepted, oral, keyboard preference, challenge intro, achievement and155gem home")
}

func observedHeartRefill() throws {
    var progress=LearningProgress();progress.hearts=4
    try check(!progress.purchaseHeartRefill(availableGems:349),"Insufficient gems must not refill")
    try check(progress.hearts == 4 && progress.spentGems == 0,"Rejected purchase changed progress")
    try check(progress.purchaseHeartRefill(availableGems:505),"Observed 505 gem purchase rejected")
    try check(progress.hearts == 5 && 505-progress.spentGems == 155,"Durable 350-gem refill differs from source reload")
    try check(!progress.purchaseHeartRefill(availableGems:155),"Full-heart purchase should be disabled")
    let restored=try JSONDecoder().decode(LearningProgress.self,from:JSONEncoder().encode(progress))
    try check(restored == progress,"Reload lost heart refill transaction")
    let old=try JSONDecoder().decode(LearningProgress.self,from:Data("{\"completedCourses\":[],\"hearts\":4}".utf8))
    try check(old.spentGems == 0 && old.hearts == 4,"Legacy progress must not acquire a gem debit")
}

do {
    try mistakeReview()
    try persistence()
    try wordTilesAndReview()
    try matching()
    try unlocksAndLegacy()
    try observedInterludes()
    try actualEnglishTrajectory()
    try actualEnglishSecondTrajectory()
    try actualEnglishThirdTrajectory()
    try actualEnglishFourthTrajectory()
    try actualEnglishSettlement()
    try actualEnglishInputStates()
    try actualEnglishAudioPairing()
    try actualEnglishTypedReview()
    try actualEnglishFifthTrajectory()
    try actualListeningDeclinePrefix()
    try actualEnglishSixthDoubleDecline()
    try actualSecondaryInputModes()
    try actualCrossQuestionPreferences()
    try actualSkipReview()
    try actualSeventhTrajectory()
    try actualPronunciationPractice()
    try laterPronunciationPractices()
    try actualGeneralPractice()
    try actualListeningDeclineReplacement()
    try actualCurrentResultHistory()
    try actualErrorResultHistory()
    try actualEighthCourse()
    try observedPathChest()
    try observedHomeClock()
    try observedPlacementPersistence()
    try actualStageTwoGrocery()
    try actualUnitPlacement()
    try actualUnit12HomeCourse()
    try actualUnit12SecondHomeCourse()
    try actualUnit12ThirdHomeCourse()
    try actualUnit12FourthHomeCourse()
    try observedHeartRefill()
    print("38 business checks passed; core layer only")
} catch {
    FileHandle.standardError.write(Data(("FAIL " + String(describing: error) + "\n").utf8))
    exit(1)
}
