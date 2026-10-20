import Foundation

public struct Choice: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let text: String
    public let audioResource: String?
    public let imageResource: String?
    public let correctImageResource: String?
}
public struct WordPair: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let left: String
    public let right: String
    public let audioResource: String?
}
public enum QuestionKind: String, Codable, Sendable {
    case choice, matching
    case wordTiles = "word_tiles"
    case textEntry = "text_entry"
}
public struct ListeningDecline: Codable, Equatable, Sendable {
    public let imageResource: String?
    public let label: String
    public let title: String
    public let body: String
}
public struct IsolationPromptToken: Codable, Equatable, Sendable {
    public let text: String
    public let isBlank: Bool
    public let underlined: Bool
}
/// Presentation compiled from an actual source result card, independently of grading.
public struct ResultReviewPresentation: Codable, Equatable, Sendable {
    public let title: String
    public let prompt: String
    public let correctAnswer: String
    public let declinedAnswer: String?
    public let audioResources: [String]
}
public struct ResultReviewEntry: Equatable, Sendable, Identifiable {
    public let id: String
    public let questionID: String
    public let presentation: ResultReviewPresentation
    public let answer: String
    public let accepted: Bool?
    public let declined: Bool
}
public struct Question: Codable, Equatable, Sendable, Identifiable {
    public let resultReview: ResultReviewPresentation?
    public let isolationPromptTokens: [IsolationPromptToken]?
    public let matchedAudioResources: [String]?
    public let correctFeedbackAudioVolume: Double?
    public let incorrectFeedbackAudioVolume: Double?
    public let correctFeedbackAudioResource: String?
    public let incorrectFeedbackAudioResource: String?
    public let practiceAudioResources: [String]?
    public let practiceAudioLabels: [String]?
    public let id: String
    public let kind: QuestionKind
    public let prompt: String
    public let options: [Choice]
    public let answer: String
    public let words: [Choice]
    public let answerWords: [String]
    public let pairs: [WordPair]
    public let explanation: String
    public let hint: String?
    public let feedbackHint: String?
    public let newWord: Bool
    public let rightOrder: [String]?
    public let audioResource: String?
    public let sourceLanguage: String?
    public let promptImageResource: String?
    public let characterResource: String?
    public let sourceType: String?
    public let slowAudioResource: String?
    public let dialogueAvatars: [String]?
    public let correctFeedback: String?
    public let indicator: String?
    public let contextExamples: [String]?
    public let contextHighlights: [String]?
    public let example: String?
    public let exampleAudioResource: String?
    public let completionPrefix: String?
    public let completionSuffix: String?
    public let listeningDecline: ListeningDecline?
    public let keyboardAnswer: String?
    public let keyboardPrompt: String?
    public let reviewWordOrder: [String]?
    public let skipLabel: String?
    public let skipCorrectText: String?
    public let feedbackReportReasons: [String]?
    enum CodingKeys: String, CodingKey {
        case resultReview, promptImageResource
        case isolationPromptTokens
        case correctFeedbackAudioVolume, incorrectFeedbackAudioVolume
        case matchedAudioResources, correctFeedbackAudioResource, incorrectFeedbackAudioResource
        case practiceAudioResources, practiceAudioLabels, feedbackHint, reviewWordOrder, skipLabel, skipCorrectText
        case keyboardAnswer, keyboardPrompt, correctFeedback, indicator, contextExamples, contextHighlights, example, exampleAudioResource, completionPrefix, completionSuffix, listeningDecline, feedbackReportReasons
        case id, kind, prompt, options, answer, words, pairs, explanation, hint, newWord, rightOrder, audioResource, sourceLanguage, characterResource, sourceType, slowAudioResource, dialogueAvatars
        case answerWords = "answer_words"
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        resultReview = try c.decodeIfPresent(ResultReviewPresentation.self, forKey: .resultReview)
        isolationPromptTokens = try c.decodeIfPresent([IsolationPromptToken].self, forKey: .isolationPromptTokens)
        matchedAudioResources = try c.decodeIfPresent([String].self, forKey: .matchedAudioResources)
        correctFeedbackAudioVolume = try c.decodeIfPresent(Double.self, forKey: .correctFeedbackAudioVolume)
        incorrectFeedbackAudioVolume = try c.decodeIfPresent(Double.self, forKey: .incorrectFeedbackAudioVolume)
        correctFeedbackAudioResource = try c.decodeIfPresent(String.self, forKey: .correctFeedbackAudioResource)
        incorrectFeedbackAudioResource = try c.decodeIfPresent(String.self, forKey: .incorrectFeedbackAudioResource)
        practiceAudioResources = try c.decodeIfPresent([String].self, forKey: .practiceAudioResources)
        practiceAudioLabels = try c.decodeIfPresent([String].self, forKey: .practiceAudioLabels)
        id = try c.decode(String.self, forKey: .id)
        kind = try c.decodeIfPresent(QuestionKind.self, forKey: .kind) ?? .choice
        prompt = try c.decode(String.self, forKey: .prompt)
        options = try c.decodeIfPresent([Choice].self, forKey: .options) ?? []
        answer = try c.decodeIfPresent(String.self, forKey: .answer) ?? ""
        words = try c.decodeIfPresent([Choice].self, forKey: .words) ?? []
        answerWords = try c.decodeIfPresent([String].self, forKey: .answerWords) ?? []
        pairs = try c.decodeIfPresent([WordPair].self, forKey: .pairs) ?? []
        explanation = try c.decode(String.self, forKey: .explanation)
        hint = try c.decodeIfPresent(String.self, forKey: .hint)
        feedbackHint = try c.decodeIfPresent(String.self, forKey: .feedbackHint)
        newWord = try c.decodeIfPresent(Bool.self, forKey: .newWord) ?? false
        rightOrder = try c.decodeIfPresent([String].self, forKey: .rightOrder)
        audioResource = try c.decodeIfPresent(String.self, forKey: .audioResource)
        sourceLanguage = try c.decodeIfPresent(String.self, forKey: .sourceLanguage)
        sourceType = try c.decodeIfPresent(String.self, forKey: .sourceType)
        slowAudioResource = try c.decodeIfPresent(String.self, forKey: .slowAudioResource)
        dialogueAvatars = try c.decodeIfPresent([String].self, forKey: .dialogueAvatars)
        promptImageResource = try c.decodeIfPresent(String.self, forKey: .promptImageResource)
        characterResource = try c.decodeIfPresent(String.self, forKey: .characterResource)
        correctFeedback = try c.decodeIfPresent(String.self, forKey: .correctFeedback)
        indicator = try c.decodeIfPresent(String.self, forKey: .indicator)
        contextHighlights = try c.decodeIfPresent([String].self, forKey: .contextHighlights)
        contextExamples = try c.decodeIfPresent([String].self, forKey: .contextExamples)
        example = try c.decodeIfPresent(String.self, forKey: .example)
        exampleAudioResource = try c.decodeIfPresent(String.self, forKey: .exampleAudioResource)
        completionPrefix = try c.decodeIfPresent(String.self, forKey: .completionPrefix)
        completionSuffix = try c.decodeIfPresent(String.self, forKey: .completionSuffix)
        listeningDecline = try c.decodeIfPresent(ListeningDecline.self, forKey: .listeningDecline)
        keyboardAnswer = try c.decodeIfPresent(String.self, forKey: .keyboardAnswer)
        keyboardPrompt = try c.decodeIfPresent(String.self, forKey: .keyboardPrompt)
        reviewWordOrder = try c.decodeIfPresent([String].self, forKey: .reviewWordOrder)
        skipLabel = try c.decodeIfPresent(String.self, forKey: .skipLabel)
        skipCorrectText = try c.decodeIfPresent(String.self, forKey: .skipCorrectText)
        feedbackReportReasons = try c.decodeIfPresent([String].self, forKey: .feedbackReportReasons)
    }
    public var correctText: String {
        switch kind {
        case .choice: options.first { $0.id == answer }?.text ?? ""
        case .wordTiles: answerWords.compactMap { id in words.first { $0.id == id }?.text }.joined(separator: " ")
        case .matching: "All pairs matched"
        case .textEntry: (completionPrefix ?? "") + answer + (completionSuffix ?? "")
        }
    }
    var valid: Bool {
        func unique(_ ids: [String]) -> Bool { !ids.isEmpty && ids.allSatisfy { !$0.isEmpty } && Set(ids).count == ids.count }
        guard !id.isEmpty, !prompt.isEmpty else { return false }
        if let order = reviewWordOrder {
            guard unique(order), Set(order) == Set(words.map(\.id)) else { return false }
        }
        switch kind {
        case .textEntry: return !answer.isEmpty
        case .choice: return unique(options.map(\.id)) && options.contains { $0.id == answer }
        case .wordTiles: return unique(words.map(\.id)) && unique(answerWords) && answerWords.allSatisfy { id in words.contains { $0.id == id } }
        case .matching: return unique(pairs.map(\.id)) && pairs.allSatisfy { !$0.left.isEmpty && !$0.right.isEmpty }
            && (rightOrder == nil || (unique(rightOrder!) && Set(rightOrder!) == Set(pairs.map(\.id))))
        }
    }
}
public struct LessonInterlude: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let afterQuestionID: String
    public let text: String
}
public struct LessonEntry: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let title: String
    public let startLabel: String
    public let declineLabel: String
}
public struct SettlementPage: Codable, Equatable, Sendable, Identifiable {
    public var artResource: String? = nil
    public var experienceIconResource: String? = nil
    public var accuracyIconResource: String? = nil
    public var heartResources: [String]? = nil
    public var retryLabel: String? = nil
    public let id: String
    public let kind: String
    public let title: String
    public let body: String?
    public let continueLabel: String
    public let secondaryLabel: String?
    public let experience: Int?
    public let observedStreak: Int?
    public let observedAccuracy: Int?
    public let observedMistakes: Int?
    public let accuracyLabel: String?
    public var levelLabel: String? = nil
    public var scoreValue: Int? = nil
    public var questTarget: Int? = nil
}
public struct DeferredSpeech: Codable, Equatable, Sendable, Identifiable {
    public var characterResource: String? = nil
    public let resultReview: ResultReviewPresentation?
    public let id: String
    public let beforeQuestionID: String
    public let title: String
    public let phrase: String
    public let audioResource: String
    public let declineLabel: String
    public let closedTitle: String
    public let closedBody: String
}
public struct SettlementFlow: Equatable, Sendable {
    public let pages: [SettlementPage]
    public private(set) var position = 0
    public var current: SettlementPage? { pages.indices.contains(position) ? pages[position] : nil }
    public init(pages: [SettlementPage]) { self.pages = pages }
    public mutating func advance() { if current != nil { position += 1 } }
}
public struct ObservedPlacementOutcome: Codable, Equatable, Sendable {
    public var activeUnit: Int? = nil
    public let activeStage: Int
    public let sectionTitle: String
    public let courseTitle: String
    public let completedStages: Set<Int>
    public let englishScore: Int
    public var homeSnapshot: HomeProgressSnapshot
    public let sourceEvidence: String
    public let observedMistakes: Int
}
public struct LessonDefinition: Codable, Equatable, Sendable, Identifiable {
    public var postHomeCoach: String? = nil
    public var completionAudioResource: String? = nil
    public var completionAudioVolume: Double? = nil
    public var placementOutcome: ObservedPlacementOutcome? = nil
    public var observedHomeSnapshot: HomeProgressSnapshot? = nil
    public var listeningDeclineReplacements: [String: Question]? = nil
    public var initialKeyboardForTiles: Bool? = nil
    public let id: String
    public let title: String
    public let questions: [Question]
    public let interludes: [LessonInterlude]?
    public let initialInterlude: LessonInterlude?
    public let entry: LessonEntry?
    public let settlement: [SettlementPage]?
    public var deferredSpeech: [DeferredSpeech]? = nil
    public var reviewInterlude: LessonInterlude? = nil
}
public struct CoursePathNode: Codable, Equatable, Sendable {
    public let kind: String
    public let lessonIDs: [String]
    public let lessonCount: Int?
}
public struct HomeProgressSnapshot: Codable, Equatable, Sendable {
    public let streak: Int?
    public let completedLessons: Int
    public let gems: Int
    public let leagueTitle: String?
    public let leagueLink: String?
    public let leagueMessage: String?
    public let leagueCountdown: String?
    public let leagueCountdownEndEpochMilliseconds: Double?
    public func leagueCountdownText(at date: Date) -> String? {
        guard let deadline = leagueCountdownEndEpochMilliseconds else { return leagueCountdown }
        let seconds = max(0, Int(floor((deadline - date.timeIntervalSince1970 * 1000) / 1000)))
        if seconds >= 3600 { return "\(seconds / 3600) 小时" }
        if seconds >= 60 { return "\(seconds / 60) 分钟" }
        return "\(seconds) 秒"
    }
    public let leagueResource: String?
    public let questTarget: Int?
    public let questProgress: Int?
    public let questCountdown: String?
}
public struct PathChestPresentation: Codable, Equatable, Sendable {
    public let id: String
    public let afterLessonIDs: [String]
    public let beforeGems: Int
    public let afterGems: Int
    public let readyResource: String
    public let openedResource: String
    public let readyCenters: [Double]
    public let openedCenters: [Double]
    public let readyHeight: Double
    public let openedHeight: Double
    public let readyImageOffset: Double
    public let openedImageOffset: Double
}
public struct HomePresentation: Codable, Equatable, Sendable {
    public let sectionTitle: String
    public let firstNodeLessonCount: Int
    public let pathKinds: [String]
    public let nextSectionTitle: String
    public let flagResource: String
    public let pronunciationResource: String
    public let completedNodeResource: String?
    public let completedNodeCenters: [Double]?
    public let completedPathHeight: Double?
    public let progressSnapshots: [HomeProgressSnapshot]?
    public let pathChest: PathChestPresentation?
}
public struct Course: Codable, Equatable, Sendable, Identifiable {
    public let mistakeHeartCost: Int
    public let id: String
    public let title: String
    public let lessons: [LessonDefinition]
    public let speechLanguage: String
    public let home: HomePresentation?
    public let interfaceLanguage: String?
    public let pathNodes: [CoursePathNode]?
    public let usesLegacyQuestions: Bool
    // Compatibility for the original single-lesson curriculum.
    public var questions: [Question] { lessons[0].questions }
    enum CodingKeys: String, CodingKey { case id, title, lessons, questions, speechLanguage, pathNodes, interfaceLanguage, home, mistakeHeartCost }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        mistakeHeartCost = try c.decodeIfPresent(Int.self, forKey: .mistakeHeartCost) ?? 1
        id = try c.decode(String.self, forKey: .id)
        title = try c.decode(String.self, forKey: .title)
        home = try c.decodeIfPresent(HomePresentation.self, forKey: .home)
        interfaceLanguage = try c.decodeIfPresent(String.self, forKey: .interfaceLanguage)
        speechLanguage = try c.decodeIfPresent(String.self, forKey: .speechLanguage) ?? "en-US"
        pathNodes = try c.decodeIfPresent([CoursePathNode].self, forKey: .pathNodes)
        if let definitions = try c.decodeIfPresent([LessonDefinition].self, forKey: .lessons) {
            guard !c.contains(.questions) else { throw DecodingError.dataCorruptedError(forKey: .lessons, in: c, debugDescription: "Declare lessons or legacy questions, not both") }
            lessons = definitions
            usesLegacyQuestions = false
        } else {
            lessons = [LessonDefinition(id: "intro", title: title, questions: try c.decode([Question].self, forKey: .questions), interludes: nil, initialInterlude: nil, entry: nil, settlement: nil)]
            usesLegacyQuestions = true
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id); try c.encode(title, forKey: .title)
        try c.encode(mistakeHeartCost, forKey: .mistakeHeartCost)
        try c.encode(speechLanguage, forKey: .speechLanguage)
        try c.encodeIfPresent(interfaceLanguage, forKey: .interfaceLanguage)
        try c.encodeIfPresent(home, forKey: .home)
        try c.encodeIfPresent(pathNodes, forKey: .pathNodes)
        if usesLegacyQuestions { try c.encode(questions, forKey: .questions) }
        else { try c.encode(lessons, forKey: .lessons) }
    }
    public static func readFixture(_ url: URL) throws -> Course {
        struct DataSection: Decodable { let candidate_course: Course }
        struct Fixture: Decodable { let data: DataSection }
        let course = try JSONDecoder().decode(Fixture.self, from: Data(contentsOf: url)).data.candidate_course
        guard !course.id.isEmpty, course.mistakeHeartCost >= 0, !course.lessons.isEmpty,
              Set(course.lessons.map(\.id)).count == course.lessons.count,
              course.lessons.allSatisfy({ lesson in
                  !lesson.id.isEmpty && !lesson.questions.isEmpty
                    && Set(lesson.questions.map(\.id)).count == lesson.questions.count
                    && lesson.questions.allSatisfy(\.valid)
                    && (lesson.listeningDeclineReplacements ?? [:]).allSatisfy { id, replacement in
                        lesson.questions.contains { $0.id == id && $0.listeningDecline != nil }
                            && replacement.valid && replacement.listeningDecline == nil
                    }
              }) else { throw CocoaError(.fileReadCorruptFile) }
        return course
    }
}

public struct Lesson: Equatable, Sendable {
    public let course: Course
    public let lessonIndex: Int
    public var definition: LessonDefinition { course.lessons[lessonIndex] }
    public private(set) var position = 0
    public private(set) var selected: String?
    public private(set) var selectedWords = [String]()
    public private(set) var enteredText = ""
    public private(set) var keyboardText = ""
    public private(set) var usingKeyboard = false
    private var prefersKeyboardForTiles = false
    private var prefersFullSentence = false
    public var displayedInput: String { usingKeyboard ? keyboardText : enteredText }
    public var displayedPrompt: String { usingKeyboard ? (question.keyboardPrompt ?? question.prompt) : question.prompt }
    public var supportsInputMode: Bool { question.keyboardAnswer != nil && question.keyboardPrompt != nil && (question.kind == .wordTiles || question.kind == .textEntry) }
    public mutating func toggleInputMode() {
        guard supportsInputMode, feedback == nil, !complete, !listeningDeclined, interlude == nil, deferredSpeech == nil else { return }
        usingKeyboard.toggle()
        if question.kind == .wordTiles { prefersKeyboardForTiles = usingKeyboard }
        else if question.kind == .textEntry { prefersFullSentence = usingKeyboard }
    }
    public private(set) var matchedPairs = Set<String>()
    public private(set) var selectedLeft: String?
    public private(set) var selectedRight: String?
    public private(set) var matchingHint: String?
    public private(set) var incorrectMatch: [String]?
    public private(set) var skipped = false
    public private(set) var feedback: Bool?
    public private(set) var hearts: Int
    public private(set) var mistakesMade = 0
    public private(set) var correctStreak = 0
    public private(set) var review = [Int]()
    public private(set) var reviewing = false
    public private(set) var complete = false
    public private(set) var interlude: LessonInterlude?
    private var handledSpeech = Set<String>()
    public private(set) var speechDeclined = false
    public private(set) var listeningDeclined = false
    public private(set) var resultReviewEntries = [ResultReviewEntry]()
    private var replacedQuestions = [Int: Question]()
    public mutating func declineListening() {
        guard question.listeningDecline != nil,
              feedback == nil, !listeningDeclined, !complete, interlude == nil, deferredSpeech == nil else { return }
        listeningDeclined = true
    }
    public var deferredSpeech: DeferredSpeech? {
        guard !complete, !reviewing else { return nil }
        return definition.deferredSpeech?.first { $0.beforeQuestionID == question.id && !handledSpeech.contains($0.id) }
    }
    public mutating func declineSpeech() {
        guard deferredSpeech != nil else { return }
        speechDeclined = true
    }
    public var question: Question { replacedQuestions[position] ?? definition.questions[position] }
    public var displayedHint: String? { feedback == nil ? question.hint : question.feedbackHint ?? question.hint }
    public var visibleWords: [Choice] {
        guard reviewing, let order = question.reviewWordOrder else { return question.words }
        return order.compactMap { id in question.words.first { $0.id == id } }
    }
    public var canSubmit: Bool {
        guard feedback == nil, !listeningDeclined, !complete, interlude == nil, deferredSpeech == nil else { return false }
        if usingKeyboard { return !keyboardText.isEmpty }
        switch question.kind {
        case .choice: return selected != nil
        case .wordTiles: return !selectedWords.isEmpty
        case .matching: return false
        case .textEntry: return !enteredText.isEmpty
        }
    }
    public init(course: Course, lessonIndex: Int = 0, hearts: Int = 5) {
        precondition(course.lessons.indices.contains(lessonIndex) && hearts >= 0)
        self.course = course; self.lessonIndex = lessonIndex; self.hearts = hearts
        self.interlude = course.lessons[lessonIndex].initialInterlude
        self.prefersKeyboardForTiles = course.lessons[lessonIndex].initialKeyboardForTiles ?? false
        self.usingKeyboard = supportsInputMode && prefersKeyboardForTiles
    }
    public mutating func choose(_ id: String) {
        guard question.kind == .choice, feedback == nil, !listeningDeclined, !complete, interlude == nil, deferredSpeech == nil, question.options.contains(where: { $0.id == id }) else { return }
        selected = id
    }
    public mutating func enterText(_ text: String) {
        guard (question.kind == .textEntry || usingKeyboard), feedback == nil, !listeningDeclined, !complete, interlude == nil, deferredSpeech == nil else { return }
        if usingKeyboard { keyboardText = text } else { enteredText = text }
    }
    public mutating func addWord(_ id: String) {
        guard question.kind == .wordTiles, feedback == nil, !listeningDeclined, !complete, interlude == nil, deferredSpeech == nil,
              question.words.contains(where: { $0.id == id }), !selectedWords.contains(id) else { return }
        selectedWords.append(id)
    }
    public mutating func removeWord(_ id: String) {
        guard question.kind == .wordTiles, feedback == nil, !listeningDeclined, !complete, interlude == nil, deferredSpeech == nil else { return }
        selectedWords.removeAll { $0 == id }
    }
    public mutating func matchLeft(_ id: String) { selectPair(id, left: true) }
    public mutating func matchRight(_ id: String) { selectPair(id, left: false) }
    private mutating func selectPair(_ id: String, left: Bool) {
        guard question.kind == .matching, feedback == nil, !listeningDeclined, !complete, interlude == nil, deferredSpeech == nil,
              question.pairs.contains(where: { $0.id == id }), !matchedPairs.contains(id) else { return }
        matchingHint = nil; incorrectMatch = nil
        if left { selectedLeft = id } else { selectedRight = id }
        if let a = selectedLeft, let b = selectedRight {
            if a == b { matchedPairs.insert(a) }
            else if question.sourceType == "listenMatch" {
                incorrectMatch = [a, b]
                hearts = max(0, hearts - course.mistakeHeartCost); mistakesMade += 1; correctStreak = 0
                // Observed mixed-error source retries this pair in-place and reviews only its typed error at lesson end.
            } else { matchingHint = "Try a different pair." } // Historical text-pair penalty remains unobserved.
            selectedLeft = nil; selectedRight = nil
            if matchedPairs.count == question.pairs.count { feedback = true; correctStreak += 1 }
        }
    }
    public mutating func skip() {
        guard question.skipLabel != nil, feedback == nil, !listeningDeclined, !complete, interlude == nil, deferredSpeech == nil else { return }
        // Actual empty q0 skip queued review without spending a heart or an error.
        // Mid-streak skip behavior remains unobserved.
        skipped = true; feedback = false
        if !review.contains(position) { review.append(position) }
    }
    public mutating func submit() {
        guard canSubmit else { return }
        // Tile IDs enforce one use per occurrence. Grading follows the visible
        // word sequence so two indistinguishable copies can exchange positions.
        let textByID = Dictionary(uniqueKeysWithValues: question.words.map { ($0.id, $0.text) })
        let correct: Bool
        if usingKeyboard {
            correct = keyboardText.caseInsensitiveCompare(question.keyboardAnswer ?? "") == .orderedSame
        } else {
        switch question.kind {
        case .choice: correct = selected == question.answer
        case .wordTiles: correct = selectedWords.compactMap { textByID[$0] } == question.answerWords.compactMap { textByID[$0] }
        case .textEntry: correct = enteredText.caseInsensitiveCompare(question.answer) == .orderedSame // HOT accepted for source hot; whitespace, punctuation and spelling tolerance remain unverified.
        case .matching: return
        }
        }
        feedback = correct
        correctStreak = correct ? correctStreak + 1 : 0
        if !correct {
            mistakesMade += 1
            hearts = max(0, hearts - course.mistakeHeartCost)
            if !review.contains(position) { review.append(position) }
        }
    }
    private mutating func clearAnswer() {
        selected = nil; selectedWords = []; enteredText = ""; keyboardText = ""; matchedPairs = []
        usingKeyboard = supportsInputMode && (question.kind == .wordTiles ? prefersKeyboardForTiles : prefersFullSentence)
        selectedLeft = nil; selectedRight = nil; matchingHint = nil; incorrectMatch = nil; feedback = nil; listeningDeclined = false; skipped = false
    }
    public mutating func advance() {
        if interlude != nil { interlude = nil; return }
        if let speech = deferredSpeech {
            guard speechDeclined else { return }
            if let presentation = speech.resultReview, let answer = presentation.declinedAnswer {
                resultReviewEntries.append(ResultReviewEntry(id: "review-\(resultReviewEntries.count)", questionID: speech.id,
                    presentation: presentation, answer: answer, accepted: nil, declined: true))
            }
            handledSpeech.insert(speech.id); speechDeclined = false
            return
        }
        guard feedback != nil || listeningDeclined, !complete else { return }
        if let accepted = feedback, let presentation = question.resultReview {
            let answer: String
            if usingKeyboard { answer = keyboardText }
            else {
                switch question.kind {
                case .choice: answer = question.options.first { $0.id == selected }?.text ?? ""
                case .wordTiles: answer = (question.completionPrefix ?? "") + selectedWords.compactMap { id in question.words.first { $0.id == id }?.text }.joined(separator: question.sourceLanguage == "en" ? "" : " ") + (question.completionSuffix ?? "")
                case .textEntry: answer = (question.completionPrefix ?? "") + enteredText + (question.completionSuffix ?? "")
                case .matching: answer = ""
                }
            }
            resultReviewEntries.append(ResultReviewEntry(id: "review-\(resultReviewEntries.count)", questionID: question.id,
                presentation: presentation, answer: answer, accepted: accepted, declined: false))
        }
        if listeningDeclined, let replacement = definition.listeningDeclineReplacements?[question.id] {
            // The skipped listening question is not graded. Its observed
            // translation occupies the same position and remains available
            // for a later wrong-answer review instead of restoring listening.
            replacedQuestions[position] = replacement
            clearAnswer()
            return
        }
        let answeredID = question.id
        let enteringReview = !reviewing && position + 1 == definition.questions.count
        if reviewing {
            if feedback == true { review.removeAll { $0 == position } }
        } else if position + 1 < definition.questions.count {
            position += 1; clearAnswer()
            interlude = definition.interludes?.first { $0.afterQuestionID == answeredID }
            return
        } else { reviewing = true }
        if let next = review.first {
            position = next
            if enteringReview { interlude = definition.reviewInterlude }
        }
        else { complete = true }
        clearAnswer()
    }
}

public struct LearningProgress: Codable, Equatable, Sendable {
    public var completedCourses: Set<String> = []
    public var completedLessons: [String: Set<String>] = [:]
    public var hearts = 5
    public var spentGems = 0
    public var placementOutcomes: [String: ObservedPlacementOutcome] = [:]
    public var openedPathChests: [String: Set<String>] = [:]
    public init() {}
    enum CodingKeys: String, CodingKey { case completedCourses, completedLessons, hearts, openedPathChests, placementOutcomes, spentGems }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        guard c.contains(.completedCourses) || c.contains(.completedLessons) else {
            throw DecodingError.dataCorruptedError(forKey: .completedCourses, in: c, debugDescription: "Stored progress must contain a completion collection")
        }
        completedCourses = c.contains(.completedCourses) ? try c.decode(Set<String>.self, forKey: .completedCourses) : []
        completedLessons = c.contains(.completedLessons) ? try c.decode([String: Set<String>].self, forKey: .completedLessons) : [:]
        placementOutcomes = try c.decodeIfPresent([String: ObservedPlacementOutcome].self, forKey: .placementOutcomes) ?? [:]
        openedPathChests = try c.decodeIfPresent([String: Set<String>].self, forKey: .openedPathChests) ?? [:]
        spentGems = try c.decodeIfPresent(Int.self, forKey: .spentGems) ?? 0
        guard spentGems >= 0 else { throw DecodingError.dataCorruptedError(forKey: .spentGems, in: c, debugDescription: "Gem spending cannot be negative") }
        hearts = c.contains(.hearts) ? try c.decode(Int.self, forKey: .hearts) : 5
        guard hearts >= 0 else { throw DecodingError.dataCorruptedError(forKey: .hearts, in: c, debugDescription: "Hearts cannot be negative") }
    }
    // Observed guest purchase: 4→5 hearts; 505→155 gems survives reload.
    // Presentation may lag the purchase; this records the durable transaction.
    @discardableResult public mutating func purchaseHeartRefill(availableGems: Int) -> Bool {
        guard hearts < 5, availableGems >= 350 else { return false }
        hearts = 5
        spentGems += 350
        return true
    }
    public func isPathChestReady(_ course: Course) -> Bool {
        guard let chest = course.home?.pathChest, !chest.afterLessonIDs.isEmpty else { return false }
        return chest.afterLessonIDs.allSatisfy { completedLessons[course.id, default: []].contains($0) }
    }
    public func isPathChestOpened(_ course: Course) -> Bool {
        guard let chest = course.home?.pathChest else { return false }
        return openedPathChests[course.id, default: []].contains(chest.id)
    }
    @discardableResult public mutating func openPathChest(_ course: Course) -> Bool {
        guard isPathChestReady(course), !isPathChestOpened(course), let chest = course.home?.pathChest else { return false }
        openedPathChests[course.id, default: []].insert(chest.id)
        return true
    }
    public func isCompleted(_ course: Course, index: Int) -> Bool {
        guard course.lessons.indices.contains(index) else { return false }
        return completedLessons[course.id, default: []].contains(course.lessons[index].id)
            || course.usesLegacyQuestions && completedCourses.contains(course.id)
    }
    public func completedCount(_ course: Course) -> Int {
        course.lessons.indices.prefix { isCompleted(course, index: $0) }.count
    }
    public func isUnlocked(_ course: Course, index: Int) -> Bool {
        course.lessons.indices.contains(index) && (0..<index).allSatisfy { isCompleted(course, index: $0) }
    }
    @discardableResult public mutating func markCompleted(_ course: Course, index: Int) -> Bool {
        guard isUnlocked(course, index: index) else { return false }
        completedLessons[course.id, default: []].insert(course.lessons[index].id)
        let hasUncompiledPath = course.pathNodes?.contains { node in
            node.kind != "chest" && (node.lessonIDs.isEmpty || (node.lessonCount ?? node.lessonIDs.count) > node.lessonIDs.count)
        } ?? false
        if completedCount(course) == course.lessons.count && !hasUncompiledPath { completedCourses.insert(course.id) }
        else { completedCourses.remove(course.id) }
        return true
    }
}
public struct ProgressStore: Sendable {
    public let url: URL
    public init(url: URL) { self.url = url }
    public func load() throws -> LearningProgress {
        guard FileManager.default.fileExists(atPath: url.path) else { return LearningProgress() }
        return try JSONDecoder().decode(LearningProgress.self, from: Data(contentsOf: url))
    }
    public func save(_ progress: LearningProgress) throws {
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONEncoder().encode(progress).write(to: url, options: .atomic)
    }
}
