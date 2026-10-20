import Foundation
import AVFoundation

// Compile alongside LearningAudio.swift: tests the shipped generator and player,
// not a substitute. Playback transport success is not an acoustic recording.
@main struct AudioChecks {
    @MainActor static func main() async throws {
        let output = URL(fileURLWithPath: CommandLine.arguments[1])
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        var distinct = Set<Data>()
        for cue in LearningAudio.Cue.allCases {
            let data = LearningAudio.wave(cue)
            let player = try AVAudioPlayer(data: data)
            precondition(player.duration > 0.03 && player.duration < 1)
            precondition(data.count > 1000)
            precondition(String(data: data.prefix(4), encoding: .ascii) == "RIFF")
            distinct.insert(data)
            try data.write(to: output.appendingPathComponent(cue.rawValue + ".wav"))
        }
        precondition(distinct.count == LearningAudio.Cue.allCases.count)
        let audio = LearningAudio(resourceURL: { name in
            URL(fileURLWithPath: "projects/education-swift/Sources/LingoSeed/Resources/Reference").appendingPathComponent(name)
        })
        precondition(audio.play(.complete))
        try await Task.sleep(for: .milliseconds(100))
        precondition(audio.isPlaying && audio.playbackTime > 0.03)
        audio.muted = true
        precondition(!audio.isPlaying && !audio.play(.correct))
        audio.muted = false
        precondition(audio.play(.correct))
        try await Task.sleep(for: .milliseconds(70))
        precondition(audio.isPlaying && audio.playbackTime > 0)
        audio.effectsEnabled = false
        precondition(!audio.isPlaying && !audio.play(.correct) && !audio.muted)
        audio.effectsEnabled = true
        precondition(audio.play(.correct))
        audio.muted = true
        let reference = "speech-" // Exact fixture source resource; no substitute waveform.
        let fixture = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: "projects/duolingo-web/reference-speech-v5.json"))) as! [String: String]
        let name = fixture.keys.sorted().first(where: { $0.hasPrefix(reference) })!
        audio.muted = false; audio.effectsEnabled = false
        audio.speak("", resource: name)
        try await Task.sleep(for: .milliseconds(100))
        precondition(audio.referenceSpeechPlaying && audio.referencePlaybackTime > 0.03)
        audio.muted = true
        precondition(!audio.referenceSpeechPlaying)
        audio.speak("", resource: name)
        precondition(!audio.referenceSpeechPlaying)
        print("PASS four distinct decodable WAV cues; actual player time advances; mute stops/blocks; unmute resumes; effects switch stops/blocks independently of global mute. Bundled source speech advances with effects disabled; global mute stops/blocks it. Acoustic output remains unverified.")
    }
}
