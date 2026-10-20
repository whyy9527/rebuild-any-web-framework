import Foundation

/// Observed account preferences. Lesson-generation effects remain separate
/// requirements; storing a preference does not establish those effects.
struct LearningPreferences: Codable {
    var pronunciationCoach: String?
    var soundEffects = true
    var animations = true
    var motivationalMessages = true
    var listeningExercises = true
    var darkMode = "System Default"
    var leaderboardStatus: Int?
    var avatarSkin: Int?
    var avatarState: [String:Int]?
}
